from llm_adapter.ai_entry_service_wrapper import get_service_status, handle_service_request


def test_service_status_defaults():
    status = get_service_status()
    assert status.wrapper_present is True
    assert status.started_by_import is False
    assert status.live_calls_enabled is False
    assert status.side_effects_enabled is False


def test_service_request_wraps_endpoint_response():
    response = handle_service_request({"message": "Compare StegVerse with Claude"})
    assert response["primary_route"] == "llm_comparison"
    assert response["governance"]["authority_issued"] is False
    assert response["service"]["wrapper_present"] is True
    assert response["service"]["live_calls_enabled"] is False
