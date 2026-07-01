from llm_adapter import (
    GovernedLLMAdapter,
    build_provider_request,
    evidence_from_fixture,
    evidence_from_payload,
)


def test_provider_request_is_hashable_and_extracts_user_query():
    request = build_provider_request(
        provider="fixture-provider",
        model="fixture-model",
        messages=[
            {"role": "system", "content": "Answer only from admitted evidence."},
            {"role": "user", "content": "What changed since the last response?"},
        ],
        allowed_sources=("receipt_index",),
        metadata={"route": "governed-fixture"},
    )

    assert request.request_hash
    assert request.user_query == "What changed since the last response?"
    assert request.to_dict()["provider"] == "fixture-provider"


def test_evidence_fixture_can_quarantine_stale_answer():
    evidence = evidence_from_fixture(
        {
            "source_type": "receipt",
            "pointer": "master-records://example/old-answer",
            "payload": {"answer": "prior state"},
            "freshness": "stale",
            "retrieved_at": "2026-07-01T00:00:00+00:00",
        }
    )
    adapter = GovernedLLMAdapter(default_provider="fixture-provider", default_model="fixture-model")

    result = adapter.govern_response(
        query="Can we reuse the prior answer?",
        candidate_output="The prior answer is reconstructable but cannot be reused as current authority.",
        allowed_sources=("receipt_index",),
        evidence=(evidence,),
        policy={"policy": "freshness-required"},
        delegation={"adapter": "read"},
    )

    assert result.decision == "QUARANTINE"
    assert result.admissibility_status == "requires_fresh_retrieval"


def test_payload_evidence_allows_current_read_only_answer():
    evidence = evidence_from_payload(
        source_type="fixture",
        pointer="fixture://current/context",
        payload={"state": "current"},
    )
    adapter = GovernedLLMAdapter(default_provider="fixture-provider", default_model="fixture-model")

    result = adapter.govern_response(
        query="Explain current governed LLM state.",
        candidate_output="The current fixture evidence supports a read-only explanation.",
        allowed_sources=("fixture",),
        evidence=(evidence,),
        policy={"policy": "read-only"},
        delegation={"adapter": "read"},
    )

    assert result.decision == "ALLOW"
    assert result.reconstruction["evidence_hashes"] == [evidence.content_hash]
