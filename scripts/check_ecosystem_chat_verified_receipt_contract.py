#!/usr/bin/env python3
"""Fail closed if live activation cannot publish the immutable receipt Site imports."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "ecosystem-chat-live-activation.yml"

REQUIRED = [
    "receipts/ecosystem-chat-live-activation.latest.json",
    "receipts/ecosystem-chat-live-activation.verified.json",
    "cp receipts/ecosystem-chat-live-activation.latest.json receipts/ecosystem-chat-live-activation.verified.json",
    "git add receipts/ecosystem-chat-live-activation.verified.json",
    "verified.get('state') != 'VERIFIED'",
    "verified.get('blockers') != []",
    "python scripts/verify_live_ecosystem_chat_activation.py",
]
FORBIDDEN = [
    "git add receipts/ecosystem-chat-live-activation.latest.json",
]


def main() -> int:
    if not WORKFLOW.exists():
        print(f"missing workflow: {WORKFLOW.relative_to(ROOT)}", file=sys.stderr)
        return 1
    text = WORKFLOW.read_text(encoding="utf-8")
    errors = [f"missing required contract text: {term}" for term in REQUIRED if term not in text]
    errors.extend(f"forbidden mutable receipt retention: {term}" for term in FORBIDDEN if term in text)
    if errors:
        for error in errors:
            print("FAIL: " + error, file=sys.stderr)
        return 1
    print("PASS: Ecosystem Chat immutable verified receipt publication matches the Site import contract.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
