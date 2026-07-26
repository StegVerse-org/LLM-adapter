"""Governed routing for bounded user-LLM access requests."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from json import dumps
from typing import Any, Callable, Mapping

from .user_llm_access import AccessDenied, AccessRequest, build_submission

Transport = Callable[[Mapping[str, Any]], Mapping[str, Any]]


@dataclass(frozen=True)
class RouteTransports:
    demo_test_suite: Transport | None = None
    entity_sandbox_runner: Transport | None = None
    hil_response_packet: Transport | None = None

    def for_route(self, route: str) -> Transport | None:
        return {
            "demo_test_suite": self.demo_test_suite,
            "entity_sandbox_runner": self.entity_sandbox_runner,
            "hil_response_packet": self.hil_response_packet,
        }.get(route)


def route_request(request: AccessRequest, transports: RouteTransports) -> dict[str, Any]:
    envelope = build_submission(request)
    transport = transports.for_route(request.route)
    if transport is None:
        return {
            "status": "DEFER",
            "reason": "route_transport_not_configured",
            "request": envelope,
            "authority_attached": False,
        }

    try:
        result = dict(transport(envelope))
    except Exception as exc:
        return {
            "status": "DEFER",
            "reason": "downstream_transport_failed",
            "detail": str(exc),
            "request": envelope,
            "authority_attached": False,
        }

    canonical_result = dumps(result, sort_keys=True, separators=(",", ":"), default=str)
    return {
        "status": "RETURNED",
        "request": envelope,
        "result": result,
        "result_hash": sha256(canonical_result.encode("utf-8")).hexdigest(),
        "authority_attached": False,
        "return_path": {
            "user_id": envelope["user_id"],
            "llm_id": envelope["llm_id"],
            "provider": envelope["provider"],
            "model": envelope["model"],
        },
    }


def handle_user_llm_request(
    body: Mapping[str, Any],
    transports: RouteTransports | None = None,
) -> dict[str, Any]:
    """Dictionary service boundary suitable for HTTP, MCP, or SDK wrappers."""
    try:
        identity_data = dict(body.get("identity") or {})
        from .user_llm_access import UserLLMIdentity

        identity = UserLLMIdentity(
            user_id=str(identity_data.get("user_id", "")),
            llm_id=str(identity_data.get("llm_id", "")),
            provider=str(identity_data.get("provider", "")),
            model=str(identity_data.get("model", "")),
            scopes=tuple(str(scope) for scope in (identity_data.get("scopes") or ())),
        )
        request = AccessRequest(
            identity=identity,
            route=str(body.get("route", "")),
            action=str(body.get("action", "")),
            payload=dict(body.get("payload") or {}),
        )
        return route_request(request, transports or RouteTransports())
    except (AccessDenied, TypeError, ValueError) as exc:
        return {
            "status": "DENY",
            "reason": str(exc),
            "authority_attached": False,
        }