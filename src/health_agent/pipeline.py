from __future__ import annotations

from pathlib import Path

from health_agent.agents import RecommendationAgent
from health_agent.data import load_patients, load_trials


def run_recommendations(
    patients_path: Path,
    trials_path: Path,
    limit: int | None = None,
    max_recommendations: int = 3,
) -> dict[str, list[dict]]:
    patients = load_patients(patients_path)
    trials = load_trials(trials_path)
    if limit is not None:
        patients = patients[:limit]

    recommendations = RecommendationAgent().recommend(
        patients,
        trials,
        max_recommendations=max_recommendations,
    )
    return {
        patient_id: [item.as_dict() for item in patient_recommendations]
        for patient_id, patient_recommendations in recommendations.items()
    }

