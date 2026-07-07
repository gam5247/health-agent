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
   - Collects public trial records from ClinicalTrials.gov API v2.
   - Default condition queries are aligned to the official example topics.
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
   - Includes manifest, summary metrics, labels TSV, official example
     predictions, synthetic prediction samples, demo cases, and disclaimer.

## Current Artifact Scale

- Trials: 116
- Official example patients: 10
- Synthetic patients: 1,000
- Retrieved patient-trial pairs: 30,000
- K-EXAONE smoke: 1 patient, top-2, 3 agent calls

## Current Metrics

- Retrieval target trial recall@30: 0.743
- Retrieval potential recall@30: 0.590
- Retrieval recommend recall@30: 0.520
- K-EXAONE HTTP 200 rate in smoke test: 3/3
- LLM valid label rate in smoke test: 1.0
- LLM JSON parse rate in smoke test: 0.667
- LLM deterministic agreement in smoke test: 0.5
- Official example predictions: 10 patients, top-5 recommendations each,
  5 eligible / 7 uncertain / 38 ineligible recommendation labels.

## Interpretation

The artifact is a reproducible competition-style slice, not a clinical
validation set. The current bottlenecks are retrieval quality for sparse
conditions, criterion extraction from free-text protocols, and K-EXAONE JSON
stability. The next improvement should be a stronger condition metadata filter
before BM25, then batch matcher prompts with strict line-protocol outputs to
reduce K-EXAONE latency and parse failures.
