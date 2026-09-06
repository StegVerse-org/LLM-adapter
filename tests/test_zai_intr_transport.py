import json
import re

from llm_adapter.provider_request import build_provider_request, stable_json
from llm_adapter.zai_intr_transport import (
    ZAI_CODING_BASE_URL,
    ZAI_GENERAL_BASE_URL,
    ZAIHTTPTransport,
    ZAITransportAdmissionError,
    ZAITransportConfigurationError,
    ZAITransportError,
    assert_no_secret_material,
    build_zai_intr_envelope,
    zai_wire_bytes,
    zai_wire_request_hash,
)


class _FakeResponse:
    def __init__(self, body=None, status_error=None):
        self._body = body or {
            "id": "zai-test-1",
            "model": "glm-fixture-model",
            "choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 3, "completion_tokens": 1, "total_tokens": 4},
        }
        self._status_error = status_error

    def raise_for_status(self):
        if self._status_error:
            raise self._status_error
        return None

    def json(self):
        return self._body


def _request(content="hello"):
    return build_provider_request(
        provider="z.ai",
        model="glm-fixture-model",
        messages=[{"role": "user", "content": content}],
        temperature=0.0,
    )


def _envelope(request, **overrides):
    kwargs = {
        "transition_id": "intr-transition-001",
        "ingress_disposition": "ALLOW",
        "ingress_receipt_hash": "a" * 64,
        "carrier_ref": "hb32:carrier:example",
        "endpoint_profile": "general",
    }
    kwargs.update(overrides)
    return build_zai_intr_envelope(request, **kwargs)


def test_ingress_requires_exact_allow():
    for disposition in ("DENY", "allow", "ALLOW ", "ALLOWED", ""):
        try:
            _envelope(_request(), ingress_disposition=disposition)
            assert False, f"{disposition!r} must not produce a transport envelope"
        except ZAITransportAdmissionError:
            pass


def test_transport_id_is_namespaced_deterministic_and_input_sensitive():
    request = _request()
    first = _envelope(request)
    second = _envelope(request)
    changed = _envelope(request, carrier_ref="hb32:carrier:other")
    assert first.transport_id == second.transport_id
    assert re.fullmatch(r"zait-[0-9a-f]{64}", first.transport_id)
    assert changed.transport_id != first.transport_id


def test_envelope_binds_exact_wire_request_not_broader_provider_envelope():
    request = _request()
    envelope = _envelope(request)
    assert envelope.request_hash == zai_wire_request_hash(request)
    assert envelope.request_hash != request.request_hash
    assert zai_wire_bytes(request) == stable_json({
        "model": request.model,
        "messages": [m.to_dict() for m in request.messages],
        "temperature": request.temperature,
    }).encode("utf-8")


def test_transport_envelope_contains_no_credential_material():
    serialized = _envelope(_request()).to_dict()
    assert serialized["credential_authority"] == "TV/TVC"
    assert serialized["credential_material_present"] is False
    assert serialized["authority_effect"] == "NONE"
    assert serialized["egress_intr_required"] is True
    assert "secret" not in " ".join(serialized.keys()).lower()
    assert "token" not in " ".join(serialized.keys()).lower()


def test_endpoint_is_strictly_allowlisted():
    try:
        ZAIHTTPTransport(credential_resolver=lambda: "ephemeral", base_url="https://example.com/v1")
        assert False, "unapproved endpoint must fail closed"
    except ZAITransportConfigurationError:
        pass


def test_post_admission_request_tamper_fails_closed_before_provider_call():
    admitted = _request()
    envelope = _envelope(admitted)
    different = _request("different")
    calls = []
    transport = ZAIHTTPTransport(credential_resolver=lambda: calls.append("credential") or "ephemeral")
    try:
        transport.complete(envelope, different)
        assert False, "wire hash mismatch must fail closed before credential resolution/provider call"
    except ZAITransportAdmissionError:
        pass
    assert calls == []


