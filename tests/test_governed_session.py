from llm_adapter import run_governed_session


def test_governed_session_allows_current_read_only_evidence():
    result = run_governed_session(
        provider="fixture-provider",
        model="fixture-model",
        messages=[{"role": "user", "content": "Explain current state."}],
        candidate_output="Current evidence supports a read-only explanation.",
        allowed_sources=("receipt_index",),
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

    assert result["provider_request_hash"]
    assert result["continuity"]["freshness_status"] == "current"
    assert result["adapter_result"]["decision"] == "ALLOW"


def test_governed_session_quarantines_stale_evidence():
    result = run_governed_session(
        provider="fixture-provider",
        model="fixture-model",
        messages=[{"role": "user", "content": "Can the prior answer be reused?"}],
        candidate_output="The prior answer is reconstructable but cannot be reused as current authority.",
        allowed_sources=("receipt_index",),
        evidence_fixtures=[
            {
                "source_type": "receipt",
                "pointer": "master-records://fixture/prior-answer",
                "payload": {"standing": "historical_only"},
                "freshness": "stale",
                "retrieved_at": "2026-07-01T00:00:00+00:00",
                "notes": "prior answer",
            }
        ],
        policy={"policy": "freshness-required"},
        delegation={"adapter": "read"},
    ).to_dict()

    assert result["continuity"]["freshness_status"] == "stale"
    assert result["adapter_result"]["decision"] == "QUARANTINE"
    assert result["adapter_result"]["admissibility_status"] == "requires_fresh_retrieval"
