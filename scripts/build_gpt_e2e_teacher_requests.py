from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from health_agent.data import load_patients, load_trials
from health_agent.orchestrator import patient_to_clinical_note
from health_agent.rag import build_rag_index, retrieve_trials
from health_agent.teacher_student import criteria_for_trial


SYSTEM_PROMPT = """You are a GPT teacher labeler creating end-to-end answer keys for a clinical-trial matching multi-agent workflow.

Use only the synthetic patient information and candidate trial information provided in the input file. Do not use outside medical knowledge to add unstated patient facts.
This is for software evaluation only, not medical advice.

For every patient, produce exactly one JSON object.
Return JSONL only. No markdown, no commentary.

Required workflow represented in each output object:
1. criteria_parser_agent: convert trial inclusion/exclusion criteria into structured rules.
2. patient_information_understanding_agent: extract the patient profile from the patient information string.
3. inference_matching_agent: judge criterion-level satisfaction for each candidate trial using currently known patient information.
4. question_generation_agent: generate follow-up questions for missing required facts.
5. interaction_simulation_agent: provide synthetic patient answers to the generated questions.
6. recommendation_agent: rank the candidate trials for the patient after applying the synthetic answers.
7. result_explanation_agent: explain final judgment and recommendations.

Allowed trial-level eligibility labels: eligible, ineligible, uncertain.
Allowed criterion status labels: satisfied, violated, unknown, not_applicable.

For exclusion criteria: satisfied means the exclusion is absent; violated means the exclusion is present.
If a required fact is missing, mark that criterion unknown, generate a question, then create a plausible synthetic answer. The final recommendation should reflect the answer.
Every candidate trial must appear exactly once in final_output.recommendations.
Every supplied criterion_id for a candidate trial must appear exactly once in initial and final criterion_results.
"""


