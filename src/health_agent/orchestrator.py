from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from typing import Any

from health_agent.llm_client import ChatResult, FriendliClient
from health_agent.models import Patient, Trial
from health_agent.rag import RetrievedTrial, format_retrieved_context
from health_agent.scoring import evaluate_trial


ALLOWED_DECISIONS = {"recommend", "needs_more_info", "not_recommended"}
CANONICAL_FLAGS = [
    "untreated_brain_metastases",
    "active_interstitial_lung_disease",
    "active_autoimmune_disease",
    "uncontrolled_cardiac_disease",
    "active_uncontrolled_infection",
    "organ_transplant",
]


@dataclass(frozen=True)
class AgentTokenBudget:
    extractor_max_tokens: int = 900
    matcher_max_tokens: int = 1800
    orchestrator_max_tokens: int = 1400


@dataclass(frozen=True)
class ParsedAgentJson:
    ok: bool
    agent_name: str
    value: Any
    error: str = ""
    repaired: bool = False
    content_preview: str = ""


def run_patient_orchestration(
    *,
    patient: Patient,
    note: str,
    retrieved: list[RetrievedTrial],
    all_trials: list[Trial],
    client: FriendliClient | None,
    token_budget: AgentTokenBudget,
) -> dict:
    started = time.perf_counter()
    expected_by_trial = {
        item.trial.trial_id: evaluate_trial(patient, item.trial).decision
        for item in retrieved
    }
    candidate_recall = compute_candidate_recall(patient, all_trials, [item.trial for item in retrieved])

    if client is None:
        labels = deterministic_label_rows(retrieved, expected_by_trial)
        return {
            "patient_id": patient.patient_id,
            "ms": elapsed_ms(started),
            "clinical_note": note,
            "retrieved": [item.as_dict() for item in retrieved],
            "candidateRecall": candidate_recall,
            "agentCalls": {},
            "parsed": {},
            "labels": labels,
        }

    extractor_call = call_agent(
        client,
        "patient_extractor",
        extractor_messages(note, patient.patient_id),
        token_budget.extractor_max_tokens,
    )
    extraction = parse_agent_json(extractor_call.content, "extractor")
    augmented_extraction = augment_extraction_from_note(extraction.value, note, patient.patient_id)

    matcher_call = call_agent(
        client,
        "eligibility_matcher",
        matcher_messages(note, augmented_extraction, retrieved),
        token_budget.matcher_max_tokens,
    )
    matcher_output = parse_agent_json(matcher_call.content, "matcher")

    orchestrator_call = call_agent(
        client,
        "trial_orchestrator",
        orchestrator_messages(note, augmented_extraction, matcher_output.value, retrieved),
        token_budget.orchestrator_max_tokens,
    )
    orchestrator_output = parse_agent_json(orchestrator_call.content, "orchestrator")

    labels = normalize_final_labels(
        orchestrator=orchestrator_output.value,
        matcher=matcher_output.value,
        retrieved_trials=[item.trial for item in retrieved],
        expected_by_trial=expected_by_trial,
    )

    return {
        "patient_id": patient.patient_id,
        "ms": elapsed_ms(started),
        "clinical_note": note,
        "retrieved": [item.as_dict() for item in retrieved],
        "candidateRecall": candidate_recall,
        "agentCalls": {
            "extractor": summarize_call(extractor_call, extraction),
            "matcher": summarize_call(matcher_call, matcher_output),
            "orchestrator": summarize_call(orchestrator_call, orchestrator_output),
        },
        "parsed": {
            "extraction": extraction.value,
            "extraction_augmented": augmented_extraction,
            "matcher": matcher_output.value,
            "orchestrator": orchestrator_output.value,
        },
        "labels": labels,
    }


def call_agent(
    client: FriendliClient,
    agent_name: str,
    messages: list[dict[str, str]],
    max_tokens: int,
) -> ChatResult:
    return client.chat(
        messages,
        max_tokens=max_tokens,
        temperature=0,
        enable_thinking=False,
        parse_reasoning=True,
    )


