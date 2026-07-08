from __future__ import annotations

from collections import Counter
from typing import Any

from health_agent.e2e_orchestrator import CRITERION_STATUSES, ELIGIBILITY_LABELS


def evaluate_predictions(
    *,
    answer_records: list[dict[str, Any]],
    prediction_records: list[dict[str, Any]],
) -> dict[str, Any]:
    answer_by_patient = {record["patient_id"]: record for record in answer_records}
    prediction_by_patient = {record["patient_id"]: record for record in prediction_records}
    common_ids = sorted(set(answer_by_patient) & set(prediction_by_patient))

    contract_errors = []
    eligibility_total = 0
    eligibility_correct = 0
    criterion_total = 0
    criterion_correct = 0
    recommendation_set_total = 0
    recommendation_set_exact = 0
    question_link_gold = 0
    question_link_pred = 0
    question_link_hit = 0
    per_patient = []
    confusion = Counter()

    for patient_id in common_ids:
        answer = answer_by_patient[patient_id]
        prediction = prediction_by_patient[patient_id]
        errors = validate_prediction_contract(prediction, answer)
        contract_errors.extend(f"{patient_id}: {error}" for error in errors)

        answer_trials = final_trials_by_id(answer)
        prediction_trials = final_trials_by_id(prediction)
        patient_eligibility_total = 0
        patient_eligibility_correct = 0
        patient_criterion_total = 0
        patient_criterion_correct = 0

        for trial_id, answer_trial in answer_trials.items():
            prediction_trial = prediction_trials.get(trial_id)
            if prediction_trial is None:
                continue
            gold_label = answer_trial.get("eligibility", "")
            pred_label = prediction_trial.get("eligibility", "")
            eligibility_total += 1
            patient_eligibility_total += 1
            confusion[(gold_label, pred_label)] += 1
            if gold_label == pred_label:
                eligibility_correct += 1
                patient_eligibility_correct += 1

            answer_criteria = criteria_by_id(answer_trial)
            prediction_criteria = criteria_by_id(prediction_trial)
            for criterion_id, answer_criterion in answer_criteria.items():
                prediction_criterion = prediction_criteria.get(criterion_id)
                if prediction_criterion is None:
                    continue
                criterion_total += 1
                patient_criterion_total += 1
                if answer_criterion.get("status") == prediction_criterion.get("status"):
                    criterion_correct += 1
                    patient_criterion_correct += 1

        recommendation_set_total += 1
        if recommended_ids(answer) == recommended_ids(prediction):
            recommendation_set_exact += 1

        gold_links = question_links(answer)
        pred_links = question_links(prediction)
        question_link_gold += len(gold_links)
        question_link_pred += len(pred_links)
        question_link_hit += len(gold_links & pred_links)

        per_patient.append(
            {
                "patient_id": patient_id,
                "eligibility_accuracy": safe_ratio(
                    patient_eligibility_correct,
                    patient_eligibility_total,
                ),
                "criterion_status_accuracy": safe_ratio(
                    patient_criterion_correct,
                    patient_criterion_total,
                ),
                "recommended_trial_ids_gold": sorted(recommended_ids(answer)),
                "recommended_trial_ids_pred": sorted(recommended_ids(prediction)),
                "contract_error_count": len(errors),
            }
        )

    missing_predictions = sorted(set(answer_by_patient) - set(prediction_by_patient))
    extra_predictions = sorted(set(prediction_by_patient) - set(answer_by_patient))
    return {
        "schema_version": "health-agent-hidden-eval-v1",
        "patient_count_gold": len(answer_records),
        "patient_count_pred": len(prediction_records),
        "patient_count_compared": len(common_ids),
        "missing_prediction_patient_ids": missing_predictions,
        "extra_prediction_patient_ids": extra_predictions,
        "eligibility": {
            "correct": eligibility_correct,
            "total": eligibility_total,
            "accuracy": safe_ratio(eligibility_correct, eligibility_total),
            "confusion": {
                f"{gold}->{pred}": count
                for (gold, pred), count in sorted(confusion.items())
            },
        },
        "criterion_status": {
            "correct": criterion_correct,
            "total": criterion_total,
            "accuracy": safe_ratio(criterion_correct, criterion_total),
        },
        "recommendation_set": {
            "exact_match": recommendation_set_exact,
            "total": recommendation_set_total,
            "accuracy": safe_ratio(recommendation_set_exact, recommendation_set_total),
        },
        "question_needed_for_links": {
            "gold": question_link_gold,
            "pred": question_link_pred,
            "hit": question_link_hit,
            "precision": safe_ratio(question_link_hit, question_link_pred),
            "recall": safe_ratio(question_link_hit, question_link_gold),
        },
        "contract": {
            "error_count": len(contract_errors),
            "errors": contract_errors[:100],
        },
        "per_patient": per_patient,
        "medical_scope": "Synthetic software-evaluation only; hidden labels are silver labels, not clinical truth.",
        "label_source": "GPT E2E teacher v2 synthetic silver labels",
        "gold_standard_caveat": "Agreement with hidden silver labels is a software benchmark, not clinical ground truth.",
    }


