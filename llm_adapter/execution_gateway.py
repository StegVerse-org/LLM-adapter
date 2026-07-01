"""Disabled execution gateway for governed LLM adapter.

This module separates authority decisions from side-effect execution. The default
fixture gateway never executes. It produces a handoff receipt so downstream
execution layers can be connected explicitly and reviewed separately.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Optional, Protocol


EXECUTION_GATEWAY_SCHEMA_VERSION = "stegverse.llm_adapter.execution_gateway.v0.1"


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def stable_hash(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class ExecutionHandoff:
    """Non-executing handoff packet for an external execution layer."""

    status: str
    reason: str
    authority_decision_hash: str
    commitment_request_hash: str
    target: str
    created_at: str = ""
    schema_version: str = EXECUTION_GATEWAY_SCHEMA_VERSION

    def to_dict(self) -> dict[str, str]:
        return {
            "schema_version": self.schema_version,
            "created_at": self.created_at or utc_now_iso(),
            "status": self.status,
            "reason": self.reason,
            "authority_decision_hash": self.authority_decision_hash,
            "commitment_request_hash": self.commitment_request_hash,
            "target": self.target,
            "execution_handoff_hash": self.execution_handoff_hash,
        }

    @property
    def execution_handoff_hash(self) -> str:
        return stable_hash(
            {
                "schema_version": self.schema_version,
                "status": self.status,
                "reason": self.reason,
                "authority_decision_hash": self.authority_decision_hash,
                "commitment_request_hash": self.commitment_request_hash,
                "target": self.target,
            }
        )


class ExecutionGateway(Protocol):
    """Execution gateway protocol.

    Implementations may perform side effects only outside the default adapter
    runtime and only after separate review. The built-in fixture never executes.
    """

    def prepare_handoff(
        self,
        *,
        commitment_request: Mapping[str, Any],
        authority_decision: Mapping[str, Any],
    ) -> ExecutionHandoff:
        """Prepare an execution handoff packet."""


@dataclass(frozen=True)
class DisabledExecutionGateway:
    """Default non-executing gateway."""

    reason: str = "execution gateway disabled; no side effect performed"

    def prepare_handoff(
        self,
        *,
        commitment_request: Mapping[str, Any],
        authority_decision: Mapping[str, Any],
    ) -> ExecutionHandoff:
        decision = str(authority_decision.get("decision", "FAIL_CLOSED"))
        status = "ready_for_external_executor" if decision == "ALLOW" else "not_executable"
        return ExecutionHandoff(
            status=status,
            reason=self.reason if decision == "ALLOW" else "authority decision does not allow execution",
            authority_decision_hash=str(authority_decision.get("authority_decision_hash", "unresolved")),
            commitment_request_hash=str(commitment_request.get("commitment_request_hash", "unresolved")),
            target=str(commitment_request.get("target", "unresolved")),
        )


def prepare_execution_handoff(
    *,
    commitment_request: Mapping[str, Any],
    authority_decision: Mapping[str, Any],
    gateway: Optional[ExecutionGateway] = None,
) -> dict[str, str]:
    """Prepare a non-executing handoff packet."""

    selected_gateway = gateway or DisabledExecutionGateway()
    return selected_gateway.prepare_handoff(
        commitment_request=commitment_request,
        authority_decision=authority_decision,
    ).to_dict()


__all__ = [
    "EXECUTION_GATEWAY_SCHEMA_VERSION",
    "DisabledExecutionGateway",
    "ExecutionGateway",
    "ExecutionHandoff",
    "prepare_execution_handoff",
]
