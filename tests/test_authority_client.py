from llm_adapter import FixtureAuthorityClient, evaluate_commitment_request, run_governed_session


def test_read_only_session_authority_decision_not_required():
    session = run_governed_session(
        provider="fixture-provider",
        model="fixture-model",
        messages=[{"role": "user", "content": "Explain current state."}],
        candidate_output="Current state can be explained as read-only output.",
        purpose="answer",
        allowed_sources=("receipt_index",),
        policy={"policy": "read-only"},
        delegation={"adapter": "read"},
    ).to_dict()

    assert session["authority_decision"]["decision"] == "NOT_REQUIRED"


def test_action_session_fails_closed_by_default():
    session = run_governed_session(
        provider="fixture-provider",
        model="fixture-model",
        messages=[{"role": "user", "content": "Commit this governed adapter change."}],
        candidate_output="Prepared a patch candidate. Do not commit until authority passes.",
        purpose="execute",
        allowed_sources=("repo_write",),
        policy={"policy": "commit-gated"},
        delegation={"adapter": "read"},
        action_target="repo://StegVerse-org/LLM-adapter",
    ).to_dict()

    assert session["commitment_request"]["status"] == "requires_downstream_commit_time_standing"
    assert session["authority_decision"]["decision"] == "FAIL_CLOSED"
    assert session["authority_decision"]["authority_decision_hash"]


def test_fixture_authority_can_allow_without_executing():
    authority = FixtureAuthorityClient(
        decision="ALLOW",
        reason="fixture standing satisfied for test only",
        policy_hash="policy-ok",
        delegation_hash="delegation-ok",
    )
    session = run_governed_session(
        provider="fixture-provider",
        model="fixture-model",
        messages=[{"role": "user", "content": "Commit this governed adapter change."}],
        candidate_output="Prepared a patch candidate. Do not commit until authority passes.",
        purpose="execute",
        allowed_sources=("repo_write",),
        policy={"policy": "commit-gated"},
        delegation={"adapter": "read"},
        action_target="repo://StegVerse-org/LLM-adapter",
        authority_client=authority,
    ).to_dict()

    assert session["authority_decision"]["decision"] == "ALLOW"
    assert session["authority_decision"]["policy_hash"] == "policy-ok"
    assert session["action_route"]["route_status"] == "route_to_commit_time_authority"


def test_malformed_commitment_request_fails_closed():
    decision = evaluate_commitment_request({"status": "unknown", "commitment_request_hash": "bad"})

    assert decision["decision"] == "FAIL_CLOSED"
