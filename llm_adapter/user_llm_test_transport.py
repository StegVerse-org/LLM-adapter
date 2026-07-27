"""Explicit non-authoritative local transports for deployment smoke testing."""

from __future__ import annotations

from hashlib import sha256
from json import dumps
from typing import Any, Mapping

from .user_llm_router import RouteTransports


def _fixture_transport(route: str):
    def transport(envelope: Mapping[str, Any]) -> Mapping[str, Any]:
        canonical = dumps(dict(envelope), sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
        return {
            "status": "TEST_RETURNED",
            "route": route,
            "request_hash": envelope.get("request_hash"),
            "fixture_result_hash": sha256(canonical).hexdigest(),
            "test_mode": True,
            "downstream_execution_verified": False,
            "authority_attached": False,
            "execution_authority": False,
            "publication_authority": False,
            "continuity_authority": False,
            "master_record_custody": False,
        }

    return transport


def build_test_route_transports() -> RouteTransports:
    """Return deterministic local transports only for explicitly enabled smoke tests."""
    return RouteTransports(
        demo_test_suite=_fixture_transport("demo_test_suite"),
        entity_sandbox_runner=_fixture_transport("entity_sandbox_runner"),
        hil_response_packet=_fixture_transport("hil_response_packet"),
    )
