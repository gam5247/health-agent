from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from health_agent.data import load_patients, load_trials
from health_agent.teacher_student import (
    build_markdown_report,
    build_target_pairs,
    compare_teacher_student,
    label_with_deterministic_baseline,
    label_with_friendli,
    label_with_openai,
    read_jsonl,
    write_jsonl,
    write_teacher_web_files,
)


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    patients = load_patients(args.patients)
    trials = load_trials(args.trials)
    pairs = build_target_pairs(
        patients=patients,
        trials=trials,
        patient_count=args.patient_count,
    )
    if len(pairs) < args.patient_count:
        print(
            json.dumps(
                {
                    "warning": "fewer_pairs_than_requested",
                    "requested": args.patient_count,
                    "built": len(pairs),
                },
                indent=2,
            )
        )
    pairs_path = args.output_dir / "pairs.jsonl"
    write_jsonl(pairs_path, pairs)
    write_teacher_web_files(args.output_dir, pairs)

    calls: dict[str, list[dict]] = {}

    teacher_labels_path = args.output_dir / "teacher_labels.jsonl"
    if args.teacher_provider == "none":
        pass
    elif args.teacher_provider == "file":
        if args.teacher_labels is None:
            raise SystemExit("--teacher-labels is required with --teacher-provider file")
        teacher_labels = read_jsonl(args.teacher_labels)
        write_jsonl(teacher_labels_path, teacher_labels)
    elif args.teacher_provider == "deterministic":
        teacher_labels = label_with_deterministic_baseline(pairs)
        write_jsonl(teacher_labels_path, teacher_labels)
    elif args.teacher_provider == "openai":
        teacher_labels, teacher_calls = label_with_openai(
            pairs=pairs,
            env_file=args.teacher_env_file,
            batch_size=args.batch_size,
            concurrency=args.teacher_concurrency,
            request_timeout_sec=args.request_timeout_sec,
            max_tokens=args.max_tokens,
        )
        calls["teacher_openai"] = teacher_calls
        write_jsonl(teacher_labels_path, teacher_labels)
    else:
        raise SystemExit(f"Unsupported teacher provider: {args.teacher_provider}")

    student_labels_path = args.output_dir / "student_labels.jsonl"
    if args.student_provider == "none":
        pass
    elif args.student_provider == "deterministic":
        student_labels = label_with_deterministic_baseline(pairs)
        write_jsonl(student_labels_path, student_labels)
    elif args.student_provider == "friendli":
        student_labels, student_calls = label_with_friendli(
            pairs=pairs,
            env_file=args.student_env_file,
            batch_size=args.batch_size,
            concurrency=args.student_concurrency,
            request_timeout_sec=args.request_timeout_sec,
            max_tokens=args.max_tokens,
        )
        calls["student_friendli"] = student_calls
        write_jsonl(student_labels_path, student_labels)
    else:
        raise SystemExit(f"Unsupported student provider: {args.student_provider}")

    if teacher_labels_path.exists() and student_labels_path.exists():
        teacher_labels = read_jsonl(teacher_labels_path)
        student_labels = read_jsonl(student_labels_path)
        comparison = compare_teacher_student(
            pairs=pairs,
            teacher_labels=teacher_labels,
            student_labels=student_labels,
        )
        (args.output_dir / "comparison.json").write_text(
            json.dumps(comparison, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (args.output_dir / "report.md").write_text(
            build_markdown_report(comparison, calls),
            encoding="utf-8",
        )
    if calls:
        (args.output_dir / "model_calls.json").write_text(
            json.dumps(calls, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    print(
        json.dumps(
            {
                "output_dir": str(args.output_dir),
                "pairs": len(pairs),
                "teacher_provider": args.teacher_provider,
                "student_provider": args.student_provider,
                "teacher_labels": teacher_labels_path.exists(),
                "student_labels": student_labels_path.exists(),
                "comparison": (args.output_dir / "comparison.json").exists(),
            },
            indent=2,
            sort_keys=True,
        )
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run teacher-student clinical trial label evaluation."
    )
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
        "--output-dir",
        type=Path,
        default=ROOT / "artifacts" / "teacher-student-eval",
    )
    parser.add_argument("--patient-count", type=int, default=100)
    parser.add_argument(
        "--teacher-provider",
        choices=["none", "file", "deterministic", "openai"],
        default="none",
    )
    parser.add_argument("--teacher-labels", type=Path, default=None)
    parser.add_argument("--teacher-env-file", type=Path, default=None)
    parser.add_argument(
        "--student-provider",
        choices=["none", "deterministic", "friendli"],
        default="none",
    )
    parser.add_argument("--student-env-file", type=Path, default=None)
    parser.add_argument("--batch-size", type=int, default=10)
    parser.add_argument("--teacher-concurrency", type=int, default=1)
    parser.add_argument("--student-concurrency", type=int, default=2)
    parser.add_argument("--request-timeout-sec", type=int, default=240)
    parser.add_argument("--max-tokens", type=int, default=8000)
    return parser.parse_args()


if __name__ == "__main__":
    main()
