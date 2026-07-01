"""Commitment request packets for downstream authority checks.

A commitment request is non-authorizing. It packages action candidates and the
adapter reconstruction state so a downstream governance layer can perform a
fresh commit-time standing determination.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence


COMMITMENT_REQUEST_SCHEMA_VERSION = "stegverse.llm_adapter.commitment_request.v0.1"


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def stable_hash(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class CommitmentRequestPacket:
    """Non-authorizing request for downstream commit-time standing."""

    action_route_hash: str
    action_candidates: tuple[Mapping[str, Any], ...]
    adapter_reconstruction_hash: str
    provider_request_hash: str
    provider_response_hash: str
    target: str
    status: str = "requires_downstream_commit_time_standing"
    requested_at: str = ""
    schema_version: str = COMMITMENT_REQUEST_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "requested_at": self.requested_at or utc_now_iso(),
            "status": self.status,
            "target": self.target,
            "action_route_hash": self.action_route_hash,
            "action_candidates": [dict(candidate) for candidate in self.action_candidates],
            "adapter_reconstruction_hash": self.adapter_reconstruction_hash,
            "provider_request_hash": self.provider_request_hash,
            "provider_response_hash": self.provider_response_hash,
            "commitment_request_hash": self.commitment_request_hash,
        }

    @property
    def commitment_request_hash(self) -> str:
        return stable_hash(
            {
                "schema_version": self.schema_version,
                "status": self.status,
                "target": self.target,
                "action_route_hash": self.action_route_hash,
                "action_candidates": [dict(candidate) for candidate in self.action_candidates],
                "adapter_reconstruction_hash": self.adapter_reconstruction_hash,
                "provider_request_hash": self.provider_request_hash,
                "provider_response_hash": self.provider_response_hash,
            }
        )


def build_commitment_request(
    *,
    session_result: Mapping[str, Any],
    target: str = "unresolved",
) -> dict[str, Any]:
    """Build a non-authorizing commitment request from a governed session."""

    action_route = dict(session_result.get("action_route", {}))
    action_candidates = tuple(action_route.get("action_candidates", ()))
    if not action_candidates:
        return {
            "schema_version": COMMITMENT_REQUEST_SCHEMA_VERSION,
            "status": "no_commitment_request_required",
            "commitment_request_hash": stable_hash({"status": "no_commitment_request_required"}),
        }

    adapter_result = dict(session_result.get("adapter_result", {}))
    provider_response = dict(session_result.get("provider_response", {}))
    packet = CommitmentRequestPacket(
        action_route_hash=stable_hash(action_route),
        action_candidates=action_candidates,
        adapter_reconstruction_hash=stable_hash(adapter_result.get("reconstruction", {})),
        provider_request_hash=str(session_result.get("provider_request_hash", "unresolved")),
        provider_response_hash=str(provider_response.get("response_hash", "unresolved")),
        target=target,
    )
    return packet.to_dict()


__all__ = [
    "COMMITMENT_REQUEST_SCHEMA_VERSION",
    "CommitmentRequestPacket",
    "build_commitment_request",
]
