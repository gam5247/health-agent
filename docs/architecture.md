# Architecture

Health Agent uses a small set of role-specific agents coordinated by a
recommendation pipeline.

```text
trial JSON -> TrialProtocolAgent ----+
                                     +-> TrialMatchingAgent -> RecommendationAgent
patient JSON -> PatientProfileAgent -+           |
                                                 v
                                  MissingInformationAgent
```

## Data Contract

The scorer returns evidence for each decision-relevant criterion:

- `matched`: the patient record supports the criterion.
- `missing`: the patient record does not contain enough information.
- `conflict`: the patient record conflicts with the criterion.

The final recommendation decision is one of:

- `recommend`
- `needs_more_info`
- `not_recommended`

## Why This Shape

The project is intentionally not a single chat prompt. Trial matching needs a
traceable contract because an answer can be wrong for several different reasons:
missing lab data, an exclusion flag, an age bound, disease mismatch, or a
biomarker conflict. The evidence list keeps these cases inspectable.

