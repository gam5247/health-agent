# Health Agent Submission Artifact

This folder is a scaled-down competition-style output bundle.

- Trials: 116
- Synthetic patients: 1000
- Candidate pairs: 30000

Files:

- `manifest.json`: run metadata and source paths
- `evaluation_summary.json`: retrieval and LLM summary metrics
- `labels.tsv`: competition eligibility labels for retrieved pairs
- `competition_predictions.json`: official example patient outputs with criterion-level evidence
- `synthetic_predictions_sample.json`: scaled synthetic sample outputs with the same schema
- `demo_cases.md`: patient-level demo cases
- `MEDICAL_DISCLAIMER.md`: required medical disclaimer

Validation:

```bash
python scripts/validate_submission_artifact.py
```

This artifact is for research prototyping only and is not medical advice.
