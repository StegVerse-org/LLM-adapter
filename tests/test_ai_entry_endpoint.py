from llm_adapter.ai_entry_endpoint import handle_ai_entry_payload


def test_endpoint_returns_backend_shape():
    response = handle_ai_entry_payload({"message": "Compare StegVerse with ChatGPT"})
    assert response["primary_route"] == "llm_comparison"
    assert response["governance"]["authority_issued"] is False
    assert response["governance"]["receipt_id"] is None
    assert len(response["comparison_outputs"]) == 3
    assert response["endpoint"]["mode"] == "pure_function_preview"


def test_endpoint_is_side_effect_free():
    response = handle_ai_entry_payload({"message": "How do I access the SDK?"})
    assert response["endpoint"]["http_server_started"] is False
    assert response["endpoint"]["live_calls_performed"] is False
    assert response["endpoint"]["side_effects_performed"] is False


def test_endpoint_normalizes_missing_message():
    response = handle_ai_entry_payload({})
    assert response["response_id"] == "welcome"
    assert response["primary_route"] == "chat_answer"