def test_endpoint_profile_must_match_admitted_envelope():
    request = _request()
    envelope = _envelope(request, endpoint_profile="coding")
    transport = ZAIHTTPTransport(credential_resolver=lambda: "ephemeral", base_url=ZAI_GENERAL_BASE_URL)
    try:
        transport.complete(envelope, request)
        assert False, "endpoint profile mismatch must fail closed"
    except ZAITransportConfigurationError:
        pass


def test_success_sends_exact_hashed_bytes_resolves_credential_once_and_requires_egress(monkeypatch):
    request = _request()
    envelope = _envelope(request)
    calls = {}
    resolver_calls = []

    def resolver():
        resolver_calls.append(1)
        return "ephemeral-tv-tvc-resolved"

    def fake_post(url, *, headers, data, timeout):
        calls["url"] = url
        calls["headers"] = headers
        calls["data"] = data
        calls["timeout"] = timeout
        return _FakeResponse()

    monkeypatch.setattr("llm_adapter.zai_intr_transport.requests.post", fake_post)
    transport = ZAIHTTPTransport(credential_resolver=resolver)
    result = transport.complete(envelope, request)

    assert calls["url"] == f"{ZAI_GENERAL_BASE_URL}/chat/completions"
    assert calls["data"] == zai_wire_bytes(request)
    assert calls["headers"]["Authorization"] == "Bearer ephemeral-tv-tvc-resolved"
    assert len(resolver_calls) == 1
    assert result.response.output == "ok"
    assert result.response.request_hash == envelope.request_hash
    assert result.provider_request_hash == request.request_hash
    assert result.response.metadata["transport_id"] == envelope.transport_id
    assert result.response.metadata["credential_material_present"] is False
    assert result.response.metadata["authority_effect"] == "NONE"
    assert result.evidence()["egress_intr_required"] is True
    assert "ephemeral-tv-tvc-resolved" not in str(result.evidence())


def test_secret_echo_in_provider_body_fails_closed(monkeypatch):
    secret = "test-secret-not-real"
    leaked = {
        "id": "zai-test-1",
        "model": "glm-fixture-model",
        "choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 3, "completion_tokens": 1, "total_tokens": 4},
        "echo": secret,
    }

    def fake_post(url, *, headers, data, timeout):
        return _FakeResponse(leaked)

    monkeypatch.setattr("llm_adapter.zai_intr_transport.requests.post", fake_post)
    try:
        ZAIHTTPTransport(credential_resolver=lambda: secret).complete(_envelope(_request()), _request())
        assert False, "provider credential echo must fail closed"
    except ZAITransportError:
        pass


def test_secret_in_outbound_structure_fails_closed():
    secret = "test-secret-not-real"
    try:
        assert_no_secret_material(secret, envelope={"carrier_ref": secret})
        assert False, "secret material in evidence must fail closed"
    except ZAITransportError:
        pass


def test_malformed_provider_usage_fails_closed(monkeypatch):
    malformed = {
        "id": "zai-test-1",
        "model": "glm-fixture-model",
        "choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": "3", "completion_tokens": 1, "total_tokens": 4},
    }

    monkeypatch.setattr(
        "llm_adapter.zai_intr_transport.requests.post",
        lambda url, *, headers, data, timeout: _FakeResponse(malformed),
    )
    try:
        ZAIHTTPTransport(credential_resolver=lambda: "ephemeral").complete(_envelope(_request()), _request())
        assert False, "malformed usage must fail closed"
    except ZAITransportError:
        pass


def test_coding_endpoint_profile_is_supported():
    request = _request()
    envelope = _envelope(request, endpoint_profile="coding")
    transport = ZAIHTTPTransport(credential_resolver=lambda: "ephemeral", base_url=ZAI_CODING_BASE_URL)
    assert transport.base_url == ZAI_CODING_BASE_URL
    assert envelope.endpoint_profile == "coding"
