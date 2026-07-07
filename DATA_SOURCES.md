# Data Sources

## Bundled Data

- `data/raw/synthetic-patients.json`: official challenge example input with ten
  synthetic patient topics (`S001`-`S010`). This is a core reference input and
  should be preserved exactly.
- `data/raw/oncology-synthetic-patients.json`: ten local oncology-focused
  synthetic patient records created for development and deterministic tests.
  They are not real patients and should not be treated as clinical records.
- `data/raw/sample-trials.json`: sample protocol-like records created for local
  development and testing. The `NCT-SAMPLE-*` identifiers are placeholders.

## Planned External Sources

For production or competition submission work, use documented public sources
where allowed by the competition rules:

- ClinicalTrials.gov API v2 for trial metadata and eligibility text.
- Friendli dedicated endpoint for K-EXAONE model calls, configured only through
  local environment variables.
- Trial sponsor protocol PDFs only when redistribution and processing are
  permitted.
- Public disease ontology or terminology sources when licensing permits.

## Source Handling Requirements

- Record source URL, retrieval date, license or terms, and transformation steps.
- Keep original raw data separate from normalized derived files.
- Store citation spans for protocol-derived eligibility criteria when possible.
- Do not ingest real patient records into this repository without a documented
  privacy, consent, retention, and access-control plan.

## Current Processed Dataset

- `data/processed/trials.jsonl`: 116 trial records collected from
  ClinicalTrials.gov API v2 through `scripts/collect_trials.py`. The current
  condition queries are aligned to the official example topics: acute
  pancreatitis, Graves disease, nephrotic syndrome, bladder cancer, migraine
  with aura, mucormycosis, hypertrophic pyloric stenosis, idiopathic pulmonary
  fibrosis, infectious mononucleosis, and retinal detachment.
- `data/processed/synthetic_patients.jsonl`: 1,000 synthetic patient notes
  generated from normalized trial criteria. These are synthetic software test
  records, not real patients.
- `artifacts/health-agent-submission/`: scaled competition artifact generated
  from the processed trial, synthetic patient files, and official example
  topics. The bundle includes `competition_predictions.json` with official
  example outputs in the required eligibility and criterion-level label sets.

Raw ClinicalTrials.gov API pages are written to `data/raw/clinicaltrials/` for
local inspection and are intentionally ignored by git.
