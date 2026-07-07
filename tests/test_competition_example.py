from __future__ import annotations

import json
import unittest
from pathlib import Path

import sys


SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from health_agent.data import load_patients


ROOT = Path(__file__).resolve().parents[1]


class CompetitionExampleInputTests(unittest.TestCase):
    def test_official_synthetic_patient_topics_are_versioned(self) -> None:
        path = ROOT / "data" / "raw" / "synthetic-patients.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertIn("topics", payload)
        self.assertEqual(len(payload["topics"]), 10)
        self.assertEqual(payload["topics"][0]["num"], "S001")
        self.assertIn("severe epigastric pain", payload["topics"][0]["title"])

    def test_official_topics_load_as_patient_notes(self) -> None:
        patients = load_patients(ROOT / "data" / "raw" / "synthetic-patients.json")
        self.assertEqual(len(patients), 10)
        self.assertEqual(patients[0].patient_id, "S001")
        self.assertEqual(patients[0].age, 54)
        self.assertEqual(patients[0].sex, "male")
        self.assertEqual(patients[0].diagnosis, "acute pancreatitis")
        self.assertEqual(patients[6].age, 0)
        self.assertIsNone(patients[6].sex)


if __name__ == "__main__":
    unittest.main()
