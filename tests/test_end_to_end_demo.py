from __future__ import annotations
import json, subprocess, sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, *args], cwd=ROOT, text=True, capture_output=True, check=True)


class EndToEndDemoTests(unittest.TestCase):
    def test_simple_query_allows(self) -> None:
        run("scripts/run_end_to_end_demo.py", "--fixture", "examples/end_to_end/simple_query.json")
        packet = json.loads((ROOT / "reports/simple_query.session.json").read_text(encoding="utf-8"))["session_packet"]
        assert packet["authority_decision"] == "ALLOW"
        assert packet["action"] == "NONE"
        assert packet["execution_handoff"] is None

    def test_action_candidate_quarantines_without_execution(self) -> None:
        run("scripts/run_end_to_end_demo.py", "--fixture", "examples/end_to_end/action_commit_candidate.json")
        packet = json.loads((ROOT / "reports/action_commit_candidate.session.json").read_text(encoding="utf-8"))["session_packet"]
        assert packet["authority_decision"] == "QUARANTINE"
        assert packet["commitment_request"]["is_authority"] is False
        assert packet["execution_handoff"]["enabled"] is False

    def test_replay_and_reconstruction_pass(self) -> None:
        run("scripts/run_end_to_end_demo.py", "--fixture", "examples/end_to_end/simple_query.json")
        assert json.loads(run("scripts/replay_demo.py", "--session-report", "reports/simple_query.session.json").stdout)["replay_result"] == "PASS"
        assert json.loads(run("scripts/reconstruct_demo.py", "--session-report", "reports/simple_query.session.json").stdout)["reconstructed_decision"] == "QUARANTINE"


if __name__ == "__main__":
    unittest.main()
