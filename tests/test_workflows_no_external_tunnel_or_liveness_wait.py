"""Workflows neither fetch a third-party tunnel nor wait on a destination (LLMA-368).

Task Registry global invariants: external_machine_awaiting_allowed=false and
destination_liveness_is_transition_predicate=false. The retired HIL ephemeral
cycle downloaded an unpinned Cloudflare quick-tunnel binary and polled public
readiness before accepting work, and capability-runtime installed uv to download
a Python interpreter; nothing in CI may reintroduce any of them.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

WORKFLOWS = Path(__file__).resolve().parents[1] / ".github" / "workflows"
FORBIDDEN = (
    re.compile(r"cloudflared", re.IGNORECASE),
    re.compile(r"trycloudflare\.com", re.IGNORECASE),
    re.compile(r"releases/latest/download"),
    re.compile(r"pip install[^\n]*\buv\b"),
    re.compile(r"\buv python install\b"),
)


class WorkflowExternalDependencyTests(unittest.TestCase):
    def test_no_workflow_fetches_a_tunnel_an_unpinned_release_or_an_interpreter(self) -> None:
        offenders = [
            f"{path.name}: {pattern.pattern}"
            for path in sorted(WORKFLOWS.glob("*.y*ml"))
            for pattern in FORBIDDEN
            if pattern.search(path.read_text(encoding="utf-8"))
        ]
        self.assertEqual(offenders, [])

    def test_retired_ephemeral_tunnel_cycle_stays_retired(self) -> None:
        root = WORKFLOWS.parents[1]
        for relative in (
            ".github/workflows/hil-triggered-ephemeral-cycle.yml",
            ".github/workflows/hil-ephemeral-controlled-probe.yml",
            "control/hil-ephemeral-trigger.json",
            "control/hil-ephemeral-probe.json",
        ):
            self.assertFalse((root / relative).exists(), relative)


if __name__ == "__main__":
    unittest.main()
