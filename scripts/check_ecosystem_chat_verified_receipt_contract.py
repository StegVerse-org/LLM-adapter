#!/usr/bin/env python3
"""Validate immutable activation-receipt semantics without hosted activation authority.

The resident StegVerse carrier owns production activation and TV/TVC owns credentials.
Repository validation checks the receipt/verifier contract only; it must not probe a
live runtime, persist activation receipts, upload them as GitHub artifacts, or mutate
the repository.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
VALIDATE_WORKFLOW = ROOT / ".github" / "workflows" / "validate.yml"
RETIRED_WORKFLOW = ROOT / ".github" / "workflows" / "ecosystem-chat-live-activation.yml"
VERIFIER = ROOT / "scripts" / "verify_live_ecosystem_chat_activation.py"
STATUS_WRITER = ROOT / "scripts" / "write_live_activation_status.py"
HANDOFF = ROOT / "docs" / "WORKFLOW_CONSOLIDATION_MIRROR_HANDOFF.md"

REQUIRED_VALIDATE = [
    "Deterministic repository validation only",
    "permissions: {}",
    "Refuse credential-bearing environment",
    "Fetch exact source anonymously",
    "Check immutable verified activation receipt contract",
    "GLOBAL_VALIDATE_GITHUB_TOKEN_AUTHORITY=NONE",
    "GLOBAL_VALIDATE_ACTIVATION_EFFECT=NONE",
]
FORBIDDEN_VALIDATE = [
    "Probe deployed Ecosystem Chat vertical slice",
    "Write stable activation status from validation probe",
    "Retain and persist current activation evidence",
    "actions/" + "upload-artifact@",
    "actions/" + "checkout@",
    "actions/" + "setup-python@",
    "git " + "push",
    "verify_" + "live_ecosystem_chat_activation.py",
]
REQUIRED_VERIFIER = [
    "receipts/ecosystem-chat-live-activation.latest.json",
    '"authority_granted": False',
    '"repository_mutation_authorized": False',
    'state = "VERIFIED" if not blockers else "PENDING"',
    'OUTPUT.write_text',
]
FORBIDDEN_VERIFIER = [
    "STEGVERSE_PROVIDER_TOKEN",
    "STEGVERSE_MASTER_RECORDS_TOKEN",
    "git " + "push",
]
REQUIRED_STATUS_WRITER = [
    "live_activation_status.v1",
    "verified_live_activation_contains_blockers",
    '"status_is_activation_authority": False',
    '"status_is_deployment_authority": False',
    '"status_is_custody": False',
    '"status_is_release_authority": False',
    "status_sha256",
]
REQUIRED_HANDOFF = [
    "credential_authority: TV/TVC",
    "github_token_runtime_authority: NONE",
    "resident sovereign carrier",
    "ecosystem-chat-live-activation.yml: RETIRED",
    "resident StegVerse carrier + TV/TVC",
]


def check_terms(errors: list[str], path: Path, required: list[str], forbidden: list[str], label: str) -> None:
    if not path.exists():
        errors.append(f"{label} missing")
        return
    text = path.read_text(encoding="utf-8")
    errors.extend(f"missing {label} contract text: {term}" for term in required if term not in text)
    errors.extend(f"forbidden {label} contract text: {term}" for term in forbidden if term in text)


def main() -> int:
    errors: list[str] = []
    if RETIRED_WORKFLOW.exists():
        errors.append("retired hosted activation workflow still exists")

    check_terms(errors, VALIDATE_WORKFLOW, REQUIRED_VALIDATE, FORBIDDEN_VALIDATE, "validation")
    check_terms(errors, VERIFIER, REQUIRED_VERIFIER, FORBIDDEN_VERIFIER, "resident-verifier")
    check_terms(errors, STATUS_WRITER, REQUIRED_STATUS_WRITER, [], "status-writer")
    check_terms(errors, HANDOFF, REQUIRED_HANDOFF, [], "StegVerse-authority-handoff")

    if errors:
        for error in errors:
            print("FAIL: " + error, file=sys.stderr)
        return 1
    print(
        "PASS: immutable activation-receipt semantics remain fail-closed while live activation "
        "and persistence remain resident-SteGVerse/TV-TVC owned and GitHub validation has no "
        "activation or repository-mutation role."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
