#!/usr/bin/env python3
"""Validate immutable receipt compatibility without requiring hosted activation authority.

The resident StegVerse carrier owns production activation. Repository validation may
retain a verified receipt for compatibility, but GitHub workflows, repository secrets,
and hosted provider execution are not production authority.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
VALIDATE_WORKFLOW = ROOT / ".github" / "workflows" / "validate.yml"
RETIRED_WORKFLOW = ROOT / ".github" / "workflows" / "ecosystem-chat-live-activation.yml"
HANDOFF = ROOT / "docs" / "WORKFLOW_CONSOLIDATION_MIRROR_HANDOFF.md"

REQUIRED_VALIDATE = [
    "receipts/ecosystem-chat-live-activation.latest.json",
    "receipts/ecosystem-chat-live-activation.verified.json",
    "cp receipts/ecosystem-chat-live-activation.latest.json receipts/ecosystem-chat-live-activation.verified.json",
    "git add receipts/ecosystem-chat-live-activation.verified.json",
    "verified.get('blockers') != []",
    "python scripts/verify_live_ecosystem_chat_activation.py",
]
FORBIDDEN_VALIDATE = [
    "git add receipts/ecosystem-chat-live-activation.latest.json",
    "${{ secrets.",
]
REQUIRED_HANDOFF = [
    "credential_authority: TV/TVC",
    "github_token_runtime_authority: NONE",
    "resident sovereign carrier",
    "ecosystem-chat-live-activation.yml",
]


def main() -> int:
    errors: list[str] = []
    if RETIRED_WORKFLOW.exists():
        errors.append("retired hosted activation workflow still exists")
    if not VALIDATE_WORKFLOW.exists():
        errors.append("validation dispatcher missing")
    else:
        text = VALIDATE_WORKFLOW.read_text(encoding="utf-8")
        errors.extend(
            f"missing validation receipt contract text: {term}"
            for term in REQUIRED_VALIDATE
            if term not in text
        )
        errors.extend(
            f"forbidden validation contract text: {term}"
            for term in FORBIDDEN_VALIDATE
            if term in text
        )
    if not HANDOFF.exists():
        errors.append("workflow consolidation handoff missing")
    else:
        handoff = HANDOFF.read_text(encoding="utf-8")
        errors.extend(
            f"missing StegVerse authority handoff text: {term}"
            for term in REQUIRED_HANDOFF
            if term not in handoff
        )
    if errors:
        for error in errors:
            print("FAIL: " + error, file=sys.stderr)
        return 1
    print(
        "PASS: immutable verified-receipt compatibility is retained while production "
        "activation remains resident-SteGVerse/TV-TVC owned."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