def extractor_messages(note: str, patient_id: str) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": "\n".join(
                [
                    "You are PatientExtractor in a clinical trial matching research prototype.",
                    "Extract only facts explicitly stated in the patient note.",
                    "Keep biomarker values as strings exactly as stated, including symbols such as %.",
                    "For negated exclusions, use the canonical flag name with false; do not invent no_* flags.",
                    "Use null for unknown scalar fields and [] or {} for unknown collections.",
                    "This is not medical advice. Return JSON only.",
                ]
            ),
        },
        {
            "role": "user",
            "content": "\n".join(
                [
                    "Return JSON with this exact shape:",
                    json.dumps(
                        {
                            "patient_id": patient_id,
                            "age": None,
                            "sex": None,
                            "diagnosis": None,
                            "stage": None,
                            "ecog": None,
                            "biomarkers": {},
                            "prior_treatments": [],
                            "flags": {},
                            "uncertain_fields": [],
                            "source_spans": [],
                        }
                    ),
                    f"Canonical flag names: {', '.join(CANONICAL_FLAGS)}.",
                    "Extraction hints: '62-year-old female' means age 62 and sex female.",
                    "'Stage is recorded as IV' means stage IV.",
                    "'ECOG performance status is 1' means ecog 1.",
                    "",
                    "Patient note:",
                    note,
                ]
            ),
        },
    ]


def matcher_messages(
    note: str,
    extraction: dict[str, Any],
    retrieved: list[RetrievedTrial],
) -> list[dict[str, str]]:
    trial_ids = [item.trial.trial_id for item in retrieved]
    return [
        {
            "role": "system",
            "content": "\n".join(
                [
                    "You are EligibilityMatcher in a clinical trial matching research prototype.",
                    "Compare patient facts against retrieved trial eligibility context.",
                    "Only use the supplied patient note, extracted facts, and RAG trial context.",
                    "Allowed decisions: recommend, needs_more_info, not_recommended.",
                    "Return compact valid JSON only. Do not use markdown.",
                    "This is not medical advice.",
                ]
            ),
        },
        {
            "role": "user",
            "content": "\n".join(
                [
                    "Decision rules:",
                    "- If disease, age, stage, ECOG, biomarker, prior therapy, sex, or exclusion criteria conflict, use not_recommended.",
                    "- If no hard conflict exists but required information is missing, use needs_more_info.",
                    "- If all important criteria match and no exclusion is present, use recommend.",
                    "- Do not infer absent facts from common clinical practice.",
                    "- If the raw patient note states a fact, use it even when the extractor missed that fact.",
                    "- You must output exactly one match object for every retrieved trial_id.",
                    f"- Required trial_id set, in order: {', '.join(trial_ids)}.",
                    "",
                    "Return JSON with this shape:",
                    json.dumps(
                        {
                            "matches": [
                                {
                                    "trial_id": "string",
                                    "decision": "recommend|needs_more_info|not_recommended",
                                    "confidence": 0.0,
                                    "evidence": ["short criterion evidence"],
                                    "missing_fields": [],
                                    "conflicts": [],
                                }
                            ]
                        }
                    ),
                    f"The matches array length must be exactly {len(retrieved)}.",
                    "",
                    "Patient note:",
                    note,
                    "",
                    "Extracted patient facts:",
                    json.dumps(extraction or {}, indent=2, sort_keys=True),
                    "",
                    "RAG trial contexts:",
                    format_retrieved_context(retrieved),
                ]
            ),
        },
    ]


def orchestrator_messages(
    note: str,
    extraction: dict[str, Any],
    matches: Any,
    retrieved: list[RetrievedTrial],
) -> list[dict[str, str]]:
    trial_ids = [item.trial.trial_id for item in retrieved]
    return [
        {
            "role": "system",
            "content": "\n".join(
                [
                    "You are TrialOrchestrator, the final adjudicator for a multi-agent clinical trial matching prototype.",
                    "Resolve obvious matcher errors, preserve uncertainty, and mark human review when evidence is thin.",
                    "Allowed decisions: recommend, needs_more_info, not_recommended.",
                    "Return compact valid JSON only. Do not use markdown.",
                    "This is not medical advice.",
                ]
            ),
        },
        {
            "role": "user",
            "content": "\n".join(
                [
                    "Return JSON with this shape:",
                    json.dumps(
                        {
                            "recommendations": [
                                {
                                    "trial_id": "string",
                                    "decision": "recommend|needs_more_info|not_recommended",
                                    "confidence": 0.0,
                                    "evidence_summary": "short explanation",
                                    "missing_fields": [],
                                    "human_review_required": True,
                                }
                            ]
                        }
                    ),
                    "- You must output exactly one recommendation object for every retrieved trial_id.",
                    f"- Required trial_id set, in order: {', '.join(trial_ids)}.",
                    f"- The recommendations array length must be exactly {len(retrieved)}.",
                    "",
                    "Adjudication rule: if matcher output says a field is missing but the raw patient note states it, correct the matcher.",
                    "Do not downgrade to needs_more_info for explicit age, sex, stage, ECOG, diagnosis, or biomarkers.",
                    "",
                    "Patient note:",
                    note,
                    "",
                    "Extractor output:",
                    json.dumps(extraction or {}, indent=2, sort_keys=True),
                    "",
                    "Matcher output:",
                    json.dumps(matches or {}, indent=2, sort_keys=True),
                    "",
                    "Raw retrieved trial contexts:",
                    format_retrieved_context(retrieved),
                ]
            ),
        },
    ]


