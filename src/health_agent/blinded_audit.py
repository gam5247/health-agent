from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any


TOP_LEVEL_KEYS = {"patient_id", "patient_information_string", "candidate_trials"}
TRIAL_KEYS = {
    "conditions",
    "criteria_to_assess",
    "interventions",
    "known_structured_fields",
    "phase",
    "raw_criteria_excerpt",
    "retrieval_rank",
    "retrieval_score",
    "status",
    "trial_id",
    "trial_source_url",
    "trial_title",
}
CRITERION_KEYS = {
    "criterion",
    "criterion_id",
    "criterion_type",
    "required",
    "structured_value",
}
KNOWN_STRUCTURED_KEYS = {
    "allowed_stages",
    "excluded_flags",
    "max_age",
    "max_ecog",
    "min_age",
    "required_biomarkers",
    "required_prior_treatments",
    "sex",
}
RAW_EXCERPT_KEYS = {
    "eligibility_criteria_excerpt",
    "exclusion",
    "inclusion",
}

FORBIDDEN_KEYS = {
    "agent_trace",
    "answer_key",
    "criterion_level_judgments",
    "final_assessment",
    "final_eligibility",
    "final_output",
    "gold_label",
    "hidden_label",
    "label_source",
    "teacher_label",
    "teacher_rationale",
}
FORBIDDEN_VALUE_PATTERN = re.compile(
    r"\b(agent_trace|final_output|teacher_label|teacher_rationale|gold_label|hidden_label)\b",
    re.IGNORECASE,
)


def audit_blinded_records(records: Iterable[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    for index, record in enumerate(records, start=1):
        record_id = str(record.get("patient_id") or f"record-{index}")
        errors.extend(f"{record_id}: {error}" for error in audit_blinded_record(record))
    return errors


def audit_blinded_record(record: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    keys = set(record)
    if keys != TOP_LEVEL_KEYS:
        errors.append(f"top-level keys mismatch: {sorted(keys)}")
    _audit_forbidden_keys(record, "$", errors)
    _audit_patient(record, errors)
    _audit_trials(record.get("candidate_trials"), errors)
    return errors


def _audit_patient(record: dict[str, Any], errors: list[str]) -> None:
    if not isinstance(record.get("patient_id"), str) or not record.get("patient_id"):
        errors.append("patient_id must be a non-empty string")
    if not isinstance(record.get("patient_information_string"), str) or not record.get("patient_information_string"):
        errors.append("patient_information_string must be a non-empty string")


def _audit_trials(value: Any, errors: list[str]) -> None:
    if not isinstance(value, list) or not value:
        errors.append("candidate_trials must be a non-empty list")
        return
    for trial_index, trial in enumerate(value):
        path = f"candidate_trials[{trial_index}]"
        if not isinstance(trial, dict):
            errors.append(f"{path} must be an object")
            continue
        extra = set(trial) - TRIAL_KEYS
        if extra:
            errors.append(f"{path} has unexpected keys: {sorted(extra)}")
        if not trial.get("trial_id"):
            errors.append(f"{path}.trial_id must be present")
        _audit_criteria(trial.get("criteria_to_assess"), f"{path}.criteria_to_assess", errors)
        _audit_known_structured_fields(trial.get("known_structured_fields"), f"{path}.known_structured_fields", errors)
        _audit_raw_excerpt(trial.get("raw_criteria_excerpt"), f"{path}.raw_criteria_excerpt", errors)


def _audit_criteria(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, list):
        errors.append(f"{path} must be a list")
        return
    for criterion_index, criterion in enumerate(value):
        criterion_path = f"{path}[{criterion_index}]"
        if not isinstance(criterion, dict):
            errors.append(f"{criterion_path} must be an object")
            continue
        extra = set(criterion) - CRITERION_KEYS
        if extra:
            errors.append(f"{criterion_path} has unexpected keys: {sorted(extra)}")
        if not criterion.get("criterion_id"):
            errors.append(f"{criterion_path}.criterion_id must be present")


def _audit_known_structured_fields(value: Any, path: str, errors: list[str]) -> None:
    if value is None:
        return
    if not isinstance(value, dict):
        errors.append(f"{path} must be an object when present")
        return
    extra = set(value) - KNOWN_STRUCTURED_KEYS
    if extra:
        errors.append(f"{path} has unexpected keys: {sorted(extra)}")


def _audit_raw_excerpt(value: Any, path: str, errors: list[str]) -> None:
    if value is None:
        return
    if not isinstance(value, dict):
        errors.append(f"{path} must be an object when present")
        return
    extra = set(value) - RAW_EXCERPT_KEYS
    if extra:
        errors.append(f"{path} has unexpected keys: {sorted(extra)}")


def _audit_forbidden_keys(value: Any, path: str, errors: list[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            if key_text in FORBIDDEN_KEYS:
                errors.append(f"{child_path} is forbidden in blinded input")
            _audit_forbidden_keys(child, child_path, errors)
        return
    if isinstance(value, list):
        for index, child in enumerate(value):
            _audit_forbidden_keys(child, f"{path}[{index}]", errors)
        return
    if isinstance(value, str) and FORBIDDEN_VALUE_PATTERN.search(value):
        errors.append(f"{path} contains evaluator-only field text")
