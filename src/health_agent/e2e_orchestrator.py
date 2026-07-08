from __future__ import annotations

import re
from collections import defaultdict
from typing import Any


ELIGIBILITY_LABELS = {"eligible", "ineligible", "uncertain"}
CRITERION_STATUSES = {"satisfied", "violated", "unknown", "not_applicable"}
DISCLAIMER = "Synthetic software-evaluation output only. Not medical advice and not a real clinical eligibility decision."


def blinded_input_from_answer_record(record: dict[str, Any]) -> dict[str, Any]:
    """Keep only the material a contestant agent may see."""
    return {
        "patient_id": record["patient_id"],
        "patient_information_string": record["patient_information_string"],
        "candidate_trials": record["candidate_trials"],
    }


def run_competition_orchestration_v2(
    input_record: dict[str, Any],
    *,
    simulated_answers: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    patient_id = input_record["patient_id"]
    note = input_record["patient_information_string"]
    candidate_trials = input_record.get("candidate_trials", [])
    facts = extract_patient_facts(note, patient_id)

    criteria_agent = build_criteria_parser_agent(candidate_trials)
    initial_evaluated = evaluate_trials(
        patient_id=patient_id,
        candidate_trials=candidate_trials,
        facts=facts,
        source="deterministic_initial_matching",
    )
    questions = generate_follow_up_questions(patient_id, initial_evaluated)
    answer_rows = normalize_simulated_answers(simulated_answers or [], questions)
    final_facts = merge_answer_facts(facts, answer_rows)
    final_evaluated = evaluate_trials(
        patient_id=patient_id,
        candidate_trials=candidate_trials,
        facts=final_facts,
        source="deterministic_final_matching",
    )
    attach_related_questions(initial_evaluated, questions)
    attach_related_questions(final_evaluated, questions)
    recommended, uncertain, excluded = split_recommendations(final_evaluated)
    patient_summary = summarize_patient_recommendations(recommended, uncertain, excluded)

    agent_trace = {
        "criteria_parser_agent": criteria_agent,
        "patient_information_understanding_agent": {
            "patient_id": patient_id,
            "extracted_patient_facts": facts,
            "known_fact_summary": summarize_facts(facts),
            "source": "deterministic_note_parser",
        },
        "initial_matching_agent": {
            "evaluated_trials": initial_evaluated,
            "source": "deterministic_criteria_matcher",
        },
        "question_generation_agent": {
            "follow_up_questions": questions,
            "source": "unknown_criterion_question_generator",
        },
        "interaction_simulation_agent": {
            "simulated_patient_answers": answer_rows,
            "source": "external_patient_answer_input",
        },
        "final_matching_agent": {
            "evaluated_trials": final_evaluated,
            "source": "deterministic_criteria_matcher_after_answers",
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
    return {
        "schema_version": "health-agent-e2e-orchestration-v2",
        "patient_id": patient_id,
        "patient_information_string": note,
        "candidate_trials": candidate_trials,
        "agent_trace": agent_trace,
        "final_output": {
            "initial_assessment": {"evaluated_trials": initial_evaluated},
            "follow_up_questions": questions,
            "simulated_patient_answers": answer_rows,
            "final_assessment_after_answers": {"evaluated_trials": final_evaluated},
            "recommended_trials": recommended,
            "uncertain_but_actionable_trials": uncertain,
            "excluded_trials": excluded,
            "patient_level_summary": patient_summary,
            "medical_disclaimer": DISCLAIMER,
        },
    }


def build_criteria_parser_agent(candidate_trials: list[dict[str, Any]]) -> dict[str, Any]:
    parsed_trials = []
    for trial in candidate_trials:
        parsed_trials.append(
            {
                "trial_id": trial["trial_id"],
                "trial_title": trial.get("trial_title") or trial.get("title", ""),
                "trial_source_url": trial.get("trial_source_url") or trial.get("source_url", ""),
                "parsed_criteria": [
                    {
                        "criterion_id": criterion["criterion_id"],
                        "type": criterion.get("criterion_type", ""),
                        "field": criterion_field(criterion),
                        "operator": criterion_operator(criterion),
                        "value": criterion.get("structured_value"),
                        "required": bool(criterion.get("required", True)),
                        "source_text": criterion.get("criterion", ""),
                    }
                    for criterion in trial.get("criteria_to_assess", [])
                ],
            }
        )
    return {
        "parsed_trials": parsed_trials,
        "source": "candidate_trial.criteria_to_assess",
    }


def evaluate_trials(
    *,
    patient_id: str,
    candidate_trials: list[dict[str, Any]],
    facts: dict[str, Any],
    source: str,
) -> list[dict[str, Any]]:
    rows = []
    for trial in candidate_trials:
        criterion_results = [
            evaluate_criterion(facts, trial, criterion)
            for criterion in trial.get("criteria_to_assess", [])
        ]
        eligibility = aggregate_eligibility(criterion_results)
        rows.append(
            {
                "trial_id": trial["trial_id"],
                "trial_title": trial.get("trial_title") or trial.get("title", ""),
                "trial_source_url": trial.get("trial_source_url") or trial.get("source_url", ""),
                "eligibility": eligibility,
                "criterion_results": criterion_results,
                "related_question_ids": [],
                "explanation": explain_trial(eligibility, criterion_results),
                "source": source,
                "patient_id": patient_id,
            }
        )
    return rows


def evaluate_criterion(
    facts: dict[str, Any],
    trial: dict[str, Any],
    criterion: dict[str, Any],
) -> dict[str, str]:
    criterion_id = criterion["criterion_id"]
    ctype = str(criterion.get("criterion_type", "")).lower()
    field = criterion_field(criterion)
    value = criterion.get("structured_value")
    status, reason = criterion_status_and_reason(
        facts=facts,
        trial=trial,
        criterion_id=criterion_id,
        criterion_type=ctype,
        field=field,
        value=value,
    )
    return {
        "criterion_id": criterion_id,
        "status": status,
        "reason": reason,
    }


def criterion_status_and_reason(
    *,
    facts: dict[str, Any],
    trial: dict[str, Any],
    criterion_id: str,
    criterion_type: str,
    field: str,
    value: Any,
) -> tuple[str, str]:
    if field == "condition":
        diagnosis = facts.get("diagnosis") or ""
        conditions = as_string_list(value) or as_string_list(trial.get("conditions"))
        if not diagnosis:
            return "unknown", "Patient diagnosis is not documented."
        if condition_matches(str(diagnosis), conditions):
            return "satisfied", f"Patient diagnosis '{diagnosis}' matches supplied trial condition."
        return "violated", f"Patient diagnosis '{diagnosis}' does not match supplied trial condition."

    if field == "age":
        age = facts.get("age")
        bounds = value if isinstance(value, dict) else {}
        min_age = maybe_int(bounds.get("min_age"))
        max_age = maybe_int(bounds.get("max_age"))
        if age is None:
            return "unknown", "Patient age is not documented."
        if min_age is not None and int(age) < min_age:
            return "violated", f"Age {age} is below minimum age {min_age}."
        if max_age is not None and int(age) > max_age:
            return "violated", f"Age {age} is above maximum age {max_age}."
        return "satisfied", f"Age {age} is within supplied bounds."

    if field == "stage":
        stage = facts.get("stage")
        allowed = {normalize_stage(item) for item in as_string_list(value)}
        if not allowed:
            return "not_applicable", "No structured stage restriction was supplied."
        if not stage:
            return "unknown", "Patient stage is not documented."
        if normalize_stage(str(stage)) in allowed:
            return "satisfied", f"Stage {stage} is allowed."
        return "violated", f"Stage {stage} is not in allowed stages {sorted(allowed)}."

    if field == "ecog":
        ecog = facts.get("ecog")
        max_ecog = maybe_int(value)
        if max_ecog is None:
            return "not_applicable", "No structured ECOG threshold was supplied."
        if ecog is None:
            return "unknown", "Patient ECOG performance status is not documented."
        if int(ecog) <= max_ecog:
            return "satisfied", f"ECOG {ecog} is at or below maximum {max_ecog}."
        return "violated", f"ECOG {ecog} is above maximum {max_ecog}."

    if field.startswith("prior_"):
        treatment = field.replace("prior_", "").replace("_", " ")
        prior = facts.get("prior_treatments", {})
        value_known = prior.get(field)
        if value_known is None:
            return "unknown", f"Prior treatment status for {treatment} is not documented."
        if value_known:
            return "satisfied", f"Prior treatment status for {treatment} is documented as present."
        return "violated", f"Required prior treatment {treatment} is documented as absent."

    if field.startswith("biomarker_"):
        marker = field.replace("biomarker_", "").upper()
        biomarkers = facts.get("biomarkers", {})
        observed = biomarkers.get(marker) or biomarkers.get(marker.lower())
        if observed is None:
            return "unknown", f"Biomarker {marker} is not documented."
        if biomarker_matches(str(observed), str(value)):
            return "satisfied", f"Biomarker {marker} value '{observed}' matches requirement."
        return "violated", f"Biomarker {marker} value '{observed}' does not match requirement."

    if field.startswith("flag_"):
        flag = field.removeprefix("flag_")
        flags = facts.get("flags", {})
        observed = flags.get(flag)
        if observed is None:
            return "unknown", f"Exclusion flag {flag} is not documented."
        if observed:
            return "violated", f"Patient has exclusion flag {flag}."
        return "satisfied", f"Patient does not have exclusion flag {flag}."

    if criterion_type == "exclusion":
        flag = normalize_flag(str(value or criterion_id))
        observed = facts.get("flags", {}).get(flag)
        if observed is None:
            return "unknown", f"Exclusion criterion {flag} is not documented."
        if observed:
            return "violated", f"Patient has exclusion criterion {flag}."
        return "satisfied", f"Patient does not have exclusion criterion {flag}."

    return "unknown", f"No deterministic matcher is available for {criterion_id}."


def generate_follow_up_questions(patient_id: str, evaluated_trials: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for trial in evaluated_trials:
        for criterion in trial.get("criterion_results", []):
            if criterion.get("status") != "unknown":
                continue
            field = question_field_from_criterion(criterion["criterion_id"], criterion.get("reason", ""))
            grouped[field].append(
                {
                    "trial_id": trial["trial_id"],
                    "criterion_id": criterion["criterion_id"],
                }
            )

    questions = []
    for index, (field, needed_for) in enumerate(sorted(grouped.items()), start=1):
        questions.append(
            {
                "question_id": f"{patient_id}-Q{index:02d}",
                "question": question_for_field(field),
                "needed_for": dedupe_needed_for(needed_for),
                "reason": f"Required information for {field.replace('_', ' ')} is unknown.",
                "source": "deterministic_question_generator",
            }
        )
    return questions


def normalize_simulated_answers(
    answers: list[dict[str, str]],
    questions: list[dict[str, Any]],
) -> list[dict[str, str]]:
    valid_ids = {question["question_id"] for question in questions}
    rows = []
    for answer in answers:
        question_id = str(answer.get("question_id", ""))
        if question_id and valid_ids and question_id not in valid_ids:
            continue
        text = str(answer.get("answer") or answer.get("synthetic_answer") or "").strip()
        if not text:
            continue
        rows.append(
            {
                "question_id": question_id,
                "answer": text,
                "source": str(answer.get("source") or "external_patient_answer_input"),
            }
        )
    return rows


def merge_answer_facts(facts: dict[str, Any], answers: list[dict[str, str]]) -> dict[str, Any]:
    merged = {
        **facts,
        "flags": dict(facts.get("flags", {})),
        "prior_treatments": dict(facts.get("prior_treatments", {})),
        "biomarkers": dict(facts.get("biomarkers", {})),
    }
    for answer in answers:
        text = answer.get("answer", "")
        apply_answer_text(merged, text)
    return merged


def apply_answer_text(facts: dict[str, Any], text: str) -> None:
    lower = text.lower()
    ecog_match = re.search(r"\becog(?: performance status)?\s*(?:is|=)?\s*([0-5])\b", lower)
    if ecog_match:
        facts["ecog"] = int(ecog_match.group(1))
    if "stage iv" in lower or "stage 4" in lower:
        facts["stage"] = "IV"
    if "stage iii" in lower or "stage 3" in lower:
        facts["stage"] = "III"
    if "prior platinum" in lower or "platinum chemotherapy" in lower:
        facts.setdefault("prior_treatments", {})["prior_platinum_chemotherapy"] = not negated(lower, "platinum")
    for flag in CANONICAL_FLAGS:
        phrase = flag.replace("_", " ")
        if phrase in lower:
            facts.setdefault("flags", {})[flag] = not negated(lower, phrase)


def attach_related_questions(evaluated_trials: list[dict[str, Any]], questions: list[dict[str, Any]]) -> None:
    by_trial: dict[str, list[str]] = defaultdict(list)
    for question in questions:
        for link in question.get("needed_for", []):
            trial_id = link.get("trial_id", "")
            if trial_id and question["question_id"] not in by_trial[trial_id]:
                by_trial[trial_id].append(question["question_id"])
    for trial in evaluated_trials:
        trial["related_question_ids"] = by_trial.get(trial["trial_id"], [])


def split_recommendations(
    final_evaluated: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    ranked = sorted(final_evaluated, key=recommendation_sort_key)
    recommended = []
    uncertain = []
    excluded = []
    for item in ranked:
        if item["eligibility"] == "eligible":
            recommended.append(
                {
                    "rank": len(recommended) + 1,
                    "trial_id": item["trial_id"],
                    "trial_title": item["trial_title"],
                    "eligibility": "eligible",
                    "recommendation_reason": item["explanation"],
                    "supporting_criterion_ids": [
                        row["criterion_id"]
                        for row in item["criterion_results"]
                        if row["status"] in {"satisfied", "not_applicable"}
                    ],
                    "related_question_ids": item.get("related_question_ids", []),
                }
            )
        elif item["eligibility"] == "uncertain":
            uncertain.append(
                {
                    "trial_id": item["trial_id"],
                    "trial_title": item["trial_title"],
                    "eligibility": "uncertain",
                    "reason": item["explanation"],
                    "unknown_criterion_ids": [
                        row["criterion_id"]
                        for row in item["criterion_results"]
                        if row["status"] == "unknown"
                    ],
                    "related_question_ids": item.get("related_question_ids", []),
                }
            )
        else:
            excluded.append(
                {
                    "trial_id": item["trial_id"],
                    "trial_title": item["trial_title"],
                    "eligibility": "ineligible",
                    "exclusion_reason": item["explanation"],
                    "violated_criteria": [
                        row
                        for row in item["criterion_results"]
                        if row["status"] == "violated"
                    ],
                    "related_question_ids": item.get("related_question_ids", []),
                }
            )
    return recommended, uncertain, excluded


def extract_patient_facts(note: str, patient_id: str) -> dict[str, Any]:
    lower = note.lower()
    facts: dict[str, Any] = {
        "patient_id": patient_id,
        "age": infer_age(note),
        "sex": infer_sex(note),
        "diagnosis": infer_diagnosis(note),
        "stage": infer_stage(note),
        "ecog": infer_ecog(note),
        "biomarkers": infer_biomarkers(note),
        "prior_treatments": {},
        "flags": infer_flags(note),
        "location": infer_location(note),
        "source_note": note,
    }
    if "platinum" in lower:
        facts["prior_treatments"]["prior_platinum_chemotherapy"] = not negated(lower, "platinum")
    elif "no prior systemic therapy" in lower or "prior systemic therapy is not listed" in lower:
        facts["prior_treatments"]["prior_platinum_chemotherapy"] = False
    return facts


def infer_age(note: str) -> int | None:
    match = re.search(r"\b(\d{1,3})-year-old\b", note, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


def infer_sex(note: str) -> str | None:
    lower = note.lower()
    if re.search(r"\b(male|man|boy)\b", lower):
        return "male"
    if re.search(r"\b(female|woman|girl)\b", lower):
        return "female"
    return None


def infer_stage(note: str) -> str | None:
    match = re.search(r"stage (?:is recorded as )?(iv|iii|ii|i|4|3|2|1)\b", note, re.IGNORECASE)
    if not match:
        return None
    return normalize_stage(match.group(1)).upper()


def infer_ecog(note: str) -> int | None:
    match = re.search(r"\bECOG performance status is\s*([0-5])\b", note, re.IGNORECASE)
    return int(match.group(1)) if match else None


def infer_diagnosis(note: str) -> str | None:
    patterns = [
        r"with ([^.]+?)\. Stage",
        r"with ([^.]+?)\. ECOG",
        r"with ([^.]+?)\. Molecular",
        r"diagnosis of ([^.]+?)\.",
    ]
    for pattern in patterns:
        match = re.search(pattern, note, re.IGNORECASE)
        if match:
            return cleanup_diagnosis(match.group(1))
    return None


def infer_biomarkers(note: str) -> dict[str, str]:
    biomarkers: dict[str, str] = {}
    for marker in ["EGFR", "ALK", "BRAF", "KRAS", "HER2", "PD-L1", "PDL1"]:
        match = re.search(rf"\b{re.escape(marker)}\b[^.]*?(positive|negative|mutated|wild type|V600E|exon 19|L858R|amplified)", note, re.IGNORECASE)
        if match:
            biomarkers[marker.replace("PDL1", "PD-L1")] = match.group(1)
    return biomarkers


CANONICAL_FLAGS = [
    "active_interstitial_lung_disease",
    "active_autoimmune_disease",
    "uncontrolled_cardiac_disease",
    "active_uncontrolled_infection",
    "organ_transplant",
]


def infer_flags(note: str) -> dict[str, bool]:
    lower = note.lower()
    flags: dict[str, bool] = {}
    for flag in CANONICAL_FLAGS:
        phrase = flag.replace("_", " ")
        if phrase in lower:
            flags[flag] = not negated(lower, phrase)
    return flags


def infer_location(note: str) -> dict[str, str]:
    match = re.search(r"receives care in ([A-Z]{2})\b", note)
    if match:
        return {"country": "US", "state": match.group(1)}
    return {}


def aggregate_eligibility(criterion_results: list[dict[str, str]]) -> str:
    statuses = {row["status"] for row in criterion_results}
    if "violated" in statuses:
        return "ineligible"
    if "unknown" in statuses:
        return "uncertain"
    if "satisfied" in statuses or "not_applicable" in statuses:
        return "eligible"
    return "uncertain"


def explain_trial(eligibility: str, criterion_results: list[dict[str, str]]) -> str:
    counts = {
        status: sum(row["status"] == status for row in criterion_results)
        for status in sorted(CRITERION_STATUSES)
    }
    if eligibility == "eligible":
        return f"Eligible because no violated or unknown supplied criteria remain; counts={counts}."
    if eligibility == "ineligible":
        violated = [row for row in criterion_results if row["status"] == "violated"]
        return "Ineligible because supplied criteria are violated: " + "; ".join(
            f"{row['criterion_id']}: {row['reason']}" for row in violated[:3]
        )
    unknown = [row for row in criterion_results if row["status"] == "unknown"]
    return "Uncertain because required information is missing: " + "; ".join(
        f"{row['criterion_id']}: {row['reason']}" for row in unknown[:3]
    )


def summarize_patient_recommendations(
    recommended: list[dict[str, Any]],
    uncertain: list[dict[str, Any]],
    excluded: list[dict[str, Any]],
) -> str:
    if recommended:
        ids = ", ".join(item["trial_id"] for item in recommended)
        return f"Recommended eligible trial ids after final matching: {ids}."
    if uncertain:
        ids = ", ".join(item["trial_id"] for item in uncertain)
        return f"No eligible trial was identified; uncertain trials needing more information: {ids}."
    return f"No eligible or uncertain trial was identified; excluded trial count: {len(excluded)}."


def summarize_facts(facts: dict[str, Any]) -> str:
    parts = []
    for key in ["age", "sex", "diagnosis", "stage", "ecog"]:
        value = facts.get(key)
        if value not in (None, "", [], {}):
            parts.append(f"{key}={value}")
    return ", ".join(parts) if parts else "No core patient facts were deterministically extracted."


def criterion_field(criterion: dict[str, Any]) -> str:
    criterion_id = str(criterion.get("criterion_id", "")).lower()
    text = f"{criterion_id} {criterion.get('criterion', '')}".lower()
    if "condition" in criterion_id or "diagnosis" in text:
        return "condition"
    if "age" in criterion_id:
        return "age"
    if "stage" in criterion_id:
        return "stage"
    if "ecog" in criterion_id or "performance" in text:
        return "ecog"
    if "prior-platinum" in criterion_id or "platinum" in text:
        return "prior_platinum_chemotherapy"
    if "biomarker" in criterion_id or "molecular" in text:
        return "biomarker_required"
    if criterion.get("criterion_type") == "exclusion":
        return "flag_" + normalize_flag(str(criterion.get("structured_value") or criterion_id))
    return "raw"


def criterion_operator(criterion: dict[str, Any]) -> str:
    field = criterion_field(criterion)
    if field == "age":
        return "within_range"
    if field == "ecog":
        return "<="
    if field.startswith("flag_"):
        return "must_be_absent"
    if field.startswith("prior_"):
        return "must_be_present"
    return "matches"


def question_field_from_criterion(criterion_id: str, reason: str) -> str:
    field = criterion_field({"criterion_id": criterion_id, "criterion": reason})
    if field.startswith("flag_"):
        return field.removeprefix("flag_")
    return field


def question_for_field(field: str) -> str:
    labels = {
        "age": "What is the patient's age?",
        "condition": "What is the patient's confirmed diagnosis?",
        "ecog": "What is the patient's ECOG performance status?",
        "stage": "What is the patient's current disease stage?",
        "prior_platinum_chemotherapy": "Has the patient received prior platinum chemotherapy?",
        "biomarker_required": "What relevant biomarker or molecular test result is documented?",
    }
    if field in labels:
        return labels[field]
    return f"Does the patient have {field.replace('_', ' ')}?"


def recommendation_sort_key(item: dict[str, Any]) -> tuple[int, int, str]:
    rank = {"eligible": 3, "uncertain": 2, "ineligible": 1}.get(item["eligibility"], 0)
    satisfied = sum(row["status"] == "satisfied" for row in item.get("criterion_results", []))
    return rank, satisfied, item["trial_id"]


def dedupe_needed_for(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    seen = set()
    result = []
    for row in rows:
        key = (row.get("trial_id", ""), row.get("criterion_id", ""))
        if key in seen:
            continue
        seen.add(key)
        result.append(row)
    return result


def condition_matches(diagnosis: str, conditions: list[str]) -> bool:
    diagnosis_norm = normalize_text(diagnosis)
    diagnosis_tokens = condition_tokens(diagnosis_norm)
    for condition in conditions:
        condition_norm = normalize_text(condition)
        if condition_norm in diagnosis_norm or diagnosis_norm in condition_norm:
            return True
        if diagnosis_tokens and diagnosis_tokens & condition_tokens(condition_norm):
            return True
    return False


def biomarker_matches(observed: str, required: str) -> bool:
    observed_norm = normalize_text(observed)
    required_norm = normalize_text(required)
    if not required_norm or required_norm == "none":
        return True
    if required_norm == "positive":
        return observed_norm not in {"negative", "not detected", "wild type"}
    if required_norm == "negative":
        return observed_norm in {"negative", "not detected", "wild type"}
    return required_norm in observed_norm or observed_norm in required_norm


def condition_tokens(value: str) -> set[str]:
    generic = {
        "advanced",
        "cancer",
        "carcinoma",
        "disease",
        "locally",
        "metastatic",
        "patient",
        "patients",
        "recurrent",
        "solid",
        "stage",
        "tumor",
        "tumors",
    }
    return {token for token in re.findall(r"[a-z0-9]+", value) if len(token) > 3 and token not in generic}


def cleanup_diagnosis(value: str) -> str:
    text = value.strip()
    text = re.sub(r"\s+", " ", text)
    return text.rstrip(".")


def normalize_stage(value: str) -> str:
    text = str(value).strip().lower()
    return {"4": "iv", "3": "iii", "2": "ii", "1": "i"}.get(text, text)


def normalize_flag(value: str) -> str:
    text = normalize_text(value)
    text = text.replace("exclude if patient has ", "")
    text = text.replace("exclude if ", "")
    return re.sub(r"[^a-z0-9]+", "_", text).strip("_")


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", str(value).strip().lower().replace("-", " "))


def as_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def maybe_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def negated(text: str, phrase: str) -> bool:
    pattern = r"\b(no|not|without|absent|absence of|lacks?|lack of)\b[^.]{0,80}" + re.escape(phrase)
    reverse_pattern = re.escape(phrase) + r"[^.]{0,80}\b(absent|negative|not present|is absent)\b"
    return bool(re.search(pattern, text) or re.search(reverse_pattern, text))
