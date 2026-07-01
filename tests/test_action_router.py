from llm_adapter import build_action_route_packet, run_governed_session


def test_action_router_skips_low_risk_read_only_output():
    packet = build_action_route_packet(
        query="Explain current state.",
        output="Current state is read-only.",
        adapter_result={"decision": "ALLOW", "admissibility_status": "allowed_read_only_candidate"},
        purpose="answer",
    ).to_dict()

    assert packet["route_status"] == "no_action_route_required"
    assert packet["action_candidates"] == []


def test_action_router_builds_commit_candidate():
    packet = build_action_route_packet(
        query="Commit this change.",
        output="Prepared candidate patch for commit.",
        adapter_result={"decision": "QUARANTINE", "admissibility_status": "requires_commit_time_authority"},
        purpose="execute",
        target="repo://StegVerse-org/LLM-adapter",
    ).to_dict()

    assert packet["route_status"] == "route_to_commit_time_authority"
    assert packet["action_candidates"][0]["action_type"] == "execute"
    assert packet["action_candidate_hashes"][0]


def test_governed_session_includes_action_route_for_commit_request():
    result = run_governed_session(
        provider="fixture-provider",
        model="fixture-model",
        messages=[{"role": "user", "content": "Commit this governed adapter change."}],
        candidate_output="Prepared a patch candidate. Do not commit until authority passes.",
        purpose="execute",
        allowed_sources=("repo_write",),
        evidence_fixtures=[],
        policy={"policy": "commit-gated"},
        delegation={"adapter": "read"},
        action_target="repo://StegVerse-org/LLM-adapter",
    ).to_dict()

    assert result["adapter_result"]["decision"] == "QUARANTINE"
    assert result["action_route"]["route_status"] == "route_to_commit_time_authority"
    assert result["action_route"]["action_candidates"][0]["target"] == "repo://StegVerse-org/LLM-adapter"
