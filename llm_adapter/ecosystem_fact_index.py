"""Exact-identifier fact index over caller-supplied ecosystem registries.

This module answers "what does the registry say about X?" for a small set of
ecosystem registries, citing the exact line of the supplied bytes. It is owned
by SHWP-ECOSYSTEM-CHAT-INFERENCE-001 (SV-LLM side SVORG-LLM-ORG-FOUNDATION-001).

Supported sources (``repository`` / ``path``):

* ``SV-LLM/.github`` / ``data/organization-tree.json`` -- indexes
  ``repositories[*].name`` as ``organization_entity`` facts (value: ``name``,
  ``class``, ``role`` and ``authority_effect`` when they are scalars).
* ``StegVerse-Labs/.github`` / ``data/canonical-task-registry.json`` -- indexes
  top-level ``tasks[*].task_id`` as ``canonical_task`` facts (value:
  ``task_id``, ``coordination_state``, ``goal``, ``parent_task_id``,
  ``root_correlation_id`` when present). Nested task references are not indexed.
* ``StegVerse-Labs/.github`` / ``data/reusable-task-registry.json`` -- indexes
  ``tasks[*].reusable_task_id`` as ``reusable_task`` facts (value:
  ``reusable_task_id``, ``name``, ``purpose`` when present).
* ``StegVerse-Labs/.github`` / ``data/task-registry-global-invariants.json`` --
  indexes every key of the top-level ``invariants`` object as
  ``global_invariant`` facts (value: the invariant key, its JSON value and the
  ``invariant_set_id``).

Nothing is fetched: no network, no subprocess, and no file reads except in
``load_source_manifest``, which reads only the manifest and files the caller
names. ``build_index`` refuses (fail closed, whole build) any source whose bytes
do not hash to the declared sha256, any unsupported source, any document whose
schema is not recognized, any document that repeats a key within one JSON
object (registries must be unambiguous) and any document nested deeper than
``_MAX_DEPTH`` containers. ``lookup`` matches the query string exactly as given
(case-sensitive, no whitespace stripping); it never guesses, normalizes or
fuzzy-matches. Every answer is
classed ``OBSERVED`` and cites ``repository@revision:path:line`` where ``line``
is the 1-based line of the supplied bytes on which the matched key appears.
"""
from __future__ import annotations

import bisect
from dataclasses import dataclass, field
from hashlib import sha256
import json
from json.decoder import scanstring
from json.scanner import NUMBER_RE
from pathlib import Path
import re
from typing import Any, Mapping, Sequence

OWNING_GOAL = "SHWP-ECOSYSTEM-CHAT-INFERENCE-001"
BUILD_ENTRYPOINT = "llm_adapter.ecosystem_fact_index.build_index"
MANIFEST_ENTRYPOINT = "llm_adapter.ecosystem_fact_index.load_source_manifest"
LOOKUP_ENTRYPOINT = "llm_adapter.ecosystem_fact_index.lookup"
SOURCE_MANIFEST_SCHEMA = "stegverse.ecosystem-fact-sources/v1"
EVIDENCE_CLASS = "OBSERVED"

SUPPORTED_SOURCES: Mapping[tuple[str, str], str] = {
    ("SV-LLM/.github", "data/organization-tree.json"): "organization_tree",
    ("StegVerse-Labs/.github", "data/canonical-task-registry.json"): "canonical_task_registry",
    ("StegVerse-Labs/.github", "data/reusable-task-registry.json"): "reusable_task_registry",
    ("StegVerse-Labs/.github", "data/task-registry-global-invariants.json"): "task_registry_global_invariants",
}

_SCHEMA_PREFIX = {
    "organization_tree": "sv-llm.organization-tree/",
    "canonical_task_registry": "stegverse.canonical-task-registry/",
    "reusable_task_registry": "stegverse.reusable-task-registry/",
    "task_registry_global_invariants": "stegverse.task-registry-global-invariants/",
}

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_WS_RE = re.compile(r"[ \t\n\r]*")
# Maximum number of nested JSON containers (objects/arrays) in a registry.
# Each level costs two Python frames in the line-tracking parser
# (``parse_value`` plus ``parse_object``/``parse_array``), so the bound must sit
# well below half the interpreter recursion limit. A RecursionError raised
# anyway is still converted into a refusal by ``build_index``.
_MAX_DEPTH = 128


