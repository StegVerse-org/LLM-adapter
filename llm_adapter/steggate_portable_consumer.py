from __future__ import annotations

"""Thin Ecosystem Chat / user-LLM consumer for portable StegGate packages.

This module does not evaluate policy. It maps explicit governance facts into the
canonical StegCore `AdmissibilityRequest`, creates a transportable
`GovernedTransitionPackage`, and delegates evaluation/execution to the ephemeral
StegGate micro-node implementation shipped by StegCore.
"""

from dataclasses import dataclass
from typing import Any, Callable, Mapping, Optional, TypeVar

T = TypeVar("T")
EXPECTED_RUNTIME_IDENTITY = {
    "contract_version": "stegverse.steggate.runtime-identity.v1",
    "runtime_identity": "stegverse:steggate:canonical:three-layer:v1",
    "canonical_owner": "StegVerse-Labs/StegCore",
    "canonical_admissibility_runtime": "stegcore.three_layer.evaluate_three_layer",
}


def _stegcore():
    try:
        from stegcore.portable_steggate import create_governed_package, execute_governed_package
        from stegcore.service import runtime_identity
        from stegcore.steggate import (
            AdmissibilityRequest,
            ApprovalState,
            Candidate,
            CapabilityState,
            ContinuityState,
            ExecutionState,
            JudgmentState,
            SignalState,
        )
    except ImportError as exc:  # pragma: no cover - exercised by deployment packaging
        raise RuntimeError(
            "portable StegGate consumer requires the pinned canonical StegCore runtime"
        ) from exc
    return {
        "create_governed_package": create_governed_package,
        "execute_governed_package": execute_governed_package,
        "runtime_identity": runtime_identity,
        "AdmissibilityRequest": AdmissibilityRequest,
        "ApprovalState": ApprovalState,
        "Candidate": Candidate,
        "CapabilityState": CapabilityState,
        "ContinuityState": ContinuityState,
        "ExecutionState": ExecutionState,
        "JudgmentState": JudgmentState,
        "SignalState": SignalState,
    }


def canonical_runtime_identity() -> dict[str, Any]:
    """Return and validate the transport-independent canonical StegGate identity."""
    identity = dict(_stegcore()["runtime_identity"]())
    if any(identity.get(key) != value for key, value in EXPECTED_RUNTIME_IDENTITY.items()):
        raise RuntimeError("canonical StegGate runtime identity mismatch")
    if identity.get("transport_identity_authoritative") is not False:
        raise RuntimeError("transport identity cannot become StegGate authority")
    return identity


@dataclass(frozen=True)
class UserLLMIntent:
    user_id: str
    llm_id: str
    provider: str
    model: str
    prompt_hash: str
    route: str = "ecosystem_chat"
    action: str = "invoke_llm"


@dataclass(frozen=True)
class GovernanceFacts:
    refusal_available: bool
    operator_recoverability: str
    workload_state: str
    time_pressure: str
    isolation_state: str
    judgment_evidence_refs: tuple[str, ...]
    admitted_signal_refs: tuple[str, ...]
    missing_inputs: tuple[str, ...]
    uncertainty_state: str
    reference_state_hash: str
    expected_reference_state_hash: str
    reconstruction_available: bool
    transformation_provenance_complete: bool
    actor_authority_current: bool
    policy_current: bool
    delegation_current: bool
    evidence_current: bool
    affected_entity_conditions_represented: bool
    recoverability_profile: str
    validity_window_open: bool
    policy_ref: str
    delegation_ref: str
    execution_evidence_refs: tuple[str, ...]
    capability_allowed: bool
    continuity_required: bool
    previous_receipt_verified: Optional[bool]
    previous_receipt_hash: Optional[str]
    approval_required: bool = False
    approval_valid: Optional[bool] = None
    approval_candidate_hash: Optional[str] = None
    permission_present: Optional[bool] = None


