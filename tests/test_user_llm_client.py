from __future__ import annotations

import pytest

from llm_adapter.user_llm_access import UserLLMIdentity
from llm_adapter.user_llm_client import (
    UserLLMClient,
    UserLLMClientConfig,
    UserLLMClientError,
)


class FakeResponse:
    def __init__(self, payload, *, status_error: Exception | None = None):
        self.payload = payload
        self.status_error = status_error

    def raise_for_status(self):
        if self.status_error:
            raise self.status_error

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append(("GET", url, kwargs))
        return self.responses.pop(0)

    def post(self, url, **kwargs):
        self.calls.append(("POST", url, kwargs))
        return self.responses.pop(0)


def identity(*scopes: str) -> UserLLMIdentity:
    return UserLLMIdentity(
        user_id="user-001",
        llm_id="llm-001",
        provider="fixture-provider",
        model="fixture-model",
        scopes=tuple(scopes),
    )


def test_config_normalizes_base_url_and_rejects_invalid_values():
    config = UserLLMClientConfig("https://runtime.example/")
    assert config.base_url == "https://runtime.example"

    with pytest.raises(ValueError):
        UserLLMClientConfig("file:///tmp/runtime")
    with pytest.raises(ValueError):
        UserLLMClientConfig("https://runtime.example", timeout_seconds=0)


def test_capabilities_uses_bearer_token_and_returns_tuple():
    session = FakeSession([
        FakeResponse({"capabilities": [{"capability_id": "demo_test_suite"}]})
    ])
    client = UserLLMClient(
        UserLLMClientConfig("https://runtime.example", bearer_token="secret", timeout_seconds=3),
        identity("demo:read"),
        session=session,
    )

    result = client.capabilities()
    assert result[0]["capability_id"] == "demo_test_suite"
    method, url, kwargs = session.calls[0]
    assert method == "GET"
    assert url == "https://runtime.example/v1/user-llm/capabilities"
    assert kwargs["headers"]["Authorization"] == "Bearer secret"
    assert kwargs["timeout"] == 3


def test_demo_and_entity_helpers_build_stable_request_shape():
    session = FakeSession([
        FakeResponse({"status": "RETURNED", "authority_attached": False}),
        FakeResponse({"status": "DEFER", "authority_attached": False}),
    ])
    client = UserLLMClient(
        UserLLMClientConfig("https://runtime.example"),
        identity("demo:submit", "sandbox:submit"),
        session=session,
    )

    client.submit_demo("submit", {"test_id": "TA-14"})
    client.submit_entity("submit", {"bundle_id": "bundle-001"})

    first = session.calls[0][2]["json"]
    second = session.calls[1][2]["json"]
    assert first["route"] == "demo_test_suite"
    assert first["identity"]["scopes"] == ["demo:submit", "sandbox:submit"]
    assert second["route"] == "entity_sandbox_runner"
    assert second["payload"]["bundle_id"] == "bundle-001"


def test_hil_helper_submits_metadata_without_publication_authority():
    session = FakeSession([
        FakeResponse({"status": "RETURNED", "authority_attached": False})
    ])
    client = UserLLMClient(
        UserLLMClientConfig("https://runtime.example"),
        identity("hil:submit"),
        session=session,
    )

    client.submit_hil(
        filename="response.pdf",
        sha256_hex="A" * 64,
        size_bytes=42,
        trace_id="trace-001",
        participant_review_status="reviewed",
    )

    body = session.calls[0][2]["json"]
    assert body["route"] == "hil_response_packet"
    assert body["action"] == "submit_pdf_metadata"
    assert body["payload"]["sha256"] == "a" * 64


def test_client_fails_closed_on_authority_or_malformed_response():
    authority_session = FakeSession([
        FakeResponse({"status": "RETURNED", "authority_attached": True})
    ])
    client = UserLLMClient(
        UserLLMClientConfig("https://runtime.example"),
        identity("demo:read"),
        session=authority_session,
    )
    with pytest.raises(UserLLMClientError, match="non-authority invariant"):
        client.submit_demo("inspect", {})

    malformed_session = FakeSession([FakeResponse(["not", "an", "object"])])
    malformed = UserLLMClient(
        UserLLMClientConfig("https://runtime.example"),
        identity("demo:read"),
        session=malformed_session,
    )
    with pytest.raises(UserLLMClientError, match="non-object"):
        malformed.submit_demo("inspect", {})


def test_transport_errors_are_wrapped():
    session = FakeSession([FakeResponse({}, status_error=RuntimeError("offline"))])
    client = UserLLMClient(
        UserLLMClientConfig("https://runtime.example"),
        identity("demo:read"),
        session=session,
    )
    with pytest.raises(UserLLMClientError, match="runtime request failed"):
        client.capabilities()
