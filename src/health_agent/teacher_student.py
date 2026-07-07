from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

from health_agent.competition import (
    CRITERION_LABELS,
    ELIGIBILITY_LABELS,
    aggregate_eligibility,
)
from health_agent.llm_client import (
    ChatResult,
    FriendliClient,
    FriendliConfig,
    load_dotenv_values,
)
from health_agent.models import Patient, Trial
from health_agent.orchestrator import patient_to_clinical_note
from health_agent.scoring import evaluate_trial


TEACHER_SYSTEM_PROMPT = """You are the teacher labeler for a clinical trial matching research prototype.
Use only the supplied synthetic patient note, extracted patient fields, trial metadata, and listed criteria.
Do not use outside medical knowledge to fill missing patient facts.
This is not medical advice and not a real clinical eligibility decision.

Return JSONL only: exactly one JSON object per supplied pair_id.
Do not wrap the output in markdown.

Allowed eligibility labels:
- eligible: all supplied required criteria are satisfied or not applicable, and no exclusion is violated.
- ineligible: at least one required inclusion conflicts, or an exclusion criterion is violated.
- uncertain: no hard conflict is proven, but required information is missing.

Allowed criterion status labels:
- satisfied: the patient information satisfies this criterion.
- violated: the patient information conflicts with this criterion, or the patient has an exclusion.
- unknown: the supplied patient information is insufficient.
- not_applicable: the criterion is not applicable to this pair.

For exclusion criteria, satisfied means the exclusion is absent; violated means the exclusion is present.
Every listed criterion_id must appear exactly once in criterion_results.
Ask follow_up_questions only for unknown required facts."""


@dataclass(frozen=True)
class OpenAIChatConfig:
    api_key: str
    model: str
    chat_completions_url: str

    @classmethod
    def from_env(cls, env_file: Path | None = None) -> "OpenAIChatConfig":
        values = load_dotenv_values(env_file) if env_file else {}
        env = {**values, **os.environ}
        base_url = env.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
        return cls(
            api_key=env.get("OPENAI_API_KEY") or "",
            model=env.get("OPENAI_MODEL")
            or env.get("GPT_TEACHER_MODEL")
            or env.get("GPT_MODEL")
            or "",
            chat_completions_url=env.get("OPENAI_CHAT_COMPLETIONS_URL")
            or f"{base_url.rstrip('/')}/chat/completions",
        )

    @property
    def configured(self) -> bool:
        return bool(self.api_key and self.model)

    @property
    def missing(self) -> list[str]:
        missing = []
        if not self.api_key:
            missing.append("OPENAI_API_KEY")
        if not self.model:
            missing.append("OPENAI_MODEL")
        return missing

    def public_status(self) -> dict[str, Any]:
        return {
            "configured": self.configured,
            "hasApiKey": bool(self.api_key),
            "hasModel": bool(self.model),
            "chatCompletionsUrl": self.chat_completions_url,
            "missing": self.missing,
        }


class OpenAIChatClient:
    def __init__(self, config: OpenAIChatConfig, timeout_sec: int = 180) -> None:
        if not config.configured:
            raise ValueError(f"Missing teacher API configuration: {', '.join(config.missing)}")
        self.config = config
        self.timeout_sec = timeout_sec

    def chat(
        self,
        messages: list[dict[str, str]],
        *,
        max_tokens: int = 8000,
        temperature: float = 0,
    ) -> ChatResult:
        started = time.perf_counter()
        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        request = urllib.request.Request(
            self.config.chat_completions_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_sec) as response:
                payload = json.loads(response.read().decode("utf-8", errors="replace"))
                content = (
                    payload.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
                )
                return ChatResult(
                    ok=200 <= response.status < 300,
                    http_status=response.status,
                    retry_after=response.headers.get("retry-after", ""),
                    ms=elapsed_ms(started),
                    content=str(content or ""),
                    finish_reason=str(
                        payload.get("choices", [{}])[0].get("finish_reason") or ""
                    ),
                )
        except urllib.error.HTTPError as error:
            return ChatResult(
                ok=False,
                http_status=error.code,
                retry_after=error.headers.get("retry-after", "") if error.headers else "",
                ms=elapsed_ms(started),
                content="",
                error=safe_error_body(error),
            )
        except OSError as error:
            return ChatResult(
                ok=False,
                http_status="ERR",
                retry_after="",
                ms=elapsed_ms(started),
                content="",
                error=str(error),
            )


