
import os
import unittest
from unittest import mock
from llm_adapter.http_provider_clients import (
    AnthropicHTTPProviderClient,
    OpenAIHTTPProviderClient,
    ProviderConfigurationError,
    StegVerseLocalHTTPProviderClient,
    XAIHTTPProviderClient,
    build_http_provider_client,
)
from llm_adapter.provider_request import build_provider_request


def _fake_post(body):
    class FakeResponse:
        def raise_for_status(self): return None
        def json(self): return body
    return lambda *args, **kwargs: FakeResponse()


class HttpProviderClientsTests(unittest.TestCase):
    def _setattr(self, target, *args, raising=True):
        """monkeypatch.setattr equivalent: dotted-path or (object, name) form, undone after the test."""
        if isinstance(target, str):
            patcher = mock.patch(target, *args, create=not raising)
        else:
            patcher = mock.patch.object(target, *args, create=not raising)
        patcher.start()
        self.addCleanup(patcher.stop)

    def _setenv(self, name, value):
        """monkeypatch.setenv equivalent: os.environ is restored after the test."""
        patcher = mock.patch.dict(os.environ, {name: str(value)})
        patcher.start()
        self.addCleanup(patcher.stop)

    def _delenv(self, name, raising=True):
        """monkeypatch.delenv equivalent: os.environ is restored after the test."""
        if raising and name not in os.environ:
            raise KeyError(name)
        patcher = mock.patch.dict(os.environ)
        patcher.start()
        self.addCleanup(patcher.stop)
        os.environ.pop(name, None)

    def test_openai_http_provider_fails_closed_without_key(self):
        self._delenv("OPENAI_API_KEY", raising=False)
        request = build_provider_request(provider="openai", model="test-model", messages=[{"role": "user", "content": "Hello"}])
        with self.assertRaises(ProviderConfigurationError):
            OpenAIHTTPProviderClient().complete(request)

    def test_anthropic_http_provider_fails_closed_without_key(self):
        self._delenv("ANTHROPIC_API_KEY", raising=False)
        request = build_provider_request(provider="anthropic", model="test-model", messages=[{"role": "user", "content": "Hello"}])
        with self.assertRaises(ProviderConfigurationError):
            AnthropicHTTPProviderClient().complete(request)

    def test_build_http_provider_client_routes_names(self):
        assert isinstance(build_http_provider_client("openai", api_key="test"), OpenAIHTTPProviderClient)
        assert isinstance(build_http_provider_client("claude", api_key="test"), AnthropicHTTPProviderClient)
        assert isinstance(build_http_provider_client("stegverse-local"), StegVerseLocalHTTPProviderClient)

    def test_sovereign_provider_rejects_public_host(self):
        with self.assertRaises(ProviderConfigurationError):
            StegVerseLocalHTTPProviderClient(base_url="https://example.com/v1/chat/completions")

    def test_sovereign_provider_accepts_loopback_without_credential(self):
        captured = {}

        class FakeResponse:
            def raise_for_status(self): return None
            def json(self):
                return {"id":"local-1","choices":[{"message":{"content":"sovereign fixture"},"finish_reason":"stop"}]}

        def fake_post(url, **kwargs):
            captured["url"] = url
            captured["headers"] = kwargs.get("headers") or {}
            return FakeResponse()

        self._setattr("llm_adapter.http_provider_clients._http.post", fake_post)
        request = build_provider_request(provider="stegverse-local", model="stegverse-local-model", messages=[{"role":"user","content":"Hello"}])
        response = StegVerseLocalHTTPProviderClient().complete(request)
        assert captured["url"].startswith("http://127.0.0.1:")
        assert "Authorization" not in captured["headers"]
        assert response.output == "sovereign fixture"
        assert response.request_hash == request.request_hash
        assert response.metadata["provider_mode"] == "stegverse_local_openai_compatible"
        assert response.metadata["third_party_execution_platform_required"] is False
        assert response.metadata["provider_credential_required"] is False

    def test_sovereign_provider_accepts_private_federated_address(self):
        client = StegVerseLocalHTTPProviderClient(base_url="http://10.23.4.5:8080/v1/chat/completions")
        assert client.base_url.startswith("http://10.23.4.5")

    def test_openai_http_provider_response_is_request_bound(self):
        class FakeResponse:
            def raise_for_status(self): return None
            def json(self): return {"id":"openai-response-id","choices":[{"message":{"content":"fixture output"},"finish_reason":"stop"}]}
        self._setattr("llm_adapter.http_provider_clients._http.post", lambda *args, **kwargs: FakeResponse())
        request = build_provider_request(provider="openai", model="test-model", messages=[{"role":"user","content":"Hello"}])
        response = OpenAIHTTPProviderClient(api_key="test-key").complete(request)
        assert response.request_hash == request.request_hash
        assert response.output == "fixture output"
        assert response.metadata["provider_mode"] == "openai_http"

    def test_anthropic_http_provider_response_is_request_bound(self):
        class FakeResponse:
            def raise_for_status(self): return None
            def json(self): return {"id":"anthropic-response-id","content":[{"type":"text","text":"fixture output"}],"stop_reason":"end_turn"}
        self._setattr("llm_adapter.http_provider_clients._http.post", lambda *args, **kwargs: FakeResponse())
        request = build_provider_request(provider="anthropic", model="test-model", messages=[{"role":"user","content":"Hello"}])
        response = AnthropicHTTPProviderClient(api_key="test-key").complete(request)
        assert response.request_hash == request.request_hash
        assert response.output == "fixture output"
        assert response.metadata["provider_mode"] == "anthropic_http"

    def test_xai_factory_requires_manifest_selected_provider(self):
        client = build_http_provider_client("xai", api_key="scoped-fixture-key")
        assert isinstance(client, XAIHTTPProviderClient)
        assert isinstance(build_http_provider_client("grok", api_key="scoped-fixture-key"), XAIHTTPProviderClient)
        assert client.base_url == "https://api.x.ai/v1/chat/completions"

    def test_xai_requires_explicit_scoped_credential(self):
        self._setenv("XAI_API_KEY", "environment-key-must-not-be-used")
        request = build_provider_request(provider="xai", model="grok-fixture", messages=[{"role": "user", "content": "Hello"}])
        with self.assertRaisesRegex(ProviderConfigurationError, "XAI_CREDENTIAL_UNAVAILABLE"):
            XAIHTTPProviderClient().complete(request)

    def test_xai_refuses_unapproved_endpoint(self):
        for url in [
            "http://api.x.ai/v1/chat/completions",
            "https://untrusted.example/v1/chat/completions",
            "https://api.x.ai@untrusted.example/v1/chat/completions",
            "https://api.x.ai/v1/responses",
        ]:
            with self.subTest(url=url):
                with self.assertRaisesRegex(ProviderConfigurationError, "XAI_ENDPOINT_NOT_ALLOWED"):
                    XAIHTTPProviderClient(api_key="scoped-fixture-key", base_url=url)

    def test_xai_returns_real_response_metadata_and_native_usage(self):
        captured = {}
        class FakeResponse:
            def raise_for_status(self): return None
            def json(self): return {
                "id": "fixture-xai-response", "model": "grok-verified-fixture",
                "choices": [{"message": {"content": "Grok fixture answer"}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 12, "completion_tokens": 6, "total_tokens": 18, "cost_in_usd_ticks": 120},
            }
        def fake_post(url, **kwargs):
            captured.update({"url": url, **kwargs})
            return FakeResponse()
        self._setattr("llm_adapter.http_provider_clients._http.post", fake_post, raising=False)
        request = build_provider_request(provider="xai", model="grok-fixture", messages=[{"role": "user", "content": "Hello"}])
        response = XAIHTTPProviderClient(api_key="scoped-fixture-key").complete(request)
        assert response.request_hash == request.request_hash
        assert response.provider == "xai"
        assert response.metadata["runtime_model"] == "grok-verified-fixture"
        assert response.metadata["usage"]["total_tokens"] == 18
        assert response.metadata["usage"]["cost_in_usd_ticks"] == 120
        assert "scoped-fixture-key" not in str(response.to_dict())
        assert captured["headers"]["Authorization"] == "Bearer scoped-fixture-key"
        assert captured["json"]["stream"] is False

    def test_xai_fails_closed_on_missing_measured_usage(self):
        class FakeResponse:
            def raise_for_status(self): return None
            def json(self): return {
                "id": "fixture-xai-response", "model": "grok-fixture",
                "choices": [{"message": {"content": "unattributed"}}],
            }
        self._setattr("llm_adapter.http_provider_clients._http.post", lambda *a, **k: FakeResponse(), raising=False)
        request = build_provider_request(provider="xai", model="grok-fixture", messages=[{"role": "user", "content": "Hello"}])
        with self.assertRaisesRegex(ProviderConfigurationError, "XAI_RESPONSE_INVALID"):
            XAIHTTPProviderClient(api_key="scoped-fixture-key").complete(request)

    def test_xai_provider_mismatch_is_actionable(self):
        request = build_provider_request(provider="openai", model="grok-fixture", messages=[{"role": "user", "content": "Hello"}])
        with self.assertRaisesRegex(ProviderConfigurationError, "XAI_PROVIDER_MISMATCH"):
            XAIHTTPProviderClient(api_key="scoped-fixture-key").complete(request)

    def test_openai_http_provider_retains_measured_usage_and_runtime_model(self):
        self._setattr("llm_adapter.http_provider_clients._http.post", _fake_post({
            "id": "openai-response-id", "model": "gpt-runtime-fixture",
            "choices": [{"message": {"content": "fixture output"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 9, "completion_tokens": 3, "total_tokens": 12, "prompt_tokens_details": {"cached_tokens": 0}},
        }))
        request = build_provider_request(provider="openai", model="test-model", messages=[{"role": "user", "content": "Hello"}])
        response = OpenAIHTTPProviderClient(api_key="test-key").complete(request)
        assert response.metadata["usage"] == {"prompt_tokens": 9, "completion_tokens": 3, "total_tokens": 12}
        assert response.metadata["usage_measured"] is True
        assert response.metadata["runtime_model"] == "gpt-runtime-fixture"

    def test_openai_http_provider_marks_missing_or_malformed_usage_unmeasured(self):
        for usage in [None, {}, {"prompt_tokens": 9, "completion_tokens": "3", "total_tokens": 12},
                                           {"prompt_tokens": True, "completion_tokens": 3, "total_tokens": 12},
                                           {"prompt_tokens": -1, "completion_tokens": 3, "total_tokens": 12}]:
            with self.subTest(usage=usage):
                body = {"id": "openai-response-id", "choices": [{"message": {"content": "fixture output"}, "finish_reason": "stop"}]}
                if usage is not None:
                    body["usage"] = usage
                self._setattr("llm_adapter.http_provider_clients._http.post", _fake_post(body))
                request = build_provider_request(provider="openai", model="test-model", messages=[{"role": "user", "content": "Hello"}])
                response = OpenAIHTTPProviderClient(api_key="test-key").complete(request)
                assert response.metadata["usage"] is None
                assert response.metadata["usage_measured"] is False
                assert response.metadata["runtime_model"] is None

    def test_anthropic_http_provider_retains_measured_usage_and_runtime_model(self):
        self._setattr("llm_adapter.http_provider_clients._http.post", _fake_post({
            "id": "anthropic-response-id", "model": "claude-runtime-fixture",
            "content": [{"type": "text", "text": "fixture output"}], "stop_reason": "end_turn",
            "usage": {"input_tokens": 11, "output_tokens": 4},
        }))
        request = build_provider_request(provider="anthropic", model="test-model", messages=[{"role": "user", "content": "Hello"}])
        response = AnthropicHTTPProviderClient(api_key="test-key").complete(request)
        assert response.metadata["usage"] == {"input_tokens": 11, "output_tokens": 4}
        assert response.metadata["usage_measured"] is True
        assert response.metadata["runtime_model"] == "claude-runtime-fixture"

    def test_anthropic_http_provider_marks_missing_usage_unmeasured(self):
        self._setattr("llm_adapter.http_provider_clients._http.post", _fake_post({
            "id": "anthropic-response-id", "content": [{"type": "text", "text": "fixture output"}], "stop_reason": "end_turn",
        }))
        request = build_provider_request(provider="anthropic", model="test-model", messages=[{"role": "user", "content": "Hello"}])
        response = AnthropicHTTPProviderClient(api_key="test-key").complete(request)
        assert response.metadata["usage"] is None
        assert response.metadata["usage_measured"] is False


if __name__ == "__main__":
    unittest.main()
