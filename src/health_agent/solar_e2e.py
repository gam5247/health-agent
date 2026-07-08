from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from health_agent.e2e_orchestrator import CRITERION_STATUSES, DISCLAIMER, ELIGIBILITY_LABELS
from health_agent.llm_client import ChatResult, SolarClient
from health_agent.solar_tools import (
    SolarToolDatabase,
    parse_solar_tool_calls,
    solar_tool_definitions,
)


@dataclass(frozen=True)
class ParsedJson:
    ok: bool
    value: dict[str, Any]
    error: str = ""
    repaired: bool = False


PROMPT_VERSION = "solar-pro3-native-tools-e2e-v1"


def run_solar_e2e_orchestration(
    input_record: dict[str, Any],
    *,
    client: SolarClient,
    trial_database_records: list[dict[str, Any]] | None = None,
    max_tokens: int = 5000,
    tool_max_tokens: int = 1600,
    max_tool_rounds: int = 3,
    max_excerpt_chars: int = 12000,
) -> dict[str, Any]:
    db = SolarToolDatabase(
        input_record,
        trial_database_records=trial_database_records,
        max_excerpt_chars=max_excerpt_chars,
    )
    messages = build_solar_tool_messages(input_record)
    tools = solar_tool_definitions()
    tool_trace: list[dict[str, Any]] = []
    final_call: ChatResult | None = None
    final_parsed = ParsedJson(False, {}, "no final response")
    used_tool_call = False

    for round_index in range(max(1, max_tool_rounds)):
        first_tool_choice: str | dict[str, Any]
        first_tool_choice = {
            "type": "function",
            "function": {"name": "get_patient_candidate_bundle"},
        } if round_index == 0 else "auto"
        call = client.chat(
            messages,
            tools=tools,
            tool_choice=first_tool_choice,
            parallel_tool_calls=False if round_index == 0 else True,
            max_tokens=tool_max_tokens,
            temperature=0,
        )
        calls = parse_solar_tool_calls(call.tool_calls)
        parsed = parse_json_object(call.content) if not calls else ParsedJson(False, {}, "tool call turn")
        tool_trace.append(
            {
                "type": "assistant_tool_turn",
                "round": round_index + 1,
                "ok": call.ok,
                "http_status": call.http_status,
                "ms": call.ms,
                "json_ok": parsed.ok,
                "tool_call_count": len(calls),
                "tool_call_names": [item.name for item in calls],
                "tool_choice": first_tool_choice,
                "content_preview": sanitize_text(call.content, 1200),
            }
        )
        if not calls:
            if not used_tool_call:
                final_call = ChatResult(
                    ok=False,
                    http_status=call.http_status,
                    retry_after=call.retry_after,
                    ms=call.ms,
                    content="",
                    finish_reason=call.finish_reason,
                    error=call.error
                    or "Solar Pro 3 returned no native tool call before final output.",
                )
                final_parsed = ParsedJson(False, {}, final_call.error)
                tool_trace.append(
                    {
                        "type": "missing_required_tool_call",
                        "round": round_index + 1,
                        "required_tool": "get_patient_candidate_bundle",
                    }
                )
                break
            tool_trace.append(
                {
                    "type": "assistant_no_more_tools",
                    "round": round_index + 1,
                    "content_preview": sanitize_text(call.content, 1200),
                }
            )
            break
        results = [db.execute(item) for item in calls]
        used_tool_call = True
        tool_trace.append({"type": "tool_results", "results": results})
        messages.append(
            {
                "role": "assistant",
                "content": call.content,
                "tool_calls": list(call.tool_calls),
            }
        )
        messages.extend(
            db.tool_result_message(item, result)
            for item, result in zip(calls, results)
        )

    if final_call is None and used_tool_call:
        messages.append(
            {
                "role": "user",
                "content": build_final_only_instruction(input_record),
            }
        )
        final_call = client.chat(
            messages,
            max_tokens=max_tokens,
            temperature=0,
        )
        final_parsed = parse_json_object(final_call.content)
        tool_trace.append(
            {
                "type": "assistant_final_turn",
                "ok": final_call.ok,
                "http_status": final_call.http_status,
                "ms": final_call.ms,
                "json_ok": final_parsed.ok,
                "content_preview": sanitize_text(final_call.content, 1200),
            }
        )

    return normalize_solar_prediction(
        input_record,
        final_call,
        final_parsed,
        runner="solar-pro3-native-tools",
        extra_trace={"solar_tool_trace": tool_trace},
    )