def patient_to_clinical_note(patient: Patient, index: int = 0) -> str:
    if patient.clinical_note:
        return patient.clinical_note
    prefix = "Oncology referral note" if index % 2 == 0 else "Tumor board intake"
    age_sex = (
        "Adult patient"
        if patient.age is None or patient.sex is None
        else f"{patient.age}-year-old {patient.sex}"
    )
    diagnosis = (
        f"with {patient.diagnosis}"
        if patient.diagnosis
        else "with cancer diagnosis not clearly documented"
    )
    stage = (
        f"Stage is recorded as {patient.stage}."
        if patient.stage
        else "No formal stage is documented."
    )
    ecog = (
        "ECOG performance status is not documented."
        if patient.ecog is None
        else f"ECOG performance status is {patient.ecog}."
    )
    treatments = (
        f"Prior therapy includes {', '.join(patient.prior_treatments)}."
        if patient.prior_treatments
        else "No prior systemic therapy is listed in the referral."
    )
    location = (
        f"The patient receives care in {patient.location['state']}."
        if patient.location.get("state")
        else ""
    )
    return " ".join(
        item
        for item in [
            f"{prefix}: {patient.patient_id} is a {age_sex} {diagnosis}.",
            stage,
            ecog,
            biomarkers_to_sentence(patient.biomarkers),
            treatments,
            flags_to_sentence(patient.flags),
            location,
            "The note is a synthetic record created for software testing, not a real patient chart.",
        ]
        if item
    )


def biomarkers_to_sentence(biomarkers: dict[str, str]) -> str:
    if not biomarkers:
        return "Molecular testing results are not available in the note."
    return (
        "Molecular testing shows "
        + ", ".join(f"{key} {value}" for key, value in biomarkers.items())
        + "."
    )


def flags_to_sentence(flags: dict[str, bool]) -> str:
    if not flags:
        return "No explicit exclusion comorbidities are addressed."
    phrases = []
    for flag, value in flags.items():
        readable = flag.replace("_", " ")
        phrases.append(
            f"The note reports {readable}."
            if value
            else f"No {readable} is reported."
        )
    return " ".join(phrases)


def parse_agent_json(content: str, agent_name: str) -> ParsedAgentJson:
    if not content or not content.strip():
        return ParsedAgentJson(False, agent_name, None, "empty content")
    cleaned = re.sub(r"^```(?:json)?", "", content.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"```$", "", cleaned, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)
    candidates = [cleaned, repair_json_text(cleaned)]
    object_candidate = slice_json_candidate(cleaned, "{", "}")
    if object_candidate:
        candidates.extend([object_candidate, repair_json_text(object_candidate)])

    last_error = ""
    for candidate in candidates:
        if not candidate:
            continue
        try:
            return ParsedAgentJson(True, agent_name, json.loads(candidate))
        except json.JSONDecodeError as error:
            last_error = str(error)

    if agent_name in {"matcher", "orchestrator"}:
        loose = parse_loose_decision_output(content, agent_name)
        rows = loose.get("matches") or loose.get("recommendations") or []
        if rows:
            return ParsedAgentJson(
                True,
                agent_name,
                loose,
                f"repaired {agent_name} output with loose parser",
                repaired=True,
            )

    return ParsedAgentJson(
        False,
        agent_name,
        None,
        f"Could not parse {agent_name} JSON: {last_error or 'unknown parse error'}",
        content_preview=content[:500],
    )


