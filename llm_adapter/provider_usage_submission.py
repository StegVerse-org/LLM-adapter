"""Internal provider-usage persistence for the governed Ecosystem Chat lifecycle.

This module records provider-owned measurements in the local usage-session ledger.
Local persistence is not a Master Records organization record and grants no authority.

It is also where every provider path records usage. Provider usage is recorded
locally and in the organization ledger by the transition receipt; Master Records
receives only released organization batches downstream. So no provider
execution waits on, or is gated by, a Master Records reply:
`record_usage_non_gating` turns a recording failure into a six-field non-ALLOW
usage disposition instead of an exception.
"""
from __future__ import annotations

import json
from hashlib import sha256
from typing import Any, Callable, Mapping

from llm_adapter.provider_usage import ProviderMetric, build_provider_usage_event

LOCAL_USAGE_RECORD_SCHEMA = "stegverse.usage.local_provider_usage_record.v1"
OWNING_EXISTING_GOAL = "LLMA-DECLARED-PATH-CONFORMANCE-368"


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
        # The provider receipt and transition identity define this measurement.
        # A wall-clock timestamp would make identical replay hash differently.
        timestamp=None,
    )

    canonical, inserted = _persist_event(event, session_id=session_id, transition_id=transition_id)

    return {
        "schema": "stegverse.usage.internal_submission.v1",
        "session_id": session_id,
        "measurement_id": canonical["measurement_id"],
        "event_sha256": canonical["event_sha256"],
        "inserted": inserted,
        "canonical_event": canonical,
        "authority_granted": False,
        "custody_recorded": False,
    }


def _persist_event(event: dict[str, Any], *, session_id: str, transition_id: str) -> tuple[dict[str, Any], bool]:
    """Write one canonical usage event to the local ledger, idempotently."""
    # Imported here so provider executors can import this module without the
    # HTTP service stack; only recording needs the ledger.
    from llm_adapter import usage_session_api

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
    return canonical, inserted


def record_provider_usage_event_locally(event: dict[str, Any]) -> dict[str, Any]:
    """Record a provider-usage event in the local ledger. The default for every provider path."""
    if not isinstance(event, dict):
        raise ValueError("provider_usage_event_not_object")
    canonical, inserted = _persist_event(
        event, session_id=str(event.get("session_id") or ""),
        transition_id=str(event.get("transition_id") or ""))
    return {
        "schema": LOCAL_USAGE_RECORD_SCHEMA,
        "status": "LOCAL_USAGE_RECORDED",
        "session_id": canonical["session_id"],
        "measurement_id": canonical["measurement_id"],
        "event_sha256": canonical["event_sha256"],
        "inserted": inserted,
        "recorded_by": "LOCAL_PROVIDER_USAGE_LEDGER",
        "organization_ledger_record": "TRANSITION_RECEIPT",
        "is_master_records_organization_record": False,
        "gates_execution": False,
        "authority_granted": False,
        "authority_effect": "NONE",
    }


def record_usage_non_gating(
    submitter: Callable[[dict[str, Any]], Mapping[str, Any]],
    event: dict[str, Any],
) -> dict[str, Any]:
    """Record usage without letting the recording gate the provider execution.

    A failed or malformed recording is a non-ALLOW usage disposition carrying
    the six standard fields; the execution it measures still proceeds.
    """
    try:
        reply = submitter(event)
    except Exception as exc:  # recording never gates execution
        return _usage_record_failed(f"usage_submitter_raised:{type(exc).__name__}")
    if not isinstance(reply, Mapping):
        return _usage_record_failed("usage_submitter_reply_not_object")
    return dict(reply)


def _usage_record_failed(predicate: str) -> dict[str, Any]:
    return {
        "schema": LOCAL_USAGE_RECORD_SCHEMA,
        "status": "USAGE_RECORD_FAILED",
        "disposition": "FAIL_CLOSED",
        "failure_code": "PROVIDER_USAGE_NOT_RECORDED",
        "failed_predicate": predicate,
        "required_evidence_or_repair": "a local provider-usage ledger write for this measurement",
        "retry_entrypoint": "llm_adapter.provider_usage_submission.record_provider_usage_event_locally",
        "owning_existing_goal": OWNING_EXISTING_GOAL,
        "next_attempt": "re-record the same canonical event; the write is idempotent",
        "gates_execution": False,
        "authority_granted": False,
        "authority_effect": "NONE",
    }