def run_solar_inline_e2e_orchestration(
    input_record: dict[str, Any],
    *,
    client: SolarClient,
    max_tokens: int = 5000,
    max_excerpt_chars: int = 1200,
) -> dict[str, Any]:
    messages = build_solar_e2e_messages(input_record, max_excerpt_chars=max_excerpt_chars)
    call = client.chat(messages, max_tokens=max_tokens, temperature=0)
    parsed = parse_json_object(call.content)
    return normalize_solar_prediction(
        input_record,
        call,
        parsed,
        runner="solar-pro3-inline",
    )


def build_solar_e2e_messages(
    input_record: dict[str, Any],
    *,
    max_excerpt_chars: int = 1200,
) -> list[dict[str, str]]:
    compact_input = {
        "patient_id": input_record["patient_id"],
        "patient_information_string": input_record["patient_information_string"],
        "candidate_trials": [
            compact_trial(trial, max_excerpt_chars=max_excerpt_chars)
            for trial in input_record.get("candidate_trials", [])
        ],
    }
    return [
        {
            "role": "system",
            "content": "\n".join(
                [
                    "You are Solar Pro 3 running a clinical-trial matching multi-agent workflow.",
                    "Use only the supplied synthetic patient note and candidate-trial criteria.",
                    "Do not invent patient facts. If information is missing, mark the criterion unknown and ask a follow-up question.",
                    "Return one valid JSON object only. Do not use markdown.",
                    "Allowed trial eligibility labels: eligible, ineligible, uncertain.",
                    "Allowed criterion statuses: satisfied, violated, unknown, not_applicable.",
                    "Eligibility semantics: any violated required criterion means ineligible; no violations but at least one unknown means uncertain; otherwise eligible.",
                    "Initial assessment must use only facts stated in the patient note and tool results.",
                    "For workflow simulation, generate simulated_patient_answers to your own follow-up questions when missing facts block eligibility resolution.",
                    "Final assessment must be a separate second pass after applying those simulated answers.",
                    "This is synthetic software evaluation only, not medical advice.",
                ]
            ),
        },
        {
            "role": "user",
            "content": "\n".join(
                [
                    "Perform these agent steps internally:",
                    "1. Criteria parser: structure every supplied criterion.",
                    "2. Patient information understanding: extract only facts stated in the note.",
                    "3. Initial matching: judge every criterion for every candidate trial.",
                    "4. Question generation: ask about missing information needed for unknown criteria.",
                    "5. Recommendation: rank eligible trials and separate uncertain/excluded trials.",
                    "6. Result explanation: explain every final trial judgment.",
                    "",
                    "Output JSON with this exact top-level shape:",
                    json.dumps(
                        {
                            "patient_id": input_record["patient_id"],
                            "criteria_parser_agent": {"parsed_trials": []},
                            "patient_information_understanding_agent": {
                                "extracted_patient_facts": {},
                                "known_fact_summary": "",
                            },
                            "initial_assessment": {
                                "evaluated_trials": [
                                    {
                                        "trial_id": "string",
                                        "eligibility": "eligible|ineligible|uncertain",
                                        "criterion_results": [
                                            {
                                                "criterion_id": "string",
                                                "status": "satisfied|violated|unknown|not_applicable",
                                                "reason": "short evidence-based reason",
                                            }
                                        ],
                                        "explanation": "short explanation",
                                    }
                                ]
                            },
                            "follow_up_questions": [
                                {
                                    "question_id": "string",
                                    "question": "string",
                                    "needed_for": [
                                        {"trial_id": "string", "criterion_id": "string"}
                                    ],
                                    "reason": "string",
                                }
                            ],
                            "simulated_patient_answers": [
                                {
                                    "question_id": "string",
                                    "answer": "synthetic patient answer used only for workflow simulation",
                                    "source": "solar-pro3-simulated-follow-up",
                                }
                            ],
                            "final_assessment_after_answers": {
                                "evaluated_trials": [
                                    {
                                        "trial_id": "string",
                                        "eligibility": "eligible|ineligible|uncertain",
                                        "criterion_results": [
                                            {
                                                "criterion_id": "string",
                                                "status": "satisfied|violated|unknown|not_applicable",
                                                "reason": "short evidence-based reason",
                                            }
                                        ],
                                        "explanation": "short explanation",
                                    }
                                ]
                            },
                            "recommended_trials": [
                                {
                                    "rank": 1,
                                    "trial_id": "string",
                                    "trial_title": "string",
                                    "eligibility": "eligible",
                                    "recommendation_reason": "string",
                                    "supporting_criterion_ids": [],
                                    "related_question_ids": [],
                                }
                            ],
                            "uncertain_but_actionable_trials": [],
                            "excluded_trials": [],
                            "patient_level_summary": "string",
                            "medical_disclaimer": DISCLAIMER,
                        },
                        ensure_ascii=False,
                    ),
                    "",
                    "Strict requirements:",
                    "- Include every candidate trial_id exactly once in initial_assessment.evaluated_trials.",
                    "- Include every candidate trial_id exactly once in final_assessment_after_answers.evaluated_trials.",
                    "- For each trial, include every criteria_to_assess criterion_id exactly once.",
                    "- Use the exact trial_id and criterion_id strings from the input.",
                    "- initial_assessment is the judgment before follow-up answers; missing facts should remain unknown there.",
                    "- simulated_patient_answers must answer the generated follow_up_questions for this synthetic workflow simulation.",
                    "- final_assessment_after_answers is the judgment after applying simulated_patient_answers; cite the simulated answer in reasons when it changes a criterion.",
                    "- If no follow-up questions are needed, simulated_patient_answers must be empty and final_assessment_after_answers may match initial_assessment.",
                    "- recommended_trials may contain only final trials labelled eligible.",
                    "- uncertain_but_actionable_trials may contain only final trials labelled uncertain.",
                    "- excluded_trials may contain only final trials labelled ineligible.",
                    "",
                    "Input JSON:",
                    json.dumps(compact_input, ensure_ascii=False, indent=2, sort_keys=True),
                ]
            ),
        },
    ]


