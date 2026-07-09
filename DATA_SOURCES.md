# Data Sources

## Bundled Data

- `data/raw/synthetic-patients.json`: official challenge example input with ten
  synthetic patient topics (`S001`-`S010`). This is a core reference input and
  should be preserved exactly.
  - Official source: [AIHC Lab challenge attachment](https://github.com/skku-aihclab/aihc-lab/blob/main/files/notice/healthcare-agentic-ai-challenge-2026/synthetic-patients.json)
  - Verified: 2026-07-10; local and official JSON are semantically identical.
  - Local SHA-256: `1D2B8197F26F7A65646B899C8FAA75C1E2443718EA1F5BBFDC69B5A33319B415`
  - Use restriction: competition-provided synthetic example; retain attribution
    to AIHC Lab and do not represent it as real patient data.
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
  - API endpoint: `https://clinicaltrials.gov/api/v2/studies`
  - Collection date: 2026-07-07
  - Terms: [ClinicalTrials.gov Terms and Conditions](https://clinicaltrials.gov/about-site/terms-conditions)
  - Transformations: recruiting-status filtering, field normalization,
    inclusion/exclusion line splitting, and limited regex extraction for age,
    sex, stage, ECOG, selected biomarkers, prior treatments, and exclusions.
  - ClinicalTrials.gov requires source attribution, current processing dates,
    and disclosure of modifications when data are published or redistributed.
- `data/processed/synthetic_patients.jsonl`: 1,000 synthetic patient notes
  generated from normalized trial criteria. These are synthetic software test
  records, not real patients. The tracked file is a frozen v1 pilot snapshot;
  future generation uses `health-agent-synthetic-v2`, which avoids oncology
  staging and oncology-note templates for non-oncology conditions and emits
  only perturbation scenarios backed by criteria present in the target trial.
- `artifacts/health-agent-submission/`: scaled competition artifact generated
  from the processed trial, synthetic patient files, and official example
  topics. The bundle includes `competition_predictions.json` with official
  example outputs in the required eligibility and criterion-level label sets.

Raw ClinicalTrials.gov API pages are written to `data/raw/clinicaltrials/` for
local inspection and are intentionally ignored by git.

## Research Benchmarks Under Consideration

- [NIST TREC 2022 Clinical Trials Track](https://trec.nist.gov/data/trials2022.html):
  public synthetic topics and relevance judgments with non-relevant, excluded,
  and eligible labels. Import only after recording the source version and terms.
- [NIH TrialGPT repository](https://github.com/ncbi-nlp/TrialGPT): reference
  implementation and public SIGIR/TREC cohort preparation. Do not copy code or
  data without preserving its license and dataset-specific citations.