def build_target_pairs(
    *,
    patients: list[Patient],
    trials: list[Trial],
    patient_count: int,
) -> list[dict[str, Any]]:
    trials_by_id = {trial.trial_id: trial for trial in trials}
    pairs = []
    for index, patient in enumerate(patients[:patient_count]):
        if not patient.target_trial_id:
            continue
        trial = trials_by_id.get(patient.target_trial_id)
        if trial is None:
            continue
        pairs.append(build_pair(patient=patient, trial=trial, patient_index=index))
    return pairs


def build_pair(*, patient: Patient, trial: Trial, patient_index: int) -> dict[str, Any]:
    return {
        "pair_id": f"{patient.patient_id}__{trial.trial_id}",
        "patient_id": patient.patient_id,
        "trial_id": trial.trial_id,
        "scenario": patient.scenario or "",
        "patient_note": patient_to_clinical_note(patient, patient_index),
        "patient_profile": patient_profile(patient),
        "trial": trial_payload(trial),
        "criteria": criteria_for_trial(trial),
    }


def patient_profile(patient: Patient) -> dict[str, Any]:
    payload = asdict(patient)
    return {
        key: value
        for key, value in payload.items()
        if key not in {"clinical_note"} and value not in (None, "", [], {})
    }


def trial_payload(trial: Trial) -> dict[str, Any]:
    return {
        "trial_id": trial.trial_id,
        "title": trial.title,
        "conditions": trial.conditions,
        "interventions": trial.interventions[:8],
        "phase": trial.phase,
        "status": trial.status,
        "source_url": trial.source_url,
        "summary": trial.summary,
        "min_age": trial.min_age,
        "max_age": trial.max_age,
        "sex": trial.sex,
        "allowed_stages": trial.allowed_stages,
        "max_ecog": trial.max_ecog,
        "required_biomarkers": trial.required_biomarkers,
        "required_prior_treatments": trial.required_prior_treatments,
        "excluded_flags": trial.excluded_flags,
        "required_patient_fields": trial.required_patient_fields,
        "inclusion_criteria": trial.inclusion_criteria[:12],
        "exclusion_criteria": trial.exclusion_criteria[:12],
        "eligibility_criteria_excerpt": excerpt(trial.eligibility_criteria, 2400),
    }


