#!/usr/bin/env python3
"""Verify provider capture boundary remains preview-only and disabled."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "llm_adapter" / "ai_entry_provider_capture_boundary.py"
FALSE_KEYS = (
    "provider_call_performed",
    "provider_output_captured",
    "provider_authority",
    "persisted",
    "live_calls_allowed",
)


def fail(message: str) -> None:
    raise SystemExit(f"ADAPTER_PROVIDER_CAPTURE_BOUNDARY_FAIL: {message}")


def load_module():
    spec = importlib.util.spec_from_file_location("ai_entry_provider_capture_boundary", MODULE)
    if spec is None or spec.loader is None:
        fail("cannot load module spec")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    text = MODULE.read_text(encoding="utf-8")
    for marker in ("preview_only", "provider_call_performed", "preview_provider_capture"):
        if marker not in text:
            fail(f"missing marker: {marker}")
    module = load_module()
    capture = module.preview_provider_capture({"input": "ignored"})
    if capture.get("mode") != "preview_only":
        fail("mode must be preview_only")
    for key in FALSE_KEYS:
        if capture.get(key) is not False:
            fail(f"{key} must be false")
    print("ADAPTER_PROVIDER_CAPTURE_BOUNDARY_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
