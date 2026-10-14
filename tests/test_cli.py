import collections
import io
import json
import shutil
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

from llm_adapter.cli import main, run_session_fixture


_Captured = collections.namedtuple("CaptureResult", "out err")


class CliTests(unittest.TestCase):
    def _tmp_path(self):
        """tmp_path equivalent: a fresh directory for this test, removed afterwards."""
        if getattr(self, "_tmp", None) is None:
            self._tmp = Path(tempfile.mkdtemp())
            self.addCleanup(shutil.rmtree, self._tmp, ignore_errors=True)
        return self._tmp

    def _capsys(self):
        """capsys equivalent: sys.stdout and sys.stderr are captured for the rest of the test."""
        streams = {"stdout": io.StringIO(), "stderr": io.StringIO()}
        for name, stream in streams.items():
            patcher = mock.patch.object(sys, name, stream)
            patcher.start()
            self.addCleanup(patcher.stop)

        def readouterr():
            captured = _Captured(streams["stdout"].getvalue(), streams["stderr"].getvalue())
            for stream in streams.values():
                stream.seek(0)
                stream.truncate()
            return captured

        return types.SimpleNamespace(readouterr=readouterr)

    def test_run_session_fixture_returns_full_governed_chain(self):
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

    def test_cli_main_runs_fixture_file(self):
        tmp_path = self._tmp_path()
        capsys = self._capsys()
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


if __name__ == "__main__":
    unittest.main()
