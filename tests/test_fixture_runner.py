import unittest
from pathlib import Path

from llm_adapter.fixture_runner import run_fixture_file


class FixtureRunnerTests(unittest.TestCase):
    def test_fixture_runner_quarantines_stale_fixture(self):
        fixture_path = Path(__file__).resolve().parents[1] / "fixtures" / "governed_response_fixture.json"

        result = run_fixture_file(fixture_path)

        assert result["decision"] == "QUARANTINE"
        assert result["admissibility_status"] == "requires_fresh_retrieval"
        assert result["provider_request_hash"]
        assert result["reconstruction"]["decision"] == "QUARANTINE"


if __name__ == "__main__":
    unittest.main()
