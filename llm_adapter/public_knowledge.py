"""Deterministic, credential-free public StegVerse knowledge resolver.

This layer grounds bounded help answers in the committed public knowledge
manifest. It performs no network call, provider call, authority transition, or
repository mutation. Unknown topics return no answer rather than inventing one.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any, Mapping

MANIFEST_PATH = Path(__file__).resolve().parent.parent / "data" / "stegverse-public-knowledge.v1.json"


class PublicKnowledgeError(ValueError):
    pass


@dataclass(frozen=True)
class PublicKnowledgeAnswer:
    entry_id: str
    answer: str
    source_ids: tuple[str, ...]
    source_refs: tuple[Mapping[str, Any], ...]
    match: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": "PUBLIC_KNOWLEDGE_GROUNDED",
            "entry_id": self.entry_id,
            "answer": self.answer,
            "source_ids": list(self.source_ids),
            "source_refs": [dict(item) for item in self.source_refs],
            "match": self.match,
            "model_memory_used_as_source": False,
            "network_retrieval_required": False,
            "authority_effect": False,
            "publication_authority": False,
        }


def load_manifest(path: Path = MANIFEST_PATH) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise PublicKnowledgeError(f"public_knowledge_manifest_unavailable:{exc}") from exc
    except json.JSONDecodeError as exc:
        raise PublicKnowledgeError("public_knowledge_manifest_invalid_json") from exc
    validate_manifest(value)
    return value


def validate_manifest(value: Mapping[str, Any]) -> None:
    if value.get("schema") != "stegverse.public-knowledge.v1":
        raise PublicKnowledgeError("unsupported_public_knowledge_schema")
    if value.get("authority_effect") is not False:
        raise PublicKnowledgeError("public_knowledge_must_not_grant_authority")
    if value.get("publication_authority") is not False:
        raise PublicKnowledgeError("public_knowledge_must_not_grant_publication_authority")
    if value.get("model_memory_is_source") is not False:
        raise PublicKnowledgeError("model_memory_must_not_be_public_knowledge_source")
    sources = value.get("sources")
    entries = value.get("entries")
    if not isinstance(sources, list) or not isinstance(entries, list) or not entries:
        raise PublicKnowledgeError("public_knowledge_sources_and_entries_required")
    source_ids: set[str] = set()
    for source in sources:
        if not isinstance(source, Mapping):
            raise PublicKnowledgeError("public_knowledge_source_invalid")
        source_id = source.get("source_id")
        if not isinstance(source_id, str) or not source_id or source_id in source_ids:
            raise PublicKnowledgeError("public_knowledge_source_id_invalid_or_duplicate")
        if source.get("public") is not True:
            raise PublicKnowledgeError(f"non_public_source_rejected:{source_id}")
        if not source.get("repository") or not source.get("path"):
            raise PublicKnowledgeError(f"source_reference_incomplete:{source_id}")
        source_ids.add(source_id)
    entry_ids: set[str] = set()
    for entry in entries:
        if not isinstance(entry, Mapping):
            raise PublicKnowledgeError("public_knowledge_entry_invalid")
        entry_id = entry.get("id")
        triggers = entry.get("triggers")
        refs = entry.get("source_ids")
        if not isinstance(entry_id, str) or not entry_id or entry_id in entry_ids:
            raise PublicKnowledgeError("public_knowledge_entry_id_invalid_or_duplicate")
        if not isinstance(entry.get("answer"), str) or not entry["answer"].strip():
            raise PublicKnowledgeError(f"public_knowledge_answer_missing:{entry_id}")
        if not isinstance(triggers, list) or not triggers or not all(isinstance(item, str) and item.strip() for item in triggers):
            raise PublicKnowledgeError(f"public_knowledge_triggers_invalid:{entry_id}")
        if not isinstance(refs, list) or not refs or any(ref not in source_ids for ref in refs):
            raise PublicKnowledgeError(f"public_knowledge_source_reference_invalid:{entry_id}")
        entry_ids.add(entry_id)


def _normalize(text: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text.lower()).split())


def resolve_public_question(question: str, manifest: Mapping[str, Any] | None = None) -> PublicKnowledgeAnswer | None:
    clean = question.strip()
    if not clean:
        return None
    data = dict(manifest) if manifest is not None else load_manifest()
    validate_manifest(data)
    normalized = _normalize(clean)
    source_map = {source["source_id"]: source for source in data["sources"]}

    best: tuple[int, int, Mapping[str, Any], str] | None = None
    for entry_index, entry in enumerate(data["entries"]):
        for trigger in entry["triggers"]:
            needle = _normalize(trigger)
            if not needle:
                continue
            if needle == normalized:
                score = 10000 + len(needle)
            elif needle in normalized:
                score = 5000 + len(needle)
            else:
                terms = set(needle.split())
                overlap = len(terms.intersection(normalized.split()))
                score = overlap * 100 - len(terms.difference(normalized.split()))
            candidate = (score, -entry_index, entry, trigger)
            if best is None or candidate[:2] > best[:2]:
                best = candidate

    if best is None or best[0] < 150:
        return None
    entry = best[2]
    refs = tuple(source_map[source_id] for source_id in entry["source_ids"])
    return PublicKnowledgeAnswer(
        entry_id=str(entry["id"]),
        answer=str(entry["answer"]),
        source_ids=tuple(str(item) for item in entry["source_ids"]),
        source_refs=refs,
        match=str(best[3]),
    )


__all__ = [
    "MANIFEST_PATH",
    "PublicKnowledgeAnswer",
    "PublicKnowledgeError",
    "load_manifest",
    "resolve_public_question",
    "validate_manifest",
]
