import pytest

from llm_adapter.user_llm_access import (
    AccessDenied,
    AccessRequest,
    UserLLMIdentity,
    build_hil_pdf_submission,
    build_submission,
)
from llm_adapter.user_llm_http_transport import HTTPRouteConfig, TransportError, build_http_route_transports
from llm_adapter.user_llm_router import RouteTransports, handle_user_llm_request
from llm_adapter.user_llm_service import create_app, handle_http_payload


def identity(*scopes: str) -> UserLLMIdentity:
    return UserLLMIdentity(
        user_id="user-001",
        llm_id="external-llm-001",
        provider="fixture-provider",
        model="fixture-model",
        scopes=tuple(scopes),
    )


def request_body(route="demo_test_suite", action="submit", scopes=None):
    return {
        "identity": {
            "user_id": "user-001",
            "llm_id": "external-llm-001",
            "provider": "fixture-provider",
            "model": "fixture-model",
            "scopes": scopes or ["demo:submit"],
        },
        "route": route,
        "action": action,
        "payload": {"test_id": "TA-14"},
    }


def test_route_action_scope_is_enforced():
    result = build_submission(
        AccessRequest(identity=identity("demo:submit"), route="demo_test_suite", action="submit", payload={})
    )
    assert result["required_scope"] == "demo:submit"
    assert result["authority"]["execution_authority"] is False

    with pytest.raises(AccessDenied, match="required scope missing"):
        build_submission(
            AccessRequest(identity=identity("demo:read"), route="demo_test_suite", action="submit", payload={})
        )


def test_unknown_action_and_production_route_fail_closed():
    for route, action in (("demo_test_suite", "execute"), ("production_execution", "execute")):
        with pytest.raises(AccessDenied):
            build_submission(AccessRequest(identity=identity("demo:submit"), route=route, action=action, payload={}))


def test_hil_submission_requires_real_hex_hash_and_scope():
    with pytest.raises(AccessDenied):
        build_hil_pdf_submission(
            identity("hil:submit"),
            filename="response.pdf",
            sha256_hex="z" * 64,
            size_bytes=100,
            trace_id="HIL-TRACE-0001",
            participant_review_status="reviewed",
        )

    result = build_hil_pdf_submission(
        identity("hil:submit"),
        filename="response.pdf",
        sha256_hex="a" * 64,
        size_bytes=100,
        trace_id="HIL-TRACE-0001",
        participant_review_status="reviewed",
    )
    assert result["route"] == "hil_response_packet"
    assert result["authority"]["publication_authority"] is False


def test_unconfigured_route_defers_without_authority():
    result = handle_user_llm_request(request_body(), RouteTransports())
    assert result["status"] == "DEFER"
    assert result["authority_attached"] is False


def test_transport_result_returns_to_originating_identity():
    result = handle_http_payload(
        request_body(),
        transports=RouteTransports(
            demo_test_suite=lambda envelope: {
                "receipt_id": "demo-receipt-001",
                "request_hash": envelope["request_hash"],
            }
        ),
        load_environment=False,
    )
    assert result["status"] == "RETURNED"
    assert result["return_path"]["user_id"] == "user-001"
    assert result["return_path"]["llm_id"] == "external-llm-001"
    assert result["authority_attached"] is False


def test_transport_failure_defers_instead_of_crashing():
    def unavailable(_):
        raise RuntimeError("offline")

    result = handle_user_llm_request(
        request_body(),
        RouteTransports(demo_test_suite=unavailable),
    )
    assert result["status"] == "DEFER"
    assert result["reason"] == "downstream_transport_failed"


def test_http_configuration_is_side_effect_free_and_validated():
    transports = build_http_route_transports(
        HTTPRouteConfig(demo_test_suite_url="https://example.invalid/demo")
    )
    assert callable(transports.demo_test_suite)
    assert transports.entity_sandbox_runner is None

    with pytest.raises(TransportError):
        build_http_route_transports(HTTPRouteConfig(demo_test_suite_url="file:///tmp/demo"))


def test_service_exposes_bounded_routes():
    app = create_app(transports=RouteTransports(), load_environment=False)
    paths = {route.path for route in app.routes}
    assert "/v1/user-llm/capabilities" in paths
    assert "/v1/user-llm/requests" in paths
    assert "/healthz" in paths
