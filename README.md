# Health Agent

Healthcare Agentic AI Challenge 2026 대응용 멀티 에이전트 임상시험 추천 시스템입니다.

이 저장소의 목표는 단순한 질의응답 챗봇이 아니라, 임상시험 프로토콜과 환자 프로파일을 구조적으로 비교하고, 근거 기반으로 참여 가능성을 판정하며, 정보가 부족한 경우 확인 질문을 생성하고, 환자별 임상시험 추천 순위를 산출하는 재현 가능한 파이프라인을 만드는 것입니다.

## 대회 요약

대회 주제는 Interactive Clinical Trial Recommendation입니다.

입력은 다음 두 축입니다.

1. ClinicalTrials.gov 등 공개 임상시험 프로토콜
   - inclusion criteria
   - exclusion criteria
   - description / brief summary
   - condition, intervention, phase 등 metadata
2. 환자 프로파일
   - 나이, 성별, 병력, 증상, 검사 결과, 투약, 과거 치료력 등
   - 제공 예시는 `data/raw/synthetic-patients.json`의 10개 synthetic vignette

최종 출력은 다음을 포함해야 합니다.

1. 임상시험 참여 가능성 판정
   - `eligible`
   - `ineligible`
   - `uncertain`
2. criterion-level 판단 근거
   - `satisfied`
   - `violated`
   - `unknown`
   - `not_applicable`
3. 부족 정보에 대한 follow-up question
4. 환자별 임상시험 추천 순위와 설명
5. 의료적 면책 고지

평가 비중은 매칭 정확성 30%, 랩 내 정성 평가 30%, 발표 점수 40%로 본다. 따라서 단순 accuracy만이 아니라, 에이전트 구성, 오케스트레이션, 근거 제시, 오류 분석, 발표 가능성이 중요하다.

## 핵심 설계 원칙

이 프로젝트는 LLM 하나에 모든 판단을 맡기지 않는다.

기본 원칙은 다음과 같다.

```text
자연어 이해와 애매한 의미 판단  -> LLM agent
명시적 수치, 성별, 나이, 기간 조건 -> Python validator
후보 trial 검색                    -> retrieval / metadata filter
충돌 및 hard case                  -> 상위 model adjudicator
최종 출력                           -> schema-validated report
```

LLM은 classifier 자체라기보다, 임상시험 기준과 환자 정보를 구조화하고 애매한 의미 판단을 보조하는 semantic module로 사용한다.

## 전체 아키텍처

```text
ClinicalTrials.gov protocol text
        |
        v
trial_criteria_parser
        |
        v
structured trial criteria JSON
        |
        v
trial index / retrieval
        |
        v
candidate trial set per patient
        |
        v
patient_profiler --------------
        |                       |
        v                       |
structured patient profile      |
        |                       |
        v                       |
eligibility_matcher <-----------
        |
        v
python_rule_validator
        |
        v
conflict_adjudicator
        |
        v
missing_info_question_generator
        |
        v
trial_ranker
        |
        v
final_explainer
```

## 에이전트 역할

| Agent | 역할 | 1차 구현 | 이후 확장 |
|---|---|---|---|
| `trial_criteria_parser` | inclusion/exclusion을 atomic rule로 분해 | deterministic / fixture | K-EXAONE 또는 Solar |
| `patient_profiler` | vignette에서 핵심 환자 정보 추출 | JSON loader | K-EXAONE |
| `candidate_trial_retriever` | 환자별 후보 trial top-k 검색 | metadata filter | BM25 + vector retrieval |
| `eligibility_matcher` | criterion별 satisfied/violated/unknown 판정 | rule scorer | K-EXAONE |
| `python_rule_validator` | 나이, 성별, 수치, 기간 조건 검증 | Python | 강화 |
| `conflict_adjudicator` | 불일치, low-confidence, exclusion conflict 판정 | stub | GLM-class model |
| `missing_info_question_generator` | unknown criterion 질문 생성 | template | Solar Pro 3 |
| `trial_ranker` | 환자별 trial ranking | score formula | learning-to-rank / LLM explanation |
| `final_explainer` | 최종 보고서 생성 | template | Solar Pro 3 |

