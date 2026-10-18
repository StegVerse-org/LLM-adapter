"""Governed bounded fallback backend for StegVerse AI Entry.

Provider execution remains owned by the canonical governed provider path. This
module supplies credential-free bounded fallback responses and grounds known
public StegVerse/help questions in the committed public-knowledge manifest.
When caller-configured, digest-pinned ecosystem registry sources are supplied,
a third resolver answers exact registry identifiers (task ids, organization
entity names, invariant keys, reusable task ids) with OBSERVED, line-cited facts
admitted through ``chat_profiles.evaluate_source``.
It does not call live providers, issue authority, expose credentials, or persist
records.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import re
from typing import Any, Mapping, Sequence

from llm_adapter.ai_entry_provider_boundary import build_disabled_provider_boundary
from llm_adapter.chat_profiles import (
    FACT_LABEL_EVIDENCE_CLASS,
    ProfileValidationError,
    SourceCandidate,
    evaluate_source,
    load_profile,
)
from llm_adapter.ecosystem_fact_index import (
    EcosystemFactSourceConfigError,
    build_index,
    load_source_manifest,
    lookup,
)
from llm_adapter.free_tier_limits import ReceiptReplayUsage, evaluate_receipt_replay_limits
from llm_adapter.free_tier_quota import FreeTierUsage, evaluate_free_tier_quota
from llm_adapter.public_knowledge import PublicKnowledgeError, resolve_public_question
from llm_adapter.provider_surface_knowledge import ProviderSurfaceKnowledgeError, resolve_provider_surface_question

ROUTE_KEYWORDS = (
    ("restricted_admin", ("secret", "token", "credential", "shell", "delete", "release", "permission", "workflow", "repo write")),
    ("llm_comparison", ("compare", "comparison", "chatgpt", "claude", "gemini", "grok", "other llm")),
    ("sdk_access_guidance", ("sdk", "api", "access", "onboard", "permission", "manifest", "receipt")),
    ("sdk_intake_candidate", ("submit", "intake", "candidate", "packet", "request access", "integration")),
    ("governance_review", ("governance", "admissibility", "authority", "evidence", "reconstruction", "replay", "transition")),
    ("runtime_status", ("runtime", "adapter", "micro-node", "micro node", "capability", "goal")),
    ("documentation_route", ("docs", "documentation", "wiki", "paper", "spec", "runbook", "proof")),
    ("ecosystem_explanation", ("ecosystem", "stegverse", "concept", "component", "role", "status")),
)

ECOSYSTEM_FACT_SOURCES_ENV = "LLM_ADAPTER_ECOSYSTEM_FACT_SOURCES"
ECOSYSTEM_FACT_ROUTE_ID = "ecosystem_fact_index"
ECOSYSTEM_CHAT_PROFILE_PATH = Path(__file__).resolve().parent.parent / "profiles" / "ecosystem-chat-llm.v1.json"
_IDENTIFIER_TOKEN_RE = re.compile(r"[A-Za-z0-9_.\-]+")


@dataclass(frozen=True)
class AIEntryBackendResponse:
    response_id: str
    primary_route: str
    stegverse_response: str
    route_guidance: str
    sdk_guidance: str
    comparison_outputs: list[dict[str, Any]]
    governance: dict[str, Any]
    activation: dict[str, Any]
    free_tier_trust: dict[str, Any]
    receipt_capture_preview: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def classify_route(message: str) -> str:
    lower = message.lower()
    for route_id, keywords in ROUTE_KEYWORDS:
        if any(keyword in lower for keyword in keywords):
            return route_id
    return "chat_answer"


def build_receipt_capture_preview(*, message: str, route_id: str, response_id: str) -> dict[str, Any]:
    return {
        "schema_version": "stegverse.ai_entry.receipt_capture_preview.v0.1",
        "preview_only": True,
        "receipt_capture_enabled": False,
        "real_receipt_issued": False,
        "record_persisted": False,
        "authority_granted": False,
        "input_hash": sha256(message.encode("utf-8")).hexdigest(),
        "route_id": route_id,
        "response_id": response_id,
        "reconstruction_metadata_required": True,
    }


def build_free_tier_trust_metadata() -> dict[str, Any]:
    quota = evaluate_free_tier_quota(FreeTierUsage()).to_dict()
    limits = evaluate_receipt_replay_limits(ReceiptReplayUsage()).to_dict()
    return {
        "schema_version": "stegverse.ai_entry.free_tier_trust.v0.1",
        "preview_only": True,
        "bounded_live_use": True,
        "static_demo_only": False,
        "quota": quota,
        "receipt_replay_limits": limits,
        "trust_window": {
            "curiosity_level_meaningful_inquiries": "3-10",
            "reliance_level_evaluation_inquiries": "20-50",
        },
        "upgrade_for": [
            "higher_quota",
            "private_connectors",
            "premium_models",
            "longer_retention",
            "deeper_replay",
            "deeper_reconstruction",
            "team_workspace",
            "api_access",
            "custom_policy",
            "exportable_audit_packet",
        ],
        "non_claims": {
            "free_tier_response_is_authority": False,
            "quota_allow_is_admissibility": False,
            "limit_allow_is_execution_authority": False,
            "upgrade_changes_admissibility_requirements": False,
        },
    }


def _provider_surface_grounding(message: str) -> tuple[str | None, str]:
    try:
        grounded = resolve_provider_surface_question(message)
    except ProviderSurfaceKnowledgeError as exc:
        return (
            "StegVerse recognized this as a provider/device/platform/access-surface question, but the canonical KV capability registry is not available in this runtime. No capability fact was inferred.",
            f"Canonical provider-surface registry unavailable: {exc}. Model memory was not used as the factual source.",
        )
    if grounded is None:
        return None, ""
    return grounded.answer, f"Grounded provider/device/platform/access-surface source: {grounded.source_ref}. Match state: {grounded.match_state}. Model memory is not the factual source."


def _public_grounding(message: str) -> tuple[str | None, str]:
    try:
        grounded = resolve_public_question(message)
    except PublicKnowledgeError as exc:
        return None, f"Public knowledge corpus unavailable: {exc}. No public fact was invented."
    if grounded is None:
        return None, "No canonical public-knowledge entry matched this question; bounded fallback will not invent a StegVerse fact."
    source_text = ", ".join(
        f"{source['repository']}/{source['path']}" for source in grounded.source_refs
    )
    return grounded.answer, f"Grounded public StegVerse sources: {source_text}. Model memory is not the factual source."


def _configured_ecosystem_fact_sources(
    explicit: Sequence[Mapping[str, Any]] | None,
) -> Sequence[Mapping[str, Any]] | None:
    if explicit is not None:
        return explicit
    manifest_path = os.environ.get(ECOSYSTEM_FACT_SOURCES_ENV, "").strip()
    if not manifest_path:
        return None
    try:
        return load_source_manifest(Path(manifest_path))
    except EcosystemFactSourceConfigError:
        return None


def _identifier_candidates(message: str) -> list[str]:
    """Identifier-shaped tokens only; plain lowercase words are never looked up."""

    candidates: list[str] = []
    for raw in _IDENTIFIER_TOKEN_RE.findall(message):
        token = raw.rstrip(".-")
        if token and not (token.isalpha() and token.islower()) and token not in candidates:
            candidates.append(token)
    return candidates


def _ecosystem_fact_grounding(
    message: str,
    sources: Sequence[Mapping[str, Any]] | None,
) -> tuple[str | None, str, dict[str, Any] | None]:
    if not sources:
        return None, "", None
    built = build_index(sources)
    if built.status != "ALLOW" or built.index is None:
        return None, "", None
    answers: list[dict[str, Any]] = []
    for candidate in _identifier_candidates(message):
        result = lookup(built.index, candidate)
        if result["status"] == "ANSWER":
            answers.extend(result["answers"])
    if not answers:
        return None, "", None
    try:
        profile = load_profile(ECOSYSTEM_CHAT_PROFILE_PATH)
    except (OSError, ValueError, ProfileValidationError):
        return None, "", None
    admitted: list[dict[str, Any]] = []
    decisions: list[dict[str, Any]] = []
    for answer in answers:
        source = answer["source"]
        decision = evaluate_source(
            profile,
            SourceCandidate(
                source_type="stegverse_registry",
                uri=f"https://github.com/{source['repository']}/blob/{source['revision']}/{source['path']}",
                admitted=True,
                authority_class="OBSERVED_REGISTRY",
                content_hash=source["sha256"],
            ),
        )
        evidence_class = FACT_LABEL_EVIDENCE_CLASS.get(decision.fact_label)
        if not decision.allowed_for_factual_grounding or evidence_class != "OBSERVED":
            continue
        admitted.append(answer)
        decisions.append({
            "citation": answer["citation"],
            "status": decision.status,
            "fact_label": decision.fact_label,
            "allowed_as_authority": decision.allowed_as_authority,
            "evidence_class": evidence_class,
        })
    if not admitted:
        return None, "", None
    citations = [answer["citation"] for answer in admitted]
    text = "Observed in the supplied ecosystem registries: " + "; ".join(
        f"{answer['kind']} {answer['key']} = "
        f"{json.dumps(answer['value'], sort_keys=True, ensure_ascii=False)} [{answer['citation']}]"
        for answer in admitted
    )
    guidance = (
        "Grounded ecosystem registry sources (evidence class OBSERVED, admitted by "
        f"chat_profiles.evaluate_source as {decisions[0]['status']}): {', '.join(citations)}. "
        "Exact-identifier lookup only; model memory is not the factual source."
    )
    governance_extra = {
        "evidence_class": "OBSERVED",
        "ecosystem_fact_citations": citations,
        "source_decisions": decisions,
    }
    return text, guidance, governance_extra


def build_ai_entry_backend_response(
    message: str,
    *,
    declared_route_id: str | None = None,
    ecosystem_fact_sources: Sequence[Mapping[str, Any]] | None = None,
) -> AIEntryBackendResponse:
    clean = message.strip()
    # Message-content classification is descriptive fallback guidance only.
    # A governed caller that supplies a manifest-selected route remains bound to
    # that declaration; this module does not substitute a route from message text.
    route_id = str(declared_route_id or "").strip() or classify_route(clean)
    provider_answer, provider_guidance = _provider_surface_grounding(clean) if clean else (None, "")
    grounded_answer, grounding_guidance = _public_grounding(clean) if clean and provider_answer is None else (None, "")
    if provider_answer is not None:
        grounded_answer, grounding_guidance = provider_answer, provider_guidance
        route_id = "provider_surface_knowledge"
    elif grounded_answer is not None:
        route_id = "public_knowledge"
    registry_governance: dict[str, Any] | None = None
    if clean and grounded_answer is None:
        configured = _configured_ecosystem_fact_sources(ecosystem_fact_sources)
        registry_answer, registry_guidance, registry_governance = _ecosystem_fact_grounding(clean, configured)
        if registry_answer is not None:
            grounded_answer, grounding_guidance = registry_answer, registry_guidance
            route_id = ECOSYSTEM_FACT_ROUTE_ID
    digest = sha256(f"{route_id}\n{clean}".encode("utf-8")).hexdigest()[:16]
    response_id = "welcome" if not clean else f"preview-{route_id}-{digest}"
    provider_boundary = build_disabled_provider_boundary()
    comparisons = [
        {
            "provider": comparison.provider,
            "authority": comparison.authority,
            "response": comparison.response,
        }
        for comparison in provider_boundary.comparisons
    ]
    governed_candidate = bool(clean)
    receipt_preview = build_receipt_capture_preview(
        message=clean,
        route_id=route_id,
        response_id=response_id,
    )
    if not clean:
        response_text = "Welcome to StegVerse AI. Ask a question or request SDK, governance, runtime, documentation, or comparison guidance."
        route_guidance = "Public help is grounded in the committed StegVerse public-knowledge corpus; provider execution remains separately governed."
    elif grounded_answer is not None:
        response_text = grounded_answer
        route_guidance = grounding_guidance
    else:
        response_text = (
            f"StegVerse received one AI Entry request and classified it as {route_id}. "
            "No canonical public-knowledge entry matched, so this bounded fallback does not invent an answer. "
            "A separately governed provider/retrieval path may answer when admitted evidence is available."
        )
        route_guidance = grounding_guidance

    return AIEntryBackendResponse(
        response_id=response_id,
        primary_route=route_id,
        stegverse_response=response_text,
        route_guidance=route_guidance,
        sdk_guidance=(
            "SDK guidance is grounded in the public knowledge corpus when a matching SDK/help entry exists."
            if route_id in {"sdk_access_guidance", "sdk_intake_candidate", "public_knowledge", "provider_surface_knowledge"}
            else "No SDK-specific public knowledge entry selected."
        ),
        comparison_outputs=comparisons,
        governance={
            "governed_candidate": governed_candidate,
            "authority_issued": False,
            "receipt_id": None,
            "reconstruction_available": False,
            **(registry_governance or {}),
        },
        activation={
            "live_provider_calls_enabled": provider_boundary.live_provider_calls_enabled,
            "credential_surface_enabled": provider_boundary.credential_surface_enabled,
            "provider_secret_required_for_tests": provider_boundary.provider_secret_required_for_tests,
            "provider_output_is_authority": provider_boundary.provider_output_is_authority,
            "receipt_capture_required_before_live_activation": provider_boundary.receipt_capture_required_before_live_activation,
        },
        free_tier_trust=build_free_tier_trust_metadata(),
        receipt_capture_preview=receipt_preview,
    )


def main() -> int:
    import json
    import sys

    message = " ".join(sys.argv[1:])
    print(json.dumps(build_ai_entry_backend_response(message).to_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
