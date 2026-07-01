from pathlib import Path

from llm_adapter import run_fixture_file


def test_fixture_runner_quarantines_stale_fixture():
    fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "governed_response_fixture.json"

    result = run_fixture_file(fixture_path)

    assert result["decision"] == "QUARANTINE"
    assert result["admissibility_status"] == "requires_fresh_retrieval"
    assert result["provider_request_hash"]
    assert result["reconstruction"]["decision"] == "QUARANTINE"
