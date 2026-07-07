from __future__ import annotations

from dataclasses import replace
from typing import Iterable

from health_agent.models import MatchEvidence, Patient, Recommendation, Trial
from health_agent.scoring import evaluate_trial


class TrialProtocolAgent:
    """Normalizes trial protocol-like dictionaries into Trial objects."""

    def parse(self, item: dict) -> Trial:
        return Trial.from_mapping(item)

    def parse_many(self, items: Iterable[dict]) -> list[Trial]:
        return [self.parse(item) for item in items]


class PatientProfileAgent:
    """Normalizes patient dictionaries into Patient objects."""

    def parse(self, item: dict) -> Patient:
        return Patient.from_mapping(item)

    def parse_many(self, items: Iterable[dict]) -> list[Patient]:
        return [self.parse(item) for item in items]


class MissingInformationAgent:
    """Turns missing evidence into focused follow-up questions."""

    FIELD_QUESTIONS = {
        "age": "What is the patient's age?",
        "sex": "What sex is recorded for trial eligibility purposes?",
        "diagnosis": "What is the confirmed diagnosis?",
        "stage": "What is the current disease stage?",
        "ecog": "What is the current ECOG performance status?",
        "prior_treatments": "Which prior systemic treatments has the patient received?",
    }

    def questions_for(self, evidence: Iterable[MatchEvidence]) -> list[str]:
        questions: list[str] = []
        seen: set[str] = set()
        for item in evidence:
            if item.status != "missing":
                continue
            question = self._question_for_criterion(item.criterion)
            if question not in seen:
                questions.append(question)
                seen.add(question)
        return questions

    def _question_for_criterion(self, criterion: str) -> str:
        if criterion.startswith("biomarker:"):
            biomarker = criterion.split(":", 1)[1]
            return f"What is the patient's {biomarker} biomarker result?"
        if criterion.startswith("flag:"):
            flag = criterion.split(":", 1)[1].replace("_", " ")
            return f"Does the patient have {flag}?"
        if criterion.startswith("field:"):
            field = criterion.split(":", 1)[1]
            return self.FIELD_QUESTIONS.get(field, f"What is the patient's {field}?")
        return f"What information is available for {criterion}?"


class TrialMatchingAgent:
    """Scores one patient against one trial and attaches questions."""

    def __init__(self, missing_agent: MissingInformationAgent | None = None) -> None:
        self.missing_agent = missing_agent or MissingInformationAgent()

    def match(self, patient: Patient, trial: Trial) -> Recommendation:
        recommendation = evaluate_trial(patient, trial)
        questions = self.missing_agent.questions_for(recommendation.evidence)
        return replace(recommendation, questions=questions)


class RecommendationAgent:
    """Ranks trial recommendations for each patient."""

    def __init__(self, matching_agent: TrialMatchingAgent | None = None) -> None:
        self.matching_agent = matching_agent or TrialMatchingAgent()

    def recommend_for_patient(
        self,
        patient: Patient,
        trials: Iterable[Trial],
        max_recommendations: int = 3,
    ) -> list[Recommendation]:
        ranked = [self.matching_agent.match(patient, trial) for trial in trials]
        ranked.sort(key=lambda item: (item.score, item.decision == "recommend"), reverse=True)
        return ranked[:max_recommendations]

    def recommend(
        self,
        patients: Iterable[Patient],
        trials: Iterable[Trial],
        max_recommendations: int = 3,
    ) -> dict[str, list[Recommendation]]:
        trial_list = list(trials)
        return {
            patient.patient_id: self.recommend_for_patient(
                patient,
                trial_list,
                max_recommendations=max_recommendations,
            )
            for patient in patients
        }