def repair_json_text(text: str) -> str:
    printable = "".join(
        character
        for character in text
        if character in "\t\n\r" or 32 <= ord(character) <= 126
    )
    lines = []
    for line in printable.replace('"human_ics_required"', '"human_review_required"').splitlines():
        stripped = line.strip()
        if not stripped or re.search(r'[{}\[\]":,]', stripped):
            lines.append(line)
    return re.sub(r",\s*([}\]])", r"\1", "\n".join(lines)).strip()


def parse_loose_decision_output(content: str, agent_name: str) -> dict[str, Any]:
    rows = []
    seen = set()
    pattern = re.compile(
        r'"trial_id"\s*:\s*"([^"]+)"[\s\S]{0,500}?"decision"\s*:\s*"([^"]+)"'
    )
    for match in pattern.finditer(content or ""):
        trial_id = match.group(1)
        decision = normalize_decision(match.group(2))
        if not trial_id or not decision or trial_id in seen:
            continue
        seen.add(trial_id)
        rows.append(
            {
                "trial_id": trial_id,
                "decision": decision,
                "confidence": 0,
                "evidence": [],
                "missing_fields": [],
                "conflicts": [],
                "parse_repaired": True,
            }
        )
    if agent_name == "orchestrator":
        return {
            "recommendations": [
                {
                    "trial_id": item["trial_id"],
                    "decision": item["decision"],
                    "confidence": item["confidence"],
                    "evidence_summary": "",
                    "missing_fields": item["missing_fields"],
                    "human_review_required": True,
                    "parse_repaired": True,
                }
                for item in rows
            ]
        }
    return {"matches": rows}


def augment_extraction_from_note(
    extraction: Any,
    note: str,
    patient_id: str,
) -> dict[str, Any]:
    result = dict(extraction) if isinstance(extraction, dict) else {}
    result.setdefault("patient_id", patient_id)
    age_sex = re.search(r"\b(\d{2,3})-year-old\s+(female|male)\b", note, re.IGNORECASE)
    if age_sex:
        result.setdefault("age", int(age_sex.group(1)))
        result.setdefault("sex", age_sex.group(2).lower())
    diagnosis = re.search(r"\bwith\s+([^.;]+?)(?:\.| Stage| No formal stage)", note, re.IGNORECASE)
    if diagnosis and not result.get("diagnosis"):
        result["diagnosis"] = diagnosis.group(1).strip()
    stage = re.search(r"\bStage is recorded as\s+([A-Za-z0-9]+)", note, re.IGNORECASE)
    if stage and not result.get("stage"):
        result["stage"] = stage.group(1).strip()
    ecog = re.search(r"\bECOG performance status is\s+(\d+)", note, re.IGNORECASE)
    if ecog and result.get("ecog") is None:
        result["ecog"] = int(ecog.group(1))
    biomarkers = result.get("biomarkers") if isinstance(result.get("biomarkers"), dict) else {}
    result["biomarkers"] = {**biomarkers, **extract_biomarkers_from_note(note)}
    result["prior_treatments"] = merge_arrays(
        result.get("prior_treatments"),
        extract_prior_treatments_from_note(note),
    )
    flags = result.get("flags") if isinstance(result.get("flags"), dict) else {}
    result["flags"] = {**flags, **extract_flags_from_note(note)}
    result["local_validator_applied"] = True
    return result


def extract_biomarkers_from_note(note: str) -> dict[str, str]:
    biomarkers: dict[str, str] = {}
    marker_names = [
        "PD-L1",
        "BRCA1",
        "BRCA2",
        "EGFR",
        "ALK",
        "BRAF",
        "HER2",
        "ER",
        "PR",
        "MSI",
        "KRAS",
        "FLT3",
        "NPM1",
    ]
    match = re.search(r"Molecular testing shows\s+([^.]*)\.", note, re.IGNORECASE)
    if not match:
        return biomarkers
    for item in re.split(r"\s*,\s*", match.group(1)):
        marker = next(
            (
                candidate
                for candidate in marker_names
                if item.lower().startswith(candidate.lower() + " ")
            ),
            "",
        )
        if marker:
            biomarkers[marker] = item[len(marker) :].strip()
    return biomarkers


def extract_prior_treatments_from_note(note: str) -> list[str]:
    match = re.search(r"Prior therapy includes\s+([^.]*)\.", note, re.IGNORECASE)
    if not match:
        return []
    return [item.strip() for item in re.split(r"\s*,\s*", match.group(1)) if item.strip()]


