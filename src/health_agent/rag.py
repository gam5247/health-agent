from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Iterable

from health_agent.models import Trial


@dataclass(frozen=True)
class RagChunk:
    trial_id: str
    section: str
    text: str
    trial: Trial
    tokens: list[str]


@dataclass(frozen=True)
class RetrievedChunk:
    section: str
    text: str
    score: float

    def as_dict(self) -> dict:
        return {
            "section": self.section,
            "text": self.text,
            "score": round(self.score, 3),
        }


@dataclass(frozen=True)
class RetrievedTrial:
    trial: Trial
    score: float
    chunks: list[RetrievedChunk]

    def as_dict(self) -> dict:
        return {
            "trial_id": self.trial.trial_id,
            "title": self.trial.title,
            "score": round(self.score, 3),
            "chunk_count": len(self.chunks),
            "top_chunks": [chunk.as_dict() for chunk in self.chunks[:3]],
        }


@dataclass(frozen=True)
class RagIndex:
    chunks: list[RagChunk]
    doc_count: int
    document_frequency: dict[str, int]


def build_rag_index(trials: Iterable[Trial]) -> RagIndex:
    chunks: list[RagChunk] = []
    for trial in trials:
        for section, text in trial_to_sections(trial).items():
            chunks.append(
                RagChunk(
                    trial_id=trial.trial_id,
                    section=section,
                    text=text,
                    trial=trial,
                    tokens=tokenize(f"{trial.title} {section} {text}"),
                )
            )
    document_frequency: dict[str, int] = {}
    for chunk in chunks:
        for token in set(chunk.tokens):
            document_frequency[token] = document_frequency.get(token, 0) + 1
    return RagIndex(
        chunks=chunks,
        doc_count=len(chunks),
        document_frequency=document_frequency,
    )


def retrieve_trials(index: RagIndex, query: str, top_k: int) -> list[RetrievedTrial]:
    query_counts = Counter(tokenize(query))
    grouped: dict[str, dict] = {}

    for chunk in index.chunks:
        chunk_counts = Counter(chunk.tokens)
        score = 0.0
        for token, query_tf in query_counts.items():
            term_frequency = chunk_counts.get(token, 0)
            if not term_frequency:
                continue
            document_frequency = index.document_frequency.get(token, 0)
            inverse_document_frequency = math.log(
                1 + (index.doc_count + 1) / (document_frequency + 1)
            )
            score += query_tf * term_frequency * inverse_document_frequency
        if score <= 0:
            continue
        item = grouped.setdefault(
            chunk.trial_id,
            {"trial": chunk.trial, "score": 0.0, "chunks": []},
        )
        item["score"] += score
        item["chunks"].append(RetrievedChunk(chunk.section, chunk.text, score))

    retrieved = [
        RetrievedTrial(
            trial=value["trial"],
            score=value["score"],
            chunks=sorted(value["chunks"], key=lambda chunk: chunk.score, reverse=True),
        )
        for value in grouped.values()
    ]
    retrieved.sort(key=lambda item: item.score, reverse=True)
    return retrieved[:top_k]


def trial_to_sections(trial: Trial) -> dict[str, str]:
    return {
        "overview": " ".join(
            [
                f"{trial.trial_id}: {trial.title}.",
                f"Phase: {trial.phase or 'not specified'}.",
                f"Conditions: {_join(trial.conditions)}.",
                f"Interventions: {_join(trial.interventions)}.",
                trial.summary or "",
            ]
        ),
        "inclusion": " ".join(
            [
                f"Age: minimum {trial.min_age if trial.min_age is not None else 'none'}, "
                f"maximum {trial.max_age if trial.max_age is not None else 'none'}.",
                f"Sex: {trial.sex or 'all'}.",
                "Allowed stages: "
                f"{_join(trial.allowed_stages) if trial.allowed_stages else 'not stage-restricted'}.",
                f"Maximum ECOG: {trial.max_ecog if trial.max_ecog is not None else 'not specified'}.",
                "Required prior treatments: "
                f"{_join(trial.required_prior_treatments) if trial.required_prior_treatments else 'none'}.",
            ]
        ),
        "biomarkers": (
            "Required biomarkers: "
            + "; ".join(
                f"{marker} must be {value}"
                for marker, value in trial.required_biomarkers.items()
            )
            + "."
            if trial.required_biomarkers
            else "No required biomarker is specified."
        ),
        "exclusions": (
            "Exclude patients with "
            + "; ".join(flag.replace("_", " ") for flag in trial.excluded_flags)
            + "."
            if trial.excluded_flags
            else "No explicit exclusion flags are listed."
        ),
    }


def format_retrieved_context(retrieved: Iterable[RetrievedTrial]) -> str:
    blocks = []
    for item in retrieved:
        sections = trial_to_sections(item.trial)
        blocks.append(
            "\n".join(
                [
                    f"--- {item.trial.trial_id} | RAG score {round(item.score, 3)} ---",
                    f"Title: {item.trial.title}",
                    "Top retrieved sections: "
                    + ", ".join(chunk.section for chunk in item.chunks[:3]),
                    sections["overview"],
                    sections["inclusion"],
                    sections["biomarkers"],
                    sections["exclusions"],
                ]
            )
        )
    return "\n\n".join(blocks)


def tokenize(text: str) -> list[str]:
    stop_words = {
        "the",
        "and",
        "or",
        "is",
        "a",
        "an",
        "of",
        "for",
        "with",
        "to",
        "in",
        "as",
        "no",
        "not",
        "are",
        "be",
        "patient",
        "patients",
        "trial",
        "note",
    }
    normalized = (
        text.lower()
        .replace("non-small", "nonsmall")
        .replace("pd-l1", "pdl1")
        .replace("msi-h", "msih")
    )
    return [
        token
        for token in re.split(r"[^a-z0-9]+", normalized)
        if len(token) > 1 and token not in stop_words
    ]


def _join(values: list[str]) -> str:
    return ", ".join(values)

