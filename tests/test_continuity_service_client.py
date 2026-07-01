import pytest

from llm_adapter import (
    ContinuityServiceClient,
    ContinuityServiceConfigurationError,
    FixtureProviderClient,
    build_provider_request,
    continuity_result_from_service_body,
    run_governed_request_session,
)


def test_continuity_service_fails_closed_without_endpoint(monkeypatch):
    monkeypatch.delenv("STEGVERSE_CONTINUITY_SEARCH_URL", raising=False)

    with pytest.raises(ContinuityServiceConfigurationError):
        ContinuityServiceClient().search("prior answer")


def test_continuity_service_body_converts_to_result():
    result = continuity_result_from_service_body(
        query="prior answer",
        body={
            "freshness_status": "stale",
            "evidence": [
                {
                    "source_type": "receipt",
                    "pointer": "master-records://service/prior-answer",
                    "content_hash": "abc123",
                    "retrieved_at": "2026-07-01T00:00:00+00:00",
                    "freshness": "stale",
                    "notes": "service result",
                }
            ],
            "reconstruction_notes": ["service-backed continuity result"],
        },
    )

    assert result.freshness_status == "stale"
    assert result.evidence[0].content_hash == "abc123"
    assert result.reconstruction_notes == ("service-backed continuity result",)


def test_continuity_service_response_can_drive_governed_session():
    continuity = continuity_result_from_service_body(
        query="prior answer",
        body={
            "freshness_status": "stale",
            "evidence": [
                {
                    "source_type": "receipt",
                    "pointer": "master-records://service/prior-answer",
                    "content_hash": "abc123",
                    "retrieved_at": "2026-07-01T00:00:00+00:00",
                    "freshness": "stale",
                    "notes": "service result",
                }
            ],
            "reconstruction_notes": ["service-backed continuity result"],
        },
    )

    class StaticContinuityClient:
        def search(self, query):
            return continuity

    request = build_provider_request(
        provider="fixture-provider",
        model="fixture-model",
        messages=[{"role": "user", "content": "Can the prior answer be reused?"}],
        allowed_sources=("receipt_index",),
    )

    session = run_governed_request_session(
        request=request,
        provider_client=FixtureProviderClient(
            output="The prior answer is reconstructable but requires fresh retrieval."
        ),
        continuity_client=StaticContinuityClient(),
        policy={"policy": "freshness-required"},
        delegation={"adapter": "read"},
    ).to_dict()

    assert session["continuity"]["freshness_status"] == "stale"
    assert session["adapter_result"]["decision"] == "QUARANTINE"
    assert session["adapter_result"]["admissibility_status"] == "requires_fresh_retrieval"
