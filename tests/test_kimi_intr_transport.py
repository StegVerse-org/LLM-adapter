import re

from llm_adapter.kimi_intr_transport import (
    KIMI_BASE_URL,
    KIMI_CHAT_URL,
    KimiHTTPTransport,
    KimiTransportAdmissionError,
    KimiTransportConfigurationError,
    KimiTransportError,
    build_kimi_intr_envelope,
    kimi_wire_bytes,
    kimi_wire_request_hash,
)
from llm_adapter.provider_request import build_provider_request, stable_json


class _FakeResponse:
    def __init__(self, body=None):
        self._body = body or {
            "id": "kimi-test-1",
            "model": "kimi-k3",
            "choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 3, "completion_tokens": 1, "total_tokens": 4},
        }

    def raise_for_status(self):
        return None

    def json(self):
        return self._body


def _request(content="hello", model="kimi-k3"):
    return build_provider_request(
        provider="kimi",
        model=model,
        messages=[{"role": "user", "content": content}],
        temperature=0.0,
    )


def _envelope(request, **overrides):
    kwargs = {
        "transition_id": "intr-transition-001",
        "ingress_disposition": "ALLOW",
        "ingress_receipt_hash": "a" * 64,
        "carrier_ref": "hb:carrier:kimi",
    }
    kwargs.update(overrides)
    return build_kimi_intr_envelope(request, **kwargs)


def test_ingress_requires_exact_allow():
    for disposition in ("DENY", "allow", "ALLOW ", "ALLOWED", ""):
        try:
            _envelope(_request(), ingress_disposition=disposition)
            assert False, f"{disposition!r} must fail closed"
        except KimiTransportAdmissionError:
            pass


def test_transport_id_is_namespaced_deterministic_and_sensitive():
    request = _request()
    first = _envelope(request)
    second = _envelope(request)
    changed = _envelope(request, carrier_ref="hb:carrier:other")
    assert first.transport_id == second.transport_id
    assert re.fullmatch(r"kmit-[0-9a-f]{64}", first.transport_id)
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
    assert envelope.request_hash == kimi_wire_request_hash(request)
    assert kimi_wire_bytes(request) == stable_json(expected).encode("utf-8")
    assert envelope.request_hash != request.request_hash


def test_only_official_endpoint_is_allowed():
    assert KIMI_BASE_URL == "https://api.moonshot.ai/v1"
    assert KIMI_CHAT_URL == "https://api.moonshot.ai/v1/chat/completions"
    try:
        KimiHTTPTransport(credential_resolver=lambda: "ephemeral", base_url="https://example.com")
        assert False, "endpoint drift must fail closed"
    except KimiTransportConfigurationError:
        pass


def test_supported_model_is_explicit():
    _envelope(_request(model="kimi-k3"))
    try:
        _envelope(_request(model="moonshot-v1"))
        assert False, "unadmitted model alias must fail closed"
    except KimiTransportConfigurationError:
        pass


def test_post_admission_tamper_fails_before_credential_resolution():
    admitted = _request()
    envelope = _envelope(admitted)
    calls = []
    transport = KimiHTTPTransport(credential_resolver=lambda: calls.append(1) or "ephemeral")
    try:
        transport.complete(envelope, _request("tampered"))
        assert False, "wire hash mismatch must fail closed"
    except KimiTransportAdmissionError:
        pass
    assert calls == []


def test_success_resolves_compatibility_credential_once_and_emits_no_secret(monkeypatch):
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

    monkeypatch.setattr("llm_adapter.kimi_intr_transport.requests.post", fake_post)
    result = KimiHTTPTransport(credential_resolver=resolver).complete(envelope, request)
    assert calls["url"] == KIMI_CHAT_URL
    assert calls["data"] == kimi_wire_bytes(request)
    assert calls["headers"]["Authorization"] == "Bearer ephemeral-tv-tvc-secret"
    assert len(resolver_calls) == 1
    assert result.response.output == "ok"
    assert result.response.metadata["authority_effect"] == "NONE"
    assert result.evidence()["egress_intr_required"] is True
    assert "ephemeral-tv-tvc-secret" not in str(result.evidence())


def test_secret_echo_fails_closed(monkeypatch):
    secret = "not-a-real-secret"
    body = {
        "id": "kimi-test-1",
        "model": "kimi-k3",
        "choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 3, "completion_tokens": 1, "total_tokens": 4},
        "echo": secret,
    }
    monkeypatch.setattr(
        "llm_adapter.kimi_intr_transport.requests.post",
        lambda *args, **kwargs: _FakeResponse(body),
    )
    try:
        KimiHTTPTransport(credential_resolver=lambda: secret).complete(_envelope(_request()), _request())
        assert False, "provider credential echo must fail closed"
    except KimiTransportError:
        pass
