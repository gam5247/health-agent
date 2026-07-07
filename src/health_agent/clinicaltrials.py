from __future__ import annotations

import json
import re
import html
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


API_URL = "https://clinicaltrials.gov/api/v2/studies"
RECRUITING_STATUSES = {
    "RECRUITING",
    "NOT_YET_RECRUITING",
    "ACTIVE_NOT_RECRUITING",
    "ENROLLING_BY_INVITATION",
}

BIOMARKER_PATTERNS = {
    "EGFR": [
        (r"egfr[^.\n;]*(?:exon\s*19|19\s*del|deletion)", "exon19del"),
        (r"egfr[^.\n;]*l858r", "L858R"),
        (r"egfr[^.\n;]*(?:mutation|mutated|positive)", "positive"),
    ],
    "ALK": [(r"\balk[^.\n;]*(?:rearrangement|fusion|positive)", "positive")],
    "BRAF": [(r"\bbraf[^.\n;]*v600e", "V600E"), (r"\bbraf[^.\n;]*(?:mutation|mutated)", "positive")],
    "HER2": [(r"\bher2[^.\n;]*(?:positive|overexpress)", "positive")],
    "MSI": [(r"\bmsi[- ]?h|microsatellite instability[- ]high", "MSI-H")],
    "FLT3": [(r"\bflt3[^.\n;]*(?:itd|tkd)", "ITD_or_TKD"), (r"\bflt3[^.\n;]*(?:mutation|mutated)", "positive")],
    "BRCA1": [(r"\bbrca1[^.\n;]*(?:pathogenic|mutation|mutated)", "pathogenic")],
    "BRCA2": [(r"\bbrca2[^.\n;]*(?:pathogenic|mutation|mutated)", "pathogenic")],
    "KRAS": [(r"\bkras[^.\n;]*wild[- ]type", "wild type")],
}

EXCLUSION_FLAG_PATTERNS = {
    "untreated_brain_metastases": r"untreated[^.\n;]*brain metast",
    "active_interstitial_lung_disease": r"interstitial lung disease|pneumonitis",
    "active_autoimmune_disease": r"active autoimmune|autoimmune disease",
    "uncontrolled_cardiac_disease": r"uncontrolled cardiac|heart failure|myocardial infarction",
    "active_uncontrolled_infection": r"active infection|uncontrolled infection",
    "organ_transplant": r"organ transplant|transplant recipient",
}


@dataclass(frozen=True)
class FetchSummary:
    requested_conditions: list[str]
    fetched_studies: int
    normalized_trials: int
    raw_dir: str
    output_path: str


def fetch_trials(
    *,
    conditions: list[str],
    limit: int,
    page_size: int,
    raw_dir: Path,
    statuses: set[str] | None = None,
) -> tuple[list[dict[str, Any]], FetchSummary]:
    raw_dir.mkdir(parents=True, exist_ok=True)
    allowed_statuses = statuses or RECRUITING_STATUSES
    seen: set[str] = set()
    studies: list[dict[str, Any]] = []

    for condition in conditions:
        page_token = ""
        while len(studies) < limit:
            payload = fetch_studies_page(
                condition=condition,
                page_size=page_size,
                page_token=page_token,
            )
            raw_path = raw_dir / f"{slugify(condition)}-{len(studies):04d}.json"
            raw_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
            for study in payload.get("studies", []):
                nct_id = get_in(study, "protocolSection", "identificationModule", "nctId")
                status = get_in(study, "protocolSection", "statusModule", "overallStatus")
                if not nct_id or nct_id in seen:
                    continue
                if status and str(status).upper() not in allowed_statuses:
                    continue
                studies.append(study)
                seen.add(nct_id)
                if len(studies) >= limit:
                    break
            page_token = str(payload.get("nextPageToken") or "")
            if not page_token:
                break

    trials = [normalize_study(study) for study in studies]
    summary = FetchSummary(
        requested_conditions=conditions,
        fetched_studies=len(studies),
        normalized_trials=len(trials),
        raw_dir=str(raw_dir),
        output_path="",
    )
    return trials, summary


def fetch_studies_page(condition: str, page_size: int, page_token: str = "") -> dict[str, Any]:
    params = {
        "format": "json",
        "query.cond": condition,
        "pageSize": str(page_size),
    }
    if page_token:
        params["pageToken"] = page_token
    url = f"{API_URL}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def normalize_study(study: dict[str, Any]) -> dict[str, Any]:
    protocol = study.get("protocolSection", {})
    identification = protocol.get("identificationModule", {})
    description = protocol.get("descriptionModule", {})
    status_module = protocol.get("statusModule", {})
    conditions_module = protocol.get("conditionsModule", {})
    design = protocol.get("designModule", {})
    arms = protocol.get("armsInterventionsModule", {})
    eligibility = protocol.get("eligibilityModule", {})
    nct_id = str(identification.get("nctId") or "")
    criteria = clean_text(eligibility.get("eligibilityCriteria"))
    inclusion, exclusion = split_criteria(criteria)
    required_biomarkers = infer_required_biomarkers(
        " ".join([criteria, clean_text(identification.get("briefTitle")), clean_text(description.get("briefSummary"))])
    )
    excluded_flags = infer_exclusion_flags(criteria)
    return {
        "trial_id": nct_id,
        "title": clean_text(identification.get("briefTitle") or identification.get("officialTitle") or nct_id),
        "phase": clean_text(", ".join(design.get("phases") or [])),
        "conditions": [clean_text(item) for item in conditions_module.get("conditions", [])],
        "interventions": [
            clean_text(item.get("name"))
            for item in arms.get("interventions", [])
            if item.get("name")
        ],
        "min_age": parse_age_years(eligibility.get("minimumAge")),
        "max_age": parse_age_years(eligibility.get("maximumAge")),
        "sex": normalize_sex(eligibility.get("sex")),
        "allowed_stages": infer_allowed_stages(criteria),
        "max_ecog": infer_max_ecog(criteria),
        "required_biomarkers": required_biomarkers,
        "required_prior_treatments": infer_prior_treatments(criteria),
        "excluded_flags": excluded_flags,
        "required_patient_fields": infer_required_patient_fields(required_biomarkers),
        "summary": clean_text(description.get("briefSummary")),
        "status": clean_text(status_module.get("overallStatus")),
        "enrollment": get_in(design, "enrollmentInfo", "count"),
        "source_url": f"https://clinicaltrials.gov/study/{nct_id}" if nct_id else "",
        "eligibility_criteria": criteria,
        "inclusion_criteria": inclusion,
        "exclusion_criteria": exclusion,
    }


