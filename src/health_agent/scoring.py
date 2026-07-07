from __future__ import annotations

from health_agent.models import MatchEvidence, Patient, Recommendation, Trial


def evaluate_trial(patient: Patient, trial: Trial) -> Recommendation:
    evidence: list[MatchEvidence] = []

    for field_name in trial.required_patient_fields:
        if _is_missing_required_field(patient, field_name):
            evidence.append(
                MatchEvidence(
                    criterion=f"field:{field_name}",
                    status="missing",
                    detail=f"Required patient field '{field_name}' is missing.",
                )
            )

    evidence.extend(_condition_evidence(patient, trial))
    evidence.extend(_age_evidence(patient, trial))
    evidence.extend(_sex_evidence(patient, trial))
    evidence.extend(_stage_evidence(patient, trial))
    evidence.extend(_ecog_evidence(patient, trial))
    evidence.extend(_biomarker_evidence(patient, trial))
    evidence.extend(_prior_treatment_evidence(patient, trial))
    evidence.extend(_exclusion_flag_evidence(patient, trial))

    score = _score_evidence(evidence)
    decision = _decision(score, evidence)
    rationale = _rationale(decision, evidence)
    return Recommendation(
        patient_id=patient.patient_id,
        trial_id=trial.trial_id,
        trial_title=trial.title,
        score=score,
        decision=decision,
        rationale=rationale,
        evidence=evidence,
    )


def _condition_evidence(patient: Patient, trial: Trial) -> list[MatchEvidence]:
    if not trial.conditions:
        return []
    if not patient.diagnosis:
        return [
            MatchEvidence("field:diagnosis", "missing", "Patient diagnosis is missing.")
        ]
    diagnosis = _norm(patient.diagnosis)
    for condition in trial.conditions:
        condition_norm = _norm(condition)
        if condition_norm in diagnosis or diagnosis in condition_norm:
            return [
                MatchEvidence(
                    "condition",
                    "matched",
                    f"Diagnosis '{patient.diagnosis}' matches trial condition '{condition}'.",
                )
            ]
    return [
        MatchEvidence(
            "condition",
            "conflict",
            f"Diagnosis '{patient.diagnosis}' does not match trial conditions.",
        )
    ]


def _age_evidence(patient: Patient, trial: Trial) -> list[MatchEvidence]:
    if trial.min_age is None and trial.max_age is None:
        return []
    if patient.age is None:
        return [MatchEvidence("field:age", "missing", "Patient age is missing.")]
    if trial.min_age is not None and patient.age < trial.min_age:
        return [
            MatchEvidence(
                "age",
                "conflict",
                f"Age {patient.age} is below minimum age {trial.min_age}.",
            )
        ]
    if trial.max_age is not None and patient.age > trial.max_age:
        return [
            MatchEvidence(
                "age",
                "conflict",
                f"Age {patient.age} is above maximum age {trial.max_age}.",
            )
        ]
    return [MatchEvidence("age", "matched", f"Age {patient.age} is within bounds.")]


def _sex_evidence(patient: Patient, trial: Trial) -> list[MatchEvidence]:
    if _norm(trial.sex) in {"all", "any", ""}:
        return []
    if not patient.sex:
        return [MatchEvidence("field:sex", "missing", "Patient sex is missing.")]
    if _norm(patient.sex) == _norm(trial.sex):
        return [MatchEvidence("sex", "matched", f"Sex '{patient.sex}' matches.")]
    return [
        MatchEvidence(
            "sex",
            "conflict",
            f"Sex '{patient.sex}' does not match trial criterion '{trial.sex}'.",
        )
    ]


def _stage_evidence(patient: Patient, trial: Trial) -> list[MatchEvidence]:
    if not trial.allowed_stages:
        return []
    if not patient.stage:
        return [MatchEvidence("field:stage", "missing", "Patient stage is missing.")]
    allowed = {_norm(stage) for stage in trial.allowed_stages}
    if _norm(patient.stage) in allowed:
        return [MatchEvidence("stage", "matched", f"Stage '{patient.stage}' is allowed.")]
    return [
        MatchEvidence(
            "stage",
            "conflict",
            f"Stage '{patient.stage}' is not in allowed stages {trial.allowed_stages}.",
        )
    ]


def _ecog_evidence(patient: Patient, trial: Trial) -> list[MatchEvidence]:
    if trial.max_ecog is None:
        return []
    if patient.ecog is None:
        return [MatchEvidence("field:ecog", "missing", "Patient ECOG is missing.")]
    if patient.ecog <= trial.max_ecog:
        return [
            MatchEvidence(
                "ecog",
                "matched",
                f"ECOG {patient.ecog} is at or below maximum {trial.max_ecog}.",
            )
        ]
    return [
        MatchEvidence(
            "ecog",
            "conflict",
            f"ECOG {patient.ecog} is above maximum {trial.max_ecog}.",
        )
    ]


