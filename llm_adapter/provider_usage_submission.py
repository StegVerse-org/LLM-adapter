"""Internal provider-usage persistence for the governed Ecosystem Chat lifecycle.

This module records provider-owned measurements in the local usage-session ledger.
Local persistence is not Master-Records custody and grants no authority.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any

from llm_adapter.provider_usage import ProviderMetric, build_provider_usage_event
from llm_adapter import usage_session_api


def _measurement_id(*, transition_id: str, run_id: str, provider_receipt_id: str | None) -> str:
    material = "\n".join((transition_id, run_id, provider_receipt_id or "provider-receipt-unavailable"))
    return "provider-usage:sha256:" + sha256(material.encode("utf-8")).hexdigest()


def persist_provider_usage(
    *,
    session_id: str,
    transition_id: str,
    run_id: str,
    parent_transition_id: str | None,
    provider_result: Any,
) -> dict[str, Any] | None:
    """Persist one successful provider result using the usage-session contract.

    Disabled, blocked, failed, or fallback provider results produce no measurement.
    Repeated identical results are idempotent; changed content under the same
    measurement identity fails closed.
    """
    if not getattr(provider_result, "used", False):
        return None

    receipt_id = getattr(provider_result, "provider_receipt_id", None)
    source_ref = receipt_id or "provider-receipt:unavailable"
    event = build_provider_usage_event(
        measurement_id=_measurement_id(
            transition_id=transition_id,
            run_id=run_id,
            provider_receipt_id=receipt_id,
        ),
        session_id=session_id,
        transition_id=transition_id,
        parent_transition_id=parent_transition_id,
        origin_entry_point="ecosystem_chat",
        interaction_type="provider_generation",
        provider=str(getattr(provider_result, "provider_name", None) or "unreported"),
        model=str(getattr(provider_result, "model", None) or "unreported"),
        metrics={
            "model_calls": ProviderMetric("1", "calls", "MEASURED", source_ref),
            "input_chars": ProviderMetric(str(int(getattr(provider_result, "input_units", 0))), "characters", "MEASURED", source_ref),
            "output_chars": ProviderMetric(str(int(getattr(provider_result, "output_units", 0))), "characters", "MEASURED", source_ref),
            "estimated_cost_usd": ProviderMetric(str(getattr(provider_result, "estimated_cost_usd", 0.0)), "USD", "DERIVED", source_ref),
        },
        receipt_refs=[receipt_id] if receipt_id else [],
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

    usage_session_api._validate_session_id(session_id)
    canonical = usage_session_api._validate_event(event, session_id)
    inserted = False
    with usage_session_api._LOCK, usage_session_api._connect() as connection:
        existing = connection.execute(
            "SELECT session_id, event_sha256 FROM usage_events WHERE metric_owner=? AND measurement_id=?",
            (canonical["metric_owner"], canonical["measurement_id"]),
        ).fetchone()
        if existing:
            if existing["session_id"] != session_id or existing["event_sha256"] != canonical["event_sha256"]:
                raise RuntimeError("provider_usage_measurement_identity_conflict")
        else:
            connection.execute(
                """
                INSERT INTO usage_events(metric_owner, measurement_id, session_id, transition_id, event_sha256, event_json)
                VALUES(?,?,?,?,?,?)
                """,
                (
                    canonical["metric_owner"], canonical["measurement_id"], session_id,
                    transition_id, canonical["event_sha256"],
                    json.dumps(canonical, sort_keys=True, separators=(",", ":")),
                ),
            )
            connection.commit()
            inserted = True

    return {
        "schema": "stegverse.usage.internal_submission.v1",
        "session_id": session_id,
        "measurement_id": canonical["measurement_id"],
        "event_sha256": canonical["event_sha256"],
        "inserted": inserted,
        "authority_granted": False,
        "custody_recorded": False,
    }