def extract_flags_from_note(note: str) -> dict[str, bool]:
    flags: dict[str, bool] = {}
    for flag in CANONICAL_FLAGS:
        readable = re.escape(flag.replace("_", " "))
        if re.search(rf"No {readable} is reported", note, re.IGNORECASE):
            flags[flag] = False
        elif re.search(rf"reports {readable}", note, re.IGNORECASE):
            flags[flag] = True
    return flags


def normalize_final_labels(
    *,
    orchestrator: Any,
    matcher: Any,
    retrieved_trials: list[Trial],
    expected_by_trial: dict[str, str],
) -> list[dict[str, Any]]:
    by_trial: dict[str, tuple[str, dict[str, Any]]] = {}
    matcher_rows = matcher.get("matches", []) if isinstance(matcher, dict) else []
    orchestrator_rows = (
        orchestrator.get("recommendations", []) if isinstance(orchestrator, dict) else []
    )
    for item in matcher_rows:
        if isinstance(item, dict):
            by_trial[str(item.get("trial_id", ""))] = ("matcher", item)
    for item in orchestrator_rows:
        if isinstance(item, dict):
            by_trial[str(item.get("trial_id", ""))] = ("orchestrator", item)

    labels = []
    for trial in retrieved_trials:
        source, item = by_trial.get(trial.trial_id, ("missing", {}))
        raw_decision = str(item.get("decision", ""))
        decision = normalize_decision(raw_decision)
        fallback = False
        if not decision:
            decision = expected_by_trial.get(trial.trial_id, "")
            source = "deterministic_fallback"
            fallback = True
        expected = expected_by_trial.get(trial.trial_id, "")
        labels.append(
            {
                "trial_id": trial.trial_id,
                "title": trial.title,
                "source": source,
                "decision": decision,
                "raw_decision": raw_decision,
                "expected_label": expected,
                "agrees": bool(decision and decision == expected),
                "confidence": read_number(item.get("confidence")),
                "missing_fields": as_string_array(item.get("missing_fields")),
                "conflicts": as_string_array(item.get("conflicts")),
                "human_review_required": bool(item.get("human_review_required")) or fallback,
                "evidence_summary": str(
                    item.get("evidence_summary")
                    or item.get("rationale")
                    or "; ".join(as_string_array(item.get("evidence")))
                    or ""
                ),
                "fallback": fallback,
            }
        )
    return labels


def deterministic_label_rows(
    retrieved: list[RetrievedTrial],
    expected_by_trial: dict[str, str],
) -> list[dict[str, Any]]:
    return [
        {
            "trial_id": item.trial.trial_id,
            "title": item.trial.title,
            "source": "deterministic_baseline",
            "decision": expected_by_trial[item.trial.trial_id],
            "raw_decision": expected_by_trial[item.trial.trial_id],
            "expected_label": expected_by_trial[item.trial.trial_id],
            "agrees": True,
            "confidence": 1.0,
            "missing_fields": [],
            "conflicts": [],
            "human_review_required": False,
            "evidence_summary": "",
            "fallback": False,
        }
        for item in retrieved
    ]


def compute_candidate_recall(
    patient: Patient,
    trials: list[Trial],
    retrieved_trials: list[Trial],
) -> dict[str, Any]:
    retrieved_ids = {trial.trial_id for trial in retrieved_trials}
    expected_recommend = [
        trial.trial_id
        for trial in trials
        if evaluate_trial(patient, trial).decision == "recommend"
    ]
    expected_potential = [
        trial.trial_id
        for trial in trials
        if evaluate_trial(patient, trial).decision != "not_recommended"
    ]
    recommend_hits = [trial_id for trial_id in expected_recommend if trial_id in retrieved_ids]
    potential_hits = [trial_id for trial_id in expected_potential if trial_id in retrieved_ids]
    return {
        "expectedRecommend": expected_recommend,
        "expectedPotential": expected_potential,
        "recommendHitCount": len(recommend_hits),
        "potentialHitCount": len(potential_hits),
        "recommendRecall": ratio(len(recommend_hits), len(expected_recommend)),
        "potentialRecall": ratio(len(potential_hits), len(expected_potential)),
    }


