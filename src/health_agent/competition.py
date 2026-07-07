from __future__ import annotations

from dataclasses import asdict
from typing import Any, Iterable

from health_agent.agents import TrialMatchingAgent
from health_agent.models import MatchEvidence, Patient, Recommendation, Trial
from health_agent.orchestrator import patient_to_clinical_note
from health_agent.rag import RetrievedTrial, build_rag_index, retrieve_trials


ELIGIBILITY_LABELS = ["eligible", "ineligible", "uncertain"]
CRITERION_LABELS = ["satisfied", "violated", "unknown", "not_applicable"]

INTERNAL_TO_ELIGIBILITY = {
    "recommend": "eligible",
    "needs_more_info": "uncertain",
    "not_recommended": "ineligible",
}

INTERNAL_TO_CRITERION = {
    "matched": "satisfied",
    "conflict": "violated",
    "missing": "unknown",
}


def internal_decision_to_eligibility(decision: str) -> str:
    return INTERNAL_TO_ELIGIBILITY.get(str(decision), "uncertain")


def build_competition_predictions(
    *,
    patients: Iterable[Patient],
    trials: Iterable[Trial],
    top_k: int,
    disclaimer: str,
    max_patients: int | None = None,
) -> dict[str, Any]:
    trial_list = list(trials)
    patient_list = list(patients)
    if max_patients is not None:
        patient_list = patient_list[:max_patients]

    index = build_rag_index(trial_list)
    matcher = TrialMatchingAgent()
    patient_outputs = []
    for patient_index, patient in enumerate(patient_list):
        note = patient_to_clinical_note(patient, patient_index)
        retrieved = retrieve_trials(index, note, top_k)
        recommendations = [
            build_competition_recommendation(
                patient=patient,
                recommendation=matcher.match(patient, item.trial),
                retrieved=item,
            )
            for item in retrieved
        ]
        recommendations.sort(
            key=lambda item: (
                eligibility_rank(item["eligibility"]),
                item["recommendation_score"],
                item["retrieval_score"],
            ),
            reverse=True,
        )
        for rank, recommendation in enumerate(recommendations, start=1):
            recommendation["rank"] = rank
        patient_outputs.append(
            {
                "patient_id": patient.patient_id,
                "clinical_note": note,
                "extracted_profile": patient_profile_payload(patient),
                "recommendations": recommendations,
                "recommended_trial_order": [
                    recommendation["trial_id"] for recommendation in recommendations
                ],
            }
        )

    return {
        "schema_version": "health-agent-competition-v1",
        "label_sets": {
            "eligibility": ELIGIBILITY_LABELS,
            "criterion_status": CRITERION_LABELS,
        },
        "disclaimer": disclaimer.strip(),
        "trial_count": len(trial_list),
        "patient_count": len(patient_outputs),
        "patients": patient_outputs,
    }


def build_competition_recommendation(
    *,
    patient: Patient,
    recommendation: Recommendation,
    retrieved: RetrievedTrial,
) -> dict[str, Any]:
    criterion_results = build_criterion_results(recommendation, retrieved.trial)
    eligibility = aggregate_eligibility(criterion_results)
    questions = follow_up_questions(recommendation, criterion_results)
    return {
        "rank": 0,
        "trial_id": recommendation.trial_id,
        "trial_title": recommendation.trial_title,
        "trial_source_url": retrieved.trial.source_url or "",
        "eligibility": eligibility,
        "internal_decision": recommendation.decision,
        "recommendation_score": recommendation_score(
            eligibility=eligibility,
            baseline_score=recommendation.score,
            unknown_count=sum(
                item["status"] == "unknown" for item in criterion_results
            ),
        ),
        "retrieval_score": round(float(retrieved.score), 3),
        "criterion_results": criterion_results,
        "follow_up_questions": questions,
        "explanation": explain_recommendation(
            eligibility=eligibility,
            recommendation=recommendation,
            criterion_results=criterion_results,
        ),
        "patient_id": patient.patient_id,
    }


def build_criterion_results(
    recommendation: Recommendation,
    trial: Trial,
) -> list[dict[str, Any]]:
    results = []
    for index, evidence in enumerate(recommendation.evidence, start=1):
        results.append(criterion_result_from_evidence(trial, evidence, index))
    results.extend(not_applicable_results(trial, len(results)))
    return results


def criterion_result_from_evidence(
    trial: Trial,
    evidence: MatchEvidence,
    index: int,
) -> dict[str, Any]:
    criterion_type = "exclusion" if evidence.criterion.startswith("flag:") else "inclusion"
    status = INTERNAL_TO_CRITERION.get(evidence.status, "unknown")
    if criterion_type == "exclusion" and evidence.status == "matched":
        status = "satisfied"
    return {
        "criterion_id": f"{trial.trial_id}-{criterion_type[:1].upper()}-{index:03d}",
        "criterion_type": criterion_type,
        "criterion": evidence.criterion,
        "status": status,
        "trial_evidence": trial_evidence_for(trial, evidence),
        "patient_evidence": evidence.detail,
        "reason": evidence.detail,
        "confidence": confidence_for_status(status),
    }


