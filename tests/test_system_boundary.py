from copy import deepcopy

import pytest

from llm_adapter.system_boundary import (
    SurfaceConfig,
    SystemBoundaryConfig,
    build_system_boundary_declaration,
    default_adapter_system_boundary,
)


def test_builds_non_authorizing_runtime_declaration():
    declaration = build_system_boundary_declaration(
        default_adapter_system_boundary(receipt_refs=("receipt://adapter/001",)),
        declaration_id="sbd-adapter-001",
        generated_at="2026-07-14T12:00:00Z",
    )

    assert declaration["schema_version"] == "0.1"
    assert declaration["surfaces"]["model"]["persistence"] == "invocation"
    assert declaration["continuity"]["trajectory_dependent"] is True
    assert declaration["continuity"]["reconstructable"] is True
    assert declaration["authority"]["model_has_execution_authority"] is False
    assert declaration["claims_boundary"]["consciousness_claim"] == "not_evaluated"


def test_rejects_model_self_modification_claim():
    config = default_adapter_system_boundary()
    surfaces = dict(config.surfaces)
    surfaces["model"] = SurfaceConfig(True, "transient", "invocation", True)
    invalid = SystemBoundaryConfig(
        system_id=config.system_id,
        surfaces=surfaces,
        feedback_paths=config.feedback_paths,
        trajectory_dependent=config.trajectory_dependent,
        reconstructable=config.reconstructable,
        evidence_refs=config.evidence_refs,
        commit_boundary=config.commit_boundary,
        decision_source=config.decision_source,
        policy_refs=config.policy_refs,
        delegation_refs=config.delegation_refs,
    )

    with pytest.raises(ValueError, match="rewrite model state"):
        build_system_boundary_declaration(invalid, declaration_id="invalid")


def test_rejects_false_trajectory_dependence_without_feedback():
    config = default_adapter_system_boundary()
    invalid = SystemBoundaryConfig(
        system_id=config.system_id,
        surfaces=config.surfaces,
        feedback_paths=(),
        trajectory_dependent=True,
        reconstructable=config.reconstructable,
        evidence_refs=config.evidence_refs,
        commit_boundary=config.commit_boundary,
        decision_source=config.decision_source,
    )

    with pytest.raises(ValueError, match="requires an explicit feedback path"):
        build_system_boundary_declaration(invalid, declaration_id="invalid")


def test_rejects_reconstructability_without_evidence():
    config = default_adapter_system_boundary()
    invalid = SystemBoundaryConfig(
        system_id=config.system_id,
        surfaces=config.surfaces,
        feedback_paths=config.feedback_paths,
        trajectory_dependent=config.trajectory_dependent,
        reconstructable=True,
        evidence_refs=(),
        commit_boundary=config.commit_boundary,
        decision_source=config.decision_source,
    )

    with pytest.raises(ValueError, match="requires evidence_refs"):
        build_system_boundary_declaration(invalid, declaration_id="invalid")


def test_output_cannot_imply_consciousness_or_execution_authority():
    declaration = build_system_boundary_declaration(
        default_adapter_system_boundary(),
        declaration_id="sbd-adapter-002",
        generated_at="2026-07-14T12:00:00Z",
    )
    mutated = deepcopy(declaration)
    mutated["authority"]["model_has_execution_authority"] = True
    mutated["claims_boundary"]["consciousness_claim"] = "confirmed"

    assert declaration["authority"]["model_has_execution_authority"] is False
    assert declaration["claims_boundary"]["consciousness_claim"] == "not_evaluated"
    assert mutated != declaration
