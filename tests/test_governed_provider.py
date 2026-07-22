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
    monkeypatch.delenv("STEGVERSE_PROVIDER_PROTOCOL", raising=False)
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
    assert "provider_not_enabled" in (result.reason or "")


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


def test_openai_compatible_profile_translates_request_and_response(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    configure(monkeypatch, tmp_path)
    monkeypatch.setenv("STEGVERSE_PROVIDER_PROTOCOL", "openai-chat-completions-v1")
    monkeypatch.setenv(
        "STEGVERSE_PROVIDER_ENDPOINT",
        "https://models.github.ai/inference/chat/completions",
    )
    monkeypatch.setenv("STEGVERSE_PROVIDER_ALLOWED_HOSTS", "models.github.ai")
    monkeypatch.setenv("STEGVERSE_PROVIDER_MODEL", "openai/gpt-4.1")

    def fake_post(url: str, *, headers: dict, data: str, timeout: float):
        request = json.loads(data)
        assert url == "https://models.github.ai/inference/chat/completions"
        assert request == {
            "model": "openai/gpt-4.1",
            "messages": [{"role": "user", "content": "Explain current state"}],
        }
        assert headers["Authorization"] == "Bearer test-token"
        return FakeResponse({
            "id": "github-models-request-1",
            "choices": [
                {"message": {"role": "assistant", "content": "Bounded model response"}}
            ],
            "usage": {"prompt_tokens": 5, "completion_tokens": 4, "total_tokens": 9},
        })

    monkeypatch.setattr(governed_provider.requests, "post", fake_post)
    result = governed_provider.generate(
        message="Explain current state",
        transition_id="transition-1",
        run_id="run-1",
    )

    assert result.used is True
    assert result.status == "USED"
    assert result.text == "Bounded model response"
    assert result.provider_request_id == "github-models-request-1"
    assert result.input_units == len("Explain current state")
    assert result.output_units == len("Bounded model response")
    assert result.provider_receipt_id.startswith("provider-response-receipt:sha256:")


def test_openai_compatible_profile_missing_choice_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    configure(monkeypatch, tmp_path)
    monkeypatch.setenv("STEGVERSE_PROVIDER_PROTOCOL", "openai-chat-completions-v1")
    monkeypatch.setattr(
        governed_provider.requests,
        "post",
        lambda *args, **kwargs: FakeResponse({"id": "request-without-choice", "choices": []}),
    )
    result = governed_provider.generate(message="hello", transition_id="t", run_id="r")
    assert result.used is False
    assert result.status == "CONTRACT_FAILED"
    assert result.fallback_required is True


def test_unsupported_protocol_fails_closed(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    configure(monkeypatch, tmp_path)
    monkeypatch.setenv("STEGVERSE_PROVIDER_PROTOCOL", "unknown-provider-wire-v9")
    provider_readiness = governed_provider.readiness()
    assert provider_readiness.ready is False
    assert provider_readiness.protocol_supported is False
    assert "provider_protocol_unsupported" in provider_readiness.blockers
    assert governed_provider.enabled() is False


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
    provider_readiness = governed_provider.readiness()
    assert provider_readiness.ready is False
    assert "provider_endpoint_hostname_not_allowlisted" in provider_readiness.blockers
    assert governed_provider.enabled() is False


def test_empty_allowlist_fails_closed(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    configure(monkeypatch, tmp_path)
    monkeypatch.delenv("STEGVERSE_PROVIDER_ALLOWED_HOSTS")
    provider_readiness = governed_provider.readiness()
    assert provider_readiness.ready is False
    assert provider_readiness.explicit_allowlist_configured is False
    assert "provider_allowed_hosts_missing" in provider_readiness.blockers
    assert governed_provider.enabled() is False


def test_readiness_is_secret_free(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    configure(monkeypatch, tmp_path)
    payload = governed_provider.readiness().to_dict()
    serialized = json.dumps(payload, sort_keys=True)
    assert payload["ready"] is True
    assert payload["state"] == "READY"
    assert payload["blockers"] == []
    assert payload["credential_configured"] is True
    assert payload["protocol"] == "stegverse-v1"
    assert payload["protocol_supported"] is True
    assert payload["authority_granted"] is False
    assert payload["execution_authority"] is False
    assert "test-token" not in serialized
    assert "token" not in payload


def test_non_https_endpoint_fails_closed(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    configure(monkeypatch, tmp_path)
    monkeypatch.setenv("STEGVERSE_PROVIDER_ENDPOINT", "http://provider.example.test/generate")
    provider_readiness = governed_provider.readiness()
    assert provider_readiness.ready is False
    assert "provider_endpoint_not_https" in provider_readiness.blockers


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
