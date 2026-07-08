from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from health_agent.exaone_e2e import PROMPT_VERSION, run_exaone_e2e_orchestration
from health_agent.llm_client import FriendliClient, FriendliConfig


def main() -> None:
    args = parse_args()
    started = time.perf_counter()
    config = FriendliConfig.from_env(args.env_file)
    if not config.configured:
        print(
            json.dumps(
                {
                    "error": "missing_api_configuration",
                    "missing": config.missing,
                    "hint": "Pass --env-file pointing to a local .env, or set OS env vars.",
                },
                indent=2,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        raise SystemExit(2)
    if not args.confirm_live_exaone_api:
        print(
            json.dumps(
                {
                    "error": "live_exaone_api_confirmation_required",
                    "hint": "Re-run with --confirm-live-exaone-api after the user approves the live API call.",
                    "runnerAnswerKeyAccess": False,
                },
                indent=2,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        raise SystemExit(3)

    input_records = read_jsonl(args.input)
    if args.max_patients is not None:
        input_records = input_records[: args.max_patients]
    existing_records = read_jsonl(args.output_jsonl) if args.resume and args.output_jsonl.exists() else []
    existing_by_patient = {record["patient_id"]: record for record in existing_records if record.get("patient_id")}
    pending = [record for record in input_records if record["patient_id"] not in existing_by_patient]

    args.output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    args.raw_output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    args.audit_output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    if not args.resume or not args.output_jsonl.exists():
        args.output_jsonl.write_text("", encoding="utf-8")
        args.raw_output_jsonl.write_text("", encoding="utf-8")
        args.audit_output_jsonl.write_text("", encoding="utf-8")
        existing_records = []
        existing_by_patient = {}
    write_json(args.manifest, build_manifest(args, config, input_records, pending))

    print(
        json.dumps(
            {
                "mode": "k-exaone-pure-e2e-orchestration",
                "configured": config.public_status(),
                "inputPatientCount": len(input_records),
                "alreadyCompleted": len(existing_by_patient),
                "pending": len(pending),
                "concurrency": args.concurrency,
                "maxTokens": args.max_tokens,
                "runnerAnswerKeyAccess": False,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )

    results = list(existing_by_patient.values())
    with ThreadPoolExecutor(max_workers=max(1, args.concurrency)) as executor:
        futures = {
            executor.submit(
                run_one,
                record,
                config,
                args.request_timeout_sec,
                args.max_tokens,
                args.max_excerpt_chars,
            ): record
            for record in pending
        }
        with args.output_jsonl.open("a", encoding="utf-8", newline="\n") as handle, args.raw_output_jsonl.open(
            "a", encoding="utf-8", newline="\n"
        ) as raw_handle, args.audit_output_jsonl.open("a", encoding="utf-8", newline="\n") as audit_handle:
            for future in as_completed(futures):
                record = futures[future]
                patient_id = record["patient_id"]
                try:
                    prediction = future.result()
                except Exception as exc:  # pragma: no cover - defensive CLI guard
                    prediction = error_prediction(record, str(exc))
                handle.write(json.dumps(prediction, ensure_ascii=False, sort_keys=True))
                handle.write("\n")
                handle.flush()
                raw_handle.write(json.dumps(raw_response_row(prediction), ensure_ascii=False, sort_keys=True))
                raw_handle.write("\n")
                raw_handle.flush()
                audit_handle.write(json.dumps(audit_row(prediction), ensure_ascii=False, sort_keys=True))
                audit_handle.write("\n")
                audit_handle.flush()
                results.append(prediction)
                call = prediction.get("agent_trace", {}).get("exaone_call", {})
                print(
                    json.dumps(
                        {
                            "checkpoint": {
                                "patient_id": patient_id,
                                "completed": len(results),
                                "total": len(input_records),
                                "http_status": call.get("http_status"),
                                "json_ok": call.get("json_ok"),
                                "ms": call.get("ms"),
                            }
                        },
                        ensure_ascii=False,
                        sort_keys=True,
                    )
                )

    results = dedupe_and_sort(results)
    write_json(
        args.output_json,
        {
            "schema_version": "health-agent-e2e-orchestration-v2-batch",
            "runner": "k-exaone-pure-single-call",
            "patient_count": len(results),
            "patients": results,
        },
    )
    summary = build_summary(results, started)
    write_json(args.summary, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run K-EXAONE pure single-call E2E orchestration on blinded input. This runner does not accept an answer-key argument."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=ROOT / "artifacts" / "e2e-orchestration-eval" / "blinded_input_100.jsonl",
    )
    parser.add_argument("--env-file", type=Path, default=None)
    parser.add_argument(
        "--output-jsonl",
        type=Path,
        default=ROOT / "outputs" / "exaone_e2e_predictions.jsonl",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=ROOT / "outputs" / "exaone_e2e_predictions.json",
    )
    parser.add_argument(
        "--summary",
        type=Path,
        default=ROOT / "outputs" / "exaone_e2e_predictions_summary.json",
    )
    parser.add_argument(
        "--raw-output-jsonl",
        type=Path,
        default=ROOT / "outputs" / "exaone_e2e_raw_responses.jsonl",
    )
    parser.add_argument(
        "--audit-output-jsonl",
        type=Path,
        default=ROOT / "outputs" / "exaone_e2e_normalization_audit.jsonl",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=ROOT / "outputs" / "exaone_e2e_run_manifest.json",
    )
    parser.add_argument("--max-patients", type=int, default=None)
    parser.add_argument("--concurrency", type=int, default=2)
    parser.add_argument("--request-timeout-sec", type=int, default=300)
    parser.add_argument("--max-tokens", type=int, default=5000)
    parser.add_argument("--max-excerpt-chars", type=int, default=1200)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument(
        "--confirm-live-exaone-api",
        action="store_true",
        help="Required guard acknowledging that this command will call the live Friendli/K-EXAONE API.",
    )
    return parser.parse_args()


def run_one(
    record: dict[str, Any],
    config: FriendliConfig,
    request_timeout_sec: int,
    max_tokens: int,
    max_excerpt_chars: int,
) -> dict[str, Any]:
    client = FriendliClient(config, timeout_sec=request_timeout_sec)
    return run_exaone_e2e_orchestration(
        record,
        client=client,
        max_tokens=max_tokens,
        max_excerpt_chars=max_excerpt_chars,
    )


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                records.append(json.loads(line))
    return records


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"))


def dedupe_and_sort(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_patient = {}
    for record in records:
        patient_id = record.get("patient_id")
        if patient_id:
            by_patient[patient_id] = record
    return [by_patient[key] for key in sorted(by_patient)]


def build_summary(predictions: list[dict[str, Any]], started: float) -> dict[str, Any]:
    eligibility = Counter()
    criterion_status = Counter()
    http_statuses = Counter()
    latencies = []
    json_ok = 0
    call_ok = 0
    question_count = 0
    final_trial_count = 0
    audit_totals = Counter()
    for prediction in predictions:
        final = prediction.get("final_output", {})
        question_count += len(final.get("follow_up_questions", []))
        for row in final.get("final_assessment_after_answers", {}).get("evaluated_trials", []):
            final_trial_count += 1
            eligibility[row.get("eligibility", "")] += 1
            for criterion in row.get("criterion_results", []):
                criterion_status[criterion.get("status", "")] += 1
        call = prediction.get("agent_trace", {}).get("exaone_call", {})
        http_statuses[str(call.get("http_status", ""))] += 1
        if call.get("ok"):
            call_ok += 1
        if call.get("json_ok"):
            json_ok += 1
        if isinstance(call.get("ms"), int):
            latencies.append(int(call["ms"]))
        audit = prediction.get("agent_trace", {}).get("exaone_normalization_audit", {})
        for key, value in audit.items():
            if isinstance(value, bool):
                audit_totals[key] += int(value)
            elif isinstance(value, int):
                audit_totals[key] += value
    latencies.sort()
    return {
        "schema_version": "health-agent-exaone-e2e-summary-v1",
        "runner": "k-exaone-pure-single-call",
        "patient_count": len(predictions),
        "final_trial_judgment_count": final_trial_count,
        "follow_up_question_count": question_count,
        "eligibility_distribution": dict(sorted(eligibility.items())),
        "criterion_status_distribution": dict(sorted(criterion_status.items())),
        "call_ok_rate": ratio(call_ok, len(predictions)),
        "json_parse_rate": ratio(json_ok, len(predictions)),
        "http_statuses": dict(sorted(http_statuses.items())),
        "p50_latency_ms": percentile(latencies, 0.5),
        "p95_latency_ms": percentile(latencies, 0.95),
        "normalization_audit_totals": dict(sorted(audit_totals.items())),
        "elapsed_sec": round(max(0.001, time.perf_counter() - started), 3),
        "runner_answer_key_access": False,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
    }


def build_manifest(
    args: argparse.Namespace,
    config: FriendliConfig,
    input_records: list[dict[str, Any]],
    pending: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "schema_version": "health-agent-exaone-run-manifest-v1",
        "runner": "k-exaone-pure-single-call",
        "provider": "Friendli",
        "model": config.model,
        "chat_completions_url": config.chat_completions_url,
        "prompt_version": PROMPT_VERSION,
        "code_version": git_head(),
        "input": str(args.input),
        "input_sha256": sha256_file(args.input) if args.input.exists() else "",
        "input_patient_count": len(input_records),
        "pending_patient_count": len(pending),
        "temperature": 0,
        "max_tokens": args.max_tokens,
        "max_excerpt_chars": args.max_excerpt_chars,
        "request_timeout_sec": args.request_timeout_sec,
        "concurrency": args.concurrency,
        "output_jsonl": str(args.output_jsonl),
        "raw_output_jsonl": str(args.raw_output_jsonl),
        "audit_output_jsonl": str(args.audit_output_jsonl),
        "runner_answer_key_access": False,
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
    }


def raw_response_row(prediction: dict[str, Any]) -> dict[str, Any]:
    call = prediction.get("agent_trace", {}).get("exaone_call", {})
    return {
        "patient_id": prediction.get("patient_id", ""),
        "ok": call.get("ok"),
        "http_status": call.get("http_status"),
        "ms": call.get("ms"),
        "finish_reason": call.get("finish_reason"),
        "json_ok": call.get("json_ok"),
        "json_repaired": call.get("json_repaired"),
        "error": call.get("error", ""),
        "content": call.get("content", ""),
    }


def audit_row(prediction: dict[str, Any]) -> dict[str, Any]:
    call = prediction.get("agent_trace", {}).get("exaone_call", {})
    audit = prediction.get("agent_trace", {}).get("exaone_normalization_audit", {})
    return {
        "patient_id": prediction.get("patient_id", ""),
        "ok": call.get("ok"),
        "http_status": call.get("http_status"),
        "json_ok": call.get("json_ok"),
        "json_repaired": call.get("json_repaired"),
        **audit,
    }


def ratio(numerator: int, denominator: int) -> float:
    return 0.0 if denominator == 0 else round(numerator / denominator, 4)


def percentile(values: list[int], percentile_value: float) -> int | None:
    if not values:
        return None
    index = int((len(values) - 1) * percentile_value)
    return values[index]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_head() -> str:
    git_dir = ROOT / ".git"
    head = git_dir / "HEAD"
    if not head.exists():
        return ""
    text = head.read_text(encoding="utf-8").strip()
    if text.startswith("ref: "):
        ref = git_dir / text.removeprefix("ref: ").strip()
        return ref.read_text(encoding="utf-8").strip() if ref.exists() else ""
    return text


def error_prediction(input_record: dict[str, Any], error: str) -> dict[str, Any]:
    patient_id = input_record["patient_id"]
    final_rows = []
    for trial in input_record.get("candidate_trials", []):
        criteria = [
            {
                "criterion_id": criterion["criterion_id"],
                "status": "unknown",
                "reason": "K-EXAONE runner raised an exception before this criterion could be judged.",
            }
            for criterion in trial.get("criteria_to_assess", [])
        ]
        final_rows.append(
            {
                "trial_id": trial["trial_id"],
                "trial_title": trial.get("trial_title") or trial.get("title", ""),
                "trial_source_url": trial.get("trial_source_url") or trial.get("source_url", ""),
                "eligibility": "uncertain",
                "criterion_results": criteria,
                "related_question_ids": [],
                "explanation": "K-EXAONE runner exception; eligibility is unresolved.",
                "source": "k-exaone-runner-exception",
                "patient_id": patient_id,
            }
        )
    return {
        "schema_version": "health-agent-e2e-orchestration-v2",
        "runner": "k-exaone-pure-single-call",
        "patient_id": patient_id,
        "patient_information_string": input_record.get("patient_information_string", ""),
        "candidate_trials": input_record.get("candidate_trials", []),
        "agent_trace": {
            "exaone_call": {
                "ok": False,
                "http_status": "CLIENT_EXCEPTION",
                "retry_after": "",
                "ms": 0,
                "finish_reason": "",
                "error": error,
                "json_ok": False,
                "json_repaired": False,
                "content_preview": "",
                "content": "",
            },
            "exaone_normalization_audit": {
                "prompt_version": PROMPT_VERSION,
                "raw_json_valid": False,
                "parse_repaired": False,
                "initial_missing_trials_filled": len(final_rows),
                "final_missing_trials_filled": len(final_rows),
                "initial_extra_trial_ids_dropped": 0,
                "final_extra_trial_ids_dropped": 0,
                "initial_missing_criteria_filled": sum(len(row["criterion_results"]) for row in final_rows),
                "final_missing_criteria_filled": sum(len(row["criterion_results"]) for row in final_rows),
                "initial_extra_criterion_ids_dropped": 0,
                "final_extra_criterion_ids_dropped": 0,
                "initial_fallback_eligibility_count": len(final_rows),
                "final_fallback_eligibility_count": len(final_rows),
                "initial_fallback_criterion_status_count": sum(len(row["criterion_results"]) for row in final_rows),
                "final_fallback_criterion_status_count": sum(len(row["criterion_results"]) for row in final_rows),
            },
        },
        "final_output": {
            "initial_assessment": {"evaluated_trials": final_rows},
            "follow_up_questions": [],
            "simulated_patient_answers": [],
            "final_assessment_after_answers": {"evaluated_trials": final_rows},
            "recommended_trials": [],
            "uncertain_but_actionable_trials": [
                {
                    "trial_id": row["trial_id"],
                    "trial_title": row["trial_title"],
                    "eligibility": "uncertain",
                    "reason": row["explanation"],
                    "unknown_criterion_ids": [
                        criterion["criterion_id"]
                        for criterion in row["criterion_results"]
                    ],
                    "related_question_ids": [],
                }
                for row in final_rows
            ],
            "excluded_trials": [],
            "patient_level_summary": "K-EXAONE call failed before a contract-complete prediction could be built.",
            "medical_disclaimer": "Synthetic software-evaluation output only. Not medical advice and not a real clinical eligibility decision.",
        },
    }


if __name__ == "__main__":
    main()