## 모델 운영 전략

현재 자원 가정:

- K-EXAONE: 무제한 사용 가능
- Solar Pro 3: 무제한 또는 사실상 무제한 사용 가능
- GLM급 모델: 상위 adjudicator로 유료 사용
- GPT / Claude: 필요 시 hard-case spot check만 사용

권장 라우팅:

```text
K-EXAONE
  - primary worker model
  - trial criteria parsing
  - patient profiling
  - first-pass eligibility matching
  - semantic clinical context 판단

Solar Pro 3
  - JSON repair
  - question generation
  - explanation draft
  - second opinion / baseline

GLM-class model
  - hard case adjudication
  - exclusion conflict
  - K-EXAONE vs Solar disagreement
  - low confidence cases

Python
  - deterministic validator
  - numeric threshold check
  - age / sex / time-window logic
  - final aggregation
```

GLM으로 올리는 조건:

```python
should_escalate = (
    confidence < 0.75
    or k_exaone_disagrees_with_solar
    or has_exclusion_conflict
    or evidence_span_missing
    or unknown_count_is_high
    or top1_top2_ranking_margin_is_small
    or high_risk_domain_involved
)
```

`high_risk_domain_involved` 예시:

- oncology
- biomarker
- line of therapy
- pregnancy
- renal function
- hepatic function
- immunosuppression
- recent infection
- numeric laboratory threshold

## 데이터 전략

### 사용 가능한 데이터

- 공개 ClinicalTrials.gov protocol text
- 제공 synthetic patient example 10건
- 추가 synthetic patient / trial-pair data 생성 가능

### 금지 또는 주의

- 개인식별정보 사용 금지
- 비공개 의료정보 사용 금지
- 모든 데이터 출처와 라이선스 명시 필요
- 모델 생성 label은 gold label이 아니라 silver label로 취급

### 목표 데이터 규모

초기 목표:

```text
trials: 50-150
synthetic patients: 100-500
retrieved patient-trial pairs: 1,000-5,000
criterion-level silver labels: 5,000+
human-reviewed gold pairs: 100-300
```

수상권 목표:

```text
trials: 150-300+
synthetic patients: 500-2,000+
retrieved patient-trial pairs: 5,000-20,000+
criterion-level silver labels: 50,000+
human-reviewed gold pairs: 300-700
```

중요한 것은 단순 개수가 아니라 coverage다.

Coverage 축:

- demographics: age, sex, pregnancy
- diagnosis: confirmed vs suspected disease
- severity: stage, ECOG, NYHA, fibrosis grade 등
- labs: numeric and qualitative findings
- medication: current and prior medication
- procedure: surgery, biopsy, transplant 등
- temporal criteria: within 14 days, prior 6 months 등
- exclusion: infection, pregnancy, organ dysfunction, prior malignancy 등
- missing information: unknown을 질문으로 바꾸는 케이스

## 내부 스키마 원칙

모든 중간 산출물은 Pydantic schema를 통과해야 한다.

예상 criterion result:

```json
{
  "criterion_id": "NCT00000000-I-001",
  "criterion_type": "inclusion",
  "status": "satisfied",
  "confidence": 0.91,
  "trial_evidence": "Age 18 years or older",
  "patient_evidence": "54-year-old man",
  "reason": "The patient is older than 18."
}
```

예상 trial-level result:

```json
{
  "patient_id": "S001",
  "trial_id": "NCT00000000",
  "overall_status": "uncertain",
  "recommendation_score": 0.72,
  "criteria_results": [],
  "missing_questions": [],
  "rationale": "..."
}
```

Aggregation policy:

```text
exclusion violated       -> ineligible
required inclusion missed -> ineligible or uncertain
required information missing -> uncertain
all required inclusion satisfied and no exclusion violated -> eligible
```

## 개발 로드맵

### Phase 0. 저장소 정리

- README, AGENTS, CODEX, TASKS를 사람이 읽을 수 있게 유지한다.
- 실행 진입점과 테스트 진입점을 명확히 둔다.
- 원본 데이터는 `data/raw/`에 보관한다.

### Phase 1. Deterministic baseline

목표: LLM 없이도 끝까지 도는 baseline.

