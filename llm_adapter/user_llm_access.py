"""Bounded user-LLM access contract for StegVerse Demo and sandbox routes."""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any, Iterable, Mapping


ALLOWED_ROUTES = {
    "demo_test_suite",
    "entity_sandbox_runner",
    "hil_response_packet",
}


@dataclass(frozen=True)
class UserLLMIdentity:
    user_id: str
    llm_id: str
    provider: str
    model: str
    scopes: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class AccessRequest:
    identity: UserLLMIdentity
    route: str
    action: str
    payload: Mapping[str, Any]


class AccessDenied(ValueError):
    """Raised when a user-LLM request exceeds the bounded access contract."""


def list_demo_capabilities() -> tuple[dict[str, Any], ...]:
    return (
        {
            "capability_id": "demo_test_suite",
            "actions": ["list", "inspect", "configure", "submit"],
            "authority": "bounded_demo_only",
        },
        {
            "capability_id": "entity_sandbox_runner",
            "actions": ["submit", "status", "retrieve_result"],
            "authority": "bounded_sandbox_only",
        },
        {
            "capability_id": "hil_response_packet",
            "actions": ["submit_pdf_metadata"],
            "authority": "non_publication_submission_only",
        },
    )


def build_submission(request: AccessRequest) -> dict[str, Any]:
    if request.route not in ALLOWED_ROUTES:
        raise AccessDenied(f"route not allowed: {request.route}")
    if not request.identity.user_id or not request.identity.llm_id:
        raise AccessDenied("user_id and llm_id are required")

    payload = dict(request.payload)
    canonical = repr(
        (
            request.identity.user_id,
            request.identity.llm_id,
            request.identity.provider,
            request.identity.model,
            request.route,
            request.action,
            sorted(payload.items()),
        )
    ).encode("utf-8")

    return {
        "schema_version": "user-llm-access-v1",
        "participant_class": "authorized_user_llm",
        "user_id": request.identity.user_id,
        "llm_id": request.identity.llm_id,
        "provider": request.identity.provider,
        "model": request.identity.model,
        "scopes": list(request.identity.scopes),
        "route": request.route,
        "action": request.action,
        "payload": payload,
        "request_hash": sha256(canonical).hexdigest(),
        "authority": {
            "sdk_equivalent_demo_access": True,
            "execution_authority": False,
            "publication_authority": False,
            "continuity_authority": False,
            "master_record_custody": False,
        },
        "status": "ready_for_governed_routing",
    }


def build_hil_pdf_submission(
    identity: UserLLMIdentity,
    *,
    filename: str,
    sha256_hex: str,
    size_bytes: int,
    trace_id: str,
    participant_review_status: str,
) -> dict[str, Any]:
    if not filename.lower().endswith(".pdf"):
        raise AccessDenied("HIL response packet must be a PDF")
    if len(sha256_hex) != 64:
        raise AccessDenied("sha256_hex must contain 64 hexadecimal characters")
    if size_bytes <= 0:
        raise AccessDenied("size_bytes must be positive")

    return build_submission(
        AccessRequest(
            identity=identity,
            route="hil_response_packet",
            action="submit_pdf_metadata",
            payload={
                "filename": filename,
                "sha256": sha256_hex.lower(),
                "size_bytes": size_bytes,
                "trace_id": trace_id,
                "participant_review_status": participant_review_status,
            },
        )
    )
