from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the scaled competition pipeline end to end.")
    parser.add_argument("--trial-limit", type=int, default=120)
    parser.add_argument("--patient-count", type=int, default=1000)
    parser.add_argument("--top-k", type=int, default=30)
    parser.add_argument("--seed", type=int, default=20260707)
    parser.add_argument("--with-llm-smoke", action="store_true")
    parser.add_argument("--env-file", type=Path, default=None)
    parser.add_argument("--llm-max-patients", type=int, default=2)
    parser.add_argument("--llm-top-k", type=int, default=2)
    parser.add_argument("--llm-concurrency", type=int, default=2)
    parser.add_argument(
        "--artifact-dir",
        type=Path,
        default=ROOT / "artifacts" / "health-agent-submission",
    )
    args = parser.parse_args()

    trials = ROOT / "data" / "processed" / "trials.jsonl"
    patients = ROOT / "data" / "processed" / "synthetic_patients.jsonl"
    candidates = ROOT / "outputs" / "retrieval_candidates.jsonl"
    retrieval_summary = ROOT / "outputs" / "retrieval_summary.json"
    llm_report = ROOT / "outputs" / "llm_eval_smoke.json"
    llm_labels = ROOT / "outputs" / "llm_eval_smoke_labels.tsv"

    run(
        "collect trials",
        [
            "scripts/collect_trials.py",
            "--limit",
            str(args.trial_limit),
            "--output",
            str(trials),
            "--summary",
            str(ROOT / "data" / "processed" / "trial_collection_summary.json"),
        ],
    )
    run(
        "generate synthetic patients",
        [
            "scripts/generate_synthetic_patients.py",
            "--trials",
            str(trials),
            "--count",
            str(args.patient_count),
            "--seed",
            str(args.seed),
            "--output",
            str(patients),
        ],
    )
    run(
        "build retrieval candidates",
        [
            "scripts/build_retrieval_candidates.py",
            "--patients",
            str(patients),
            "--trials",
            str(trials),
            "--top-k",
            str(args.top_k),
            "--output",
            str(candidates),
            "--summary",
            str(retrieval_summary),
        ],
    )

    report_args = [
        "scripts/build_submission_report.py",
        "--trials",
        str(trials),
        "--patients",
        str(patients),
        "--candidates",
        str(candidates),
        "--retrieval-summary",
        str(retrieval_summary),
        "--output-dir",
        str(args.artifact_dir),
    ]
    if args.with_llm_smoke:
        if args.env_file is None:
            raise SystemExit("--env-file is required with --with-llm-smoke")
        run(
            "run LLM smoke",
            [
                "scripts/run_llm_eval.py",
                "--env-file",
                str(args.env_file),
                "--patients",
                str(patients),
                "--trials",
                str(trials),
                "--max-patients",
                str(args.llm_max_patients),
                "--top-k",
                str(args.llm_top_k),
                "--concurrency",
                str(args.llm_concurrency),
                "--output",
                str(llm_report),
                "--labels-output",
                str(llm_labels),
            ],
        )
        report_args.extend(["--llm-report", str(llm_report)])
    run("build submission artifact", report_args)


def run(label: str, args: list[str]) -> None:
    print(f"== {label} ==")
    completed = subprocess.run([sys.executable, *args], cwd=ROOT)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


if __name__ == "__main__":
    main()

