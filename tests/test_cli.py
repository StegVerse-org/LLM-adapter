import json
from pathlib import Path

from llm_adapter.cli import main, run_session_fixture


def test_run_session_fixture_returns_full_governed_chain():
    fixture = {
        "provider_request": {
            "provider": "fixture-provider",
            "model": "fixture-model",
            "messages": [{"role": "user", "content": "Commit this governed adapter change."}],
            "purpose": "execute",
            "allowed_sources": ["repo_write"],
        },
        "candidate_output": "Prepared a patch candidate. Do not commit until authority passes.",
        "policy": {"policy": "commit-gated"},
        "delegation": {"adapter": "read"},
        "action_target": "repo://StegVerse-org/LLM-adapter",
    }

    result = run_session_fixture(fixture)

    assert result["adapter_result"]["decision"] == "QUARANTINE"
    assert result["authority_decision"]["decision"] == "FAIL_CLOSED"
    assert result["execution_handoff"]["status"] == "not_executable"


def test_cli_main_runs_fixture_file(tmp_path, capsys):
    fixture_path = tmp_path / "fixture.json"
    fixture_path.write_text(
        json.dumps(
            {
                "provider_request": {
                    "provider": "fixture-provider",
                    "model": "fixture-model",
                    "messages": [{"role": "user", "content": "Explain current state."}],
                    "purpose": "answer",
                    "allowed_sources": ["receipt_index"],
                },
                "candidate_output": "Current state can be explained as read-only output.",
                "policy": {"policy": "read-only"},
                "delegation": {"adapter": "read"},
            }
        ),
        encoding="utf-8",
    )

    exit_code = main([str(fixture_path)])
    captured = capsys.readouterr()
    result = json.loads(captured.out)

    assert exit_code == 0
    assert result["adapter_result"]["decision"] == "ALLOW"
    assert result["authority_decision"]["decision"] == "NOT_REQUIRED"
