#!/usr/bin/env python3
"""Write a secret-free governed-provider readiness status document."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from llm_adapter.governed_provider import readiness

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "reports" / "provider-readiness-status.json"


def canonical_hash(payload: dict) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def build_status() -> dict:
    payload = {
        "schema": "stegverse.provider-readiness.v1",
        "observed_at": datetime.now(timezone.utc).isoformat(),
        **readiness().to_dict(),
        "credential_value_retained": False,
        "provider_contact_attempted": False,
        "provider_response_verified": False,
        "custody_verified_by_this_status": False,
        "activation_authority": False,
    }
    payload["status_sha256"] = canonical_hash(payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    payload = build_status()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
