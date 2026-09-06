from __future__ import annotations

from dataclasses import replace

import pytest

from llm_adapter.distributed_workload import (
    build_contribution,
    build_distributed_workload,
    build_governed_result,
    build_reconciliation_request,
    build_source_descriptor,
    build_source_provider_request,
    validate_contribution,
    validate_governed_result,
    validate_reconciliation_request,
    validate_workload,
)
from llm_adapter.provider_client import FixtureProviderClient, ProviderResponse


FIXED = "2026-09-06T06:00:00+00:00"
CANONICAL_REQUEST_HASH = "a" * 64


def source(source_id: str, provider: str, model: str, *, required: bool = False):
    return build_source_descriptor(
        source_id=source_id,
        provider=provider,
        model=model,
        capabilities=("reasoning", "text"),
        required=required,
        locality="sovereign" if source_id == "steg-local" else "external-optional",
        sovereignty="stegverse" if source_id == "steg-local" else "provider",
    )


def workload(mode: str = "parallel"):
    return build_distributed_workload(
        workload_id="workload:test:001",
        canonical_request_id="event:req:001",
        canonical_request_hash=CANONICAL_REQUEST_HASH,
        routing_mode=mode,
        sources=(
            source("steg-local", "stegverse-local", "stegverse-reference-lm-v1", required=True),
            source("named-source-b", "provider-b", "model-b"),
        ),
        purpose="answer",
        required_capabilities=("reasoning",),
        policy_refs=("policy:governed-answer",),
        governance_refs=("intr:ecosystem-chat",),
        created_at=FIXED,
    )


def request_for(w, source_id: str):
    return build_source_provider_request(
        w,
        source_id,
        [{"role": "user", "content": "Explain the represented transition."}],
        metadata={"fixture": True},
    )


def returned_contribution(w, source_id: str, output: str, disagreement_refs=()):
    req = request_for(w, source_id)
    response = FixtureProviderClient(output=output).complete(req)
    return build_contribution(
        w,
        source_id=source_id,
        request=req,
        response=response,
        provenance_refs=(f"provider:{source_id}", req.request_hash),
        evidence_refs=("evidence:fixture",),
        usage_refs=(f"usage:{source_id}",),
        disagreement_refs=disagreement_refs,
        created_at=FIXED,
    )


def test_parallel_workload_is_deterministic_with_fixed_time_and_preserves_named_sources():
    w1 = workload()
    w2 = workload()
    assert w1.to_dict() == w2.to_dict()
    assert w1.workload_hash == w2.workload_hash
    assert [item.source_id for item in w1.sources] == ["steg-local", "named-source-b"]
    assert w1.to_dict()["authority"] == {
        "grants_admission": False,
        "grants_execution": False,
        "grants_credentials": False,
        "grants_custody": False,
        "grants_governance": False,
    }


def test_two_source_contributions_reconcile_without_voting_authority():
    w = workload()
    a = returned_contribution(w, "steg-local", "Contribution A")
    b = returned_contribution(w, "named-source-b", "Contribution B", disagreement_refs=(a.contribution_hash,))

    reconciliation = build_reconciliation_request(
        w,
        (b, a),  # source order is normalized back to workload order
        governance_refs=("intr:decision:001",),
        created_at=FIXED,
    )
    assert reconciliation.source_ids == ("steg-local", "named-source-b")
    assert reconciliation.to_dict()["reconciliation_role"] == "EVIDENCE_FOR_EXISTING_GOVERNANCE"
    assert not any(reconciliation.to_dict()["authority"].values())

    result = build_governed_result(
        w,
        reconciliation,
        (a, b),
        disposition="ADMITTED",
        result_text="Governed synthesis of the represented contributions.",
        governance_refs=("intr:decision:001",),
        decision_refs=("decision:001",),
        provenance_refs=(a.contribution_hash, b.contribution_hash),
        created_at=FIXED,
    )
    assert result.source_ids == ("steg-local", "named-source-b")
    assert result.disposition == "ADMITTED"
    assert b.disagreement_refs == (a.contribution_hash,)
    assert not any(result.to_dict()["authority"].values())


def test_required_source_missing_fails_closed():
    w = workload()
    b = returned_contribution(w, "named-source-b", "Only optional source returned")
    with pytest.raises(ValueError, match="required source contribution missing"):
        build_reconciliation_request(w, (b,), governance_refs=("intr:decision:001",), created_at=FIXED)


def test_unknown_source_fails_closed():
    w = workload()
    with pytest.raises(ValueError, match="unknown source_id"):
        request_for(w, "not-declared")


def test_duplicate_source_ids_fail_closed():
    duplicate = source("same", "provider-a", "model-a")
    with pytest.raises(ValueError, match="duplicate source_id"):
        build_distributed_workload(
            workload_id="w",
            canonical_request_id="r",
            canonical_request_hash=CANONICAL_REQUEST_HASH,
            routing_mode="parallel",
            sources=(duplicate, replace(duplicate, provider="provider-b", model="model-b")),
            created_at=FIXED,
        )


def test_single_and_fallback_cardinality_fail_closed():
    sources = (source("a", "a", "a"), source("b", "b", "b"))
    with pytest.raises(ValueError, match="single routing_mode requires exactly one source"):
        build_distributed_workload(
            workload_id="w-single",
            canonical_request_id="r",
            canonical_request_hash=CANONICAL_REQUEST_HASH,
            routing_mode="single",
            sources=sources,
            created_at=FIXED,
        )
    with pytest.raises(ValueError, match="fallback routing_mode requires at least two"):
        build_distributed_workload(
            workload_id="w-fallback",
            canonical_request_id="r",
            canonical_request_hash=CANONICAL_REQUEST_HASH,
            routing_mode="fallback",
            sources=(sources[0],),
            created_at=FIXED,
        )


