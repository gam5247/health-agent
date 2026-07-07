from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from health_agent.data import load_patients, load_trials
from health_agent.llm_client import parse_openai_compatible_sse
from health_agent.orchestrator import (
    AgentTokenBudget,
    normalize_final_labels,
    parse_agent_json,
    patient_to_clinical_note,
    run_patient_orchestration,
)
from health_agent.rag import build_rag_index, retrieve_trials
from health_agent.scoring import evaluate_trial


class LlmIntegrationSupportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.patients = load_patients(ROOT / "data" / "raw" / "synthetic-patients.json")
        self.trials = load_trials(ROOT / "data" / "raw" / "sample-trials.json")

    def test_sse_parser_concatenates_openai_compatible_chunks(self) -> None:
        stream = "\n\n".join(
            [
                'data: {"choices":[{"delta":{"content":"hel"}}]}',
                'data: {"choices":[{"delta":{"content":"lo"},"finish_reason":"stop"}]}',
                "data: [DONE]",
            ]
        )
        parsed = parse_openai_compatible_sse(stream)
        self.assertEqual(parsed.content, "hello")
        self.assertEqual(parsed.finish_reason, "stop")

    def test_rag_retrieves_egfr_trial_for_egfr_note(self) -> None:
        index = build_rag_index(self.trials)
        note = patient_to_clinical_note(self.patients[0])
        retrieved = retrieve_trials(index, note, top_k=1)
        self.assertEqual(retrieved[0].trial.trial_id, "NCT-SAMPLE-001")

    def test_agent_json_parser_repairs_trailing_comma(self) -> None:
        parsed = parse_agent_json(
            '{"matches":[{"trial_id":"NCT-SAMPLE-001","decision":"recommend",}],}',
            "matcher",
        )
        self.assertTrue(parsed.ok)
        self.assertEqual(parsed.value["matches"][0]["decision"], "recommend")

    def test_normalize_final_labels_uses_deterministic_fallback(self) -> None:
        trial = self.trials[0]
        expected = {trial.trial_id: evaluate_trial(self.patients[0], trial).decision}
        labels = normalize_final_labels(
            orchestrator={},
            matcher={},
            retrieved_trials=[trial],
            expected_by_trial=expected,
        )
        self.assertEqual(labels[0]["source"], "deterministic_fallback")
        self.assertEqual(labels[0]["decision"], "recommend")
        self.assertTrue(labels[0]["human_review_required"])

    def test_dry_run_orchestration_returns_labels_without_api_calls(self) -> None:
        index = build_rag_index(self.trials)
        note = patient_to_clinical_note(self.patients[0])
        retrieved = retrieve_trials(index, note, top_k=2)
        result = run_patient_orchestration(
            patient=self.patients[0],
            note=note,
            retrieved=retrieved,
            all_trials=self.trials,
            client=None,
            token_budget=AgentTokenBudget(),
        )
        self.assertEqual(result["agentCalls"], {})
        self.assertEqual(len(result["labels"]), 2)
        self.assertTrue(all(label["decision"] for label in result["labels"]))


if __name__ == "__main__":
    unittest.main()

