from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

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
    request = json.loads(args.input_batch.read_text(encoding="utf-8"))
    expected_patients = request["patients"]
    expected_by_id = {patient["patient_id"]: patient for patient in expected_patients}
    expected_ids = [patient["patient_id"] for patient in expected_patients]
    text = response_text(args.response)
    parsed = extract_json_objects(text)
    normalized = []
    seen = set()
    for item in parsed:
        patient_id = item.get("patient_id")
        if patient_id not in expected_by_id or patient_id in seen:
            continue
        seen.add(patient_id)
        normalized.append(normalize_record(item, expected_by_id[patient_id]))
    errors = validate_records(normalized, expected_by_id, expected_ids)
    args.output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with args.output_jsonl.open("w", encoding="utf-8", newline="\n") as handle:
        for item in normalized:
            handle.write(json.dumps(item, ensure_ascii=False, sort_keys=True))
            handle.write("\n")
    args.output_json.write_text(
        json.dumps(
            {
                "source": str(args.response),
                "patient_count": len(normalized),
                "patients": normalized,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    summary = {
        "source": str(args.response),
        "output_jsonl": str(args.output_jsonl),
        "output_json": str(args.output_json),
        "expected_patient_ids": expected_ids,
        "parsed_json_objects": len(parsed),
        "saved_patient_ids": [item["patient_id"] for item in normalized],
        "missing_patient_ids": [pid for pid in expected_ids if pid not in seen],
        "validation_error_count": len(errors),
        "validation_errors": errors[:50],
    }
    args.summary.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    if errors or len(normalized) != len(expected_ids):
        raise SystemExit(1)


def response_text(path: Path) -> str:
    raw = path.read_bytes()
    for encoding in ["utf-8-sig", "utf-16", "utf-8"]:
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        text = raw.decode("utf-8", errors="replace")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return text
    for key in ["answerText", "answer", "content", "text"]:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value
    artifact = payload.get("answerArtifact")
    if isinstance(artifact, dict):
        for key in ["text", "markdown"]:
            value = artifact.get(key)
            if isinstance(value, str) and value.strip():
                return value
    return text


def extract_json_objects(text: str) -> list[dict[str, Any]]:
    decoder = json.JSONDecoder()
    items = []
    index = 0
    while index < len(text):
        start = text.find("{", index)
        if start < 0:
            break
        try:
            item, offset = decoder.raw_decode(text[start:])
        except json.JSONDecodeError:
            index = start + 1
            continue
        if isinstance(item, dict) and item.get("patient_id"):
            items.append(item)
        index = start + offset
    return items


def normalize_record(item: dict[str, Any], expected: dict[str, Any]) -> dict[str, Any]:
    agent_trace = item.get("agent_trace")
    if not isinstance(agent_trace, dict):
        agent_trace = {
            key: item.get(key, {})
            for key in AGENT_KEYS
            if key in item
        }
    final_output = normalize_final_output(item, expected)
    patient_id = item["patient_id"]
    return {
        "patient_id": patient_id,
        "input": item.get("input")
        or {
            "patient_information_string": expected["patient_information_string"],
            "candidate_trial_ids": [
                trial["trial_id"] for trial in expected.get("candidate_trials", [])
            ],
        },
        "agent_trace": agent_trace,
        "final_output": final_output,
    }


def normalize_final_output(item: dict[str, Any], expected: dict[str, Any]) -> dict[str, Any]:
    patient_id = item["patient_id"]
    final_output = item.get("final_output") if isinstance(item.get("final_output"), dict) else {}
    recommendations = final_output.get("recommendations")
    if not isinstance(recommendations, list):
        recommendation_agent = item.get("recommendation_agent")
        if isinstance(recommendation_agent, dict):
            recommendations = (
                recommendation_agent.get("final_output")
                or recommendation_agent.get("final_recommendations")
                or recommendation_agent.get("final_trial_assessments")
                or recommendation_agent.get("final_outputs")
                or recommendation_agent.get("ranking")
            )
    if not isinstance(recommendations, list):
        recommendations = recommendations_from_compact_agents(item)
    if not isinstance(recommendations, list):
        recommendations = []
    normalized_recommendations = []
    title_by_id = {
        trial["trial_id"]: trial.get("title", "")
        for trial in expected.get("candidate_trials", [])
    }
    url_by_id = {
        trial["trial_id"]: trial.get("source_url", "")
        for trial in expected.get("candidate_trials", [])
    }
    for index, recommendation in enumerate(recommendations, start=1):
        trial_id = recommendation.get("trial_id", "")
        eligibility = (
            recommendation.get("eligibility")
            or recommendation.get("final_eligibility")
            or recommendation.get("final_label")
            or recommendation.get("label")
            or "uncertain"
        )
        normalized_recommendations.append(
            {
                "rank": int(recommendation.get("rank") or recommendation.get("recommendation_rank") or index),
                "trial_id": trial_id,
                "trial_title": recommendation.get("trial_title")
                or recommendation.get("title")
                or title_by_id.get(trial_id, ""),
                "trial_source_url": recommendation.get("trial_source_url")
                or url_by_id.get(trial_id, ""),
                "eligibility": eligibility,
                "criterion_results": normalize_criteria(
                    recommendation.get("criterion_results")
                    or recommendation.get("criterion_level_judgments")
                    or recommendation.get("criteria")
                    or recommendation.get("criterion_assessments")
                    or []
                ),
                "follow_up_questions": recommendation.get("follow_up_questions") or [],
                "simulated_patient_answers": recommendation.get("simulated_patient_answers") or [],
                "explanation": recommendation.get("explanation")
                or recommendation.get("final_explanation")
                or recommendation.get("recommendation_reason")
                or recommendation.get("summary_reason")
                or "",
            }
        )
    criteria_by_trial = compact_criteria_by_trial(item)
    for recommendation in normalized_recommendations:
        if not recommendation["criterion_results"]:
            recommendation["criterion_results"] = criteria_by_trial.get(
                recommendation["trial_id"],
                [],
            )
    ordered = final_output.get("recommended_trial_order")
    if not isinstance(ordered, list) or not ordered:
        ordered = final_output.get("recommended_trial_ids")
    if not isinstance(ordered, list) or len(ordered) != len(normalized_recommendations):
        ordered = [item["trial_id"] for item in sorted(normalized_recommendations, key=lambda row: row["rank"])]
    return {
        "patient_id": final_output.get("patient_id") or patient_id,
        "recommendations": normalized_recommendations,
        "recommended_trial_order": ordered,
        "medical_disclaimer": final_output.get("medical_disclaimer")
        or "software evaluation only, not medical advice",
    }


def normalize_criteria(value: Any) -> list[dict[str, str]]:
    if isinstance(value, dict):
        rows = []
        for criterion_id, payload in value.items():
            if isinstance(payload, dict):
                rows.append(
                    {
                        "criterion_id": str(criterion_id),
                        "status": str(payload.get("status") or payload.get("judgment") or "unknown"),
                        "reason": str(payload.get("reason") or payload.get("rationale") or ""),
                    }
                )
            else:
                rows.append(
                    {
                        "criterion_id": str(criterion_id),
                        "status": "unknown",
                        "reason": str(payload),
                    }
                )
        return rows
    rows = []
    for item in value if isinstance(value, list) else []:
        if isinstance(item, dict):
            rows.append(
                {
                    "criterion_id": str(item.get("criterion_id", "")),
                    "status": str(item.get("status") or item.get("judgment") or "unknown"),
                    "reason": str(item.get("reason") or item.get("rationale") or ""),
                }
            )
        elif isinstance(item, list) and len(item) >= 3:
            rows.append(
                {
                    "criterion_id": str(item[0]),
                    "status": str(item[1]),
                    "reason": str(item[2]),
                }
            )
    return rows


def recommendations_from_compact_agents(item: dict[str, Any]) -> list[dict[str, Any]]:
    inference = item.get("inference_matching_agent")
    if not isinstance(inference, dict):
        return []
    rows = (
        inference.get("final_output")
        or inference.get("final_outputs")
        or inference.get("final_trial_assessments")
        or inference.get("initial_output")
        or inference.get("initial_outputs")
        or inference.get("initial_trial_assessments")
    )
    if not isinstance(rows, list):
        return []
    recommendations = []
    for index, row in enumerate(rows, start=1):
        if isinstance(row, dict):
            trial_id = str(row.get("trial_id", ""))
            eligibility = str(row.get("eligibility") or row.get("label") or "uncertain")
            raw_criteria = (
                row.get("criterion_results")
                or row.get("criteria")
                or row.get("criterion_statuses")
                or row.get("criterion_assessments")
                or []
            )
            rationale = str(row.get("rationale") or row.get("summary_reason") or "")
        elif isinstance(row, list) and len(row) >= 3:
            trial_id = str(row[0])
            eligibility = str(row[1])
            raw_criteria = row[2] if isinstance(row[2], list) else []
            rationale = str(row[3]) if len(row) >= 4 else ""
        else:
            continue
        criteria = []
        for criterion in raw_criteria:
            if isinstance(criterion, dict):
                criteria.append(criterion)
            elif isinstance(criterion, list) and len(criterion) >= 3:
                criteria.append(
                    {
                        "criterion_id": str(criterion[0]),
                        "status": str(criterion[1]),
                        "reason": str(criterion[2]),
                    }
                )
        recommendations.append(
            {
                "rank": index,
                "trial_id": trial_id,
                "eligibility": eligibility,
                "criterion_results": criteria,
                "explanation": rationale,
            }
        )
    return recommendations


def compact_criteria_by_trial(item: dict[str, Any]) -> dict[str, list[dict[str, str]]]:
    return {
        recommendation["trial_id"]: recommendation["criterion_results"]
        for recommendation in recommendations_from_compact_agents(item)
    }


def validate_records(
    records: list[dict[str, Any]],
    expected_by_id: dict[str, dict[str, Any]],
    expected_ids: list[str],
) -> list[str]:
    errors = []
    by_id = {record["patient_id"]: record for record in records}
    for patient_id in expected_ids:
        if patient_id not in by_id:
            errors.append(f"{patient_id}: missing output record")
            continue
        record = by_id[patient_id]
        expected = expected_by_id[patient_id]
        for key in AGENT_KEYS:
            if key not in record["agent_trace"]:
                errors.append(f"{patient_id}: missing {key}")
        expected_trials = [trial["trial_id"] for trial in expected.get("candidate_trials", [])]
        recommendations = record["final_output"].get("recommendations", [])
        seen_trials = [item.get("trial_id") for item in recommendations]
        if sorted(seen_trials) != sorted(expected_trials):
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
            actual = {
                item.get("criterion_id", "")
                for item in recommendation.get("criterion_results", [])
            }
            if actual != expected_criteria.get(trial_id, set()):
                errors.append(f"{patient_id}/{trial_id}: final criterion ids mismatch")
    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest a GPT E2E teacher-label response.")
    parser.add_argument("--input-batch", type=Path, required=True)
    parser.add_argument("--response", type=Path, required=True)
    parser.add_argument("--output-jsonl", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    return parser.parse_args()


if __name__ == "__main__":
    main()
