from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from health_agent.data import load_trials, write_jsonl
from health_agent.synthetic import generate_synthetic_patients


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic patient notes for trial matching.")
    parser.add_argument(
        "--trials",
        type=Path,
        default=ROOT / "data" / "processed" / "trials.jsonl",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data" / "processed" / "synthetic_patients.jsonl",
    )
    parser.add_argument("--count", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=20260707)
    args = parser.parse_args()

    trials = load_trials(args.trials)
    records = generate_synthetic_patients(trials, count=args.count, seed=args.seed)
    write_jsonl(args.output, records)
    summary = {
        "synthetic_patients": len(records),
        "trials_source": str(args.trials),
        "output_path": str(args.output),
        "seed": args.seed,
        "scenarios": sorted({record["scenario"] for record in records}),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

