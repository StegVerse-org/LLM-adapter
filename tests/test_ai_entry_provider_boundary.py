from llm_adapter.ai_entry_provider_boundary import build_disabled_provider_boundary


def test_provider_boundary_disabled_by_default():
    result = build_disabled_provider_boundary()
    assert result.live_provider_calls_enabled is False
    assert result.credential_surface_enabled is False
    assert result.provider_secret_required_for_tests is False
    assert result.provider_output_is_authority is False
    assert result.receipt_capture_required_before_live_activation is True


def test_comparison_outputs_are_non_authoritative():
    result = build_disabled_provider_boundary()
    assert {item.provider for item in result.comparisons} == {"ChatGPT", "Claude", "Other LLM"}
    for item in result.comparisons:
        assert item.enabled is False
        assert item.live_call_allowed is False
        assert item.authority is False
        assert item.comparison_only is True
