#!/usr/bin/env python3
"""Run the credential-free subset of the canonical Goal 4 validation matrix.

StegCore-coupled checks remain in ``verify_goal4_full.py`` and require the
explicit ``stegcore-integration`` dependency path. This script exists so the
repository-wide source validation lane can remain credential-free without
weakening or silently substituting the exact StegCore integration contract.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]

COMMANDS: tuple[tuple[str, ...], ...] = (
    (sys.executable, "scripts/verify_goal4.py"),
    (sys.executable, "scripts/check_architecture_guard.py"),
    (sys.executable, "-m", "pytest", "tests/test_local_node_vertical_slice.py", "-v"),
    (sys.executable, "scripts/check_stegverse_live_baseline_runtime_readiness.py"),
    (sys.executable, "scripts/check_stegverse_live_baseline_provider_authority_binding.py"),
    (sys.executable, "scripts/check_stegdeploy_image_publication_readiness.py"),
    (sys.executable, "scripts/check_exceed_federal_security_baseline.py"),
    (sys.executable, "scripts/check_session_provider_layer_consolidation.py"),
    (sys.executable, "scripts/check_session_provider_layer_archive_disposition.py"),
    (sys.executable, "scripts/check_llm_adapter_orchestration_state_current.py"),
    (sys.executable, "scripts/validate_ecosystem_va_chat_session_consolidation.py"),
    (sys.executable, "scripts/validate_va_claim_assistant_session_consolidation.py"),
    (sys.executable, "scripts/validate_va_claims_chat_runtime_contract.py"),
    (sys.executable, "tests/test_va_claim_assistant_privacy_runtime.py"),
    (sys.executable, "scripts/validate_va_claim_assistant_privacy_runtime.py"),
    (sys.executable, "tests/test_va_claim_assistant_route_classifier.py"),
    (sys.executable, "tests/test_va_claim_assistant_route_generators.py"),
    (sys.executable, "tests/test_va_claim_assistant_governed_retrieval.py"),
    (sys.executable, "tests/test_va_claim_assistant_governed_dispatch.py"),
    (sys.executable, "scripts/verify_hil_compatibility_full.py"),
    (sys.executable, "scripts/check_workflow_parity.py"),
    (sys.executable, "scripts/check_ai_entry_authority_boundary.py"),
    (sys.executable, "scripts/check_ai_entry_receipt_boundary.py"),
    (sys.executable, "scripts/check_ai_entry_provider_capture_boundary.py"),
    (sys.executable, "scripts/check_ai_entry_provider_capture_fixtures.py"),
    (sys.executable, "scripts/check_ai_entry_provider_capture_completion.py"),
    (sys.executable, "scripts/check_ai_entry_recovery_boundary.py"),
)

STEGCORE_INTEGRATION_COMMANDS: tuple[str, ...] = (
    "scripts/observe_va_service_connection_execution.py",
    "scripts/validate_va_claim_assistant_governed_retrieval_receipts.py",
    "tests/test_math_solver_gateway.py",
    "scripts/verify_math_solver_governed_runtime.py",
    "tests/test_steggate_portable_consumer.py",
    "scripts/verify_steggate_portable_consumer.py",
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


def main() -> int:
    for command in COMMANDS:
        run(command)
    print("ADAPTER_GOAL4_CREDENTIAL_FREE_PASS")
    print("STEGCORE_INTEGRATION_EXTRA=stegcore-integration")
    print("STEGCORE_INTEGRATION_COMMANDS=" + ",".join(STEGCORE_INTEGRATION_COMMANDS))
    print("GITHUB_TOKEN_AUTHORITY=NONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
