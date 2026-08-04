"""Provider-neutral session binding for governed StegVerse chat LLM profiles.

The binding layer turns a validated Chat LLM profile, messages, requested
capabilities, candidate tools, and source metadata into a deterministic provider-
ready envelope. It performs no network calls, requests no provider permission,
and executes no tool or other side effect.

VA Claims Chat applies the same LLM capability surface as Ecosystem Chat while
failing closed when required factual grounding is not an admitted official VA
source or a privacy-approved, separately labeled user-record fact.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Sequence, Tuple

from .chat_profiles import (
    ChatLLMProfile,
    SourceCandidate,
    SourceDecision,
    load_profile,
    manifest_sha256,
    validate_profile_manifest,
    evaluate_source,
)


ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATHS = {
    "ecosystem-chat-llm": ROOT / "profiles" / "ecosystem-chat-llm.v1.json",
    "va-claims-chat-llm": ROOT / "profiles" / "va-claims-chat-llm.v1.json",
}

ALLOWED_MESSAGE_ROLES = {"system", "developer", "user", "assistant", "tool"}
ALLOWED_RESPONSE_FORMATS = {"text", "json", "json_schema", "artifact"}


class SessionBindingError(ValueError):
    """Raised when a session request violates the profile binding contract."""


@dataclass(frozen=True)
class PreparedSession:
    """Deterministic session-preparation result."""

    state: str
    blockers: Tuple[str, ...]
    envelope: Mapping[str, Any] | None
    receipt: Mapping[str, Any]


@dataclass(frozen=True)
class CandidateValidation:
    """Candidate-response validation result."""

    state: str
    reasons: Tuple[str, ...]
    receipt: Mapping[str, Any]


def canonical_json(value: Any) -> bytes:
    """Encode a JSON-compatible value deterministically."""

    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return sha256(canonical_json(value)).hexdigest()


def _load_profile_manifest(profile_id: str) -> tuple[ChatLLMProfile, Mapping[str, Any]]:
    path = PROFILE_PATHS.get(profile_id)
    if path is None:
        raise SessionBindingError("unknown_profile_id")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(manifest, Mapping):
        raise SessionBindingError("profile_manifest_root_must_be_object")
    return validate_profile_manifest(manifest), manifest


def _normalize_messages(raw_messages: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_messages, Sequence) or isinstance(raw_messages, (str, bytes)):
        raise SessionBindingError("messages_must_be_array")
    messages: list[dict[str, Any]] = []
    saw_user = False
    for index, raw in enumerate(raw_messages):
        if not isinstance(raw, Mapping):
            raise SessionBindingError(f"message_{index}_must_be_object")
        role = str(raw.get("role", "")).strip()
        content = raw.get("content")
        if role not in ALLOWED_MESSAGE_ROLES:
            raise SessionBindingError(f"message_{index}_role_invalid")
        if not isinstance(content, str) or not content.strip():
            raise SessionBindingError(f"message_{index}_content_required")
        if role == "user":
            saw_user = True
        normalized: dict[str, Any] = {
            "role": role,
            "content": content,
        }
        if raw.get("name") is not None:
            name = str(raw["name"]).strip()
            if not name:
                raise SessionBindingError(f"message_{index}_name_invalid")
            normalized["name"] = name
        messages.append(normalized)
    if not messages:
        raise SessionBindingError("at_least_one_message_required")
    if not saw_user:
        raise SessionBindingError("at_least_one_user_message_required")
    return messages


def _normalize_requested_features(
    profile: ChatLLMProfile,
    requested: Any,
) -> list[str]:
    if requested is None:
        return list(profile.features)
    if not isinstance(requested, Sequence) or isinstance(requested, (str, bytes)):
        raise SessionBindingError("requested_features_must_be_array")
    features = [str(item) for item in requested]
    if not features or any(not item for item in features):
        raise SessionBindingError("requested_features_must_be_non_empty")
    if len(features) != len(set(features)):
        raise SessionBindingError("requested_features_must_be_unique")
    unsupported = sorted(set(features) - set(profile.features))
    if unsupported:
        raise SessionBindingError(
            "unsupported_requested_features:" + ",".join(unsupported)
        )
    return features


def _normalize_tools(raw_tools: Any) -> list[dict[str, Any]]:
    if raw_tools is None:
        return []
    if not isinstance(raw_tools, Sequence) or isinstance(raw_tools, (str, bytes)):
        raise SessionBindingError("tools_must_be_array")
    tools: list[dict[str, Any]] = []
    names: set[str] = set()
    for index, raw in enumerate(raw_tools):
        if not isinstance(raw, Mapping):
            raise SessionBindingError(f"tool_{index}_must_be_object")
        name = str(raw.get("name", "")).strip()
        description = str(raw.get("description", "")).strip()
        input_schema = raw.get("input_schema")
        if not name:
            raise SessionBindingError(f"tool_{index}_name_required")
        if name in names:
            raise SessionBindingError("tool_names_must_be_unique")
        if not description:
            raise SessionBindingError(f"tool_{index}_description_required")
        if not isinstance(input_schema, Mapping):
            raise SessionBindingError(f"tool_{index}_input_schema_required")
        names.add(name)
        tools.append(
            {
                "name": name,
                "description": description,
                "input_schema": dict(input_schema),
                "execution_state": "CANDIDATE_ONLY_NOT_EXECUTED",
                "execution_authority": False,
            }
        )
    return tools


def _source_candidate(raw: Mapping[str, Any]) -> SourceCandidate:
    return SourceCandidate(
        source_type=str(raw.get("source_type", "")),
        uri=str(raw.get("uri", "")),
        admitted=raw.get("admitted") is True,
        authority_class=str(raw.get("authority_class", "")),
        privacy_status=str(raw.get("privacy_status", "NOT_APPLICABLE")),
        consent_present=raw.get("consent_present") is True,
        content_hash=str(raw.get("content_hash", "")),
    )


def _normalize_sources(
    profile: ChatLLMProfile,
    raw_sources: Any,
) -> tuple[list[dict[str, Any]], list[str]]:
    if raw_sources is None:
        return [], []
    if not isinstance(raw_sources, Sequence) or isinstance(raw_sources, (str, bytes)):
        raise SessionBindingError("sources_must_be_array")
    records: list[dict[str, Any]] = []
    required_blockers: list[str] = []
    source_ids: set[str] = set()
    for index, raw in enumerate(raw_sources):
        if not isinstance(raw, Mapping):
            raise SessionBindingError(f"source_{index}_must_be_object")
        source_id = str(raw.get("source_id", "")).strip()
        if not source_id:
            raise SessionBindingError(f"source_{index}_source_id_required")
        if source_id in source_ids:
            raise SessionBindingError("source_ids_must_be_unique")
        source_ids.add(source_id)
        candidate = _source_candidate(raw)
        decision: SourceDecision = evaluate_source(profile, candidate)
        required = raw.get("required_for_answer") is True
        if required and not decision.allowed_for_factual_grounding:
            required_blockers.append(
                f"required_source_denied:{source_id}:" + ",".join(decision.reasons)
            )
        source_metadata = {
            "source_id": source_id,
            "source_type": candidate.source_type,
            "uri": candidate.uri,
            "admitted": candidate.admitted,
            "authority_class": candidate.authority_class,
            "privacy_status": candidate.privacy_status,
            "consent_present": candidate.consent_present,
            "content_hash": candidate.content_hash,
            "required_for_answer": required,
        }
        records.append(
            {
                **source_metadata,
                "source_metadata_sha256": canonical_sha256(source_metadata),
                "decision": {
                    "status": decision.status,
                    "allowed_for_factual_grounding": decision.allowed_for_factual_grounding,
                    "allowed_as_authority": decision.allowed_as_authority,
                    "fact_label": decision.fact_label,
                    "reasons": list(decision.reasons),
                    "normalized_host": decision.normalized_host,
                },
            }
        )
    return records, required_blockers


def _policy_instructions(profile: ChatLLMProfile) -> list[str]:
    instructions = [
        "Preserve the complete requested LLM capability surface.",
        "Use only source records marked allowed_for_factual_grounding for factual claims.",
        "Label factual claims with the exact source decision fact_label.",
        "Treat tools and actions as candidates only; do not claim execution.",
        "Do not claim authority, admissibility, custody, publication, filing, or activation.",
    ]
    if profile.profile_id == "va-claims-chat-llm":
        instructions.extend(
            [
                "Use admitted official va.gov sources for external VA factual claims.",
                "Use privacy-approved user records only as separately labeled user_record_fact.",
                "Do not use general web or model memory as VA factual support.",
                "Do not invent diagnosis, nexus, rating, effective date, adjudication, or filing authority.",
            ]
        )
    return instructions


def prepare_session(
    request: Mapping[str, Any],
) -> PreparedSession:
    """Prepare a deterministic provider-neutral LLM session envelope."""

    if not isinstance(request, Mapping):
        raise SessionBindingError("request_must_be_object")
    profile_id = str(request.get("profile_id", "")).strip()
    profile, profile_manifest = _load_profile_manifest(profile_id)
    messages = _normalize_messages(request.get("messages"))
    requested_features = _normalize_requested_features(
        profile, request.get("requested_features")
    )
    tools = _normalize_tools(request.get("tools"))
    sources, required_source_blockers = _normalize_sources(
        profile, request.get("sources")
    )
    response_format = str(request.get("response_format", "text"))
    if response_format not in ALLOWED_RESPONSE_FORMATS:
        raise SessionBindingError("response_format_invalid")

    requires_factual_grounding = request.get("requires_factual_grounding")
    if requires_factual_grounding is None:
        requires_factual_grounding = profile.profile_id == "va-claims-chat-llm"
    if not isinstance(requires_factual_grounding, bool):
        raise SessionBindingError("requires_factual_grounding_must_be_boolean")

    allowed_sources = [
        source
        for source in sources
        if source["decision"]["allowed_for_factual_grounding"] is True
    ]
    blockers = list(required_source_blockers)
    if requires_factual_grounding and not allowed_sources:
        blockers.append("factual_grounding_required_but_no_allowed_source")

    request_projection = {
        "profile_id": profile.profile_id,
        "profile_manifest_sha256": manifest_sha256(profile_manifest),
        "messages": messages,
        "requested_features": requested_features,
        "tools": tools,
        "response_format": response_format,
        "requires_factual_grounding": requires_factual_grounding,
        "sources": sources,
    }
    request_sha256 = canonical_sha256(request_projection)

    receipt: Dict[str, Any] = {
        "schema": "stegverse.chat_llm_session_preparation.v1",
        "state": "BLOCKED_SOURCE_POLICY" if blockers else "READY_FOR_PROVIDER_BINDING",
        "profile_id": profile.profile_id,
        "profile_manifest_sha256": request_projection["profile_manifest_sha256"],
        "request_sha256": request_sha256,
        "requested_feature_count": len(requested_features),
        "declared_profile_feature_count": len(profile.features),
        "message_count": len(messages),
        "candidate_tool_count": len(tools),
        "source_count": len(sources),
        "allowed_grounding_source_count": len(allowed_sources),
        "blockers": blockers,
        "provider_call_performed": False,
        "tools_executed": False,
        "authority_effect": False,
        "activation_effect": False,
    }

    if blockers:
        receipt["receipt_sha256"] = canonical_sha256(receipt)
        return PreparedSession(
            state="BLOCKED_SOURCE_POLICY",
            blockers=tuple(blockers),
            envelope=None,
            receipt=receipt,
        )

    envelope: Dict[str, Any] = {
        "schema": "stegverse.chat_llm_session_envelope.v1",
        "state": "READY_FOR_PROVIDER_BINDING",
        "profile": {
            "profile_id": profile.profile_id,
            "display_name": profile.display_name,
            "purpose": profile.purpose,
            "llm_surface": profile.llm_surface,
            "profile_manifest_sha256": request_projection["profile_manifest_sha256"],
        },
        "messages": messages,
        "requested_features": requested_features,
        "response_format": response_format,
        "candidate_tools": tools,
        "grounding_sources": allowed_sources,
        "source_decisions": sources,
        "policy_instructions": _policy_instructions(profile),
        "return_contract": {
            "require_source_ids_for_factual_claims": requires_factual_grounding,
            "require_fact_labels": True,
            "require_candidate_tool_status": "CANDIDATE_NOT_EXECUTED",
            "side_effects_executed": False,
            "authority_claimed": False,
        },
        "request_sha256": request_sha256,
        "provider_configuration_attached": False,
        "provider_permission_requested": False,
        "provider_call_performed": False,
        "tools_executed": False,
        "authority_effect": False,
        "activation_effect": False,
    }
    envelope["envelope_sha256"] = canonical_sha256(envelope)
    receipt["envelope_sha256"] = envelope["envelope_sha256"]
    receipt["receipt_sha256"] = canonical_sha256(receipt)
    return PreparedSession(
        state="READY_FOR_PROVIDER_BINDING",
        blockers=(),
        envelope=envelope,
        receipt=receipt,
    )


def _allowed_source_map(envelope: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    sources = envelope.get("grounding_sources")
    if not isinstance(sources, Sequence) or isinstance(sources, (str, bytes)):
        raise SessionBindingError("envelope_grounding_sources_invalid")
    result: dict[str, Mapping[str, Any]] = {}
    for source in sources:
        if not isinstance(source, Mapping):
            raise SessionBindingError("envelope_grounding_source_invalid")
        source_id = str(source.get("source_id", ""))
        if not source_id:
            raise SessionBindingError("envelope_grounding_source_id_missing")
        result[source_id] = source
    return result


def validate_candidate_response(
    envelope: Mapping[str, Any],
    candidate: Mapping[str, Any],
) -> CandidateValidation:
    """Validate a provider candidate without treating it as executed or authoritative."""

    if envelope.get("state") != "READY_FOR_PROVIDER_BINDING":
        raise SessionBindingError("envelope_not_ready")
    if not isinstance(candidate, Mapping):
        raise SessionBindingError("candidate_must_be_object")

    reasons: list[str] = []
    text = candidate.get("text")
    if not isinstance(text, str) or not text.strip():
        reasons.append("candidate_text_required")

    allowed_sources = _allowed_source_map(envelope)
    citations = candidate.get("citations", [])
    if not isinstance(citations, Sequence) or isinstance(citations, (str, bytes)):
        reasons.append("citations_must_be_array")
        citations = []
    citation_ids = [str(item) for item in citations]
    unknown_citations = sorted(set(citation_ids) - set(allowed_sources))
    if unknown_citations:
        reasons.append("unknown_citations:" + ",".join(unknown_citations))

    factual_claims = candidate.get("factual_claims", [])
    if not isinstance(factual_claims, Sequence) or isinstance(
        factual_claims, (str, bytes)
    ):
        reasons.append("factual_claims_must_be_array")
        factual_claims = []
    for index, claim in enumerate(factual_claims):
        if not isinstance(claim, Mapping):
            reasons.append(f"factual_claim_{index}_must_be_object")
            continue
        source_id = str(claim.get("source_id", ""))
        fact_label = str(claim.get("fact_label", ""))
        source = allowed_sources.get(source_id)
        if source is None:
            reasons.append(f"factual_claim_{index}_source_not_allowed")
            continue
        expected_label = str(source["decision"].get("fact_label", ""))
        if fact_label != expected_label:
            reasons.append(f"factual_claim_{index}_fact_label_mismatch")
        if source_id not in citation_ids:
            reasons.append(f"factual_claim_{index}_citation_missing")

    declared_tools = {
        str(tool.get("name", ""))
        for tool in envelope.get("candidate_tools", [])
        if isinstance(tool, Mapping)
    }
    tool_calls = candidate.get("tool_calls", [])
    if not isinstance(tool_calls, Sequence) or isinstance(tool_calls, (str, bytes)):
        reasons.append("tool_calls_must_be_array")
        tool_calls = []
    for index, tool_call in enumerate(tool_calls):
        if not isinstance(tool_call, Mapping):
            reasons.append(f"tool_call_{index}_must_be_object")
            continue
        name = str(tool_call.get("name", ""))
        status = str(tool_call.get("status", ""))
        if name not in declared_tools:
            reasons.append(f"tool_call_{index}_undeclared_tool")
        if status != "CANDIDATE_NOT_EXECUTED":
            reasons.append(f"tool_call_{index}_execution_status_invalid")

    if candidate.get("side_effects_executed") is not False:
        reasons.append("side_effects_must_remain_false")
    if candidate.get("authority_claimed") is not False:
        reasons.append("authority_claimed_must_remain_false")
    if candidate.get("publication_claimed") is True:
        reasons.append("publication_claim_not_allowed")
    if candidate.get("custody_claimed") is True:
        reasons.append("custody_claim_not_allowed")

    state = "ACCEPT_CANDIDATE" if not reasons else "REJECT_CANDIDATE"
    candidate_projection = {
        "text": text if isinstance(text, str) else "",
        "citations": citation_ids,
        "factual_claims": list(factual_claims),
        "tool_calls": list(tool_calls),
        "side_effects_executed": candidate.get("side_effects_executed"),
        "authority_claimed": candidate.get("authority_claimed"),
        "publication_claimed": candidate.get("publication_claimed", False),
        "custody_claimed": candidate.get("custody_claimed", False),
    }
    receipt: Dict[str, Any] = {
        "schema": "stegverse.chat_llm_candidate_validation.v1",
        "state": state,
        "profile_id": envelope.get("profile", {}).get("profile_id"),
        "envelope_sha256": envelope.get("envelope_sha256"),
        "candidate_sha256": canonical_sha256(candidate_projection),
        "citation_count": len(citation_ids),
        "factual_claim_count": len(factual_claims),
        "candidate_tool_call_count": len(tool_calls),
        "reasons": reasons,
        "provider_output_is_authority": False,
        "tools_executed": False,
        "authority_effect": False,
        "activation_effect": False,
    }
    receipt["receipt_sha256"] = canonical_sha256(receipt)
    return CandidateValidation(
        state=state,
        reasons=tuple(reasons),
        receipt=receipt,
    )
