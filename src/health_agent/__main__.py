from __future__ import annotations

import argparse
import json
from pathlib import Path

from health_agent.pipeline import run_recommendations


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Health Agent matching.")
    parser.add_argument("--patients", required=True, help="Path to patient JSON.")
    parser.add_argument("--trials", required=True, help="Path to trial JSON.")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    result = run_recommendations(
        patients_path=Path(args.patients),
        trials_path=Path(args.trials),
        limit=args.limit,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

