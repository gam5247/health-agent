from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from health_agent.agents import PatientProfileAgent, TrialProtocolAgent
from health_agent.models import Patient, Trial


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_patients(path: Path) -> list[Patient]:
    payload = load_json(path)
    if not isinstance(payload, list):
        raise ValueError(f"Expected a list of patients in {path}")
    return PatientProfileAgent().parse_many(payload)


def load_trials(path: Path) -> list[Trial]:
    payload = load_json(path)
    if not isinstance(payload, list):
        raise ValueError(f"Expected a list of trials in {path}")
    return TrialProtocolAgent().parse_many(payload)

