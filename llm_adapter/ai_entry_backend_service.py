"""Interim governed backend scaffold for StegVerse AI Entry.

This module combines the local provider comparison boundary with a response
shape suitable for the Site AI Entry Point. It is disabled-by-default and does
not call live providers, issue authority, expose credentials, or persist records.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from typing import Any

from llm_adapter.ai_entry_provider_boundary import build_disabled_provider_boundary

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

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def classify_route(message: str) -> str:
    lower = message.lower()
    for route_id, keywords in ROUTE_KEYWORDS:
        if any(keyword in lower for keyword in keywords):
            return route_id
    return "chat_answer"


def build_ai_entry_backend_response(message: str) -> AIEntryBackendResponse:
    clean = message.strip()
    route_id = classify_route(clean)
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
    return AIEntryBackendResponse(
        response_id=response_id,
        primary_route=route_id,
        stegverse_response=(
            "Welcome to StegVerse AI. Ask a question or request SDK, governance, runtime, documentation, or comparison guidance."
            if not clean
            else f"StegVerse received one AI Entry request and classified it as {route_id}. This interim backend returns a bounded preview response."
        ),
        route_guidance="Interim backend route classification only; no live calls or authority are issued.",
        sdk_guidance=(
            "SDK guidance path selected; receipt capture remains preview-only until SDK activation."
            if route_id.startswith("sdk")
            else "No SDK-specific route selected."
        ),
        comparison_outputs=comparisons,
        governance={
            "governed_candidate": governed_candidate,
            "authority_issued": False,
            "receipt_id": None,
            "reconstruction_available": False,
        },
        activation={
            "live_provider_calls_enabled": provider_boundary.live_provider_calls_enabled,
            "credential_surface_enabled": provider_boundary.credential_surface_enabled,
            "provider_secret_required_for_tests": provider_boundary.provider_secret_required_for_tests,
            "provider_output_is_authority": provider_boundary.provider_output_is_authority,
            "receipt_capture_required_before_live_activation": provider_boundary.receipt_capture_required_before_live_activation,
        },
    )


def main() -> int:
    import json
    import sys

    message = " ".join(sys.argv[1:])
    print(json.dumps(build_ai_entry_backend_response(message).to_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
