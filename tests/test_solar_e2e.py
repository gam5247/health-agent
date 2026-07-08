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
from health_agent.solar_e2e import (
    aggregate_from_criterion_statuses,
    build_solar_e2e_messages,
    build_solar_tool_messages,
    normalize_solar_prediction,
    parse_json_object,
    run_solar_e2e_orchestration,
    run_solar_multi_agent_e2e_orchestration,
)
from health_agent.hidden_eval import validate_prediction_contract
from health_agent.llm_client import ChatResult
from health_agent.solar_tools import (
    SolarToolDatabase,
    ToolCall,
    parse_solar_tool_calls,
    solar_tool_definitions,
)


ANSWER_KEY = ROOT / "artifacts" / "gpt-e2e-teacher-labeling" / "gpt_e2e_teacher_labels_100.v2.jsonl"


class SolarE2ETests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        answer = json.loads(ANSWER_KEY.read_text(encoding="utf-8").splitlines()[0])
        cls.answer = answer
        cls.blinded = blinded_input_from_answer_record(answer)

    def test_prompt_contains_no_hidden_answer_fields(self) -> None:
        messages = build_solar_e2e_messages(self.blinded)
        text = "\n".join(message["content"] for message in messages)
        self.assertIn(self.blinded["patient_id"], text)
        self.assertNotIn("teacher_rationale", text)
        self.assertNotIn("final_output", json.dumps(self.blinded))
        self.assertNotIn("agent_trace", json.dumps(self.blinded))

    def test_tool_prompt_uses_native_tools_without_inlining_candidate_database(self) -> None:
        messages = build_solar_tool_messages(self.blinded)
        text = "\n".join(message["content"] for message in messages)
        self.assertIn(self.blinded["patient_id"], text)
        self.assertIn("function tools", text)
        self.assertNotIn("candidate_trials", text)
        tool_names = [item["function"]["name"] for item in solar_tool_definitions()]
        self.assertIn("get_patient_candidate_bundle", tool_names)
        for tool in solar_tool_definitions():
            parameters = tool["function"]["parameters"]
            self.assertEqual(parameters["type"], "object")
            self.assertIn("properties", parameters)
            self.assertFalse(parameters["additionalProperties"])

    def test_solar_tool_database_returns_visible_bundle(self) -> None:
        trial = self.blinded["candidate_trials"][0]
        db = SolarToolDatabase(
            self.blinded,
            trial_database_records=[
                {
                    "trial_id": trial["trial_id"],
                    "title": trial["trial_title"],
                    "eligibility_criteria": "Public trial criteria text.",
                    "private_note": "must not leak",
                }
            ],
        )
        result = db.execute(
            ToolCall(
                call_id="call_1",
                name="get_patient_candidate_bundle",
                arguments={},
            )
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["result"]["patient_id"], self.blinded["patient_id"])
        self.assertEqual(
            len(result["result"]["candidate_trials"]),
            len(self.blinded["candidate_trials"]),
        )
        first_detail = result["result"]["candidate_trials"][0]
        self.assertIn("database_record", first_detail)
        self.assertIn("eligibility_criteria", first_detail["database_record"])
        self.assertNotIn("private_note", first_detail["database_record"])

    def test_parse_native_solar_tool_calls(self) -> None:
        calls = parse_solar_tool_calls(
            [
                {
                    "id": "toolu_1",
                    "type": "function",
                    "function": {
                        "name": "get_trial_detail",
                        "arguments": "{\"trial_id\":\"NCT00000000\"}",
                    },
                }
            ]
        )
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0].call_id, "toolu_1")
        self.assertEqual(calls[0].name, "get_trial_detail")
        self.assertEqual(calls[0].arguments["trial_id"], "NCT00000000")

    def test_parse_json_object_repairs_fenced_json(self) -> None:
        parsed = parse_json_object('```json\n{"a": 1,}\n```')
        self.assertTrue(parsed.ok)
        self.assertTrue(parsed.repaired)
        self.assertEqual(parsed.value["a"], 1)

    def test_normalized_solar_output_satisfies_competition_contract(self) -> None:
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
        prediction = normalize_solar_prediction(self.blinded, call, parsed)
        self.assertEqual(
            validate_prediction_contract(prediction, self.answer),
            [],
        )
        self.assertEqual(
            len(prediction["final_output"]["final_assessment_after_answers"]["evaluated_trials"]),
            len(self.blinded["candidate_trials"]),
        )

    def test_simulated_patient_answers_are_preserved_and_validated(self) -> None:
        trial = self.blinded["candidate_trials"][0]
        question_id = f"{self.blinded['patient_id']}-Q01"
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
                                "reason": "Missing before follow-up.",
                            }
                            for criterion in trial["criteria_to_assess"]
                        ],
                        "explanation": "Initial judgment needs more information.",
                    }
                ]
            },
            "follow_up_questions": [
                {
                    "question_id": question_id,
                    "question": "Is the missing eligibility fact present?",
                    "needed_for": [
                        {
                            "trial_id": trial["trial_id"],
                            "criterion_id": trial["criteria_to_assess"][0]["criterion_id"],
                        }
                    ],
                    "reason": "Needed to resolve the initial unknown status.",
                }
            ],
            "simulated_patient_answers": [
                {
                    "question_id": question_id,
                    "answer": "No, the missing exclusion finding is absent.",
                },
                {
                    "question_id": "not-a-real-question",
                    "answer": "This answer must be dropped.",
                },
            ],
            "final_assessment_after_answers": {
                "evaluated_trials": [
                    {
                        "trial_id": trial["trial_id"],
                        "eligibility": "eligible",
                        "criterion_results": [
                            {
                                "criterion_id": criterion["criterion_id"],
                                "status": "satisfied",
                                "reason": "Resolved using the simulated follow-up answer.",
                            }
                            for criterion in trial["criteria_to_assess"]
                        ],
                        "explanation": "Final judgment uses the simulated follow-up answer.",
                    }
                ]
            },
            "patient_level_summary": "The second-pass judgment changed after follow-up.",
        }
        call = ChatResult(
            ok=True,
            http_status=200,
            retry_after="",
            ms=123,
            content=json.dumps(payload),
            finish_reason="stop",
        )
        prediction = normalize_solar_prediction(
            self.blinded,
            call,
            parse_json_object(call.content),
        )
        answers = prediction["final_output"]["simulated_patient_answers"]
        self.assertEqual(len(answers), 1)
        self.assertEqual(answers[0]["question_id"], question_id)
        self.assertIn("exclusion finding is absent", answers[0]["answer"])
        audit = prediction["agent_trace"]["solar_normalization_audit"]
        self.assertEqual(audit["simulated_answers_kept"], 1)
        self.assertEqual(audit["simulated_answers_dropped"], 1)
        self.assertEqual(validate_prediction_contract(prediction, self.answer), [])

    def test_structural_questions_are_based_on_initial_unknowns(self) -> None:
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
                                "reason": "Missing before follow-up.",
                            }
                            for criterion in trial["criteria_to_assess"]
                        ],
                        "explanation": "Initial judgment needs more information.",
                    }
                ]
            },
            "follow_up_questions": [],
            "simulated_patient_answers": [],
            "final_assessment_after_answers": {
                "evaluated_trials": [
                    {
                        "trial_id": trial["trial_id"],
                        "eligibility": "eligible",
                        "criterion_results": [
                            {
                                "criterion_id": criterion["criterion_id"],
                                "status": "satisfied",
                                "reason": "Resolved after follow-up simulation.",
                            }
                            for criterion in trial["criteria_to_assess"]
                        ],
                        "explanation": "Final judgment changed after follow-up.",
                    }
                ]
            },
            "patient_level_summary": "The second-pass judgment changed after follow-up.",
        }
        call = ChatResult(
            ok=True,
            http_status=200,
            retry_after="",
            ms=123,
            content=json.dumps(payload),
            finish_reason="stop",
        )
        prediction = normalize_solar_prediction(
            self.blinded,
            call,
            parse_json_object(call.content),
        )
        questions = prediction["final_output"]["follow_up_questions"]
        self.assertEqual(len(questions), 1)
        needed_for = {
            (item["trial_id"], item["criterion_id"])
            for item in questions[0]["needed_for"]
        }
        expected_links = {
            (trial["trial_id"], criterion["criterion_id"])
            for criterion in trial["criteria_to_assess"]
        }
        self.assertTrue(expected_links.issubset(needed_for))
        self.assertEqual(validate_prediction_contract(prediction, self.answer), [])

    def test_inconsistent_trial_eligibility_is_corrected_from_criteria(self) -> None:
        trial = self.blinded["candidate_trials"][0]
        payload = {
            "patient_id": self.blinded["patient_id"],
            "initial_assessment": {
                "evaluated_trials": [
                    {
                        "trial_id": trial["trial_id"],
                        "eligibility": "eligible",
                        "criterion_results": [
                            {
                                "criterion_id": criterion["criterion_id"],
                                "status": "unknown" if index == 0 else "satisfied",
                                "reason": "Synthetic test reason.",
                            }
                            for index, criterion in enumerate(trial["criteria_to_assess"])
                        ],
                        "explanation": "Model-level label conflicts with criterion statuses.",
                    }
                ]
            },
            "final_assessment_after_answers": {
                "evaluated_trials": [
                    {
                        "trial_id": trial["trial_id"],
                        "eligibility": "eligible",
                        "criterion_results": [
                            {
                                "criterion_id": criterion["criterion_id"],
                                "status": "unknown" if index == 0 else "satisfied",
                                "reason": "Synthetic test reason.",
                            }
                            for index, criterion in enumerate(trial["criteria_to_assess"])
                        ],
                        "explanation": "Model-level label conflicts with criterion statuses.",
                    }
                ]
            },
            "follow_up_questions": [],
            "simulated_patient_answers": [],
        }
        prediction = normalize_solar_prediction(
            self.blinded,
            ChatResult(
                ok=True,
                http_status=200,
                retry_after="",
                ms=123,
                content=json.dumps(payload),
            ),
            parse_json_object(json.dumps(payload)),
        )
        final_row = prediction["final_output"]["final_assessment_after_answers"]["evaluated_trials"][0]
        self.assertEqual(final_row["eligibility"], "uncertain")
        audit = prediction["agent_trace"]["solar_normalization_audit"]
        self.assertEqual(audit["final_inconsistent_eligibility_corrected"], 1)
        self.assertEqual(validate_prediction_contract(prediction, self.answer), [])

    def test_not_applicable_criterion_makes_trial_ineligible(self) -> None:
        self.assertEqual(
            aggregate_from_criterion_statuses(
                [
                    {"criterion_id": "A", "status": "satisfied"},
                    {"criterion_id": "B", "status": "not_applicable"},
                ]
            ),
            "ineligible",
        )

    def test_failed_solar_parse_still_builds_contract_complete_prediction(self) -> None:
        call = ChatResult(
            ok=True,
            http_status=200,
            retry_after="",
            ms=123,
            content="not json",
        )
        parsed = parse_json_object(call.content)
        prediction = normalize_solar_prediction(self.blinded, call, parsed)
        self.assertFalse(prediction["agent_trace"]["solar_call"]["json_ok"])
        self.assertEqual(validate_prediction_contract(prediction, self.answer), [])

    def test_native_tool_orchestration_satisfies_competition_contract(self) -> None:
        trial = self.blinded["candidate_trials"][0]
        final_payload = {
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
                                "reason": "The patient note does not state this detail.",
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
                    "question": "Can the missing eligibility details be confirmed?",
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
                                "reason": "The patient note does not state this detail.",
                            }
                            for criterion in trial["criteria_to_assess"]
                        ],
                        "explanation": "More information is needed.",
                    }
                ]
            },
            "patient_level_summary": "No eligible trial was confirmed.",
        }
        client = FakeSolarClient(json.dumps(final_payload))
        prediction = run_solar_e2e_orchestration(
            self.blinded,
            client=client,
            trial_database_records=[],
            max_tool_rounds=1,
        )
        self.assertEqual(validate_prediction_contract(prediction, self.answer), [])
        self.assertEqual(prediction["runner"], "solar-pro3-native-tools")
        self.assertTrue(prediction["agent_trace"]["solar_tool_trace"])
        self.assertEqual(len(client.requests), 2)
        self.assertTrue(client.requests[0]["tools"])
        self.assertEqual(
            client.requests[0]["tool_choice"],
            {
                "type": "function",
                "function": {"name": "get_patient_candidate_bundle"},
            },
        )
        self.assertFalse(client.requests[0]["parallel_tool_calls"])
        tool_messages = [
            message
            for message in client.requests[1]["messages"]
            if message.get("role") == "tool"
        ]
        self.assertEqual(len(tool_messages), 1)
        self.assertIn(self.blinded["patient_id"], tool_messages[0]["content"])

    def test_native_tool_orchestration_fails_closed_when_no_tool_call_occurs(self) -> None:
        client = FakeSolarClient(
            json.dumps({"patient_id": self.blinded["patient_id"]}),
            first_tool_calls=(),
        )
        prediction = run_solar_e2e_orchestration(
            self.blinded,
            client=client,
            trial_database_records=[],
            max_tool_rounds=1,
        )
        self.assertFalse(prediction["agent_trace"]["solar_call"]["ok"])
        self.assertIn(
            "no native tool call",
            prediction["agent_trace"]["solar_call"]["error"],
        )
        self.assertEqual(validate_prediction_contract(prediction, self.answer), [])

    def test_six_call_multi_agent_orchestration_satisfies_contract(self) -> None:
        initial_rows = build_test_evaluated_rows(
            self.blinded,
            eligibility="uncertain",
            status="unknown",
            reason="The patient note does not state this detail.",
        )
        final_rows = build_test_evaluated_rows(
            self.blinded,
            eligibility="eligible",
            status="satisfied",
            reason="The simulated follow-up answer resolves this detail.",
        )
        first_trial = self.blinded["candidate_trials"][0]
        first_criterion = first_trial["criteria_to_assess"][0]
        question_id = f"{self.blinded['patient_id']}-Q01"
        client = FakeSequenceSolarClient(
            [
                {
                    "patient_id": self.blinded["patient_id"],
                    "parsed_trials": [
                        {
                            "trial_id": trial["trial_id"],
                            "trial_title": trial["trial_title"],
                            "parsed_criteria": trial["criteria_to_assess"],
                        }
                        for trial in self.blinded["candidate_trials"]
                    ],
                },
                {
                    "patient_id": self.blinded["patient_id"],
                    "extracted_patient_facts": {"diagnosis": "synthetic diagnosis"},
                    "missing_patient_fields": ["follow_up_detail"],
                    "known_fact_summary": "Synthetic patient facts were extracted.",
                },
                {
                    "patient_id": self.blinded["patient_id"],
                    "evaluated_trials": initial_rows,
                },
                {
                    "patient_id": self.blinded["patient_id"],
                    "follow_up_questions": [
                        {
                            "question_id": question_id,
                            "question": "Can the missing eligibility detail be confirmed?",
                            "needed_for": [
                                {
                                    "trial_id": first_trial["trial_id"],
                                    "criterion_id": first_criterion["criterion_id"],
                                }
                            ],
                            "reason": "The initial pass marked this criterion unknown.",
                        }
                    ],
                    "simulated_patient_answers": [
                        {
                            "question_id": question_id,
                            "answer": "Yes, the missing detail is confirmed for this synthetic workflow.",
                            "source": "solar-pro3-simulated-follow-up",
                        }
                    ],
                },
                {
                    "patient_id": self.blinded["patient_id"],
                    "final_assessment_after_answers": {
                        "evaluated_trials": final_rows,
                    },
                    "recommended_trials": [],
                    "uncertain_but_actionable_trials": [],
                    "excluded_trials": [],
                },
                {
                    "patient_id": self.blinded["patient_id"],
                    "trial_explanations": [
                        {
                            "trial_id": trial["trial_id"],
                            "explanation": "Final explanation from the result explanation agent.",
                        }
                        for trial in self.blinded["candidate_trials"]
                    ],
                    "patient_level_summary": "All supplied trials are eligible in this fake response.",
                    "medical_disclaimer": "Synthetic software-evaluation output only. Not medical advice and not a real clinical eligibility decision.",
                },
            ]
        )
        prediction = run_solar_multi_agent_e2e_orchestration(
            self.blinded,
            client=client,
            trial_database_records=[],
        )
        self.assertEqual(validate_prediction_contract(prediction, self.answer), [])
        self.assertEqual(prediction["runner"], "solar-pro3-six-call-multi-agent")
        self.assertEqual(len(client.requests), 6)
        self.assertEqual(
            prediction["agent_trace"]["solar_multi_agent_api_call_count"],
            6,
        )
        self.assertEqual(
            [
                row["agent"]
                for row in prediction["agent_trace"]["solar_multi_agent_calls"]
            ],
            [
                "criteria_parser_agent",
                "patient_information_understanding_agent",
                "inference_matching_agent_initial",
                "question_generation_agent",
                "recommendation_agent",
                "result_explanation_agent",
            ],
        )
        self.assertIn(
            "result explanation agent",
            prediction["final_output"]["final_assessment_after_answers"]["evaluated_trials"][0]["explanation"],
        )


