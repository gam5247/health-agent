from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from health_agent.blinded_audit import audit_blinded_records


FORBIDDEN_PATH_TERMS = {
    "answer-key",
    "answer_key",
    "eval-report",
    "eval_report",
    "gpt-e2e-teacher-labeling",
    "gold-label",
    "gold_label",
    "hidden-eval",
    "hidden_eval",
    "teacher-label",
    "teacher_label",
}
FORBIDDEN_JSON_KEYS = {
    "agent_trace",
    "answer_key",
    "criterion_level_judgments",
    "final_assessment",
    "final_eligibility",
    "final_output",
    "gold_label",
    "hidden_label",
    "teacher_label",
    "teacher_rationale",
}
SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"Bearer\s+[A-Za-z0-9._-]{20,}", re.IGNORECASE),
]


def main() -> None:
    args = parse_args()
    errors = assert_workspace_clean(args.workspace)
    if errors:
        print("Agent workspace safety check failed:", file=sys.stderr)
        for error in errors[:100]:
            print(f"- {error}", file=sys.stderr)
        raise SystemExit(1)
    print(json.dumps({"workspace": str(args.workspace), "status": "clean"}, indent=2, sort_keys=True))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fail if an agent runtime workspace contains hidden-label material.")
    parser.add_argument("workspace", type=Path)
    return parser.parse_args()


def assert_workspace_clean(workspace: Path) -> list[str]:
    root = workspace.resolve()
    errors: list[str] = []
    if not root.exists():
        return [f"{root} does not exist"]
    if not root.is_dir():
        return [f"{root} is not a directory"]
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        rel = path.relative_to(root)
        if rel.parts and rel.parts[0] == "outputs":
            continue
        lower_rel = str(rel).replace("\\", "/").lower()
        for term in FORBIDDEN_PATH_TERMS:
            if term in lower_rel:
                errors.append(f"{rel}: forbidden evaluator-only path term '{term}'")
        errors.extend(_scan_file(path, rel))
    return errors


def _scan_file(path: Path, rel: Path) -> list[str]:
    errors: list[str] = []
    try:
        data = path.read_bytes()
    except OSError as exc:
        return [f"{rel}: could not read file: {exc}"]
    for pattern in SECRET_PATTERNS:
        if pattern.search(data.decode("utf-8", errors="ignore")):
            errors.append(f"{rel}: possible secret or bearer token")
    if path.suffix.lower() == ".jsonl":
        errors.extend(_scan_jsonl(path, rel))
    elif path.suffix.lower() == ".json":
        errors.extend(_scan_json(path, rel))
    return errors


def _scan_jsonl(path: Path, rel: Path) -> list[str]:
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                value = json.loads(line)
                if isinstance(value, dict):
                    records.append(value)
                else:
                    errors.append(f"{rel}: JSONL row is not an object")
    except (OSError, json.JSONDecodeError) as exc:
        return [f"{rel}: invalid JSONL: {exc}"]
    if rel.name == "blinded_input_100.jsonl":
        errors.extend(f"{rel}: {error}" for error in audit_blinded_records(records))
        return errors
    for index, record in enumerate(records, start=1):
        errors.extend(_scan_json_keys(record, f"{rel}:{index}"))
    return errors


def _scan_json(path: Path, rel: Path) -> list[str]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"{rel}: invalid JSON: {exc}"]
    return _scan_json_keys(payload, str(rel))


def _scan_json_keys(value: Any, path: str) -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key)
            if key_text in FORBIDDEN_JSON_KEYS:
                errors.append(f"{path}.{key_text}: forbidden evaluator-only key")
            errors.extend(_scan_json_keys(child, f"{path}.{key_text}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(_scan_json_keys(child, f"{path}[{index}]"))
    return errors


if __name__ == "__main__":
    main()