def split_criteria(criteria: str) -> tuple[list[str], list[str]]:
    inclusion: list[str] = []
    exclusion: list[str] = []
    current = inclusion
    for raw_line in criteria.splitlines():
        line = raw_line.strip(" -*\t")
        if not line:
            continue
        lower = line.lower()
        if "inclusion criteria" in lower:
            current = inclusion
            continue
        if "exclusion criteria" in lower:
            current = exclusion
            continue
        if len(line) >= 4:
            current.append(line)
    return inclusion[:80], exclusion[:80]


def clean_text(value: Any) -> str:
    text = html.unescape(str(value or ""))
    text = text.replace("\u2264", "<=").replace("\u2265", ">=")
    text = text.replace("\u2013", "-").replace("\u2014", "-").replace("\u2212", "-")
    text = text.encode("ascii", errors="ignore").decode("ascii")
    return re.sub(r"[ \t]+", " ", text).strip()


def parse_age_years(value: Any) -> int | None:
    text = str(value or "").strip()
    if not text or text.upper() == "N/A":
        return None
    match = re.search(r"(\d+)", text)
    if not match:
        return None
    number = int(match.group(1))
    lower = text.lower()
    if "month" in lower:
        return max(0, round(number / 12))
    if "week" in lower or "day" in lower:
        return 0
    return number


def normalize_sex(value: Any) -> str:
    text = str(value or "all").strip().lower()
    if text in {"female", "male"}:
        return text
    return "all"


def infer_allowed_stages(text: str) -> list[str]:
    found: set[str] = set()
    normalized = text.upper()
    for match in re.finditer(r"STAGE(?:S)?[^.\n;:]{0,100}", normalized):
        segment = match.group(0)
        for stage in ["IV", "III", "II", "I"]:
            if re.search(rf"\b{stage}(?:A|B|C)?\b", segment):
                found.add(stage)
    if "ADVANCED" in normalized or "METASTATIC" in normalized:
        found.add("IV")
    return sorted(found, key=["I", "II", "III", "IV"].index)


def infer_max_ecog(text: str) -> int | None:
    matches = re.findall(r"ECOG[^0-9]{0,30}(?:<=|0-|0\s+to\s+|or\s+)?([0-4])", text, re.IGNORECASE)
    if not matches:
        return None
    return max(int(item) for item in matches)


def infer_required_biomarkers(text: str) -> dict[str, str]:
    required: dict[str, str] = {}
    lower = text.lower()
    for marker, patterns in BIOMARKER_PATTERNS.items():
        for pattern, value in patterns:
            match = re.search(pattern, lower, re.IGNORECASE)
            if match and not has_negative_biomarker_context(lower, match.start()):
                required[marker] = merge_biomarker_value(required.get(marker), value)
                break
    return required


def has_negative_biomarker_context(text: str, start: int) -> bool:
    context = text[max(0, start - 60) : start]
    return bool(
        re.search(
            r"\b(no|without|negative for|absence of|lack of|wild[- ]type)\b",
            context,
            re.IGNORECASE,
        )
    )


def merge_biomarker_value(existing: str | None, value: str) -> str:
    if not existing:
        return value
    if existing == value:
        return existing
    if {existing, value} == {"L858R", "exon19del"}:
        return "L858R_or_exon19del"
    return existing


def infer_prior_treatments(text: str) -> list[str]:
    lower = text.lower()
    treatments = []
    if "platinum" in lower:
        treatments.append("platinum chemotherapy")
    if "trastuzumab" in lower:
        treatments.append("trastuzumab")
    if "oxaliplatin" in lower:
        treatments.append("oxaliplatin")
    if "induction chemotherapy" in lower:
        treatments.append("induction chemotherapy")
    if "androgen receptor" in lower:
        treatments.append("androgen receptor inhibitor")
    return sorted(set(treatments))


def infer_exclusion_flags(text: str) -> list[str]:
    lower = text.lower()
    return [
        flag
        for flag, pattern in EXCLUSION_FLAG_PATTERNS.items()
        if re.search(pattern, lower, re.IGNORECASE)
    ]


def infer_required_patient_fields(required_biomarkers: dict[str, str]) -> list[str]:
    fields = ["diagnosis", "stage", "ecog"]
    if required_biomarkers:
        fields.append("biomarkers")
    return fields


def get_in(value: dict[str, Any], *keys: str) -> Any:
    current: Any = value
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "query"
