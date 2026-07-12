"""Fail-closed Master-Records submission client for completed chat transitions.

The client is disabled unless an HTTPS endpoint is configured. A record is marked
RECORDED only when the remote response preserves transition/run/final-receipt
identity and returns both a custody receipt and Master-Records reference.
"""
from __future__ import annotations

import os
from typing import Any
from urllib.parse import urlparse

import requests

from llm_adapter.transition_store import TransitionStore, store

ENDPOINT = os.getenv("STEGVERSE_MASTER_RECORDS_ENDPOINT", "").strip()
TOKEN = os.getenv("STEGVERSE_MASTER_RECORDS_TOKEN", "").strip()
TIMEOUT_SECONDS = float(os.getenv("STEGVERSE_MASTER_RECORDS_TIMEOUT_SECONDS", "10"))
ALLOWED_HOSTS = {
    host.strip().lower()
    for host in os.getenv("STEGVERSE_MASTER_RECORDS_ALLOWED_HOSTS", "").split(",")
    if host.strip()
}


def enabled() -> bool:
    if not ENDPOINT:
        return False
    parsed = urlparse(ENDPOINT)
    if parsed.scheme != "https" or not parsed.hostname:
        return False
    if ALLOWED_HOSTS and parsed.hostname.lower() not in ALLOWED_HOSTS:
        return False
    return True


def build_submission(record: dict[str, Any]) -> dict[str, Any]:
    continuity = record.get("continuity", {})
    final_receipt_id = continuity.get("final_receipt_id")
    if record.get("lifecycle_state") != "COMPLETED" or not final_receipt_id:
        raise ValueError("Master-Records submission requires COMPLETED plus final_receipt_id")
    return {
        "schema_version": "1.0.0",
        "submission_type": "governed_transition_custody_candidate",
        "transition_id": record["transition_id"],
        "run_id": record["run_id"],
        "final_receipt_id": final_receipt_id,
        "record": record,
        "requested_result": {
            "custody_receipt_required": True,
            "master_record_ref_required": True,
            "reconstruction_result_required": True,
        },
        "authority_boundary": {
            "submission_is_custody": False,
            "local_persistence_is_custody": False,
            "client_may_self_issue_custody_receipt": False,
        },
    }


def validate_response(record: dict[str, Any], response: dict[str, Any]) -> tuple[str, str]:
    expected = (
        record["transition_id"],
        record["run_id"],
        record["continuity"]["final_receipt_id"],
    )
    actual = (
        response.get("transition_id"),
        response.get("run_id"),
        response.get("final_receipt_id"),
    )
    if actual != expected:
        raise ValueError("Master-Records response identity mismatch")
    if response.get("custody_status") != "RECORDED":
        raise ValueError("Master-Records response did not confirm RECORDED")
    custody_receipt_id = response.get("custody_receipt_id")
    master_record_ref = response.get("master_record_ref")
    if not custody_receipt_id or not master_record_ref:
        raise ValueError("Master-Records response missing custody receipt or record reference")
    if response.get("reconstruction_status") != "PASS":
        raise ValueError("Master-Records response missing reconstruction PASS")
    return str(custody_receipt_id), str(master_record_ref)


def submit_record(record: dict[str, Any], *, transition_store: TransitionStore = store) -> dict[str, Any]:
    transition_id = record["transition_id"]
    if not enabled():
        transition_store.mark_attempt(
            transition_id,
            state="PENDING",
            error="Master-Records endpoint is not enabled",
        )
        return {"submitted": False, "state": "PENDING", "reason": "endpoint_not_enabled"}

    headers = {"Content-Type": "application/json"}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    try:
        response = requests.post(
            ENDPOINT,
            json=build_submission(record),
            headers=headers,
            timeout=TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json()
        custody_receipt_id, master_record_ref = validate_response(record, payload)
        updated = transition_store.mark_recorded(
            transition_id,
            custody_receipt_id=custody_receipt_id,
            master_record_ref=master_record_ref,
        )
        return {
            "submitted": True,
            "state": "RECORDED",
            "custody_receipt_id": custody_receipt_id,
            "master_record_ref": master_record_ref,
            "record": updated,
        }
    except Exception as exc:  # fail closed; never invent custody
        transition_store.mark_attempt(transition_id, state="RETRY", error=str(exc)[:500])
        return {"submitted": False, "state": "RETRY", "reason": type(exc).__name__}


def process_pending(*, transition_store: TransitionStore = store, limit: int = 20) -> list[dict[str, Any]]:
    return [submit_record(item["record"], transition_store=transition_store) for item in transition_store.pending_custody(limit)]
