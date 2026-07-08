# E2E Orchestration Hidden Evaluation

This workflow evaluates the multi-agent clinical-trial matching output against
the GPT E2E teacher v2 answer key without passing hidden labels to the agent
runner.

## Files

- Hidden labels, evaluator-only:
  `artifacts/gpt-e2e-teacher-labeling/gpt_e2e_teacher_labels_100.v2.jsonl`
- Agent-visible input:
  `artifacts/e2e-orchestration-eval/blinded_input_100.jsonl`
- Deterministic prediction output:
  `outputs/e2e_orchestration_predictions_v2.jsonl`
- Hidden evaluation report:
  `outputs/e2e_orchestration_hidden_eval_report.json`

## Commands

Prepare the blinded input from the answer key:

```powershell
python scripts\prepare_hidden_e2e_eval.py
```

Run the competition-format orchestration. This command intentionally has no
`--answer-key` option.

```powershell
python scripts\run_e2e_orchestration_v2.py
```

For stricter agent isolation, build a prediction-side workspace that excludes
hidden labels and evaluator-only files:

```powershell
python scripts\build_agent_eval_workspace.py --force
python scripts\assert_agent_workspace_clean.py artifacts\e2e-orchestration-agent-workspace
cd artifacts\e2e-orchestration-agent-workspace
python scripts\run_e2e_orchestration_v2.py
```

Score predictions against the hidden labels:

```powershell
python scripts\evaluate_hidden_e2e_predictions.py --fail-on-contract-errors
```

## Contract

The agent-visible input contains only:

- `patient_id`
- `patient_information_string`
- `candidate_trials`

`prepare_hidden_e2e_eval.py` also runs a recursive allowlist audit over the
blinded JSONL. The audit permits public trial eligibility-criteria text but
rejects answer-key structures such as `final_output`, `agent_trace`, teacher
labels, and gold-label fields.

The prediction must contain:

- criteria parser output
- patient information understanding output
- initial matching output
- follow-up questions
- simulated patient answers, if externally supplied
- final matching output
- recommended, uncertain, and excluded trial lists
- result explanation
- medical disclaimer

The hidden evaluator checks:

- all candidate trials are evaluated initially and finally
- eligibility labels use `eligible`, `ineligible`, or `uncertain`
- criterion statuses use `satisfied`, `violated`, `unknown`, or
  `not_applicable`
- criterion IDs match the candidate-trial criteria
- recommendations contain only eligible final trials
- excluded trials contain only ineligible final trials
- question `needed_for` links point to valid trials and criteria
- simulated answers do not reference missing question IDs

## Current Baseline

The deterministic local runner is a structural baseline, not the target model.
It verifies the full workflow shape and hidden-eval harness before running a
K-EXAONE/Friendli or other LLM-backed orchestration.

## K-EXAONE Pure Run

The pure K-EXAONE runner uses the same blinded input and does not accept an
answer-key argument. It makes one Friendli/K-EXAONE chat-completions call per
patient and normalizes the model's JSON into the competition v2 contract.

Smoke command:

```powershell
python scripts\run_exaone_e2e_orchestration.py `
  --env-file "C:\Users\kll45\OneDrive\문서\New project\.env" `
  --max-patients 3 `
  --concurrency 1 `
  --confirm-live-exaone-api `
  --output-jsonl outputs\exaone_e2e_predictions_smoke.jsonl `
  --output-json outputs\exaone_e2e_predictions_smoke.json `
  --summary outputs\exaone_e2e_predictions_smoke_summary.json `
  --raw-output-jsonl outputs\exaone_e2e_raw_responses_smoke.jsonl `
  --audit-output-jsonl outputs\exaone_e2e_normalization_audit_smoke.jsonl `
  --manifest outputs\exaone_e2e_run_manifest_smoke.json
```

Full 100-patient command:

```powershell
python scripts\run_exaone_e2e_orchestration.py `
  --env-file "C:\Users\kll45\OneDrive\문서\New project\.env" `
  --concurrency 4 `
  --resume `
  --confirm-live-exaone-api
```

The explicit `--confirm-live-exaone-api` flag is required so the command cannot
accidentally call the live API during local preflight. The runner also writes
raw model responses, normalization/fallback audit rows, and a run manifest under
`outputs/`.

Then score the EXAONE predictions:

```powershell
python scripts\evaluate_hidden_e2e_predictions.py `
  --predictions outputs\exaone_e2e_predictions.jsonl `
  --output outputs\exaone_e2e_hidden_eval_report.json `
  --fail-on-contract-errors
```

For strict isolation, run `scripts\run_exaone_e2e_orchestration.py` from an
answer-key-free agent workspace and copy only the prediction JSONL back to the
evaluator environment.

Latest local dry run:

- patients compared: 100
- final trial judgments: 500
- prediction contract errors: 0
- eligibility accuracy against silver labels: 0.788
- criterion-status accuracy against silver labels: 0.6503
- recommendation-set exact match: 0.52
- question-link precision: 0.6105
- question-link recall: 0.6334

These scores are expected to improve only after replacing or augmenting the
deterministic baseline with stronger LLM agent calls. The labels remain
synthetic silver labels for software evaluation only, not clinical truth.

## Isolation Boundary

The repo contains evaluator-only artifacts for development. A fully isolated
agent run should use the generated agent workspace instead of a full repo
checkout. The runner can only consume blinded input, but an unconstrained
process with access to the full repository could still inspect hidden labels.
Keep the scoring step in the main repo or another evaluator-only environment.
