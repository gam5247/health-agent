from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from health_agent.e2e_orchestrator import blinded_input_from_answer_record
from health_agent.blinded_audit import audit_blinded_records


def main() -> None:
    args = parse_args()
    answer_records = read_jsonl(args.answer_key)
    if args.max_patients is not None:
        answer_records = answer_records[: args.max_patients]
    blinded_records = [
        blinded_input_from_answer_record(record)
        for record in answer_records
    ]
    audit_errors = audit_blinded_records(blinded_records)
    if audit_errors:
        raise SystemExit(
            "Blinded input failed recursive safety audit:\n"
            + "\n".join(audit_errors[:50])
        )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    input_path = args.output_dir / "blinded_input_100.jsonl"
    manifest_path = args.output_dir / "blinded_input_manifest.json"
    write_jsonl(input_path, blinded_records)
    manifest = {
        "schema_version": "health-agent-hidden-e2e-input-v1",
        "patient_count": len(blinded_records),
        "source_answer_key": "evaluator-only; path intentionally omitted from the agent-visible manifest",
        "blinded_input": relative_path(input_path),
        "blinded_input_sha256": sha256_file(input_path),
        "contains_hidden_labels": False,
        "recursive_audit": "passed",
        "recursive_audit_error_count": 0,
        "visible_fields": [
            "patient_id",
            "patient_information_string",
            "candidate_trials",
        ],
        "note": "This file is safe for the agent runner. The hidden answer key remains evaluator-only.",
    }
    write_json(manifest_path, manifest)
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build blinded E2E orchestration input from the hidden answer key.")
    parser.add_argument(
        "--answer-key",
        type=Path,
        default=ROOT / "artifacts" / "gpt-e2e-teacher-labeling" / "gpt_e2e_teacher_labels_100.v2.jsonl",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "artifacts" / "e2e-orchestration-eval",
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


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
            handle.write("\n")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_bytes((json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


if __name__ == "__main__":
    main()
