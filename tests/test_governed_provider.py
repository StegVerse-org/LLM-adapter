from __future__ import annotations

import json
from pathlib import Path

import pytest

from llm_adapter import governed_provider


class FakeResponse:
    def __init__(self, payload: dict, status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise governed_provider.requests.HTTPError(f"HTTP {self.status_code}")

    def json(self) -> dict:
        return self._payload


def configure(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("STEGVERSE_PROVIDER_ENABLED", "true")
    monkeypatch.setenv("STEGVERSE_PROVIDER_ENDPOINT", "https://provider.example.test/generate")
    monkeypatch.setenv("STEGVERSE_PROVIDER_ALLOWED_HOSTS", "provider.example.test")
    monkeypatch.setenv("STEGVERSE_PROVIDER_TOKEN", "test-token")
    monkeypatch.setenv("STEGVERSE_PROVIDER_MODEL", "bounded-model")
    monkeypatch.setenv("STEGVERSE_PROVIDER_NAME", "test-provider")
    monkeypatch.setenv("STEGVERSE_TRANSITION_DB", str(tmp_path / "provider.db"))
    monkeypatch.setenv("STEGVERSE_PROVIDER_MAX_INPUT_CHARS", "12000")
    monkeypatch.setenv("STEGVERSE_PROVIDER_MAX_OUTPUT_CHARS", "6000")
    monkeypatch.setenv("STEGVERSE_PROVIDER_DAILY_REQUEST_LIMIT", "10")
    monkeypatch.setenv("STEGVERSE_PROVIDER_DAILY_COST_LIMIT_USD", "5")
    monkeypatch.setenv("STEGVERSE_PROVIDER_MAX_REQUEST_COST_USD", "1")


def test_disabled_provider_requires_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("STEGVERSE_PROVIDER_ENABLED", raising=False)
    result = governed_provider.generate(message="hello", transition_id="t", run_id="r")
    assert result.used is False
    assert result.status == "DISABLED"
    assert result.fallback_required is True


def test_provider_call_preserves_identity_and_writes_receipt(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    configure(monkeypatch, tmp_path)

    def fake_post(url: str, *, headers: dict, data: str, timeout: float):
        request = json.loads(data)
        assert request["metadata"]["transition_id"] == "transition-1"
        assert request["metadata"]["run_id"] == "run-1"
        assert headers["Authorization"] == "Bearer test-token"
        return FakeResponse({
            "text": "Provider bounded response",
            "provider_request_id": "provider-request-1",
            "usage": {"input_chars": 20, "output_chars": 25},
            "metadata": {"transition_id": "transition-1", "run_id": "run-1"},
        })

    monkeypatch.setattr(governed_provider.requests, "post", fake_post)
    result = governed_provider.generate(
        message="Explain current state",
        transition_id="transition-1",
        run_id="run-1",
    )
    assert result.used is True
    assert result.status == "USED"
    assert result.text == "Provider bounded response"
    assert result.provider_receipt_id.startswith("provider-response-receipt:sha256:")
    assert result.fallback_required is False
    count, spent = governed_provider.ProviderUsageLedger().current("test-provider")
    assert count == 1
    assert spent > 0


def test_identity_mismatch_fails_closed(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    configure(monkeypatch, tmp_path)
    monkeypatch.setattr(
        governed_provider.requests,
        "post",
        lambda *args, **kwargs: FakeResponse({
            "text": "Wrong identity response",
            "metadata": {"transition_id": "other", "run_id": "run-1"},
        }),
    )
    result = governed_provider.generate(message="hello", transition_id="transition-1", run_id="run-1")
    assert result.used is False
    assert result.status == "IDENTITY_FAILED"
    assert result.fallback_required is True


def test_unapproved_hostname_disables_provider(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    configure(monkeypatch, tmp_path)
    monkeypatch.setenv("STEGVERSE_PROVIDER_ALLOWED_HOSTS", "approved.example.test")
    assert governed_provider.enabled() is False


def test_cost_ceiling_blocks_before_transport(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    configure(monkeypatch, tmp_path)
    monkeypatch.setenv("STEGVERSE_PROVIDER_MAX_REQUEST_COST_USD", "0.000001")
    called = False

    def fake_post(*args, **kwargs):
        nonlocal called
        called = True
        return FakeResponse({"text": "should not happen"})

    monkeypatch.setattr(governed_provider.requests, "post", fake_post)
    result = governed_provider.generate(message="hello", transition_id="t", run_id="r")
    assert result.status == "COST_BLOCKED"
    assert called is False
