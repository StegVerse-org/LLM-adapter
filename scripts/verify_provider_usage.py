#!/usr/bin/env python3
"""Verify machine-readable adapter role and provider usage-event emission."""
from llm_adapter.entry_point_role import get_llm_adapter_role
from llm_adapter.provider_usage import ProviderMetric, build_provider_usage_event


def main() -> int:
    role = get_llm_adapter_role()
    assert role["entry_point_id"] == "llm_adapter"
    assert role["authority_boundaries"]["provider_output_is_authority"] is False

    event = build_provider_usage_event(
        measurement_id="verify-provider-usage-001",
        session_id="verify-session-001",
        transition_id="verify-transition-002",
        parent_transition_id="verify-transition-001",
        origin_entry_point="ecosystem_chat",
        interaction_type="governed_research",
        provider="verification-provider",
        model="verification-model",
        metrics={
            "input_tokens": ProviderMetric("100", "tokens", "CONFIGURED", "verification-fixture"),
            "output_tokens": ProviderMetric("25", "tokens", "CONFIGURED", "verification-fixture"),
            "latency_ms": ProviderMetric("300", "ms", "CONFIGURED", "verification-fixture"),
        },
    )
    assert event["metric_owner"] == "llm_adapter"
    assert event["origin_entry_point"] == "ecosystem_chat"
    assert event["metrics"]["input_tokens"]["evidence_class"] == "CONFIGURED"
    assert event["invariants"]["usage_event_is_authority"] is False
    print("LLM Adapter role and provider usage event: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