작업:

1. `data/raw/synthetic-patients.json` loader 완성
2. `data/raw/sample-trials.json` loader 완성
3. trial / patient / criterion / result Pydantic schema 고정
4. deterministic eligibility scorer 구현
5. missing information question template 구현
6. `scripts/run_demo.py`로 end-to-end demo 출력
7. unittest 통과

성공 기준:

```bash
python scripts/run_demo.py --limit 3
python -m unittest discover -s tests
```

### Phase 2. Trial ingestion

목표: ClinicalTrials.gov protocol을 가져와 내부 trial schema로 변환.

작업:

1. ClinicalTrials.gov API 또는 다운로드 파일 ingestion
2. NCT ID, condition, intervention, phase, status metadata 저장
3. inclusion/exclusion raw text 저장
4. criterion ID 생성
5. 데이터 출처와 라이선스 기록

산출물:

```text
data/processed/trials.jsonl
data/processed/criteria.jsonl
DATA_SOURCES.md
```

### Phase 3. Retrieval

목표: 모든 patient-trial pair를 brute force하지 않고 후보 trial만 고른다.

작업:

1. condition / keyword 기반 metadata filter
2. BM25 baseline
3. optional embedding retrieval
4. 환자별 top-k trial candidate 생성
5. retrieval recall@k 평가

산출물:

```text
outputs/retrieval_candidates.jsonl
```

### Phase 4. LLM worker integration

목표: K-EXAONE / Solar를 provider-neutral interface 뒤에 붙인다.

작업:

1. `src/hc_agent/llm.py`에 provider abstraction 구현
2. `configs/models.yaml`로 model routing 관리
3. structured output validation
4. retry / repair loop 구현
5. token usage와 latency logging

초기 agent routing:

```text
criteria parser: K-EXAONE
patient profiler: K-EXAONE
question generator: Solar Pro 3
explanation generator: Solar Pro 3
format repair: Solar Pro 3
```

### Phase 5. Matching and adjudication

목표: core eligibility matching 성능 개선.

작업:

1. K-EXAONE first-pass matcher
2. Solar second opinion option
3. Python rule validator 적용
4. disagreement detector
5. GLM escalation
6. final aggregation policy 고정

Hard case 조건:

```text
low confidence
exclusion conflict
missing evidence
unknown count high
high-risk domain
ranking tie
```

### Phase 6. Evaluation

목표: 개선 여부를 숫자로 확인한다.

Metric:

- criterion status accuracy
- exclusion violation recall
- unknown detection F1
- evidence presence / grounding proxy
- question coverage
- trial ranking recall@k
- cost per patient
- latency per patient

Ablation:

- deterministic baseline
- K-EXAONE only
- Solar only
- K-EXAONE + Python validator
- K-EXAONE + Solar disagreement routing
- GLM adjudication on hard cases
- retrieval top-k variants

### Phase 7. Final demo and presentation

목표: 평가자에게 구조와 성능을 설득한다.

발표 구성:

1. Problem definition
2. Agent architecture
3. Data and schema design
4. Retrieval design
5. Eligibility matching logic
6. Missing information question loop
7. Model routing and cost control
8. Evaluation results
9. Error analysis
10. Demo cases
11. Limitations and medical disclaimer
12. Conclusion

## Repository layout

