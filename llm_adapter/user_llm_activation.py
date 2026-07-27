"""Deterministic activation-proof projection for bounded user-LLM routes."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from json import dumps
from typing import Any

from .user_llm_http_transport import HTTPRouteConfig

_REQUIRED_ROUTES = ("demo_test_suite", "entity_sandbox_runner", "hil_response_packet")


@dataclass(frozen=True)
class RouteActivationProof:
    route: str
    configured: bool
    endpoint_hash: str | None

    def as_dict(self) -> dict[str, Any]:
        return {"route": self.route, "configured": self.configured, "endpoint_hash": self.endpoint_hash}


@dataclass(frozen=True)
class ActivationProof:
    schema_version: str
    state: str
    routes: tuple[RouteActivationProof, ...]
    proof_hash: str

    @property
    def activated(self) -> bool:
        return self.state == "ACTIVATED"

    def as_public_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "state": self.state,
            "routes": [route.as_dict() for route in self.routes],
            "proof_hash": self.proof_hash,
            "authority_attached": False,
            "execution_authority": False,
            "publication_authority": False,
            "continuity_authority": False,
            "master_record_custody": False,
        }


def _hash_endpoint(url: str | None) -> str | None:
    return sha256(url.encode("utf-8")).hexdigest() if url else None


def build_activation_proof(config: HTTPRouteConfig | None = None) -> ActivationProof:
    """Build a secret-free proof that all required route endpoints are configured."""
    active = config or HTTPRouteConfig.from_environment()
    urls = {
        "demo_test_suite": active.demo_test_suite_url,
        "entity_sandbox_runner": active.entity_sandbox_runner_url,
        "hil_response_packet": active.hil_response_packet_url,
    }
    routes = tuple(
        RouteActivationProof(route=name, configured=bool(urls[name]), endpoint_hash=_hash_endpoint(urls[name]))
        for name in _REQUIRED_ROUTES
    )
    state = "ACTIVATED" if all(route.configured for route in routes) else "DEFERRED"
    canonical = dumps(
        {"schema_version": "user-llm-endpoint-activation-v1", "state": state, "routes": [r.as_dict() for r in routes]},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return ActivationProof(
        schema_version="user-llm-endpoint-activation-v1",
        state=state,
        routes=routes,
        proof_hash=sha256(canonical).hexdigest(),
    )