def _biomarker_evidence(patient: Patient, trial: Trial) -> list[MatchEvidence]:
    result: list[MatchEvidence] = []
    patient_biomarkers = {_norm(key): value for key, value in patient.biomarkers.items()}
    for marker, required_value in trial.required_biomarkers.items():
        patient_value = patient_biomarkers.get(_norm(marker))
        criterion = f"biomarker:{marker}"
        if patient_value is None:
            result.append(
                MatchEvidence(
                    criterion,
                    "missing",
                    f"Required biomarker '{marker}' is missing.",
                )
            )
        elif _biomarker_matches(patient_value, required_value):
            result.append(
                MatchEvidence(
                    criterion,
                    "matched",
                    f"{marker} value '{patient_value}' matches '{required_value}'.",
                )
            )
        else:
            result.append(
                MatchEvidence(
                    criterion,
                    "conflict",
                    f"{marker} value '{patient_value}' does not match '{required_value}'.",
                )
            )
    return result


def _prior_treatment_evidence(patient: Patient, trial: Trial) -> list[MatchEvidence]:
    if not trial.required_prior_treatments:
        return []
    if not patient.prior_treatments:
        return [
            MatchEvidence(
                "field:prior_treatments",
                "missing",
                "Prior treatment history is missing.",
            )
        ]
    observed = {_norm(item) for item in patient.prior_treatments}
    result: list[MatchEvidence] = []
    for treatment in trial.required_prior_treatments:
        treatment_norm = _norm(treatment)
        matched = any(treatment_norm in item or item in treatment_norm for item in observed)
        result.append(
            MatchEvidence(
                f"prior_treatment:{treatment}",
                "matched" if matched else "conflict",
                (
                    f"Prior treatment '{treatment}' is documented."
                    if matched
                    else f"Prior treatment '{treatment}' is not documented."
                ),
            )
        )
    return result


def _exclusion_flag_evidence(patient: Patient, trial: Trial) -> list[MatchEvidence]:
    result: list[MatchEvidence] = []
    for flag in trial.excluded_flags:
        criterion = f"flag:{flag}"
        if flag not in patient.flags:
            result.append(
                MatchEvidence(
                    criterion,
                    "missing",
                    f"Exclusion flag '{flag}' is unknown.",
                )
            )
        elif patient.flags[flag]:
            result.append(
                MatchEvidence(
                    criterion,
                    "conflict",
                    f"Patient has exclusion flag '{flag}'.",
                )
            )
        else:
            result.append(
                MatchEvidence(
                    criterion,
                    "matched",
                    f"Patient does not have exclusion flag '{flag}'.",
                )
            )
    return result


def _is_missing_required_field(patient: Patient, field_name: str) -> bool:
    value = getattr(patient, field_name, None)
    return value is None or value == {} or value == []


def _score_evidence(evidence: list[MatchEvidence]) -> float:
    if not evidence:
        return 0.0
    points = 0.0
    for item in evidence:
        if item.status == "matched":
            points += 1.0
        elif item.status == "missing":
            points += 0.35
    return round(points / len(evidence), 3)


def _decision(score: float, evidence: list[MatchEvidence]) -> str:
    if any(item.status == "conflict" for item in evidence):
        return "not_recommended"
    if any(item.status == "missing" for item in evidence):
        return "needs_more_info" if score >= 0.45 else "not_recommended"
    if score >= 0.75:
        return "recommend"
    return "not_recommended"


def _rationale(decision: str, evidence: list[MatchEvidence]) -> str:
    matched = sum(item.status == "matched" for item in evidence)
    missing = sum(item.status == "missing" for item in evidence)
    conflicts = sum(item.status == "conflict" for item in evidence)
    if decision == "recommend":
        return f"Eligible-looking match across {matched} checked criteria."
    if decision == "needs_more_info":
        return f"Potential match, but {missing} required criteria need confirmation."
    return f"Not recommended because {conflicts} conflicts and {missing} missing items were found."


def _biomarker_matches(observed: str, required: str) -> bool:
    observed_norm = _norm(observed)
    required_norm = _norm(required)
    if required_norm == "positive":
        return observed_norm not in {"negative", "not detected", "wild type", "stable"}
    if required_norm == "negative":
        return observed_norm in {"negative", "not detected", "wild type"}
    options = required_norm.split("_or_")
    return observed_norm in options


def _norm(value: str | None) -> str:
    if value is None:
        return ""
    return str(value).strip().lower().replace("-", " ")

