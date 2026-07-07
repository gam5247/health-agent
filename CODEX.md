# Codex Project Notes

This scaffold is designed for iterative Codex work.

## Current State

- Python package: `src/health_agent`
- Demo command: `python scripts/run_demo.py`
- Tests: `python -m unittest discover -s tests`
- Data: synthetic patients and sample trial protocols under `data/raw`

## Implementation Rules

- Keep the scoring engine explainable and testable.
- Add new eligibility dimensions as evidence items first, then update ranking.
- Do not hide hard conflicts behind high aggregate scores.
- Keep missing information separate from confirmed ineligibility.
- Do not use real patient data unless the repository has an explicit privacy and
  compliance plan.

## Useful Next Tasks

- Add ClinicalTrials.gov v2 API ingestion.
- Add extracted protocol citation spans to each evidence item.
- Add a report writer that emits one patient recommendation packet at a time.
- Add a human review status field for each recommendation.
