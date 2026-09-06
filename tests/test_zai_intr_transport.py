from llm_adapter.provider_request import build_provider_request
from llm_adapter.zai_intr_transport import (
    ZAI_CODING_BASE_URL,
    ZAI_GENERAL_BASE_URL,
    ZAIHTTPTransport,
    ZAITransportAdmissionError,
    ZAITransportConfigurationError,
    build_zai_intr_envelope,
)


class _FakeResponse:
    def raise_for_status(self):
        return None

    def json(self):
        return {
            "id": "zai-test-1",
            "model": "glm-fixture-model",
            "choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 3, "completion_tokens": 1, "total_tokens": 4},
        }


def _request():
    return build_provider_request(
        provider="z.ai",
        model="glm-fixture-model",
        messages=[{"role": "user", "content": "hello"}],
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


def test_ingress_deny_fails_closed():
    request = _request()
    try:
        _envelope(request, ingress_disposition="DENY")
        assert False, "DENY must not produce a transport envelope"
    except ZAITransportAdmissionError:
        pass


def test_transport_envelope_contains_no_credential_material():
    envelope = _envelope(_request())
    serialized = envelope.to_dict()
    assert serialized["credential_authority"] == "TV/TVC"
    assert serialized["credential_material_present"] is False
    assert serialized["authority_effect"] == "NONE"
    assert serialized["egress_intr_required"] is True
    assert "secret" not in " ".join(serialized.keys()).lower()
    assert "token" not in " ".join(serialized.keys()).lower()


def test_endpoint_is_strictly_allowlisted():
    try:
        ZAIHTTPTransport(credential="ephemeral", base_url="https://example.com/v1")
        assert False, "unapproved endpoint must fail closed"
    except ZAITransportConfigurationError:
        pass


def test_request_hash_mismatch_fails_closed():
    admitted = _request()
    envelope = _envelope(admitted)
    different = build_provider_request(
        provider="z.ai",
        model="glm-fixture-model",
        messages=[{"role": "user", "content": "different"}],
    )
    transport = ZAIHTTPTransport(credential="ephemeral")
    try:
        transport.complete(envelope, different)
        assert False, "hash mismatch must fail closed before provider call"
    except ZAITransportAdmissionError:
        pass


def test_endpoint_profile_must_match_admitted_envelope():
    request = _request()
    envelope = _envelope(request, endpoint_profile="coding")
    transport = ZAIHTTPTransport(credential="ephemeral", base_url=ZAI_GENERAL_BASE_URL)
    try:
        transport.complete(envelope, request)
        assert False, "endpoint profile mismatch must fail closed"
    except ZAITransportConfigurationError:
        pass


def test_success_retains_ingress_binding_and_requires_egress(monkeypatch):
    request = _request()
    envelope = _envelope(request)
    calls = {}

    def fake_post(url, *, headers, json, timeout):
        calls["url"] = url
        calls["headers"] = headers
        calls["json"] = json
        calls["timeout"] = timeout
        return _FakeResponse()

    monkeypatch.setattr("llm_adapter.zai_intr_transport.requests.post", fake_post)
    transport = ZAIHTTPTransport(credential="ephemeral-tv-tvc-resolved")
    result = transport.complete(envelope, request)

    assert calls["url"] == f"{ZAI_GENERAL_BASE_URL}/chat/completions"
    assert calls["headers"]["Authorization"].startswith("Bearer ")
    assert result.response.output == "ok"
    assert result.response.metadata["transport_id"] == envelope.transport_id
    assert result.response.metadata["ingress_receipt_hash"] == "a" * 64
    assert result.response.metadata["credential_material_present"] is False
    assert result.response.metadata["authority_effect"] == "NONE"
    assert result.egress_intr_required is True
    assert result.evidence()["egress_intr_required"] is True
    assert "ephemeral-tv-tvc-resolved" not in str(result.evidence())


def test_coding_endpoint_profile_is_supported():
    request = _request()
    envelope = _envelope(request, endpoint_profile="coding")
    transport = ZAIHTTPTransport(credential="ephemeral", base_url=ZAI_CODING_BASE_URL)
    assert transport.base_url == ZAI_CODING_BASE_URL
    assert envelope.endpoint_profile == "coding"
