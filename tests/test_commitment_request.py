import unittest
from llm_adapter.commitment_request import build_commitment_request
from llm_adapter.governed_session import run_governed_session


class CommitmentRequestTests(unittest.TestCase):
    def test_read_only_session_needs_no_commitment_request(self):
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

        request = build_commitment_request(session_result=session)

        assert session["action_route"]["route_status"] == "no_action_route_required"
        assert request["status"] == "no_commitment_request_required"
        assert session["commitment_request"]["status"] == "no_commitment_request_required"

    def test_action_session_builds_commitment_request(self):
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

        request = session["commitment_request"]

        assert session["adapter_result"]["decision"] == "QUARANTINE"
        assert request["status"] == "requires_downstream_commit_time_standing"
        assert request["target"] == "repo://StegVerse-org/LLM-adapter"
        assert request["action_candidates"][0]["status"] == "requires_commit_time_authority"
        assert request["commitment_request_hash"]


if __name__ == "__main__":
    unittest.main()
