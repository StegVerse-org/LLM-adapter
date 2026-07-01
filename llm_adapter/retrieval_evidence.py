"""Retrieval evidence helpers for governed LLM adapter.

The adapter should pass evidence pointers into the SDK contract instead of
copying full source payloads into every receipt. These helpers create evidence
pointers from local fixture data, receipt references, or future retrieval layers.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Mapping, Optional, Sequence

try:
    from stegverse.governed_llm import EvidencePointer  # type: ignore[import]
except ImportError:  # pragma: no cover
    from .governed_adapter import EvidencePointer  # type: ignore[no-redef]


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def stable_hash(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def evidence_from_payload(
    *,
    source_type: str,
    pointer: str,
    payload: Any,
    freshness: str = "current",
    authority_scope: str = "read",
    retrieved_at: Optional[str] = None,
    notes: str = "",
) -> EvidencePointer:
    """Create an evidence pointer from a payload without retaining the payload."""

    return EvidencePointer(
        source_type=source_type,
        pointer=pointer,
        content_hash=stable_hash(payload),
        retrieved_at=retrieved_at or utc_now_iso(),
        freshness=freshness,
        authority_scope=authority_scope,
        notes=notes,
    )


def evidence_from_fixture(fixture: Mapping[str, Any]) -> EvidencePointer:
    """Create an evidence pointer from a dictionary fixture.

    Expected fixture fields:
    - source_type
    - pointer
    - payload or content_hash
    Optional fixture fields:
    - freshness
    - authority_scope
    - retrieved_at
    - notes
    """

    if "source_type" not in fixture or "pointer" not in fixture:
        raise ValueError("evidence fixture requires source_type and pointer")

    if "content_hash" in fixture:
        content_hash = str(fixture["content_hash"])
    elif "payload" in fixture:
        content_hash = stable_hash(fixture["payload"])
    else:
        raise ValueError("evidence fixture requires payload or content_hash")

    return EvidencePointer(
        source_type=str(fixture["source_type"]),
        pointer=str(fixture["pointer"]),
        content_hash=content_hash,
        retrieved_at=str(fixture.get("retrieved_at") or utc_now_iso()),
        freshness=str(fixture.get("freshness", "current")),
        authority_scope=str(fixture.get("authority_scope", "read")),
        notes=str(fixture.get("notes", "")),
    )


def evidence_list_from_fixtures(fixtures: Sequence[Mapping[str, Any]]) -> tuple[EvidencePointer, ...]:
    return tuple(evidence_from_fixture(fixture) for fixture in fixtures)


__all__ = [
    "evidence_from_payload",
    "evidence_from_fixture",
    "evidence_list_from_fixtures",
    "stable_hash",
]
