from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from health_agent.blinded_audit import audit_blinded_records
from scripts.assert_agent_workspace_clean import assert_workspace_clean


DEFAULT_INPUT = ROOT / "artifacts" / "e2e-orchestration-eval" / "blinded_input_100.jsonl"
RUNTIME_FILES = [
    "scripts/run_e2e_orchestration_v2.py",
    "src/health_agent/e2e_orchestrator.py",
    "MEDICAL_DISCLAIMER.md",
]


def main() -> None:
    args = parse_args()
    output_dir = prepare_output_dir(args.output_dir, args.force)
    input_records = read_jsonl(args.blinded_input)
    if args.max_patients is not None:
        input_records = input_records[: args.max_patients]
    audit_errors = audit_blinded_records(input_records)
    if audit_errors:
        raise SystemExit("Blinded input failed recursive audit:\n" + "\n".join(audit_errors[:50]))

    copied_files = []
    for rel in RUNTIME_FILES:
        src = ROOT / rel
        dst = output_dir / rel
        copy_file(src, dst)
        copied_files.append(rel)
    init_path = output_dir / "src" / "health_agent" / "__init__.py"
    init_path.write_text('"""Minimal package for isolated E2E orchestration runs."""\n', encoding="utf-8")
    copied_files.append("src/health_agent/__init__.py")
    input_dst = output_dir / "artifacts" / "e2e-orchestration-eval" / "blinded_input_100.jsonl"
    write_jsonl(input_dst, input_records)
    copied_files.append("artifacts/e2e-orchestration-eval/blinded_input_100.jsonl")

    readme_path = output_dir / "README_AGENT_WORKSPACE.md"
    write_agent_readme(readme_path)
    copied_files.append("README_AGENT_WORKSPACE.md")

    manifest = {
        "schema_version": "health-agent-agent-workspace-v1",
        "patient_count": len(input_records),
        "blinded_input": "artifacts/e2e-orchestration-eval/blinded_input_100.jsonl",
        "blinded_input_sha256": sha256_file(input_dst),
        "copied_files": copied_files,
        "contains_hidden_labels": False,
        "runner_answer_key_access": False,
        "note": "Agent execution workspace only. Evaluator-only answer keys and scoring scripts are intentionally excluded.",
    }
    manifest_path = output_dir / "agent_workspace_manifest.json"
    manifest_path.write_bytes((json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8"))

    clean_errors = assert_workspace_clean(output_dir)
    if clean_errors:
        raise SystemExit("Agent workspace failed clean check:\n" + "\n".join(clean_errors[:100]))
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build an answer-key-free workspace for agent-side E2E runs.")
    parser.add_argument(
        "--blinded-input",
        type=Path,
        default=DEFAULT_INPUT,
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "artifacts" / "e2e-orchestration-agent-workspace",
    )
    parser.add_argument("--max-patients", type=int, default=None)
    parser.add_argument("--force", action="store_true", help="Replace a non-empty output directory after safety checks.")
    return parser.parse_args()


def prepare_output_dir(path: Path, force: bool) -> Path:
    resolved = path.resolve()
    if resolved == ROOT.resolve():
        raise SystemExit("Refusing to use repository root as the agent workspace output directory.")
    if resolved.exists() and any(resolved.iterdir()):
        if not force:
            raise SystemExit(f"{resolved} is not empty; pass --force to replace it.")
        if ROOT.resolve() in resolved.parents:
            shutil.rmtree(resolved)
        else:
            raise SystemExit("Refusing to remove a non-repository output directory.")
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                records.append(json.loads(line))
    return records


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
            handle.write("\n")


def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def write_agent_readme(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "# Health Agent E2E Agent Workspace",
                "",
                "This directory is for prediction-side execution only.",
                "It contains the runner, deterministic orchestration code, and blinded input.",
                "It intentionally does not contain hidden labels, evaluator code, or scoring reports.",
                "",
                "Run:",
                "",
                "```powershell",
                "python scripts\\run_e2e_orchestration_v2.py",
                "```",
                "",
                "The output is written under `outputs/` inside this workspace.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    main()
