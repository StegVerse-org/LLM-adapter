from llm_adapter.ai_entry_backend_service import build_ai_entry_backend_response


def test_ai_entry_response_includes_free_tier_trust_metadata():
    response = build_ai_entry_backend_response("How does governed replay work?")

    assert response.free_tier_trust["schema_version"] == "stegverse.ai_entry.free_tier_trust.v0.1"
    assert response.free_tier_trust["preview_only"] is True
    assert response.free_tier_trust["bounded_live_use"] is True
    assert response.free_tier_trust["static_demo_only"] is False


def test_ai_entry_free_tier_quota_metadata_is_non_authorizing():
    response = build_ai_entry_backend_response("Explain admissibility")
    quota = response.free_tier_trust["quota"]

    assert quota["status"] == "ALLOW_QUOTA"
    assert quota["allowed"] is True
    assert quota["non_claims"]["quota_allow_is_admissibility"] is False
    assert quota["non_claims"]["quota_allow_is_execution_authority"] is False


def test_ai_entry_free_tier_limits_metadata_is_non_authorizing():
    response = build_ai_entry_backend_response("Can I export a receipt?")
    limits = response.free_tier_trust["receipt_replay_limits"]

    assert limits["status"] == "ALLOW_LIMIT"
    assert limits["allowed"] is True
    assert limits["scope"]["reconstruction_scope"] == "recent_session_limited"
    assert limits["non_claims"]["limit_allow_is_admissibility"] is False
    assert limits["non_claims"]["reconstruction_grants_commit_time_standing"] is False


def test_ai_entry_free_tier_upgrade_reasons_are_site_visible():
    response = build_ai_entry_backend_response("Compare models")

    assert "higher_quota" in response.free_tier_trust["upgrade_for"]
    assert "private_connectors" in response.free_tier_trust["upgrade_for"]
    assert "premium_models" in response.free_tier_trust["upgrade_for"]
    assert "exportable_audit_packet" in response.free_tier_trust["upgrade_for"]
