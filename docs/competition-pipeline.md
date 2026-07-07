# Competition Pipeline

This document describes the scaled-down end-to-end artifact path for the
Healthcare Agentic AI Challenge 2026 project.

## One-Command Run

Without API calls:

```bash
python scripts/run_competition_pipeline.py \
  --trial-limit 120 \
  --patient-count 1000 \
  --top-k 30
```

With a small K-EXAONE/Friendli smoke test:

```bash
python scripts/run_competition_pipeline.py \
  --trial-limit 120 \
  --patient-count 1000 \
  --top-k 30 \
  --with-llm-smoke \
  --env-file "<path-to-local-env-file>"
```

## Pipeline Stages

1. `scripts/collect_trials.py`
   - Collects public oncology trial records from ClinicalTrials.gov API v2.
   - Writes normalized records to `data/processed/trials.jsonl`.
   - Stores raw API pages under `data/raw/clinicaltrials/`, which is ignored by git.

2. `scripts/generate_synthetic_patients.py`
   - Generates synthetic patient notes from normalized trial criteria.
   - Writes `data/processed/synthetic_patients.jsonl`.

3. `scripts/build_retrieval_candidates.py`
   - Builds a local lexical RAG index over trial sections and raw criteria.
   - Writes retrieved candidates to `outputs/retrieval_candidates.jsonl`.

4. `scripts/run_llm_eval.py`
   - Optional K-EXAONE/Friendli smoke test.
   - Runs PatientExtractor, EligibilityMatcher, and TrialOrchestrator.
   - Compares LLM labels with the deterministic baseline.

5. `scripts/build_submission_report.py`
   - Builds `artifacts/health-agent-submission/`.
   - Includes manifest, summary metrics, labels TSV, demo cases, and disclaimer.

## Current Artifact Scale

- Trials: 120
- Synthetic patients: 1,000
- Retrieved patient-trial pairs: 30,000
- K-EXAONE smoke: 2 patients, top-2, 6 agent calls

## Current Metrics

- Retrieval target trial recall@30: 0.523
- Retrieval potential recall@30: 0.218
- Retrieval recommend recall@30: 0.095
- K-EXAONE HTTP 200 rate in smoke test: 6/6
- LLM valid label rate in smoke test: 1.0
- LLM JSON parse rate in smoke test: 1.0
- LLM deterministic agreement in smoke test: 1.0

## Interpretation

The artifact is a reproducible competition-style slice, not a clinical
validation set. The most important current bottleneck is retrieval quality:
target trial recall improves with a wider top-k, but lexical retrieval is still
weak for many similar oncology protocols. The next improvement should be a
hybrid condition/biomarker metadata filter before BM25, then batch matcher
prompts to reduce K-EXAONE latency.
