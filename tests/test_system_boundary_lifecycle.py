from copy import deepcopy

import pytest

from llm_adapter.system_boundary_lifecycle import bind_system_boundary_to_lifecycle
from llm_adapter.system_boundary_receipt import verify_system_boundary_receipt


def sample_response():
    return {
        "transition_id": "transition-001",
        "run_id": "run-001",
        "receipt_id": "gateway-receipt:001",
        "final_receipt_id": "final-receipt:001",
        "lifecycle_state": "COMPLETED",
        "authority": {
            "repository_mutation_allowed": False,
            "publication_allowed": False,
            "local_persistence_is_master_records_custody": False,
        },
    }


def bind(payload=None, **overrides):
    kwargs = {
        "session_id": "session-001",
        "transition_id": "transition-001",
        "run_id": "run-001",
        "generated_at": "2026-07-14T13:00:00Z",
        "source_commit": "commit-001",
    }
    kwargs.update(overrides)
    return bind_system_boundary_to_lifecycle(payload or sample_response(), **kwargs)


def test_binds_after_governed_response_without_authority_or_custody_escalation():
    source = sample_response()
    result = bind(source)

    assert "system_boundary_declaration" not in source
    assert verify_system_boundary_receipt(
        result["system_boundary_declaration"],
        result["system_boundary_declaration_receipt"],
    )
    reference = result["system_boundary_declaration_ref"]
    assert reference["authorizing"] is False
    assert reference["custody_transferred"] is False
    assert reference["admissibility_determined"] is False
    assert reference["production_binding_enabled"] is False
    assert result["authority"]["system_boundary_declaration_is_execution_authority"] is False
    assert result["authority"]["system_boundary_receipt_is_master_records_custody"] is False


def test_binding_persists_session_transition_run_and_receipt_evidence():
    result = bind()
    declaration = result["system_boundary_declaration"]

    assert declaration["surfaces"]["session"]["storage_refs"] == ["session://session-001"]
    assert declaration["continuity"]["evidence_refs"] == [
        "transition://transition-001",
        "run://run-001",
        "final-receipt:001",
        "gateway-receipt:001",
    ]


def test_identical_replay_is_idempotent():
    first = bind()
    second = bind(first)

    assert second == first


def test_material_lifecycle_change_produces_new_identity():
    first = bind()
    changed = sample_response()
    changed["final_receipt_id"] = "final-receipt:002"
    second = bind(changed)

    assert first["system_boundary_declaration_ref"]["declaration_id"] != second["system_boundary_declaration_ref"]["declaration_id"]
    assert first["system_boundary_declaration_receipt"]["receipt_hash"] != second["system_boundary_declaration_receipt"]["receipt_hash"]


def test_rejects_transition_or_run_identity_mismatch():
    with pytest.raises(ValueError, match="transition_id"):
        bind(transition_id="transition-other")

    with pytest.raises(ValueError, match="run_id"):
        bind(run_id="run-other")


def test_rejects_partial_prior_binding():
    payload = sample_response()
    payload["system_boundary_declaration_ref"] = {}

    with pytest.raises(ValueError, match="partial"):
        bind(payload)


def test_rejects_tampered_prior_receipt():
    payload = bind()
    tampered = deepcopy(payload)
    tampered["system_boundary_declaration_receipt"]["receipt_hash"] = "sha256:" + "0" * 64

    with pytest.raises(ValueError, match="verification failed"):
        bind(tampered)


def test_receipt_chain_changes_receipt_not_declaration_identity():
    first = bind(previous_receipt_hash=None)
    second = bind(previous_receipt_hash="sha256:" + "1" * 64)

    assert first["system_boundary_declaration_ref"]["declaration_id"] == second["system_boundary_declaration_ref"]["declaration_id"]
    assert first["system_boundary_declaration_receipt"]["receipt_hash"] != second["system_boundary_declaration_receipt"]["receipt_hash"]
