from llm_adapter.free_tier_limits import ReceiptReplayUsage, evaluate_receipt_replay_limits


def test_receipt_replay_limits_allow_default_usage():
    decision = evaluate_receipt_replay_limits(ReceiptReplayUsage())

    assert decision.status == "ALLOW_LIMIT"
    assert decision.allowed is True
    assert decision.reasons == ()
    assert decision.remaining["receipt_exports_today"] == 1
    assert decision.remaining["replays_today"] == 1
    assert decision.remaining["reconstructions_today"] == 1
    assert decision.non_claims["limit_allow_is_admissibility"] is False
    assert decision.non_claims["reconstruction_grants_commit_time_standing"] is False


def test_receipt_export_limit_denies_when_exhausted():
    decision = evaluate_receipt_replay_limits(
        ReceiptReplayUsage(receipt_exports_today=1)
    )

    assert decision.status == "DENY_LIMIT"
    assert "receipt_export_limit_exhausted" in decision.reasons
    assert "receipt_export_capacity_needed" in decision.upgrade_triggers
    assert decision.remaining["receipt_exports_today"] == 0


def test_replay_and_reconstruction_limits_deny_when_exhausted():
    decision = evaluate_receipt_replay_limits(
        ReceiptReplayUsage(replays_today=1, reconstructions_today=1)
    )

    assert decision.status == "DENY_LIMIT"
    assert "replay_limit_exhausted" in decision.reasons
    assert "reconstruction_limit_exhausted" in decision.reasons
    assert "deeper_replay_needed" in decision.upgrade_triggers
    assert "deeper_reconstruction_needed" in decision.upgrade_triggers


def test_retention_and_audit_requests_deny_on_free_tier():
    decision = evaluate_receipt_replay_limits(
        ReceiptReplayUsage(
            wants_full_evidence_bundle=True,
            wants_exportable_audit_packet=True,
            wants_long_term_retention=True,
        )
    )

    assert decision.status == "DENY_LIMIT"
    assert "full_evidence_bundle_disabled_on_free_tier" in decision.reasons
    assert "exportable_audit_packet_disabled_on_free_tier" in decision.reasons
    assert "long_term_retention_disabled_on_free_tier" in decision.reasons
    assert "evidence_bundle_retention_needed" in decision.upgrade_triggers
    assert "audit_packet_needed" in decision.upgrade_triggers
    assert "longer_retention_needed" in decision.upgrade_triggers


def test_cross_session_reconstruction_denies_on_free_tier():
    decision = evaluate_receipt_replay_limits(
        ReceiptReplayUsage(wants_cross_session_reconstruction=True)
    )

    assert decision.status == "DENY_LIMIT"
    assert "cross_session_reconstruction_disabled_on_free_tier" in decision.reasons
    assert "cross_session_reconstruction_needed" in decision.upgrade_triggers
    assert decision.scope["reconstruction_scope"] == "recent_session_limited"


def test_custom_limit_policy_supported():
    decision = evaluate_receipt_replay_limits(
        ReceiptReplayUsage(receipt_exports_today=2, replays_today=0, reconstructions_today=0),
        policy={
            "tier": "free",
            "receipt_exports_per_day": 2,
            "replays_per_day": 3,
            "reconstructions_per_day": 4,
            "reconstruction_scope": "recent_session_limited",
        },
    )

    assert decision.status == "DENY_LIMIT"
    assert "receipt_export_limit_exhausted" in decision.reasons
    assert decision.remaining["replays_today"] == 3
    assert decision.remaining["reconstructions_today"] == 4
