#!/usr/bin/env python3
"""Verify adapter authority boundary mirror remains fail-closed."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "llm_adapter" / "ai_entry_authority_boundary.py"
FALSE_KEYS = (
    "authority_issued",
    "execution_allowed",
    "credential_access_allowed",
    "live_provider_calls_allowed",
    "live_sdk_calls_allowed",
    "repo_mutation_allowed",
    "activation_request_executes",
)


def fail(message: str) -> None:
    raise SystemExit(f"ADAPTER_AUTHORITY_BOUNDARY_FAIL: {message}")


def load_module():
    spec = importlib.util.spec_from_file_location("ai_entry_authority_boundary", MODULE)
    if spec is None or spec.loader is None:
        fail("cannot load module spec")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    text = MODULE.read_text(encoding="utf-8")
    for marker in ("DENY", "preview_only", "must not grant capabilities"):
        if marker not in text:
            fail(f"missing marker: {marker}")
    module = load_module()
    decision = module.preview_authority_decision({"request": "ignored"})
    if decision.get("authority_decision") != "DENY":
        fail("decision must be DENY")
    if decision.get("decision_mode") != "preview_only":
        fail("decision mode must be preview_only")
    for key in FALSE_KEYS:
        if decision.get(key) is not False:
            fail(f"{key} must be false")
    print("ADAPTER_AUTHORITY_BOUNDARY_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
