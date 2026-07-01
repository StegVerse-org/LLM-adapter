"""Local retrieval fixtures for governed adapter proof paths."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, Sequence

try:
    from stegverse.governed_llm import EvidencePointer
except ImportError:  # pragma: no cover
    from .governed_adapter import EvidencePointer


def stable_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def stable_hash(value: object) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class RetrievalRecord:
    source_type: str
    pointer: str
    content: str
    freshness: str = "current"
    authority_scope: str = "read"

    def to_evidence_pointer(self) -> EvidencePointer:
        return EvidencePointer(
            source_type=self.source_type,
            pointer=self.pointer,
            content_hash=stable_hash({"content": self.content}),
            retrieved_at=utc_now_iso(),
            freshness=self.freshness,
            authority_scope=self.authority_scope,
        )


class InMemoryRetrievalIndex:
    def __init__(self, records: Iterable[RetrievalRecord] = ()) -> None:
        self.records = tuple(records)

    def search(self, query: str, allowed_sources: Sequence[str]) -> tuple[EvidencePointer, ...]:
        allowed = {source.lower() for source in allowed_sources}
        terms = {term.strip().lower() for term in query.split() if term.strip()}
        matches = []
        for record in self.records:
            if record.source_type.lower() not in allowed:
                continue
            content = record.content.lower()
            pointer = record.pointer.lower()
            if not terms or any(term in content or term in pointer for term in terms):
                matches.append(record.to_evidence_pointer())
        return tuple(matches)


def default_fixture_index() -> InMemoryRetrievalIndex:
    return InMemoryRetrievalIndex(
        (
            RetrievalRecord(
                source_type="receipt_index",
                pointer="receipt-index/example-001",
                content="A prior answer can be reconstructed from receipt data.",
            ),
            RetrievalRecord(
                source_type="policy_index",
                pointer="policy-index/read-only-v0.1",
                content="Read-only answers can proceed when evidence is current.",
            ),
        )
    )


__all__ = [
    "InMemoryRetrievalIndex",
    "RetrievalRecord",
    "default_fixture_index",
    "stable_hash",
    "utc_now_iso",
]
