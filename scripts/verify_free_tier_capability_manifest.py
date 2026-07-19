#!/usr/bin/env python3
"""Verify machine-readable free-tier trust fields in adapter.capabilities.json."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "adapter.capabilities.json"


def main() -> int:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    runtime = manifest["runtime_surfaces"]
    response_fields = manifest["ai_entry_response_fields"]
    free_tier = response_fields["free_tier_trust"]
    policy = manifest["free_tier_policy"]
    non_claims = set(manifest["explicit_non_claims"])
    local = manifest["local_verification"]

    checks = {
        "manifest_schema_supports_free_tier": manifest["schema_version"]
        in {
            "stegverse.llm_adapter.capabilities.v0.2",
            "stegverse.llm_adapter.capabilities.v0.3",
        },
        "free_tier_status_present": manifest["status"]
        in {
            "adapter-boundary-complete-with-free-tier-trust-boundary",
            "adapter-boundary-complete-with-system-boundary-declaration",
        },
        "quota_runtime_surface_present": runtime["free_tier_quota_evaluator"] == "built_side_effect_free",
        "limits_runtime_surface_present": runtime["free_tier_receipt_replay_limits"] == "built_side_effect_free",
        "metadata_runtime_surface_present": runtime["ai_entry_free_tier_trust_metadata"] == "built_preview_only",
        "free_tier_response_schema_present": free_tier["schema_version"] == "stegverse.ai_entry.free_tier_trust.v0.1",
        "bounded_live_use_true": free_tier["bounded_live_use"] is True,
        "static_demo_only_false": free_tier["static_demo_only"] is False,
        "upgrade_reasons_present": "higher_quota" in free_tier["upgrade_for"]
        and "private_connectors" in free_tier["upgrade_for"]
        and "premium_models" in free_tier["upgrade_for"]
        and "exportable_audit_packet" in free_tier["upgrade_for"],
        "policy_pointers_present": policy["policy_doc"] == "docs/FREE_TIER_TRUST_POLICY.md"
        and policy["policy_manifest"] == "examples/free_tier_trust_policy.json"
        and policy["quota_module"] == "llm_adapter/free_tier_quota.py"
        and policy["receipt_replay_limit_module"] == "llm_adapter/free_tier_limits.py",
        "non_claims_present": "Quota availability is not admissibility." in non_claims
        and "Receipt export is not permanent retention." in non_claims
        and "Replay does not grant commit-time standing." in non_claims
        and "Reconstruction does not grant commit-time standing." in non_claims
        and "Upgrading does not change admissibility requirements." in non_claims,
        "verification_commands_present": local["aggregate_verifier"] == "python scripts/verify_goal4.py"
        and local["free_tier_quota_verifier"] == "python scripts/verify_free_tier_quota.py"
        and local["free_tier_limits_verifier"] == "python scripts/verify_free_tier_limits.py"
        and local["ai_entry_free_tier_metadata_verifier"] == "python scripts/verify_ai_entry_free_tier_metadata.py",
    }

    status = "PASS" if all(checks.values()) else "FAIL"
    print(json.dumps({"status": status, "checks": checks}, indent=2, sort_keys=True))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
