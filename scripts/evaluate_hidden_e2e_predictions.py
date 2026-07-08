from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from health_agent.hidden_eval import evaluate_predictions


def main() -> None:
    args = parse_args()
    answer_records = read_jsonl(args.answer_key)
    prediction_records = read_jsonl(args.predictions)
    report = evaluate_predictions(
        answer_records=answer_records,
        prediction_records=prediction_records,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes((json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    if args.fail_on_contract_errors and report["contract"]["error_count"]:
        raise SystemExit(1)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate E2E orchestration predictions against the hidden v2 answer key.")
    parser.add_argument(
        "--answer-key",
        type=Path,
        default=ROOT / "artifacts" / "gpt-e2e-teacher-labeling" / "gpt_e2e_teacher_labels_100.v2.jsonl",
        help="Evaluator-only hidden labels. Do not pass this path to the agent runner.",
    )
    parser.add_argument(
        "--predictions",
        type=Path,
        default=ROOT / "outputs" / "e2e_orchestration_predictions_v2.jsonl",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "outputs" / "e2e_orchestration_hidden_eval_report.json",
    )
    parser.add_argument("--fail-on-contract-errors", action="store_true")
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                records.append(json.loads(line))
    return records


if __name__ == "__main__":
    main()
