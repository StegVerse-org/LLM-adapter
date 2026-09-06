import pytest

from llm_adapter.ai_entity_coordination_ingress import (
    AIEntityAuthorityError,
    AIEntityConsensusError,
    AIEntityIdentity,
    EntityDisposition,
    SANDBOX_ROOT,
    admit_ai_entity,
    authorize_chatgpt_implementation_candidate,
    build_sandbox_solution,
    evaluate_unanimous_consensus,
)


def _entity(entity_id: str, provider: str = "example", model: str = "model", *, chatgpt: bool = False):
    return AIEntityIdentity(entity_id=entity_id, provider=provider, model=model, is_chatgpt=chatgpt)


def _solution(entity=None):
    entity = entity or _entity("claude", "anthropic", "claude")
    envelope = admit_ai_entity(
        entity,
        session_id="session-1",
        transition_id="transition-1",
        ecosystem_snapshot_hash="snapshot-hash",
        requested_actions=["INSPECT", "DIAGNOSE", "PROPOSE", "SIMULATE", "AGREE"],
        issue_refs=["StegVerse-org/LLM-adapter#282"],
    )
    return build_sandbox_solution(
        envelope,
        issue_ref="StegVerse-org/LLM-adapter#282",
        diagnosis="bounded diagnosis",
        proposal="bounded solution",
        sandbox_artifacts={f"{SANDBOX_ROOT}/claude/patch.diff": "diff --git ..."},
        simulation_evidence={"tests": "PASS", "ecosystem_mutation": False},
    )


def test_external_entity_enters_same_ecosystem_chat_ingress_without_mutation_authority():
    envelope = admit_ai_entity(
        _entity("deepseek", "deepseek", "deepseek-model"),
        session_id="s",
        transition_id="t",
        ecosystem_snapshot_hash="snapshot",
        requested_actions=["INSPECT", "DIAGNOSE", "PROPOSE", "SIMULATE"],
    )
    assert envelope.entry_point == "ecosystem_chat"
    assert envelope.entity.role == "SANDBOX_CONTRIBUTOR"
    assert envelope.mutation_authority == "CHATGPT_ONLY_GOVERNED"
    assert envelope.authority_effect == "NONE"
    assert envelope.credential_material_present is False


def test_sandbox_solution_cannot_escape_coordination_root():
    envelope = admit_ai_entity(
        _entity("kimi", "moonshot", "kimi"),
        session_id="s",
        transition_id="t",
        ecosystem_snapshot_hash="snapshot",
        requested_actions=["PROPOSE"],
    )
    with pytest.raises(AIEntityAuthorityError):
        build_sandbox_solution(
            envelope,
            issue_ref="issue",
            diagnosis="diagnosis",
            proposal="proposal",
            sandbox_artifacts={"llm_adapter/unsafe.py": "mutation"},
            simulation_evidence={},
        )


def test_unanimous_consensus_requires_every_participating_entity():
    solution = _solution()
    entities = [_entity("claude"), _entity("kimi")]
    with pytest.raises(AIEntityConsensusError):
        evaluate_unanimous_consensus(
            solution,
            required_entities=entities,
            dispositions=[EntityDisposition("claude", "AGREE", "a" * 64)],
        )


def test_disagreement_is_preserved_and_blocks_chatgpt_gate():
    solution = _solution()
    entities = [_entity("claude"), _entity("kimi"), _entity("deepseek")]
    consensus = evaluate_unanimous_consensus(
        solution,
        required_entities=entities,
        dispositions=[
            EntityDisposition("claude", "AGREE", "a" * 64),
            EntityDisposition("kimi", "DISAGREE", "b" * 64),
            EntityDisposition("deepseek", "AGREE", "c" * 64),
        ],
    )
    assert consensus.unanimous is False
    assert consensus.ready_for_chatgpt_review is False
    with pytest.raises(AIEntityConsensusError):
        authorize_chatgpt_implementation_candidate(
            consensus,
            actor=_entity("chatgpt", "openai", "gpt", chatgpt=True),
        )


def test_only_chatgpt_can_open_implementation_review_gate():
    solution = _solution()
    entities = [_entity("claude"), _entity("kimi")]
    consensus = evaluate_unanimous_consensus(
        solution,
        required_entities=entities,
        dispositions=[
            EntityDisposition("claude", "AGREE", "a" * 64),
            EntityDisposition("kimi", "AGREE", "b" * 64),
        ],
    )
    with pytest.raises(AIEntityAuthorityError):
        authorize_chatgpt_implementation_candidate(
            consensus,
            actor=_entity("claude", "anthropic", "claude"),
        )


def test_unanimous_consensus_opens_non_authorizing_chatgpt_review_gate():
    solution = _solution()
    entities = [_entity("claude"), _entity("kimi"), _entity("deepseek"), _entity("chatgpt", "openai", "gpt", chatgpt=True)]
    consensus = evaluate_unanimous_consensus(
        solution,
        required_entities=entities,
        dispositions=[
            EntityDisposition("claude", "AGREE", "a" * 64),
            EntityDisposition("kimi", "AGREE", "b" * 64),
            EntityDisposition("deepseek", "AGREE", "c" * 64),
            EntityDisposition("chatgpt", "AGREE", "d" * 64),
        ],
    )
    gate = authorize_chatgpt_implementation_candidate(
        consensus,
        actor=_entity("chatgpt", "openai", "gpt", chatgpt=True),
    )
    assert gate.actor == "chatgpt"
    assert gate.state == "READY_FOR_GOVERNED_IMPLEMENTATION_REVIEW"
    assert gate.requires_intr_admission is True
    assert gate.requires_existing_authority_checks is True
    assert gate.authority_effect == "NONE_LOCAL"
