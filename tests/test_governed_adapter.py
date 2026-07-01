from llm_adapter import GovernedLLMAdapter


def test_read_only_candidate_is_allowed():
    adapter = GovernedLLMAdapter(default_provider="test", default_model="model")

    result = adapter.govern_response(
        query="What does a governed LLM do?",
        candidate_output="It produces a receipt-bound candidate response.",
        allowed_sources=("model_knowledge",),
        policy={"policy": "read-only"},
        delegation={"adapter": "read"},
    )

    assert result.decision == "ALLOW"
    assert result.response_receipt["decision"] == "ALLOW"
    assert result.reconstruction["reconstruction_status"] == "reconstructable"


def test_action_candidate_is_quarantined_until_commit_time_authority():
    adapter = GovernedLLMAdapter(default_provider="test", default_model="model")

    result = adapter.govern_response(
        query="Commit this change to the repo.",
        candidate_output="Prepared commit instructions.",
        allowed_sources=("repo_write",),
        policy={"policy": "commit-gated"},
        delegation={"adapter": "read"},
    )

    assert result.decision == "QUARANTINE"
    assert result.admissibility_status == "requires_commit_time_authority"