def build_solar_tool_messages(input_record: dict[str, Any]) -> list[dict[str, str]]:
    candidate_count = len(input_record.get("candidate_trials", []))
    output_shape = {
        "patient_id": input_record["patient_id"],
        "initial_assessment": {"evaluated_trials": []},
        "follow_up_questions": [],
        "simulated_patient_answers": [
            {
                "question_id": "string",
                "answer": "synthetic patient answer used only for workflow simulation",
                "source": "solar-pro3-simulated-follow-up",
            }
        ],
        "final_assessment_after_answers": {"evaluated_trials": []},
        "recommended_trials": [],
        "uncertain_but_actionable_trials": [],
        "excluded_trials": [],
        "patient_level_summary": "string",
        "medical_disclaimer": DISCLAIMER,
    }
    return [
        {
            "role": "system",
            "content": "\n".join(
                [
                    "You are Solar Pro 3 running a clinical-trial matching multi-agent workflow.",
                    "You have access to a local, read-only trial database through native function tools.",
                    "Use the provided tools to fetch the same visible patient and candidate-trial information available to the local agent.",
                    "Do not invent patient facts. If information is missing, mark the criterion unknown and ask a follow-up question.",
                    "When you have enough tool results, return one final JSON object only. Do not use markdown.",
                    "Allowed trial eligibility labels: eligible, ineligible, uncertain.",
                    "Allowed criterion statuses: satisfied, violated, unknown, not_applicable.",
                    "Eligibility semantics: any violated required criterion means ineligible; no violations but at least one unknown means uncertain; otherwise eligible.",
                    "Initial assessment must use only facts stated in the patient note and tool results.",
                    "For workflow simulation, generate simulated_patient_answers to your own follow-up questions when missing facts block eligibility resolution.",
                    "Final assessment must be a separate second pass after applying those simulated answers.",
                    "Do not present simulated answers as original patient-note facts.",
                    "This is synthetic software evaluation only, not medical advice.",
                ]
            ),
        },
        {
            "role": "user",
            "content": "\n".join(
                [
                    "Task:",
                    f"Evaluate one synthetic patient against {candidate_count} candidate clinical trials.",
                    "The database is visible only through the function tools attached to this request.",
                    "",
                    "Recommended efficient first step:",
                    "Call get_patient_candidate_bundle to retrieve the patient note and all candidate-trial criteria.",
                    "",
                    "After tool results are provided, perform these agent steps internally:",
                    "1. Criteria parser: structure every supplied criterion.",
                    "2. Patient information understanding: extract only facts stated in the note.",
                    "3. Initial matching: judge every criterion for every candidate trial.",
                    "4. Question generation: ask about missing information needed for unknown criteria.",
                    "5. Recommendation: rank eligible trials and separate uncertain/excluded trials.",
                    "6. Result explanation: explain every final trial judgment.",
                    "",
                    "Final output JSON shape:",
                    json.dumps(output_shape, ensure_ascii=False, indent=2, sort_keys=True),
                    "",
                    "Strict final-output requirements:",
                    "- Do not spend final-answer tokens restating parsed criteria or raw trial text.",
                    "- Do not include criteria_parser_agent, patient_information_understanding_agent, parsed_trials, criteria, or reasons arrays in the final JSON.",
                    "- Include every candidate trial_id exactly once in initial_assessment.evaluated_trials.",
                    "- Include every candidate trial_id exactly once in final_assessment_after_answers.evaluated_trials.",
                    "- For each trial, include every criteria_to_assess criterion_id exactly once.",
                    "- Use exact trial_id and criterion_id strings returned by the tools.",
                    "- initial_assessment is the judgment before follow-up answers; missing facts should remain unknown there.",
                    "- simulated_patient_answers must answer the generated follow_up_questions for this synthetic workflow simulation.",
                    "- final_assessment_after_answers is the judgment after applying simulated_patient_answers; cite the simulated answer in reasons when it changes a criterion.",
                    "- If no follow-up questions are needed, simulated_patient_answers must be empty and final_assessment_after_answers may match initial_assessment.",
                    "- recommended_trials may contain only final trials labelled eligible.",
                    "- uncertain_but_actionable_trials may contain only final trials labelled uncertain.",
                    "- excluded_trials may contain only final trials labelled ineligible.",
                ]
            ),
        },
    ]


