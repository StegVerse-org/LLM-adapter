#!/usr/bin/env python3
"""Verify the side-effect-free free-tier receipt/replay limit boundary."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from llm_adapter.free_tier_limits import ReceiptReplayUsage, evaluate_receipt_replay_limits

POLICY_PATH = ROOT / "examples" / "free_tier_trust_policy.json"
MODULE_PATH = ROOT / "llm_adapter" / "free_tier_limits.py"
TEST_PATH = ROOT / "tests" / "test_free_tier_limits.py"


def main() -> int:
    policy_payload = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    quota = policy_payload["quota"]
    retention = policy_payload["retention"]
    capabilities = policy_payload["capabilities"]

    policy = {
        "tier": policy_payload["tier"],
        "receipt_exports_per_day": quota["receipt_exports_per_day"],
        "replays_per_day": quota["replays_per_day"],
        "reconstructions_per_day": 1,
        "reconstruction_scope": capabilities["recent_session_reconstruction"]
        and "recent_session_limited",
        "full_evidence_bundle_retention_enabled": retention[
            "full_evidence_bundle_retention"
        ],
        "exportable_audit_packet_enabled": retention["exportable_audit_packet"],
        "cross_session_reconstruction_enabled": False,
    }

    allow = evaluate_receipt_replay_limits(ReceiptReplayUsage(), policy=policy).to_dict()
    receipt_deny = evaluate_receipt_replay_limits(
        ReceiptReplayUsage(receipt_exports_today=quota["receipt_exports_per_day"]),
        policy=policy,
    ).to_dict()
    replay_deny = evaluate_receipt_replay_limits(
        ReceiptReplayUsage(replays_today=quota["replays_per_day"], reconstructions_today=1),
        policy=policy,
    ).to_dict()
    scope_deny = evaluate_receipt_replay_limits(
        ReceiptReplayUsage(
            wants_full_evidence_bundle=True,
            wants_exportable_audit_packet=True,
            wants_cross_session_reconstruction=True,
            wants_long_term_retention=True,
        ),
        policy=policy,
    ).to_dict()

    checks = {
        "policy_manifest_exists": POLICY_PATH.exists(),
        "limit_module_exists": MODULE_PATH.exists(),
        "limit_tests_exist": TEST_PATH.exists(),
        "allow_path_allows": allow["status"] == "ALLOW_LIMIT" and allow["allowed"] is True,
        "receipt_export_exhaustion_denies": receipt_deny["status"] == "DENY_LIMIT"
        and "receipt_export_limit_exhausted" in receipt_deny["reasons"],
        "replay_and_reconstruction_exhaustion_denies": replay_deny["status"] == "DENY_LIMIT"
        and "replay_limit_exhausted" in replay_deny["reasons"]
        and "reconstruction_limit_exhausted" in replay_deny["reasons"],
        "scope_requests_deny": scope_deny["status"] == "DENY_LIMIT"
        and "full_evidence_bundle_disabled_on_free_tier" in scope_deny["reasons"]
        and "exportable_audit_packet_disabled_on_free_tier" in scope_deny["reasons"]
        and "cross_session_reconstruction_disabled_on_free_tier" in scope_deny["reasons"]
        and "long_term_retention_disabled_on_free_tier" in scope_deny["reasons"],
        "limit_allow_non_authorizing": allow["non_claims"]["limit_allow_is_admissibility"] is False
        and allow["non_claims"]["limit_allow_is_execution_authority"] is False
        and allow["non_claims"]["reconstruction_grants_commit_time_standing"] is False,
    }

    status = "PASS" if all(checks.values()) else "FAIL"
    print(json.dumps({"status": status, "checks": checks}, indent=2, sort_keys=True))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