def build_eval_report(
    *,
    started: float,
    synthetic_patients: int,
    synthetic_trials: int,
    evaluated_patients: int,
    top_k: int,
    dry_run: bool,
    results: list[dict],
) -> dict[str, Any]:
    all_calls = [
        call
        for result in results
        for call in result.get("agentCalls", {}).values()
    ]
    all_labels = [label for result in results for label in result.get("labels", [])]
    statuses: dict[str, int] = {}
    for call in all_calls:
        key = str(call.get("httpStatus", ""))
        statuses[key] = statuses.get(key, 0) + 1
    call_latencies = sorted(
        int(call.get("ms", 0)) for call in all_calls if isinstance(call.get("ms"), int)
    )
    valid_labels = [label for label in all_labels if label.get("decision") in ALLOWED_DECISIONS]
    agreements = [label for label in valid_labels if label.get("agrees")]
    summary = {
        "elapsedSec": round_number(max(1, time.perf_counter() - started)),
        "dryRun": dry_run,
        "syntheticPatients": synthetic_patients,
        "syntheticTrials": synthetic_trials,
        "evaluatedPatients": evaluated_patients,
        "topK": top_k,
        "agentCalls": len(all_calls),
        "failedAgentCalls": len([call for call in all_calls if not call.get("ok")]),
        "jsonParseRate": ratio(
            len([call for call in all_calls if call.get("jsonOk")]),
            len(all_calls),
        ),
        "statuses": statuses,
        "labelCount": len(all_labels),
        "validLabelCount": len(valid_labels),
        "validLabelRate": ratio(len(valid_labels), len(all_labels)),
        "agreementRate": ratio(len(agreements), len(valid_labels)),
        "fallbackLabelRate": ratio(
            len([label for label in all_labels if label.get("fallback")]),
            len(all_labels),
        ),
        "p50AgentLatencyMs": percentile(call_latencies, 0.5),
        "p95AgentLatencyMs": percentile(call_latencies, 0.95),
        "retryAfterValues": sorted(
            {
                str(call.get("retryAfter"))
                for call in all_calls
                if call.get("retryAfter")
            }
        ),
    }
    return {"summary": summary, "results": results}


def labels_to_tsv(results: list[dict]) -> str:
    lines = ["PATIENT_ID\tTRIAL_ID\tLABEL\tSOURCE\tAGREES\tHUMAN_REVIEW_REQUIRED"]
    for result in results:
        patient_id = result.get("patient_id", "")
        for label in result.get("labels", []):
            lines.append(
                "\t".join(
                    [
                        str(patient_id),
                        str(label.get("trial_id", "")),
                        str(label.get("decision", "")),
                        str(label.get("source", "")),
                        "1" if label.get("agrees") else "0",
                        "1" if label.get("human_review_required") else "0",
                    ]
                )
            )
    return "\n".join(lines) + "\n"


def summarize_call(call: ChatResult, parsed: ParsedAgentJson) -> dict[str, Any]:
    return {
        "ok": call.ok,
        "httpStatus": call.http_status,
        "retryAfter": call.retry_after,
        "ms": call.ms,
        "jsonOk": parsed.ok,
        "repaired": parsed.repaired,
        "error": call.error or parsed.error,
        "contentPreview": sanitize_report_text(call.content, 700),
        "content": sanitize_report_text(call.content, 4000),
    }


def normalize_decision(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text == "recommend":
        return "recommend"
    if text in {"needs_more_info", "needs more info", "needs-more-info"}:
        return "needs_more_info"
    if text in {"not_recommended", "not recommended", "not-recommended"}:
        return "not_recommended"
    return ""


def sanitize_report_text(value: Any, max_length: int) -> str:
    text = str(value or "")
    text = "".join(
        character
        for character in text
        if character in "\t\n\r" or 32 <= ord(character) <= 126
    )
    return text[:max_length]


def slice_json_candidate(text: str, open_marker: str, close_marker: str) -> str:
    start = text.find(open_marker)
    end = text.rfind(close_marker)
    if start == -1 or end == -1 or end <= start:
        return ""
    return text[start : end + 1]


def merge_arrays(left: Any, right: list[str]) -> list[str]:
    values = []
    for item in list(left if isinstance(left, list) else []) + right:
        if item not in values:
            values.append(item)
    return values


def as_string_array(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def read_number(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0
    return number if number == number else 0


def percentile(values: list[int], percentile_value: float) -> int | None:
    if not values:
        return None
    index = int((len(values) - 1) * percentile_value)
    return values[index]


def ratio(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 1.0
    return round_number(numerator / denominator)


def round_number(value: float) -> float:
    return round(float(value), 3)


def elapsed_ms(started: float) -> int:
    return round((time.perf_counter() - started) * 1000)

