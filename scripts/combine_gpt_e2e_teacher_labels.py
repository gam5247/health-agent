from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


AGENT_KEYS = [
    "criteria_parser_agent",
    "patient_information_understanding_agent",
    "inference_matching_agent",
    "question_generation_agent",
    "interaction_simulation_agent",
    "recommendation_agent",
    "result_explanation_agent",
]


def main() -> None:
    args = parse_args()
    expected_payload = json.loads(args.input_100.read_text(encoding="utf-8"))
    expected_patients = expected_payload["patients"]
    expected_by_id = {patient["patient_id"]: patient for patient in expected_patients}
    expected_ids = [patient["patient_id"] for patient in expected_patients]

    records = read_batch_records(args.responses_dir, args.batch_count)
    records_by_id: dict[str, dict[str, Any]] = {}
    duplicate_ids: list[str] = []
    for record in records:
        patient_id = record["patient_id"]
        if patient_id in records_by_id:
            duplicate_ids.append(patient_id)
            continue
        records_by_id[patient_id] = enrich_record(record, expected_by_id.get(patient_id, {}))

    ordered_records = [
        records_by_id[patient_id]
        for patient_id in expected_ids
        if patient_id in records_by_id
    ]
    errors = validate_records(ordered_records, expected_by_id, expected_ids, duplicate_ids)
    semantic_warnings = semantic_consistency_warnings(ordered_records)
    summary = build_summary(ordered_records, expected_ids, duplicate_ids, errors, semantic_warnings)

    args.output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with args.output_jsonl.open("w", encoding="utf-8", newline="\n") as handle:
        for record in ordered_records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
            handle.write("\n")
    args.output_json.write_text(
        json.dumps(
            {
                "source": {
                    "input_100": str(args.input_100),
                    "responses_dir": str(args.responses_dir),
                },
                "patient_count": len(ordered_records),
                "patients": ordered_records,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    args.summary.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    if errors:
        raise SystemExit(1)


def read_batch_records(responses_dir: Path, batch_count: int) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index in range(1, batch_count + 1):
        path = responses_dir / f"gpt_e2e_teacher_response_batch_{index:02d}.jsonl"
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    records.append(json.loads(line))
    return records


def enrich_record(record: dict[str, Any], expected: dict[str, Any]) -> dict[str, Any]:
    patient_text = (
        record.get("patient_information_string")
        or record.get("input", {}).get("patient_information_string")
        or expected.get("patient_information_string", "")
    )
    enriched = dict(record)
    enriched["patient_information_string"] = patient_text
    enriched["synthetic_source_profile"] = expected.get("synthetic_source_profile", {})
    enriched["input"] = {
        "patient_information_string": patient_text,
        "candidate_trial_ids": [
            trial["trial_id"] for trial in expected.get("candidate_trials", [])
        ],
    }
    return enriched


def validate_records(
    records: list[dict[str, Any]],
    expected_by_id: dict[str, dict[str, Any]],
    expected_ids: list[str],
    duplicate_ids: list[str],
) -> list[str]:
    errors: list[str] = []
    by_id = {record["patient_id"]: record for record in records}
    for patient_id in duplicate_ids:
        errors.append(f"{patient_id}: duplicate output record")
    for patient_id in expected_ids:
        if patient_id not in by_id:
            errors.append(f"{patient_id}: missing output record")
            continue
        record = by_id[patient_id]
        expected = expected_by_id[patient_id]
        if not record.get("patient_information_string"):
            errors.append(f"{patient_id}: missing patient_information_string")
        for key in AGENT_KEYS:
            if key not in record.get("agent_trace", {}):
                errors.append(f"{patient_id}: missing {key}")
        recommendations = record.get("final_output", {}).get("recommendations", [])
        expected_trials = [trial["trial_id"] for trial in expected.get("candidate_trials", [])]
        actual_trials = [recommendation.get("trial_id") for recommendation in recommendations]
        if sorted(actual_trials) != sorted(expected_trials):
            errors.append(f"{patient_id}: final recommendations do not match candidate trials")
        expected_criteria = {
            trial["trial_id"]: {
                criterion["criterion_id"]
                for criterion in trial.get("criteria_to_assess", [])
            }
            for trial in expected.get("candidate_trials", [])
        }
        for recommendation in recommendations:
            trial_id = recommendation.get("trial_id", "")
            actual_criteria = {
                criterion.get("criterion_id", "")
                for criterion in recommendation.get("criterion_results", [])
            }
            if actual_criteria != expected_criteria.get(trial_id, set()):
                errors.append(f"{patient_id}/{trial_id}: final criterion ids mismatch")
    return errors


def build_summary(
    records: list[dict[str, Any]],
    expected_ids: list[str],
    duplicate_ids: list[str],
    errors: list[str],
    semantic_warnings: list[str],
) -> dict[str, Any]:
    eligibility_counts: Counter[str] = Counter()
    criterion_counts: Counter[str] = Counter()
    recommendation_count = 0
    criterion_result_count = 0
    follow_up_question_count = 0
    simulated_answer_count = 0
    patients_with_follow_up: set[str] = set()
    for record in records:
        patient_id = record["patient_id"]
        for recommendation in record.get("final_output", {}).get("recommendations", []):
            recommendation_count += 1
            eligibility_counts[str(recommendation.get("eligibility", "unknown"))] += 1
            questions = recommendation.get("follow_up_questions", [])
            answers = recommendation.get("simulated_patient_answers", [])
            follow_up_question_count += len(questions)
            simulated_answer_count += len(answers)
            if questions:
                patients_with_follow_up.add(patient_id)
            for criterion in recommendation.get("criterion_results", []):
                criterion_result_count += 1
                criterion_counts[str(criterion.get("status", "unknown"))] += 1
    saved_ids = [record["patient_id"] for record in records]
    return {
        "expected_patient_count": len(expected_ids),
        "patient_count": len(records),
        "missing_patient_ids": [patient_id for patient_id in expected_ids if patient_id not in saved_ids],
        "duplicate_patient_ids": duplicate_ids,
        "recommendation_count": recommendation_count,
        "criterion_result_count": criterion_result_count,
        "follow_up_question_count": follow_up_question_count,
        "patients_with_follow_up_count": len(patients_with_follow_up),
        "simulated_patient_answer_count": simulated_answer_count,
        "eligibility_distribution": dict(sorted(eligibility_counts.items())),
        "criterion_status_distribution": dict(sorted(criterion_counts.items())),
        "validation_error_count": len(errors),
        "validation_errors": errors[:100],
        "semantic_consistency_warning_count": len(semantic_warnings),
        "semantic_consistency_warnings": semantic_warnings[:100],
    }


def semantic_consistency_warnings(records: list[dict[str, Any]]) -> list[str]:
    warnings: list[str] = []
    for record in records:
        patient_id = record["patient_id"]
        for recommendation in record.get("final_output", {}).get("recommendations", []):
            trial_id = recommendation.get("trial_id", "")
            eligibility = recommendation.get("eligibility", "")
            statuses = {
                criterion.get("status", "unknown")
                for criterion in recommendation.get("criterion_results", [])
            }
            if eligibility == "eligible" and statuses & {"violated", "unknown"}:
                warnings.append(
                    f"{patient_id}/{trial_id}: eligible with criterion statuses {sorted(statuses)}"
                )
            elif eligibility == "uncertain" and (
                "violated" in statuses or "unknown" not in statuses
            ):
                warnings.append(
                    f"{patient_id}/{trial_id}: uncertain with criterion statuses {sorted(statuses)}"
                )
            elif eligibility == "ineligible" and "violated" not in statuses:
                warnings.append(
                    f"{patient_id}/{trial_id}: ineligible with criterion statuses {sorted(statuses)}"
                )
    return warnings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Combine GPT E2E teacher-label batches.")
    parser.add_argument(
        "--input-100",
        type=Path,
        default=Path("artifacts/gpt-e2e-teacher-labeling/gpt_e2e_teacher_input_100.json"),
    )
    parser.add_argument(
        "--responses-dir",
        type=Path,
        default=Path("artifacts/gpt-e2e-teacher-labeling/responses"),
    )
    parser.add_argument("--batch-count", type=int, default=20)
    parser.add_argument(
        "--output-jsonl",
        type=Path,
        default=Path("artifacts/gpt-e2e-teacher-labeling/gpt_e2e_teacher_labels_100.jsonl"),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("artifacts/gpt-e2e-teacher-labeling/gpt_e2e_teacher_labels_100.json"),
    )
    parser.add_argument(
        "--summary",
        type=Path,
        default=Path("artifacts/gpt-e2e-teacher-labeling/gpt_e2e_teacher_labels_100_summary.json"),
    )
    return parser.parse_args()


if __name__ == "__main__":
    main()
