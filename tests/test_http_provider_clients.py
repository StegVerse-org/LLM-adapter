import pytest

from llm_adapter import (
    AnthropicHTTPProviderClient,
    OpenAIHTTPProviderClient,
    ProviderConfigurationError,
    build_http_provider_client,
    build_provider_request,
)


def test_openai_http_provider_fails_closed_without_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    request = build_provider_request(
        provider="openai",
        model="test-model",
        messages=[{"role": "user", "content": "Hello"}],
    )

    with pytest.raises(ProviderConfigurationError):
        OpenAIHTTPProviderClient().complete(request)


def test_anthropic_http_provider_fails_closed_without_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    request = build_provider_request(
        provider="anthropic",
        model="test-model",
        messages=[{"role": "user", "content": "Hello"}],
    )

    with pytest.raises(ProviderConfigurationError):
        AnthropicHTTPProviderClient().complete(request)


def test_build_http_provider_client_routes_names():
    assert isinstance(build_http_provider_client("openai", api_key="test"), OpenAIHTTPProviderClient)
    assert isinstance(build_http_provider_client("claude", api_key="test"), AnthropicHTTPProviderClient)


def test_openai_http_provider_response_is_request_bound(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "id": "openai-response-id",
                "choices": [
                    {
                        "message": {"content": "fixture output"},
                        "finish_reason": "stop",
                    }
                ],
            }

    def fake_post(*args, **kwargs):
        return FakeResponse()

    monkeypatch.setattr("llm_adapter.http_provider_clients.requests.post", fake_post)
    request = build_provider_request(
        provider="openai",
        model="test-model",
        messages=[{"role": "user", "content": "Hello"}],
    )

    response = OpenAIHTTPProviderClient(api_key="test-key").complete(request)

    assert response.request_hash == request.request_hash
    assert response.output == "fixture output"
    assert response.metadata["provider_mode"] == "openai_http"


def test_anthropic_http_provider_response_is_request_bound(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "id": "anthropic-response-id",
                "content": [{"type": "text", "text": "fixture output"}],
                "stop_reason": "end_turn",
            }

    def fake_post(*args, **kwargs):
        return FakeResponse()

    monkeypatch.setattr("llm_adapter.http_provider_clients.requests.post", fake_post)
    request = build_provider_request(
        provider="anthropic",
        model="test-model",
        messages=[{"role": "user", "content": "Hello"}],
    )

    response = AnthropicHTTPProviderClient(api_key="test-key").complete(request)

    assert response.request_hash == request.request_hash
    assert response.output == "fixture output"
    assert response.metadata["provider_mode"] == "anthropic_http"
