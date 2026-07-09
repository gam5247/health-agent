# Competition Research Roadmap

Last reviewed: 2026-07-10

## Decision Summary

The repository is a working competition MVP, but the current 100-patient score
must not be treated as the final research result.

The largest technical gap is criterion coverage. The 116 collected trials
contain 2,181 inclusion/exclusion bullet lines, while the current deterministic
schema exposes about 317 structured matcher units. That is roughly 14.5% of the
raw protocol bullets. The current benchmark can therefore reward agreement on a
small, simplified subset while missing much of the real protocol.

The second gap is benchmark independence. The 100 GPT teacher labels are public
silver labels in this repository. They are useful for development and contract
regression, but they are not a private holdout and are not clinical ground
truth.

The third gap is interaction validity. The current question agent also creates
the simulated patient answer. A stronger experiment must generate a hidden full
patient state first and let the patient simulator reveal only facts already in
that state. Otherwise the model can accidentally create answers that make its
own recommendation easier.

## Official Target

The organizer describes six required stages: protocol input, patient input,
information extraction and matching, missing-information detection, question
and reassessment, and trial recommendation. The required submission includes a
presentation, reproducible code and dependency specification, data provenance
and licensing, and a medical disclaimer.

Official evaluation weights are matching accuracy 30%, lab qualitative review
30%, and presentation 40%. Final model submission is due 2026-08-30 and the
presentation is scheduled for 2026-08-31.

Sources:

