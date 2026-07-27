"""Optional HTTP service for bounded user-LLM access."""

from __future__ import annotations

import os
from typing import Any, Mapping

from .user_llm_router import RouteTransports, handle_user_llm_request


def resolve_route_transports(
    transports: RouteTransports | None = None,
    *,
    load_environment: bool = True,
) -> RouteTransports:
    if transports is not None:
        return transports
    if not load_environment:
        return RouteTransports()
    from .user_llm_http_transport import build_http_route_transports
    return build_http_route_transports()


def handle_http_payload(
    payload: Mapping[str, Any],
    *,
    transports: RouteTransports | None = None,
    load_environment: bool = True,
) -> dict[str, Any]:
    resolved = resolve_route_transports(transports, load_environment=load_environment)
    return handle_user_llm_request(payload, transports=resolved)


def create_app(
    *,
    transports: RouteTransports | None = None,
    load_environment: bool = True,
):
    try:
        from fastapi import FastAPI
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("FastAPI service dependencies are not installed") from exc

    resolved = resolve_route_transports(transports, load_environment=load_environment)
    app = FastAPI(
        title="StegVerse User-LLM Access",
        version="1.0.0",
        description="Bounded SDK-equivalent Demo/test access for an authorized user-controlled LLM",
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
        return handle_http_payload(payload, transports=resolved, load_environment=False)

    @app.get("/healthz")
    def health() -> dict[str, Any]:
        return {
            "status": "OK",
            "service": "stegverse-user-llm-access",
            "live_network_started_by_import": False,
            "route_transports": {
                "demo_test_suite": bool(resolved.demo_test_suite),
                "entity_sandbox_runner": bool(resolved.entity_sandbox_runner),
                "hil_response_packet": bool(resolved.hil_response_packet),
            },
            "authority_attached": False,
        }

    return app


def main() -> int:
    try:
        import uvicorn
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("Uvicorn is not installed; install the service extra") from exc
    host = os.getenv("STEGVERSE_USER_LLM_HOST", "127.0.0.1")
    try:
        port = int(os.getenv("STEGVERSE_USER_LLM_PORT", "8080"))
    except ValueError as exc:
        raise RuntimeError("STEGVERSE_USER_LLM_PORT must be an integer") from exc
    if not 1 <= port <= 65535:
        raise RuntimeError("STEGVERSE_USER_LLM_PORT must be between 1 and 65535")
    uvicorn.run(
        create_app(),
        host=host,
        port=port,
        log_level=os.getenv("STEGVERSE_USER_LLM_LOG_LEVEL", "info"),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