def criteria_for_trial(trial: Trial) -> list[dict[str, Any]]:
    criteria = [
        {
            "criterion_id": f"{trial.trial_id}-I-condition",
            "criterion_type": "inclusion",
            "criterion": "Patient diagnosis should match the trial condition.",
            "structured_value": trial.conditions,
            "required": True,
        }
    ]
    if trial.min_age is not None or trial.max_age is not None:
        criteria.append(
            {
                "criterion_id": f"{trial.trial_id}-I-age",
                "criterion_type": "inclusion",
                "criterion": "Patient age should be within trial bounds.",
                "structured_value": {
                    "min_age": trial.min_age,
                    "max_age": trial.max_age,
                },
                "required": True,
            }
        )
    if str(trial.sex or "").lower() not in {"", "all", "any"}:
        criteria.append(
            {
                "criterion_id": f"{trial.trial_id}-I-sex",
                "criterion_type": "inclusion",
                "criterion": "Patient recorded sex should match the trial sex criterion.",
                "structured_value": trial.sex,
                "required": True,
            }
        )
    if trial.allowed_stages:
        criteria.append(
            {
                "criterion_id": f"{trial.trial_id}-I-stage",
                "criterion_type": "inclusion",
                "criterion": "Patient disease stage should be allowed.",
                "structured_value": trial.allowed_stages,
                "required": True,
            }
        )
    if trial.max_ecog is not None:
        criteria.append(
            {
                "criterion_id": f"{trial.trial_id}-I-ecog",
                "criterion_type": "inclusion",
                "criterion": "Patient ECOG performance status should be at or below the maximum.",
                "structured_value": trial.max_ecog,
                "required": True,
            }
        )
    for marker, value in trial.required_biomarkers.items():
        criteria.append(
            {
                "criterion_id": f"{trial.trial_id}-I-biomarker-{slug(marker)}",
                "criterion_type": "inclusion",
                "criterion": f"Patient biomarker {marker} should match {value}.",
                "structured_value": {marker: value},
                "required": True,
            }
        )
    for treatment in trial.required_prior_treatments:
        criteria.append(
            {
                "criterion_id": f"{trial.trial_id}-I-prior-{slug(treatment)}",
                "criterion_type": "inclusion",
                "criterion": f"Patient should have prior treatment: {treatment}.",
                "structured_value": treatment,
                "required": True,
            }
        )
    for flag in trial.excluded_flags:
        criteria.append(
            {
                "criterion_id": f"{trial.trial_id}-E-{slug(flag)}",
                "criterion_type": "exclusion",
                "criterion": f"Exclude if patient has {flag.replace('_', ' ')}.",
                "structured_value": flag,
                "required": True,
            }
        )
    return criteria


def write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
            handle.write("\n")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                records.append(json.loads(line))
    return records