```text
README.md
AGENTS.md
CODEX.md
CODEX_BOOTSTRAP_PROMPT.md
TASKS.md
DATA_SOURCES.md
LICENSE_NOTES.md
MEDICAL_DISCLAIMER.md
pyproject.toml
configs/
  models.yaml
  pipeline.yaml
data/
  raw/
  processed/
docs/
  architecture.md
  evaluation.md
  model_strategy.md
  project_plan.md
scripts/
  run_demo.py
  inspect_sample_patients.py
src/
  hc_agent/
    schemas.py
    config.py
    llm.py
    graph.py
    nodes/
    retrieval/
    eval/
tests/
```

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
python scripts/run_demo.py --limit 3
python -m unittest discover -s tests
```

설치형 프로젝트로 정리한 뒤에는 다음을 사용한다.

```bash
pip install -e .
health-agent-demo --limit 3
health-agent-llm-eval --dry-run --max-patients 2 --top-k 2
```

추가 로컬 검증:

```bash
python -m unittest discover -s tests
python scripts/run_demo.py --limit 3
python scripts/run_llm_eval.py --dry-run --max-patients 2 --top-k 2
```

## K-EXAONE / Friendli Evaluation

LLM evaluation path는 선택 기능이며, API key는 저장소에 넣지 않는다. OS
environment 또는 로컬 `.env` 파일에서만 읽는다.

Required environment variables:

- `FRIENDLI_API_KEY`, or fallback `K_EXAONE_API_KEY`
- `K_EXAONE_ENDPOINT_ID`, or fallback `FRIENDLI_ENDPOINT_ID` / `K_EXAONE_MODEL`

Optional variables:

- `FRIENDLI_BASE_URL`, default `https://api.friendli.ai/dedicated/v1`
- `FRIENDLI_CHAT_COMPLETIONS_URL`, default
  `https://api.friendli.ai/dedicated/v1/chat/completions`

API 호출 없는 dry-run:

```bash
python scripts/run_llm_eval.py --dry-run --max-patients 3 --top-k 3
```

실제 Friendli/K-EXAONE smoke test:

```bash
python scripts/run_llm_eval.py \
  --env-file "<path-to-local-env-file>" \
  --max-patients 1 \
  --top-k 1 \
  --concurrency 1
```

Evaluator는 local RAG retrieval, PatientExtractor, EligibilityMatcher,
TrialOrchestrator prompt 호출, JSON repair/loose parsing, deterministic
baseline 비교를 수행하고 `outputs/` 아래에 JSON report를 쓴다.
`--labels-output outputs/labels.tsv`를 추가하면
`PATIENT_ID<TAB>TRIAL_ID<TAB>LABEL` 형식의 batch labeling 파일도 만든다.

## 축소 대회 산출물 파이프라인

현재 repo는 대회 기준의 축소 end-to-end artifact를 생성할 수 있다.

```bash
python scripts/run_competition_pipeline.py \
  --trial-limit 120 \
  --patient-count 1000 \
  --top-k 30
```

K-EXAONE smoke까지 포함하려면:

```bash
python scripts/run_competition_pipeline.py \
  --trial-limit 120 \
  --patient-count 1000 \
  --top-k 30 \
  --with-llm-smoke \
  --env-file "<path-to-local-env-file>"
```

현재 생성된 기준 산출물:

- `data/processed/trials.jsonl`: ClinicalTrials.gov에서 수집/정규화한 120개 trial
- `data/processed/synthetic_patients.jsonl`: synthetic patient 1,000명
- `outputs/retrieval_candidates.jsonl`: 30,000개 retrieved patient-trial pair
- `artifacts/health-agent-submission/`: manifest, evaluation summary, labels TSV, demo cases, disclaimer

현재 smoke 지표:

- retrieval target trial recall@30: `0.523`
- candidate pairs: `30,000`
- K-EXAONE smoke: 2명, top-2, 6 agent calls, HTTP 200 `6/6`
- LLM valid label rate: `1.0`
- LLM JSON parse rate: `1.0`

## Codex 작업 순서

Codex는 다음 순서로 읽고 작업한다.

1. `README.md`
2. `AGENTS.md`
3. `CODEX.md`
4. `TASKS.md`
5. `src/hc_agent/schemas.py`
6. `scripts/run_demo.py`
7. `tests/`

첫 작업은 다음이다.

```text
1. 현재 테스트를 실행한다.
2. 깨지는 테스트가 있으면 스키마 또는 import path부터 고친다.
3. README의 Phase 1 항목을 기준으로 deterministic baseline을 완성한다.
4. 그 다음 ClinicalTrials.gov ingestion stub을 구현한다.
```

## Medical disclaimer

이 프로젝트의 출력은 연구 및 참고용이며, 의학적 자문이나 실제 임상 의사결정으로 사용해서는 안 된다. 실제 환자 진료, 임상시험 등록, 치료 결정에는 반드시 자격 있는 의료 전문가와 공식 임상시험 담당자의 판단이 필요하다.
