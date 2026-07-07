from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from health_agent.clinicaltrials import fetch_trials
from health_agent.data import write_jsonl


DEFAULT_CONDITIONS = [
    "acute pancreatitis",
    "Graves disease",
    "nephrotic syndrome",
    "bladder cancer",
    "migraine with aura",
    "mucormycosis",
    "hypertrophic pyloric stenosis",
    "idiopathic pulmonary fibrosis",
    "infectious mononucleosis",
    "retinal detachment",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect oncology trials from ClinicalTrials.gov.")
    parser.add_argument("--conditions", nargs="*", default=DEFAULT_CONDITIONS)
    parser.add_argument("--limit", type=int, default=120)
    parser.add_argument("--page-size", type=int, default=50)
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=ROOT / "data" / "raw" / "clinicaltrials",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data" / "processed" / "trials.jsonl",
    )
    parser.add_argument(
        "--summary",
        type=Path,
        default=ROOT / "data" / "processed" / "trial_collection_summary.json",
    )
    args = parser.parse_args()

    trials, summary = fetch_trials(
        conditions=args.conditions,
        limit=args.limit,
        page_size=args.page_size,
        raw_dir=args.raw_dir,
    )
    write_jsonl(args.output, trials)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    summary_payload = {
        "requested_conditions": summary.requested_conditions,
        "fetched_studies": summary.fetched_studies,
        "normalized_trials": summary.normalized_trials,
        "raw_dir": str(args.raw_dir),
        "output_path": str(args.output),
        "source": "https://clinicaltrials.gov/api/v2/studies",
    }
    args.summary.write_text(json.dumps(summary_payload, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(summary_payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
