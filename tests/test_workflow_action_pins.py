"""Every `uses:` in this repository's workflows is pinned to a commit (#368 M-P9).

A floating tag such as `@v4` lets the referenced action change under an unchanged
workflow. Each reference names a 40-hex commit; for actions/* the resolved tag is
kept as a trailing comment. Reads workflow text only.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_DIRS = (ROOT / ".github/workflows", ROOT / "iosnoperiod/github/workflows",
                 # G17 (StegVerse-org/.github#166): verbatim records of the folded workflows,
                 # whose run blocks tools/tasks/run_catalog.py verify pins to the executed steps.
                 ROOT / "tools/tasks/folded")
USES = re.compile(r"^\s*(?:- )?uses:\s*(\S+)(.*)$", re.M)
PINNED = re.compile(r"^[^@\s]+@[0-9a-f]{40}$")


class WorkflowActionPins(unittest.TestCase):
    def references(self):
        for directory in WORKFLOW_DIRS:
            for path in sorted(directory.glob("*.y*ml")):
                for match in USES.finditer(path.read_text(encoding="utf-8")):
                    yield path.name, match.group(1), match.group(2)

    def test_every_uses_reference_is_a_full_commit_sha(self):
        refs = list(self.references())
        self.assertTrue(refs, "the guard would be vacuous")
        for name, ref, _ in refs:
            with self.subTest(workflow=name, uses=ref):
                self.assertRegex(ref, PINNED)

    def test_pinned_actions_record_the_resolved_tag(self):
        for name, ref, trailer in self.references():
            if ref.startswith("actions/"):
                with self.subTest(workflow=name, uses=ref):
                    self.assertRegex(trailer, r"^\s+# v\d+")


if __name__ == "__main__":
    unittest.main()
