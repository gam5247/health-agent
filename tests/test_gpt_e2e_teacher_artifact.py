from __future__ import annotations

import json
import sys
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


ARTIFACT_DIR = ROOT / "artifacts" / "gpt-e2e-teacher-labeling"
ALLOWED_ELIGIBILITY = {"eligible", "ineligible", "uncertain"}
ALLOWED_CRITERION_STATUS = {"satisfied", "violated", "unknown", "not_applicable"}
AGENT_KEYS = {
    "criteria_parser_agent",
    "patient_information_understanding_agent",
    "inference_matching_agent",
    "question_generation_agent",
    "interaction_simulation_agent",
    "recommendation_agent",
    "result_explanation_agent",
}


class GptE2ETeacherArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.input_payload = json.loads(
            (ARTIFACT_DIR / "gpt_e2e_teacher_input_100.json").read_text(encoding="utf-8")
        )
        cls.expected_patients = {
            patient["patient_id"]: patient
            for patient in cls.input_payload["patients"]
        }
        cls.jsonl_records = [
            json.loads(line)
            for line in (ARTIFACT_DIR / "gpt_e2e_teacher_labels_100.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        ]
        cls.json_payload = json.loads(
            (ARTIFACT_DIR / "gpt_e2e_teacher_labels_100.json").read_text(encoding="utf-8")
        )
        cls.summary = json.loads(
            (ARTIFACT_DIR / "gpt_e2e_teacher_labels_100_summary.json").read_text(
                encoding="utf-8"
            )
        )

    def test_jsonl_is_canonical_and_json_copy_matches(self) -> None:
        self.assertEqual(self.json_payload["patients"], self.jsonl_records)
        self.assertEqual(self.json_payload["patient_count"], 100)
        self.assertEqual(len(self.jsonl_records), 100)
        self.assertEqual(
            [record["patient_id"] for record in self.jsonl_records],
            [f"SYN-GEN-{index:05d}" for index in range(1, 101)],
        )

    def test_records_match_schema_contract_and_input_ids(self) -> None:
        for record in self.jsonl_records:
            patient_id = record["patient_id"]
            expected = self.expected_patients[patient_id]
            self.assertTrue(record["patient_information_string"])
            self.assertEqual(
                record["input"]["patient_information_string"],
                record["patient_information_string"],
            )
            self.assertTrue(AGENT_KEYS <= set(record["agent_trace"]))

            expected_trials = [trial["trial_id"] for trial in expected["candidate_trials"]]
            output = record["final_output"]
            self.assertEqual(output["patient_id"], patient_id)
            self.assertTrue(output["medical_disclaimer"])
            self.assertEqual(
                sorted(output["recommended_trial_order"]),
                sorted(expected_trials),
            )
            self.assertEqual(
                sorted(item["trial_id"] for item in output["recommendations"]),
                sorted(expected_trials),
            )

            expected_criteria = {
                trial["trial_id"]: {
                    criterion["criterion_id"]
                    for criterion in trial["criteria_to_assess"]
                }
                for trial in expected["candidate_trials"]
            }
            for recommendation in output["recommendations"]:
                self.assertIn(recommendation["eligibility"], ALLOWED_ELIGIBILITY)
                self.assertGreaterEqual(int(recommendation["rank"]), 1)
                actual_criteria = {
                    criterion["criterion_id"]
                    for criterion in recommendation["criterion_results"]
                }
                self.assertEqual(
                    actual_criteria,
                    expected_criteria[recommendation["trial_id"]],
                )
                for criterion in recommendation["criterion_results"]:
                    self.assertIn(criterion["status"], ALLOWED_CRITERION_STATUS)
                    self.assertIsInstance(criterion["reason"], str)

    def test_summary_counts_match_records(self) -> None:
        eligibility = Counter()
        criterion_status = Counter()
        recommendation_count = 0
        criterion_count = 0
        question_count = 0
        answer_count = 0
        patients_with_questions = set()
        for record in self.jsonl_records:
            patient_id = record["patient_id"]
            for recommendation in record["final_output"]["recommendations"]:
                recommendation_count += 1
                eligibility[recommendation["eligibility"]] += 1
                question_count += len(recommendation["follow_up_questions"])
                answer_count += len(recommendation["simulated_patient_answers"])
                if recommendation["follow_up_questions"]:
                    patients_with_questions.add(patient_id)
                for criterion in recommendation["criterion_results"]:
                    criterion_count += 1
                    criterion_status[criterion["status"]] += 1

        self.assertEqual(self.summary["patient_count"], 100)
        self.assertEqual(self.summary["recommendation_count"], recommendation_count)
        self.assertEqual(self.summary["criterion_result_count"], criterion_count)
        self.assertEqual(self.summary["follow_up_question_count"], question_count)
        self.assertEqual(self.summary["simulated_patient_answer_count"], answer_count)
        self.assertEqual(
            self.summary["patients_with_follow_up_count"],
            len(patients_with_questions),
        )
        self.assertEqual(self.summary["eligibility_distribution"], dict(sorted(eligibility.items())))
        self.assertEqual(
            self.summary["criterion_status_distribution"],
            dict(sorted(criterion_status.items())),
        )
        self.assertEqual(self.summary["validation_error_count"], 0)
        self.assertEqual(self.summary["semantic_consistency_warning_count"], 28)


if __name__ == "__main__":
    unittest.main()