def build_final_only_instruction(input_record: dict[str, Any]) -> str:
    return "\n".join(
        [
            "No more tool rounds are available. Return the final competition JSON now using only the tool results already provided.",
            "Do not call another tool.",
            "Return JSON only. Do not use markdown.",
            "Do not include criteria_parser_agent, patient_information_understanding_agent, parsed_trials, criteria, or reasons arrays.",
            "Every evaluated trial row must include criterion_results. Do not replace criterion_results with a reasons array.",
            "Use only these top-level keys:",
            "patient_id, initial_assessment, follow_up_questions, simulated_patient_answers, final_assessment_after_answers, recommended_trials, uncertain_but_actionable_trials, excluded_trials, patient_level_summary, medical_disclaimer.",
            "Fill this skeleton exactly. Keep all trial_id and criterion_id values unchanged:",
            json.dumps(final_output_skeleton(input_record), ensure_ascii=False, indent=2, sort_keys=True),
        ]
    )


def final_output_skeleton(input_record: dict[str, Any]) -> dict[str, Any]:
    evaluated = []
    for trial in input_record.get("candidate_trials", []):
        evaluated.append(
            {
                "trial_id": trial["trial_id"],
                "eligibility": "eligible|ineligible|uncertain",
                "criterion_results": [
                    {
                        "criterion_id": criterion["criterion_id"],
                        "status": "satisfied|violated|unknown|not_applicable",
                        "reason": "evidence-based reason",
                    }
                    for criterion in trial.get("criteria_to_assess", [])
                ],
                "explanation": "trial-level explanation",
            }
        )
    return {
        "patient_id": input_record["patient_id"],
        "initial_assessment": {"evaluated_trials": evaluated},
        "follow_up_questions": [
            {
                "question_id": "string",
                "question": "string",
                "needed_for": [{"trial_id": "string", "criterion_id": "string"}],
                "reason": "string",
            }
        ],
        "simulated_patient_answers": [
            {
                "question_id": "string",
                "answer": "synthetic patient answer used only for workflow simulation",
                "source": "solar-pro3-simulated-follow-up",
            }
        ],
        "final_assessment_after_answers": {"evaluated_trials": evaluated},
        "recommended_trials": [
            {
                "rank": 1,
                "trial_id": "string",
                "trial_title": "string",
                "eligibility": "eligible",
                "recommendation_reason": "string",
                "supporting_criterion_ids": [],
                "related_question_ids": [],
            }
        ],
        "uncertain_but_actionable_trials": [],
        "excluded_trials": [],
        "patient_level_summary": "string",
        "medical_disclaimer": DISCLAIMER,
    }


