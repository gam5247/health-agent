# Architecture

Health Agent has three execution paths with different purposes.

1. `scripts/run_demo.py`: deterministic structural baseline.
2. `scripts/run_llm_eval.py`: legacy Friendli/K-EXAONE smoke path.
3. `scripts/run_solar_e2e_orchestration.py`: competition-format Solar Pro 3 path.

## Solar Pro 3 Multi-Agent Path

```text
blinded patient note + candidate trials
  -> criteria_parser_agent
  -> patient_information_understanding_agent
  -> inference_matching_agent_initial
  -> question_generation_agent + synthetic answer simulation
  -> recommendation_agent (second matching pass)
  -> result_explanation_agent
  -> deterministic normalization and contract validation
```

The default `multi-agent` mode makes six model calls per patient. The runner
records each call, parse status, latency, normalization fallback counts, and API
token usage when the provider includes a `usage` object.

## Output Contract

Patient-level eligibility labels:

- `eligible`
- `ineligible`
- `uncertain`

Criterion-level labels:

- `satisfied`
- `violated`
- `unknown`
- `not_applicable`

The final output separates:

- `initial_assessment`: original note only
- `follow_up_questions`: questions linked to exact trial and criterion IDs
- `simulated_patient_answers`: synthetic workflow answers, never original facts
- `final_assessment_after_answers`: second judgment after answers
- `recommended_trials`: eligible trials only
- `uncertain_but_actionable_trials`: unresolved trials only
- `excluded_trials`: ineligible trials only
- patient summary and medical disclaimer

Python normalization enforces candidate/criterion coverage, corrects trial-level
labels that conflict with criterion statuses, drops unknown identifiers, and
fills missing rows with explicit fallback judgments. Every fallback is counted
in the audit output; contract-valid output alone is not evidence of model
quality.

## Isolation Boundary

The public repository contains the development silver labels, so they are not a
private holdout. `scripts/build_agent_eval_workspace.py` creates a prediction
workspace that excludes labels and evaluator code, and
`scripts/assert_agent_workspace_clean.py` scans it for answer-key fields and
credential patterns. This demonstrates process isolation for the public
development benchmark. Final research claims require a separately stored
private holdout.

## Known Research Boundary

The current candidate schema covers only a limited structured subset of raw
protocol criteria. Full atomic criterion parsing, a hidden-state patient
simulator, hybrid retrieval, and appropriateness ranking are research work, not
completed MVP features. See [research-roadmap.md](research-roadmap.md).