class EcosystemFactSourceConfigError(ValueError):
    """Raised when a caller-named source manifest cannot be loaded."""


@dataclass(frozen=True)
class EcosystemFact:
    kind: str
    key: str
    value: Any
    repository: str
    path: str
    revision: str
    sha256: str
    line: int

    @property
    def citation(self) -> str:
        return f"{self.repository}@{self.revision}:{self.path}:{self.line}"


@dataclass(frozen=True)
class EcosystemFactIndex:
    sources: tuple[Mapping[str, str], ...]
    facts: Mapping[str, tuple[EcosystemFact, ...]] = field(repr=False)

    def keys(self) -> tuple[str, ...]:
        return tuple(sorted(self.facts))


@dataclass(frozen=True)
class IndexBuildResult:
    status: str
    index: EcosystemFactIndex | None
    refusal: Mapping[str, Any] | None

    def to_dict(self) -> dict[str, Any]:
        if self.status == "ALLOW" and self.index is not None:
            return {
                "status": "ALLOW",
                "sources": [dict(item) for item in self.index.sources],
                "fact_count": sum(len(items) for items in self.index.facts.values()),
            }
        return dict(self.refusal or {})


# --------------------------------------------------------------------------
# Line-aware JSON parsing (standard library primitives only)
# --------------------------------------------------------------------------


class _LocatedDict(dict):
    """dict that also records the 1-based line on which each key appeared."""

    __slots__ = ("key_lines",)

    def __init__(self) -> None:
        super().__init__()
        self.key_lines: dict[str, int] = {}


class _ParseError(ValueError):
    pass


class _NestingTooDeep(_ParseError):
    pass


class _DuplicateKey(_ParseError):
    pass


def _parse_located_json(text: str) -> Any:
    newlines = [match.start() for match in re.finditer("\n", text)]
    length = len(text)

    def line_of(pos: int) -> int:
        return bisect.bisect_left(newlines, pos) + 1

    def skip(pos: int) -> int:
        return _WS_RE.match(text, pos).end()

    def parse_value(pos: int, depth: int) -> tuple[Any, int]:
        pos = skip(pos)
        char = text[pos:pos + 1]
        if char in ("{", "[") and depth + 1 > _MAX_DEPTH:
            raise _NestingTooDeep(f"json_nesting_exceeds_{_MAX_DEPTH}_at_line_{line_of(pos)}")
        if char == "{":
            return parse_object(pos + 1, depth + 1)
        if char == "[":
            return parse_array(pos + 1, depth + 1)
        if char == '"':
            return scanstring(text, pos + 1, True)
        for literal, value in (("null", None), ("true", True), ("false", False)):
            if text.startswith(literal, pos):
                return value, pos + len(literal)
        match = NUMBER_RE.match(text, pos)
        if match and match.end() > pos:
            integer, frac, exp = match.groups()
            if frac or exp:
                return float(integer + (frac or "") + (exp or "")), match.end()
            return int(integer), match.end()
        raise _ParseError(f"unexpected_json_token_at_line_{line_of(pos)}")

    def parse_object(pos: int, depth: int) -> tuple[_LocatedDict, int]:
        result = _LocatedDict()
        pos = skip(pos)
        if text[pos:pos + 1] == "}":
            return result, pos + 1
        while True:
            if text[pos:pos + 1] != '"':
                raise _ParseError(f"expected_object_key_at_line_{line_of(pos)}")
            key_pos = pos
            key, pos = scanstring(text, pos + 1, True)
            pos = skip(pos)
            if text[pos:pos + 1] != ":":
                raise _ParseError(f"expected_colon_at_line_{line_of(pos)}")
            if key in result:
                raise _DuplicateKey(f"duplicate_object_key_{json.dumps(key)}_at_line_{line_of(key_pos)}")
            value, pos = parse_value(pos + 1, depth)
            result[key] = value
            result.key_lines[key] = line_of(key_pos)
            pos = skip(pos)
            char = text[pos:pos + 1]
            if char == ",":
                pos = skip(pos + 1)
                continue
            if char == "}":
                return result, pos + 1
            raise _ParseError(f"expected_object_separator_at_line_{line_of(pos)}")

    def parse_array(pos: int, depth: int) -> tuple[list[Any], int]:
        items: list[Any] = []
        pos = skip(pos)
        if text[pos:pos + 1] == "]":
            return items, pos + 1
        while True:
            value, pos = parse_value(pos, depth)
            items.append(value)
            pos = skip(pos)
            char = text[pos:pos + 1]
            if char == ",":
                pos += 1
                continue
            if char == "]":
                return items, pos + 1
            raise _ParseError(f"expected_array_separator_at_line_{line_of(pos)}")

    try:
        value, end = parse_value(0, 0)
    except json.JSONDecodeError as exc:
        raise _ParseError(f"invalid_json_string:{exc.msg}") from exc
    if skip(end) != length:
        raise _ParseError(f"trailing_data_at_line_{line_of(end)}")
    return value


