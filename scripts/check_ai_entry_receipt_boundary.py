#!/usr/bin/env python3
"""Verify adapter receipt boundary mirror remains preview-only."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "llm_adapter" / "ai_entry_receipt_boundary.py"
FALSE_KEYS = (
    "real_receipt_issued",
    "receipt_persisted",
    "reconstruction_available",
    "authority_issued",
    "execution_allowed",
    "live_calls_allowed",
)


def fail(message: str) -> None:
    raise SystemExit(f"ADAPTER_RECEIPT_BOUNDARY_FAIL: {message}")


def load_module():
    module_name = "ai_entry_receipt_boundary"
    spec = importlib.util.spec_from_file_location(module_name, MODULE)
    if spec is None or spec.loader is None:
        fail("cannot load module spec")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    text = MODULE.read_text(encoding="utf-8")
    for marker in ("NOT_ISSUED", "preview_only", "preview_receipt"):
        if marker not in text:
            fail(f"missing marker: {marker}")
    module = load_module()
    receipt = module.preview_receipt({"input": "ignored"})
    if receipt.get("status") != "NOT_ISSUED":
        fail("status must be NOT_ISSUED")
    if receipt.get("mode") != "preview_only":
        fail("mode must be preview_only")
    for key in FALSE_KEYS:
        if receipt.get(key) is not False:
            fail(f"{key} must be false")
    print("ADAPTER_RECEIPT_BOUNDARY_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
