"""Optional HTTP service for bounded user-LLM access.

Importing this module does not start a server. FastAPI is imported lazily through
``create_app`` so core package users do not require service dependencies.
"""

from __future__ import annotations

from typing import Any, Mapping

from .user_llm_router import RouteTransports, handle_user_llm_request


def handle_http_payload(
    payload: Mapping[str, Any],
    *,
    transports: RouteTransports | None = None,
) -> dict[str, Any]:
    """Handle one transport-neutral HTTP/MCP-compatible request payload."""
    return handle_user_llm_request(payload, transports=transports)


def create_app(*, transports: RouteTransports | None = None):
    """Create a FastAPI application without starting network listeners."""
    try:
        from fastapi import FastAPI
    except ImportError as exc:  # pragma: no cover - depends on optional extra
        raise RuntimeError(
            "FastAPI service dependencies are not installed; install the service extra"
        ) from exc

    app = FastAPI(
        title="StegVerse User-LLM Access",
        version="1.0.0",
        description=(
            "Bounded SDK-equivalent Demo/test access for an authorized user-controlled LLM"
        ),
    )

    @app.get("/v1/user-llm/capabilities")
    def capabilities() -> dict[str, Any]:
        from .user_llm_access import list_demo_capabilities

        return {
            "status": "OK",
            "participant_class": "authorized_user_llm",
            "capabilities": list(list_demo_capabilities()),
            "authority_attached": False,
        }

    @app.post("/v1/user-llm/requests")
    def submit_request(payload: dict[str, Any]) -> dict[str, Any]:
        return handle_http_payload(payload, transports=transports)

    @app.get("/healthz")
    def health() -> dict[str, Any]:
        configured = {
            "demo_test_suite": bool(transports and transports.demo_test_suite),
            "entity_sandbox_runner": bool(transports and transports.entity_sandbox_runner),
            "hil_response_packet": bool(transports and transports.hil_response_packet),
        }
        return {
            "status": "OK",
            "service": "stegverse-user-llm-access",
            "live_network_started_by_import": False,
            "route_transports": configured,
            "authority_attached": False,
        }

    return app