def _plain(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_plain(item) for item in value]
    return value


def _scalar_fields(entry: Mapping[str, Any], names: Sequence[str]) -> dict[str, Any]:
    return {
        name: entry[name]
        for name in names
        if name in entry and (entry[name] is None or isinstance(entry[name], (str, int, float, bool)))
    }


# --------------------------------------------------------------------------
# Refusals
# --------------------------------------------------------------------------


def _refusal(
    failure_code: str,
    failed_predicate: str,
    required_evidence_or_repair: str,
    next_attempt: str,
    *,
    source: Mapping[str, Any] | None = None,
    detail: str = "",
    retry_entrypoint: str = BUILD_ENTRYPOINT,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "status": "REFUSED",
        "failure_code": failure_code,
        "failed_predicate": failed_predicate,
        "required_evidence_or_repair": required_evidence_or_repair,
        "retry_entrypoint": retry_entrypoint,
        "owning_existing_goal": OWNING_GOAL,
        "next_attempt": next_attempt,
        "authority_effect": "NONE",
    }
    if source is not None:
        record["source"] = dict(source)
    if detail:
        record["detail"] = detail
    return record


def _refused(record: dict[str, Any]) -> IndexBuildResult:
    return IndexBuildResult(status="REFUSED", index=None, refusal=record)


def _source_label(source: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "repository": source.get("repository"),
        "path": source.get("path"),
        "revision": source.get("revision"),
        "declared_sha256": source.get("sha256"),
    }


