"""Bounded user-LLM access contract for StegVerse Demo and sandbox routes."""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from json import dumps
from typing import Any, Mapping


ROUTE_ACTION_SCOPES: dict[str, dict[str, str]] = {
    "demo_test_suite": {
        "list": "demo:read",
        "inspect": "demo:read",
        "configure": "demo:submit",
        "submit": "demo:submit",
    },
    "entity_sandbox_runner": {
        "submit": "sandbox:submit",
        "status": "sandbox:read",
        "retrieve_result": "sandbox:read",
    },
    "hil_response_packet": {
        "submit_pdf_metadata": "hil:submit",
    },
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
    return tuple(
        {
            "capability_id": route,
            "actions": list(actions),
            "required_scopes": dict(actions),
            "authority": {
                "demo_test_suite": "bounded_demo_only",
                "entity_sandbox_runner": "bounded_sandbox_only",
                "hil_response_packet": "non_publication_submission_only",
            }[route],
        }
        for route, actions in ROUTE_ACTION_SCOPES.items()
    )


def _validate_request(request: AccessRequest) -> str:
    if not request.identity.user_id or not request.identity.llm_id:
        raise AccessDenied("user_id and llm_id are required")
    if not request.identity.provider or not request.identity.model:
        raise AccessDenied("provider and model are required")
    actions = ROUTE_ACTION_SCOPES.get(request.route)
    if actions is None:
        raise AccessDenied(f"route not allowed: {request.route}")
    required_scope = actions.get(request.action)
    if required_scope is None:
        raise AccessDenied(f"action not allowed for route: {request.route}/{request.action}")
    if required_scope not in request.identity.scopes:
        raise AccessDenied(f"required scope missing: {required_scope}")
    return required_scope


def build_submission(request: AccessRequest) -> dict[str, Any]:
    required_scope = _validate_request(request)
    payload = dict(request.payload)
    canonical = dumps(
        {
            "user_id": request.identity.user_id,
            "llm_id": request.identity.llm_id,
            "provider": request.identity.provider,
            "model": request.identity.model,
            "scopes": sorted(request.identity.scopes),
            "route": request.route,
            "action": request.action,
            "payload": payload,
        },
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")

    return {
        "schema_version": "user-llm-access-v1",
        "participant_class": "authorized_user_llm",
        "user_id": request.identity.user_id,
        "llm_id": request.identity.llm_id,
        "provider": request.identity.provider,
        "model": request.identity.model,
        "scopes": list(request.identity.scopes),
        "required_scope": required_scope,
        "route": request.route,
        "action": request.action,
        "payload": payload,
        "request_hash": sha256(canonical).hexdigest(),
        "authority": {
            "sdk_equivalent_demo_access": request.route == "demo_test_suite",
            "bounded_sandbox_submission": request.route == "entity_sandbox_runner",
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
    normalized_hash = sha256_hex.lower()
    if not filename.lower().endswith(".pdf"):
        raise AccessDenied("HIL response packet must be a PDF")
    if len(normalized_hash) != 64 or any(c not in "0123456789abcdef" for c in normalized_hash):
        raise AccessDenied("sha256_hex must contain 64 hexadecimal characters")
    if size_bytes <= 0:
        raise AccessDenied("size_bytes must be positive")
    if not trace_id.strip():
        raise AccessDenied("trace_id is required")
    if not participant_review_status.strip():
        raise AccessDenied("participant_review_status is required")

    return build_submission(
        AccessRequest(
            identity=identity,
            route="hil_response_packet",
            action="submit_pdf_metadata",
            payload={
                "filename": filename,
                "sha256": normalized_hash,
                "size_bytes": size_bytes,
                "trace_id": trace_id,
                "participant_review_status": participant_review_status,
            },
        )
    )
