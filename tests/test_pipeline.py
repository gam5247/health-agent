from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from health_agent.data import load_patients, load_trials
from health_agent.pipeline import run_recommendations


class HealthAgentPipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.patients_path = ROOT / "data" / "raw" / "synthetic-patients.json"
        self.trials_path = ROOT / "data" / "raw" / "sample-trials.json"

    def test_loads_synthetic_patients(self) -> None:
        patients = load_patients(self.patients_path)
        self.assertEqual(len(patients), 10)
        self.assertEqual(patients[0].patient_id, "SYN-001")

    def test_loads_sample_trials(self) -> None:
        trials = load_trials(self.trials_path)
        self.assertEqual(len(trials), 5)
        self.assertEqual(trials[0].trial_id, "NCT-SAMPLE-001")

    def test_egfr_patient_gets_nsclc_trial(self) -> None:
        result = run_recommendations(
            patients_path=self.patients_path,
            trials_path=self.trials_path,
            limit=1,
            max_recommendations=1,
        )
        top = result["SYN-001"][0]
        self.assertEqual(top["trial_id"], "NCT-SAMPLE-001")
        self.assertEqual(top["decision"], "recommend")
        self.assertGreaterEqual(top["score"], 0.8)

    def test_missing_biomarker_generates_questions(self) -> None:
        result = run_recommendations(
            patients_path=self.patients_path,
            trials_path=self.trials_path,
            max_recommendations=3,
        )
        nsclc_recommendation = next(
            item for item in result["SYN-009"] if item["trial_id"] == "NCT-SAMPLE-001"
        )
        question_text = " ".join(nsclc_recommendation["questions"])
        self.assertIn("EGFR", question_text)
        self.assertIn("ECOG", question_text)


if __name__ == "__main__":
    unittest.main()