def validate_prediction_contract(prediction: dict[str, Any], answer: dict[str, Any]) -> list[str]:
    errors = []
    final = prediction.get("final_output", {})
    required = [
        "initial_assessment",
        "follow_up_questions",
        "simulated_patient_answers",
        "final_assessment_after_answers",
        "recommended_trials",
        "uncertain_but_actionable_trials",
        "excluded_trials",
        "patient_level_summary",
        "medical_disclaimer",
    ]
    for key in required:
        if key not in final:
            errors.append(f"missing final_output.{key}")
    if not final.get("medical_disclaimer"):
        errors.append("missing medical disclaimer")
    expected_trials = sorted(candidate_trial_ids(answer))
    actual_trials = sorted(row.get("trial_id", "") for row in final_trials(prediction))
    if actual_trials != expected_trials:
        errors.append("final evaluated trials do not match candidate trials")
    initial_trials = sorted(
        row.get("trial_id", "")
        for row in final.get("initial_assessment", {}).get("evaluated_trials", [])
    )
    if initial_trials != expected_trials:
        errors.append("initial evaluated trials do not match candidate trials")
    final_by_id = final_trials_by_id(prediction)
    for row in final_trials(prediction):
        trial_id = row.get("trial_id", "")
        if row.get("eligibility") not in ELIGIBILITY_LABELS:
            errors.append(f"{trial_id}: invalid eligibility")
        if not row.get("explanation"):
            errors.append(f"{trial_id}: missing explanation")
        answer_criteria = {
            criterion["criterion_id"]
            for trial in answer.get("candidate_trials", [])
            if trial["trial_id"] == trial_id
            for criterion in trial.get("criteria_to_assess", [])
        }
        actual_criteria = {item.get("criterion_id", "") for item in row.get("criterion_results", [])}
        if actual_criteria != answer_criteria:
            errors.append(f"{trial_id}: criterion id set mismatch")
        for criterion in row.get("criterion_results", []):
            if criterion.get("status") not in CRITERION_STATUSES:
                errors.append(f"{trial_id}/{criterion.get('criterion_id', '')}: invalid criterion status")
            if "reason" not in criterion:
                errors.append(f"{trial_id}/{criterion.get('criterion_id', '')}: missing reason")
    for row in final.get("recommended_trials", []):
        trial_id = row.get("trial_id", "")
        if row.get("eligibility") != "eligible":
            errors.append(f"{trial_id}: recommended row is not marked eligible")
        if final_by_id.get(trial_id, {}).get("eligibility") != "eligible":
            errors.append(f"{trial_id}: non-eligible final row in recommended_trials")
    for row in final.get("uncertain_but_actionable_trials", []):
        trial_id = row.get("trial_id", "")
        if row.get("eligibility") != "uncertain":
            errors.append(f"{trial_id}: uncertain row is not marked uncertain")
    for row in final.get("excluded_trials", []):
        trial_id = row.get("trial_id", "")
        if row.get("eligibility") != "ineligible":
            errors.append(f"{trial_id}: excluded row is not marked ineligible")
    partition = sorted(
        [row.get("trial_id", "") for row in final.get("recommended_trials", [])]
        + [row.get("trial_id", "") for row in final.get("uncertain_but_actionable_trials", [])]
        + [row.get("trial_id", "") for row in final.get("excluded_trials", [])]
    )
    if partition != expected_trials:
        errors.append("recommended/uncertain/excluded partition does not cover candidates")
    question_ids = {row.get("question_id", "") for row in final.get("follow_up_questions", [])}
    for answer_row in final.get("simulated_patient_answers", []):
        if answer_row.get("question_id") and answer_row["question_id"] not in question_ids:
            errors.append(f"{answer_row['question_id']}: answer references missing question")
    return errors


def final_trials(record: dict[str, Any]) -> list[dict[str, Any]]:
    return (
        record.get("final_output", {})
        .get("final_assessment_after_answers", {})
        .get("evaluated_trials", [])
    )


def final_trials_by_id(record: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["trial_id"]: row for row in final_trials(record)}


def criteria_by_id(trial_row: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        row["criterion_id"]: row
        for row in trial_row.get("criterion_results", [])
    }


def candidate_trial_ids(record: dict[str, Any]) -> list[str]:
    return [
        trial["trial_id"] if isinstance(trial, dict) else str(trial)
        for trial in record.get("candidate_trials", [])
    ]


def recommended_ids(record: dict[str, Any]) -> set[str]:
    return {
        row.get("trial_id", "")
        for row in record.get("final_output", {}).get("recommended_trials", [])
    }


def question_links(record: dict[str, Any]) -> set[tuple[str, str]]:
    links = set()
    for question in record.get("final_output", {}).get("follow_up_questions", []):
        for link in question.get("needed_for", []):
            trial_id = link.get("trial_id", "")
            criterion_id = link.get("criterion_id", "")
            if trial_id or criterion_id:
                links.add((trial_id, criterion_id))
    return links


def safe_ratio(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 4)
