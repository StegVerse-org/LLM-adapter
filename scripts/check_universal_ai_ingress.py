#!/usr/bin/env python3
"""Machine validator for the universal AI ingress registry and contract."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from llm_adapter.universal_ai_ingress import (  # noqa: E402
    AI_ADAPTER_REGISTRY,
    audit_ai_adapter_registry,
)


REQUIRED_ADAPTERS = {
    "ai-adapter:zai",
    "ai-adapter:deepseek",
    "ai-adapter:kimi",
    "ai-adapter:anthropic",
    "ai-adapter:openai",
    "ai-adapter:openai-compatible",
    "ai-adapter:sovereign-local",
    "ai-adapter:browser-session",
}


def main() -> int:
    audit = audit_ai_adapter_registry()
    present = {adapter.adapter_id for adapter in AI_ADAPTER_REGISTRY}
    missing = sorted(REQUIRED_ADAPTERS - present)
    executable_external = sorted(
        adapter.adapter_id
        for adapter in AI_ADAPTER_REGISTRY
        if adapter.external_connection_dispatch
    )
    report = {
        "schema": "stegverse.llm_adapter.universal_ai_ingress_validation.v1",
        "task": "LLMA-UNIVERSAL-AI-INGRESS-324",
        "registry_audit": audit,
        "missing_required_adapters": missing,
        "external_connection_dispatch_adapters": executable_external,
        "expected_external_connection_dispatch_adapters": [
            "ai-adapter:anthropic",
            "ai-adapter:deepseek",
            "ai-adapter:kimi",
            "ai-adapter:zai",
        ],
        "pass": False,
    }
    report["pass"] = (
        audit["pass"]
        and not missing
        and executable_external == report["expected_external_connection_dispatch_adapters"]
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
