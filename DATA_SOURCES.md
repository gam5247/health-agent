# Data Sources

## Bundled Data

- `data/raw/synthetic-patients.json`: ten synthetic patient records created for
  local development and testing. They are not real patients and should not be
  treated as clinical records.
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