OUTPUT_SCHEMA = {
    "patient_id": "same patient_id",
    "input": {
        "patient_information_string": "same supplied patient string",
        "candidate_trial_ids": ["trial ids in supplied order"],
    },
    "agent_trace": {
        "criteria_parser_agent": {
            "parsed_trials": [
                {
                    "trial_id": "trial id",
                    "structured_rules": [
                        {
                            "criterion_id": "same supplied criterion_id",
                            "criterion_type": "inclusion|exclusion",
                            "criterion": "short parsed criterion",
                            "required": True,
                        }
                    ],
                }
            ]
        },
        "patient_information_understanding_agent": {
            "extracted_profile": {
                "age": "number or null",
                "sex": "string or null",
                "diagnosis": "string or null",
                "stage": "string or null",
                "ecog": "number or null",
                "biomarkers": {},
                "prior_treatments": [],
                "flags": {},
            },
            "missing_or_unstated_fields": ["field names"],
        },
        "inference_matching_agent": {
            "initial_trial_judgments": [
                {
                    "trial_id": "trial id",
                    "eligibility": "eligible|ineligible|uncertain",
                    "criterion_results": [
                        {
                            "criterion_id": "same supplied criterion_id",
                            "status": "satisfied|violated|unknown|not_applicable",
                            "reason": "grounded reason",
                        }
                    ],
                    "rationale": "short reason",
                }
            ]
        },
        "question_generation_agent": {
            "questions": [
                {
                    "question_id": "patient_id__trial_id__Q01",
                    "patient_id": "patient id",
                    "trial_id": "trial id",
                    "criterion_id": "criterion id",
                    "question": "follow-up question",
                    "reason": "why this information is needed",
                }
            ]
        },
        "interaction_simulation_agent": {
            "simulated_patient_answers": [
                {
                    "question_id": "same question id",
                    "answer": "synthetic patient answer",
                    "profile_updates": {},
                }
            ]
        },
        "recommendation_agent": {
            "recommended_trial_order": ["trial ids ordered best to worst"],
            "ranked_recommendations": [
                {
                    "rank": 1,
                    "trial_id": "trial id",
                    "eligibility": "eligible|ineligible|uncertain",
                    "recommendation_score": 0.0,
                }
            ],
        },
        "result_explanation_agent": {
            "summary": "plain-language explanation",
            "medical_disclaimer": "software evaluation only, not medical advice",
        },
    },
    "final_output": {
        "patient_id": "same patient_id",
        "recommendations": [
            {
                "rank": 1,
                "trial_id": "trial id",
                "trial_title": "trial title",
                "eligibility": "eligible|ineligible|uncertain",
                "criterion_results": [
                    {
                        "criterion_id": "same supplied criterion_id",
                        "status": "satisfied|violated|unknown|not_applicable",
                        "reason": "grounded reason after simulated answers",
                    }
                ],
                "follow_up_questions": [],
                "simulated_patient_answers": [],
                "explanation": "why this final judgment and rank were assigned",
            }
        ],
        "recommended_trial_order": ["trial ids ordered best to worst"],
        "medical_disclaimer": "software evaluation only, not medical advice",
    },
}


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    patients = load_patients(args.patients)[: args.patient_count]
    trials = load_trials(args.trials)
    trials_by_id = {trial.trial_id: trial for trial in trials}
    index = build_rag_index(trials)
    records = []
    for patient_index, patient in enumerate(patients):
        note = patient.clinical_note or patient_to_clinical_note(patient, patient_index)
        candidates = []
        seen = set()
        if patient.target_trial_id and patient.target_trial_id in trials_by_id:
            trial = trials_by_id[patient.target_trial_id]
            candidates.append(candidate_payload(trial, retrieval_rank=1, retrieval_score=1.0))
            seen.add(trial.trial_id)
        for retrieved in retrieve_trials(index, note, args.candidate_count * 4):
            if retrieved.trial.trial_id in seen:
                continue
            candidates.append(
                candidate_payload(
                    retrieved.trial,
                    retrieval_rank=len(candidates) + 1,
                    retrieval_score=retrieved.score,
                )
            )
            seen.add(retrieved.trial.trial_id)
            if len(candidates) >= args.candidate_count:
                break
        records.append(
            {
                "patient_id": patient.patient_id,
                "patient_information_string": note,
                "synthetic_source_profile": {
                    key: value
                    for key, value in patient.__dict__.items()
                    if key != "clinical_note" and value not in (None, "", [], {})
                },
                "candidate_trials": candidates,
            }
        )

    all_input_path = args.output_dir / "gpt_e2e_teacher_input_100.json"
    all_input_path.write_text(
        json.dumps({"patients": records}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    prompt_paths = []
    for batch_index, start in enumerate(range(0, len(records), args.batch_size), start=1):
        batch = records[start : start + args.batch_size]
        request = build_request_markdown(
            batch_index=batch_index,
            batch=batch,
        )
        path = args.output_dir / "requests" / f"gpt_e2e_teacher_request_batch_{batch_index:02d}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(request, encoding="utf-8")
        prompt_paths.append(path)

    manifest = {
        "patient_count": len(records),
        "candidate_count": args.candidate_count,
        "batch_size": args.batch_size,
        "batch_count": len(prompt_paths),
        "input_json": str(all_input_path),
        "request_files": [str(path) for path in prompt_paths],
        "expected_response_format": "JSONL, one object per patient",
    }
    manifest_path = args.output_dir / "gpt_e2e_teacher_request_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


def candidate_payload(trial: Any, *, retrieval_rank: int, retrieval_score: float) -> dict[str, Any]:
    return {
        "trial_id": trial.trial_id,
        "title": trial.title,
        "source_url": trial.source_url or "",
        "retrieval_rank": retrieval_rank,
        "retrieval_score": round(float(retrieval_score), 3),
        "conditions": trial.conditions,
        "phase": trial.phase,
        "status": trial.status,
        "interventions": trial.interventions[:8],
        "known_structured_fields": {
            "min_age": trial.min_age,
            "max_age": trial.max_age,
            "sex": trial.sex,
            "allowed_stages": trial.allowed_stages,
            "max_ecog": trial.max_ecog,
            "required_biomarkers": trial.required_biomarkers,
            "required_prior_treatments": trial.required_prior_treatments,
            "excluded_flags": trial.excluded_flags,
        },
        "criteria_to_assess": criteria_for_trial(trial),
        "raw_criteria_excerpt": {
            "inclusion": trial.inclusion_criteria[:10],
            "exclusion": trial.exclusion_criteria[:10],
            "eligibility_criteria_excerpt": excerpt(trial.eligibility_criteria, 1800),
        },
    }


def build_request_markdown(*, batch_index: int, batch: list[dict[str, Any]]) -> str:
    return "\n".join(
        [
            "# GPT End-to-End Health-Agent Teacher Label Request",
            "",
            "Return JSONL only, one JSON object per patient. Do not wrap in markdown.",
            "",
            "## System Instructions",
            "",
            SYSTEM_PROMPT,
            "",
            "## Required Output Schema",
            "",
            "```json",
            json.dumps(OUTPUT_SCHEMA, ensure_ascii=False, indent=2),
            "```",
            "",
            "## Input Batch",
            "",
            json.dumps(
                {
                    "batch_id": f"gpt_e2e_teacher_batch_{batch_index:02d}",
                    "patients": batch,
                },
                ensure_ascii=False,
                indent=2,
            ),
            "",
        ]
    )


def excerpt(value: str | None, max_chars: int) -> str:
    return " ".join(str(value or "").split())[:max_chars]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build GPT end-to-end teacher-label request batches."
    )
    parser.add_argument(
        "--patients",
        type=Path,
        default=ROOT / "data" / "processed" / "synthetic_patients.jsonl",
    )
    parser.add_argument(
        "--trials",
        type=Path,
        default=ROOT / "data" / "processed" / "trials.jsonl",
    )
    parser.add_argument("--patient-count", type=int, default=100)
    parser.add_argument("--candidate-count", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=5)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "artifacts" / "gpt-e2e-teacher-labeling",
    )
    return parser.parse_args()


if __name__ == "__main__":
    main()