class FakeSolarClient:
    def __init__(self, final_content: str, *, first_tool_calls=None) -> None:
        self.final_content = final_content
        self.first_tool_calls = first_tool_calls
        self.requests: list[dict[str, object]] = []

    def chat(self, messages, **kwargs) -> ChatResult:
        self.requests.append({"messages": messages, **kwargs})
        if len(self.requests) == 1:
            tool_calls = self.first_tool_calls
            if tool_calls is None:
                tool_calls = (
                    {
                        "id": "call_1",
                        "type": "function",
                        "function": {
                            "name": "get_patient_candidate_bundle",
                            "arguments": "{}",
                        },
                    },
                )
            return ChatResult(
                ok=True,
                http_status=200,
                retry_after="",
                ms=10,
                content=None,
                finish_reason="tool_calls",
                tool_calls=tool_calls,
            )
        return ChatResult(
            ok=True,
            http_status=200,
            retry_after="",
            ms=20,
            content=self.final_content,
            finish_reason="stop",
        )


class FakeSequenceSolarClient:
    def __init__(self, payloads: list[dict[str, object]]) -> None:
        self.payloads = payloads
        self.requests: list[dict[str, object]] = []

    def chat(self, messages, **kwargs) -> ChatResult:
        self.requests.append({"messages": messages, **kwargs})
        index = len(self.requests) - 1
        if index >= len(self.payloads):
            raise AssertionError("Unexpected extra Solar API call")
        return ChatResult(
            ok=True,
            http_status=200,
            retry_after="",
            ms=10 + index,
            content=json.dumps(self.payloads[index]),
            finish_reason="stop",
        )


def build_test_evaluated_rows(
    input_record: dict[str, object],
    *,
    eligibility: str,
    status: str,
    reason: str,
) -> list[dict[str, object]]:
    rows = []
    for trial in input_record["candidate_trials"]:
        rows.append(
            {
                "trial_id": trial["trial_id"],
                "eligibility": eligibility,
                "criterion_results": [
                    {
                        "criterion_id": criterion["criterion_id"],
                        "status": status,
                        "reason": reason,
                    }
                    for criterion in trial["criteria_to_assess"]
                ],
                "explanation": reason,
            }
        )
    return rows


if __name__ == "__main__":
    unittest.main()
