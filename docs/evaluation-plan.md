# Evaluation Plan

## Local Checks

- Unit tests verify parser, scoring, ranking, and question generation behavior.
- Demo output is manually inspected for each synthetic patient.
- Hard conflicts must override otherwise high-looking aggregate scores.
- Submission artifacts are checked for the required eligibility labels
  (`eligible`, `ineligible`, `uncertain`) and criterion labels
  (`satisfied`, `violated`, `unknown`, `not_applicable`).

## Suggested Competition Metrics

- Patient-level eligible-trial recall at fixed candidate counts.
- Eligibility contradiction rate.
- Missing-question usefulness rate.
- Evidence citation completeness.
- Latency per patient-trial pair.
- Parse/repair rate for LLM structured outputs.
- Per-label precision, recall, and F1 for eligibility and criterion statuses.
- Criterion accuracy by family: condition, age, sex, stage, ECOG, biomarker,
  prior treatment, and exclusion.
- Initial-to-final transition accuracy after follow-up answers.
- Recommendation precision, recall, F1, exact-set agreement, and NDCG.
- API-reported token usage per agent when available.

## Review Checklist

- Every recommendation includes explicit evidence.
- Missing information is not treated as confirmed ineligibility.
- Exclusion criteria are visible in the output.
- Data provenance is documented.
- No real patient data is committed.
- Public development silver labels are not reported as a private holdout.
- Synthetic follow-up answers come from a pre-generated hidden patient state,
  not from the question/recommendation agent itself.
