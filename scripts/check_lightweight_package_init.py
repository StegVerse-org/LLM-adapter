#!/usr/bin/env python3
"""Verify llm_adapter package import remains lightweight for preview validation."""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

INIT = ROOT / "llm_adapter" / "__init__.py"


def fail(message: str) -> None:
    raise SystemExit(f"LIGHTWEIGHT_PACKAGE_INIT_FAIL: {message}")


def main() -> int:
    text = INIT.read_text(encoding="utf-8")
    blocked_markers = (
        "http_provider_clients",
        "continuity_service_client",
        "requests",
        "OpenAIHTTPProviderClient",
        "AnthropicHTTPProviderClient",
    )
    for marker in blocked_markers:
        if marker in text:
            fail(f"package init must not import optional dependency marker: {marker}")

    module = importlib.import_module("llm_adapter")
    if not hasattr(module, "__all__"):
        fail("package init must define __all__")

    service = importlib.import_module("llm_adapter.ai_entry_service_wrapper")
    response = service.handle_service_request({"message": "Compare StegVerse with Claude"})
    if response.get("primary_route") != "llm_comparison":
        fail("AI Entry service wrapper import smoke test failed")
    if response.get("service", {}).get("live_calls_enabled") is not False:
        fail("service wrapper must remain disabled by default")

    print("LIGHTWEIGHT_PACKAGE_INIT_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
