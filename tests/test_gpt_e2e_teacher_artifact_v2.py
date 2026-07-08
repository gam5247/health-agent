from __future__ import annotations

import json
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = ROOT / "artifacts" / "gpt-e2e-teacher-labeling"
ALLOWED_ELIGIBILITY = {"eligible", "ineligible", "uncertain"}
ALLOWED_CRITERION_STATUS = {"satisfied", "violated", "unknown", "not_applicable"}
AGENT_KEYS = {
    "criteria_parser_agent",
    "patient_information_understanding_agent",
    "initial_matching_agent",
    "question_generation_agent",
    "interaction_simulation_agent",
    "final_matching_agent",
    "recommendation_agent",
    "result_explanation_agent",
}


class GptE2ETeacherArtifactV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.input_payload = json.loads(
            (ARTIFACT_DIR / "gpt_e2e_teacher_input_100.json").read_text(encoding="utf-8")
        )
        cls.expected_patients = {
            patient["patient_id"]: patient
            for patient in cls.input_payload["patients"]
        }
        cls.records = [
            json.loads(line)
            for line in (ARTIFACT_DIR / "gpt_e2e_teacher_labels_100.v2.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        ]
        cls.json_payload = json.loads(
            (ARTIFACT_DIR / "gpt_e2e_teacher_labels_100.v2.json").read_text(
                encoding="utf-8"
            )
        )
        cls.summary = json.loads(
            (ARTIFACT_DIR / "gpt_e2e_teacher_labels_100.v2_summary.json").read_text(
                encoding="utf-8"
            )
        )

    def test_jsonl_is_canonical_and_json_copy_matches(self) -> None:
        self.assertEqual(self.json_payload["patients"], self.records)
        self.assertEqual(self.json_payload["patient_count"], 100)
        self.assertEqual(len(self.records), 100)
        self.assertEqual(
            [record["patient_id"] for record in self.records],
            [f"SYN-GEN-{index:05d}" for index in range(1, 101)],
        )

    def test_final_output_matches_competition_answer_contract(self) -> None:
        for record in self.records:
            patient_id = record["patient_id"]
            expected = self.expected_patients[patient_id]
            expected_trials = [trial["trial_id"] for trial in expected["candidate_trials"]]
            expected_criteria = {
                trial["trial_id"]: {
                    criterion["criterion_id"]
                    for criterion in trial["criteria_to_assess"]
                }
                for trial in expected["candidate_trials"]
            }
            candidate_trial_ids = [trial["trial_id"] for trial in record["candidate_trials"]]
            self.assertEqual(sorted(candidate_trial_ids), sorted(expected_trials))
            self.assertTrue(record["patient_information_string"])
            self.assertTrue(AGENT_KEYS <= set(record["agent_trace"]))

            output = record["final_output"]
            self.assertTrue(output["medical_disclaimer"])
            self.assertTrue(output["patient_level_summary"])
            initial_trials = output["initial_assessment"]["evaluated_trials"]
            final_trials = output["final_assessment_after_answers"]["evaluated_trials"]
            self.assertEqual(sorted(row["trial_id"] for row in initial_trials), sorted(expected_trials))
            self.assertEqual(sorted(row["trial_id"] for row in final_trials), sorted(expected_trials))
            self._assert_evaluated_trials(initial_trials, expected_criteria)
            self._assert_evaluated_trials(final_trials, expected_criteria)

            final_by_id = {row["trial_id"]: row for row in final_trials}
            recommendation_ids = [row["trial_id"] for row in output["recommended_trials"]]
            uncertain_ids = [row["trial_id"] for row in output["uncertain_but_actionable_trials"]]
            excluded_ids = [row["trial_id"] for row in output["excluded_trials"]]
            self.assertEqual(
                sorted(recommendation_ids + uncertain_ids + excluded_ids),
                sorted(expected_trials),
            )
            for row in output["recommended_trials"]:
                self.assertEqual(row["eligibility"], "eligible")
                self.assertEqual(final_by_id[row["trial_id"]]["eligibility"], "eligible")
                self.assertTrue(row["recommendation_reason"])
            for row in output["uncertain_but_actionable_trials"]:
                self.assertEqual(row["eligibility"], "uncertain")
                self.assertEqual(final_by_id[row["trial_id"]]["eligibility"], "uncertain")
                self.assertTrue(row["reason"])
            for row in output["excluded_trials"]:
                self.assertEqual(row["eligibility"], "ineligible")
                self.assertEqual(final_by_id[row["trial_id"]]["eligibility"], "ineligible")
                self.assertTrue(row["exclusion_reason"])

            question_ids = {
                question["question_id"]
                for question in output["follow_up_questions"]
            }
            valid_criteria = {
                criterion_id
                for criteria in expected_criteria.values()
                for criterion_id in criteria
            }
            for question in output["follow_up_questions"]:
                self.assertTrue(question["question"])
                self.assertIsInstance(question["needed_for"], list)
                for link in question["needed_for"]:
                    self.assertIn(link["trial_id"], expected_trials)
                    if link["criterion_id"]:
                        self.assertIn(link["criterion_id"], valid_criteria)
            for answer in output["simulated_patient_answers"]:
                self.assertIn(answer["question_id"], question_ids)
                self.assertTrue(answer["answer"])

    def test_summary_counts_match_records(self) -> None:
        eligibility = Counter()
        criterion_status = Counter()
        recommended_count = 0
        uncertain_count = 0
        excluded_count = 0
        question_count = 0
        answer_count = 0
        final_evaluated_count = 0
        initial_evaluated_count = 0
        for record in self.records:
            output = record["final_output"]
            recommended_count += len(output["recommended_trials"])
            uncertain_count += len(output["uncertain_but_actionable_trials"])
            excluded_count += len(output["excluded_trials"])
            question_count += len(output["follow_up_questions"])
            answer_count += len(output["simulated_patient_answers"])
            initial_evaluated_count += len(output["initial_assessment"]["evaluated_trials"])
            for row in output["final_assessment_after_answers"]["evaluated_trials"]:
                final_evaluated_count += 1
                eligibility[row["eligibility"]] += 1
                for criterion in row["criterion_results"]:
                    criterion_status[criterion["status"]] += 1

        self.assertEqual(self.summary["patient_count"], 100)
        self.assertEqual(self.summary["recommended_trial_count"], recommended_count)
        self.assertEqual(self.summary["uncertain_but_actionable_trial_count"], uncertain_count)
        self.assertEqual(self.summary["excluded_trial_count"], excluded_count)
        self.assertEqual(self.summary["follow_up_question_count"], question_count)
        self.assertEqual(self.summary["simulated_patient_answer_count"], answer_count)
        self.assertEqual(self.summary["initial_evaluated_trial_count"], initial_evaluated_count)
        self.assertEqual(self.summary["final_evaluated_trial_count"], final_evaluated_count)
        self.assertEqual(self.summary["eligibility_distribution"], dict(sorted(eligibility.items())))
        self.assertEqual(
            self.summary["criterion_status_distribution"],
            dict(sorted(criterion_status.items())),
        )
        self.assertEqual(self.summary["validation_error_count"], 0)

    def test_review_regression_examples_are_fixed(self) -> None:
        record_71 = self._record("SYN-GEN-00071")
        output_71 = record_71["final_output"]
        self.assertEqual(
            [(row["trial_id"], row["eligibility"]) for row in output_71["recommended_trials"]],
            [("NCT07312760", "eligible"), ("NCT07091617", "eligible")],
        )
        self.assertTrue(
            all(row["eligibility"] == "ineligible" for row in output_71["excluded_trials"])
        )
        initial_71 = {
            row["trial_id"]: row["eligibility"]
            for row in output_71["initial_assessment"]["evaluated_trials"]
        }
        final_71 = {
            row["trial_id"]: row["eligibility"]
            for row in output_71["final_assessment_after_answers"]["evaluated_trials"]
        }
        self.assertEqual(initial_71["NCT07312760"], "uncertain")
        self.assertEqual(final_71["NCT07312760"], "eligible")
        self.assertEqual(len(output_71["follow_up_questions"]), 5)
        self.assertEqual(len(output_71["simulated_patient_answers"]), 5)

        record_86 = self._record("SYN-GEN-00086")
        self.assertNotIn("answer_only_question_placeholder_added", record_86["quality_flags"])
        questions_86 = {
            question["question_id"]: question
            for question in record_86["final_output"]["follow_up_questions"]
        }
        self.assertIn(
            {
                "trial_id": "NCT03237780",
                "criterion_id": "NCT03237780-I-prior-platinum-chemotherapy",
            },
            questions_86["SYN-GEN-00086-Q02"]["needed_for"],
        )

    def _record(self, patient_id: str) -> dict:
        return next(record for record in self.records if record["patient_id"] == patient_id)

    def _assert_evaluated_trials(
        self,
        rows: list[dict],
        expected_criteria: dict[str, set[str]],
    ) -> None:
        for row in rows:
            self.assertIn(row["eligibility"], ALLOWED_ELIGIBILITY)
            self.assertTrue(row["explanation"])
            actual_criteria = {
                criterion["criterion_id"]
                for criterion in row["criterion_results"]
            }
            self.assertEqual(actual_criteria, expected_criteria[row["trial_id"]])
            for criterion in row["criterion_results"]:
                self.assertIn(criterion["status"], ALLOWED_CRITERION_STATUS)
                self.assertIsInstance(criterion["reason"], str)


if __name__ == "__main__":
    unittest.main()
