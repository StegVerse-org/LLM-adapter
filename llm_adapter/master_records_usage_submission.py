"""Authenticated Master-Records submission for provider-owned usage events.

This module is server-side only. Configuration is resolved at call time, credentials
never enter response payloads, and a transport response is not treated as custody
until the returned receipt is identity-bound and explicitly records custody.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Callable
from urllib import error, request
from urllib.parse import urlparse


class MasterRecordsUsageError(RuntimeError):
    """Fail-closed Master-Records usage submission error."""


@dataclass(frozen=True)
class MasterRecordsUsageConfig:
    endpoint: str
    token: str
    timeout_seconds: float = 10.0


def _resolve_endpoint() -> tuple[str, bool]:
    explicit_endpoint = os.getenv("STEGVERSE_MASTER_RECORDS_USAGE_URL", "").strip()
    base_endpoint = os.getenv("STEGVERSE_MASTER_RECORDS_ENDPOINT", "").strip().rstrip("/")
    private_hostport = os.getenv("STEGVERSE_MASTER_RECORDS_HOSTPORT", "").strip().strip("/")
    if explicit_endpoint:
        return explicit_endpoint, False
    if base_endpoint:
        return base_endpoint + "/api/custody/provider-usage", False
    if private_hostport:
        return f"http://{private_hostport}/api/custody/provider-usage", True
    return "", False


def _configured() -> MasterRecordsUsageConfig | None:
    endpoint, private_network = _resolve_endpoint()
    token = os.getenv("STEGVERSE_MASTER_RECORDS_TOKEN", "").strip()
    if not endpoint and not token:
        return None
    if not endpoint or not token:
        raise MasterRecordsUsageError("master_records_usage_configuration_incomplete")

    parsed = urlparse(endpoint)
    local_http = parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1", "::1"}
    allow_local = os.getenv("STEGVERSE_ALLOW_LOCAL_MASTER_RECORDS_HTTP", "").lower() == "true"
    allow_private = os.getenv("STEGVERSE_ALLOW_PRIVATE_MASTER_RECORDS_HTTP", "").lower() == "true"
    safe_http = (local_http and allow_local) or (private_network and allow_private)
    if parsed.scheme != "https" and not safe_http:
        raise MasterRecordsUsageError("master_records_usage_endpoint_must_use_https")
    if not parsed.netloc:
        raise MasterRecordsUsageError("master_records_usage_endpoint_invalid")

    try:
        timeout = float(os.getenv("STEGVERSE_MASTER_RECORDS_TIMEOUT_SECONDS", "10"))
    except ValueError as exc:
        raise MasterRecordsUsageError("master_records_usage_timeout_invalid") from exc
    if timeout <= 0:
        raise MasterRecordsUsageError("master_records_usage_timeout_invalid")
    return MasterRecordsUsageConfig(endpoint=endpoint, token=token, timeout_seconds=timeout)


def _validate_receipt(receipt: Any, event: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(receipt, dict):
        raise MasterRecordsUsageError("master_records_usage_receipt_not_object")
    required = {"receipt_id", "session_id", "measurement_id", "event_sha256", "custody_recorded", "authority_granted"}
    missing = sorted(required.difference(receipt))
    if missing:
        raise MasterRecordsUsageError("master_records_usage_receipt_missing:" + ",".join(missing))
    if receipt["session_id"] != event["session_id"]:
        raise MasterRecordsUsageError("master_records_usage_session_mismatch")
    if receipt["measurement_id"] != event["measurement_id"]:
        raise MasterRecordsUsageError("master_records_usage_measurement_mismatch")
    if receipt["event_sha256"] != event["event_sha256"]:
        raise MasterRecordsUsageError("master_records_usage_event_digest_mismatch")
    if receipt["custody_recorded"] is not True:
        raise MasterRecordsUsageError("master_records_usage_custody_not_recorded")
    if receipt["authority_granted"] is not False:
        raise MasterRecordsUsageError("master_records_usage_authority_escalation")
    if not isinstance(receipt["receipt_id"], str) or not receipt["receipt_id"].strip():
        raise MasterRecordsUsageError("master_records_usage_receipt_id_invalid")
    return receipt


def submit_provider_usage_to_master_records(event: dict[str, Any], *, opener: Callable[..., Any] = request.urlopen) -> dict[str, Any]:
    config = _configured()
    if config is None:
        return {"schema": "stegverse.usage.master_records_submission.v1", "status": "NOT_CONFIGURED", "authority_granted": False, "custody_recorded": False}

    body = json.dumps({"schema": "stegverse.master_records.provider_usage_submission.v1", "event": event, "authority_requested": False, "custody_requested": True}, sort_keys=True, separators=(",", ":")).encode("utf-8")
    outbound = request.Request(config.endpoint, data=body, method="POST", headers={"Authorization": f"Bearer {config.token}", "Content-Type": "application/json", "Accept": "application/json", "X-SteGVerse-Session": str(event["session_id"])})
    try:
        with opener(outbound, timeout=config.timeout_seconds) as response:
            status = int(getattr(response, "status", 200))
            raw = response.read()
    except (error.URLError, TimeoutError, OSError) as exc:
        raise MasterRecordsUsageError("master_records_usage_transport_failed") from exc
    if status < 200 or status >= 300:
        raise MasterRecordsUsageError(f"master_records_usage_http_status:{status}")
    try:
        receipt = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MasterRecordsUsageError("master_records_usage_response_invalid_json") from exc

    validated = _validate_receipt(receipt, event)
    return {"schema": "stegverse.usage.master_records_submission.v1", "status": "CUSTODY_RECORDED", "receipt_id": validated["receipt_id"], "session_id": validated["session_id"], "measurement_id": validated["measurement_id"], "event_sha256": validated["event_sha256"], "reconstructability": validated.get("reconstructability", "PENDING"), "authority_granted": False, "custody_recorded": True}
