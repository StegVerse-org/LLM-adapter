"""Runtime system-boundary declaration generation for the LLM adapter.

This module inventories operational state and authority surfaces. It does not
classify consciousness, personhood, welfare status, or execution standing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

SURFACE_NAMES = ("model", "orchestration", "session", "memory", "environment")
VALID_STATE_KINDS = {"none", "transient", "session", "durable", "external"}
VALID_PERSISTENCE = {"none", "invocation", "session", "cross-session", "indefinite"}
VALID_DECISION_SOURCES = {"policy-engine", "human", "quorum", "none"}


@dataclass(frozen=True)
class SurfaceConfig:
    present: bool
    state_kind: str
    persistence: str
    mutable_by_inference: bool
    storage_refs: tuple[str, ...] = field(default_factory=tuple)

    def validate(self, name: str) -> None:
        if self.state_kind not in VALID_STATE_KINDS:
            raise ValueError(f"surface {name}.state_kind invalid")
        if self.persistence not in VALID_PERSISTENCE:
            raise ValueError(f"surface {name}.persistence invalid")
        if any(not isinstance(ref, str) or not ref for ref in self.storage_refs):
            raise ValueError(f"surface {name}.storage_refs must contain non-empty strings")

    def to_dict(self) -> dict[str, Any]:
        return {
            "present": self.present,
            "state_kind": self.state_kind,
            "persistence": self.persistence,
            "mutable_by_inference": self.mutable_by_inference,
            "storage_refs": list(self.storage_refs),
        }


@dataclass(frozen=True)
class SystemBoundaryConfig:
    system_id: str
    surfaces: Mapping[str, SurfaceConfig]
    feedback_paths: tuple[str, ...]
    trajectory_dependent: bool
    reconstructable: bool
    evidence_refs: tuple[str, ...]
    commit_boundary: str
    decision_source: str
    policy_refs: tuple[str, ...] = field(default_factory=tuple)
    delegation_refs: tuple[str, ...] = field(default_factory=tuple)

    def validate(self) -> None:
        if not self.system_id:
            raise ValueError("system_id is required")
        if set(self.surfaces) != set(SURFACE_NAMES):
            raise ValueError("surface set must be exact")
        for name in SURFACE_NAMES:
            self.surfaces[name].validate(name)
        model = self.surfaces["model"]
        if model.persistence != "invocation":
            raise ValueError("model persistence must remain invocation-scoped")
        if model.mutable_by_inference:
            raise ValueError("inference must not claim to rewrite model state")
        if self.decision_source not in VALID_DECISION_SOURCES:
            raise ValueError("decision_source invalid")
        if not self.commit_boundary:
            raise ValueError("commit_boundary is required")
        if any(not isinstance(path, str) or not path for path in self.feedback_paths):
            raise ValueError("feedback_paths must contain non-empty strings")
        if self.trajectory_dependent and not self.feedback_paths:
            raise ValueError("trajectory dependence requires an explicit feedback path")
        if self.reconstructable and not self.evidence_refs:
            raise ValueError("reconstructable continuity requires evidence_refs")


def build_system_boundary_declaration(
    config: SystemBoundaryConfig,
    *,
    declaration_id: str,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Build a deterministic, non-authorizing system-boundary declaration."""

    config.validate()
    if not declaration_id:
        raise ValueError("declaration_id is required")
    timestamp = generated_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    return {
        "schema_version": "0.1",
        "declaration_id": declaration_id,
        "system_id": config.system_id,
        "generated_at": timestamp,
        "surfaces": {name: config.surfaces[name].to_dict() for name in SURFACE_NAMES},
        "continuity": {
            "prior_state_can_affect_future_transition": bool(config.feedback_paths),
            "feedback_paths": list(config.feedback_paths),
            "trajectory_dependent": config.trajectory_dependent,
            "reconstructable": config.reconstructable,
            "evidence_refs": list(config.evidence_refs),
        },
        "authority": {
            "model_has_execution_authority": False,
            "commit_boundary": config.commit_boundary,
            "decision_source": config.decision_source,
            "policy_refs": list(config.policy_refs),
            "delegation_refs": list(config.delegation_refs),
        },
        "claims_boundary": {
            "consciousness_claim": "not_evaluated",
            "personhood_claim": "not_evaluated",
            "welfare_claim": "not_evaluated",
            "scope_note": "This declaration describes operational state and authority boundaries only.",
        },
    }


def default_adapter_system_boundary(
    *,
    system_id: str = "stegverse-llm-adapter",
    session_ref: str = "session://current",
    receipt_refs: Sequence[str] = ("receipt://adapter/pending",),
) -> SystemBoundaryConfig:
    """Return the bounded default inventory for the deployed adapter surface."""

    return SystemBoundaryConfig(
        system_id=system_id,
        surfaces={
            "model": SurfaceConfig(True, "transient", "invocation", False),
            "orchestration": SurfaceConfig(True, "session", "session", True, (session_ref,)),
            "session": SurfaceConfig(True, "session", "session", True, (session_ref,)),
            "memory": SurfaceConfig(True, "durable", "cross-session", False, ("memory://governed-record-store",)),
            "environment": SurfaceConfig(True, "external", "indefinite", False, ("environment://tool-observation-receipts",)),
        },
        feedback_paths=(
            "model-output->orchestration-state",
            "orchestration-state->future-model-input",
            "environment-observation->session-continuity",
        ),
        trajectory_dependent=True,
        reconstructable=True,
        evidence_refs=tuple(receipt_refs),
        commit_boundary="governed-transition/commitment-request",
        decision_source="policy-engine",
        policy_refs=("policy://governed-llm/default",),
    )
