"""Governed product profiles for StegVerse chat-based LLMs.

This module separates model capability from consequence authority:

* a profile may expose the complete provider-supported LLM interaction surface;
* source policy determines what may ground factual output;
* downstream governance independently determines whether any tool call or other
  side effect may execute.

The profile engine performs no network calls and grants no execution authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional, Tuple
from urllib.parse import urlparse


FULL_LLM_FEATURES: Tuple[str, ...] = (
    "multi_turn_conversation",
    "system_developer_user_instruction_layers",
    "long_context",
    "streaming_response",
    "structured_output",
    "function_and_tool_calling",
    "retrieval_augmented_generation",
    "web_retrieval",
    "file_understanding",
    "image_understanding",
    "audio_understanding",
    "code_generation",
    "artifact_generation",
    "multilingual_generation",
    "planning_and_multi_step_reasoning",
    "memory_candidate_generation",
    "model_routing",
    "citation_and_provenance_output",
    "candidate_action_generation",
)

ALLOWED_SOURCE_MODES = {"GENERAL_ADMITTED", "OFFICIAL_VA_ONLY"}
ALLOWED_SOURCE_TYPES = {
    "official_external",
    "general_web",
    "stegverse_internal",
    "user_record",
    "model_memory",
}


class ProfileValidationError(ValueError):
    """Raised when a chat LLM profile violates the canonical contract."""


@dataclass(frozen=True)
class ChatLLMProfile:
    """Validated runtime-neutral Chat LLM profile."""

    schema: str
    profile_id: str
    display_name: str
    purpose: str
    llm_surface: str
    features: Tuple[str, ...]
    source_policy: Mapping[str, Any]
    authority_policy: Mapping[str, bool]

    @property
    def has_full_llm_surface(self) -> bool:
        return set(FULL_LLM_FEATURES).issubset(set(self.features))


@dataclass(frozen=True)
class SourceCandidate:
    """Candidate evidence or context offered to an LLM profile."""

    source_type: str
    uri: str = ""
    admitted: bool = False
    authority_class: str = ""
    privacy_status: str = "NOT_APPLICABLE"
    consent_present: bool = False
    content_hash: str = ""


@dataclass(frozen=True)
class SourceDecision:
    """Fail-closed source-policy result."""

    status: str
    allowed_for_factual_grounding: bool
    allowed_as_authority: bool
    fact_label: str
    reasons: Tuple[str, ...]
    normalized_host: str


def _canonical_json(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def manifest_sha256(value: Mapping[str, Any]) -> str:
    """Return a deterministic digest for a profile manifest."""

    return sha256(_canonical_json(value)).hexdigest()


def normalize_host(uri_or_host: str) -> str:
    """Normalize a URL or hostname without accepting lookalike suffixes."""

    raw = uri_or_host.strip().lower()
    if not raw:
        return ""
    parsed = urlparse(raw if "://" in raw else "https://" + raw)
    host = parsed.hostname or ""
    return host.rstrip(".")


def is_official_va_host(uri_or_host: str) -> bool:
    """Return True only for va.gov itself or a genuine va.gov subdomain."""

    host = normalize_host(uri_or_host)
    return host == "va.gov" or host.endswith(".va.gov")


def _require_mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ProfileValidationError(f"{field}_must_be_object")
    return value


def validate_profile_manifest(manifest: Mapping[str, Any]) -> ChatLLMProfile:
    """Validate and normalize a profile manifest.

    Validation is intentionally strict so profile drift cannot silently remove
    an LLM capability or broaden VA Claims sourcing.
    """

    required_strings = (
        "schema",
        "profile_id",
        "display_name",
        "purpose",
        "llm_surface",
    )
    for field in required_strings:
        value = manifest.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ProfileValidationError(f"{field}_must_be_non_empty_string")

    features_raw = manifest.get("features")
    if not isinstance(features_raw, list) or not all(
        isinstance(item, str) and item for item in features_raw
    ):
        raise ProfileValidationError("features_must_be_non_empty_string_array")
    if len(features_raw) != len(set(features_raw)):
        raise ProfileValidationError("features_must_be_unique")

    missing_features = sorted(set(FULL_LLM_FEATURES) - set(features_raw))
    if missing_features:
        raise ProfileValidationError(
            "full_llm_surface_missing:" + ",".join(missing_features)
        )

    if manifest["llm_surface"] != "FULL_PROVIDER_SUPPORTED":
        raise ProfileValidationError("llm_surface_must_be_full_provider_supported")

    source_policy = _require_mapping(manifest.get("source_policy"), "source_policy")
    mode = source_policy.get("mode")
    if mode not in ALLOWED_SOURCE_MODES:
        raise ProfileValidationError("unsupported_source_policy_mode")

    authority_policy = _require_mapping(
        manifest.get("authority_policy"), "authority_policy"
    )
    required_false_authorities = (
        "model_output_is_execution_authority",
        "tool_candidate_is_execution_authority",
        "source_acceptance_is_admissibility",
        "provider_response_is_publication_authority",
        "user_record_is_government_authority",
    )
    for field in required_false_authorities:
        if authority_policy.get(field) is not False:
            raise ProfileValidationError(f"authority_policy_must_be_false:{field}")

    if mode == "OFFICIAL_VA_ONLY":
        if source_policy.get("official_va_only") is not True:
            raise ProfileValidationError("va_profile_must_require_official_va_only")
        suffixes = source_policy.get("allowed_external_host_suffixes")
        if suffixes != ["va.gov"]:
            raise ProfileValidationError("va_profile_allowed_suffix_must_equal_va.gov")
        if source_policy.get("allow_general_web") is not False:
            raise ProfileValidationError("va_profile_general_web_must_be_false")
        if source_policy.get("allow_model_memory_as_factual_source") is not False:
            raise ProfileValidationError(
                "va_profile_model_memory_as_source_must_be_false"
            )
        if source_policy.get("allow_user_record_facts") is not True:
            raise ProfileValidationError("va_profile_must_allow_user_record_facts")
        if source_policy.get("user_records_are_va_authority") is not False:
            raise ProfileValidationError("user_records_must_not_be_va_authority")

    return ChatLLMProfile(
        schema=manifest["schema"],
        profile_id=manifest["profile_id"],
        display_name=manifest["display_name"],
        purpose=manifest["purpose"],
        llm_surface=manifest["llm_surface"],
        features=tuple(features_raw),
        source_policy=dict(source_policy),
        authority_policy={
            key: bool(value) for key, value in authority_policy.items()
        },
    )


def load_profile(path: Path) -> ChatLLMProfile:
    """Load and validate one JSON profile."""

    with path.open("r", encoding="utf-8") as handle:
        manifest = json.load(handle)
    if not isinstance(manifest, Mapping):
        raise ProfileValidationError("manifest_root_must_be_object")
    return validate_profile_manifest(manifest)


def _user_record_decision(candidate: SourceCandidate) -> SourceDecision:
    reasons = []
    if candidate.privacy_status != "PASS":
        reasons.append("user_record_privacy_not_pass")
    if not candidate.consent_present:
        reasons.append("user_record_consent_missing")
    if not candidate.content_hash:
        reasons.append("user_record_hash_missing")
    allowed = not reasons
    return SourceDecision(
        status="ALLOW_USER_RECORD_FACT" if allowed else "DENY_SOURCE",
        allowed_for_factual_grounding=allowed,
        allowed_as_authority=False,
        fact_label="user_record_fact" if allowed else "",
        reasons=tuple(reasons),
        normalized_host=normalize_host(candidate.uri),
    )


def evaluate_source(
    profile: ChatLLMProfile,
    candidate: SourceCandidate,
) -> SourceDecision:
    """Evaluate one source candidate against a validated profile."""

    if candidate.source_type not in ALLOWED_SOURCE_TYPES:
        return SourceDecision(
            status="DENY_SOURCE",
            allowed_for_factual_grounding=False,
            allowed_as_authority=False,
            fact_label="",
            reasons=("unknown_source_type",),
            normalized_host=normalize_host(candidate.uri),
        )

    mode = profile.source_policy["mode"]
    host = normalize_host(candidate.uri)

    if candidate.source_type == "user_record":
        if profile.source_policy.get("allow_user_record_facts") is not True:
            return SourceDecision(
                status="DENY_SOURCE",
                allowed_for_factual_grounding=False,
                allowed_as_authority=False,
                fact_label="",
                reasons=("user_record_facts_disabled",),
                normalized_host=host,
            )
        return _user_record_decision(candidate)

    if candidate.source_type == "model_memory":
        allow_memory = profile.source_policy.get(
            "allow_model_memory_as_factual_source", False
        )
        return SourceDecision(
            status="ALLOW_UNSOURCED_CONTEXT" if allow_memory else "DENY_SOURCE",
            allowed_for_factual_grounding=bool(allow_memory),
            allowed_as_authority=False,
            fact_label="model_context" if allow_memory else "",
            reasons=() if allow_memory else ("model_memory_not_a_factual_source",),
            normalized_host=host,
        )

    if not candidate.admitted:
        return SourceDecision(
            status="DENY_SOURCE",
            allowed_for_factual_grounding=False,
            allowed_as_authority=False,
            fact_label="",
            reasons=("source_not_admitted",),
            normalized_host=host,
        )

    if mode == "OFFICIAL_VA_ONLY":
        if candidate.source_type != "official_external":
            return SourceDecision(
                status="DENY_SOURCE",
                allowed_for_factual_grounding=False,
                allowed_as_authority=False,
                fact_label="",
                reasons=("va_claims_external_source_must_be_official",),
                normalized_host=host,
            )
        if not is_official_va_host(candidate.uri):
            return SourceDecision(
                status="DENY_SOURCE",
                allowed_for_factual_grounding=False,
                allowed_as_authority=False,
                fact_label="",
                reasons=("external_source_not_official_va",),
                normalized_host=host,
            )
        return SourceDecision(
            status="ALLOW_VA_SOURCE_FACT",
            allowed_for_factual_grounding=True,
            allowed_as_authority=True,
            fact_label="va_source_fact",
            reasons=(),
            normalized_host=host,
        )

    return SourceDecision(
        status="ALLOW_ADMITTED_SOURCE",
        allowed_for_factual_grounding=True,
        allowed_as_authority=candidate.source_type == "official_external",
        fact_label=(
            "official_source_fact"
            if candidate.source_type == "official_external"
            else "admitted_source_fact"
        ),
        reasons=(),
        normalized_host=host,
    )


def validate_parallel_profiles(
    ecosystem_manifest: Mapping[str, Any],
    claims_manifest: Mapping[str, Any],
) -> Tuple[ChatLLMProfile, ChatLLMProfile]:
    """Validate the paired product contract and prevent capability divergence."""

    ecosystem = validate_profile_manifest(ecosystem_manifest)
    claims = validate_profile_manifest(claims_manifest)

    if ecosystem.profile_id != "ecosystem-chat-llm":
        raise ProfileValidationError("unexpected_ecosystem_profile_id")
    if claims.profile_id != "va-claims-chat-llm":
        raise ProfileValidationError("unexpected_claims_profile_id")
    if set(ecosystem.features) != set(claims.features):
        raise ProfileValidationError("chat_profiles_must_share_full_llm_surface")
    if ecosystem.source_policy.get("mode") != "GENERAL_ADMITTED":
        raise ProfileValidationError("ecosystem_profile_must_be_general_admitted")
    if claims.source_policy.get("mode") != "OFFICIAL_VA_ONLY":
        raise ProfileValidationError("claims_profile_must_be_official_va_only")

    return ecosystem, claims


def capability_matrix(profiles: Iterable[ChatLLMProfile]) -> Dict[str, Dict[str, bool]]:
    """Return a deterministic feature matrix for projection and receipts."""

    return {
        profile.profile_id: {
            feature: feature in profile.features for feature in FULL_LLM_FEATURES
        }
        for profile in profiles
    }
