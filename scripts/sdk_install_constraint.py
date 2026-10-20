#!/usr/bin/env python3
"""Materialize the StegVerse SDK install constraint for the commit this project pins.

`pip install -e .` installs the SDK named in pyproject.toml at a fixed commit. This
reads that commit, takes ``constraints/sdk-install.txt`` from the SDK archive of the
same commit, writes it under ``--dest`` and prints its path, so a workflow step can
``export PIP_CONSTRAINT`` before installing. pip applies the constraint inside the
isolated build environment too, so the setuptools/wheel build backend is pinned.

Standard library only. On any failure prints a six-field FAIL_CLOSED record to stderr
and exits 1; nothing is installed or retried.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PIN = re.compile(r'"stegverse-sdk @ git\+https://github\.com/StegVerse-org/StegVerse-SDK\.git@([0-9a-f]{40})"')
ARCHIVE_URL = "https://github.com/StegVerse-org/StegVerse-SDK/archive/{sha}.tar.gz"
MEMBER = "constraints/sdk-install.txt"


class FailClosed(Exception):
    def __init__(self, failure_code: str, failed_predicate: str, repair: str):
        super().__init__(failure_code)
        self.record = {
            "disposition": "FAIL_CLOSED",
            "failure_code": failure_code,
            "failed_predicate": failed_predicate,
            "required_evidence_or_repair": repair,
            "retry_entrypoint": "scripts/sdk_install_constraint.py",
            "owning_existing_goal": "LLMA-DECLARED-PATH-CONFORMANCE-368",
            "next_attempt": "re-run the install step once the repair holds",
        }


def pinned_sha(pyproject: Path) -> str:
    found = PIN.findall(pyproject.read_text(encoding="utf-8"))
    if len(found) != 1:
        raise FailClosed("SDK_PIN_NOT_UNIQUE", "PYPROJECT_PINS_EXACTLY_ONE_SDK_COMMIT",
                         "pyproject.toml names the SDK once as git+...StegVerse-SDK.git@<40 hex>")
    return found[0]


def constraint_bytes(archive: bytes, sha: str) -> bytes:
    expected = f"StegVerse-SDK-{sha}/{MEMBER}"
    try:
        with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as tar:
            member = tar.getmember(expected)
            handle = tar.extractfile(member) if member.isfile() else None
            if handle is None:
                raise KeyError(expected)
            return handle.read()
    except (KeyError, tarfile.TarError, OSError) as exc:
        raise FailClosed("SDK_INSTALL_CONSTRAINT_ABSENT_AT_PINNED_COMMIT",
                         "PINNED_SDK_ARCHIVE_CARRIES_CONSTRAINTS_SDK_INSTALL_TXT",
                         f"pin an SDK commit whose archive carries {MEMBER} ({type(exc).__name__})") from exc


def fetch(sha: str) -> bytes:
    try:
        with urllib.request.urlopen(ARCHIVE_URL.format(sha=sha), timeout=120) as response:
            return response.read()
    except OSError as exc:
        raise FailClosed("SDK_ARCHIVE_NOT_RETRIEVED", "PINNED_SDK_ARCHIVE_RETRIEVED",
                         f"the SDK archive at {sha} is reachable from the step ({type(exc).__name__})") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--pyproject", type=Path, default=ROOT / "pyproject.toml")
    parser.add_argument("--archive", type=Path, help="read a local SDK archive instead of fetching it")
    parser.add_argument("--dest", type=Path, default=Path(os.environ.get("RUNNER_TEMP") or tempfile.gettempdir()))
    args = parser.parse_args(argv)
    try:
        sha = pinned_sha(args.pyproject)
        data = constraint_bytes(args.archive.read_bytes() if args.archive else fetch(sha), sha)
    except FailClosed as exc:
        print(json.dumps(exc.record, sort_keys=True), file=sys.stderr)
        return 1
    out = args.dest / f"stegverse-sdk-{sha}" / MEMBER
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data)
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