- [AIHC Lab challenge notice](https://github.com/skku-aihclab/aihc-lab/blob/main/data/notices/healthcare-agentic-ai-challenge-2026.json)
- [SKKU department announcement](https://professor.skku.edu/iesys/notice.do?article.offset=0&articleLimit=10&articleNo=221730&mode=view)

## Current Audit Snapshot

| Area | Current state | Interpretation |
|---|---:|---|
| Unit tests | 48 passing after this review | Software contract is stable |
| Collected trials | 116 | Pilot scale only |
| Raw eligibility bullets | 2,181 | Actual parsing workload |
| Structured matcher units | about 317 | About 14.5% of raw bullets |
| Public silver benchmark | 100 patients, 500 pairs | Development set, not private test set |
| Solar final eligibility agreement | 84.0% | Agreement with silver labels only |
| Eligibility macro F1 | 58.71% | `uncertain` is poorly recognized |
| Solar criterion-status agreement | 73.21% | Weakest on prior treatment and exclusions |
| Criterion-status macro F1 | 49.29% | Rare labels are hidden by aggregate accuracy |
| Exact recommendation-set agreement | 55.0% | Ranking/recommendation remains weak |
| Follow-up question link recall | 34.07% | Many needed criteria are not queried |
| Changed criterion transition accuracy | 17.06% | Question/answer loop rarely matches expected state change |
| Median six-call patient latency | about 83.3 seconds | Too slow for an interactive demo at scale |
| Reconstructed 100-run token estimate | about 6.85M | Criteria parsing is repeatedly paid per patient |

Current criterion accuracy by family:

| Criterion family | Accuracy against public silver labels |
|---|---:|
| sex | 100.0% |
| age | 91.4% |
| ECOG | 90.5% |
| condition | 80.2% |
| stage | 71.3% |
| exclusion flag | 62.7% |
| prior treatment | 51.7% |

The final eligibility label F1 scores are 70.2% for `eligible`, 90.5% for
`ineligible`, and only 15.4% for `uncertain`. Criterion F1 is 80.4% for
`violated`, 80.4% for `satisfied`, 36.4% for `unknown`, and 0% for
`not_applicable`. Aggregate accuracy therefore overstates the quality of the
interactive and abstention behavior that the competition specifically asks to
demonstrate.

The tracked 1,000-patient synthetic snapshot also contains realism artifacts:
486 non-oncology records have a stage value and 687 non-oncology records use an
oncology-referral or tumor-board prefix. The `health-agent-synthetic-v2`
generator now prevents these patterns for future datasets; the existing v1
snapshot remains frozen so the public silver benchmark is not silently changed.

## Research Program

### R0. Freeze Honest Evaluation

Goal: prevent tuning against the answer key and separate software regression
from research evaluation.

Method:

1. Keep the current public 100-patient set as `dev-silver-v1`.
2. Build a private synthetic holdout from hidden full patient states. Do not
   commit its labels or full hidden states to the public repository.
3. Split by trial ID and condition family, not by random patient row, so near
   duplicate trial templates cannot cross splits.
4. Add TREC Clinical Trials 2021 and 2022 as an external retrieval benchmark.
   TREC 2022 qrels distinguish non-relevant, excluded, and eligible trials.
5. Review at least 150 private patient-trial pairs twice and adjudicate
   disagreements. Until clinicians review them, call them reviewed silver, not
   gold.

Primary references:

- [NIST TREC 2022 Clinical Trials data and qrels](https://trec.nist.gov/data/trials2022.html)
- [NIH TrialGPT code and public cohorts](https://github.com/ncbi-nlp/TrialGPT)

Acceptance criteria:

- Prediction process cannot read evaluator labels.
- No patient template or trial ID overlap between development and holdout.
- Report inter-annotator agreement and adjudication counts.
- Run the private holdout once per frozen experiment family, not after every
  prompt edit.

### R1. Parse Every Protocol Criterion

Goal: replace the current shallow regex representation with atomic, traceable
criteria.

Atomic schema:

```text
criterion_id
inclusion_or_exclusion
source_text and source offsets
clinical concept
operator
value and unit
temporal window
negation
logical group (AND/OR)
required patient fields
parse confidence
```

Experiment:

1. Select 30 trials stratified by condition and criterion complexity.
2. Manually annotate every bullet and nested condition in those trials.
3. Compare current regex extraction, Solar parsing, and Solar plus deterministic
   numeric/temporal validation.
4. Measure source-span coverage, atomicity errors, operator/value accuracy,
   temporal-window accuracy, and logical-group accuracy.

Initial target: at least 95% source-bullet coverage and 90% exact accuracy for
operator, value, unit, and temporal window on the reviewed set.

Criteria-to-SQL research is useful here because it explicitly covers Boolean,
counting, and order-sensitive criteria:
[Criteria2SQL paper](https://aclanthology.org/2020.lrec-1.714/).

### R2. Build Retrieval as a Separate Measured System

Goal: retrieve relevant trials before spending LLM calls on eligibility.

Variants:

1. BM25 over trial title, condition, summary, and atomic criteria.
2. Dense biomedical embeddings over the same two index levels.
3. Reciprocal-rank fusion of BM25 and dense retrieval.
4. Metadata filters for recruitment status, age, sex, location, study type, and
   treatment purpose before semantic ranking.
5. Criterion-level reranking after trial-level retrieval.

Metrics:

- eligible-trial recall at candidate counts 10, 20, and 50
- NDCG at 10
- excluded-trial and irrelevant-trial contamination
- latency and index size
- performance by condition and rare terminology

TrialGPT uses lexical plus semantic retrieval before criterion matching, while
TrialMatchAI indexes both trial-level metadata and individual criteria and
applies demographic/status filters before reranking:
[NIH TrialGPT overview](https://www.ncbi.nlm.nih.gov/research/trialgpt/faq/),
[TrialMatchAI](https://www.nature.com/articles/s41467-026-70509-w).

### R3. Make the Question Loop Causally Valid

Goal: show that questions resolve missing information without inventing it.

Data design:

```text
hidden full synthetic patient state
        -> redaction policy
visible initial note
        -> agent questions
patient simulator reads hidden state only
        -> factual answers or "unknown"
final reassessment
```

The question generator must not see hidden fields or generate the answer. The
simulator must not see the trial recommendation, only the question and hidden
patient state.

Question policy:

- ask only about criteria that can change a decision or recommendation order
- merge duplicate questions shared by several trials
- prioritize hard exclusions and required inclusion facts
- cap the default interaction at five questions
- allow abstention when the hidden state does not contain the answer

Metrics:

- unknown detection precision/recall/F1
- question-to-criterion link precision/recall/F1
- factual answer consistency with hidden state
- criterion transition accuracy before and after answers
- eligibility gain after valid answers
- unnecessary-question rate

Recent RAG research reports that criterion complexity, abstention, and patient
record chunking materially affect matching performance:
[ML4H 2026 RAG study](https://proceedings.mlr.press/v297/leon-tramontini26a.html).

### R4. Hybrid Matching and Safety Validation

Goal: reserve LLM reasoning for semantic ambiguity and make explicit facts
deterministic.

Pipeline:

1. LLM maps criterion and patient evidence to typed fields and source spans.
2. Python evaluates numeric thresholds, age, sex, laboratory units, dates,
   durations, and Boolean exclusions.
3. LLM handles semantic equivalence and clinically ambiguous wording.
4. A conflict detector escalates disagreement, missing evidence, and high-risk
   criteria.
5. Final aggregation is deterministic and records every override.

Run ablations for Solar only, Solar plus validators, and validators plus
adjudication. Report exclusion-violation recall separately because a false
eligible decision is more consequential than an unnecessary uncertain result.

### R5. Rank Appropriateness, Not Just Eligibility

Goal: distinguish "can participate" from "most appropriate trial".

After eligibility gating, score:

- disease and intervention relevance
- therapeutic versus diagnostic/behavioral intent
- recruitment status
- geographic feasibility
- phase and study burden
- unresolved critical criteria
- patient preferences when provided

The current repeated false positives for `NCT07091617` show why this matters: a
broad cancer-genetic-testing delivery study can appear eligible for many cancer
notes but is not automatically the most appropriate treatment recommendation.

Metrics should include recommendation precision/recall/F1, exact-set agreement,
NDCG, and a blinded human preference comparison of explanations and ordering.

### R6. Reduce Cost Without Hiding Accuracy Loss

The 100-patient run repeated criteria parsing for every patient. Cache parsed
criteria by `(trial_id, source_text_hash, parser_version)` and invalidate the
cache when protocol text or parser version changes. Then batch only matching
work, preserve per-agent latency and API-reported token usage, and retry failed
batches independently.

Compare:

- six calls per patient
- cached criteria plus five calls per patient
- cached criteria plus batched matcher/recommender

Report accuracy, criterion coverage, JSON repair rate, latency, and actual API
token usage together. Cost reduction is not a win if criterion recall falls.

## Experiment Order

| ID | Change | Evaluation set | Main decision |
|---|---|---|---|
| E00 | Freeze current Solar result | public dev silver | Reference only |
| E01 | New evaluator metrics | same predictions | Locate failure families |
| E10 | Atomic criteria parser | 30 reviewed trials | Parsing coverage and faithfulness |
| E11 | Criteria cache | same E10 parser | Cost/latency without output drift |
| E20 | BM25 baseline | TREC 2021/2022 | External retrieval baseline |
| E21 | Hybrid retrieval | TREC plus private holdout | Recall gain over BM25 |
| E30 | Hidden-state patient simulator | private synthetic cases | Valid question-loop gain |
| E40 | Python validators | reviewed pair set | Exclusion and numeric accuracy |
| E50 | Appropriateness ranker | blinded pairwise review | Better recommendation order |
| E60 | Full system ablation | private holdout | Contribution of each component |

Each experiment must save configuration, code commit, input hashes, output
hashes, model name, prompt version, actual token usage when supplied by the API,
latency, and contract/fallback counts.

## Calendar to Submission

| Date | Deliverable |
|---|---|
| Jul 10-14 | Freeze dev benchmark, build private holdout protocol, import TREC topics/qrels |
| Jul 15-23 | Atomic criteria annotation and parser experiments |
| Jul 24-Aug 2 | Retrieval baselines and hybrid retrieval |
| Aug 3-12 | Hidden-state question loop and deterministic validators |
| Aug 13-20 | Ranking, adjudication, and ablations |
| Aug 21-26 | Frozen full run, error analysis, qualitative review |
| Aug 27-30 | Reproducible package and final presentation |
| Aug 31 | Presentation and live demo |

## Next Concrete Work Package

The next implementation should be E10, not another 100-patient Solar rerun:

1. Create an atomic criterion schema with source offsets and logical groups.
2. Annotate all criteria for 30 stratified trials.
3. Add a parser coverage report that compares raw bullets with emitted atomic
   criteria.
4. Cache parser output by trial text hash.
5. Rerun only 20 public development patients to verify the interface.
6. Evaluate once on the private holdout after the parser and prompts are frozen.

This work directly targets the largest measured gap and also improves the 30%
qualitative score because the agent trace becomes more complete, auditable, and
easy to demonstrate.
