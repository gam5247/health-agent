from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from health_agent.competition import (
    build_competition_predictions,
    internal_decision_to_eligibility,
)
from health_agent.data import load_patients, load_records, load_trials


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a compact competition-style artifact bundle.")
    parser.add_argument("--trials", type=Path, default=ROOT / "data" / "processed" / "trials.jsonl")
    parser.add_argument(
        "--patients",
        type=Path,
        default=ROOT / "data" / "processed" / "synthetic_patients.jsonl",
    )
    parser.add_argument(
        "--candidates",
        type=Path,
        default=ROOT / "outputs" / "retrieval_candidates.jsonl",
    )
    parser.add_argument("--retrieval-summary", type=Path, default=ROOT / "outputs" / "retrieval_summary.json")
    parser.add_argument("--llm-report", type=Path, default=None)
    parser.add_argument(
        "--example-patients",
        type=Path,
        default=ROOT / "data" / "raw" / "synthetic-patients.json",
    )
    parser.add_argument("--prediction-top-k", type=int, default=5)
    parser.add_argument("--synthetic-prediction-sample", type=int, default=25)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "artifacts" / "health-agent-submission",
    )
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    trials = load_trials(args.trials)
    patients = load_patients(args.patients)
    example_patients = load_patients(args.example_patients)
    candidates = load_records(args.candidates) if args.candidates.exists() else []
    retrieval_summary = read_json(args.retrieval_summary)
    llm_report = read_json(args.llm_report) if args.llm_report else {}
    disclaimer = read_text(ROOT / "MEDICAL_DISCLAIMER.md")
    manifest = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "trial_count": len(trials),
        "synthetic_patient_count": len(patients),
        "official_example_patient_count": len(example_patients),
        "candidate_pair_count": sum(len(row.get("retrieved", [])) for row in candidates),
        "retrieval_summary": retrieval_summary,
        "llm_summary": llm_report.get("summary", {}),
        "source_files": {
            "trials": str(args.trials),
            "patients": str(args.patients),
            "official_examples": str(args.example_patients),
            "candidates": str(args.candidates),
            "llm_report": str(args.llm_report) if args.llm_report else "",
        },
        "disclaimer": "Synthetic software evaluation only; not medical advice.",
    }
    write_json(args.output_dir / "manifest.json", manifest)
    write_json(args.output_dir / "evaluation_summary.json", build_evaluation_summary(manifest))
    (args.output_dir / "labels.tsv").write_text(build_labels_tsv(candidates), encoding="utf-8")
    write_json(
        args.output_dir / "competition_predictions.json",
        build_competition_predictions(
            patients=example_patients,
            trials=trials,
            top_k=args.prediction_top_k,
            disclaimer=disclaimer,
        ),
    )
    write_json(
        args.output_dir / "synthetic_predictions_sample.json",
        build_competition_predictions(
            patients=patients,
            trials=trials,
            top_k=args.prediction_top_k,
            disclaimer=disclaimer,
            max_patients=args.synthetic_prediction_sample,
        ),
    )
    (args.output_dir / "demo_cases.md").write_text(build_demo_cases(candidates[:10]), encoding="utf-8")
    (args.output_dir / "README.md").write_text(build_readme(manifest), encoding="utf-8")
    copy_if_exists(ROOT / "MEDICAL_DISCLAIMER.md", args.output_dir / "MEDICAL_DISCLAIMER.md")
    print(json.dumps({"artifactDir": str(args.output_dir), **manifest}, indent=2, sort_keys=True))


def read_json(path: Path | None) -> dict:
    if path is None or not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_text(path: Path) -> str:
    if not path.exists():
        return "Synthetic software evaluation only; not medical advice."
    return path.read_text(encoding="utf-8")


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_evaluation_summary(manifest: dict) -> dict:
    return {
        "trial_count": manifest["trial_count"],
        "synthetic_patient_count": manifest["synthetic_patient_count"],
        "candidate_pair_count": manifest["candidate_pair_count"],
        "retrieval": manifest.get("retrieval_summary", {}),
        "llm": manifest.get("llm_summary", {}),
        "interpretation": [
            "This is a scaled-down competition artifact, not a clinical validation set.",
            "LLM labels are silver-label drafts and must be reviewed for clinical use.",
            "Deterministic baseline disagreement, missing information, and low confidence should enter human review.",
        ],
    }


def build_labels_tsv(candidates: list[dict]) -> str:
    lines = [
        "PATIENT_ID\tTRIAL_ID\tELIGIBILITY\tINTERNAL_BASELINE_LABEL\tBASELINE_SCORE\tRANK"
    ]
    for row in candidates:
        labels = {item["trial_id"]: item for item in row.get("baseline_labels", [])}
        for rank, retrieved in enumerate(row.get("retrieved", []), start=1):
            trial_id = retrieved.get("trial_id", "")
            label = labels.get(trial_id, {})
            internal_label = str(label.get("decision", ""))
            lines.append(
                "\t".join(
                    [
                        str(row.get("patient_id", "")),
                        str(trial_id),
                        internal_decision_to_eligibility(internal_label),
                        internal_label,
                        str(label.get("score", "")),
                        str(rank),
                    ]
                )
            )
    return "\n".join(lines) + "\n"


def build_demo_cases(candidates: list[dict]) -> str:
    lines = ["# Demo Cases", ""]
    for row in candidates:
        lines.extend(
            [
                f"## {row.get('patient_id', '')}",
                "",
                row.get("clinical_note", ""),
                "",
                "| Rank | Trial ID | Title | Baseline Label | Score |",
                "|---:|---|---|---|---:|",
            ]
        )
        labels = {item["trial_id"]: item for item in row.get("baseline_labels", [])}
        for rank, retrieved in enumerate(row.get("retrieved", [])[:5], start=1):
            trial_id = retrieved.get("trial_id", "")
            label = labels.get(trial_id, {})
            lines.append(
                f"| {rank} | {trial_id} | {retrieved.get('title', '')} | "
                f"{label.get('decision', '')} | {label.get('score', '')} |"
            )
        lines.append("")
    return "\n".join(lines)


def build_readme(manifest: dict) -> str:
    return "\n".join(
        [
            "# Health Agent Submission Artifact",
            "",
            "This folder is a scaled-down competition-style output bundle.",
            "",
            f"- Trials: {manifest['trial_count']}",
            f"- Synthetic patients: {manifest['synthetic_patient_count']}",
            f"- Candidate pairs: {manifest['candidate_pair_count']}",
            "",
            "Files:",
            "",
            "- `manifest.json`: run metadata and source paths",
            "- `evaluation_summary.json`: retrieval and LLM summary metrics",
            "- `labels.tsv`: competition eligibility labels for retrieved pairs",
            "- `competition_predictions.json`: official example patient outputs with criterion-level evidence",
            "- `synthetic_predictions_sample.json`: scaled synthetic sample outputs with the same schema",
            "- `demo_cases.md`: patient-level demo cases",
            "- `MEDICAL_DISCLAIMER.md`: required medical disclaimer",
            "",
            "Validation:",
            "",
            "```bash",
            "python scripts/validate_submission_artifact.py",
            "```",
            "",
            "This artifact is for research prototyping only and is not medical advice.",
            "",
        ]
    )


def copy_if_exists(source: Path, target: Path) -> None:
    if source.exists():
        shutil.copyfile(source, target)


if __name__ == "__main__":
    main()
