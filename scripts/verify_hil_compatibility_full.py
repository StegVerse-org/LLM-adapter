#!/usr/bin/env python3
"""Run HIL compatibility checks without granting runtime or lifecycle authority."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]

COMMANDS: tuple[tuple[str, ...], ...] = (
    (sys.executable, "scripts/verify_hil_deployment_profile.py"),
    (sys.executable, "-m", "pytest", "tests/test_hil_storage_consistency.py", "-v"),
    (sys.executable, "-m", "pytest", "tests/test_hil_https_receiver_probe.py", "-v"),
    (sys.executable, "-m", "pytest", "-q", "tests/test_hil_intake_api.py", "tests/test_hil_provenance_chain.py", "tests/test_hil_publication_api.py", "tests/test_hil_controlled_cycle.py"),
    (sys.executable, "scripts/verify_hil_rtg_notification_contract.py"),
    (sys.executable, "-m", "pytest", "-q", "tests/test_hil_notification_delivery.py", "tests/test_hil_gateway_attempt_contract.py", "tests/test_hil_submission_status.py", "tests/test_hil_notification_schema.py", "tests/test_hil_submission_status_schema.py", "tests/test_hil_readiness_contract.py", "tests/test_hil_readiness_schema.py", "tests/test_hil_authority_evidence.py", "tests/test_hil_authority_evidence_schema.py"),
    (sys.executable, "-m", "pytest", "-q", "tests/test_service_gateway.py"),
)


def run(command: Sequence[str]) -> None:
    completed = subprocess.run(
        list(command),
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    print("$ " + " ".join(command))
    print(completed.stdout.rstrip())
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def verify_authority_boundary() -> None:
    handoff = (ROOT / "docs/HIL_LLM_ADAPTER_MIRROR_HANDOFF.md").read_text(encoding="utf-8")
    required = (
        "credential_authority: TV/TVC",
        "github_token_runtime_authority: NONE",
        "MERGED INTO: StegVerse-Labs/TVC/docs/HIL_TVC_MIRROR_HANDOFF.md",
    )
    missing = [marker for marker in required if marker not in handoff]
    if missing:
        raise SystemExit("HIL_COMPATIBILITY_AUTHORITY_FAIL:" + ",".join(missing))
    print("HIL_COMPATIBILITY_AUTHORITY=NONE")


def main() -> int:
    for command in COMMANDS:
        run(command)
    verify_authority_boundary()
    print("HIL_COMPATIBILITY_FULL_PASS")
    print("activation_effect=false private_review_authority=false publication_authority=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
