import pytest

from llm_adapter.http_provider_clients import (
    AnthropicHTTPProviderClient,
    OpenAIHTTPProviderClient,
    ProviderConfigurationError,
    StegVerseLocalHTTPProviderClient,
    build_http_provider_client,
)
from llm_adapter.provider_request import build_provider_request


def test_openai_http_provider_fails_closed_without_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    request = build_provider_request(provider="openai", model="test-model", messages=[{"role": "user", "content": "Hello"}])
    with pytest.raises(ProviderConfigurationError):
        OpenAIHTTPProviderClient().complete(request)


def test_anthropic_http_provider_fails_closed_without_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    request = build_provider_request(provider="anthropic", model="test-model", messages=[{"role": "user", "content": "Hello"}])
    with pytest.raises(ProviderConfigurationError):
        AnthropicHTTPProviderClient().complete(request)


def test_build_http_provider_client_routes_names():
    assert isinstance(build_http_provider_client("openai", api_key="test"), OpenAIHTTPProviderClient)
    assert isinstance(build_http_provider_client("claude", api_key="test"), AnthropicHTTPProviderClient)
    assert isinstance(build_http_provider_client("stegverse-local"), StegVerseLocalHTTPProviderClient)


def test_sovereign_provider_rejects_public_host():
    with pytest.raises(ProviderConfigurationError):
        StegVerseLocalHTTPProviderClient(base_url="https://example.com/v1/chat/completions")


def test_sovereign_provider_accepts_loopback_without_credential(monkeypatch):
    captured = {}

    class FakeResponse:
        def raise_for_status(self): return None
        def json(self):
            return {"id":"local-1","choices":[{"message":{"content":"sovereign fixture"},"finish_reason":"stop"}]}

    def fake_post(url, **kwargs):
        captured["url"] = url
        captured["headers"] = kwargs.get("headers") or {}
        return FakeResponse()

    monkeypatch.setattr("llm_adapter.http_provider_clients.requests.post", fake_post)
    request = build_provider_request(provider="stegverse-local", model="stegverse-local-model", messages=[{"role":"user","content":"Hello"}])
    response = StegVerseLocalHTTPProviderClient().complete(request)
    assert captured["url"].startswith("http://127.0.0.1:")
    assert "Authorization" not in captured["headers"]
    assert response.output == "sovereign fixture"
    assert response.request_hash == request.request_hash
    assert response.metadata["provider_mode"] == "stegverse_local_openai_compatible"
    assert response.metadata["third_party_execution_platform_required"] is False
    assert response.metadata["provider_credential_required"] is False


def test_sovereign_provider_accepts_private_federated_address():
    client = StegVerseLocalHTTPProviderClient(base_url="http://10.23.4.5:8080/v1/chat/completions")
    assert client.base_url.startswith("http://10.23.4.5")


def test_openai_http_provider_response_is_request_bound(monkeypatch):
    class FakeResponse:
        def raise_for_status(self): return None
        def json(self): return {"id":"openai-response-id","choices":[{"message":{"content":"fixture output"},"finish_reason":"stop"}]}
    monkeypatch.setattr("llm_adapter.http_provider_clients.requests.post", lambda *args, **kwargs: FakeResponse())
    request = build_provider_request(provider="openai", model="test-model", messages=[{"role":"user","content":"Hello"}])
    response = OpenAIHTTPProviderClient(api_key="test-key").complete(request)
    assert response.request_hash == request.request_hash
    assert response.output == "fixture output"
    assert response.metadata["provider_mode"] == "openai_http"


def test_anthropic_http_provider_response_is_request_bound(monkeypatch):
    class FakeResponse:
        def raise_for_status(self): return None
        def json(self): return {"id":"anthropic-response-id","content":[{"type":"text","text":"fixture output"}],"stop_reason":"end_turn"}
    monkeypatch.setattr("llm_adapter.http_provider_clients.requests.post", lambda *args, **kwargs: FakeResponse())
    request = build_provider_request(provider="anthropic", model="test-model", messages=[{"role":"user","content":"Hello"}])
    response = AnthropicHTTPProviderClient(api_key="test-key").complete(request)
    assert response.request_hash == request.request_hash
    assert response.output == "fixture output"
    assert response.metadata["provider_mode"] == "anthropic_http"
