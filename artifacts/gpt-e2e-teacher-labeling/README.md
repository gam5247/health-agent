# GPT E2E Teacher Labels

This folder contains GPT-generated end-to-end teacher labels for the clinical
trial matching workflow.

## Unit

- 100 synthetic patients
- 5 candidate trials per patient
- 500 patient-trial final judgments

## Main Files

- `gpt_e2e_teacher_input_100.json`: source input given to GPT.
- `gpt_e2e_teacher_labels_100.v2.jsonl`: canonical final answer key, one
  patient per line.
- `gpt_e2e_teacher_labels_100.v2.json`: same v2 answer key as a JSON document.
- `gpt_e2e_teacher_labels_100.v2_summary.json`: v2 validation and label-count
  summary.
- `gpt_e2e_teacher_labels_100.jsonl`: legacy normalized GPT draft kept for
  provenance.
- `gpt_e2e_teacher_labels_100.json`: same legacy draft as a JSON document.
- `gpt_e2e_teacher_labels_100_summary.json`: legacy validation summary.
- `MANIFEST.json`: provenance, scale, validation commands, and hashes.
- `inputs/`: 20 input batches, 5 patients each.
- `requests/`: prompt/request files for the 20 batches.
- `responses/`: normalized, validated GPT responses for each batch. Raw ChatGPT
  response captures are intentionally ignored by git.

The canonical schema is `schemas/gpt_e2e_teacher_label_v2.schema.json`. The
legacy v1 schema is kept at `schemas/gpt_e2e_teacher_label.schema.json`.

## Each Patient Record Contains

- patient information string
- criteria parser agent output
- patient information understanding agent output
- inference and matching agent output
- follow-up question generation
- simulated patient answers
- recommendation agent output
- initial assessment before follow-up
- follow-up questions and simulated patient answers
- final assessment after simulated answers
- separate `recommended_trials`, `uncertain_but_actionable_trials`, and
  `excluded_trials`
- criterion-level rationales, patient-level explanation, and medical disclaimer

## Validation Summary

Canonical v2 answer key:

- patient count: 100
- candidate trials per patient: 5
- initial trial judgments: 500
- final trial judgments: 500
- criterion-level judgments: 2,934
- follow-up questions: 449
- simulated patient answers: 420
- final eligible recommendations: 100
- uncertain but actionable trials: 8
- excluded trials: 392
- validation errors: 0
- normalization warnings: 295

Normalization warnings identify where the v2 builder had to preserve a weaker
legacy draft shape, such as deriving a missing explanation from criterion-level
judgments or using the final draft as the initial-assessment fallback. They are
recorded in `quality_flags` and do not indicate structural validation failure.
