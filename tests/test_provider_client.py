import pytest

from llm_adapter import (
    FixtureProviderClient,
    ProviderResponse,
    build_provider_request,
    run_governed_request_session,
    run_governed_response_session,
)


def test_fixture_provider_response_binds_to_request_hash():
    request = build_provider_request(
        provider="fixture-provider",
        model="fixture-model",
        messages=[{"role": "user", "content": "Explain governed output."}],
    )
    provider = FixtureProviderClient(output="Governed output must still be checked.")

    response = provider.complete(request)

    assert response.request_hash == request.request_hash
    assert response.response_hash
    assert response.to_dict()["metadata"]["provider_mode"] == "fixture"


def test_governed_request_session_uses_provider_client_output():
    request = build_provider_request(
        provider="fixture-provider",
        model="fixture-model",
        messages=[{"role": "user", "content": "Explain current state."}],
        allowed_sources=("receipt_index",),
    )
    provider = FixtureProviderClient(output="Current state can be explained as read-only output.")

    result = run_governed_request_session(
        request=request,
        provider_client=provider,
        evidence_fixtures=[
            {
                "source_type": "receipt",
                "pointer": "master-records://fixture/current-state",
                "payload": {"standing": "current"},
                "freshness": "current",
                "retrieved_at": "2026-07-01T00:00:00+00:00",
                "notes": "current state",
            }
        ],
        policy={"policy": "read-only"},
        delegation={"adapter": "read"},
    ).to_dict()

    assert result["provider_response"]["request_hash"] == request.request_hash
    assert result["adapter_result"]["decision"] == "ALLOW"


def test_governed_response_session_rejects_mismatched_response_hash():
    request = build_provider_request(
        provider="fixture-provider",
        model="fixture-model",
        messages=[{"role": "user", "content": "Explain current state."}],
    )
    response = ProviderResponse(
        provider="fixture-provider",
        model="fixture-model",
        output="This response is mismatched.",
        request_hash="not-the-request-hash",
        metadata={"provider_mode": "fixture"},
    )

    with pytest.raises(ValueError):
        run_governed_response_session(request=request, provider_response=response)