def compact_trial(trial: dict[str, Any], *, max_excerpt_chars: int) -> dict[str, Any]:
    raw_excerpt = trial.get("raw_criteria_excerpt") if isinstance(trial.get("raw_criteria_excerpt"), dict) else {}
    return {
        "trial_id": trial.get("trial_id", ""),
        "trial_title": trial.get("trial_title") or trial.get("title", ""),
        "trial_source_url": trial.get("trial_source_url") or trial.get("source_url", ""),
        "status": trial.get("status"),
        "phase": trial.get("phase"),
        "conditions": trial.get("conditions", []),
        "interventions": trial.get("interventions", []),
        "known_structured_fields": trial.get("known_structured_fields", {}),
        "criteria_to_assess": trial.get("criteria_to_assess", []),
        "raw_criteria_excerpt": {
            "inclusion": truncate_list(raw_excerpt.get("inclusion", []), max_excerpt_chars),
            "exclusion": truncate_list(raw_excerpt.get("exclusion", []), max_excerpt_chars),
        },
    }


def parse_json_object(content: Any) -> ParsedJson:
    if not content or not content.strip():
        return ParsedJson(False, {}, "empty content")
    cleaned = strip_code_fence(str(content).strip())
    candidates = [cleaned, repair_json_text(cleaned)]
    sliced = slice_json_candidate(cleaned)
    if sliced:
        candidates.extend([sliced, repair_json_text(sliced)])

    last_error = ""
    for index, candidate in enumerate(candidates):
        if not candidate:
            continue
        try:
            value = json.loads(candidate)
            if isinstance(value, dict):
                return ParsedJson(True, value, repaired=index > 0)
            last_error = "JSON root is not an object"
        except json.JSONDecodeError as error:
            last_error = str(error)
    return ParsedJson(False, {}, last_error)


