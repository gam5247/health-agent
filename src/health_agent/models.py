from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


def _list_of_strings(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    return [str(item) for item in value]


def _dict_of_strings(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    return {str(key): str(item) for key, item in value.items()}


@dataclass(frozen=True)
class Patient:
    patient_id: str
    age: int | None
    sex: str | None
    diagnosis: str | None
    stage: str | None
    ecog: int | None
    biomarkers: dict[str, str] = field(default_factory=dict)
    prior_treatments: list[str] = field(default_factory=list)
    flags: dict[str, bool] = field(default_factory=dict)
    location: dict[str, str] = field(default_factory=dict)
    clinical_note: str | None = None
    scenario: str | None = None
    target_trial_id: str | None = None

    @classmethod
    def from_mapping(cls, item: dict[str, Any]) -> "Patient":
        return cls(
            patient_id=str(item.get("patient_id") or item.get("id") or ""),
            age=_optional_int(item.get("age")),
            sex=_optional_string(item.get("sex")),
            diagnosis=_optional_string(item.get("diagnosis")),
            stage=_optional_string(item.get("stage")),
            ecog=_optional_int(item.get("ecog")),
            biomarkers=_dict_of_strings(item.get("biomarkers")),
            prior_treatments=_list_of_strings(item.get("prior_treatments")),
            flags={str(key): bool(value) for key, value in (item.get("flags") or {}).items()},
            location=_dict_of_strings(item.get("location")),
            clinical_note=_optional_string(item.get("clinical_note")),
            scenario=_optional_string(item.get("scenario")),
            target_trial_id=_optional_string(item.get("target_trial_id")),
        )


@dataclass(frozen=True)
class Trial:
    trial_id: str
    title: str
    phase: str | None
    conditions: list[str]
    interventions: list[str]
    min_age: int | None
    max_age: int | None
    sex: str
    allowed_stages: list[str]
    max_ecog: int | None
    required_biomarkers: dict[str, str]
    required_prior_treatments: list[str]
    excluded_flags: list[str]
    required_patient_fields: list[str]
    summary: str | None = None
    status: str | None = None
    enrollment: int | None = None
    source_url: str | None = None
    eligibility_criteria: str | None = None
    inclusion_criteria: list[str] = field(default_factory=list)
    exclusion_criteria: list[str] = field(default_factory=list)

    @classmethod
    def from_mapping(cls, item: dict[str, Any]) -> "Trial":
        return cls(
            trial_id=str(item.get("trial_id") or item.get("nct_id") or item.get("id") or ""),
            title=str(item.get("title") or "Untitled trial"),
            phase=_optional_string(item.get("phase")),
            conditions=_list_of_strings(item.get("conditions")),
            interventions=_list_of_strings(item.get("interventions")),
            min_age=_optional_int(item.get("min_age")),
            max_age=_optional_int(item.get("max_age")),
            sex=str(item.get("sex") or "all"),
            allowed_stages=_list_of_strings(item.get("allowed_stages")),
            max_ecog=_optional_int(item.get("max_ecog")),
            required_biomarkers=_dict_of_strings(item.get("required_biomarkers")),
            required_prior_treatments=_list_of_strings(item.get("required_prior_treatments")),
            excluded_flags=_list_of_strings(item.get("excluded_flags")),
            required_patient_fields=_list_of_strings(item.get("required_patient_fields")),
            summary=_optional_string(item.get("summary")),
            status=_optional_string(item.get("status")),
            enrollment=_optional_int(item.get("enrollment")),
            source_url=_optional_string(item.get("source_url")),
            eligibility_criteria=_optional_string(item.get("eligibility_criteria")),
            inclusion_criteria=_list_of_strings(item.get("inclusion_criteria")),
            exclusion_criteria=_list_of_strings(item.get("exclusion_criteria")),
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "trial_id": self.trial_id,
            "title": self.title,
            "phase": self.phase,
            "conditions": list(self.conditions),
            "interventions": list(self.interventions),
            "min_age": self.min_age,
            "max_age": self.max_age,
            "sex": self.sex,
            "allowed_stages": list(self.allowed_stages),
            "max_ecog": self.max_ecog,
            "required_biomarkers": dict(self.required_biomarkers),
            "required_prior_treatments": list(self.required_prior_treatments),
            "excluded_flags": list(self.excluded_flags),
            "required_patient_fields": list(self.required_patient_fields),
            "summary": self.summary,
            "status": self.status,
            "enrollment": self.enrollment,
            "source_url": self.source_url,
            "eligibility_criteria": self.eligibility_criteria,
            "inclusion_criteria": list(self.inclusion_criteria),
            "exclusion_criteria": list(self.exclusion_criteria),
        }


@dataclass(frozen=True)
class MatchEvidence:
    criterion: str
    status: str
    detail: str

    def as_dict(self) -> dict[str, str]:
        return {
            "criterion": self.criterion,
            "status": self.status,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class Recommendation:
    patient_id: str
    trial_id: str
    trial_title: str
    score: float
    decision: str
    rationale: str
    evidence: list[MatchEvidence]
    questions: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "patient_id": self.patient_id,
            "trial_id": self.trial_id,
            "trial_title": self.trial_title,
            "score": self.score,
            "decision": self.decision,
            "rationale": self.rationale,
            "evidence": [item.as_dict() for item in self.evidence],
            "questions": list(self.questions),
        }


def _optional_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    return int(value)


def _optional_string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
