from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from health_agent.data import load_patients, load_trials
from health_agent.llm_client import FriendliClient, FriendliConfig
from health_agent.orchestrator import (
    AgentTokenBudget,
    build_eval_report,
    labels_to_tsv,
    patient_to_clinical_note,
    run_patient_orchestration,
)
from health_agent.rag import build_rag_index, retrieve_trials


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    started = time.perf_counter()
    patients = load_patients(args.patients)
    trials = load_trials(args.trials)
    patients = patients[: args.max_patients]
    index = build_rag_index(trials)

    config = FriendliConfig.from_env(args.env_file)
    client = None
    if not args.dry_run:
        if not config.configured:
            print(
                json.dumps(
                    {
                        "error": "missing_api_configuration",
                        "missing": config.missing,
                        "hint": "Pass --env-file pointing to a local .env, or set OS env vars.",
                    },
                    indent=2,
                ),
                file=sys.stderr,
            )
            raise SystemExit(2)
        client = FriendliClient(config, timeout_sec=args.request_timeout_sec)

    print(
        json.dumps(
            {
                "mode": "health-agent-llm-eval",
                "dryRun": args.dry_run,
                "configured": config.public_status() if not args.dry_run else {"configured": False},
                "syntheticPatients": len(load_patients(args.patients)),
                "syntheticTrials": len(trials),
                "evaluatedPatients": len(patients),
                "topK": args.top_k,
                "concurrency": args.concurrency,
            },
            indent=2,
        )
    )

    token_budget = AgentTokenBudget(
        extractor_max_tokens=args.extractor_max_tokens,
        matcher_max_tokens=args.matcher_max_tokens,
        orchestrator_max_tokens=args.orchestrator_max_tokens,
    )

    results = []
    with ThreadPoolExecutor(max_workers=max(1, args.concurrency)) as executor:
        futures = {}
        for index_number, patient in enumerate(patients):
            note = patient_to_clinical_note(patient, index_number)
            retrieved = retrieve_trials(index, note, args.top_k)
            future = executor.submit(
                run_patient_orchestration,
                patient=patient,
                note=note,
                retrieved=retrieved,
                all_trials=trials,
                client=client,
                token_budget=token_budget,
            )
            futures[future] = patient.patient_id
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            print(
                json.dumps(
                    {
                        "checkpoint": {
                            "patient_id": result["patient_id"],
                            "completed": len(results),
                            "total": len(patients),
                        }
                    }
                )
            )

    results.sort(key=lambda item: item["patient_id"])
    report = build_eval_report(
        started=started,
        synthetic_patients=len(load_patients(args.patients)),
        synthetic_trials=len(trials),
        evaluated_patients=len(patients),
        top_k=args.top_k,
        dry_run=args.dry_run,
        results=results,
    )
    output_path = args.output or default_output_path()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    if args.labels_output:
        args.labels_output.parent.mkdir(parents=True, exist_ok=True)
        args.labels_output.write_text(labels_to_tsv(results), encoding="utf-8")

    print(json.dumps(report["summary"], indent=2, sort_keys=True))
    print(json.dumps({"reportPath": str(output_path)}, indent=2))


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description="Run K-EXAONE/Friendli LLM evaluation.")
    parser.add_argument(
        "--patients",
        type=Path,
        default=root / "data" / "raw" / "oncology-synthetic-patients.json",
    )
    parser.add_argument(
        "--trials",
        type=Path,
        default=root / "data" / "raw" / "sample-trials.json",
    )
    parser.add_argument("--env-file", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--labels-output", type=Path, default=None)
    parser.add_argument("--max-patients", type=int, default=3)
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--concurrency", type=int, default=1)
    parser.add_argument("--request-timeout-sec", type=int, default=180)
    parser.add_argument("--extractor-max-tokens", type=int, default=900)
    parser.add_argument("--matcher-max-tokens", type=int, default=1800)
    parser.add_argument("--orchestrator-max-tokens", type=int, default=1400)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run RAG and deterministic baseline without API calls.",
    )
    return parser.parse_args(argv)


def default_output_path() -> Path:
    stamp = datetime.now(timezone.utc).isoformat().replace(":", "-").replace(".", "-")
    return Path("outputs") / f"health-agent-llm-eval-{stamp}.json"


if __name__ == "__main__":
    main()