def create_user_llm_governed_package(
    *,
    package_id: str,
    intent: UserLLMIntent,
    governance: GovernanceFacts,
    expires_at: Optional[str] = None,
    declared_execution_context: Optional[Mapping[str, Any]] = None,
):
    """Map explicit consumer facts into the canonical portable StegGate package."""

    s = _stegcore()
    identity = canonical_runtime_identity()
    identity_binding = {
        "steggate_contract_version": identity["contract_version"],
        "steggate_runtime_identity": identity["runtime_identity"],
        "steggate_canonical_owner": identity["canonical_owner"],
        "steggate_canonical_admissibility_runtime": identity["canonical_admissibility_runtime"],
    }
    request = s["AdmissibilityRequest"](
        candidate=s["Candidate"](
            actor_class="user_llm",
            action=intent.action,
            target=f"llm:{intent.provider}:{intent.model}",
            scope=intent.route,
            parameters={
                "user_id": intent.user_id,
                "llm_id": intent.llm_id,
                "provider": intent.provider,
                "model": intent.model,
                "prompt_hash": intent.prompt_hash,
                **identity_binding,
            },
        ),
        judgment=s["JudgmentState"](
            refusal_available=governance.refusal_available,
            operator_recoverability=governance.operator_recoverability,
            workload_state=governance.workload_state,
            time_pressure=governance.time_pressure,
            isolation_state=governance.isolation_state,
            evidence_refs=list(governance.judgment_evidence_refs),
        ),
        signal=s["SignalState"](
            admitted_signal_refs=list(governance.admitted_signal_refs),
            transformations=["llm_adapter.portable_steggate_consumer.v2"],
            missing_inputs=list(governance.missing_inputs),
            uncertainty_state=governance.uncertainty_state,
            reference_state_hash=governance.reference_state_hash,
            expected_reference_state_hash=governance.expected_reference_state_hash,
            reconstruction_available=governance.reconstruction_available,
            transformation_provenance_complete=governance.transformation_provenance_complete,
        ),
        execution=s["ExecutionState"](
            actor_authority_current=governance.actor_authority_current,
            policy_current=governance.policy_current,
            delegation_current=governance.delegation_current,
            evidence_current=governance.evidence_current,
            affected_entity_conditions_represented=governance.affected_entity_conditions_represented,
            recoverability_profile=governance.recoverability_profile,
            validity_window_open=governance.validity_window_open,
            policy_ref=governance.policy_ref,
            delegation_ref=governance.delegation_ref,
            evidence_refs=list(governance.execution_evidence_refs),
        ),
        capability=s["CapabilityState"](allowed=governance.capability_allowed),
        continuity=s["ContinuityState"](
            required=governance.continuity_required,
            previous_receipt_verified=governance.previous_receipt_verified,
            previous_receipt_hash=governance.previous_receipt_hash,
        ),
        approval=s["ApprovalState"](
            required=governance.approval_required,
            valid=governance.approval_valid,
            candidate_hash=governance.approval_candidate_hash,
        ),
        permission_present=governance.permission_present,
        declared_context={
            "consumer": "StegVerse-org/LLM-adapter",
            "route": intent.route,
            **identity_binding,
        },
    )

    return s["create_governed_package"](
        package_id=package_id,
        request=request,
        expires_at=expires_at,
        declared_execution_context=dict(declared_execution_context or {})
        | {
            "consumer": "StegVerse-org/LLM-adapter",
            "user_id": intent.user_id,
            "llm_id": intent.llm_id,
            "route": intent.route,
            **identity_binding,
        },
        capability_surface={
            "actions_exposed": [intent.action],
            "execution_mode": "manual",
            "requires_governed_commit": True,
        },
        authority_resolution={
            "status": "approved" if governance.actor_authority_current else "denied",
            "basis_invalidated_by_action": False,
        },
    )


def execute_user_llm_governed_package(package, provider_call: Callable[[], T]):
    """Run the provider callback only through the canonical ephemeral StegGate boundary."""

    return _stegcore()["execute_governed_package"](package, provider_call)
