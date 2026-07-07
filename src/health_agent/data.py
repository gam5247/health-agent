from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from health_agent.agents import PatientProfileAgent, TrialProtocolAgent
from health_agent.models import Patient, Trial


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_records(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".jsonl":
        records = []
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    records.append(json.loads(line))
        return records
    payload = load_json(path)
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("records"), list):
        return payload["records"]
    raise ValueError(f"Expected a list or JSONL records in {path}")


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True, ensure_ascii=False))
            handle.write("\n")


def load_patients(path: Path) -> list[Patient]:
    return PatientProfileAgent().parse_many(load_records(path))


def load_trials(path: Path) -> list[Trial]:
    return TrialProtocolAgent().parse_many(load_records(path))
