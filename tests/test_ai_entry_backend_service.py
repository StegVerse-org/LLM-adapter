from llm_adapter.ai_entry_backend_service import build_ai_entry_backend_response


def test_backend_service_welcome_is_not_governed_candidate():
    response = build_ai_entry_backend_response("")
    assert response.primary_route == "chat_answer"
    assert response.governance["governed_candidate"] is False
    assert response.governance["authority_issued"] is False
    assert response.governance["receipt_id"] is None


def test_backend_service_comparison_outputs_are_non_authoritative():
    response = build_ai_entry_backend_response("Compare StegVerse with ChatGPT")
    assert response.primary_route == "llm_comparison"
    assert response.activation["live_provider_calls_enabled"] is False
    assert response.activation["credential_surface_enabled"] is False
    assert response.activation["provider_output_is_authority"] is False
    assert len(response.comparison_outputs) == 3
    for item in response.comparison_outputs:
        assert item["authority"] is False


def test_backend_service_sdk_route_is_preview_only():
    response = build_ai_entry_backend_response("How do I access the SDK?")
    assert response.primary_route == "sdk_access_guidance"
    assert response.governance["governed_candidate"] is True
    assert response.governance["authority_issued"] is False
    assert response.governance["receipt_id"] is None
