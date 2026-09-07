"""Credential-free client for the Master Records local provider-usage custody broker.

The caller supplies only the canonical provider-usage event. Master Records keeps
its bearer and receipt-key material inside its own process and returns a sanitized
custody+reconstruction result over an owner-local Unix socket.
"""
from __future__ import annotations

import json
import os
import socket
from typing import Any, Callable, Mapping

DEFAULT_SOCKET = "/run/stegverse/master-records-provider-usage.sock"
REQUEST_SCHEMA = "stegverse.master_records.local_provider_usage_request.v1"
RESPONSE_SCHEMA = "stegverse.master_records.local_provider_usage_result.v1"
MAX_MESSAGE = 2_000_000


class MasterRecordsLocalUsageError(RuntimeError):
    pass


def _exchange_unix(request_value: Mapping[str, Any], *, socket_path: str, timeout_seconds: float = 10.0) -> dict[str, Any]:
    if not isinstance(socket_path, str) or not socket_path.startswith("/"):
        raise MasterRecordsLocalUsageError("master_records_local_socket_must_be_absolute")
    raw = (json.dumps(dict(request_value), sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")
    if len(raw) > MAX_MESSAGE:
        raise MasterRecordsLocalUsageError("master_records_local_request_too_large")
    chunks: list[bytes] = []
    total = 0
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.settimeout(timeout_seconds)
            client.connect(socket_path)
            client.sendall(raw)
            while True:
                part = client.recv(min(65536, MAX_MESSAGE - total))
                if not part:
                    break
                chunks.append(part)
                total += len(part)
                if total >= MAX_MESSAGE:
                    raise MasterRecordsLocalUsageError("master_records_local_response_too_large")
                if b"\n" in part:
                    break
    except (OSError, TimeoutError) as exc:
        raise MasterRecordsLocalUsageError("master_records_local_transport_failed") from exc
    response_raw = b"".join(chunks).split(b"\n", 1)[0]
    try:
        response = json.loads(response_raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MasterRecordsLocalUsageError("master_records_local_response_invalid_json") from exc
    if not isinstance(response, dict):
        raise MasterRecordsLocalUsageError("master_records_local_response_not_object")
    return response


def _validate_reply(reply: Mapping[str, Any], event: Mapping[str, Any]) -> dict[str, Any]:
    if reply.get("schema") != RESPONSE_SCHEMA:
        raise MasterRecordsLocalUsageError("master_records_local_response_schema_mismatch")
    if reply.get("decision") != "ALLOW_CUSTODY_RESULT" or reply.get("status") != "CUSTODY_RECORDED":
        raise MasterRecordsLocalUsageError("master_records_local_custody_not_admitted")
    if reply.get("custody_recorded") is not True or reply.get("reconstructability") != "PASS":
        raise MasterRecordsLocalUsageError("master_records_local_reconstruction_not_pass")
    for key in ("authority_granted", "admissibility_determined", "execution_authority", "publication_authority"):
        if reply.get(key) is not False:
            raise MasterRecordsLocalUsageError(f"master_records_local_authority_escalation:{key}")
    for key in ("secret_material_returned", "credential_material_returned"):
        if reply.get(key) is not False:
            raise MasterRecordsLocalUsageError(f"master_records_local_secret_boundary_violation:{key}")
    if reply.get("authority_effect") != "NONE":
        raise MasterRecordsLocalUsageError("master_records_local_authority_effect_invalid")
    if reply.get("credential_authority") != "TV/TVC":
        raise MasterRecordsLocalUsageError("master_records_local_credential_authority_mismatch")
    for key in ("session_id", "measurement_id", "event_sha256"):
        if reply.get(key) != event.get(key):
            raise MasterRecordsLocalUsageError(f"master_records_local_identity_mismatch:{key}")
    receipt_id = reply.get("receipt_id")
    if not isinstance(receipt_id, str) or not receipt_id.strip():
        raise MasterRecordsLocalUsageError("master_records_local_receipt_id_invalid")
    return {
        "schema": "stegverse.usage.master_records_submission.v1",
        "status": "CUSTODY_RECORDED",
        "receipt_id": receipt_id,
        "session_id": reply["session_id"],
        "measurement_id": reply["measurement_id"],
        "event_sha256": reply["event_sha256"],
        "reconstructability": "PASS",
        "authority_granted": False,
        "custody_recorded": True,
        "credential_material_present": False,
        "transport": "master_records_local_unix_socket",
        "authority_effect": "NONE",
    }


def submit_provider_usage_to_local_master_records(
    event: dict[str, Any],
    *,
    socket_path: str | None = None,
    exchange: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    if not isinstance(event, dict):
        raise MasterRecordsLocalUsageError("provider_usage_event_not_object")
    for key in ("session_id", "measurement_id", "event_sha256"):
        if not isinstance(event.get(key), str) or not event[key]:
            raise MasterRecordsLocalUsageError(f"provider_usage_event_identity_missing:{key}")
    if event.get("metric_owner") != "llm_adapter" or event.get("authority_granted") is not False or event.get("custody_recorded") is not False:
        raise MasterRecordsLocalUsageError("provider_usage_event_boundary_invalid")
    request_value = {
        "schema": REQUEST_SCHEMA,
        "event": dict(event),
        "authority_requested": False,
        "custody_requested": True,
    }
    if exchange is None:
        selected = socket_path or os.getenv("STEGVERSE_MASTER_RECORDS_PROVIDER_USAGE_SOCKET", DEFAULT_SOCKET)
        reply = _exchange_unix(request_value, socket_path=selected)
    else:
        reply = exchange(request_value)
    if not isinstance(reply, Mapping):
        raise MasterRecordsLocalUsageError("master_records_local_response_not_object")
    return _validate_reply(reply, event)


__all__ = [
    "DEFAULT_SOCKET", "MasterRecordsLocalUsageError",
    "submit_provider_usage_to_local_master_records",
]
