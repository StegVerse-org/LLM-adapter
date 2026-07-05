from llm_adapter.free_tier_quota import FreeTierUsage, evaluate_free_tier_quota


def test_free_tier_allows_within_limits():
    decision = evaluate_free_tier_quota(
        FreeTierUsage(
            governed_inquiries_today=0,
            trial_governed_inquiries_total=0,
            receipt_exports_today=0,
            replays_today=0,
        )
    )

    assert decision.status == "ALLOW_QUOTA"
    assert decision.allowed is True
    assert decision.reasons == ()
    assert decision.remaining["governed_inquiries_today"] == 5
    assert decision.non_claims["quota_allow_is_admissibility"] is False
    assert decision.non_claims["quota_allow_is_execution_authority"] is False


def test_free_tier_denies_daily_governed_inquiry_exhaustion():
    decision = evaluate_free_tier_quota(
        FreeTierUsage(
            governed_inquiries_today=5,
            trial_governed_inquiries_total=3,
        )
    )

    assert decision.status == "DENY_QUOTA"
    assert decision.allowed is False
    assert "daily_governed_inquiry_quota_exhausted" in decision.reasons
    assert "quota_needed" in decision.upgrade_triggers
    assert decision.remaining["governed_inquiries_today"] == 0


def test_free_tier_denies_trial_total_exhaustion():
    decision = evaluate_free_tier_quota(
        FreeTierUsage(
            governed_inquiries_today=1,
            trial_governed_inquiries_total=25,
        )
    )

    assert decision.status == "DENY_QUOTA"
    assert "trial_governed_inquiry_quota_exhausted" in decision.reasons
    assert "quota_needed" in decision.upgrade_triggers


def test_free_tier_denies_connector_and_premium_model_requests():
    decision = evaluate_free_tier_quota(
        FreeTierUsage(
            wants_private_connector=True,
            wants_premium_model=True,
        )
    )

    assert decision.status == "DENY_QUOTA"
    assert "private_connectors_disabled_on_free_tier" in decision.reasons
    assert "premium_models_disabled_on_free_tier" in decision.reasons
    assert "private_connector_needed" in decision.upgrade_triggers
    assert "premium_model_needed" in decision.upgrade_triggers


def test_free_tier_denies_retention_and_audit_packet_requests():
    decision = evaluate_free_tier_quota(
        FreeTierUsage(
            wants_full_evidence_bundle_retention=True,
            wants_exportable_audit_packet=True,
        )
    )

    assert decision.status == "DENY_QUOTA"
    assert "full_evidence_bundle_retention_disabled_on_free_tier" in decision.reasons
    assert "exportable_audit_packet_disabled_on_free_tier" in decision.reasons
    assert "longer_retention_needed" in decision.upgrade_triggers
    assert "audit_packet_needed" in decision.upgrade_triggers


def test_free_tier_custom_policy_limits_are_supported():
    decision = evaluate_free_tier_quota(
        FreeTierUsage(
            governed_inquiries_today=2,
            trial_governed_inquiries_total=9,
            receipt_exports_today=0,
            replays_today=0,
        ),
        policy={
            "tier": "free",
            "governed_inquiries_per_day": 2,
            "trial_governed_inquiries_total": 10,
            "receipt_exports_per_day": 1,
            "replays_per_day": 1,
        },
    )

    assert decision.status == "DENY_QUOTA"
    assert "daily_governed_inquiry_quota_exhausted" in decision.reasons
    assert decision.remaining["trial_governed_inquiries_total"] == 1
