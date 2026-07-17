from __future__ import annotations

import json

import pytest

from llm_adapter.master_records_usage_submission import (
    MasterRecordsUsageError,
    submit_provider_usage_to_master_records,
)


def _event() -> dict:
    return {
        "schema": "stegverse.usage.event.v1",
        "session_id": "session-custody-1",
        "measurement_id": "measure-custody-1",
        "event_sha256": "a" * 64,
        "metric_owner": "llm_adapter",
        "authority_granted": False,
        "custody_recorded": False,
    }


class _Response:
    def __init__(self, payload: dict, status: int = 200) -> None:
        self.status = status
        self._payload = payload

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def _receipt(event: dict) -> dict:
    return {
        "receipt_id": "mr-usage-receipt-1",
        "session_id": event["session_id"],
        "measurement_id": event["measurement_id"],
        "event_sha256": event["event_sha256"],
        "custody_recorded": True,
        "authority_granted": False,
        "reconstructability": "PASS",
    }


def test_missing_configuration_is_visible_and_non_custodial(monkeypatch) -> None:
    for name in ("STEGVERSE_MASTER_RECORDS_USAGE_URL", "STEGVERSE_MASTER_RECORDS_ENDPOINT", "STEGVERSE_MASTER_RECORDS_HOSTPORT", "STEGVERSE_MASTER_RECORDS_TOKEN"):
        monkeypatch.delenv(name, raising=False)
    result = submit_provider_usage_to_master_records(_event())
    assert result["status"] == "NOT_CONFIGURED"
    assert result["custody_recorded"] is False
    assert result["authority_granted"] is False


def test_partial_configuration_fails_closed(monkeypatch) -> None:
    monkeypatch.setenv("STEGVERSE_MASTER_RECORDS_USAGE_URL", "https://records.example/api/custody/provider-usage")
    monkeypatch.delenv("STEGVERSE_MASTER_RECORDS_TOKEN", raising=False)
    with pytest.raises(MasterRecordsUsageError, match="configuration_incomplete"):
        submit_provider_usage_to_master_records(_event())


def test_remote_http_is_rejected(monkeypatch) -> None:
    monkeypatch.setenv("STEGVERSE_MASTER_RECORDS_USAGE_URL", "http://records.example/api/custody/provider-usage")
    monkeypatch.setenv("STEGVERSE_MASTER_RECORDS_TOKEN", "secret")
    with pytest.raises(MasterRecordsUsageError, match="must_use_https"):
        submit_provider_usage_to_master_records(_event())


def test_private_render_hostport_is_allowed_only_by_explicit_server_flag(monkeypatch) -> None:
    monkeypatch.delenv("STEGVERSE_MASTER_RECORDS_USAGE_URL", raising=False)
    monkeypatch.delenv("STEGVERSE_MASTER_RECORDS_ENDPOINT", raising=False)
    monkeypatch.setenv("STEGVERSE_MASTER_RECORDS_HOSTPORT", "stegverse-master-records-custody:10000")
    monkeypatch.setenv("STEGVERSE_MASTER_RECORDS_TOKEN", "generated-secret")
    event = _event()
    captured = {}

    def opener(outbound, timeout):
        captured["url"] = outbound.full_url
        captured["authorization"] = outbound.headers["Authorization"]
        return _Response(_receipt(event))

    with pytest.raises(MasterRecordsUsageError, match="must_use_https"):
        submit_provider_usage_to_master_records(event, opener=opener)
    monkeypatch.setenv("STEGVERSE_ALLOW_PRIVATE_MASTER_RECORDS_HTTP", "true")
    result = submit_provider_usage_to_master_records(event, opener=opener)
    assert captured["url"] == "http://stegverse-master-records-custody:10000/api/custody/provider-usage"
    assert captured["authorization"] == "Bearer generated-secret"
    assert result["custody_recorded"] is True
    assert "generated-secret" not in json.dumps(result)


def test_identity_bound_receipt_records_custody_without_authority(monkeypatch) -> None:
    monkeypatch.setenv("STEGVERSE_MASTER_RECORDS_USAGE_URL", "https://records.example/api/custody/provider-usage")
    monkeypatch.setenv("STEGVERSE_MASTER_RECORDS_TOKEN", "secret")
    event = _event()
    captured = {}

    def opener(outbound, timeout):
        captured["authorization"] = outbound.headers["Authorization"]
        captured["session"] = outbound.headers["X-stegverse-session"]
        captured["body"] = json.loads(outbound.data.decode("utf-8"))
        return _Response(_receipt(event))

    result = submit_provider_usage_to_master_records(event, opener=opener)
    assert result["status"] == "CUSTODY_RECORDED"
    assert result["custody_recorded"] is True
    assert result["authority_granted"] is False
    assert result["reconstructability"] == "PASS"
    assert captured["authorization"] == "Bearer secret"
    assert captured["session"] == event["session_id"]
    assert captured["body"]["authority_requested"] is False
    assert captured["body"]["custody_requested"] is True
    assert "secret" not in json.dumps(result)


def test_receipt_identity_drift_fails_closed(monkeypatch) -> None:
    monkeypatch.setenv("STEGVERSE_MASTER_RECORDS_USAGE_URL", "https://records.example/api/custody/provider-usage")
    monkeypatch.setenv("STEGVERSE_MASTER_RECORDS_TOKEN", "secret")
    event = _event()

    def opener(outbound, timeout):
        receipt = _receipt(event)
        receipt["session_id"] = "different-session"
        return _Response(receipt)

    with pytest.raises(MasterRecordsUsageError, match="session_mismatch"):
        submit_provider_usage_to_master_records(event, opener=opener)


def test_authority_escalation_fails_closed(monkeypatch) -> None:
    monkeypatch.setenv("STEGVERSE_MASTER_RECORDS_USAGE_URL", "https://records.example/api/custody/provider-usage")
    monkeypatch.setenv("STEGVERSE_MASTER_RECORDS_TOKEN", "secret")
    event = _event()

    def opener(outbound, timeout):
        receipt = _receipt(event)
        receipt["authority_granted"] = True
        return _Response(receipt)

    with pytest.raises(MasterRecordsUsageError, match="authority_escalation"):
        submit_provider_usage_to_master_records(event, opener=opener)
