"""Commit-time action routing seam for governed LLM adapter.

The router turns high-consequence candidate output into non-executing action
candidates. It does not perform commits, sends, publications, memory writes, or
other side effects. Downstream governance must establish commit-time authority.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Optional, Sequence


ACTION_ROUTE_SCHEMA_VERSION = "stegverse.llm_adapter.action_route.v0.1"
ACTION_VERBS = ("publish", "commit", "send", "execute", "remember", "store", "memory")


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def stable_hash(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ActionCandidate:
    """Non-executing downstream action candidate."""

    action_type: str
    target: str
    basis_hash: str
    requested_by: str = "llm-adapter"
    status: str = "requires_commit_time_authority"
    notes: str = ""
    schema_version: str = ACTION_ROUTE_SCHEMA_VERSION

    def to_dict(self) -> dict[str, str]:
        return asdict(self)

    @property
    def candidate_hash(self) -> str:
        return stable_hash(self.to_dict())


@dataclass(frozen=True)
class ActionRoutePacket:
    """Packet returned when output must be routed instead of executed."""

    route_status: str
    action_candidates: tuple[ActionCandidate, ...]
    adapter_decision: str
    adapter_admissibility_status: str
    schema_version: str = ACTION_ROUTE_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "route_status": self.route_status,
            "adapter_decision": self.adapter_decision,
            "adapter_admissibility_status": self.adapter_admissibility_status,
            "action_candidates": [candidate.to_dict() for candidate in self.action_candidates],
            "action_candidate_hashes": [candidate.candidate_hash for candidate in self.action_candidates],
        }


def infer_action_type(text: str, purpose: Optional[str] = None) -> Optional[str]:
    """Infer a high-consequence action type from purpose or text."""

    if purpose in {"publish", "commit", "send", "execute", "mutate_memory"}:
        return purpose

    lowered = text.lower()
    if "publish" in lowered:
        return "publish"
    if "commit" in lowered:
        return "commit"
    if "send" in lowered or "email" in lowered:
        return "send"
    if "remember" in lowered or "store" in lowered or "memory" in lowered:
        return "mutate_memory"
    if "execute" in lowered or "run" in lowered:
        return "execute"
    return None


def build_action_route_packet(
    *,
    query: str,
    output: str,
    adapter_result: Mapping[str, Any],
    purpose: Optional[str] = None,
    target: str = "unresolved",
    requested_by: str = "llm-adapter",
) -> ActionRoutePacket:
    """Build a downstream route packet for consequence-bearing output."""

    action_type = infer_action_type("\n".join([query, output]), purpose)
    decision = str(adapter_result.get("decision", "UNRESOLVED"))
    status = str(adapter_result.get("admissibility_status", "unresolved"))

    if action_type is None and decision != "QUARANTINE":
        return ActionRoutePacket(
            route_status="no_action_route_required",
            action_candidates=(),
            adapter_decision=decision,
            adapter_admissibility_status=status,
        )

    candidate = ActionCandidate(
        action_type=action_type or "unclassified_high_consequence",
        target=target,
        basis_hash=stable_hash(
            {
                "query": query,
                "output": output,
                "adapter_result": dict(adapter_result),
            }
        ),
        requested_by=requested_by,
        notes="Candidate only. No consequence may attach until downstream commit-time authority passes.",
    )
    return ActionRoutePacket(
        route_status="route_to_commit_time_authority",
        action_candidates=(candidate,),
        adapter_decision=decision,
        adapter_admissibility_status=status,
    )


__all__ = [
    "ACTION_ROUTE_SCHEMA_VERSION",
    "ActionCandidate",
    "ActionRoutePacket",
    "build_action_route_packet",
    "infer_action_type",
]
