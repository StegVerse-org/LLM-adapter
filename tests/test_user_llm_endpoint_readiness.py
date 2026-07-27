from __future__ import annotations

from fastapi.testclient import TestClient

from llm_adapter.user_llm_deployment import evaluate_endpoint_readiness
from llm_adapter.user_llm_http_transport import HTTPRouteConfig
from llm_adapter.user_llm_router import RouteTransports
from llm_adapter.user_llm_service import create_app


def _transport(envelope):
    return {"status": "RETURNED", "request_hash": envelope.get("request_hash")}


def test_deployment_readiness_is_deferred_until_all_routes_are_configured():
    deferred = evaluate_endpoint_readiness(HTTPRouteConfig(demo_test_suite_url="https://demo.example"))
    assert deferred.state == "DEFERRED"
    assert deferred.configured_routes == ("demo_test_suite",)
    assert deferred.missing_routes == ("entity_sandbox_runner", "hil_response_packet")
    assert deferred.as_public_dict()["authority_attached"] is False

    ready = evaluate_endpoint_readiness(
        HTTPRouteConfig(
            demo_test_suite_url="https://demo.example",
            entity_sandbox_runner_url="https://sandbox.example",
            hil_response_packet_url="https://hil.example",
        )
    )
    assert ready.ready is True
    assert ready.missing_routes == ()


def test_readyz_fails_closed_when_routes_are_missing():
    client = TestClient(create_app(transports=RouteTransports(), load_environment=False))
    response = client.get("/readyz")
    assert response.status_code == 503
    payload = response.json()
    assert payload["state"] == "DEFERRED"
    assert payload["configured_routes"] == []
    assert payload["authority_attached"] is False


def test_readyz_reports_ready_only_with_all_bounded_transports():
    client = TestClient(
        create_app(
            transports=RouteTransports(
                demo_test_suite=_transport,
                entity_sandbox_runner=_transport,
                hil_response_packet=_transport,
            ),
            load_environment=False,
        )
    )
    response = client.get("/readyz")
    assert response.status_code == 200
    payload = response.json()
    assert payload["state"] == "READY"
    assert payload["missing_routes"] == []
    assert payload["execution_authority"] is False
    assert payload["publication_authority"] is False
    assert payload["continuity_authority"] is False
    assert payload["master_record_custody"] is False
