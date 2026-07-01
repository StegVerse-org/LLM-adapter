"""Continuity search boundary for governed LLM adapter.

This module defines a local, deterministic interface for resolving query evidence
from receipt/history state. It is intentionally provider-free and network-free.
Future continuity-search services can implement the same response shape.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Sequence

from .retrieval_evidence import evidence_list_from_fixtures


CONTINUITY_SEARCH_SCHEMA_VERSION = "stegverse.llm_adapter.continuity_search.v0.1"


@dataclass(frozen=True)
class ContinuitySearchResult:
    """Result returned by a continuity-search boundary."""

    query: str
    evidence: tuple[Any, ...]
    freshness_status: str
    reconstruction_notes: tuple[str, ...] = field(default_factory=tuple)
    schema_version: str = CONTINUITY_SEARCH_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "query": self.query,
            "evidence": [item.to_dict() for item in self.evidence],
            "freshness_status": self.freshness_status,
            "reconstruction_notes": list(self.reconstruction_notes),
        }


class FixtureContinuitySearch:
    """In-memory continuity-search implementation for deterministic tests."""

    def __init__(self, fixtures: Sequence[Mapping[str, Any]]) -> None:
        self.fixtures = tuple(fixtures)

    def search(self, query: str) -> ContinuitySearchResult:
        matched = []
        notes = []
        lowered = query.lower()
        for fixture in self.fixtures:
            searchable = " ".join(
                str(fixture.get(key, "")) for key in ("pointer", "source_type", "notes", "freshness")
            ).lower()
            if not searchable or any(word in searchable for word in lowered.split()):
                matched.append(fixture)

        if not matched:
            notes.append("No fixture evidence matched; returning empty evidence set.")
            freshness_status = "unresolved"
        else:
            freshness_values = {str(item.get("freshness", "current")) for item in matched}
            if freshness_values <= {"current"}:
                freshness_status = "current"
            elif "revoked" in freshness_values:
                freshness_status = "revoked"
            elif "superseded" in freshness_values:
                freshness_status = "superseded"
            elif "stale" in freshness_values:
                freshness_status = "stale"
            else:
                freshness_status = "mixed"
            notes.append("Fixture continuity search returned evidence pointers only; payloads remain outside receipts.")

        return ContinuitySearchResult(
            query=query,
            evidence=evidence_list_from_fixtures(matched),
            freshness_status=freshness_status,
            reconstruction_notes=tuple(notes),
        )


def continuity_result_from_fixtures(
    query: str,
    fixtures: Sequence[Mapping[str, Any]],
) -> ContinuitySearchResult:
    """Convenience helper for deterministic continuity-search tests."""

    return FixtureContinuitySearch(fixtures).search(query)


__all__ = [
    "CONTINUITY_SEARCH_SCHEMA_VERSION",
    "ContinuitySearchResult",
    "FixtureContinuitySearch",
    "continuity_result_from_fixtures",
]
