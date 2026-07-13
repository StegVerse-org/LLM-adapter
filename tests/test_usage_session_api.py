from __future__ import annotations

import importlib
import os
import tempfile

from fastapi import FastAPI
from fastapi.testclient import TestClient

from llm_adapter.provider_usage import ProviderMetric, build_provider_usage_event


def client_for(temp: str) -> TestClient:
    os.environ["STEGVERSE_USAGE_SESSION_DB"] = os.path.join(temp, "usage.db")
    os.environ["STEGVERSE_USAGE_SUBMIT_TOKEN"] = "submit-token"
    import llm_adapter.usage_session_api as module
    module = importlib.reload(module)
    app = FastAPI()
    app.include_router(module.router)
    return TestClient(app)


def event(session_id: str = "session-1", measurement_id: str = "measurement-1") -> dict:
    return build_provider_usage_event(
        measurement_id=measurement_id,
        session_id=session_id,
        transition_id="transition-1",
        origin_entry_point="ecosystem_chat",
        interaction_type="provider_generation",
        provider="fixture-provider",
        model="fixture-model",
        metrics={
            "model_calls": ProviderMetric(value="1", unit="calls", evidence_class="CONFIGURED")
        },
        receipt_refs=["provider-receipt:fixture"],
        timestamp="2026-07-13T00:00:00Z",
    )


def submission(item: dict) -> dict:
    return {
        "schema_version": "1.0.0",
        "submission_type": "usage_session_event_batch",
        "session_id": item["session_id"],
        "events": [item],
    }


def test_submit_and_same_origin_header_retrieve() -> None:
    with tempfile.TemporaryDirectory() as temp:
        client = client_for(temp)
        item = event()
        created = client.post(
            "/api/usage/sessions",
            json=submission(item),
            headers={"Authorization": "Bearer submit-token"},
        )
        assert created.status_code == 200
        assert created.json()["inserted_events"] == 1

        retrieved = client.get(
            "/api/usage/sessions/session-1",
            headers={"X-SteGVerse-Session": "session-1"},
        )
        assert retrieved.status_code == 200
        body = retrieved.json()
        assert body["schema"] == "stegverse.usage.session.v1"
        assert body["source_class"] == "LIVE_USAGE_API"
        assert body["session_id"] == "session-1"
        assert len(body["events"]) == 1
        assert body["retrieval_receipt"]["authority_granted"] is False
        assert body["retrieval_receipt"]["custody_recorded"] is False


def test_same_origin_cookie_retrieve() -> None:
    with tempfile.TemporaryDirectory() as temp:
        client = client_for(temp)
        item = event()
        client.post(
            "/api/usage/sessions",
            json=submission(item),
            headers={"Authorization": "Bearer submit-token"},
        )
        client.cookies.set("stegverse_session_id", "session-1")
        response = client.get("/api/usage/sessions/session-1")
        assert response.status_code == 200


def test_retrieval_without_matching_session_fails_closed() -> None:
    with tempfile.TemporaryDirectory() as temp:
        client = client_for(temp)
        item = event()
        client.post(
            "/api/usage/sessions",
            json=submission(item),
            headers={"Authorization": "Bearer submit-token"},
        )
        response = client.get(
            "/api/usage/sessions/session-1",
            headers={"X-SteGVerse-Session": "different-session"},
        )
        assert response.status_code == 401


def test_submission_requires_machine_authentication() -> None:
    with tempfile.TemporaryDirectory() as temp:
        client = client_for(temp)
        response = client.post("/api/usage/sessions", json=submission(event()))
        assert response.status_code == 401


def test_measurement_identity_conflict_fails_closed() -> None:
    with tempfile.TemporaryDirectory() as temp:
        client = client_for(temp)
        first = event()
        assert client.post(
            "/api/usage/sessions",
            json=submission(first),
            headers={"Authorization": "Bearer submit-token"},
        ).status_code == 200
        changed = event()
        changed["transition_id"] = "changed-transition"
        changed.pop("event_sha256", None)
        response = client.post(
            "/api/usage/sessions",
            json=submission(changed),
            headers={"Authorization": "Bearer submit-token"},
        )
        assert response.status_code == 409


def test_unavailable_metric_with_value_fails_closed() -> None:
    with tempfile.TemporaryDirectory() as temp:
        client = client_for(temp)
        item = event()
        item["metrics"]["model_calls"] = {
            "value": "1",
            "unit": "calls",
            "evidence_class": "UNAVAILABLE",
            "source_ref": None,
        }
        item.pop("event_sha256", None)
        response = client.post(
            "/api/usage/sessions",
            json=submission(item),
            headers={"Authorization": "Bearer submit-token"},
        )
        assert response.status_code == 422
