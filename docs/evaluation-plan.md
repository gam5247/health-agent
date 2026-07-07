# Evaluation Plan

## Local Checks

- Unit tests verify parser, scoring, ranking, and question generation behavior.
- Demo output is manually inspected for each synthetic patient.
- Hard conflicts must override otherwise high-looking aggregate scores.
- Submission artifacts are checked for the required eligibility labels
  (`eligible`, `ineligible`, `uncertain`) and criterion labels
  (`satisfied`, `violated`, `unknown`, `not_applicable`).

## Suggested Competition Metrics

- Patient-level top-k trial recall against a labeled reference set.
- Eligibility contradiction rate.
- Missing-question usefulness rate.
- Evidence citation completeness.
- Latency per patient-trial pair.
- Parse/repair rate for LLM structured outputs.

## Review Checklist

- Every recommendation includes explicit evidence.
- Missing information is not treated as confirmed ineligibility.
- Exclusion criteria are visible in the output.
- Data provenance is documented.
- No real patient data is committed.
