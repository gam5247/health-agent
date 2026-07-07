# Codex Bootstrap Prompt

You are working in the `health-agent` repository.

Goal: build a multi-agent clinical trial matching system that parses trial
protocols, profiles patient data, asks for missing information, and recommends
clinical trials with explicit evidence. This must not behave like a generic
chatbot.

Start by running:

```bash
python -m unittest discover -s tests
python scripts/run_demo.py --limit 3
python scripts/run_llm_eval.py --dry-run --max-patients 2 --top-k 2
```

Preserve these invariants:

- Every recommendation has patient id, trial id, score, decision, rationale,
  evidence, and follow-up questions.
- Missing information and confirmed conflicts are different states.
- All bundled patient records are synthetic.
- Clinical output must remain covered by `MEDICAL_DISCLAIMER.md`.
- API keys must stay in OS env or a local `.env`; never paste them into prompts,
  commits, or reports.
