#!/usr/bin/env python3
"""Fail closed unless the StegVerse exceed-federal security contract is complete."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "data" / "security" / "exceed-federal-baseline.json"

REQUIRED_DOMAINS = {
    "identity-and-access",
    "cryptography-and-key-management",
    "zero-trust-and-network-boundaries",
    "software-supply-chain",
    "logging-audit-and-continuity",
    "runtime-and-execution-governance",
}
REQUIRED_STATES = {
    "COMPLETE",
    "BLOCKED",
    "RETRY",
    "REVIEW_REQUIRED",
    "FAILED",
    "CLAIMED",
    "SUPERSEDED",
    "MERGED",
}
PROHIBITED_CLAIMS = {
    "federal compliant",
    "FedRAMP authorized",
    "FIPS validated",
    "NIST certified",
    "agency approved",
    "production secure",
}


def fail(message: str) -> None:
    raise SystemExit(f"EXCEED_FEDERAL_SECURITY_BASELINE_FAIL:{message}")


def main() -> int:
    if not CONTRACT.is_file():
        fail("missing_contract")
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))

    if payload.get("schema") != "stegverse.security.exceed_federal_baseline.v1":
        fail("schema")
    rule = payload.get("baseline_rule") or {}
    for key in (
        "federal_requirements_are_minimum",
        "must_exceed_applicable_baseline",
        "fail_closed_when_applicability_or_evidence_is_unknown",
        "no_compliance_claim_without_evidence",
    ):
        if rule.get(key) is not True:
            fail(f"baseline_rule:{key}")

    domains = payload.get("control_domains") or []
    domain_ids = {item.get("id") for item in domains}
    if domain_ids != REQUIRED_DOMAINS:
        fail(f"control_domains:{sorted(domain_ids)}")
    for item in domains:
        if not item.get("minimum") or not item.get("stegverse_exceedance"):
            fail(f"incomplete_domain:{item.get('id')}")

    if set(payload.get("states") or []) != REQUIRED_STATES:
        fail("states")
    if set(payload.get("prohibited_claims_without_evidence") or []) != PROHIBITED_CLAIMS:
        fail("prohibited_claims")
    if payload.get("authority_effect") != "NONE":
        fail("authority_effect")
    if payload.get("manual_user_action_required") is not False:
        fail("manual_user_action_required")
    if not payload.get("next_executable_action"):
        fail("next_executable_action")

    print("EXCEED_FEDERAL_SECURITY_BASELINE_PASS")
    print(f"- domains: {len(domains)}")
    print("- authority effect: NONE")
    print("- certification claims: EVIDENCE REQUIRED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
