from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from health_agent.clinicaltrials import normalize_study
from health_agent.competition import build_competition_predictions
from health_agent.data import load_patients, load_trials, write_jsonl
from health_agent.models import Trial
from health_agent.synthetic import generate_synthetic_patients


class CompetitionPipelineTests(unittest.TestCase):
    def test_normalizes_clinicaltrials_v2_study(self) -> None:
        study = {
            "protocolSection": {
                "identificationModule": {"nctId": "NCT123", "briefTitle": "EGFR NSCLC trial"},
                "descriptionModule": {"briefSummary": "Advanced EGFR-mutated NSCLC."},
                "statusModule": {"overallStatus": "RECRUITING"},
                "conditionsModule": {"conditions": ["Non-Small Cell Lung Cancer"]},
                "designModule": {"phases": ["PHASE2"], "enrollmentInfo": {"count": 40}},
                "armsInterventionsModule": {"interventions": [{"name": "osimertinib"}]},
                "eligibilityModule": {
                    "minimumAge": "18 Years",
                    "maximumAge": "80 Years",
                    "sex": "ALL",
                    "eligibilityCriteria": """
                    Inclusion Criteria:
                    Stage IV non-small cell lung cancer.
                    EGFR exon 19 deletion or L858R mutation.
                    ECOG performance status 0 to 2.
                    Exclusion Criteria:
                    Untreated brain metastases.
                    Active interstitial lung disease.
                    """,
                },
            }
        }
        trial = normalize_study(study)
        self.assertEqual(trial["trial_id"], "NCT123")
        self.assertEqual(trial["min_age"], 18)
        self.assertIn("EGFR", trial["required_biomarkers"])
        self.assertIn("IV", trial["allowed_stages"])
        self.assertIn("untreated_brain_metastases", trial["excluded_flags"])
        self.assertIn("stage", trial["required_patient_fields"])
        self.assertIn("ecog", trial["required_patient_fields"])

    def test_general_trial_does_not_require_oncology_fields(self) -> None:
        study = {
            "protocolSection": {
                "identificationModule": {"nctId": "NCT456", "briefTitle": "Migraine trial"},
                "descriptionModule": {"briefSummary": "Migraine prevention."},
                "statusModule": {"overallStatus": "RECRUITING"},
                "conditionsModule": {"conditions": ["Migraine With Aura"]},
                "designModule": {"phases": ["PHASE2"]},
                "armsInterventionsModule": {"interventions": [{"name": "drug"}]},
                "eligibilityModule": {
                    "minimumAge": "18 Years",
                    "sex": "ALL",
                    "eligibilityCriteria": """
                    Inclusion Criteria:
                    Diagnosis of migraine with aura.
                    Exclusion Criteria:
                    Significant uncontrolled cardiac disease.
                    """,
                },
            }
        }
        trial = normalize_study(study)
        self.assertEqual(trial["required_patient_fields"], ["diagnosis"])

    def test_jsonl_loader_supports_processed_records(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "patients.jsonl"
            write_jsonl(
                path,
                [
                    {
                        "patient_id": "P1",
                        "age": 50,
                        "sex": "female",
                        "diagnosis": "melanoma",
                        "stage": "IV",
                        "ecog": 1,
                        "clinical_note": "Synthetic note",
                    }
                ],
            )
            patients = load_patients(path)
        self.assertEqual(patients[0].patient_id, "P1")
        self.assertEqual(patients[0].clinical_note, "Synthetic note")

    def test_synthetic_generator_preserves_target_trial_id(self) -> None:
        trial = Trial(
            trial_id="T1",
            title="BRAF melanoma",
            phase="Phase 2",
            conditions=["melanoma"],
            interventions=["braf inhibitor"],
            min_age=18,
            max_age=None,
            sex="all",
            allowed_stages=["IV"],
            max_ecog=1,
            required_biomarkers={"BRAF": "V600E"},
            required_prior_treatments=[],
            excluded_flags=["active_autoimmune_disease"],
            required_patient_fields=["diagnosis", "stage", "ecog", "biomarkers"],
        )
        records = generate_synthetic_patients([trial], count=4, seed=1)
        self.assertEqual(len(records), 4)
        self.assertTrue(all(record["target_trial_id"] == "T1" for record in records))
        self.assertTrue(all(record["clinical_note"] for record in records))

    def test_synthetic_generator_does_not_make_non_oncology_metastatic(self) -> None:
        trial = Trial(
            trial_id="T2",
            title="Acute pancreatitis trial",
            phase="Phase 2",
            conditions=["Acute Pancreatitis"],
            interventions=["supportive care"],
            min_age=18,
            max_age=None,
            sex="all",
            allowed_stages=[],
            max_ecog=None,
            required_biomarkers={},
            required_prior_treatments=[],
            excluded_flags=[],
            required_patient_fields=["diagnosis"],
        )
        records = generate_synthetic_patients([trial], count=6, seed=1)
        self.assertEqual(records[0]["diagnosis"], "acute pancreatitis")
        self.assertEqual(records[0]["generator_version"], "health-agent-synthetic-v2")
        self.assertEqual(
            {record["scenario"] for record in records},
            {"age_conflict", "clear_candidate", "missing_age", "wrong_condition"},
        )
        records_by_scenario = {record["scenario"]: record for record in records}
        self.assertIsNone(records_by_scenario["missing_age"]["age"])
        self.assertEqual(records_by_scenario["age_conflict"]["age"], 17)
        self.assertTrue(all(record["stage"] is None for record in records))
        self.assertTrue(all(record["ecog"] is None for record in records))
        self.assertTrue(records[0]["clinical_note"].startswith("Clinical referral note"))
        self.assertNotIn("Tumor board", records[0]["clinical_note"])
        self.assertNotIn("Molecular testing", records[0]["clinical_note"])

    def test_competition_predictions_use_required_label_sets(self) -> None:
        patients = load_patients(ROOT / "data" / "raw" / "oncology-synthetic-patients.json")
        trials = load_trials(ROOT / "data" / "raw" / "sample-trials.json")
        report = build_competition_predictions(
            patients=patients[:1],
            trials=trials,
            top_k=2,
            disclaimer="Synthetic testing only.",
        )
        self.assertEqual(report["schema_version"], "health-agent-competition-v1")
        recommendation = report["patients"][0]["recommendations"][0]
        self.assertIn(recommendation["eligibility"], {"eligible", "ineligible", "uncertain"})
        statuses = {
            item["status"]
            for item in recommendation["criterion_results"]
        }
        self.assertTrue(statuses)
        self.assertLessEqual(
            statuses,
            {"satisfied", "violated", "unknown", "not_applicable"},
        )
        self.assertIn("follow_up_questions", recommendation)


if __name__ == "__main__":
    unittest.main()
