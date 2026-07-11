#!/usr/bin/env python3
"""Verify Site-facing free-tier trust metadata in AI Entry response."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from llm_adapter.ai_entry_backend_service import build_ai_entry_backend_response

BACKEND_PATH = ROOT / "llm_adapter" / "ai_entry_backend_service.py"
TEST_PATH = ROOT / "tests" / "test_ai_entry_free_tier_trust_metadata.py"


def main() -> int:
    response = build_ai_entry_backend_response("Explain governed replay").to_dict()
    free_tier = response["free_tier_trust"]
    quota = free_tier["quota"]
    limits = free_tier["receipt_replay_limits"]

    checks = {
        "backend_path_exists": BACKEND_PATH.exists(),
        "metadata_tests_exist": TEST_PATH.exists(),
        "metadata_schema_present": free_tier["schema_version"] == "stegverse.ai_entry.free_tier_trust.v0.1",
        "bounded_live_use_enabled": free_tier["bounded_live_use"] is True,
        "static_demo_only_false": free_tier["static_demo_only"] is False,
        "quota_metadata_present": quota["status"] == "ALLOW_QUOTA" and quota["allowed"] is True,
        "limit_metadata_present": limits["status"] == "ALLOW_LIMIT" and limits["allowed"] is True,
        "quota_non_authorizing": quota["non_claims"]["quota_allow_is_admissibility"] is False
        and quota["non_claims"]["quota_allow_is_execution_authority"] is False,
        "limit_non_authorizing": limits["non_claims"]["limit_allow_is_admissibility"] is False
        and limits["non_claims"]["reconstruction_grants_commit_time_standing"] is False,
        "upgrade_reasons_site_visible": "higher_quota" in free_tier["upgrade_for"]
        and "private_connectors" in free_tier["upgrade_for"]
        and "premium_models" in free_tier["upgrade_for"]
        and "exportable_audit_packet" in free_tier["upgrade_for"],
    }

    status = "PASS" if all(checks.values()) else "FAIL"
    print(json.dumps({"status": status, "checks": checks}, indent=2, sort_keys=True))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
