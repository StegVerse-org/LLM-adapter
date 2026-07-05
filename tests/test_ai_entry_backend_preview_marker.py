from llm_adapter.ai_entry_backend_service import build_ai_entry_backend_response


def test_backend_response_contains_preview_marker():
    response = build_ai_entry_backend_response("Compare StegVerse with ChatGPT")
    marker = response.receipt_capture_preview
    assert marker["preview_only"] is True
    assert marker["receipt_capture_enabled"] is False
    assert marker["record_persisted"] is False
    assert marker["authority_granted"] is False
    assert marker["route_id"] == response.primary_route
    assert marker["response_id"] == response.response_id
    assert len(marker["input_hash"]) == 64
