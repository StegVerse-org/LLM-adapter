import json
from urllib.error import URLError

import pytest

from llm_adapter.user_llm_http_transport import (
    HTTPRouteConfig,
    TransportError,
    build_http_route_transports,
    configured_route_status,
    make_http_transport,
)


def test_empty_config_keeps_all_routes_unconfigured():
    config = HTTPRouteConfig()
    transports = build_http_route_transports(config)
    assert transports.demo_test_suite is None
    assert transports.entity_sandbox_runner is None
    assert transports.hil_response_packet is None
    assert configured_route_status(config) == {
        "demo_test_suite": False,
        "entity_sandbox_runner": False,
        "hil_response_packet": False,
    }


def test_configured_routes_create_only_requested_transports():
    config = HTTPRouteConfig(
        demo_test_suite_url="https://demo.example.test/v1/submit",
        hil_response_packet_url="https://hil.example.test/v1/packets",
    )
    transports = build_http_route_transports(config)
    assert callable(transports.demo_test_suite)
    assert transports.entity_sandbox_runner is None
    assert callable(transports.hil_response_packet)


def test_invalid_scheme_fails_closed():
    with pytest.raises(TransportError):
        make_http_transport("file:///tmp/unsafe")


def test_invalid_environment_timeout_fails_closed(monkeypatch):
    monkeypatch.setenv("STEGVERSE_USER_LLM_HTTP_TIMEOUT_SECONDS", "not-a-number")
    with pytest.raises(TransportError):
        HTTPRouteConfig.from_environment()


def test_transport_posts_json_and_returns_object(monkeypatch):
    captured = {}

    class Response:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps({"status": "accepted", "receipt_id": "r-1"}).encode()

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["method"] = request.get_method()
        captured["authorization"] = request.headers.get("Authorization")
        captured["body"] = json.loads(request.data.decode())
        captured["timeout"] = timeout
        return Response()

    monkeypatch.setattr("llm_adapter.user_llm_http_transport.urlopen", fake_urlopen)
    transport = make_http_transport(
        "https://demo.example.test/v1/submit",
        bearer_token="token-1",
        timeout_seconds=7,
    )
    result = transport({"request_hash": "abc", "route": "demo_test_suite"})
    assert result["status"] == "accepted"
    assert captured == {
        "url": "https://demo.example.test/v1/submit",
        "method": "POST",
        "authorization": "Bearer token-1",
        "body": {"request_hash": "abc", "route": "demo_test_suite"},
        "timeout": 7,
    }


def test_transport_network_failure_is_not_misreported_as_success(monkeypatch):
    def fake_urlopen(request, timeout):
        raise URLError("offline")

    monkeypatch.setattr("llm_adapter.user_llm_http_transport.urlopen", fake_urlopen)
    transport = make_http_transport("https://demo.example.test/v1/submit")
    with pytest.raises(TransportError, match="unavailable"):
        transport({"route": "demo_test_suite"})


def test_transport_rejects_non_object_json(monkeypatch):
    class Response:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return b"[]"

    monkeypatch.setattr(
        "llm_adapter.user_llm_http_transport.urlopen",
        lambda request, timeout: Response(),
    )
    transport = make_http_transport("https://demo.example.test/v1/submit")
    with pytest.raises(TransportError, match="JSON object"):
        transport({"route": "demo_test_suite"})
