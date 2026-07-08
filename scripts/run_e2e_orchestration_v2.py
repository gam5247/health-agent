from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from health_agent.e2e_orchestrator import run_competition_orchestration_v2


def main() -> None:
    args = parse_args()
    input_records = read_jsonl(args.input)
    if args.max_patients is not None:
        input_records = input_records[: args.max_patients]
    answers_by_patient = read_answers(args.simulated_answers)

    predictions = [
        run_competition_orchestration_v2(
            record,
            simulated_answers=answers_by_patient.get(record["patient_id"], []),
        )
        for record in input_records
    ]
    args.output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.output_jsonl, predictions)
    write_json(
        args.output_json,
        {
            "schema_version": "health-agent-e2e-orchestration-v2-batch",
            "patient_count": len(predictions),
            "patients": predictions,
        },
    )
    summary = build_summary(predictions)
    write_json(args.summary, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run competition-format E2E orchestration on blinded input. This runner does not accept an answer-key argument."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=ROOT / "artifacts" / "e2e-orchestration-eval" / "blinded_input_100.jsonl",
    )
    parser.add_argument(
        "--output-jsonl",
        type=Path,
        default=ROOT / "outputs" / "e2e_orchestration_predictions_v2.jsonl",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=ROOT / "outputs" / "e2e_orchestration_predictions_v2.json",
    )
    parser.add_argument(
        "--summary",
        type=Path,
        default=ROOT / "outputs" / "e2e_orchestration_predictions_v2_summary.json",
    )
    parser.add_argument(
        "--simulated-answers",
        type=Path,
        default=None,
        help="Optional patient-answer JSONL. This is not an answer key; it may contain only patient_id and simulated_patient_answers.",
    )
    parser.add_argument("--max-patients", type=int, default=None)
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                records.append(json.loads(line))
    return records


def read_answers(path: Path | None) -> dict[str, list[dict[str, str]]]:
    if path is None:
        return {}
    result: dict[str, list[dict[str, str]]] = {}
    for record in read_jsonl(path):
        result[str(record["patient_id"])] = list(record.get("simulated_patient_answers", []))
    return result


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
            handle.write("\n")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"))


def build_summary(predictions: list[dict[str, Any]]) -> dict[str, Any]:
    eligibility = Counter()
    criterion_status = Counter()
    question_count = 0
    answer_count = 0
    for prediction in predictions:
        final = prediction["final_output"]
        question_count += len(final["follow_up_questions"])
        answer_count += len(final["simulated_patient_answers"])
        for row in final["final_assessment_after_answers"]["evaluated_trials"]:
            eligibility[row["eligibility"]] += 1
            for criterion in row["criterion_results"]:
                criterion_status[criterion["status"]] += 1
    return {
        "schema_version": "health-agent-e2e-orchestration-v2-summary",
        "patient_count": len(predictions),
        "final_trial_judgment_count": sum(
            len(prediction["final_output"]["final_assessment_after_answers"]["evaluated_trials"])
            for prediction in predictions
        ),
        "follow_up_question_count": question_count,
        "simulated_patient_answer_count": answer_count,
        "eligibility_distribution": dict(sorted(eligibility.items())),
        "criterion_status_distribution": dict(sorted(criterion_status.items())),
        "runner_answer_key_access": False,
    }


if __name__ == "__main__":
    main()
