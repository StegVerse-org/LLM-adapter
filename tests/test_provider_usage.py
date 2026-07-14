from __future__ import annotations

import importlib
import os
import tempfile
from types import SimpleNamespace

from llm_adapter.entry_point_role import get_llm_adapter_role
from llm_adapter.provider_usage import ProviderMetric, ProviderUsageError, build_provider_usage_event


def test_machine_readable_adapter_role_is_bounded() -> None:
    role = get_llm_adapter_role()
    assert role["entry_point_id"] == "llm_adapter"
    assert role["authority_boundaries"]["translation_is_admissibility"] is False
    assert role["usage_reporting"]["metric_owner"] == "llm_adapter"
    assert len(role["role_sha256"]) == 64


def test_provider_usage_event_preserves_cross_entry_session() -> None:
    event = build_provider_usage_event(
        measurement_id="measure-provider-001",
        session_id="session-001",
        transition_id="transition-002",
        parent_transition_id="transition-001",
        origin_entry_point="ecosystem_chat",
        interaction_type="governed_coding",
        provider="external-provider",
        model="provider-model",
        metrics={
            "input_tokens": ProviderMetric("120", "tokens", "MEASURED", "trace-001"),
            "output_tokens": ProviderMetric("40", "tokens", "MEASURED", "trace-001"),
            "latency_ms": ProviderMetric("350", "ms", "MEASURED", "trace-001"),
        },
        receipt_refs=["receipt-provider-001"],
        timestamp="2026-07-12T14:00:00Z",
    )
    assert event["entry_point"] == "llm_adapter"
    assert event["origin_entry_point"] == "ecosystem_chat"
    assert event["metric_owner"] == "llm_adapter"
    assert event["parent_transition_id"] == "transition-001"
    assert event["metrics"]["input_tokens"]["evidence_class"] == "MEASURED"
    assert len(event["event_sha256"]) == 64


def test_configured_provider_metric_remains_configured() -> None:
    event = build_provider_usage_event(
        measurement_id="measure-provider-fixture",
        session_id="session-fixture",
        transition_id="transition-fixture",
        origin_entry_point="sdk",
        interaction_type="runtime_comparison",
        provider="fixture-provider",
        model="fixture-model",
        metrics={"total_cost_usd": ProviderMetric("0.01", "USD", "CONFIGURED", "fixture")},
    )
    assert event["metrics"]["total_cost_usd"]["evidence_class"] == "CONFIGURED"


def test_unavailable_provider_metric_rejects_value() -> None:
    try:
        build_provider_usage_event(
            measurement_id="measure-bad",
            session_id="session-bad",
            transition_id="transition-bad",
            origin_entry_point="sdk",
            interaction_type="provider_output_normalization",
            provider="provider",
            model="model",
            metrics={"total_cost_usd": ProviderMetric("1", "USD", "UNAVAILABLE")},
        )
    except ProviderUsageError:
        return
    raise AssertionError("UNAVAILABLE metric with a value must fail closed")


def _persistence_module(temp: str):
    os.environ["STEGVERSE_USAGE_SESSION_DB"] = os.path.join(temp, "usage.db")
    import llm_adapter.usage_session_api as usage_api
    usage_api = importlib.reload(usage_api)
    import llm_adapter.provider_usage_submission as submission
    submission = importlib.reload(submission)
    return usage_api, submission


def _used_provider_result() -> SimpleNamespace:
    return SimpleNamespace(
        used=True,
        provider_name="fixture-provider",
        model="fixture-model",
        provider_receipt_id="provider-response-receipt:sha256:" + "a" * 64,
        input_units=120,
        output_units=40,
        estimated_cost_usd=0.0012,
    )


def test_successful_provider_result_is_persisted_and_idempotent() -> None:
    with tempfile.TemporaryDirectory() as temp:
        usage_api, submission = _persistence_module(temp)
        first = submission.persist_provider_usage(
            session_id="session-auto-1",
            transition_id="transition-auto-1",
            run_id="run-auto-1",
            parent_transition_id="transition-parent",
            provider_result=_used_provider_result(),
        )
        assert first is not None
        assert first["inserted"] is True
        assert first["authority_granted"] is False
        assert first["custody_recorded"] is False

        repeated = submission.persist_provider_usage(
            session_id="session-auto-1",
            transition_id="transition-auto-1",
            run_id="run-auto-1",
            parent_transition_id="transition-parent",
            provider_result=_used_provider_result(),
        )
        assert repeated is not None
        assert repeated["inserted"] is False

        with usage_api._connect() as connection:
            row = connection.execute("SELECT event_json FROM usage_events").fetchone()
        assert row is not None
        event = __import__("json").loads(row["event_json"])
        assert event["session_id"] == "session-auto-1"
        assert event["parent_transition_id"] == "transition-parent"
        assert event["metrics"]["model_calls"]["evidence_class"] == "MEASURED"
        assert event["metrics"]["estimated_cost_usd"]["evidence_class"] == "DERIVED"


def test_fallback_provider_result_creates_no_usage_event() -> None:
    with tempfile.TemporaryDirectory() as temp:
        usage_api, submission = _persistence_module(temp)
        result = submission.persist_provider_usage(
            session_id="session-auto-2",
            transition_id="transition-auto-2",
            run_id="run-auto-2",
            parent_transition_id=None,
            provider_result=SimpleNamespace(used=False),
        )
        assert result is None
        with usage_api._connect() as connection:
            count = connection.execute("SELECT COUNT(*) FROM usage_events").fetchone()[0]
        assert count == 0
