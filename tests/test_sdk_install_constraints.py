"""Every workflow install of this project pins the SDK's transitive set (#368 M-P8).

`pip install -e .` installs the SDK commit pinned in pyproject.toml. Each step that
runs it must first export PIP_CONSTRAINT to that commit's constraints/sdk-install.txt,
as materialized by scripts/sdk_install_constraint.py. Reads workflow text only.
"""
from __future__ import annotations

import io
import re
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import sdk_install_constraint as sic  # noqa: E402

WORKFLOW_DIRS = (ROOT / ".github/workflows", ROOT / "iosnoperiod/github/workflows")
STEP = re.compile(r"^\s*- (?:name|uses|run):", re.M)
INSTALL = re.compile(r"pip install\b")


def install_steps():
    for directory in WORKFLOW_DIRS:
        for path in sorted(directory.glob("*.y*ml")):
            text = path.read_text(encoding="utf-8")
            starts = [m.start() for m in STEP.finditer(text)] + [len(text)]
            for a, b in zip(starts, starts[1:]):
                step = text[a:b]
                if INSTALL.search(step):
                    yield path, step


def archive(sha: str, files: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as tar:
        for name, data in files.items():
            info = tarfile.TarInfo(f"StegVerse-SDK-{sha}/{name}")
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    return buffer.getvalue()


class WorkflowInstallsAreConstrained(unittest.TestCase):
    def test_every_install_step_exports_the_pinned_sdk_constraint_first(self):
        steps = list(install_steps())
        self.assertGreaterEqual(len(steps), 10, "the guard would be vacuous")
        for path, step in steps:
            with self.subTest(workflow=path.name):
                install = INSTALL.search(step).start()
                before = step[:install]
                self.assertIn("set -euo pipefail", before)
                self.assertRegex(before, r'constraint="\$\((?:"\$PYTHON_BIN"|python3) scripts/sdk_install_constraint\.py\)"')
                self.assertIn('export PIP_CONSTRAINT="$constraint"', before)
                self.assertEqual(len(INSTALL.findall(step)), 1)


class ConstraintMaterialization(unittest.TestCase):
    SHA = "a" * 40

    def test_pyproject_pins_exactly_one_sdk_commit(self):
        self.assertRegex(sic.pinned_sha(ROOT / "pyproject.toml"), r"^[0-9a-f]{40}$")

    def test_constraint_is_taken_from_the_archive_of_the_pinned_commit(self):
        data = archive(self.SHA, {"constraints/sdk-install.txt": b"wheel==0.48.0\n"})
        self.assertEqual(sic.constraint_bytes(data, self.SHA), b"wheel==0.48.0\n")

    def test_an_archive_of_another_commit_is_refused(self):
        data = archive("b" * 40, {"constraints/sdk-install.txt": b"wheel==0.48.0\n"})
        with self.assertRaises(sic.FailClosed) as caught:
            sic.constraint_bytes(data, self.SHA)
        self.assertEqual(caught.exception.record["failure_code"], "SDK_INSTALL_CONSTRAINT_ABSENT_AT_PINNED_COMMIT")

    def test_an_archive_without_the_constraint_is_refused_with_six_fields(self):
        data = archive(self.SHA, {"pyproject.toml": b""})
        with self.assertRaises(sic.FailClosed) as caught:
            sic.constraint_bytes(data, self.SHA)
        self.assertEqual(set(caught.exception.record) - {"disposition"}, {
            "failure_code", "failed_predicate", "required_evidence_or_repair",
            "retry_entrypoint", "owning_existing_goal", "next_attempt"})

    def test_cli_writes_the_constraint_and_prints_its_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            pyproject = tmp / "pyproject.toml"
            pyproject.write_text(
                f'dependencies = ["stegverse-sdk @ git+https://github.com/StegVerse-org/StegVerse-SDK.git@{self.SHA}"]\n')
            (tmp / "sdk.tar.gz").write_bytes(archive(self.SHA, {"constraints/sdk-install.txt": b"pip==25.2\n"}))
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts/sdk_install_constraint.py"), "--pyproject", str(pyproject),
                 "--archive", str(tmp / "sdk.tar.gz"), "--dest", str(tmp / "out")],
                capture_output=True, text=True, check=True)
            path = Path(result.stdout.strip())
            self.assertEqual(path, tmp / "out" / f"stegverse-sdk-{self.SHA}" / "constraints/sdk-install.txt")
            self.assertEqual(path.read_bytes(), b"pip==25.2\n")

    def test_cli_fails_closed_without_a_unique_pin(self):
        with tempfile.TemporaryDirectory() as tmp:
            pyproject = Path(tmp) / "pyproject.toml"
            pyproject.write_text("dependencies = []\n")
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts/sdk_install_constraint.py"), "--pyproject", str(pyproject)],
                capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn('"failure_code": "SDK_PIN_NOT_UNIQUE"', result.stderr)
            self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
