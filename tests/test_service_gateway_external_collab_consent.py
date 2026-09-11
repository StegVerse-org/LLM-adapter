from __future__ import annotations

from types import SimpleNamespace

import requests
from fastapi.testclient import TestClient

from llm_adapter import runtime_gateway
from llm_adapter import service_gateway_external_collab_consent as consent_routes


def _response(*, status_code=200, content=b"{}", headers=None):
    return SimpleNamespace(
        status_code=status_code,
        content=content,
        headers=requests.structures.CaseInsensitiveDict(headers or {"content-type": "application/json"}),
    )


def test_begin_forbids_query_without_contacting_listener(monkeypatch):
    def unexpected(*args, **kwargs):
        raise AssertionError("upstream must not be called")

    monkeypatch.setattr(consent_routes.requests, "get", unexpected)
    response = TestClient(runtime_gateway.app).get(
        "/tvc/external-collaboration/google-drive/consent/begin?unexpected=1"
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "query_string_forbidden"


def test_health_forbids_query_without_contacting_listener(monkeypatch):
    def unexpected(*args, **kwargs):
        raise AssertionError("upstream must not be called")

    monkeypatch.setattr(consent_routes.requests, "get", unexpected)
    response = TestClient(runtime_gateway.app).get(
        "/tvc/external-collaboration/google-drive/consent/health?state=x"
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "query_string_forbidden"


def test_callback_preserves_exact_allowed_query_and_does_not_follow_redirect(monkeypatch):
    observed = {}

    def fake_get(url, *, allow_redirects, timeout):
        observed.update(url=url, allow_redirects=allow_redirects, timeout=timeout)
        return _response(
            status_code=302,
            content=b"",
            headers={
                "Location": "https://stegverse.org/workspace/complete",
                "Cache-Control": "no-store",
                "Set-Cookie": "must-not-cross-gateway=1",
                "X-Debug-Secret": "must-not-cross-gateway",
            },
        )

    monkeypatch.setattr(consent_routes.requests, "get", fake_get)
    client = TestClient(runtime_gateway.app, follow_redirects=False)
    raw_query = "state=extcollab.a%2Bb&code=abc%2F123&error_description="
    response = client.get(
        "/tvc/google-drive/external-collaboration/callback?" + raw_query
    )

    assert response.status_code == 302
    assert observed == {
        "url": "http://127.0.0.1:8786/tvc/google-drive/external-collaboration/callback?" + raw_query,
        "allow_redirects": False,
        "timeout": consent_routes.UPSTREAM_TIMEOUT_SECONDS,
    }
    assert response.headers["location"] == "https://stegverse.org/workspace/complete"
    assert response.headers["cache-control"] == "no-store"
    assert "set-cookie" not in response.headers
    assert "x-debug-secret" not in response.headers


def test_callback_rejects_uncontracted_query_key(monkeypatch):
    def unexpected(*args, **kwargs):
        raise AssertionError("upstream must not be called")

    monkeypatch.setattr(consent_routes.requests, "get", unexpected)
    response = TestClient(runtime_gateway.app).get(
        "/tvc/google-drive/external-collaboration/callback?state=s&code=c&token=forbidden"
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "callback_query_key_not_admitted"


def test_listener_unreachable_fails_closed(monkeypatch):
    def unavailable(*args, **kwargs):
        raise requests.ConnectionError("loopback unavailable")

    monkeypatch.setattr(consent_routes.requests, "get", unavailable)
    response = TestClient(runtime_gateway.app).get(
        "/tvc/external-collaboration/google-drive/consent/health"
    )
    assert response.status_code == 503
    assert response.json()["detail"] == "external_collaboration_listener_unreachable"


def test_begin_forwards_only_response_allowlist(monkeypatch):
    observed = {}

    def fake_get(url, *, allow_redirects, timeout):
        observed["url"] = url
        return _response(
            status_code=302,
            content=b"",
            headers={
                "Location": "https://accounts.google.com/o/oauth2/v2/auth?client_id=public-id",
                "Content-Type": "text/plain; charset=utf-8",
                "Pragma": "no-cache",
                "X-Upstream-Debug": "hidden",
            },
        )

    monkeypatch.setattr(consent_routes.requests, "get", fake_get)
    response = TestClient(runtime_gateway.app, follow_redirects=False).get(
        "/tvc/external-collaboration/google-drive/consent/begin"
    )
    assert response.status_code == 302
    assert observed["url"] == (
        "http://127.0.0.1:8786/tvc/external-collaboration/google-drive/consent/begin"
    )
    assert response.headers["location"].startswith("https://accounts.google.com/")
    assert response.headers["pragma"] == "no-cache"
    assert "x-upstream-debug" not in response.headers
