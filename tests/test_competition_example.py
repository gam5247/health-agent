from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CompetitionExampleInputTests(unittest.TestCase):
    def test_official_synthetic_patient_topics_are_versioned(self) -> None:
        path = ROOT / "data" / "raw" / "synthetic-patients.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertIn("topics", payload)
        self.assertEqual(len(payload["topics"]), 10)
        self.assertEqual(payload["topics"][0]["num"], "S001")
        self.assertIn("severe epigastric pain", payload["topics"][0]["title"])


if __name__ == "__main__":
    unittest.main()

