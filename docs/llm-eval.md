# Legacy K-EXAONE / Friendli Evaluation

This is the older Friendli/K-EXAONE smoke-evaluation path. For the
competition-format hidden E2E evaluation, use
`scripts/run_solar_e2e_orchestration.py`.

This repository can run a reproducible local evaluation that combines:

- synthetic clinical notes derived from structured patient fixtures
- local deterministic trial RAG retrieval
- three K-EXAONE agent prompts: PatientExtractor, EligibilityMatcher, and
  TrialOrchestrator
- JSON repair and loose decision parsing
- comparison against the deterministic `scoring.py` baseline

## Configuration

Keep secrets outside git. The evaluator reads these variables from OS env or an
explicit local `.env` path:

- `FRIENDLI_API_KEY`, or fallback `K_EXAONE_API_KEY`
- `K_EXAONE_ENDPOINT_ID`, or fallback `FRIENDLI_ENDPOINT_ID` / `K_EXAONE_MODEL`

Defaults:

- `FRIENDLI_BASE_URL=https://api.friendli.ai/dedicated/v1`
- `FRIENDLI_CHAT_COMPLETIONS_URL=https://api.friendli.ai/dedicated/v1/chat/completions`

The request payload uses `stream: true`, `temperature: 0`,
`chat_template_kwargs.enable_thinking: false`, and `parse_reasoning: true`.
OpenAI-compatible SSE chunks are parsed from `choices[0].delta.content`.

## Commands

Dry-run:

```bash
python scripts/run_llm_eval.py --dry-run --max-patients 3 --top-k 3
```

Actual API smoke test:

```bash
python scripts/run_llm_eval.py \
  --env-file "<path-to-local-env-file>" \
  --max-patients 1 \
  --top-k 1 \
  --concurrency 1 \
  --labels-output outputs/labels.tsv
```

## Output

The JSON report includes:

- retrieved trial chunks per patient
- agent call status, latency, retry-after, and sanitized content preview
- parsed extractor, matcher, and orchestrator output
- final labels per patient-trial pair
- deterministic baseline agreement
- valid label rate, JSON parse rate, fallback label rate, and latency percentiles

The optional TSV label file uses:

```text
PATIENT_ID<TAB>TRIAL_ID<TAB>LABEL<TAB>SOURCE<TAB>AGREES<TAB>HUMAN_REVIEW_REQUIRED
```

## Scaling Notes

The current 3-call-per-patient pipeline is good for validation and debugging,
but too slow for large labeling jobs. For bulk work, keep local RAG retrieval,
prefer parser/validator extraction before LLM calls, batch matcher and
orchestrator prompts, retry only failed or malformed batches, and treat LLM
labels as silver-label drafts rather than gold labels.
