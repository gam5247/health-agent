from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ToolCall:
    call_id: str
    name: str
    arguments: dict[str, Any]


class SolarToolDatabase:
    def __init__(
        self,
        input_record: dict[str, Any],
        *,
        trial_database_records: list[dict[str, Any]] | None = None,
        max_excerpt_chars: int = 12000,
    ) -> None:
        self.input_record = input_record
        self.max_excerpt_chars = max_excerpt_chars
        self.candidate_by_id = {
            trial["trial_id"]: trial for trial in input_record.get("candidate_trials", [])
        }
        self.trial_db_by_id = {
            str(record.get("trial_id", "")): record
            for record in trial_database_records or []
            if record.get("trial_id")
        }

    def execute(self, tool_call: ToolCall) -> dict[str, Any]:
        name = tool_call.name
        args = tool_call.arguments
        if name == "get_patient_note":
            return {
                "tool_call_id": tool_call.call_id,
                "name": name,
                "ok": True,
                "result": {
                    "patient_id": self.input_record["patient_id"],
                    "patient_information_string": self.input_record[
                        "patient_information_string"
                    ],
                },
            }
        if name == "list_candidate_trials":
            return {
                "tool_call_id": tool_call.call_id,
                "name": name,
                "ok": True,
                "result": {
                    "patient_id": self.input_record["patient_id"],
                    "candidate_trials": [
                        {
                            "trial_id": trial["trial_id"],
                            "trial_title": trial.get("trial_title")
                            or trial.get("title", ""),
                            "retrieval_rank": trial.get("retrieval_rank"),
                            "retrieval_score": trial.get("retrieval_score"),
                        }
                        for trial in self.input_record.get("candidate_trials", [])
                    ],
                },
            }
        if name == "get_trial_detail":
            trial_id = str(args.get("trial_id", ""))
            return self._trial_detail_result(tool_call.call_id, name, trial_id)
        if name == "get_patient_candidate_bundle":
            return {
                "tool_call_id": tool_call.call_id,
                "name": name,
                "ok": True,
                "result": {
                    "patient_id": self.input_record["patient_id"],
                    "patient_information_string": self.input_record[
                        "patient_information_string"
                    ],
                    "candidate_trials": [
                        self._trial_detail(trial_id) for trial_id in self.candidate_by_id
                    ],
                },
            }
        return {
            "tool_call_id": tool_call.call_id,
            "name": name,
            "ok": False,
            "error": f"Unknown tool: {name}",
            "result": None,
        }

    def tool_result_message(self, tool_call: ToolCall, result: dict[str, Any]) -> dict[str, str]:
        return {
            "role": "tool",
            "tool_call_id": tool_call.call_id,
            "name": tool_call.name,
            "content": json.dumps(result, ensure_ascii=False, sort_keys=True),
        }

    def _trial_detail_result(self, call_id: str, name: str, trial_id: str) -> dict[str, Any]:
        if trial_id not in self.candidate_by_id:
            return {
                "tool_call_id": call_id,
                "name": name,
                "ok": False,
                "error": f"trial_id is not in candidate set: {trial_id}",
                "result": None,
            }
        return {
            "tool_call_id": call_id,
            "name": name,
            "ok": True,
            "result": self._trial_detail(trial_id),
        }

    def _trial_detail(self, trial_id: str) -> dict[str, Any]:
        candidate = dict(self.candidate_by_id[trial_id])
        db_record = self.trial_db_by_id.get(trial_id, {})
        detail = {
            **candidate,
            "database_record": compact_database_record(db_record, self.max_excerpt_chars),
        }
        raw_excerpt = detail.get("raw_criteria_excerpt")
        if isinstance(raw_excerpt, dict):
            detail["raw_criteria_excerpt"] = truncate_nested_strings(
                raw_excerpt, self.max_excerpt_chars
            )
        return detail


def solar_tool_definitions() -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": "get_patient_note",
                "description": "Return the synthetic patient information string for the current case.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "list_candidate_trials",
                "description": "Return candidate trial IDs and retrieval metadata for the current patient.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_trial_detail",
                "description": "Return all visible details for one candidate trial_id, including criteria and public database text when available.",
                "parameters": {
                    "type": "object",
                    "properties": {"trial_id": {"type": "string"}},
                    "required": ["trial_id"],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_patient_candidate_bundle",
                "description": "Return the patient note plus all visible candidate-trial details in one tool result.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False,
                },
            },
        },
    ]


def parse_solar_tool_calls(rows: Any) -> list[ToolCall]:
    if not isinstance(rows, (list, tuple)):
        return []
    calls = []
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            continue
        function = row.get("function") if isinstance(row.get("function"), dict) else {}
        name = str(function.get("name") or row.get("name") or "")
        if not name:
            continue
        args = function.get("arguments", row.get("arguments", {}))
        if isinstance(args, str):
            try:
                args = json.loads(args) if args.strip() else {}
            except json.JSONDecodeError:
                args = {}
        if not isinstance(args, dict):
            args = {}
        calls.append(
            ToolCall(
                call_id=str(row.get("id") or f"call_{index}"),
                name=name,
                arguments=args,
            )
        )
    return calls


def compact_database_record(record: dict[str, Any], max_chars: int) -> dict[str, Any]:
    if not record:
        return {}
    allowed = {
        "trial_id",
        "title",
        "phase",
        "conditions",
        "interventions",
        "min_age",
        "max_age",
        "sex",
        "allowed_stages",
        "max_ecog",
        "required_biomarkers",
        "required_prior_treatments",
        "excluded_flags",
        "required_patient_fields",
        "summary",
        "status",
        "source_url",
        "eligibility_criteria",
        "inclusion_criteria",
        "exclusion_criteria",
    }
    return {
        key: truncate_nested_strings(value, max_chars)
        for key, value in record.items()
        if key in allowed
    }


def truncate_nested_strings(value: Any, max_chars: int) -> Any:
    if isinstance(value, str):
        return value if len(value) <= max_chars else value[:max_chars] + "..."
    if isinstance(value, list):
        return [truncate_nested_strings(item, max_chars) for item in value]
    if isinstance(value, dict):
        return {
            str(key): truncate_nested_strings(child, max_chars)
            for key, child in value.items()
        }
    return value