def write_teacher_web_files(output_dir: Path, pairs: list[dict[str, Any]]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(output_dir / "pairs_for_teacher.jsonl", pairs)
    (output_dir / "teacher_web_prompt.md").write_text(
        "\n".join(
            [
                "# Teacher Labeling Request",
                "",
                "Read the attached `pairs_for_teacher.jsonl` file.",
                "Return JSONL only, one JSON object per input pair.",
                "",
                "Required output object:",
                "",
                "```json",
                json.dumps(
                    {
                        "pair_id": "same pair_id",
                        "patient_id": "same patient_id",
                        "trial_id": "same trial_id",
                        "eligibility": "eligible|ineligible|uncertain",
                        "criterion_results": [
                            {
                                "criterion_id": "same listed criterion_id",
                                "status": "satisfied|violated|unknown|not_applicable",
                                "reason": "short reason grounded in supplied patient/trial text",
                            }
                        ],
                        "follow_up_questions": ["short questions for unknown required facts"],
                        "rationale": "short final rationale",
                    },
                    indent=2,
                ),
                "```",
                "",
                TEACHER_SYSTEM_PROMPT,
            ]
        ),
        encoding="utf-8",
    )


def label_with_deterministic_baseline(pairs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    labels = []
    for pair in pairs:
        patient = Patient.from_mapping(pair["patient_profile"])
        trial = Trial.from_mapping(pair["trial"])
        recommendation = evaluate_trial(patient, trial)
        criterion_results = baseline_criterion_results(pair, recommendation)
        eligibility = aggregate_eligibility(criterion_results)
        labels.append(
            {
                "pair_id": pair["pair_id"],
                "patient_id": pair["patient_id"],
                "trial_id": pair["trial_id"],
                "eligibility": eligibility,
                "criterion_results": criterion_results,
                "follow_up_questions": [
                    question_for_pair_criterion(item)
                    for item in criterion_results
                    if item["status"] == "unknown"
                ],
                "rationale": baseline_rationale(eligibility, criterion_results),
                "source": "deterministic_baseline",
            }
        )
    return labels


def baseline_criterion_results(
    pair: dict[str, Any],
    recommendation: Any,
) -> list[dict[str, str]]:
    evidence_by_criterion = {item.criterion: item for item in recommendation.evidence}
    return [
        baseline_criterion_result(criterion, evidence_by_criterion)
        for criterion in pair.get("criteria", [])
    ]


def baseline_criterion_result(
    criterion: dict[str, Any],
    evidence_by_criterion: dict[str, Any],
) -> dict[str, str]:
    evidence_keys = evidence_keys_for_pair_criterion(criterion)
    evidence = next(
        (evidence_by_criterion[key] for key in evidence_keys if key in evidence_by_criterion),
        None,
    )
    if evidence is None:
        return {
            "criterion_id": str(criterion.get("criterion_id") or ""),
            "status": "unknown",
            "reason": "The deterministic baseline did not produce evidence for this listed criterion.",
        }
    return {
        "criterion_id": str(criterion.get("criterion_id") or ""),
        "status": baseline_status(evidence.status),
        "reason": evidence.detail,
    }


def evidence_keys_for_pair_criterion(criterion: dict[str, Any]) -> list[str]:
    criterion_id = str(criterion.get("criterion_id") or "")
    structured = criterion.get("structured_value")
    suffix = criterion_id.split("-", 1)[1] if "-" in criterion_id else criterion_id
    if suffix == "I-condition":
        return ["condition", "field:diagnosis"]
    if suffix == "I-age":
        return ["age", "field:age"]
    if suffix == "I-sex":
        return ["sex", "field:sex"]
    if suffix == "I-stage":
        return ["stage", "field:stage"]
    if suffix == "I-ecog":
        return ["ecog", "field:ecog"]
    if suffix.startswith("I-biomarker-") and isinstance(structured, dict):
        return [f"biomarker:{marker}" for marker in structured]
    if suffix.startswith("I-prior-"):
        return [f"prior_treatment:{structured}", "field:prior_treatments"]
    if suffix.startswith("E-"):
        return [f"flag:{structured}"]
    return []


def baseline_status(status: str) -> str:
    return {
        "matched": "satisfied",
        "conflict": "violated",
        "missing": "unknown",
    }.get(status, "unknown")


def question_for_pair_criterion(criterion_result: dict[str, str]) -> str:
    criterion_id = criterion_result.get("criterion_id", "criterion")
    readable = criterion_id.split("-", 1)[1].replace("-", " ") if "-" in criterion_id else criterion_id
    return f"What patient information is available for {readable}?"


def baseline_rationale(
    eligibility: str,
    criterion_results: list[dict[str, str]],
) -> str:
    counts = Counter(item["status"] for item in criterion_results)
    if eligibility == "eligible":
        return f"All {counts['satisfied']} listed required criteria were satisfied."
    if eligibility == "ineligible":
        return f"{counts['violated']} listed criterion conflicts were found."
    return f"{counts['unknown']} listed criteria need more information."


def label_with_friendli(
    *,
    pairs: list[dict[str, Any]],
    env_file: Path | None,
    batch_size: int,
    concurrency: int,
    request_timeout_sec: int,
    max_tokens: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    config = FriendliConfig.from_env(env_file)
    if not config.configured:
        raise ValueError(f"Missing K-EXAONE configuration: {', '.join(config.missing)}")
    batches = chunked(pairs, batch_size)
    labels: list[dict[str, Any]] = []
    calls: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=max(1, concurrency)) as executor:
        futures = {
            executor.submit(
                call_friendli_batch,
                config,
                batch,
                request_timeout_sec,
                max_tokens,
            ): batch
            for batch in batches
        }
        for future in as_completed(futures):
            batch = futures[future]
            call, batch_labels = future.result()
            calls.append(call)
            labels.extend(batch_labels)
            missing = {
                pair["pair_id"]
                for pair in batch
            } - {label.get("pair_id", "") for label in batch_labels}
            for pair_id in sorted(missing):
                labels.append(fallback_label_for_pair(pair_id, batch, call))
    return sorted(labels, key=lambda item: item.get("pair_id", "")), calls


def call_friendli_batch(
    config: FriendliConfig,
    batch: list[dict[str, Any]],
    request_timeout_sec: int,
    max_tokens: int,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    client = FriendliClient(config, timeout_sec=request_timeout_sec)
    started = time.perf_counter()
    result = client.chat(
        labeler_messages(batch),
        max_tokens=max_tokens,
        temperature=0,
        enable_thinking=False,
        parse_reasoning=True,
    )
    labels = parse_label_output(result.content, expected_pair_ids=[p["pair_id"] for p in batch])
    return (
        {
            "provider": "friendli",
            "ok": result.ok,
            "http_status": result.http_status,
            "retry_after": result.retry_after,
            "ms": result.ms or elapsed_ms(started),
            "label_count": len(labels),
            "error": result.error,
            "content_preview": result.content[:700],
        },
        labels,
    )


def label_with_openai(
    *,
    pairs: list[dict[str, Any]],
    env_file: Path | None,
    batch_size: int,
    concurrency: int,
    request_timeout_sec: int,
    max_tokens: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    config = OpenAIChatConfig.from_env(env_file)
    if not config.configured:
        raise ValueError(f"Missing GPT teacher configuration: {', '.join(config.missing)}")
    batches = chunked(pairs, batch_size)
    labels: list[dict[str, Any]] = []
    calls: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=max(1, concurrency)) as executor:
        futures = {
            executor.submit(
                call_openai_batch,
                config,
                batch,
                request_timeout_sec,
                max_tokens,
            ): batch
            for batch in batches
        }
        for future in as_completed(futures):
            batch = futures[future]
            call, batch_labels = future.result()
            calls.append(call)
            labels.extend(batch_labels)
            missing = {
                pair["pair_id"]
                for pair in batch
            } - {label.get("pair_id", "") for label in batch_labels}
            for pair_id in sorted(missing):
                labels.append(fallback_label_for_pair(pair_id, batch, call))
    return sorted(labels, key=lambda item: item.get("pair_id", "")), calls


def call_openai_batch(
    config: OpenAIChatConfig,
    batch: list[dict[str, Any]],
    request_timeout_sec: int,
    max_tokens: int,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    client = OpenAIChatClient(config, timeout_sec=request_timeout_sec)
    result = client.chat(
        labeler_messages(batch),
        max_tokens=max_tokens,
        temperature=0,
    )
    labels = parse_label_output(result.content, expected_pair_ids=[p["pair_id"] for p in batch])
    return (
        {
            "provider": "openai",
            "ok": result.ok,
            "http_status": result.http_status,
            "retry_after": result.retry_after,
            "ms": result.ms,
            "label_count": len(labels),
            "error": result.error,
            "content_preview": result.content[:700],
        },
        labels,
    )


def labeler_messages(batch: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": TEACHER_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": "\n".join(
                [
                    "Label these synthetic patient-trial pairs.",
                    "Return JSONL only.",
                    "Input JSON:",
                    json.dumps(batch, ensure_ascii=False, sort_keys=True),
                ]
            ),
        },
    ]


def parse_label_output(content: str, expected_pair_ids: list[str]) -> list[dict[str, Any]]:
    text = strip_markdown(content)
    labels = parse_json_array_or_object(text)
    if not labels:
        labels = parse_json_lines(text)
    expected = set(expected_pair_ids)
    normalized = []
    seen = set()
    for item in labels:
        if not isinstance(item, dict):
            continue
        pair_id = str(item.get("pair_id") or "")
        if pair_id not in expected or pair_id in seen:
            continue
        seen.add(pair_id)
        normalized.append(normalize_label(item))
    return normalized


def parse_json_array_or_object(text: str) -> list[Any]:
    candidates = [text]
    sliced = slice_json(text, "[", "]")
    if sliced:
        candidates.append(sliced)
    object_sliced = slice_json(text, "{", "}")
    if object_sliced:
        candidates.append(object_sliced)
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, dict):
            for key in ["labels", "results", "items"]:
                if isinstance(parsed.get(key), list):
                    return parsed[key]
            return [parsed]
    return []


def parse_json_lines(text: str) -> list[Any]:
    items = []
    for raw_line in text.splitlines():
        line = raw_line.strip().strip(",")
        if not line or not line.startswith("{"):
            continue
        try:
            items.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return items


def normalize_label(item: dict[str, Any]) -> dict[str, Any]:
    eligibility = str(item.get("eligibility") or "").strip().lower()
    if eligibility not in ELIGIBILITY_LABELS:
        eligibility = "uncertain"
    criteria = []
    for criterion in item.get("criterion_results") or []:
        if not isinstance(criterion, dict):
            continue
        status = str(criterion.get("status") or "").strip().lower()
        if status not in CRITERION_LABELS:
            status = "unknown"
        criteria.append(
            {
                "criterion_id": str(criterion.get("criterion_id") or ""),
                "status": status,
                "reason": str(criterion.get("reason") or "")[:500],
            }
        )
    return {
        "pair_id": str(item.get("pair_id") or ""),
        "patient_id": str(item.get("patient_id") or ""),
        "trial_id": str(item.get("trial_id") or ""),
        "eligibility": eligibility,
        "criterion_results": criteria,
        "follow_up_questions": [
            str(question)[:300]
            for question in (item.get("follow_up_questions") or [])
            if str(question).strip()
        ],
        "rationale": str(item.get("rationale") or "")[:1000],
        "source": str(item.get("source") or "llm"),
    }


def fallback_label_for_pair(
    pair_id: str,
    batch: list[dict[str, Any]],
    call: dict[str, Any],
) -> dict[str, Any]:
    pair = next(pair for pair in batch if pair["pair_id"] == pair_id)
    return {
        "pair_id": pair_id,
        "patient_id": pair["patient_id"],
        "trial_id": pair["trial_id"],
        "eligibility": "uncertain",
        "criterion_results": [
            {
                "criterion_id": criterion["criterion_id"],
                "status": "unknown",
                "reason": "Model output was missing or unparsable for this pair.",
            }
            for criterion in pair.get("criteria", [])
        ],
        "follow_up_questions": ["Repeat the eligibility review with a valid structured output."],
        "rationale": "Fallback label caused by missing model output.",
        "source": "fallback",
        "call_error": call.get("error", ""),
    }


def compare_teacher_student(
    *,
    pairs: list[dict[str, Any]],
    teacher_labels: list[dict[str, Any]],
    student_labels: list[dict[str, Any]],
) -> dict[str, Any]:
    pairs_by_id = {pair["pair_id"]: pair for pair in pairs}
    teacher_by_id = {label["pair_id"]: label for label in teacher_labels}
    student_by_id = {label["pair_id"]: label for label in student_labels}
    comparable_ids = sorted(set(teacher_by_id) & set(student_by_id))
    rows = []
    scenario_stats: dict[str, Counter] = defaultdict(Counter)
    teacher_distribution = Counter()
    student_distribution = Counter()
    criterion_compared = 0
    criterion_agreed = 0

    for pair_id in comparable_ids:
        pair = pairs_by_id.get(pair_id, {})
        teacher = teacher_by_id[pair_id]
        student = student_by_id[pair_id]
        teacher_label = teacher.get("eligibility", "")
        student_label = student.get("eligibility", "")
        teacher_distribution[teacher_label] += 1
        student_distribution[student_label] += 1
        label_agrees = teacher_label == student_label
        scenario = str(pair.get("scenario") or "")
        scenario_stats[scenario]["count"] += 1
        scenario_stats[scenario]["eligibility_agree"] += int(label_agrees)

        teacher_criteria = {
            item.get("criterion_id"): item.get("status")
            for item in teacher.get("criterion_results", [])
        }
        student_criteria = {
            item.get("criterion_id"): item.get("status")
            for item in student.get("criterion_results", [])
        }
        common_criteria = sorted(set(teacher_criteria) & set(student_criteria))
        row_criterion_agreed = sum(
            teacher_criteria[criterion_id] == student_criteria[criterion_id]
            for criterion_id in common_criteria
        )
        criterion_compared += len(common_criteria)
        criterion_agreed += row_criterion_agreed
        rows.append(
            {
                "pair_id": pair_id,
                "patient_id": pair.get("patient_id", ""),
                "trial_id": pair.get("trial_id", ""),
                "scenario": scenario,
                "teacher_eligibility": teacher_label,
                "student_eligibility": student_label,
                "eligibility_agrees": label_agrees,
                "criterion_compared": len(common_criteria),
                "criterion_agreed": row_criterion_agreed,
                "teacher_rationale": teacher.get("rationale", ""),
                "student_rationale": student.get("rationale", ""),
            }
        )

    pair_count = len(comparable_ids)
    disagreements = [row for row in rows if not row["eligibility_agrees"]]
    return {
        "summary": {
            "pair_count": pair_count,
            "teacher_label_count": len(teacher_labels),
            "student_label_count": len(student_labels),
            "eligibility_agreement": ratio(
                sum(row["eligibility_agrees"] for row in rows),
                pair_count,
            ),
            "criterion_status_agreement": ratio(criterion_agreed, criterion_compared),
            "criterion_compared": criterion_compared,
            "teacher_distribution": dict(teacher_distribution),
            "student_distribution": dict(student_distribution),
            "disagreement_count": len(disagreements),
        },
        "scenario_summary": {
            scenario: {
                "count": counts["count"],
                "eligibility_agreement": ratio(
                    counts["eligibility_agree"],
                    counts["count"],
                ),
            }
            for scenario, counts in sorted(scenario_stats.items())
        },
        "disagreements": disagreements[:30],
        "rows": rows,
    }


def build_markdown_report(comparison: dict[str, Any], calls: dict[str, list[dict[str, Any]]]) -> str:
    summary = comparison["summary"]
    lines = [
        "# Teacher-Student Evaluation",
        "",
        "This evaluation treats the teacher labels as silver labels for a research prototype, not as clinical truth.",
        "",
        "## Summary",
        "",
        f"- patient-trial pairs compared: {summary['pair_count']}",
        f"- eligibility agreement: {summary['eligibility_agreement']}",
        f"- criterion status agreement: {summary['criterion_status_agreement']}",
        f"- disagreements: {summary['disagreement_count']}",
        f"- teacher label distribution: {summary['teacher_distribution']}",
        f"- student label distribution: {summary['student_distribution']}",
        "",
        "## Scenario Summary",
        "",
        "| Scenario | Count | Eligibility agreement |",
        "|---|---:|---:|",
    ]
    for scenario, row in comparison["scenario_summary"].items():
        lines.append(f"| {scenario} | {row['count']} | {row['eligibility_agreement']} |")
    lines.extend(["", "## Model Calls", ""])
    for provider, provider_calls in calls.items():
        ok = sum(1 for call in provider_calls if call.get("ok"))
        lines.append(f"- {provider}: {ok}/{len(provider_calls)} calls ok")
    lines.extend(["", "## First Disagreements", ""])
    for row in comparison["disagreements"][:10]:
        lines.append(
            "- "
            + f"{row['pair_id']}: teacher={row['teacher_eligibility']}, "
            + f"student={row['student_eligibility']}, scenario={row['scenario']}"
        )
    lines.append("")
    return "\n".join(lines)


def strip_markdown(text: str) -> str:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json|jsonl)?", "", cleaned, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()
    return cleaned


def slice_json(text: str, open_marker: str, close_marker: str) -> str:
    start = text.find(open_marker)
    end = text.rfind(close_marker)
    if start == -1 or end == -1 or end <= start:
        return ""
    return text[start : end + 1]


def chunked(values: list[dict[str, Any]], size: int) -> list[list[dict[str, Any]]]:
    return [values[index : index + size] for index in range(0, len(values), max(1, size))]


def ratio(numerator: int | float, denominator: int | float) -> float:
    if not denominator:
        return 0.0
    return round(float(numerator) / float(denominator), 3)


def elapsed_ms(started: float) -> int:
    return round((time.perf_counter() - started) * 1000)


def safe_error_body(error: urllib.error.HTTPError) -> str:
    try:
        return error.read().decode("utf-8", errors="replace")[:1000]
    except OSError:
        return str(error.reason or "HTTP error")


def excerpt(value: str | None, max_chars: int) -> str:
    text = " ".join(str(value or "").split())
    return text[:max_chars]


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "criterion"
