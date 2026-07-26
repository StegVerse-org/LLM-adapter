from llm_adapter.user_llm_access import AccessRequest, UserLLMIdentity
from llm_adapter.user_llm_router import (
    RouteTransports,
    handle_user_llm_request,
    route_request,
)


def identity() -> UserLLMIdentity:
    return UserLLMIdentity(
        user_id="user-001",
        llm_id="external-llm-001",
        provider="fixture-provider",
        model="fixture-model",
        scopes=("demo:read", "demo:submit", "sandbox:submit"),
    )


def test_unconfigured_route_defers_without_authority():
    result = route_request(
        AccessRequest(identity(), "demo_test_suite", "list", {}),
        RouteTransports(),
    )
    assert result["status"] == "DEFER"
    assert result["reason"] == "route_transport_not_configured"
    assert result["authority_attached"] is False


def test_configured_route_returns_hash_bound_result_to_originating_llm():
    def demo_transport(envelope):
        return {"accepted": True, "request_hash": envelope["request_hash"]}

    result = route_request(
        AccessRequest(identity(), "demo_test_suite", "list", {}),
        RouteTransports(demo_test_suite=demo_transport),
    )
    assert result["status"] == "RETURNED"
    assert len(result["result_hash"]) == 64
    assert result["return_path"]["llm_id"] == "external-llm-001"
    assert result["authority_attached"] is False


def test_service_boundary_fails_closed_for_production_execution():
    result = handle_user_llm_request(
        {
            "identity": {
                "user_id": "user-001",
                "llm_id": "external-llm-001",
                "provider": "fixture-provider",
                "model": "fixture-model",
            },
            "route": "production_execution",
            "action": "execute",
            "payload": {},
        }
    )
    assert result["status"] == "DENY"
    assert result["authority_attached"] is False


def test_service_boundary_is_transport_wrapper_ready():
    def sandbox_transport(envelope):
        return {"sandbox_receipt": "sandbox-receipt-001", "route": envelope["route"]}

    result = handle_user_llm_request(
        {
            "identity": {
                "user_id": "user-001",
                "llm_id": "external-llm-001",
                "provider": "fixture-provider",
                "model": "fixture-model",
                "scopes": ["sandbox:submit"],
            },
            "route": "entity_sandbox_runner",
            "action": "submit",
            "payload": {"bundle_ref": "sha256:fixture"},
        },
        RouteTransports(entity_sandbox_runner=sandbox_transport),
    )
    assert result["status"] == "RETURNED"
    assert result["result"]["sandbox_receipt"] == "sandbox-receipt-001"
