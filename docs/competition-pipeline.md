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

With a small legacy K-EXAONE/Friendli smoke test:

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
   - Optional legacy K-EXAONE/Friendli smoke test.
   - Runs PatientExtractor, EligibilityMatcher, and TrialOrchestrator.
   - Compares LLM labels with the deterministic baseline.

4b. `scripts/run_solar_e2e_orchestration.py`
   - Solar Pro 3 isolated development-eval runner for the competition-format E2E contract.
   - Uses native function calling to read the local patient/trial database.
   - Does not accept an answer-key argument.

5. `scripts/build_submission_report.py`
   - Builds `artifacts/health-agent-submission/`.
   - Includes manifest, summary metrics, labels TSV, official example
     predictions, synthetic prediction samples, demo cases, and disclaimer.

## Current Artifact Scale

- Trials: 116
- Official example patients: 10
- Synthetic patients: 1,000
- Retrieved patient-trial pairs: 30,000
- Legacy K-EXAONE smoke: 1 patient, top-2, 3 agent calls

## Current Metrics

- Retrieval target trial recall@30: 0.743
- Retrieval potential recall@30: 0.590
- Retrieval recommend recall@30: 0.520
- Legacy K-EXAONE HTTP 200 rate in smoke test: 3/3
- LLM valid label rate in smoke test: 1.0
- LLM JSON parse rate in smoke test: 0.667
- LLM deterministic agreement in smoke test: 0.5
- Official example predictions: 10 patients, five candidate judgments each,
  5 eligible / 7 uncertain / 38 ineligible labels in the deterministic artifact.

## Interpretation

The artifact is a reproducible competition-style slice, not a clinical
validation set. Its 1,000-patient file is a frozen v1 pilot snapshot and should
not be used as an independent test set because patients were generated from the
same trial records used for matching. Future generation uses
`health-agent-synthetic-v2` to avoid oncology staging and oncology-note wording
for non-oncology conditions.

The main research bottlenecks are full free-text criterion coverage, retrieval
quality for sparse conditions, valid question/answer simulation, and
appropriateness ranking. The public GPT silver labels are a development set,
not a private holdout. See [research-roadmap.md](research-roadmap.md) before
starting another large Solar run.
