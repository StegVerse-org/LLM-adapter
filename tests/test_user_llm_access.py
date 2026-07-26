import pytest

from llm_adapter.user_llm_access import (
    AccessDenied,
    AccessRequest,
    UserLLMIdentity,
    build_hil_pdf_submission,
    build_submission,
    list_demo_capabilities,
)


def identity() -> UserLLMIdentity:
    return UserLLMIdentity(
        user_id="user-001",
        llm_id="external-llm-001",
        provider="fixture-provider",
        model="fixture-model",
        scopes=("demo:read", "demo:submit", "sandbox:submit"),
    )


def test_capability_catalog_exposes_original_routes():
    ids = {item["capability_id"] for item in list_demo_capabilities()}
    assert ids == {"demo_test_suite", "entity_sandbox_runner", "hil_response_packet"}


def test_demo_submission_is_user_class_and_non_authorizing():
    result = build_submission(
        AccessRequest(
            identity=identity(),
            route="demo_test_suite",
            action="configure",
            payload={"test_id": "TA-14", "parameters": {"mode": "comparison"}},
        )
    )
    assert result["participant_class"] == "authorized_user_llm"
    assert result["authority"]["sdk_equivalent_demo_access"] is True
    assert result["authority"]["execution_authority"] is False
    assert result["status"] == "ready_for_governed_routing"


def test_entity_sandbox_submission_is_supported():
    result = build_submission(
        AccessRequest(
            identity=identity(),
            route="entity_sandbox_runner",
            action="submit",
            payload={"bundle_ref": "sha256:fixture"},
        )
    )
    assert result["route"] == "entity_sandbox_runner"


def test_unknown_route_fails_closed():
    with pytest.raises(AccessDenied):
        build_submission(
            AccessRequest(
                identity=identity(),
                route="production_execution",
                action="execute",
                payload={},
            )
        )


def test_hil_pdf_submission_is_bounded_and_hash_bound():
    result = build_hil_pdf_submission(
        identity(),
        filename="HIL-TRACE-0001-response.pdf",
        sha256_hex="a" * 64,
        size_bytes=2048,
        trace_id="HIL-TRACE-0001",
        participant_review_status="reviewed",
    )
    assert result["route"] == "hil_response_packet"
    assert result["payload"]["filename"].endswith(".pdf")
    assert result["authority"]["publication_authority"] is False


def test_hil_non_pdf_fails_closed():
    with pytest.raises(AccessDenied):
        build_hil_pdf_submission(
            identity(),
            filename="response.txt",
            sha256_hex="a" * 64,
            size_bytes=100,
            trace_id="HIL-TRACE-0001",
            participant_review_status="reviewed",
        )
