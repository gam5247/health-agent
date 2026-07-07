from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from health_agent.data import load_patients, load_trials, write_jsonl
from health_agent.orchestrator import patient_to_clinical_note
from health_agent.rag import build_rag_index, retrieve_trials
from health_agent.scoring import evaluate_trial


def main() -> None:
    parser = argparse.ArgumentParser(description="Build patient-trial retrieval candidates.")
    parser.add_argument(
        "--patients",
        type=Path,
        default=ROOT / "data" / "processed" / "synthetic_patients.jsonl",
    )
    parser.add_argument(
        "--trials",
        type=Path,
        default=ROOT / "data" / "processed" / "trials.jsonl",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "outputs" / "retrieval_candidates.jsonl",
    )
    parser.add_argument(
        "--summary",
        type=Path,
        default=ROOT / "outputs" / "retrieval_summary.json",
    )
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--limit-patients", type=int, default=0)
    args = parser.parse_args()

    patients = load_patients(args.patients)
    trials = load_trials(args.trials)
    if args.limit_patients:
        patients = patients[: args.limit_patients]
    index = build_rag_index(trials)
    rows = []
    recommend_hits = 0
    recommend_total = 0
    potential_hits = 0
    potential_total = 0
    target_hits = 0
    target_total = 0

    for patient_index, patient in enumerate(patients):
        note = patient_to_clinical_note(patient, patient_index)
        retrieved = retrieve_trials(index, note, args.top_k)
        retrieved_ids = {item.trial.trial_id for item in retrieved}
        expected_recommend = [
            trial.trial_id
            for trial in trials
            if evaluate_trial(patient, trial).decision == "recommend"
        ]
        expected_potential = [
            trial.trial_id
            for trial in trials
            if evaluate_trial(patient, trial).decision != "not_recommended"
        ]
        if patient.target_trial_id:
            target_total += 1
            if patient.target_trial_id in retrieved_ids:
                target_hits += 1
        recommend_hits += len([trial_id for trial_id in expected_recommend if trial_id in retrieved_ids])
        recommend_total += len(expected_recommend)
        potential_hits += len([trial_id for trial_id in expected_potential if trial_id in retrieved_ids])
        potential_total += len(expected_potential)
        rows.append(
            {
                "patient_id": patient.patient_id,
                "scenario": patient.scenario,
                "target_trial_id": patient.target_trial_id,
                "clinical_note": note,
                "expected_recommend_trial_ids": expected_recommend,
                "expected_potential_trial_ids": expected_potential,
                "retrieved": [item.as_dict() for item in retrieved],
                "baseline_labels": [
                    {
                        "trial_id": item.trial.trial_id,
                        "decision": evaluate_trial(patient, item.trial).decision,
                        "score": evaluate_trial(patient, item.trial).score,
                    }
                    for item in retrieved
                ],
            }
        )

    summary = {
        "patients": len(patients),
        "trials": len(trials),
        "topK": args.top_k,
        "candidatePairs": sum(len(row["retrieved"]) for row in rows),
        "recommendRecallAtK": ratio(recommend_hits, recommend_total),
        "potentialRecallAtK": ratio(potential_hits, potential_total),
        "targetTrialRecallAtK": ratio(target_hits, target_total),
        "outputPath": str(args.output),
    }
    write_jsonl(args.output, rows)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))


def ratio(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 1.0
    return round(numerator / denominator, 3)


if __name__ == "__main__":
    main()
