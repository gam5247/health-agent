from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from health_agent.e2e_orchestrator import (
    blinded_input_from_answer_record,
    run_competition_orchestration_v2,
)
from health_agent.blinded_audit import audit_blinded_record
from health_agent.hidden_eval import evaluate_predictions, validate_prediction_contract


ANSWER_KEY = ROOT / "artifacts" / "gpt-e2e-teacher-labeling" / "gpt_e2e_teacher_labels_100.v2.jsonl"


class E2EOrchestrationV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.answer_records = [
            json.loads(line)
            for line in ANSWER_KEY.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ][:3]

    def test_blinded_input_removes_hidden_labels(self) -> None:
        blinded = blinded_input_from_answer_record(self.answer_records[0])
        self.assertEqual(
            sorted(blinded),
            ["candidate_trials", "patient_id", "patient_information_string"],
        )
        self.assertNotIn("final_output", blinded)
        self.assertNotIn("agent_trace", blinded)
        self.assertEqual(len(blinded["candidate_trials"]), 5)
        self.assertEqual(audit_blinded_record(blinded), [])

    def test_blinded_input_audit_rejects_nested_answer_fields(self) -> None:
        blinded = blinded_input_from_answer_record(self.answer_records[0])
        tampered = json.loads(json.dumps(blinded))
        tampered["candidate_trials"][0]["final_output"] = {"eligibility": "eligible"}
        errors = audit_blinded_record(tampered)
        self.assertTrue(any("final_output" in error for error in errors))

    def test_orchestrator_outputs_competition_v2_contract(self) -> None:
        blinded = blinded_input_from_answer_record(self.answer_records[0])
        prediction = run_competition_orchestration_v2(blinded)
        errors = validate_prediction_contract(prediction, self.answer_records[0])
        self.assertEqual(errors, [])
        final = prediction["final_output"]
        self.assertEqual(
            len(final["initial_assessment"]["evaluated_trials"]),
            len(blinded["candidate_trials"]),
        )
        self.assertEqual(
            len(final["final_assessment_after_answers"]["evaluated_trials"]),
            len(blinded["candidate_trials"]),
        )
        self.assertTrue(final["medical_disclaimer"])
        self.assertTrue(final["patient_level_summary"])

    def test_hidden_eval_scores_predictions_without_contract_errors(self) -> None:
        predictions = [
            run_competition_orchestration_v2(blinded_input_from_answer_record(record))
            for record in self.answer_records
        ]
        report = evaluate_predictions(
            answer_records=self.answer_records,
            prediction_records=predictions,
        )
        self.assertEqual(report["patient_count_compared"], 3)
        self.assertEqual(report["contract"]["error_count"], 0)
        self.assertIn("accuracy", report["eligibility"])
        self.assertIn("macro_f1", report["eligibility"])
        self.assertIn("initial_eligibility", report)
        self.assertIn("by_family", report["criterion_status"])
        self.assertIn("interaction_transition", report)
        self.assertIn("f1", report["recommendation_set"])
        self.assertIn("precision", report["question_needed_for_links"])
        self.assertIn("f1", report["question_needed_for_links"])
        self.assertEqual(report["label_source"], "GPT E2E teacher v2 synthetic silver labels")

    def test_simulated_answers_can_update_final_matching(self) -> None:
        blinded = {
            "patient_id": "SYN-TEST-ANSWER-001",
            "patient_information_string": (
                "Tumor board intake: SYN-TEST-ANSWER-001 is a 55-year-old female "
                "with metastatic bladder urothelial carcinoma. Stage is recorded as IV. "
                "Molecular testing results are not available in the note. "
                "No active autoimmune disease is reported. The note is synthetic."
            ),
            "candidate_trials": [
                {
                    "trial_id": "NCTTEST001",
                    "trial_title": "Synthetic ECOG Follow-up Trial",
                    "trial_source_url": "https://clinicaltrials.gov/study/NCTTEST001",
                    "conditions": ["Metastatic Bladder Urothelial Carcinoma"],
                    "criteria_to_assess": [
                        {
                            "criterion_id": "NCTTEST001-I-condition",
                            "criterion_type": "inclusion",
                            "criterion": "Patient diagnosis should match the trial condition.",
                            "required": True,
                            "structured_value": ["Metastatic Bladder Urothelial Carcinoma"],
                        },
                        {
                            "criterion_id": "NCTTEST001-I-age",
                            "criterion_type": "inclusion",
                            "criterion": "Patient age should be within trial bounds.",
                            "required": True,
                            "structured_value": {"min_age": 18, "max_age": 75},
                        },
                        {
                            "criterion_id": "NCTTEST001-I-stage",
                            "criterion_type": "inclusion",
                            "criterion": "Patient disease stage should be allowed.",
                            "required": True,
                            "structured_value": ["IV"],
                        },
                        {
                            "criterion_id": "NCTTEST001-I-ecog",
                            "criterion_type": "inclusion",
                            "criterion": "Patient ECOG performance status should be at or below the maximum.",
                            "required": True,
                            "structured_value": 2,
                        },
                    ],
                }
            ],
        }
        prediction = run_competition_orchestration_v2(
            blinded,
            simulated_answers=[
                {
                    "question_id": "SYN-TEST-ANSWER-001-Q01",
                    "answer": "ECOG performance status is 1.",
                }
            ],
        )
        final = prediction["final_output"]
        self.assertEqual(final["initial_assessment"]["evaluated_trials"][0]["eligibility"], "uncertain")
        self.assertEqual(
            final["final_assessment_after_answers"]["evaluated_trials"][0]["eligibility"],
            "eligible",
        )
        self.assertEqual(final["simulated_patient_answers"][0]["question_id"], "SYN-TEST-ANSWER-001-Q01")
        self.assertEqual(final["recommended_trials"][0]["trial_id"], "NCTTEST001")

    def test_agent_workspace_builder_excludes_hidden_labels_and_runs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir) / "agent-workspace"
            subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "build_agent_eval_workspace.py"),
                    "--output-dir",
                    str(workspace),
                    "--max-patients",
                    "2",
                ],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "assert_agent_workspace_clean.py"),
                    str(workspace),
                ],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                [
                    sys.executable,
                    "scripts/run_e2e_orchestration_v2.py",
                    "--max-patients",
                    "1",
                ],
                cwd=workspace,
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertFalse((workspace / "artifacts" / "gpt-e2e-teacher-labeling").exists())
            self.assertFalse((workspace / "src" / "health_agent" / "hidden_eval.py").exists())

    def test_agent_workspace_cleaner_rejects_upstage_key(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir) / "agent-workspace"
            workspace.mkdir()
            (workspace / ".env").write_text(
                "UPSTAGE_API_KEY=up_" + "A" * 24 + "\n",
                encoding="utf-8",
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "assert_agent_workspace_clean.py"),
                    str(workspace),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1)
            self.assertIn("possible secret", completed.stderr)


if __name__ == "__main__":
    unittest.main()
