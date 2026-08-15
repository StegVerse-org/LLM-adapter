"""Source-policy layer for the broad VACC public-information companion.

The existing VA Claims Chat profile remains unchanged. This module evaluates
whether a proposed public information source is admitted for VACC grounding.
It grants no adjudication, filing, provider, publication, or custody authority.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse

PROFILE_PATH = Path(__file__).resolve().parent.parent / "profiles" / "vacc-public-information-llm.v1.json"


class VACCSourcePolicyError(ValueError):
    pass


@dataclass(frozen=True)
class VACCSourceCandidate:
    source_id: str
    url: str
    authority_class: str
    admitted: bool
    public: bool
    freshness_required: bool = False
    freshness_verified: bool = False
    sanitized_public_projection: bool = False


@dataclass(frozen=True)
class VACCSourceDecision:
    state: str
    allowed_for_grounding: bool
    allowed_as_government_authority: bool
    reasons: tuple[str, ...]
    source_id: str
    normalized_host: str
    authority_class: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "allowed_for_grounding": self.allowed_for_grounding,
            "allowed_as_government_authority": self.allowed_as_government_authority,
            "reasons": list(self.reasons),
            "source_id": self.source_id,
            "normalized_host": self.normalized_host,
            "authority_class": self.authority_class,
            "adjudication_authority": False,
            "medical_opinion_authority": False,
            "representation_authority": False,
            "filing_authority": False,
            "publication_authority": False,
        }


def normalize_host(url_or_host: str) -> str:
    raw = url_or_host.strip().lower()
    if not raw:
        return ""
    parsed = urlparse(raw if "://" in raw else "https://" + raw)
    return (parsed.hostname or "").rstrip(".")


def _matches_suffix(host: str, suffix: str) -> bool:
    normalized = suffix.strip().lower().rstrip(".")
    return host == normalized or host.endswith("." + normalized)


def load_profile(path: Path = PROFILE_PATH) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise VACCSourcePolicyError(f"vacc_profile_unavailable:{exc}") from exc
    except json.JSONDecodeError as exc:
        raise VACCSourcePolicyError("vacc_profile_invalid_json") from exc
    validate_profile(value)
    return value


def validate_profile(profile: Mapping[str, Any]) -> None:
    if profile.get("schema") != "stegverse.vacc_public_information_profile.v1":
        raise VACCSourcePolicyError("unsupported_vacc_profile_schema")
    if profile.get("profile_id") != "vacc-public-information-llm":
        raise VACCSourcePolicyError("unexpected_vacc_profile_id")
    if profile.get("llm_surface") != "FULL_PROVIDER_SUPPORTED":
        raise VACCSourcePolicyError("vacc_llm_surface_must_be_full_provider_supported")
    if profile.get("canonical_source_registry") != "StegVerse-Labs/Site/data/va-claim-assistant/source-registry.json":
        raise VACCSourcePolicyError("vacc_canonical_source_registry_mismatch")
    classes = profile.get("allowed_source_classes")
    suffixes = profile.get("allowed_public_host_suffixes")
    if not isinstance(classes, list) or not classes or len(classes) != len(set(classes)):
        raise VACCSourcePolicyError("vacc_source_classes_invalid")
    if not isinstance(suffixes, list) or not suffixes or len(suffixes) != len(set(suffixes)):
        raise VACCSourcePolicyError("vacc_host_suffixes_invalid")
    private_policy = profile.get("private_source_policy")
    if not isinstance(private_policy, Mapping):
        raise VACCSourcePolicyError("vacc_private_source_policy_missing")
    if private_policy.get("private_vawatchdog_content_is_public_grounding") is not False:
        raise VACCSourcePolicyError("private_vawatchdog_content_must_not_be_public_grounding")
    claims_boundary = profile.get("claims_profile_boundary")
    if not isinstance(claims_boundary, Mapping) or claims_boundary.get("existing_official_va_only_policy_unchanged") is not True:
        raise VACCSourcePolicyError("existing_va_claims_profile_must_remain_unchanged")
    authority = profile.get("authority_policy")
    if not isinstance(authority, Mapping) or any(value is not False for value in authority.values()):
        raise VACCSourcePolicyError("vacc_authority_policy_must_be_all_false")
    credential = profile.get("credential_policy")
    if (
        not isinstance(credential, Mapping)
        or credential.get("credential_authority") != "TV/TVC"
        or credential.get("non_tv_tvc_secret_or_token_required") is not False
        or credential.get("github_token_runtime_authority") != "NONE"
    ):
        raise VACCSourcePolicyError("vacc_credential_policy_invalid")


def evaluate_public_source(
    candidate: VACCSourceCandidate,
    profile: Mapping[str, Any] | None = None,
) -> VACCSourceDecision:
    config = dict(profile) if profile is not None else load_profile()
    validate_profile(config)
    reasons: list[str] = []
    host = normalize_host(candidate.url)

    if not candidate.source_id.strip():
        reasons.append("source_id_missing")
    if candidate.authority_class not in set(config["allowed_source_classes"]):
        reasons.append("authority_class_not_admitted")
    if candidate.admitted is not True:
        reasons.append("source_not_admitted")
    if candidate.public is not True:
        reasons.append("source_not_public")
    if candidate.freshness_required and not candidate.freshness_verified:
        reasons.append("freshness_not_verified")

    is_vawatchdog = candidate.source_id.upper().startswith("VAW-") or "vawatchdog" in candidate.url.lower()
    if is_vawatchdog and not candidate.sanitized_public_projection:
        reasons.append("private_vawatchdog_requires_sanitized_public_projection")

    allowed_host = any(_matches_suffix(host, suffix) for suffix in config["allowed_public_host_suffixes"])
    if not allowed_host and not (is_vawatchdog and candidate.sanitized_public_projection):
        reasons.append("host_not_in_vacc_public_allowlist")

    allowed = not reasons
    government_authority = allowed and candidate.authority_class in {"CONTROLLING", "OFFICIAL_OPERATIONAL"} and not is_vawatchdog
    return VACCSourceDecision(
        state="ALLOW_PUBLIC_GROUNDING" if allowed else "DENY_SOURCE",
        allowed_for_grounding=allowed,
        allowed_as_government_authority=government_authority,
        reasons=tuple(reasons),
        source_id=candidate.source_id,
        normalized_host=host,
        authority_class=candidate.authority_class,
    )


__all__ = [
    "PROFILE_PATH",
    "VACCSourceCandidate",
    "VACCSourceDecision",
    "VACCSourcePolicyError",
    "evaluate_public_source",
    "load_profile",
    "normalize_host",
    "validate_profile",
]
