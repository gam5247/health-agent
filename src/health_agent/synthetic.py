from __future__ import annotations

import random
from dataclasses import replace
from typing import Any

from health_agent.models import Patient, Trial
from health_agent.orchestrator import patient_to_clinical_note


SEXES = ["female", "male"]
US_STATES = ["CA", "NY", "TX", "WA", "MA", "IL", "FL", "PA", "CO", "AZ"]
BIOMARKER_NEGATIVES = {
    "EGFR": "negative",
    "ALK": "negative",
    "BRAF": "wild type",
    "HER2": "negative",
    "MSI": "stable",
    "FLT3": "negative",
    "BRCA1": "wild type",
    "BRCA2": "wild type",
    "KRAS": "mutated",
}


def generate_synthetic_patients(
    trials: list[Trial],
    *,
    count: int,
    seed: int = 20260707,
) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    usable_trials = [trial for trial in trials if trial.conditions] or trials
    if not usable_trials:
        raise ValueError("At least one trial is required to generate synthetic patients.")
    records = []
    for index in range(count):
        trial_position = index % len(usable_trials)
        trial = usable_trials[trial_position]
        trial_cycle = index // len(usable_trials)
        scenarios = applicable_scenarios(trial)
        scenario = scenarios[(trial_position + trial_cycle) % len(scenarios)]
        patient = patient_for_trial(trial, scenario, index, rng)
        note = patient_to_clinical_note(patient, index)
        record = {
            "generator_version": "health-agent-synthetic-v2",
            "patient_id": patient.patient_id,
            "age": patient.age,
            "sex": patient.sex,
            "diagnosis": patient.diagnosis,
            "stage": patient.stage,
            "ecog": patient.ecog,
            "biomarkers": patient.biomarkers,
            "prior_treatments": patient.prior_treatments,
            "flags": patient.flags,
            "location": patient.location,
            "clinical_note": note,
            "scenario": scenario,
            "target_trial_id": trial.trial_id,
        }
        records.append(record)
    return records


def applicable_scenarios(trial: Trial) -> list[str]:
    scenarios = ["clear_candidate", "wrong_condition", "missing_age"]
    if trial.min_age is not None or trial.max_age is not None:
        scenarios.append("age_conflict")
    if trial.sex in {"female", "male"}:
        scenarios.append("sex_conflict")
    if trial.required_biomarkers:
        scenarios.append("missing_biomarker")
    if trial.excluded_flags:
        scenarios.append("exclusion_conflict")
    if trial.allowed_stages:
        scenarios.append("stage_conflict")
    if trial.max_ecog is not None:
        scenarios.extend(["ecog_conflict", "missing_ecog"])
    if trial.required_prior_treatments:
        scenarios.append("prior_treatment_gap")
    return scenarios


def patient_for_trial(trial: Trial, scenario: str, index: int, rng: random.Random) -> Patient:
    patient_id = f"SYN-GEN-{index + 1:05d}"
    age = choose_age(trial, scenario, rng)
    sex = choose_sex(trial, scenario, rng)
    diagnosis = choose_diagnosis(trial, scenario, rng)
    stage = choose_stage(trial, scenario, rng)
    ecog = choose_ecog(trial, scenario, rng)
    biomarkers = choose_biomarkers(trial, scenario)
    prior_treatments = choose_prior_treatments(trial, scenario)
    flags = choose_flags(trial, scenario)
    patient = Patient(
        patient_id=patient_id,
        age=age,
        sex=sex,
        diagnosis=diagnosis,
        stage=stage,
        ecog=ecog,
        biomarkers=biomarkers,
        prior_treatments=prior_treatments,
        flags=flags,
        location={"country": "US", "state": US_STATES[index % len(US_STATES)]},
        scenario=scenario,
    )
    if scenario == "missing_ecog":
        return replace(patient, ecog=None)
    return patient


def choose_age(trial: Trial, scenario: str, rng: random.Random) -> int | None:
    if scenario == "missing_age":
        return None
    if scenario == "age_conflict":
        if trial.min_age is not None and trial.min_age > 0:
            return trial.min_age - 1
        if trial.max_age is not None:
            return trial.max_age + 1
    minimum = trial.min_age if trial.min_age is not None else 18
    maximum = trial.max_age if trial.max_age is not None else 82
    maximum = max(minimum, min(maximum, 88))
    return rng.randint(minimum, maximum)


def choose_sex(trial: Trial, scenario: str, rng: random.Random) -> str:
    if scenario == "sex_conflict" and trial.sex in {"female", "male"}:
        return "male" if trial.sex == "female" else "female"
    if trial.sex in {"female", "male"}:
        return trial.sex
    return rng.choice(SEXES)


def choose_diagnosis(trial: Trial, scenario: str, rng: random.Random) -> str:
    if scenario == "wrong_condition":
        return rng.choice(
            [
                "advanced renal cell carcinoma",
                "metastatic colorectal cancer",
                "unresectable melanoma",
                "relapsed acute myeloid leukemia",
            ]
        )
    if trial.conditions:
        condition = trial.conditions[0].lower()
        if is_oncology_condition(condition):
            return f"metastatic {condition}"
        return condition
    return "advanced solid tumor"


def is_oncology_condition(condition: str) -> bool:
    oncology_terms = [
        "cancer",
        "carcinoma",
        "leukemia",
        "lymphoma",
        "melanoma",
        "myeloma",
        "neoplasm",
        "sarcoma",
        "tumor",
    ]
    return any(term in condition for term in oncology_terms)


def choose_stage(trial: Trial, scenario: str, rng: random.Random) -> str | None:
    if not trial.allowed_stages and not trial_is_oncology(trial):
        return None
    if scenario == "stage_conflict":
        return "I"
    if trial.allowed_stages:
        return rng.choice(trial.allowed_stages)
    return rng.choice(["III", "IV", None])


def choose_ecog(trial: Trial, scenario: str, rng: random.Random) -> int | None:
    if trial.max_ecog is None and not trial_is_oncology(trial):
        return None
    if scenario == "ecog_conflict":
        return min(4, (trial.max_ecog if trial.max_ecog is not None else 2) + 1)
    maximum = trial.max_ecog if trial.max_ecog is not None else 2
    return rng.randint(0, max(0, maximum))


def trial_is_oncology(trial: Trial) -> bool:
    return any(is_oncology_condition(condition) for condition in trial.conditions)


def choose_biomarkers(trial: Trial, scenario: str) -> dict[str, str]:
    if scenario == "missing_biomarker":
        return {}
    biomarkers = dict(trial.required_biomarkers)
    if scenario == "wrong_condition":
        return {
            marker: BIOMARKER_NEGATIVES.get(marker, "negative")
            for marker in biomarkers
        }
    return biomarkers


def choose_prior_treatments(trial: Trial, scenario: str) -> list[str]:
    if scenario == "prior_treatment_gap":
        return []
    return list(trial.required_prior_treatments)


def choose_flags(trial: Trial, scenario: str) -> dict[str, bool]:
    flags = {flag: False for flag in trial.excluded_flags}
    if scenario == "exclusion_conflict" and trial.excluded_flags:
        flags[trial.excluded_flags[0]] = True
    return flags