def normalize_solar_prediction(
    input_record: dict[str, Any],
    call: ChatResult,
    parsed: ParsedJson,
    *,
    runner: str = "solar-pro3-native-tools",
    extra_trace: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = parsed.value if parsed.ok else {}
    final_output = normalize_final_output(input_record, payload, parsed)
    trace = {
        "solar_call": {
            "ok": call.ok,
            "http_status": call.http_status,
            "retry_after": call.retry_after,
            "ms": call.ms,
            "finish_reason": call.finish_reason,
            "error": call.error or parsed.error,
            "json_ok": parsed.ok,
            "json_repaired": parsed.repaired,
            "content_preview": sanitize_text(call.content, 1500),
            "content": call.content,
        },
        "solar_normalization_audit": final_output["normalization_audit"],
        "criteria_parser_agent": payload.get("criteria_parser_agent", {}),
        "patient_information_understanding_agent": payload.get(
            "patient_information_understanding_agent", {}
        ),
        "initial_matching_agent": final_output["initial_assessment"],
        "question_generation_agent": {
            "follow_up_questions": final_output["follow_up_questions"]
        },
        "interaction_simulation_agent": {
            "simulated_patient_answers": final_output["simulated_patient_answers"]
        },
        "final_matching_agent": final_output["final_assessment_after_answers"],
        "recommendation_agent": {
            "recommended_trials": final_output["recommended_trials"],
            "uncertain_but_actionable_trials": final_output["uncertain_but_actionable_trials"],
            "excluded_trials": final_output["excluded_trials"],
        },
        "result_explanation_agent": {
            "patient_level_summary": final_output["patient_level_summary"],
            "medical_disclaimer": final_output["medical_disclaimer"],
        },
    }
    if extra_trace:
        trace.update(extra_trace)
    return {
        "schema_version": "health-agent-e2e-orchestration-v2",
        "runner": runner,
        "patient_id": input_record["patient_id"],
        "patient_information_string": input_record["patient_information_string"],
        "candidate_trials": input_record.get("candidate_trials", []),
        "agent_trace": trace,
        "final_output": final_output,
    }


def normalize_final_output(
    input_record: dict[str, Any],
    payload: dict[str, Any],
    parsed: ParsedJson,
) -> dict[str, Any]:
    initial = payload.get("initial_assessment") if isinstance(payload.get("initial_assessment"), dict) else {}
    final = (
        payload.get("final_assessment_after_answers")
        if isinstance(payload.get("final_assessment_after_answers"), dict)
        else initial
    )
    audit = {
        "prompt_version": PROMPT_VERSION,
        "raw_json_valid": parsed.ok,
        "parse_repaired": parsed.repaired,
        "initial_missing_trials_filled": 0,
        "final_missing_trials_filled": 0,
        "initial_extra_trial_ids_dropped": 0,
        "final_extra_trial_ids_dropped": 0,
        "initial_missing_criteria_filled": 0,
        "final_missing_criteria_filled": 0,
        "initial_extra_criterion_ids_dropped": 0,
        "final_extra_criterion_ids_dropped": 0,
        "initial_fallback_eligibility_count": 0,
        "final_fallback_eligibility_count": 0,
        "initial_fallback_criterion_status_count": 0,
        "final_fallback_criterion_status_count": 0,
        "simulated_answers_kept": 0,
        "simulated_answers_dropped": 0,
    }
    initial_rows = normalize_trial_rows(
        input_record,
        initial.get("evaluated_trials") if isinstance(initial, dict) else [],
        source="initial",
        audit=audit,
    )
    final_rows = normalize_trial_rows(
        input_record,
        final.get("evaluated_trials") if isinstance(final, dict) else [],
        source="final",
        audit=audit,
    )
    questions = normalize_questions(
        payload.get("follow_up_questions", []),
        input_record,
        initial_rows,
    )
    answer_rows = normalize_simulated_answers(
        payload.get("simulated_patient_answers", []),
        questions,
        audit,
    )
    attach_question_ids(final_rows, questions)
    attach_question_ids(initial_rows, questions)
    recommended, uncertain, excluded = partition_trials(final_rows)
    return {
        "initial_assessment": {"evaluated_trials": initial_rows},
        "follow_up_questions": questions,
        "simulated_patient_answers": answer_rows,
        "final_assessment_after_answers": {"evaluated_trials": final_rows},
        "recommended_trials": recommended,
        "uncertain_but_actionable_trials": uncertain,
        "excluded_trials": excluded,
        "patient_level_summary": normalize_text_field(
            payload.get("patient_level_summary"),
            default_summary(recommended, uncertain, excluded),
        ),
        "medical_disclaimer": normalize_text_field(payload.get("medical_disclaimer"), DISCLAIMER),
        "normalization_audit": audit,
    }


def normalize_trial_rows(
    input_record: dict[str, Any],
    rows: Any,
    *,
    source: str,
    audit: dict[str, Any],
) -> list[dict[str, Any]]:
    by_trial = {
        str(row.get("trial_id", "")): row
        for row in rows
        if isinstance(row, dict) and row.get("trial_id")
    } if isinstance(rows, list) else {}
    expected_ids = {trial["trial_id"] for trial in input_record.get("candidate_trials", [])}
    audit[f"{source}_extra_trial_ids_dropped"] += len(set(by_trial) - expected_ids)
    normalized = []
    for trial in input_record.get("candidate_trials", []):
        trial_id = trial["trial_id"]
        row = by_trial.get(trial_id, {})
        if not row:
            audit[f"{source}_missing_trials_filled"] += 1
        criterion_results = normalize_criterion_results(
            trial,
            row.get("criterion_results", []),
            source=source,
            audit=audit,
        )
        eligibility = normalize_eligibility(row.get("eligibility"))
        if not eligibility:
            audit[f"{source}_fallback_eligibility_count"] += 1
            eligibility = aggregate_from_criterion_statuses(criterion_results)
        explanation = normalize_text_field(
            row.get("explanation"),
            f"{source} Solar Pro 3 judgment normalized as {eligibility}.",
        )
        normalized.append(
            {
                "trial_id": trial_id,
                "trial_title": trial.get("trial_title") or trial.get("title", ""),
                "trial_source_url": trial.get("trial_source_url") or trial.get("source_url", ""),
                "eligibility": eligibility,
                "criterion_results": criterion_results,
                "related_question_ids": [],
                "explanation": explanation,
                "source": "solar-pro3-native-tools",
                "patient_id": input_record["patient_id"],
            }
        )
    return normalized


def normalize_criterion_results(
    trial: dict[str, Any],
    rows: Any,
    *,
    source: str,
    audit: dict[str, Any],
) -> list[dict[str, str]]:
    by_criterion = {
        str(row.get("criterion_id", "")): row
        for row in rows
        if isinstance(row, dict) and row.get("criterion_id")
    } if isinstance(rows, list) else {}
    expected_ids = {criterion["criterion_id"] for criterion in trial.get("criteria_to_assess", [])}
    audit[f"{source}_extra_criterion_ids_dropped"] += len(set(by_criterion) - expected_ids)
    normalized = []
    for criterion in trial.get("criteria_to_assess", []):
        criterion_id = criterion["criterion_id"]
        row = by_criterion.get(criterion_id, {})
        if not row:
            audit[f"{source}_missing_criteria_filled"] += 1
        status = normalize_status(row.get("status"))
        if not status:
            audit[f"{source}_fallback_criterion_status_count"] += 1
            status = "unknown"
        normalized.append(
            {
                "criterion_id": criterion_id,
                "status": status,
                "reason": normalize_text_field(
                    row.get("reason"),
                    "Solar Pro 3 did not provide a usable reason for this criterion.",
                ),
            }
        )
    return normalized


def normalize_questions(
    rows: Any,
    input_record: dict[str, Any],
    final_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    valid_pairs = {
        (trial["trial_id"], criterion["criterion_id"])
        for trial in input_record.get("candidate_trials", [])
        for criterion in trial.get("criteria_to_assess", [])
    }
    question_rows = rows if isinstance(rows, list) else []
    questions = []
    for index, row in enumerate(question_rows, start=1):
        if not isinstance(row, dict):
            continue
        needed_for = []
        for link in row.get("needed_for", []):
            if not isinstance(link, dict):
                continue
            pair = (str(link.get("trial_id", "")), str(link.get("criterion_id", "")))
            if pair in valid_pairs and pair not in needed_for:
                needed_for.append(pair)
        if not needed_for:
            continue
        questions.append(
            {
                "question_id": normalize_text_field(
                    row.get("question_id"),
                    f"{input_record['patient_id']}-Q{len(questions) + 1:02d}",
                ),
                "question": normalize_text_field(row.get("question"), "What missing clinical information is available?"),
                "needed_for": [
                    {"trial_id": trial_id, "criterion_id": criterion_id}
                    for trial_id, criterion_id in needed_for
                ],
                "reason": normalize_text_field(row.get("reason"), "Solar Pro 3 marked related criteria unknown."),
                "source": "solar-pro3-native-tools",
            }
        )
    if questions:
        return questions
    return structural_questions_for_unknowns(input_record["patient_id"], final_rows)


def normalize_simulated_answers(
    rows: Any,
    questions: list[dict[str, Any]],
    audit: dict[str, Any],
) -> list[dict[str, Any]]:
    valid_question_ids = {question["question_id"] for question in questions}
    answer_rows = rows if isinstance(rows, list) else []
    normalized = []
    seen = set()
    for row in answer_rows:
        if not isinstance(row, dict):
            audit["simulated_answers_dropped"] += 1
            continue
        question_id = str(row.get("question_id", "")).strip()
        if question_id not in valid_question_ids or question_id in seen:
            audit["simulated_answers_dropped"] += 1
            continue
        answer = normalize_text_field(
            row.get("answer") or row.get("response") or row.get("patient_answer"),
            "",
        )
        if not answer:
            audit["simulated_answers_dropped"] += 1
            continue
        seen.add(question_id)
        audit["simulated_answers_kept"] += 1
        normalized.append(
            {
                "question_id": question_id,
                "answer": answer,
                "source": normalize_text_field(
                    row.get("source"),
                    "solar-pro3-simulated-follow-up",
                ),
            }
        )
    return normalized


def structural_questions_for_unknowns(patient_id: str, final_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    links = []
    for row in final_rows:
        for criterion in row.get("criterion_results", []):
            if criterion.get("status") == "unknown":
                links.append(
                    {
                        "trial_id": row["trial_id"],
                        "criterion_id": criterion["criterion_id"],
                    }
                )
    if not links:
        return []
    return [
        {
            "question_id": f"{patient_id}-Q01",
            "question": "What missing clinical details are needed to resolve the unknown eligibility criteria?",
            "needed_for": links,
            "reason": "One or more Solar Pro 3 criterion judgments were unknown.",
            "source": "structural_question_fallback_from_solar_unknowns",
        }
    ]


def partition_trials(final_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    recommended = []
    uncertain = []
    excluded = []
    for row in sorted(final_rows, key=partition_sort_key):
        if row["eligibility"] == "eligible":
            recommended.append(
                {
                    "rank": len(recommended) + 1,
                    "trial_id": row["trial_id"],
                    "trial_title": row["trial_title"],
                    "eligibility": "eligible",
                    "recommendation_reason": row["explanation"],
                    "supporting_criterion_ids": [
                        item["criterion_id"]
                        for item in row["criterion_results"]
                        if item["status"] in {"satisfied", "not_applicable"}
                    ],
                    "related_question_ids": row.get("related_question_ids", []),
                }
            )
        elif row["eligibility"] == "uncertain":
            uncertain.append(
                {
                    "trial_id": row["trial_id"],
                    "trial_title": row["trial_title"],
                    "eligibility": "uncertain",
                    "reason": row["explanation"],
                    "unknown_criterion_ids": [
                        item["criterion_id"]
                        for item in row["criterion_results"]
                        if item["status"] == "unknown"
                    ],
                    "related_question_ids": row.get("related_question_ids", []),
                }
            )
        else:
            excluded.append(
                {
                    "trial_id": row["trial_id"],
                    "trial_title": row["trial_title"],
                    "eligibility": "ineligible",
                    "exclusion_reason": row["explanation"],
                    "violated_criteria": [
                        item
                        for item in row["criterion_results"]
                        if item["status"] == "violated"
                    ],
                    "related_question_ids": row.get("related_question_ids", []),
                }
            )
    return recommended, uncertain, excluded


def attach_question_ids(rows: list[dict[str, Any]], questions: list[dict[str, Any]]) -> None:
    by_trial: dict[str, list[str]] = {}
    for question in questions:
        for link in question.get("needed_for", []):
            trial_id = link.get("trial_id", "")
            if trial_id:
                by_trial.setdefault(trial_id, [])
                if question["question_id"] not in by_trial[trial_id]:
                    by_trial[trial_id].append(question["question_id"])
    for row in rows:
        row["related_question_ids"] = by_trial.get(row["trial_id"], [])


def aggregate_from_criterion_statuses(criteria: list[dict[str, str]]) -> str:
    statuses = {item["status"] for item in criteria}
    if "violated" in statuses:
        return "ineligible"
    if "unknown" in statuses:
        return "uncertain"
    return "eligible"


def partition_sort_key(row: dict[str, Any]) -> tuple[int, int, str]:
    rank = {"eligible": 3, "uncertain": 2, "ineligible": 1}.get(row.get("eligibility"), 0)
    satisfied = sum(item.get("status") == "satisfied" for item in row.get("criterion_results", []))
    return (-rank, -satisfied, str(row.get("trial_id", "")))


def normalize_eligibility(value: Any) -> str:
    text = str(value or "").strip().lower()
    return text if text in ELIGIBILITY_LABELS else ""


def normalize_status(value: Any) -> str:
    text = str(value or "").strip().lower()
    return text if text in CRITERION_STATUSES else ""


def normalize_text_field(value: Any, default: str) -> str:
    text = str(value or "").strip()
    return text if text else default


def default_summary(
    recommended: list[dict[str, Any]],
    uncertain: list[dict[str, Any]],
    excluded: list[dict[str, Any]],
) -> str:
    if recommended:
        return "Solar Pro 3 identified eligible trials: " + ", ".join(row["trial_id"] for row in recommended) + "."
    if uncertain:
        return "Solar Pro 3 found no eligible trials; unresolved trials need more information: " + ", ".join(row["trial_id"] for row in uncertain) + "."
    return f"Solar Pro 3 excluded all supplied candidate trials; excluded trial count: {len(excluded)}."


def truncate_list(value: Any, max_chars: int) -> list[str]:
    if not isinstance(value, list):
        return []
    result = []
    for item in value:
        text = str(item)
        result.append(text if len(text) <= max_chars else text[:max_chars] + "...")
    return result


def strip_code_fence(text: str) -> str:
    text = re.sub(r"^```(?:json)?", "", text.strip(), flags=re.IGNORECASE)
    text = re.sub(r"```$", "", text.strip(), flags=re.IGNORECASE)
    return text.strip()


def repair_json_text(text: str) -> str:
    text = text.replace("\ufeff", "")
    text = re.sub(r",\s*([}\]])", r"\1", text)
    return text.strip()


def slice_json_candidate(text: str) -> str:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return ""
    return text[start : end + 1]


def sanitize_text(value: Any, max_length: int) -> str:
    text = str(value or "")
    text = "".join(
        character
        for character in text
        if character in "\t\n\r" or 32 <= ord(character) <= 126
    )
    return text[:max_length]