def not_applicable_results(trial: Trial, offset: int) -> list[dict[str, Any]]:
    checks = []
    if str(trial.sex or "").lower() in {"", "all", "any"}:
        checks.append(("sex", "Trial is open to all recorded sexes."))
    if not trial.allowed_stages:
        checks.append(("stage", "No explicit stage restriction was normalized."))
    if trial.max_ecog is None:
        checks.append(("ecog", "No explicit ECOG threshold was normalized."))
    if not trial.required_biomarkers:
        checks.append(("biomarker", "No required biomarker was normalized."))

    return [
        {
            "criterion_id": f"{trial.trial_id}-N-{offset + index:03d}",
            "criterion_type": "not_applicable",
            "criterion": criterion,
            "status": "not_applicable",
            "trial_evidence": evidence,
            "patient_evidence": "",
            "reason": evidence,
            "confidence": 1.0,
        }
        for index, (criterion, evidence) in enumerate(checks, start=1)
    ]


def aggregate_eligibility(criterion_results: list[dict[str, Any]]) -> str:
    statuses = {item.get("status") for item in criterion_results}
    applicable = [status for status in statuses if status != "not_applicable"]
    if "violated" in statuses:
        return "ineligible"
    if "unknown" in statuses:
        return "uncertain"
    if "satisfied" in statuses:
        return "eligible"
    if not applicable:
        return "uncertain"
    return "uncertain"


def follow_up_questions(
    recommendation: Recommendation,
    criterion_results: list[dict[str, Any]],
) -> list[str]:
    questions = list(recommendation.questions)
    known = set(questions)
    for item in criterion_results:
        if item.get("status") != "unknown":
            continue
        question = question_for_criterion(str(item.get("criterion", "")))
        if question not in known:
            questions.append(question)
            known.add(question)
    return questions


def question_for_criterion(criterion: str) -> str:
    if criterion.startswith("field:"):
        field = criterion.split(":", 1)[1].replace("_", " ")
        return f"What is the patient's {field}?"
    if criterion.startswith("biomarker:"):
        marker = criterion.split(":", 1)[1]
        return f"What is the patient's {marker} biomarker result?"
    if criterion.startswith("flag:"):
        flag = criterion.split(":", 1)[1].replace("_", " ")
        return f"Does the patient have {flag}?"
    return f"What patient information is available for {criterion}?"


def explain_recommendation(
    *,
    eligibility: str,
    recommendation: Recommendation,
    criterion_results: list[dict[str, Any]],
) -> str:
    satisfied = sum(item["status"] == "satisfied" for item in criterion_results)
    violated = sum(item["status"] == "violated" for item in criterion_results)
    unknown = sum(item["status"] == "unknown" for item in criterion_results)
    if eligibility == "eligible":
        return (
            f"Ranked as eligible because {satisfied} applicable criteria were "
            "satisfied and no violated or unknown criteria were found."
        )
    if eligibility == "ineligible":
        return (
            f"Ranked as ineligible because {violated} criterion conflicts were "
            f"found. Baseline rationale: {recommendation.rationale}"
        )
    return (
        f"Ranked as uncertain because {unknown} required criteria need more "
        f"information. Baseline rationale: {recommendation.rationale}"
    )


def recommendation_score(
    *,
    eligibility: str,
    baseline_score: float,
    unknown_count: int,
) -> float:
    if eligibility == "eligible":
        base = 0.75 + 0.25 * baseline_score
    elif eligibility == "uncertain":
        base = 0.45 + 0.25 * baseline_score - min(0.2, unknown_count * 0.03)
    else:
        base = 0.1 + 0.2 * baseline_score
    return round(max(0.0, min(1.0, base)), 3)


def eligibility_rank(label: str) -> int:
    return {"eligible": 3, "uncertain": 2, "ineligible": 1}.get(label, 0)


def trial_evidence_for(trial: Trial, evidence: MatchEvidence) -> str:
    if evidence.criterion == "condition":
        return "Trial conditions: " + ", ".join(trial.conditions)
    if evidence.criterion == "age":
        return f"Trial age range: {trial.min_age} to {trial.max_age}"
    if evidence.criterion == "sex":
        return f"Trial sex criterion: {trial.sex}"
    if evidence.criterion == "stage":
        return "Allowed stages: " + ", ".join(trial.allowed_stages)
    if evidence.criterion == "ecog":
        return f"Maximum ECOG: {trial.max_ecog}"
    if evidence.criterion.startswith("biomarker:"):
        marker = evidence.criterion.split(":", 1)[1]
        return f"Required biomarker {marker}: {trial.required_biomarkers.get(marker, '')}"
    if evidence.criterion.startswith("flag:"):
        flag = evidence.criterion.split(":", 1)[1]
        return f"Exclusion criterion: {flag.replace('_', ' ')}"
    if evidence.criterion.startswith("field:"):
        return f"Required patient field: {evidence.criterion.split(':', 1)[1]}"
    return trial.eligibility_criteria or trial.summary or trial.title


def confidence_for_status(status: str) -> float:
    if status == "satisfied":
        return 0.82
    if status == "violated":
        return 0.88
    if status == "unknown":
        return 0.55
    return 1.0


def patient_profile_payload(patient: Patient) -> dict[str, Any]:
    payload = asdict(patient)
    return {
        key: value
        for key, value in payload.items()
        if key not in {"clinical_note"} and value not in (None, "", [], {})
    }
