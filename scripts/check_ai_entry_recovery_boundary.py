#!/usr/bin/env python3
"""Verify adapter recovery boundary mirror remains preview-only."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "llm_adapter" / "ai_entry_recovery_boundary.py"
FALSE_KEYS = (
    "recovery_confirmed",
    "activation_allowed",
    "execution_allowed",
    "live_provider_calls_allowed",
    "live_sdk_calls_allowed",
)


def fail(message: str) -> None:
    raise SystemExit(f"ADAPTER_RECOVERY_BOUNDARY_FAIL: {message}")


def load_module():
    module_name = "ai_entry_recovery_boundary"
    spec = importlib.util.spec_from_file_location(module_name, MODULE)
    if spec is None or spec.loader is None:
        fail("cannot load module spec")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    module = load_module()
    recovery = module.preview_recovery({"input": "ignored"})
    if recovery.get("decision") != "DENY":
        fail("decision must be DENY")
    if recovery.get("mode") != "preview_only":
        fail("mode must be preview_only")
    for key in FALSE_KEYS:
        if recovery.get(key) is not False:
            fail(f"{key} must be false")
    print("ADAPTER_RECOVERY_BOUNDARY_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
