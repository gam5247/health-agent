# Health Agent

Health Agent is a competition-ready scaffold for a multi-agent clinical trial
matching system. It parses trial protocols, profiles patient records, asks for
missing eligibility information, and returns patient-level trial
recommendations with evidence.

This repository is intentionally small and auditable. The current implementation
uses deterministic rules so it can be tested locally before replacing any agent
with an LLM, retrieval system, or external clinical-trial API.

## What It Does

- Normalizes clinical trial protocol fields into structured eligibility rules.
- Normalizes synthetic patient records into a consistent profile.
- Scores each patient against each trial using condition, age, sex, stage, ECOG,
  biomarkers, prior treatments, and exclusion flags.
- Generates follow-up questions when a patient record is missing information
  needed for eligibility.
- Produces recommendations with evidence items instead of opaque chat output.

This is not a medical device and does not provide medical advice. See
`MEDICAL_DISCLAIMER.md`.

## Repository Layout

```text
README.md
AGENTS.md
CODEX.md
CODEX_BOOTSTRAP_PROMPT.md
DATA_SOURCES.md
LICENSE_NOTES.md
MEDICAL_DISCLAIMER.md
pyproject.toml
configs/
data/raw/
docs/
scripts/
src/
tests/
```

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python scripts/run_demo.py
python -m unittest discover -s tests
```

The demo reads:

- `data/raw/synthetic-patients.json`
- `data/raw/sample-trials.json`

and prints the top recommendation per synthetic patient.

## Agent Roles

- `TrialProtocolAgent`: converts protocol JSON into normalized trial objects.
- `PatientProfileAgent`: converts patient JSON into normalized patient objects.
- `MissingInformationAgent`: turns missing eligibility evidence into questions.
- `TrialMatchingAgent`: scores one patient against one trial and records
  evidence.
- `RecommendationAgent`: ranks trials per patient and returns final
  recommendations.

## Expected Competition Extension Points

Replace or extend the deterministic pieces in this order:

1. Add ingestion for official trial protocol files or ClinicalTrials.gov API
   responses.
2. Add schema validation and source citation storage for every extracted rule.
3. Add retrieval over protocol text for inclusion and exclusion criteria.
4. Add an LLM agent only after the structured scoring contract is stable.
5. Add manual clinician review fields before any real-world use.

## Local Validation

```bash
python -m unittest discover -s tests
python scripts/run_demo.py --limit 3
```

The tests verify that the synthetic patient set loads, recommendations are
generated, known biomarker matches are ranked correctly, and missing data
produces follow-up questions.
