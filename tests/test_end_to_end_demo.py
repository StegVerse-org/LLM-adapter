from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def run_script(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=True,
    )


def test_simple_query_demo_allows_and_writes_report() -> None:
    run_script("scripts/run_end_to_end_demo.py", "--fixture", "examples/end_to_end/simple_query.json")
    report_path = REPO_ROOT / "reports" / "simple_query.session.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    packet = report["session_packet"]
    assert packet["authority_decision"] == "ALLOW"
    assert packet["action"] == "NONE"
    assert packet["execution_handoff"] is None
    assert report["receipt"]["provider_output_is_authority"] is False


def test_action_commit_candidate_quarantines_without_execution() -> None:
    run_script("scripts/run_end_to_end_demo.py", "--fixture", "examples/end_to_end/action_commit_candidate.json")
    report_path = REPO_ROOT / "reports" / "action_commit_candidate.session.json"
    packet = json.loads(report_path.read_text(encoding="utf-8"))["session_packet"]
    assert packet["authority_decision"] == "QUARANTINE"
    assert packet["commitment_request"]["is_authority"] is False
    assert packet["execution_handoff"]["enabled"] is False
    assert packet["execution_handoff"]["executes_side_effect"] is False


def test_replay_and_reconstruction_pass() -> None:
    run_script("scripts/run_end_to_end_demo.py", "--fixture", "examples/end_to_end/simple_query.json")
    replay = run_script("scripts/replay_demo.py", "--session-report", "reports/simple_query.session.json")
    replay_payload = json.loads(replay.stdout)
    assert replay_payload["replay_result"] == "PASS"
    recon = run_script("scripts/reconstruct_demo.py", "--session-report", "reports/simple_query.session.json")
    recon_payload = json.loads(recon.stdout)
    assert recon_payload["reconstruction_result"] == "PASS"
    assert recon_payload["reconstructed_decision"] == "QUARANTINE"
    assert recon_payload["side_effects_executed"] is False
