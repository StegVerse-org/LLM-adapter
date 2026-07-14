from copy import deepcopy

import pytest

from llm_adapter.system_boundary import (
    build_system_boundary_declaration,
    default_adapter_system_boundary,
)
from llm_adapter.system_boundary_receipt import (
    build_system_boundary_receipt,
    derive_declaration_id,
    verify_system_boundary_receipt,
)


def _declaration():
    provisional = build_system_boundary_declaration(
        default_adapter_system_boundary(
            session_ref="session://test/001",
            receipt_refs=("receipt://adapter/test-001",),
        ),
        declaration_id="provisional",
        generated_at="2026-07-14T12:00:00Z",
    )
    provisional["declaration_id"] = derive_declaration_id(provisional)
    return provisional


def test_declaration_identity_ignores_observation_time():
    first = _declaration()
    second = deepcopy(first)
    second["generated_at"] = "2026-07-14T13:00:00Z"

    assert derive_declaration_id(first) == derive_declaration_id(second)


def test_declaration_identity_changes_with_runtime_boundary():
    first = _declaration()
    second = deepcopy(first)
    second["surfaces"]["memory"]["storage_refs"] = ["memory://different-store"]

    assert derive_declaration_id(first) != derive_declaration_id(second)


def test_receipt_reconstructs_deterministically():
    declaration = _declaration()
    first = build_system_boundary_receipt(
        declaration,
        source_commit="c5100464159c3e15119400bf4ba4748011ee2fc8",
    )
    second = build_system_boundary_receipt(
        declaration,
        source_commit="c5100464159c3e15119400bf4ba4748011ee2fc8",
    )

    assert first == second
    assert verify_system_boundary_receipt(declaration, first) is True
    assert first["authority_boundary"]["receipt_is_execution_authority"] is False
    assert first["authority_boundary"]["declaration_proves_consciousness"] is False


def test_receipt_rejects_noncanonical_supplied_identifier():
    declaration = _declaration()
    declaration["declaration_id"] = "sbd:incorrect"

    with pytest.raises(ValueError, match="does not match canonical content"):
        build_system_boundary_receipt(declaration)


def test_receipt_rejects_authority_escalation():
    declaration = _declaration()
    declaration["authority"]["model_has_execution_authority"] = True

    with pytest.raises(ValueError, match="model_has_execution_authority=false"):
        build_system_boundary_receipt(declaration)


def test_receipt_rejects_consciousness_reclassification():
    declaration = _declaration()
    declaration["claims_boundary"]["consciousness_claim"] = "confirmed"

    with pytest.raises(ValueError, match="consciousness_claim=not_evaluated"):
        build_system_boundary_receipt(declaration)