def _normalize_digest(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text.startswith("sha256:"):
        text = text[len("sha256:"):]
    return text


# --------------------------------------------------------------------------
# Index construction
# --------------------------------------------------------------------------


def _facts_for(kind: str, document: Any) -> list[tuple[str, str, Any, int]] | None:
    """Return (fact_kind, key, value, line) tuples, or None if the shape is unrecognized."""

    if not isinstance(document, _LocatedDict):
        return None
    schema = document.get("schema")
    if not isinstance(schema, str) or not schema.startswith(_SCHEMA_PREFIX[kind]):
        return None
    facts: list[tuple[str, str, Any, int]] = []
    if kind == "organization_tree":
        entries = document.get("repositories")
        if not isinstance(entries, list):
            return None
        for entry in entries:
            if isinstance(entry, _LocatedDict) and isinstance(entry.get("name"), str) and entry["name"]:
                value = _scalar_fields(entry, ("name", "class", "role", "authority_effect"))
                facts.append(("organization_entity", entry["name"], value, entry.key_lines["name"]))
    elif kind in {"canonical_task_registry", "reusable_task_registry"}:
        entries = document.get("tasks")
        if not isinstance(entries, list):
            return None
        if kind == "canonical_task_registry":
            id_field, fact_kind = "task_id", "canonical_task"
            fields = ("task_id", "coordination_state", "goal", "parent_task_id", "root_correlation_id")
        else:
            id_field, fact_kind = "reusable_task_id", "reusable_task"
            fields = ("reusable_task_id", "name", "purpose")
        for entry in entries:
            if isinstance(entry, _LocatedDict) and isinstance(entry.get(id_field), str) and entry[id_field]:
                value = _scalar_fields(entry, fields)
                facts.append((fact_kind, entry[id_field], value, entry.key_lines[id_field]))
    elif kind == "task_registry_global_invariants":
        invariants = document.get("invariants")
        if not isinstance(invariants, _LocatedDict):
            return None
        set_id = document.get("invariant_set_id")
        for key, raw in invariants.items():
            value = {"invariant_key": key, "value": _plain(raw)}
            if isinstance(set_id, str):
                value["invariant_set_id"] = set_id
            facts.append(("global_invariant", key, value, invariants.key_lines[key]))
    return facts


def build_index(sources: Sequence[Mapping[str, Any]]) -> IndexBuildResult:
    """Build an exact-identifier index from caller-supplied registry bytes.

    Each source is a mapping with ``repository``, ``path``, ``revision``,
    ``sha256`` (64 lowercase hex, optional ``sha256:`` prefix) and ``bytes``.
    Any failing source refuses the whole build; no partial index is returned.
    """

    if isinstance(sources, (str, bytes)) or not isinstance(sources, Sequence) or not sources:
        return _refused(_refusal(
            "ECOSYSTEM_FACT_SOURCES_EMPTY",
            "AT_LEAST_ONE_SUPPORTED_SOURCE_SUPPLIED",
            "Supply at least one supported registry source with repository, path, revision, sha256 and bytes.",
            "Call build_index with a non-empty sequence of supported sources.",
        ))
    facts: dict[str, list[EcosystemFact]] = {}
    labels: list[Mapping[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for source in sources:
        if not isinstance(source, Mapping):
            return _refused(_refusal(
                "ECOSYSTEM_FACT_SOURCE_INVALID",
                "SOURCE_DECLARATION_COMPLETE",
                "Each source must be a mapping with repository, path, revision, sha256 and bytes.",
                "Re-supply the source as a complete mapping.",
            ))
        label = _source_label(source)
        repository, path, revision = source.get("repository"), source.get("path"), source.get("revision")
        payload = source.get("bytes")
        declared = _normalize_digest(source.get("sha256"))
        if (
            not all(isinstance(item, str) and item.strip() for item in (repository, path, revision))
            or not isinstance(payload, (bytes, bytearray))
            or not _SHA256_RE.match(declared)
        ):
            return _refused(_refusal(
                "ECOSYSTEM_FACT_SOURCE_INVALID",
                "SOURCE_DECLARATION_COMPLETE",
                "Declare non-empty repository, path and revision, a 64-hex sha256, and the registry bytes.",
                "Re-supply the source with every declaration field present.",
                source=label,
            ))
        kind = SUPPORTED_SOURCES.get((repository, path))
        if kind is None:
            return _refused(_refusal(
                "ECOSYSTEM_FACT_SOURCE_UNSUPPORTED",
                "SOURCE_IS_SUPPORTED_REGISTRY",
                "Supply only supported registries: "
                + ", ".join(f"{repo}:{rel}" for repo, rel in SUPPORTED_SOURCES),
                "Remove the unsupported source or extend SUPPORTED_SOURCES under the owning goal.",
                source=label,
            ))
        if (repository, path) in seen:
            return _refused(_refusal(
                "ECOSYSTEM_FACT_SOURCE_DUPLICATE",
                "SOURCE_DECLARED_ONCE",
                "Supply each registry at most once so citations are unambiguous.",
                "Remove the duplicate source declaration.",
                source=label,
            ))
        seen.add((repository, path))
        observed = sha256(bytes(payload)).hexdigest()
        if observed != declared:
            refused = _refusal(
                "ECOSYSTEM_FACT_SOURCE_DIGEST_MISMATCH",
                "REGISTRY_BYTES_MATCH_DECLARED_SHA256",
                "Supply registry bytes whose sha256 equals the declared digest, or declare the digest of the exact bytes being supplied.",
                "Re-read the registry at the declared revision and retry build_index with matching bytes and digest.",
                source=label,
            )
            refused["source"]["observed_sha256"] = observed
            return _refused(refused)
        try:
            document = _parse_located_json(bytes(payload).decode("utf-8"))
        except (_NestingTooDeep, RecursionError) as exc:
            return _refused(_refusal(
                "ECOSYSTEM_FACT_SOURCE_NESTING_TOO_DEEP",
                "REGISTRY_NESTING_WITHIN_BOUND",
                f"Supply registry JSON nested at most {_MAX_DEPTH} objects/arrays deep.",
                "Re-supply the registry bytes with bounded nesting, or extend the bound under the owning goal.",
                source=label,
                detail=str(exc) if isinstance(exc, _NestingTooDeep) else "json_nesting_exhausted_recursion_limit",
            ))
        except _DuplicateKey as exc:
            return _refused(_refusal(
                "ECOSYSTEM_FACT_SOURCE_DUPLICATE_KEY",
                "REGISTRY_OBJECT_KEYS_UNIQUE",
                "Supply registry JSON in which every object key appears at most once; duplicate keys are ambiguous.",
                "Remove the duplicate key from the registry revision and retry build_index with its digest.",
                source=label,
                detail=str(exc),
            ))
        except (UnicodeDecodeError, _ParseError) as exc:
            return _refused(_refusal(
                "ECOSYSTEM_FACT_SOURCE_SCHEMA_UNRECOGNIZED",
                "REGISTRY_SCHEMA_RECOGNIZED",
                "Supply UTF-8 JSON registry bytes.",
                "Re-supply the registry bytes as UTF-8 JSON.",
                source=label,
                detail=str(exc),
            ))
        try:
            extracted = _facts_for(kind, document)
        except RecursionError:
            return _refused(_refusal(
                "ECOSYSTEM_FACT_SOURCE_NESTING_TOO_DEEP",
                "REGISTRY_NESTING_WITHIN_BOUND",
                f"Supply registry JSON nested at most {_MAX_DEPTH} objects/arrays deep.",
                "Re-supply the registry bytes with bounded nesting, or extend the bound under the owning goal.",
                source=label,
                detail="json_nesting_exhausted_recursion_limit",
            ))
        if extracted is None:
            return _refused(_refusal(
                "ECOSYSTEM_FACT_SOURCE_SCHEMA_UNRECOGNIZED",
                "REGISTRY_SCHEMA_RECOGNIZED",
                f"Supply a document whose schema starts with {_SCHEMA_PREFIX[kind]!r} and has the indexed container.",
                "Supply a supported registry revision or extend the indexer for the new schema under the owning goal.",
                source=label,
            ))
        for fact_kind, key, value, line in extracted:
            facts.setdefault(key, []).append(EcosystemFact(
                kind=fact_kind,
                key=key,
                value=value,
                repository=repository,
                path=path,
                revision=revision,
                sha256=observed,
                line=line,
            ))
        labels.append({"repository": repository, "path": path, "revision": revision, "sha256": observed})
    index = EcosystemFactIndex(
        sources=tuple(labels),
        facts={key: tuple(items) for key, items in facts.items()},
    )
    return IndexBuildResult(status="ALLOW", index=index, refusal=None)


# --------------------------------------------------------------------------
# Lookup
# --------------------------------------------------------------------------


def _not_found(query: str, index: EcosystemFactIndex) -> dict[str, Any]:
    return {
        "status": "NOT_FOUND",
        "query": query,
        "failure_code": "ECOSYSTEM_FACT_NOT_FOUND",
        "failed_predicate": "FACT_PRESENT_IN_SUPPLIED_REGISTRIES",
        "required_evidence_or_repair": (
            "Supply a registry revision that contains this exact task id, organization entity name, "
            "invariant key or reusable task id; lookup matches exact identifiers only and infers nothing."
        ),
        "retry_entrypoint": LOOKUP_ENTRYPOINT,
        "owning_existing_goal": OWNING_GOAL,
        "next_attempt": (
            "Retry lookup with the identifier exactly as written in the registry, or rebuild the index "
            "from a registry revision that contains it."
        ),
        "searched_sources": [
            f"{item['repository']}@{item['revision']}:{item['path']}" for item in index.sources
        ],
        "authority_effect": "NONE",
    }


def lookup(index: EcosystemFactIndex, query: str, *, kind: str | None = None) -> dict[str, Any]:
    """Return ANSWER records for an exact identifier, or NOT_FOUND with six fields.

    ``query`` is matched byte-for-byte against indexed keys: no case folding and
    no whitespace stripping, so ``" X"`` does not match ``"X"``. Callers that
    extract identifiers from free text must pass the bare token.
    """

    if not isinstance(index, EcosystemFactIndex):
        raise TypeError("lookup requires an EcosystemFactIndex from build_index")
    clean = query if isinstance(query, str) else ""
    matches = [fact for fact in index.facts.get(clean, ()) if kind is None or fact.kind == kind]
    if not clean or not matches:
        return _not_found(clean, index)
    return {
        "status": "ANSWER",
        "query": clean,
        "evidence_class": EVIDENCE_CLASS,
        "answers": [
            {
                "kind": fact.kind,
                "key": fact.key,
                "value": fact.value,
                "citation": fact.citation,
                "evidence_class": EVIDENCE_CLASS,
                "source": {
                    "repository": fact.repository,
                    "path": fact.path,
                    "revision": fact.revision,
                    "sha256": fact.sha256,
                    "line": fact.line,
                },
            }
            for fact in matches
        ],
        "model_memory_used_as_source": False,
        "network_retrieval_performed": False,
        "authority_effect": "NONE",
    }


# --------------------------------------------------------------------------
# Optional local configuration (reads only caller-named local files)
# --------------------------------------------------------------------------


def load_source_manifest(path: Path) -> list[dict[str, Any]]:
    """Load sources declared by a local manifest the caller names.

    Manifest shape::

        {"schema": "stegverse.ecosystem-fact-sources/v1",
         "sources": [{"repository": ..., "path": ..., "revision": ...,
                      "sha256": ..., "local_path": "relative/or/absolute.json"}]}

    ``local_path`` is resolved against the manifest's directory. The declared
    digest is passed through unchanged so ``build_index`` performs the check.
    """

    manifest_path = Path(path)
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
        raise EcosystemFactSourceConfigError(f"ecosystem_fact_source_manifest_unavailable:{exc}") from exc
    if not isinstance(manifest, dict) or manifest.get("schema") != SOURCE_MANIFEST_SCHEMA:
        raise EcosystemFactSourceConfigError("ecosystem_fact_source_manifest_schema_unsupported")
    entries = manifest.get("sources")
    if not isinstance(entries, list):
        raise EcosystemFactSourceConfigError("ecosystem_fact_source_manifest_sources_required")
    loaded: list[dict[str, Any]] = []
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("local_path"), str):
            raise EcosystemFactSourceConfigError("ecosystem_fact_source_local_path_required")
        local = Path(entry["local_path"])
        if not local.is_absolute():
            local = manifest_path.parent / local
        try:
            payload = local.read_bytes()
        except OSError as exc:
            raise EcosystemFactSourceConfigError(f"ecosystem_fact_source_unreadable:{exc}") from exc
        loaded.append({
            "repository": entry.get("repository"),
            "path": entry.get("path"),
            "revision": entry.get("revision"),
            "sha256": entry.get("sha256"),
            "bytes": payload,
        })
    return loaded


def source_manifest_refusal(error: EcosystemFactSourceConfigError) -> dict[str, Any]:
    """Six-field refusal for a configured manifest that ``load_source_manifest`` rejected.

    ``detail`` carries only the stable error code (the text before the first
    ``:``) so local filesystem paths and OS messages are not echoed.
    """

    code = str(error).split(":", 1)[0] or "ecosystem_fact_source_manifest_unavailable"
    return _refusal(
        "ECOSYSTEM_FACT_SOURCE_MANIFEST_REFUSED",
        "SOURCE_MANIFEST_LOADABLE",
        f"Supply a readable {SOURCE_MANIFEST_SCHEMA} manifest whose sources each name a readable local_path.",
        "Repair the configured manifest and its local files, then retry; the build re-checks every digest.",
        detail=code,
        retry_entrypoint=MANIFEST_ENTRYPOINT,
    )


__all__ = [
    "EVIDENCE_CLASS",
    "EcosystemFact",
    "EcosystemFactIndex",
    "EcosystemFactSourceConfigError",
    "IndexBuildResult",
    "OWNING_GOAL",
    "SUPPORTED_SOURCES",
    "build_index",
    "load_source_manifest",
    "lookup",
    "source_manifest_refusal",
]
