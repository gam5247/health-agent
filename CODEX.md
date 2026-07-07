# Codex Project Notes

This scaffold is designed for iterative Codex work.

## Current State

- Python package: `src/health_agent`
- Demo command: `python scripts/run_demo.py`
- Tests: `python -m unittest discover -s tests`
- Data: synthetic patients and sample trial protocols under `data/raw`
- LLM eval: `python scripts/run_llm_eval.py --dry-run --max-patients 2 --top-k 2`
- Scaled artifact: `python scripts/run_competition_pipeline.py --trial-limit 120 --patient-count 1000 --top-k 30`

## Implementation Rules

- Keep the scoring engine explainable and testable.
- Add new eligibility dimensions as evidence items first, then update ranking.
- Do not hide hard conflicts behind high aggregate scores.
- Keep missing information separate from confirmed ineligibility.
- Do not use real patient data unless the repository has an explicit privacy and
  compliance plan.
- Never print or commit Friendli/K-EXAONE API keys. Use OS env or a local
  `.env` passed with `--env-file`.

## Useful Next Tasks

- Add ClinicalTrials.gov v2 API ingestion.
- Add extracted protocol citation spans to each evidence item.
- Batch matcher and orchestrator prompts to reduce K-EXAONE latency.
- Improve retrieval with condition/biomarker metadata filters before lexical
  ranking.
- Add a human review status field for each recommendation.
