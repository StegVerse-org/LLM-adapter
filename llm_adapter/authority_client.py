"""Downstream authority client seam for commitment requests.

Authority evaluation is still non-executing. It determines whether a commitment
request may proceed to a separate execution layer, must be denied, or must fail
closed because required standing is unresolved.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Optional, Protocol


AUTHORITY_DECISION_SCHEMA_VERSION = "stegverse.llm_adapter.authority_decision.v0.1"


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def stable_hash(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class AuthorityDecision:
    """Non-executing standing decision for a commitment request."""

    decision: str
    reason: str
    commitment_request_hash: str
    policy_hash: str = "unresolved"
    delegation_hash: str = "unresolved"
    decided_at: str = ""
    schema_version: str = AUTHORITY_DECISION_SCHEMA_VERSION

    def to_dict(self) -> dict[str, str]:
        return {
            "schema_version": self.schema_version,
            "decided_at": self.decided_at or utc_now_iso(),
            "decision": self.decision,
            "reason": self.reason,
            "commitment_request_hash": self.commitment_request_hash,
            "policy_hash": self.policy_hash,
            "delegation_hash": self.delegation_hash,
            "authority_decision_hash": self.authority_decision_hash,
        }

    @property
    def authority_decision_hash(self) -> str:
        return stable_hash(
            {
                "schema_version": self.schema_version,
                "decision": self.decision,
                "reason": self.reason,
                "commitment_request_hash": self.commitment_request_hash,
                "policy_hash": self.policy_hash,
                "delegation_hash": self.delegation_hash,
            }
        )


class AuthorityClient(Protocol):
    """Authority client protocol for downstream standing checks."""

    def evaluate(self, commitment_request: Mapping[str, Any]) -> AuthorityDecision:
        """Evaluate a commitment request without executing it."""


@dataclass(frozen=True)
class FixtureAuthorityClient:
    """Deterministic authority client for local tests.

    By default, it fails closed unless explicitly configured to allow. This keeps
    the fixture path conservative and prevents scaffolding from implying authority.
    """

    decision: str = "FAIL_CLOSED"
    reason: str = "fixture authority does not grant execution by default"
    policy_hash: str = "fixture-policy"
    delegation_hash: str = "fixture-delegation"

    def evaluate(self, commitment_request: Mapping[str, Any]) -> AuthorityDecision:
        status = str(commitment_request.get("status", "unresolved"))
        request_hash = str(commitment_request.get("commitment_request_hash", "unresolved"))
        if status == "no_commitment_request_required":
            return AuthorityDecision(
                decision="NOT_REQUIRED",
                reason="read-only session did not require commitment standing",
                commitment_request_hash=request_hash,
                policy_hash=self.policy_hash,
                delegation_hash=self.delegation_hash,
            )
        if status != "requires_downstream_commit_time_standing":
            return AuthorityDecision(
                decision="FAIL_CLOSED",
                reason="commitment request status is unresolved or malformed",
                commitment_request_hash=request_hash,
                policy_hash=self.policy_hash,
                delegation_hash=self.delegation_hash,
            )
        return AuthorityDecision(
            decision=self.decision,
            reason=self.reason,
            commitment_request_hash=request_hash,
            policy_hash=self.policy_hash,
            delegation_hash=self.delegation_hash,
        )


def evaluate_commitment_request(
    commitment_request: Mapping[str, Any],
    authority_client: Optional[AuthorityClient] = None,
) -> dict[str, str]:
    """Evaluate a commitment request through an authority client."""

    client = authority_client or FixtureAuthorityClient()
    return client.evaluate(commitment_request).to_dict()


__all__ = [
    "AUTHORITY_DECISION_SCHEMA_VERSION",
    "AuthorityClient",
    "AuthorityDecision",
    "FixtureAuthorityClient",
    "evaluate_commitment_request",
]
