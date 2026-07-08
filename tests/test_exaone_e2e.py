from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from health_agent.e2e_orchestrator import blinded_input_from_answer_record
from health_agent.exaone_e2e import (
    build_exaone_e2e_messages,
    normalize_exaone_prediction,
    parse_json_object,
)
from health_agent.hidden_eval import validate_prediction_contract
from health_agent.llm_client import ChatResult


ANSWER_KEY = ROOT / "artifacts" / "gpt-e2e-teacher-labeling" / "gpt_e2e_teacher_labels_100.v2.jsonl"


class ExaoneE2ETests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        answer = json.loads(ANSWER_KEY.read_text(encoding="utf-8").splitlines()[0])
        cls.answer = answer
        cls.blinded = blinded_input_from_answer_record(answer)

    def test_prompt_contains_no_hidden_answer_fields(self) -> None:
        messages = build_exaone_e2e_messages(self.blinded)
        text = "\n".join(message["content"] for message in messages)
        self.assertIn(self.blinded["patient_id"], text)
        self.assertNotIn("teacher_rationale", text)
        self.assertNotIn("final_output", json.dumps(self.blinded))
        self.assertNotIn("agent_trace", json.dumps(self.blinded))

    def test_parse_json_object_repairs_fenced_json(self) -> None:
        parsed = parse_json_object('```json\n{"a": 1,}\n```')
        self.assertTrue(parsed.ok)
        self.assertTrue(parsed.repaired)
        self.assertEqual(parsed.value["a"], 1)

    def test_normalized_exaone_output_satisfies_competition_contract(self) -> None:
        trial = self.blinded["candidate_trials"][0]
        payload = {
            "patient_id": self.blinded["patient_id"],
            "initial_assessment": {
                "evaluated_trials": [
                    {
                        "trial_id": trial["trial_id"],
                        "eligibility": "uncertain",
                        "criterion_results": [
                            {
                                "criterion_id": criterion["criterion_id"],
                                "status": "unknown",
                                "reason": "Missing information.",
                            }
                            for criterion in trial["criteria_to_assess"]
                        ],
                        "explanation": "More information is needed.",
                    }
                ]
            },
            "follow_up_questions": [
                {
                    "question_id": f"{self.blinded['patient_id']}-Q01",
                    "question": "What missing information is available?",
                    "needed_for": [
                        {
                            "trial_id": trial["trial_id"],
                            "criterion_id": trial["criteria_to_assess"][0]["criterion_id"],
                        }
                    ],
                    "reason": "The criterion was unknown.",
                }
            ],
            "simulated_patient_answers": [],
            "final_assessment_after_answers": {
                "evaluated_trials": [
                    {
                        "trial_id": trial["trial_id"],
                        "eligibility": "uncertain",
                        "criterion_results": [
                            {
                                "criterion_id": criterion["criterion_id"],
                                "status": "unknown",
                                "reason": "Missing information.",
                            }
                            for criterion in trial["criteria_to_assess"]
                        ],
                        "explanation": "More information is needed.",
                    }
                ]
            },
            "patient_level_summary": "No eligible trial was confirmed.",
        }
        call = ChatResult(
            ok=True,
            http_status=200,
            retry_after="",
            ms=123,
            content=json.dumps(payload),
            finish_reason="stop",
        )
        parsed = parse_json_object(call.content)
        prediction = normalize_exaone_prediction(self.blinded, call, parsed)
        self.assertEqual(
            validate_prediction_contract(prediction, self.answer),
            [],
        )
        self.assertEqual(
            len(prediction["final_output"]["final_assessment_after_answers"]["evaluated_trials"]),
            len(self.blinded["candidate_trials"]),
        )

    def test_failed_exaone_parse_still_builds_contract_complete_prediction(self) -> None:
        call = ChatResult(
            ok=True,
            http_status=200,
            retry_after="",
            ms=123,
            content="not json",
        )
        parsed = parse_json_object(call.content)
        prediction = normalize_exaone_prediction(self.blinded, call, parsed)
        self.assertFalse(prediction["agent_trace"]["exaone_call"]["json_ok"])
        self.assertEqual(validate_prediction_contract(prediction, self.answer), [])


if __name__ == "__main__":
    unittest.main()
