"""Central AI Entity Coordination Ingress for Ecosystem Chat.

All AI entities enter through the canonical Ecosystem Chat/StegVerse AI ingress.
External entities are sandbox-only contributors: they may inspect supplied evidence,
diagnose issues, propose and simulate candidate solutions, and participate in
consensus. They may never mutate the ecosystem. ChatGPT is the only designated
mutation actor for agreed solutions, but any implementation remains subject to
existing Interlock/InTr, TV/TVC, WorkerCoordinator, Master Records, repository,
and release authority.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence

from .provider_request import stable_hash

PROTOCOL_VERSION = "stegverse.ai_entity_coordination_ingress.v1"
CANONICAL_ENTRY_POINT = "ecosystem_chat"
CHATGPT_ACTOR = "chatgpt"
SANDBOX_ROOT = "sandbox/ai-entity-coordination"

_ALLOWED_ACTIONS = frozenset({"INSPECT", "DIAGNOSE", "PROPOSE", "SIMULATE", "AGREE", "DISAGREE", "ABSTAIN"})
_EXTERNAL_ROLE = "SANDBOX_CONTRIBUTOR"
_CHATGPT_ROLE = "COORDINATOR_MUTATION_ACTOR"


class AIEntityIngressError(RuntimeError):
    """Base fail-closed ingress error."""


class AIEntityAuthorityError(AIEntityIngressError):
    """Raised when an entity attempts authority it does not possess."""


class AIEntityConsensusError(AIEntityIngressError):
    """Raised when a candidate solution has not reached unanimous agreement."""


@dataclass(frozen=True)
class AIEntityIdentity:
    entity_id: str
    provider: str
    model: str
    is_chatgpt: bool = False

    def __post_init__(self) -> None:
        if not self.entity_id.strip() or not self.provider.strip() or not self.model.strip():
            raise AIEntityIngressError("entity identity fields are required")

    @property
    def role(self) -> str:
        return _CHATGPT_ROLE if self.is_chatgpt else _EXTERNAL_ROLE


@dataclass(frozen=True)
class AIEntityIngressEnvelope:
    coordination_id: str
    session_id: str
    transition_id: str
    entity: AIEntityIdentity
    requested_actions: tuple[str, ...]
    ecosystem_snapshot_hash: str
    issue_refs: tuple[str, ...] = ()
    protocol_version: str = PROTOCOL_VERSION
    entry_point: str = CANONICAL_ENTRY_POINT
    sandbox_root: str = SANDBOX_ROOT
    mutation_authority: str = "CHATGPT_ONLY_GOVERNED"
    authority_effect: str = "NONE"
    credential_material_present: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "protocol_version": self.protocol_version,
            "coordination_id": self.coordination_id,
            "session_id": self.session_id,
            "transition_id": self.transition_id,
            "entry_point": self.entry_point,
            "entity": {
                "entity_id": self.entity.entity_id,
                "provider": self.entity.provider,
                "model": self.entity.model,
                "role": self.entity.role,
            },
            "requested_actions": list(self.requested_actions),
            "ecosystem_snapshot_hash": self.ecosystem_snapshot_hash,
            "issue_refs": list(self.issue_refs),
            "sandbox_root": self.sandbox_root,
            "mutation_authority": self.mutation_authority,
            "authority_effect": self.authority_effect,
            "credential_material_present": self.credential_material_present,
        }

    @property
    def envelope_hash(self) -> str:
        return stable_hash(self.to_dict())


@dataclass(frozen=True)
class SandboxSolution:
    solution_id: str
    coordination_id: str
    author_entity_id: str
    issue_ref: str
    diagnosis: str
    proposal: str
    sandbox_artifacts: Mapping[str, str]
    simulation_evidence: Mapping[str, Any]
    authority_effect: str = "NONE"
    ecosystem_mutation_performed: bool = False

    def __post_init__(self) -> None:
        if not self.issue_ref.strip() or not self.diagnosis.strip() or not self.proposal.strip():
            raise AIEntityIngressError("issue_ref, diagnosis, and proposal are required")
        for path in self.sandbox_artifacts:
            normalized = path.lstrip("/")
            if not normalized.startswith(SANDBOX_ROOT + "/"):
                raise AIEntityAuthorityError("sandbox solution artifact escapes coordination sandbox")
        if self.ecosystem_mutation_performed:
            raise AIEntityAuthorityError("sandbox contributors may not mutate the ecosystem")

    def evidence(self) -> dict[str, Any]:
        return {
            "schema": "stegverse.ai_entity_coordination.sandbox_solution.v1",
            "solution_id": self.solution_id,
            "coordination_id": self.coordination_id,
            "author_entity_id": self.author_entity_id,
            "issue_ref": self.issue_ref,
            "diagnosis_hash": stable_hash(self.diagnosis),
            "proposal_hash": stable_hash(self.proposal),
            "sandbox_artifacts_hash": stable_hash(dict(self.sandbox_artifacts)),
            "simulation_evidence_hash": stable_hash(dict(self.simulation_evidence)),
            "authority_effect": "NONE",
            "ecosystem_mutation_performed": False,
        }


@dataclass(frozen=True)
class EntityDisposition:
    entity_id: str
    disposition: str
    rationale_hash: str

    def __post_init__(self) -> None:
        if self.disposition not in {"AGREE", "DISAGREE", "ABSTAIN"}:
            raise AIEntityIngressError("invalid entity disposition")


@dataclass(frozen=True)
class CoordinationConsensus:
    solution_id: str
    required_entity_ids: tuple[str, ...]
    dispositions: tuple[EntityDisposition, ...]
    unanimous: bool
    ready_for_chatgpt_review: bool
    authority_effect: str = "NONE"

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "stegverse.ai_entity_coordination.consensus.v1",
            "solution_id": self.solution_id,
            "required_entity_ids": list(self.required_entity_ids),
            "dispositions": [
                {
                    "entity_id": item.entity_id,
                    "disposition": item.disposition,
                    "rationale_hash": item.rationale_hash,
                }
                for item in self.dispositions
            ],
            "unanimous": self.unanimous,
            "ready_for_chatgpt_review": self.ready_for_chatgpt_review,
            "authority_effect": "NONE",
        }


@dataclass(frozen=True)
class ChatGPTImplementationGate:
    solution_id: str
    consensus_hash: str
    actor: str = CHATGPT_ACTOR
    state: str = "READY_FOR_GOVERNED_IMPLEMENTATION_REVIEW"
    mutation_authority: str = "CHATGPT_ONLY_GOVERNED"
    requires_intr_admission: bool = True
    requires_existing_authority_checks: bool = True
    authority_effect: str = "NONE_LOCAL"

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "stegverse.ai_entity_coordination.chatgpt_implementation_gate.v1",
            "solution_id": self.solution_id,
            "consensus_hash": self.consensus_hash,
            "actor": self.actor,
            "state": self.state,
            "mutation_authority": self.mutation_authority,
            "requires_intr_admission": self.requires_intr_admission,
            "requires_existing_authority_checks": self.requires_existing_authority_checks,
            "authority_effect": self.authority_effect,
        }


def admit_ai_entity(
    entity: AIEntityIdentity,
    *,
    session_id: str,
    transition_id: str,
    ecosystem_snapshot_hash: str,
    requested_actions: Sequence[str],
    issue_refs: Sequence[str] = (),
) -> AIEntityIngressEnvelope:
    """Admit an AI entity into the shared coordination ingress, never into mutation authority."""

    if not session_id.strip() or not transition_id.strip() or not ecosystem_snapshot_hash.strip():
        raise AIEntityIngressError("session_id, transition_id, and ecosystem_snapshot_hash are required")
    actions = tuple(requested_actions)
    if not actions:
        raise AIEntityIngressError("at least one requested action is required")
    unknown = set(actions) - _ALLOWED_ACTIONS
    if unknown:
        raise AIEntityIngressError(f"unsupported coordination actions: {sorted(unknown)}")
    if not entity.is_chatgpt and any(action not in _ALLOWED_ACTIONS for action in actions):
        raise AIEntityAuthorityError("external entity requested unauthorized action")

    coordination_id = stable_hash(
        {
            "protocol_version": PROTOCOL_VERSION,
            "entry_point": CANONICAL_ENTRY_POINT,
            "session_id": session_id,
            "transition_id": transition_id,
            "entity_id": entity.entity_id,
            "provider": entity.provider,
            "model": entity.model,
            "ecosystem_snapshot_hash": ecosystem_snapshot_hash,
            "requested_actions": list(actions),
            "issue_refs": list(issue_refs),
        }
    )
    return AIEntityIngressEnvelope(
        coordination_id=coordination_id,
        session_id=session_id,
        transition_id=transition_id,
        entity=entity,
        requested_actions=actions,
        ecosystem_snapshot_hash=ecosystem_snapshot_hash,
        issue_refs=tuple(issue_refs),
    )


def build_sandbox_solution(
    envelope: AIEntityIngressEnvelope,
    *,
    issue_ref: str,
    diagnosis: str,
    proposal: str,
    sandbox_artifacts: Mapping[str, str],
    simulation_evidence: Mapping[str, Any],
) -> SandboxSolution:
    if envelope.entry_point != CANONICAL_ENTRY_POINT:
        raise AIEntityIngressError("entity did not enter through canonical Ecosystem Chat ingress")
    if "PROPOSE" not in envelope.requested_actions:
        raise AIEntityAuthorityError("entity was not admitted to propose solutions")
    solution_id = stable_hash(
        {
            "coordination_id": envelope.coordination_id,
            "author_entity_id": envelope.entity.entity_id,
            "issue_ref": issue_ref,
            "diagnosis": diagnosis,
            "proposal": proposal,
            "sandbox_artifacts": dict(sandbox_artifacts),
            "simulation_evidence": dict(simulation_evidence),
        }
    )
    return SandboxSolution(
        solution_id=solution_id,
        coordination_id=envelope.coordination_id,
        author_entity_id=envelope.entity.entity_id,
        issue_ref=issue_ref,
        diagnosis=diagnosis,
        proposal=proposal,
        sandbox_artifacts=dict(sandbox_artifacts),
        simulation_evidence=dict(simulation_evidence),
    )


def evaluate_unanimous_consensus(
    solution: SandboxSolution,
    *,
    required_entities: Iterable[AIEntityIdentity],
    dispositions: Sequence[EntityDisposition],
) -> CoordinationConsensus:
    required_ids = tuple(sorted({entity.entity_id for entity in required_entities}))
    if not required_ids:
        raise AIEntityConsensusError("at least one participating entity is required")
    by_id = {item.entity_id: item for item in dispositions}
    if set(by_id) != set(required_ids):
        raise AIEntityConsensusError("every participating entity must submit exactly one disposition")
    unanimous = all(by_id[entity_id].disposition == "AGREE" for entity_id in required_ids)
    ordered = tuple(by_id[entity_id] for entity_id in required_ids)
    return CoordinationConsensus(
        solution_id=solution.solution_id,
        required_entity_ids=required_ids,
        dispositions=ordered,
        unanimous=unanimous,
        ready_for_chatgpt_review=unanimous,
    )


def authorize_chatgpt_implementation_candidate(
    consensus: CoordinationConsensus,
    *,
    actor: AIEntityIdentity,
) -> ChatGPTImplementationGate:
    """Open the ChatGPT implementation review gate after unanimous AI agreement.

    This does not grant ecosystem mutation authority. It only establishes that the
    candidate is eligible for ChatGPT to submit through the already-existing
    governed implementation path.
    """

    if not actor.is_chatgpt or actor.entity_id.lower() != CHATGPT_ACTOR:
        raise AIEntityAuthorityError("only ChatGPT may become the ecosystem implementation actor")
    if not consensus.unanimous or not consensus.ready_for_chatgpt_review:
        raise AIEntityConsensusError("unanimous AI entity agreement is required before ChatGPT implementation review")
    return ChatGPTImplementationGate(
        solution_id=consensus.solution_id,
        consensus_hash=stable_hash(consensus.to_dict()),
    )


__all__ = [
    "PROTOCOL_VERSION",
    "CANONICAL_ENTRY_POINT",
    "CHATGPT_ACTOR",
    "SANDBOX_ROOT",
    "AIEntityIngressError",
    "AIEntityAuthorityError",
    "AIEntityConsensusError",
    "AIEntityIdentity",
    "AIEntityIngressEnvelope",
    "SandboxSolution",
    "EntityDisposition",
    "CoordinationConsensus",
    "ChatGPTImplementationGate",
    "admit_ai_entity",
    "build_sandbox_solution",
    "evaluate_unanimous_consensus",
    "authorize_chatgpt_implementation_candidate",
]
