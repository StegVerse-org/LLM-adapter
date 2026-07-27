"""Deployment readiness contract for the bounded user-LLM service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .user_llm_http_transport import HTTPRouteConfig

_REQUIRED_ROUTES = (
    "demo_test_suite",
    "entity_sandbox_runner",
    "hil_response_packet",
)


@dataclass(frozen=True)
class EndpointReadiness:
    state: str
    configured_routes: tuple[str, ...]
    missing_routes: tuple[str, ...]

    @property
    def ready(self) -> bool:
        return self.state == "READY"

    def as_public_dict(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "configured_routes": list(self.configured_routes),
            "missing_routes": list(self.missing_routes),
            "required_routes": list(_REQUIRED_ROUTES),
            "authority_attached": False,
            "execution_authority": False,
            "publication_authority": False,
            "continuity_authority": False,
            "master_record_custody": False,
        }


def evaluate_endpoint_readiness(config: HTTPRouteConfig | None = None) -> EndpointReadiness:
    active = config or HTTPRouteConfig.from_environment()
    route_urls = {
        "demo_test_suite": active.demo_test_suite_url,
        "entity_sandbox_runner": active.entity_sandbox_runner_url,
        "hil_response_packet": active.hil_response_packet_url,
    }
    configured = tuple(name for name in _REQUIRED_ROUTES if route_urls[name])
    missing = tuple(name for name in _REQUIRED_ROUTES if not route_urls[name])
    return EndpointReadiness(
        state="READY" if not missing else "DEFERRED",
        configured_routes=configured,
        missing_routes=missing,
    )
