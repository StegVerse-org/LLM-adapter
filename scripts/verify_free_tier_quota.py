#!/usr/bin/env python3
"""Verify the side-effect-free free-tier quota boundary."""

from __future__ import annotations

import json
from pathlib import Path

from llm_adapter.free_tier_quota import FreeTierUsage, evaluate_free_tier_quota

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "examples" / "free_tier_trust_policy.json"
DOC_PATH = ROOT / "docs" / "FREE_TIER_TRUST_POLICY.md"
MODULE_PATH = ROOT / "llm_adapter" / "free_tier_quota.py"
TEST_PATH = ROOT / "tests" / "test_free_tier_quota.py"


def main() -> int:
    policy_payload = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    quota = policy_payload["quota"]
    policy = {
        "tier": policy_payload["tier"],
        "governed_inquiries_per_day": quota["governed_inquiries_per_day"],
        "trial_governed_inquiries_total": quota["trial_governed_inquiries_total"],
        "receipt_exports_per_day": quota["receipt_exports_per_day"],
        "replays_per_day": quota["replays_per_day"],
    }

    allow = evaluate_free_tier_quota(FreeTierUsage(), policy=policy).to_dict()
    deny = evaluate_free_tier_quota(
        FreeTierUsage(
            governed_inquiries_today=quota["governed_inquiries_per_day"],
            trial_governed_inquiries_total=1,
        ),
        policy=policy,
    ).to_dict()
    connector_deny = evaluate_free_tier_quota(
        FreeTierUsage(wants_private_connector=True, wants_premium_model=True),
        policy=policy,
    ).to_dict()

    checks = {
        "policy_manifest_exists": POLICY_PATH.exists(),
        "policy_doc_exists": DOC_PATH.exists(),
        "quota_module_exists": MODULE_PATH.exists(),
        "quota_tests_exist": TEST_PATH.exists(),
        "allow_path_allows": allow["status"] == "ALLOW_QUOTA" and allow["allowed"] is True,
        "daily_exhaustion_denies": deny["status"] == "DENY_QUOTA"
        and "daily_governed_inquiry_quota_exhausted" in deny["reasons"],
        "connector_and_model_denies": connector_deny["status"] == "DENY_QUOTA"
        and "private_connectors_disabled_on_free_tier" in connector_deny["reasons"]
        and "premium_models_disabled_on_free_tier" in connector_deny["reasons"],
        "quota_allow_non_authorizing": allow["non_claims"]["quota_allow_is_admissibility"] is False
        and allow["non_claims"]["quota_allow_is_execution_authority"] is False,
    }

    status = "PASS" if all(checks.values()) else "FAIL"
    print(json.dumps({"status": status, "checks": checks}, indent=2, sort_keys=True))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
