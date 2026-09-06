import re

from llm_adapter.deepseek_intr_transport import (
    DEEPSEEK_BASE_URL,
    DEEPSEEK_CHAT_URL,
    DeepSeekHTTPTransport,
    DeepSeekTransportAdmissionError,
    DeepSeekTransportConfigurationError,
    DeepSeekTransportError,
    build_deepseek_intr_envelope,
    deepseek_wire_bytes,
    deepseek_wire_request_hash,
)
from llm_adapter.provider_request import build_provider_request, stable_json


class _FakeResponse:
    def __init__(self, body=None):
        self._body = body or {
            "id": "deepseek-test-1",
            "model": "deepseek-v4-flash",
            "choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 3, "completion_tokens": 1, "total_tokens": 4},
        }

    def raise_for_status(self):
        return None

    def json(self):
        return self._body


def _request(content="hello", model="deepseek-v4-flash"):
    return build_provider_request(
        provider="deepseek",
        model=model,
        messages=[{"role": "user", "content": content}],
        temperature=0.0,
    )


def _envelope(request, **overrides):
    kwargs = {
        "transition_id": "intr-transition-001",
        "ingress_disposition": "ALLOW",
        "ingress_receipt_hash": "a" * 64,
        "carrier_ref": "hb:carrier:deepseek",
    }
    kwargs.update(overrides)
    return build_deepseek_intr_envelope(request, **kwargs)


def test_ingress_requires_exact_allow():
    for disposition in ("DENY", "allow", "ALLOW ", "ALLOWED", ""):
        try:
            _envelope(_request(), ingress_disposition=disposition)
            assert False, f"{disposition!r} must fail closed"
        except DeepSeekTransportAdmissionError:
            pass


def test_transport_id_is_namespaced_deterministic_and_sensitive():
    request = _request()
    first = _envelope(request)
    second = _envelope(request)
    changed = _envelope(request, carrier_ref="hb:carrier:other")
    assert first.transport_id == second.transport_id
    assert re.fullmatch(r"dsit-[0-9a-f]{64}", first.transport_id)
    assert changed.transport_id != first.transport_id


def test_envelope_binds_exact_wire_bytes():
    request = _request()
    envelope = _envelope(request)
    expected = {
        "model": request.model,
        "messages": [m.to_dict() for m in request.messages],
        "temperature": request.temperature,
        "stream": False,
    }
    assert envelope.request_hash == deepseek_wire_request_hash(request)
    assert deepseek_wire_bytes(request) == stable_json(expected).encode("utf-8")
    assert envelope.request_hash != request.request_hash


def test_only_official_endpoint_is_allowed():
    assert DEEPSEEK_BASE_URL == "https://api.deepseek.com"
    assert DEEPSEEK_CHAT_URL == "https://api.deepseek.com/chat/completions"
    try:
        DeepSeekHTTPTransport(credential_resolver=lambda: "ephemeral", base_url="https://example.com")
        assert False, "endpoint drift must fail closed"
    except DeepSeekTransportConfigurationError:
        pass


def test_supported_models_are_explicit():
    _envelope(_request(model="deepseek-v4-flash"))
    _envelope(_request(model="deepseek-v4-pro"))
    try:
        _envelope(_request(model="deepseek-chat"))
        assert False, "retired/unsupported model alias must fail closed"
    except DeepSeekTransportConfigurationError:
        pass


def test_post_admission_tamper_fails_before_credential_resolution():
    admitted = _request()
    envelope = _envelope(admitted)
    calls = []
    transport = DeepSeekHTTPTransport(credential_resolver=lambda: calls.append(1) or "ephemeral")
    try:
        transport.complete(envelope, _request("tampered"))
        assert False, "wire hash mismatch must fail closed"
    except DeepSeekTransportAdmissionError:
        pass
    assert calls == []


def test_success_resolves_credential_once_and_emits_no_secret(monkeypatch):
    request = _request()
    envelope = _envelope(request)
    calls = {}
    resolver_calls = []

    def resolver():
        resolver_calls.append(1)
        return "ephemeral-tv-tvc-secret"

    def fake_post(url, *, headers, data, timeout):
        calls.update(url=url, headers=headers, data=data, timeout=timeout)
        return _FakeResponse()

    monkeypatch.setattr("llm_adapter.deepseek_intr_transport.requests.post", fake_post)
    result = DeepSeekHTTPTransport(credential_resolver=resolver).complete(envelope, request)
    assert calls["url"] == DEEPSEEK_CHAT_URL
    assert calls["data"] == deepseek_wire_bytes(request)
    assert calls["headers"]["Authorization"] == "Bearer ephemeral-tv-tvc-secret"
    assert len(resolver_calls) == 1
    assert result.response.output == "ok"
    assert result.response.metadata["authority_effect"] == "NONE"
    assert result.evidence()["egress_intr_required"] is True
    assert "ephemeral-tv-tvc-secret" not in str(result.evidence())


def test_secret_echo_fails_closed(monkeypatch):
    secret = "not-a-real-secret"
    body = {
        "id": "deepseek-test-1",
        "model": "deepseek-v4-flash",
        "choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 3, "completion_tokens": 1, "total_tokens": 4},
        "echo": secret,
    }
    monkeypatch.setattr(
        "llm_adapter.deepseek_intr_transport.requests.post",
        lambda *args, **kwargs: _FakeResponse(body),
    )
    try:
        DeepSeekHTTPTransport(credential_resolver=lambda: secret).complete(_envelope(_request()), _request())
        assert False, "provider credential echo must fail closed"
    except DeepSeekTransportError:
        pass
