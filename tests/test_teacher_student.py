from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from health_agent.data import load_patients, load_trials
from health_agent.teacher_student import (
    build_target_pairs,
    compare_teacher_student,
    label_with_deterministic_baseline,
)


class TeacherStudentEvalTests(unittest.TestCase):
    def test_builds_patient_target_trial_pairs(self) -> None:
        patients = load_patients(ROOT / "data" / "processed" / "synthetic_patients.jsonl")
        trials = load_trials(ROOT / "data" / "processed" / "trials.jsonl")
        pairs = build_target_pairs(patients=patients, trials=trials, patient_count=5)
        self.assertEqual(len(pairs), 5)
        self.assertIn("pair_id", pairs[0])
        self.assertIn("patient_note", pairs[0])
        self.assertIn("criteria", pairs[0])
        self.assertGreaterEqual(len(pairs[0]["criteria"]), 1)

    def test_compares_teacher_and_student_labels(self) -> None:
        patients = load_patients(ROOT / "data" / "processed" / "synthetic_patients.jsonl")
        trials = load_trials(ROOT / "data" / "processed" / "trials.jsonl")
        pairs = build_target_pairs(patients=patients, trials=trials, patient_count=3)
        labels = label_with_deterministic_baseline(pairs)
        self.assertEqual(
            {item["criterion_id"] for item in labels[0]["criterion_results"]},
            {item["criterion_id"] for item in pairs[0]["criteria"]},
        )
        comparison = compare_teacher_student(
            pairs=pairs,
            teacher_labels=labels,
            student_labels=labels,
        )
        self.assertEqual(comparison["summary"]["pair_count"], 3)
        self.assertEqual(comparison["summary"]["eligibility_agreement"], 1.0)
        self.assertGreater(comparison["summary"]["criterion_compared"], 0)
        self.assertEqual(comparison["summary"]["criterion_status_agreement"], 1.0)


if __name__ == "__main__":
    unittest.main()
