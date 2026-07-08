from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


AGENT_KEYS = [
    "criteria_parser_agent",
    "patient_information_understanding_agent",
    "initial_matching_agent",
    "question_generation_agent",
    "interaction_simulation_agent",
    "final_matching_agent",
    "recommendation_agent",
    "result_explanation_agent",
]

ELIGIBILITY_LABELS = {"eligible", "ineligible", "uncertain"}
CRITERION_STATUSES = {"satisfied", "violated", "unknown", "not_applicable"}
DISCLAIMER = "Synthetic software-evaluation output only. Not medical advice and not a real clinical eligibility decision."


def main() -> None:
    args = parse_args()
    expected_payload = json.loads(args.input_100.read_text(encoding="utf-8"))
    expected_by_id = {
        patient["patient_id"]: patient
        for patient in expected_payload["patients"]
    }
    draft_records = read_jsonl(args.draft_jsonl)
    records = []
    validation_errors: list[str] = []
    warning_counts: Counter[str] = Counter()

    for draft in draft_records:
        patient_id = draft["patient_id"]
        expected = expected_by_id[patient_id]
        record, warnings = build_v2_record(draft, expected)
        records.append(record)
        warning_counts.update(warnings)
        validation_errors.extend(validate_record(record, expected))

    summary = build_summary(records, validation_errors, warning_counts)
    args.output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.output_jsonl, records)
    write_text_lf(
        args.output_json,
        json.dumps(
            {
                "source": {
                    "draft_jsonl": str(args.draft_jsonl),
                    "input_100": str(args.input_100),
                },
                "patient_count": len(records),
                "patients": records,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
    )
    write_text_lf(args.summary, json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    if validation_errors:
        raise SystemExit(1)


def build_v2_record(draft: dict[str, Any], expected: dict[str, Any]) -> tuple[dict[str, Any], Counter[str]]:
    warnings: Counter[str] = Counter()
    patient_id = draft["patient_id"]
    candidate_trials = expected.get("candidate_trials", [])
    expected_trial_ids = [trial["trial_id"] for trial in candidate_trials]
    expected_criteria = criteria_by_trial(expected)
    agent_trace = draft.get("agent_trace", {})
    if not isinstance(agent_trace, dict):
        agent_trace = {}

    final_rows = normalize_final_rows(draft, expected, warnings)
    initial_rows = normalize_initial_rows(agent_trace, final_rows, expected, warnings)
    questions = collect_questions(
        patient_id=patient_id,
        agent_trace=agent_trace,
        final_rows=final_rows,
        initial_rows=initial_rows,
        expected=expected,
        warnings=warnings,
    )
    answers = collect_answers(patient_id, agent_trace, questions, final_rows, warnings)
    questions = ensure_questions_for_answers(patient_id, questions, answers, warnings)
    question_ids_by_trial = related_question_ids_by_trial(questions, expected_trial_ids)
    explanation_by_trial = result_explanations(agent_trace)
    patient_summary = patient_level_summary(agent_trace, final_rows)

    final_evaluated = []
    initial_evaluated = []
    for trial_id in expected_trial_ids:
        final_row = final_rows[trial_id]
        initial_row = initial_rows[trial_id]
        final_explanation = (
            final_row.get("explanation")
            or explanation_by_trial.get(trial_id)
            or derived_trial_explanation(final_row)
        )
        if not final_row.get("explanation") and not explanation_by_trial.get(trial_id):
            warnings["derived_final_explanation"] += 1
        final_item = {
            **trial_identity(trial_id, expected),
            "eligibility": clean_eligibility(final_row.get("eligibility")),
            "criterion_results": final_row["criterion_results"],
            "related_question_ids": question_ids_by_trial.get(trial_id, []),
            "explanation": final_explanation,
            "source_rank": final_row.get("rank"),
        }
        initial_item = {
            **trial_identity(trial_id, expected),
            "eligibility": clean_eligibility(initial_row.get("eligibility")),
            "criterion_results": initial_row["criterion_results"],
            "related_question_ids": question_ids_by_trial.get(trial_id, []),
            "explanation": initial_row.get("explanation") or derived_trial_explanation(initial_row),
            "source": initial_row.get("source", "agent_trace"),
        }
        final_evaluated.append(final_item)
        initial_evaluated.append(initial_item)

    recommended = []
    uncertain = []
    excluded = []
    for item in sorted(final_evaluated, key=lambda row: row.get("source_rank") or 999):
        if item["eligibility"] == "eligible":
            recommended.append(
                {
                    "rank": len(recommended) + 1,
                    "trial_id": item["trial_id"],
                    "trial_title": item["trial_title"],
                    "eligibility": item["eligibility"],
                    "recommendation_reason": item["explanation"],
                    "supporting_criterion_ids": [
                        row["criterion_id"]
                        for row in item["criterion_results"]
                        if row["status"] in {"satisfied", "not_applicable"}
                    ],
                    "related_question_ids": item["related_question_ids"],
                }
            )
        elif item["eligibility"] == "uncertain":
            uncertain.append(
                {
                    "trial_id": item["trial_id"],
                    "trial_title": item["trial_title"],
                    "eligibility": item["eligibility"],
                    "reason": item["explanation"],
                    "unknown_criterion_ids": [
                        row["criterion_id"]
                        for row in item["criterion_results"]
                        if row["status"] == "unknown"
                    ],
                    "related_question_ids": item["related_question_ids"],
                }
            )
        else:
            violated = [
                row
                for row in item["criterion_results"]
                if row["status"] == "violated"
            ]
            excluded.append(
                {
                    "trial_id": item["trial_id"],
                    "trial_title": item["trial_title"],
                    "eligibility": item["eligibility"],
                    "exclusion_reason": item["explanation"],
                    "violated_criteria": violated,
                    "related_question_ids": item["related_question_ids"],
                }
            )

    v2_agent_trace = {
        "criteria_parser_agent": build_structured_criteria_parser(expected),
        "patient_information_understanding_agent": agent_trace.get(
            "patient_information_understanding_agent",
            {},
        ),
        "initial_matching_agent": {
            "evaluated_trials": initial_evaluated,
            "source_agent": "inference_matching_agent",
        },
        "question_generation_agent": {
            "follow_up_questions": questions,
        },
        "interaction_simulation_agent": {
            "simulated_patient_answers": answers,
        },
        "final_matching_agent": {
            "evaluated_trials": final_evaluated,
            "source": "normalized GPT final judgments plus trace-level repairs",
        },
        "recommendation_agent": {
            "recommended_trials": recommended,
            "uncertain_but_actionable_trials": uncertain,
            "excluded_trials": excluded,
        },
        "result_explanation_agent": {
            "patient_level_summary": patient_summary,
            "trial_explanations": [
                {
                    "trial_id": item["trial_id"],
                    "explanation": item["explanation"],
                }
                for item in final_evaluated
            ],
        },
    }

    record = {
        "patient_id": patient_id,
        "patient_information_string": draft.get("patient_information_string")
        or draft.get("input", {}).get("patient_information_string")
        or expected["patient_information_string"],
        "candidate_trials": candidate_trial_payloads(expected),
        "agent_trace": v2_agent_trace,
        "final_output": {
            "initial_assessment": {
                "evaluated_trials": initial_evaluated,
            },
            "follow_up_questions": questions,
            "simulated_patient_answers": answers,
            "final_assessment_after_answers": {
                "evaluated_trials": final_evaluated,
            },
            "recommended_trials": recommended,
            "uncertain_but_actionable_trials": uncertain,
            "excluded_trials": excluded,
            "patient_level_summary": patient_summary,
            "medical_disclaimer": draft.get("final_output", {}).get("medical_disclaimer")
            or DISCLAIMER,
        },
        "source_draft": {
            "draft_schema": "gpt_e2e_teacher_labels_100",
            "normalization_notes": [
                "Original draft final_output.recommendations represented all evaluated candidate trials.",
                "v2 separates evaluated_trials from recommended, uncertain, and excluded trial lists.",
            ],
        },
        "quality_flags": sorted(warnings.elements()),
    }
    # Keep criterion coverage deterministic even when GPT order varied.
    for row in record["final_output"]["final_assessment_after_answers"]["evaluated_trials"]:
        row["criterion_results"] = ordered_criteria(row["criterion_results"], expected_criteria[row["trial_id"]])
    for row in record["final_output"]["initial_assessment"]["evaluated_trials"]:
        row["criterion_results"] = ordered_criteria(row["criterion_results"], expected_criteria[row["trial_id"]])
    return record, warnings


def normalize_final_rows(
    draft: dict[str, Any],
    expected: dict[str, Any],
    warnings: Counter[str],
) -> dict[str, dict[str, Any]]:
    rows = {}
    final_output = draft.get("final_output", {})
    recommendations = final_output.get("recommendations", []) if isinstance(final_output, dict) else []
    fallback_by_trial = {
        trial["trial_id"]: trial
        for trial in expected.get("candidate_trials", [])
    }
    for index, row in enumerate(recommendations, start=1):
        if not isinstance(row, dict):
            continue
        trial_id = str(row.get("trial_id", ""))
        if not trial_id:
            continue
        rows[trial_id] = {
            "trial_id": trial_id,
            "rank": int(row.get("rank") or index),
            "eligibility": clean_eligibility(row.get("eligibility")),
            "criterion_results": normalize_criterion_results(row.get("criterion_results")),
            "follow_up_questions": as_string_list(row.get("follow_up_questions")),
            "simulated_patient_answers": as_string_list(row.get("simulated_patient_answers")),
            "explanation": str(
                row.get("explanation")
                or row.get("reason")
                or row.get("final_explanation")
                or row.get("recommendation_reason")
                or row.get("summary_reason")
                or ""
            ),
        }
    for trial_id, trial in fallback_by_trial.items():
        if trial_id not in rows:
            warnings["missing_final_trial_filled_unknown"] += 1
            rows[trial_id] = {
                "trial_id": trial_id,
                "rank": len(rows) + 1,
                "eligibility": "uncertain",
                "criterion_results": unknown_criteria(trial),
                "follow_up_questions": [],
                "simulated_patient_answers": [],
                "explanation": "No final GPT trial judgment was available in the draft normalization.",
            }
        rows[trial_id]["criterion_results"] = fill_missing_criteria(
            rows[trial_id]["criterion_results"],
            trial,
            warnings,
            context=f"{trial_id}:final",
        )
    return rows


def normalize_initial_rows(
    agent_trace: dict[str, Any],
    final_rows: dict[str, dict[str, Any]],
    expected: dict[str, Any],
    warnings: Counter[str],
) -> dict[str, dict[str, Any]]:
    inference = agent_trace.get("inference_matching_agent")
    raw_rows = first_list(
        inference,
        [
            "initial_trial_assessments",
            "initial_trial_judgments",
            "initial_output",
            "initial_outputs",
            "initial_assessments",
            "trial_assessments",
        ],
    )
    rows: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(raw_rows, start=1):
        if not isinstance(row, dict):
            continue
        trial_id = str(row.get("trial_id", ""))
        if not trial_id:
            continue
        rows[trial_id] = {
            "trial_id": trial_id,
            "rank": int(row.get("rank") or index),
            "eligibility": clean_eligibility(row.get("eligibility") or row.get("label")),
            "criterion_results": normalize_criterion_results(
                row.get("criterion_results")
                or row.get("criterion_level_judgments")
                or row.get("criteria")
                or row.get("criterion_statuses")
                or row.get("criterion_assessments")
            ),
            "explanation": str(
                row.get("explanation")
                or row.get("reason")
                or row.get("rationale")
                or row.get("summary_reason")
                or ""
            ),
            "source": "agent_trace.inference_matching_agent",
        }
    for trial in expected.get("candidate_trials", []):
        trial_id = trial["trial_id"]
        if trial_id not in rows:
            warnings["initial_assessment_fallback_from_final"] += 1
            final_row = final_rows[trial_id]
            rows[trial_id] = {
                "trial_id": trial_id,
                "rank": final_row.get("rank"),
                "eligibility": final_row.get("eligibility", "uncertain"),
                "criterion_results": final_row["criterion_results"],
                "explanation": final_row.get("explanation")
                or "Initial GPT assessment was not separately available; final draft assessment was used as a fallback.",
                "source": "final_draft_fallback",
            }
        rows[trial_id]["criterion_results"] = fill_missing_criteria(
            rows[trial_id]["criterion_results"],
            trial,
            warnings,
            context=f"{trial_id}:initial",
        )
    return rows


def collect_questions(
    *,
    patient_id: str,
    agent_trace: dict[str, Any],
    final_rows: dict[str, dict[str, Any]],
    initial_rows: dict[str, dict[str, Any]],
    expected: dict[str, Any],
    warnings: Counter[str],
) -> list[dict[str, Any]]:
    rows: list[Any] = []
    q_agent = agent_trace.get("question_generation_agent")
    trace_rows = first_list(q_agent, ["follow_up_questions", "questions", "list"])
    rows.extend(trace_rows)
    if not trace_rows:
        for trial_id, row in final_rows.items():
            for question in row.get("follow_up_questions", []):
                rows.append({"question": question, "trial_id": trial_id, "source": "final_trial"})
    by_text: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(rows, start=1):
        if isinstance(item, str):
            payload = {"question": item}
        elif isinstance(item, dict):
            payload = item
        else:
            continue
        question = str(
            payload.get("question")
            or payload.get("prompt")
            or payload.get("text")
            or ""
        ).strip()
        if not question:
            continue
        question_id = str(payload.get("question_id") or f"{patient_id}-Q{index:02d}")
        needed_for = normalize_needed_for(
            payload,
            question,
            initial_rows,
            expected,
        )
        key = normalize_text(question)
        by_text[key] = {
            "question_id": question_id,
            "question": question,
            "needed_for": needed_for,
            "reason": str(payload.get("reason") or payload.get("why_needed") or ""),
            "source": str(payload.get("source") or "agent_trace"),
        }
    if not by_text:
        warnings["no_follow_up_questions_available"] += 1
    return list(by_text.values())


def collect_answers(
    patient_id: str,
    agent_trace: dict[str, Any],
    questions: list[dict[str, Any]],
    final_rows: dict[str, dict[str, Any]],
    warnings: Counter[str],
) -> list[dict[str, str]]:
    rows: list[Any] = []
    sim_agent = agent_trace.get("interaction_simulation_agent")
    trace_rows = first_list(
        sim_agent,
        [
            "simulated_patient_answers",
            "synthetic_patient_answers",
            "synthesized_patient_answers",
            "simulated_answers",
            "synthetic_answers",
            "answers",
            "list",
        ],
    )
    rows.extend(trace_rows)
    if not trace_rows:
        for trial_id, row in final_rows.items():
            for index, answer in enumerate(row.get("simulated_patient_answers", []), start=1):
                rows.append(
                    {
                        "question_id": related_question_id_for_trial(questions, trial_id, index),
                        "answer": answer,
                        "source": "final_trial",
                    }
                )

    question_ids = [q["question_id"] for q in questions]
    normalized = []
    for index, item in enumerate(rows, start=1):
        if isinstance(item, str):
            payload = {"answer": item}
        elif isinstance(item, dict):
            payload = item
        else:
            continue
        answer = str(payload.get("answer") or payload.get("response") or payload.get("text") or "").strip()
        if not answer:
            continue
        question_id = str(payload.get("question_id") or "")
        if not question_id:
            question_id = question_ids[index - 1] if index - 1 < len(question_ids) else f"{patient_id}-Q{index:02d}"
        normalized.append(
            {
                "question_id": question_id,
                "answer": answer,
                "source": str(payload.get("source") or "agent_trace"),
            }
        )
    if questions and not normalized:
        warnings["questions_without_answers"] += 1
    return dedupe_answers(normalized)


def ensure_questions_for_answers(
    patient_id: str,
    questions: list[dict[str, Any]],
    answers: list[dict[str, str]],
    warnings: Counter[str],
) -> list[dict[str, Any]]:
    by_id = {question["question_id"]: question for question in questions}
    for answer in answers:
        question_id = answer.get("question_id", "")
        if not question_id or question_id in by_id:
            continue
        warnings["answer_only_question_placeholder_added"] += 1
        by_id[question_id] = {
            "question_id": question_id,
            "question": "Question text was not preserved in the draft normalization; see the linked simulated answer.",
            "needed_for": [],
            "reason": "Added during v2 normalization to preserve a simulated answer that referenced this question_id.",
            "source": "answer_only_repair",
        }
    return sorted(
        by_id.values(),
        key=lambda item: question_sort_key(patient_id, item.get("question_id", "")),
    )


def question_sort_key(patient_id: str, question_id: str) -> tuple[int, str]:
    match = re.search(r"Q(\d+)$", question_id)
    if question_id.startswith(patient_id) and match:
        return (int(match.group(1)), question_id)
    return (9999, question_id)


def normalize_needed_for(
    payload: dict[str, Any],
    question: str,
    initial_rows: dict[str, dict[str, Any]],
    expected: dict[str, Any],
) -> list[dict[str, str]]:
    explicit = payload.get("needed_for") or payload.get("needed_for_criteria") or []
    normalized = []
    if isinstance(explicit, str):
        explicit = [explicit]
    if isinstance(explicit, list):
        for item in explicit:
            if isinstance(item, dict):
                trial_id = str(item.get("trial_id", ""))
                criterion_id = str(item.get("criterion_id", ""))
            else:
                text = str(item)
                trial_id = first_trial_id(text)
                criterion_id = first_criterion_id(text)
            if trial_id or criterion_id:
                normalized.append(
                    {
                        "trial_id": trial_id,
                        "criterion_id": criterion_id,
                    }
                )
    if payload.get("trial_id") or payload.get("criterion_id"):
        normalized.append(
            {
                "trial_id": str(payload.get("trial_id", "")),
                "criterion_id": str(payload.get("criterion_id", "")),
            }
        )
    if normalized:
        return dedupe_needed_for(normalized, expected)

    fact_key = str(payload.get("fact_key") or "")
    hints = criterion_field_hints(f"{fact_key} {question}")
    if hints:
        hinted = []
        for trial_id, row in initial_rows.items():
            for criterion in row.get("criterion_results", []):
                if criterion.get("status") != "unknown":
                    continue
                field = criterion.get("criterion_id", "").lower().replace("_", "-")
                if any(hint in field for hint in hints):
                    hinted.append(
                        {
                            "trial_id": trial_id,
                            "criterion_id": criterion.get("criterion_id", ""),
                        }
                    )
        if hinted:
            return dedupe_needed_for(hinted, expected)
        expected_hinted = expected_criteria_matching_hints(hints, expected)
        if expected_hinted:
            return dedupe_needed_for(expected_hinted, expected)

    title_matches = matching_trials_by_question(question, expected)
    if title_matches:
        return [
            {"trial_id": trial_id, "criterion_id": ""}
            for trial_id in title_matches
        ]

    question_tokens = set(tokenize(f"{fact_key} {question}"))
    unknowns = []
    for trial_id, row in initial_rows.items():
        for criterion in row.get("criterion_results", []):
            criterion_id = criterion.get("criterion_id", "")
            reason = criterion.get("reason", "")
            if criterion.get("status") != "unknown":
                continue
            criterion_tokens = set(tokenize(f"{criterion_id} {reason}"))
            if question_tokens and criterion_tokens and question_tokens & criterion_tokens:
                unknowns.append({"trial_id": trial_id, "criterion_id": criterion_id})
    if unknowns:
        return dedupe_needed_for(unknowns, expected)

    return []


def expected_criteria_matching_hints(hints: list[str], expected: dict[str, Any]) -> list[dict[str, str]]:
    matches = []
    for trial in expected.get("candidate_trials", []):
        for criterion in trial.get("criteria_to_assess", []):
            criterion_id = str(criterion.get("criterion_id", ""))
            haystack = normalize_text(
                f"{criterion_id} {criterion.get('criterion', '')} {criterion.get('structured_value', '')}"
            ).replace("_", "-")
            if any(hint in haystack for hint in hints):
                matches.append(
                    {
                        "trial_id": trial["trial_id"],
                        "criterion_id": criterion_id,
                    }
                )
    return matches


def criterion_field_hints(text: str) -> list[str]:
    normalized = normalize_text(text).replace("_", " ")
    patterns = [
        ("ecog", ["ecog"]),
        ("performance status", ["ecog"]),
        ("platinum", ["prior-platinum-chemotherapy"]),
        ("autoimmune", ["active-autoimmune-disease"]),
        ("interstitial lung", ["active-interstitial-lung-disease"]),
        ("cardiac", ["uncontrolled-cardiac-disease"]),
        ("infection", ["active-uncontrolled-infection"]),
        ("organ transplant", ["organ-transplant"]),
        ("transplant", ["organ-transplant"]),
        ("stage", ["stage"]),
        ("biomarker", ["biomarker"]),
        ("molecular", ["biomarker"]),
        ("prior systemic", ["prior-treatment", "prior-systemic-therapy"]),
    ]
    hints: list[str] = []
    for phrase, values in patterns:
        if phrase in normalized:
            hints.extend(values)
    return sorted(set(hints))


def matching_trials_by_question(question: str, expected: dict[str, Any]) -> list[str]:
    generic = {
        "cancer",
        "patient",
        "patients",
        "trial",
        "study",
        "testing",
        "condition",
        "criteria",
        "participation",
        "advanced",
        "metastatic",
        "solid",
        "tumor",
        "tumors",
        "care",
    }
    question_tokens = set(tokenize(question)) - generic
    special_aliases = [
        {"psychotherapy", "existential", "distress", "orphys"},
        {"genetic", "inherited"},
        {"rural"},
        {"urothelial", "bladder"},
        {"lymphoma", "cell"},
        {"fibrosis", "pulmonary"},
    ]
    matches: list[str] = []
    trial_tokens: dict[str, set[str]] = {}
    for trial in expected.get("candidate_trials", []):
        trial_tokens[trial["trial_id"]] = (
            set(tokenize(trial.get("title", "")))
            | set(tokenize(" ".join(trial.get("conditions", []))))
        ) - generic

    for alias_tokens in special_aliases:
        if question_tokens & alias_tokens:
            special_matches = [
                trial_id
                for trial_id, tokens in trial_tokens.items()
                if tokens & alias_tokens
            ]
            if special_matches:
                return sorted(special_matches)

    for trial in expected.get("candidate_trials", []):
        if trial["trial_id"] in question:
            matches.append(trial["trial_id"])
            continue
        combined = trial_tokens[trial["trial_id"]]
        overlap = question_tokens & combined
        if len(overlap) >= 2:
            matches.append(trial["trial_id"])
    return sorted(set(matches))


def related_question_ids_by_trial(
    questions: list[dict[str, Any]],
    trial_ids: list[str],
) -> dict[str, list[str]]:
    result: dict[str, list[str]] = defaultdict(list)
    for question in questions:
        qid = question["question_id"]
        needed_for = question.get("needed_for") or []
        if not needed_for:
            continue
        for item in needed_for:
            trial_id = item.get("trial_id", "")
            if trial_id in trial_ids and qid not in result[trial_id]:
                result[trial_id].append(qid)
    return dict(result)


def related_question_id_for_trial(
    questions: list[dict[str, Any]],
    trial_id: str,
    index: int,
) -> str:
    related = [
        q["question_id"]
        for q in questions
        if any(item.get("trial_id") == trial_id for item in q.get("needed_for", []))
    ]
    if index - 1 < len(related):
        return related[index - 1]
    return related[0] if related else ""


def build_structured_criteria_parser(expected: dict[str, Any]) -> dict[str, Any]:
    parsed_trials = []
    for trial in expected.get("candidate_trials", []):
        parsed_criteria = []
        for criterion in trial.get("criteria_to_assess", []):
            parsed_criteria.append(
                {
                    "criterion_id": criterion["criterion_id"],
                    "type": criterion.get("criterion_type", ""),
                    "field": criterion_field(criterion),
                    "operator": criterion_operator(criterion),
                    "value": criterion.get("structured_value"),
                    "required": bool(criterion.get("required", True)),
                    "source_text": criterion.get("criterion", ""),
                }
            )
        parsed_trials.append(
            {
                "trial_id": trial["trial_id"],
                "trial_title": trial.get("title", ""),
                "parsed_criteria": parsed_criteria,
            }
        )
    return {
        "parsed_trials": parsed_trials,
        "source": "criteria_to_assess plus raw criteria metadata supplied to GPT",
    }


def candidate_trial_payloads(expected: dict[str, Any]) -> list[dict[str, Any]]:
    payloads = []
    for trial in expected.get("candidate_trials", []):
        payloads.append(
            {
                "trial_id": trial["trial_id"],
                "trial_title": trial.get("title", ""),
                "trial_source_url": trial.get("source_url", ""),
                "retrieval_rank": trial.get("retrieval_rank"),
                "retrieval_score": trial.get("retrieval_score"),
                "conditions": trial.get("conditions", []),
                "phase": trial.get("phase"),
                "status": trial.get("status"),
                "interventions": trial.get("interventions", []),
                "known_structured_fields": trial.get("known_structured_fields", {}),
                "criteria_to_assess": trial.get("criteria_to_assess", []),
                "raw_criteria_excerpt": trial.get("raw_criteria_excerpt", {}),
            }
        )
    return payloads


def result_explanations(agent_trace: dict[str, Any]) -> dict[str, str]:
    result_agent = agent_trace.get("result_explanation_agent")
    explanations = {}
    for row in first_list(result_agent, ["trial_explanations", "explanations"]):
        if not isinstance(row, dict):
            continue
        trial_id = str(row.get("trial_id", ""))
        explanation = str(
            row.get("explanation")
            or row.get("reason")
            or row.get("rationale")
            or row.get("summary")
            or ""
        )
        if trial_id and explanation:
            explanations[trial_id] = explanation
    if isinstance(result_agent, dict):
        raw = result_agent.get("explanations")
        if isinstance(raw, dict):
            for trial_id, payload in raw.items():
                if isinstance(payload, dict):
                    explanation = str(payload.get("explanation") or payload.get("reason") or "")
                else:
                    explanation = str(payload)
                if explanation:
                    explanations[str(trial_id)] = explanation
    return explanations


def patient_level_summary(agent_trace: dict[str, Any], final_rows: dict[str, dict[str, Any]]) -> str:
    result_agent = agent_trace.get("result_explanation_agent")
    if isinstance(result_agent, dict):
        for key in ["patient_level_summary", "summary"]:
            value = result_agent.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    eligible = [
        trial_id
        for trial_id, row in final_rows.items()
        if clean_eligibility(row.get("eligibility")) == "eligible"
    ]
    if eligible:
        return "Recommended eligible trial ids after final matching: " + ", ".join(eligible) + "."
    return "No eligible trial was identified after final matching."


def derived_trial_explanation(row: dict[str, Any]) -> str:
    eligibility = clean_eligibility(row.get("eligibility"))
    criteria = row.get("criterion_results", [])
    violated = [item for item in criteria if item.get("status") == "violated"]
    unknown = [item for item in criteria if item.get("status") == "unknown"]
    if eligibility == "eligible":
        return "Eligible because all normalized criterion judgments are satisfied or not applicable."
    if eligibility == "uncertain":
        if unknown:
            return "Uncertain because required information remains unknown: " + "; ".join(
                reason_fragment(item) for item in unknown[:3]
            )
        return "Uncertain based on the GPT final judgment; no unresolved criterion-level reason was preserved."
    if violated:
        return "Excluded because criterion-level violations were found: " + "; ".join(
            reason_fragment(item) for item in violated[:3]
        )
    return "Excluded based on the GPT final judgment; no criterion-level violation reason was preserved."


def reason_fragment(item: dict[str, Any]) -> str:
    return f"{item.get('criterion_id', '')}: {item.get('reason', '')}".strip()


def validate_record(record: dict[str, Any], expected: dict[str, Any]) -> list[str]:
    errors = []
    patient_id = record["patient_id"]
    expected_trials = [trial["trial_id"] for trial in expected.get("candidate_trials", [])]
    expected_criteria = criteria_by_trial(expected)
    final = record["final_output"]
    candidate_trials = record.get("candidate_trials", [])
    if sorted(record_candidate_trial_ids(candidate_trials)) != sorted(expected_trials):
        errors.append(f"{patient_id}: candidate_trials do not match expected candidates")
    for candidate in candidate_trials:
        if not isinstance(candidate, dict):
            errors.append(f"{patient_id}: candidate_trials must contain objects, not ids")
            continue
        if not candidate.get("trial_title") or not candidate.get("criteria_to_assess"):
            errors.append(f"{patient_id}/{candidate.get('trial_id', '')}: incomplete candidate trial payload")
    if not final.get("medical_disclaimer"):
        errors.append(f"{patient_id}: missing medical disclaimer")
    initial_trials = final["initial_assessment"].get("evaluated_trials", [])
    final_trials = final["final_assessment_after_answers"].get("evaluated_trials", [])
    if sorted(item.get("trial_id") for item in initial_trials) != sorted(expected_trials):
        errors.append(f"{patient_id}: initial evaluated trials do not match candidates")
    if sorted(item.get("trial_id") for item in final_trials) != sorted(expected_trials):
        errors.append(f"{patient_id}: final evaluated trials do not match candidates")
    for section, rows in [
        ("initial", initial_trials),
        ("final", final_trials),
    ]:
        for row in rows:
            trial_id = row.get("trial_id", "")
            if row.get("eligibility") not in ELIGIBILITY_LABELS:
                errors.append(f"{patient_id}/{trial_id}: invalid {section} eligibility")
            if not row.get("explanation"):
                errors.append(f"{patient_id}/{trial_id}: missing {section} explanation")
            actual_criteria = [item.get("criterion_id", "") for item in row.get("criterion_results", [])]
            if sorted(actual_criteria) != sorted(expected_criteria.get(trial_id, [])):
                errors.append(f"{patient_id}/{trial_id}: {section} criterion ids mismatch")
            for criterion in row.get("criterion_results", []):
                if criterion.get("status") not in CRITERION_STATUSES:
                    errors.append(f"{patient_id}/{trial_id}/{criterion.get('criterion_id')}: invalid status")
                if "reason" not in criterion:
                    errors.append(f"{patient_id}/{trial_id}/{criterion.get('criterion_id')}: missing reason")
    for row in final.get("recommended_trials", []):
        trial_id = row.get("trial_id", "")
        final_row = next(item for item in final_trials if item["trial_id"] == trial_id)
        if row.get("eligibility") != "eligible":
            errors.append(f"{patient_id}/{trial_id}: recommended trial missing eligible label")
        if final_row["eligibility"] != "eligible":
            errors.append(f"{patient_id}/{trial_id}: non-eligible trial in recommended_trials")
        if not row.get("recommendation_reason"):
            errors.append(f"{patient_id}/{trial_id}: missing recommendation reason")
    for row in final.get("uncertain_but_actionable_trials", []):
        trial_id = row.get("trial_id", "")
        if row.get("eligibility") != "uncertain":
            errors.append(f"{patient_id}/{trial_id}: uncertain trial missing uncertain label")
    for row in final.get("excluded_trials", []):
        trial_id = row.get("trial_id", "")
        final_row = next(item for item in final_trials if item["trial_id"] == trial_id)
        if row.get("eligibility") != "ineligible":
            errors.append(f"{patient_id}/{trial_id}: excluded trial missing ineligible label")
        if final_row["eligibility"] != "ineligible":
            errors.append(f"{patient_id}/{trial_id}: non-ineligible trial in excluded_trials")
        if not row.get("exclusion_reason"):
            errors.append(f"{patient_id}/{trial_id}: missing exclusion reason")
    if sorted(
        [row["trial_id"] for row in final.get("recommended_trials", [])]
        + [row["trial_id"] for row in final.get("uncertain_but_actionable_trials", [])]
        + [row["trial_id"] for row in final.get("excluded_trials", [])]
    ) != sorted(expected_trials):
        errors.append(f"{patient_id}: recommended/uncertain/excluded partition does not cover candidates")
    question_ids = {item["question_id"] for item in final.get("follow_up_questions", [])}
    for answer in final.get("simulated_patient_answers", []):
        if answer.get("question_id") and answer["question_id"] not in question_ids:
            errors.append(f"{patient_id}/{answer['question_id']}: answer references missing question")
    return errors


def record_candidate_trial_ids(candidate_trials: Any) -> list[str]:
    if not isinstance(candidate_trials, list):
        return []
    ids = []
    for candidate in candidate_trials:
        if isinstance(candidate, dict):
            ids.append(str(candidate.get("trial_id", "")))
        else:
            ids.append(str(candidate))
    return ids


def build_summary(
    records: list[dict[str, Any]],
    validation_errors: list[str],
    warning_counts: Counter[str],
) -> dict[str, Any]:
    eligibility = Counter()
    criterion_status = Counter()
    recommended_count = 0
    uncertain_count = 0
    excluded_count = 0
    question_count = 0
    answer_count = 0
    final_evaluated_count = 0
    initial_evaluated_count = 0
    for record in records:
        final = record["final_output"]
        recommended_count += len(final["recommended_trials"])
        uncertain_count += len(final["uncertain_but_actionable_trials"])
        excluded_count += len(final["excluded_trials"])
        question_count += len(final["follow_up_questions"])
        answer_count += len(final["simulated_patient_answers"])
        initial_evaluated_count += len(final["initial_assessment"]["evaluated_trials"])
        for row in final["final_assessment_after_answers"]["evaluated_trials"]:
            final_evaluated_count += 1
            eligibility[row["eligibility"]] += 1
            for criterion in row["criterion_results"]:
                criterion_status[criterion["status"]] += 1
    return {
        "patient_count": len(records),
        "initial_evaluated_trial_count": initial_evaluated_count,
        "final_evaluated_trial_count": final_evaluated_count,
        "recommended_trial_count": recommended_count,
        "uncertain_but_actionable_trial_count": uncertain_count,
        "excluded_trial_count": excluded_count,
        "follow_up_question_count": question_count,
        "simulated_patient_answer_count": answer_count,
        "eligibility_distribution": dict(sorted(eligibility.items())),
        "criterion_status_distribution": dict(sorted(criterion_status.items())),
        "warning_counts": dict(sorted(warning_counts.items())),
        "validation_error_count": len(validation_errors),
        "validation_errors": validation_errors[:100],
    }


def clean_eligibility(value: Any) -> str:
    label = str(value or "").strip().lower()
    return label if label in ELIGIBILITY_LABELS else "uncertain"


def clean_status(value: Any) -> str:
    status = str(value or "").strip().lower()
    return status if status in CRITERION_STATUSES else "unknown"


def normalize_criterion_results(value: Any) -> list[dict[str, str]]:
    if isinstance(value, dict):
        rows = []
        for criterion_id, payload in value.items():
            if isinstance(payload, dict):
                rows.append(
                    {
                        "criterion_id": str(criterion_id),
                        "status": clean_status(payload.get("status") or payload.get("judgment")),
                        "reason": str(payload.get("reason") or payload.get("rationale") or ""),
                    }
                )
            else:
                rows.append(
                    {
                        "criterion_id": str(criterion_id),
                        "status": "unknown",
                        "reason": str(payload),
                    }
                )
        return rows
    rows = []
    for item in value if isinstance(value, list) else []:
        if isinstance(item, dict):
            rows.append(
                {
                    "criterion_id": str(item.get("criterion_id", "")),
                    "status": clean_status(item.get("status") or item.get("judgment")),
                    "reason": str(item.get("reason") or item.get("rationale") or ""),
                }
            )
        elif isinstance(item, list) and len(item) >= 3:
            rows.append(
                {
                    "criterion_id": str(item[0]),
                    "status": clean_status(item[1]),
                    "reason": str(item[2]),
                }
            )
    return rows


def fill_missing_criteria(
    rows: list[dict[str, str]],
    trial: dict[str, Any],
    warnings: Counter[str],
    *,
    context: str,
) -> list[dict[str, str]]:
    by_id = {row["criterion_id"]: row for row in rows if row.get("criterion_id")}
    for criterion in trial.get("criteria_to_assess", []):
        criterion_id = criterion["criterion_id"]
        if criterion_id not in by_id:
            warnings["missing_criterion_filled_unknown"] += 1
            by_id[criterion_id] = {
                "criterion_id": criterion_id,
                "status": "unknown",
                "reason": f"No GPT judgment was preserved for {context}; criterion retained as unknown.",
            }
        elif "reason" not in by_id[criterion_id]:
            by_id[criterion_id]["reason"] = ""
    return list(by_id.values())


def ordered_criteria(rows: list[dict[str, str]], expected_ids: list[str]) -> list[dict[str, str]]:
    by_id = {row["criterion_id"]: row for row in rows}
    return [by_id[criterion_id] for criterion_id in expected_ids if criterion_id in by_id]


def unknown_criteria(trial: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {
            "criterion_id": criterion["criterion_id"],
            "status": "unknown",
            "reason": "No GPT criterion judgment was available.",
        }
        for criterion in trial.get("criteria_to_assess", [])
    ]


def criteria_by_trial(expected: dict[str, Any]) -> dict[str, list[str]]:
    return {
        trial["trial_id"]: [
            criterion["criterion_id"]
            for criterion in trial.get("criteria_to_assess", [])
        ]
        for trial in expected.get("candidate_trials", [])
    }


def trial_identity(trial_id: str, expected: dict[str, Any]) -> dict[str, str]:
    for trial in expected.get("candidate_trials", []):
        if trial["trial_id"] == trial_id:
            return {
                "trial_id": trial_id,
                "trial_title": trial.get("title", ""),
                "trial_source_url": trial.get("source_url", ""),
            }
    return {"trial_id": trial_id, "trial_title": "", "trial_source_url": ""}


def first_list(value: Any, keys: list[str]) -> list[Any]:
    if isinstance(value, list):
        return value
    if not isinstance(value, dict):
        return []
    for key in keys:
        candidate = value.get(key)
        if isinstance(candidate, list):
            return candidate
        if isinstance(candidate, dict):
            nested = candidate.get("trials") or candidate.get("evaluated_trials")
            if isinstance(nested, list):
                return nested
    return []


def as_string_list(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    return []


def dedupe_answers(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    seen = set()
    result = []
    for row in rows:
        key = (row.get("question_id", ""), normalize_text(row.get("answer", "")))
        if key in seen:
            continue
        seen.add(key)
        result.append(row)
    return result


def dedupe_needed_for(rows: list[dict[str, str]], expected: dict[str, Any]) -> list[dict[str, str]]:
    valid_trials = {trial["trial_id"] for trial in expected.get("candidate_trials", [])}
    valid_criteria = {
        criterion["criterion_id"]: trial["trial_id"]
        for trial in expected.get("candidate_trials", [])
        for criterion in trial.get("criteria_to_assess", [])
    }
    seen = set()
    result = []
    for row in rows:
        trial_id = row.get("trial_id", "")
        criterion_id = row.get("criterion_id", "")
        if criterion_id and criterion_id in valid_criteria:
            trial_id = valid_criteria[criterion_id]
        if trial_id and trial_id not in valid_trials:
            continue
        key = (trial_id, criterion_id)
        if key in seen:
            continue
        seen.add(key)
        result.append({"trial_id": trial_id, "criterion_id": criterion_id})
    return result


def criterion_field(criterion: dict[str, Any]) -> str:
    criterion_id = criterion.get("criterion_id", "")
    match = re.match(r"NCT\d+-[IE]-(.+)", criterion_id)
    if match:
        return match.group(1).replace("-", "_")
    text = criterion.get("criterion", "").lower()
    if "age" in text:
        return "age"
    if "diagnosis" in text or "condition" in text:
        return "condition"
    if "stage" in text:
        return "stage"
    return "clinical_fact"


def criterion_operator(criterion: dict[str, Any]) -> str:
    if criterion.get("criterion_type") == "exclusion":
        return "must_be_absent"
    value = criterion.get("structured_value")
    field = criterion_field(criterion)
    if field == "age" and isinstance(value, dict):
        return "range"
    if isinstance(value, list):
        return "one_of"
    if value is None:
        return "clinical_match"
    return "equals"


def first_trial_id(text: str) -> str:
    match = re.search(r"NCT\d+", text)
    return match.group(0) if match else ""


def first_criterion_id(text: str) -> str:
    match = re.search(r"NCT\d+-[IE]-[A-Za-z0-9-]+", text)
    return match.group(0) if match else ""


def tokenize(text: str) -> list[str]:
    return [
        token
        for token in re.split(r"[^a-z0-9]+", text.lower().replace("_", " "))
        if len(token) > 2
    ]


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", str(text).strip().lower())


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
            handle.write("\n")


def write_text_lf(path: Path, text: str) -> None:
    path.write_bytes(text.encode("utf-8"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build final v2 GPT E2E teacher-label artifact.")
    parser.add_argument(
        "--input-100",
        type=Path,
        default=Path("artifacts/gpt-e2e-teacher-labeling/gpt_e2e_teacher_input_100.json"),
    )
    parser.add_argument(
        "--draft-jsonl",
        type=Path,
        default=Path("artifacts/gpt-e2e-teacher-labeling/gpt_e2e_teacher_labels_100.jsonl"),
    )
    parser.add_argument(
        "--output-jsonl",
        type=Path,
        default=Path("artifacts/gpt-e2e-teacher-labeling/gpt_e2e_teacher_labels_100.v2.jsonl"),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("artifacts/gpt-e2e-teacher-labeling/gpt_e2e_teacher_labels_100.v2.json"),
    )
    parser.add_argument(
        "--summary",
        type=Path,
        default=Path("artifacts/gpt-e2e-teacher-labeling/gpt_e2e_teacher_labels_100.v2_summary.json"),
    )
    return parser.parse_args()


if __name__ == "__main__":
    main()
