#!/usr/bin/env python3
"""Verify the adapter usage-session submission and retrieval contract."""
from __future__ import annotations

import importlib
import os
import tempfile

from fastapi import FastAPI
from fastapi.testclient import TestClient

from llm_adapter.provider_usage import ProviderMetric, build_provider_usage_event


def main() -> int:
    with tempfile.TemporaryDirectory() as temp:
        os.environ["STEGVERSE_USAGE_SESSION_DB"] = os.path.join(temp, "usage.db")
        os.environ["STEGVERSE_USAGE_SUBMIT_TOKEN"] = "verification-token"
        import llm_adapter.usage_session_api as module
        module = importlib.reload(module)
        app = FastAPI()
        app.include_router(module.router)
        client = TestClient(app)

        event = build_provider_usage_event(
            measurement_id="usage-api-verification-1",
            session_id="usage-api-session-1",
            transition_id="usage-api-transition-1",
            origin_entry_point="ecosystem_chat",
            interaction_type="provider_generation",
            provider="verification-provider",
            model="verification-model",
            metrics={
                "model_calls": ProviderMetric(
                    value="1", unit="calls", evidence_class="CONFIGURED"
                )
            },
            receipt_refs=["provider-receipt:verification"],
            timestamp="2026-07-13T00:00:00Z",
        )
        submission = {
            "schema_version": "1.0.0",
            "submission_type": "usage_session_event_batch",
            "session_id": event["session_id"],
            "events": [event],
        }
        created = client.post(
            "/api/usage/sessions",
            json=submission,
            headers={"Authorization": "Bearer verification-token"},
        )
        assert created.status_code == 200, created.text
        assert created.json()["custody_recorded"] is False

        unauthorized = client.get("/api/usage/sessions/usage-api-session-1")
        assert unauthorized.status_code == 401

        retrieved = client.get(
            "/api/usage/sessions/usage-api-session-1",
            headers={"X-SteGVerse-Session": "usage-api-session-1"},
        )
        assert retrieved.status_code == 200, retrieved.text
        body = retrieved.json()
        assert body["schema"] == "stegverse.usage.session.v1"
        assert body["source_class"] == "LIVE_USAGE_API"
        assert body["session_id"] == "usage-api-session-1"
        assert body["retrieval_receipt"]["authority_granted"] is False
        assert body["retrieval_receipt"]["custody_recorded"] is False
        assert len(body["events"]) == 1
        print("USAGE_SESSION_API_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