def test_embedded_provider_credentials_fail_closed():
    with pytest.raises(ValueError, match="embedded provider credential"):
        build_source_descriptor(
            source_id="bad",
            provider="provider",
            model="model",
            metadata={"api_key": "must-not-appear"},
        )
    with pytest.raises(ValueError, match="embedded provider credential"):
        build_distributed_workload(
            workload_id="bad",
            canonical_request_id="r",
            canonical_request_hash=CANONICAL_REQUEST_HASH,
            routing_mode="single",
            sources=(source("a", "a", "a"),),
            metadata={"nested": {"access_token": "must-not-appear"}},
            created_at=FIXED,
        )


def test_missing_contribution_provenance_fails_closed():
    w = workload()
    req = request_for(w, "steg-local")
    response = FixtureProviderClient(output="answer").complete(req)
    with pytest.raises(ValueError, match="provenance_refs are required"):
        build_contribution(
            w,
            source_id="steg-local",
            request=req,
            response=response,
            provenance_refs=(),
            created_at=FIXED,
        )


def test_response_request_hash_and_source_identity_mismatches_fail_closed():
    w = workload()
    req = request_for(w, "steg-local")
    bad_hash = ProviderResponse(
        provider=req.provider,
        model=req.model,
        output="answer",
        request_hash="b" * 64,
        metadata={},
    )
    with pytest.raises(ValueError, match="request_hash mismatch"):
        build_contribution(
            w,
            source_id="steg-local",
            request=req,
            response=bad_hash,
            provenance_refs=("provider:steg-local",),
            created_at=FIXED,
        )

    bad_identity = ProviderResponse(
        provider="different-provider",
        model=req.model,
        output="answer",
        request_hash=req.request_hash,
        metadata={},
    )
    with pytest.raises(ValueError, match="identity does not match declared source"):
        build_contribution(
            w,
            source_id="steg-local",
            request=req,
            response=bad_identity,
            provenance_refs=("provider:steg-local",),
            created_at=FIXED,
        )


def test_returned_contribution_requires_response_and_output():
    w = workload()
    req = request_for(w, "steg-local")
    with pytest.raises(ValueError, match="RETURNED contribution requires a provider response"):
        build_contribution(
            w,
            source_id="steg-local",
            request=req,
            response=None,
            status="RETURNED",
            provenance_refs=("provider:steg-local",),
            created_at=FIXED,
        )


def test_refusal_is_retained_as_evidence_without_becoming_failure_or_authority():
    w = workload()
    req = request_for(w, "steg-local")
    refused = build_contribution(
        w,
        source_id="steg-local",
        request=req,
        response=None,
        status="REFUSED",
        provenance_refs=("provider:steg-local",),
        uncertainty_notes=("source declined the request",),
        created_at=FIXED,
    )
    assert refused.status == "REFUSED"
    assert refused.output is None
    assert not any(refused.to_dict()["authority"].values())


def test_reconciliation_hash_mismatch_fails_closed():
    w = workload()
    a = returned_contribution(w, "steg-local", "A")
    b = returned_contribution(w, "named-source-b", "B")
    reconciliation = build_reconciliation_request(
        w, (a, b), governance_refs=("intr:decision:001",), created_at=FIXED
    )
    tampered = replace(reconciliation, contribution_hashes=("c" * 64, b.contribution_hash))
    with pytest.raises(ValueError, match="contribution hash mismatch"):
        validate_reconciliation_request(w, (a, b), tampered)


def test_admitted_result_requires_existing_governance_decision_refs_and_text():
    w = workload()
    a = returned_contribution(w, "steg-local", "A")
    b = returned_contribution(w, "named-source-b", "B")
    reconciliation = build_reconciliation_request(
        w, (a, b), governance_refs=("intr:decision:001",), created_at=FIXED
    )
    with pytest.raises(ValueError, match="requires result_text"):
        build_governed_result(
            w,
            reconciliation,
            (a, b),
            disposition="ADMITTED",
            result_text=None,
            governance_refs=("intr:decision:001",),
            decision_refs=("decision:001",),
            provenance_refs=(a.contribution_hash, b.contribution_hash),
            created_at=FIXED,
        )
    with pytest.raises(ValueError, match="requires decision_refs"):
        build_governed_result(
            w,
            reconciliation,
            (a, b),
            disposition="ADMITTED",
            result_text="answer",
            governance_refs=("intr:decision:001",),
            decision_refs=(),
            provenance_refs=(a.contribution_hash, b.contribution_hash),
            created_at=FIXED,
        )


def test_authority_escalation_is_rejected_by_validators():
    w = workload()
    assert validate_workload(w)
    a = returned_contribution(w, "steg-local", "A")
    assert validate_contribution(w, a)
    b = returned_contribution(w, "named-source-b", "B")
    reconciliation = build_reconciliation_request(w, (a, b), governance_refs=("intr:decision:001",), created_at=FIXED)
    assert validate_reconciliation_request(w, (a, b), reconciliation)
    result = build_governed_result(
        w,
        reconciliation,
        (a, b),
        disposition="DENIED",
        result_text=None,
        governance_refs=("intr:decision:001",),
        decision_refs=("decision:deny:001",),
        provenance_refs=(a.contribution_hash, b.contribution_hash),
        created_at=FIXED,
    )
    assert validate_governed_result(w, reconciliation, result)
