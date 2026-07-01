from llm_adapter import FixtureAuthorityClient, prepare_execution_handoff, run_governed_session


def test_default_execution_handoff_is_not_executable_for_fail_closed():
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

    assert session["authority_decision"]["decision"] == "FAIL_CLOSED"
    assert session["execution_handoff"]["status"] == "not_executable"
    assert session["execution_handoff"]["execution_handoff_hash"]


def test_allowed_authority_creates_external_executor_handoff_without_execution():
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
    assert session["execution_handoff"]["status"] == "ready_for_external_executor"
    assert session["execution_handoff"]["target"] == "repo://StegVerse-org/LLM-adapter"


def test_prepare_execution_handoff_without_allow_is_not_executable():
    handoff = prepare_execution_handoff(
        commitment_request={"commitment_request_hash": "request", "target": "repo://example"},
        authority_decision={"decision": "DENY", "authority_decision_hash": "decision"},
    )

    assert handoff["status"] == "not_executable"
