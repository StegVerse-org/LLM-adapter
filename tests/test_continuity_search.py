from llm_adapter import FixtureContinuitySearch, GovernedLLMAdapter


def test_fixture_continuity_search_returns_stale_status_and_evidence():
    search = FixtureContinuitySearch(
        [
            {
                "source_type": "receipt",
                "pointer": "master-records://fixture/prior-answer",
                "payload": {"standing": "historical_only"},
                "freshness": "stale",
                "retrieved_at": "2026-07-01T00:00:00+00:00",
                "notes": "prior answer",
            }
        ]
    )

    result = search.search("prior answer")

    assert result.freshness_status == "stale"
    assert len(result.evidence) == 1
    assert result.evidence[0].freshness == "stale"


def test_continuity_search_evidence_quarantines_adapter_result():
    search = FixtureContinuitySearch(
        [
            {
                "source_type": "receipt",
                "pointer": "master-records://fixture/prior-answer",
                "payload": {"standing": "historical_only"},
                "freshness": "stale",
                "retrieved_at": "2026-07-01T00:00:00+00:00",
                "notes": "prior answer",
            }
        ]
    )
    continuity = search.search("prior answer")
    adapter = GovernedLLMAdapter(default_provider="fixture", default_model="fixture")

    result = adapter.govern_response(
        query="Can the prior answer be reused?",
        candidate_output="The prior answer is reconstructable but requires fresh retrieval.",
        allowed_sources=("receipt_index",),
        evidence=continuity.evidence,
        policy={"policy": "freshness-required"},
        delegation={"adapter": "read"},
    )

    assert result.decision == "QUARANTINE"
    assert result.admissibility_status == "requires_fresh_retrieval"
