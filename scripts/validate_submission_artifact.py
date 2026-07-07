from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "manifest.json",
    "evaluation_summary.json",
    "labels.tsv",
    "competition_predictions.json",
    "synthetic_predictions_sample.json",
    "MEDICAL_DISCLAIMER.md",
]
ELIGIBILITY_LABELS = {"eligible", "ineligible", "uncertain"}
CRITERION_LABELS = {"satisfied", "violated", "unknown", "not_applicable"}


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate submission artifact shape.")
    parser.add_argument(
        "--artifact-dir",
        type=Path,
        default=ROOT / "artifacts" / "health-agent-submission",
    )
    args = parser.parse_args()
    errors = validate_artifact(args.artifact_dir)
    if errors:
        print(json.dumps({"ok": False, "errors": errors}, indent=2), file=sys.stderr)
        raise SystemExit(1)
    predictions = read_json(args.artifact_dir / "competition_predictions.json")
    print(
        json.dumps(
            {
                "ok": True,
                "artifact_dir": str(args.artifact_dir),
                "official_example_patients": len(predictions.get("patients", [])),
                "trial_count": predictions.get("trial_count"),
            },
            indent=2,
            sort_keys=True,
        )
    )


def validate_artifact(artifact_dir: Path) -> list[str]:
    errors: list[str] = []
    for filename in REQUIRED_FILES:
        path = artifact_dir / filename
        if not path.exists():
            errors.append(f"missing required file: {filename}")
    if errors:
        return errors

    predictions = read_json(artifact_dir / "competition_predictions.json")
    if predictions.get("schema_version") != "health-agent-competition-v1":
        errors.append("competition_predictions.json has unexpected schema_version")
    labels = predictions.get("label_sets", {})
    if set(labels.get("eligibility", [])) != ELIGIBILITY_LABELS:
        errors.append("eligibility label set mismatch")
    if set(labels.get("criterion_status", [])) != CRITERION_LABELS:
        errors.append("criterion status label set mismatch")
    if not predictions.get("disclaimer"):
        errors.append("missing disclaimer in competition_predictions.json")

    for patient in predictions.get("patients", []):
        patient_id = str(patient.get("patient_id", ""))
        if not patient.get("clinical_note"):
            errors.append(f"{patient_id}: missing clinical_note")
        recommendations = patient.get("recommendations", [])
        if not recommendations:
            errors.append(f"{patient_id}: missing recommendations")
        for recommendation in recommendations:
            validate_recommendation(patient_id, recommendation, errors)

    header = (artifact_dir / "labels.tsv").read_text(encoding="utf-8").splitlines()[0]
    expected_header = (
        "PATIENT_ID\tTRIAL_ID\tELIGIBILITY\tINTERNAL_BASELINE_LABEL\t"
        "BASELINE_SCORE\tRANK"
    )
    if header != expected_header:
        errors.append("labels.tsv header mismatch")
    return errors


def validate_recommendation(
    patient_id: str,
    recommendation: dict,
    errors: list[str],
) -> None:
    trial_id = str(recommendation.get("trial_id", ""))
    eligibility = recommendation.get("eligibility")
    if eligibility not in ELIGIBILITY_LABELS:
        errors.append(f"{patient_id}/{trial_id}: bad eligibility {eligibility}")
    if "explanation" not in recommendation:
        errors.append(f"{patient_id}/{trial_id}: missing explanation")
    if "follow_up_questions" not in recommendation:
        errors.append(f"{patient_id}/{trial_id}: missing follow_up_questions")
    criteria = recommendation.get("criterion_results", [])
    if not criteria:
        errors.append(f"{patient_id}/{trial_id}: missing criterion_results")
    for criterion in criteria:
        status = criterion.get("status")
        if status not in CRITERION_LABELS:
            errors.append(f"{patient_id}/{trial_id}: bad criterion status {status}")
        for key in ["criterion_id", "criterion_type", "criterion", "reason"]:
            if key not in criterion:
                errors.append(f"{patient_id}/{trial_id}: criterion missing {key}")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
