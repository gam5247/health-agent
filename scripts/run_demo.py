from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from health_agent.pipeline import run_recommendations


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Health Agent demo.")
    parser.add_argument(
        "--patients",
        default=str(ROOT / "data" / "raw" / "oncology-synthetic-patients.json"),
        help="Path to patient JSON.",
    )
    parser.add_argument(
        "--trials",
        default=str(ROOT / "data" / "raw" / "sample-trials.json"),
        help="Path to trial JSON.",
    )
    parser.add_argument("--limit", type=int, default=None, help="Limit patients.")
    args = parser.parse_args()

    recommendations = run_recommendations(
        patients_path=Path(args.patients),
        trials_path=Path(args.trials),
        limit=args.limit,
    )
    print(json.dumps(recommendations, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
