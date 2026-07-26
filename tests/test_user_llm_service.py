from llm_adapter.user_llm_router import RouteTransports
from llm_adapter.user_llm_service import (
    create_app,
    handle_http_payload,
    resolve_route_transports,
)


def payload(route: str = "demo_test_suite") -> dict:
    return {
        "identity": {
            "user_id": "user-001",
            "llm_id": "external-llm-001",
            "provider": "fixture-provider",
            "model": "fixture-model",
            "scopes": ["demo:read", "demo:submit"],
        },
        "route": route,
        "action": "submit",
        "payload": {"test_id": "TA-14"},
    }


def test_http_boundary_defers_without_transport():
    result = handle_http_payload(payload(), load_environment=False)
    assert result["status"] == "DEFER"
    assert result["reason"] == "route_transport_not_configured"
    assert result["authority_attached"] is False


def test_http_boundary_returns_to_originating_llm():
    transports = RouteTransports(
        demo_test_suite=lambda request: {
            "receipt_id": "demo-receipt-001",
            "request_hash": request["request_hash"],
        }
    )
    result = handle_http_payload(payload(), transports=transports)
    assert result["status"] == "RETURNED"
    assert result["return_path"]["user_id"] == "user-001"
    assert result["return_path"]["llm_id"] == "external-llm-001"
    assert result["authority_attached"] is False


def test_explicit_transports_override_environment(monkeypatch):
    monkeypatch.setenv("STEGVERSE_DEMO_TEST_SUITE_URL", "https://example.invalid/demo")
    explicit = RouteTransports(demo_test_suite=lambda request: {"source": "explicit"})
    resolved = resolve_route_transports(explicit)
    assert resolved is explicit


def test_environment_configuration_creates_transport_without_network_call(monkeypatch):
    monkeypatch.setenv("STEGVERSE_DEMO_TEST_SUITE_URL", "https://example.invalid/demo")
    resolved = resolve_route_transports()
    assert callable(resolved.demo_test_suite)
    assert resolved.entity_sandbox_runner is None
    assert resolved.hil_response_packet is None


def test_environment_loading_can_be_disabled(monkeypatch):
    monkeypatch.setenv("STEGVERSE_DEMO_TEST_SUITE_URL", "https://example.invalid/demo")
    resolved = resolve_route_transports(load_environment=False)
    assert resolved.demo_test_suite is None


def test_fastapi_app_exposes_capability_request_and_health_routes():
    app = create_app(transports=RouteTransports())
    paths = {route.path for route in app.routes}
    assert "/v1/user-llm/capabilities" in paths
    assert "/v1/user-llm/requests" in paths
    assert "/healthz" in paths
