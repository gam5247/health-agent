# GPT E2E Teacher Labels

This folder contains GPT-generated end-to-end teacher labels for the clinical
trial matching workflow.

## Unit

- 100 synthetic patients
- 5 candidate trials per patient
- 500 patient-trial final judgments

## Main Files

- `gpt_e2e_teacher_input_100.json`: source input given to GPT.
- `gpt_e2e_teacher_labels_100.jsonl`: final answer key, one patient per line.
- `gpt_e2e_teacher_labels_100.json`: same answer key as a JSON document.
- `gpt_e2e_teacher_labels_100_summary.json`: validation and label-count summary.
- `MANIFEST.json`: provenance, scale, validation commands, and hashes.
- `inputs/`: 20 input batches, 5 patients each.
- `requests/`: prompt/request files for the 20 batches.
- `responses/`: normalized, validated GPT responses for each batch. Raw ChatGPT
  response captures are intentionally ignored by git.

The canonical schema is `schemas/gpt_e2e_teacher_label.schema.json`.

## Each Patient Record Contains

- patient information string
- criteria parser agent output
- patient information understanding agent output
- inference and matching agent output
- follow-up question generation
- simulated patient answers
- recommendation agent output
- final trial judgments, criterion-level rationales, explanations, and medical
  disclaimer

## Validation Summary

Current generated answer key:

- patient count: 100
- final trial judgments: 500
- criterion-level judgments: 2,934
- follow-up questions: 255
- simulated patient answers: 255
- validation errors: 0
- semantic consistency warnings: 28

Semantic consistency warnings mean the final trial label is not fully implied
by the normalized `criteria_to_assess` subset alone. Some GPT judgments use
the supplied raw criteria excerpt in addition to the structured criterion IDs.
