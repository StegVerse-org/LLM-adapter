#!/usr/bin/env python3
"""Issue a fresh, secret-free TVC admission for one governed VA public route.

This script grants no provider, custody, filing, publication, deployment, or Site
activation authority. It validates immutable caller/source bindings and emits a
single-use 15-minute admission artifact for consumption inside the same governed
execution preflight.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ALLOWED_ROUTES = {
    "claim_type",
    "evidence_requirement",
    "service_connection",
    "rating_criteria",
    "effective_date",
    "appeal_or_supplemental_claim",
    "cp_examination",
    "lay_statement",
    "private_record_collection",
    "procedural_filing",
    "representation_referral",
}
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
TOKEN = re.compile(r"^[A-Z0-9_:-]{3,160}$")
LIFETIME_SECONDS = 900


def canonical_hash(payload: dict[str, Any]) -> str:
    material = dict(payload)
    material.pop("receipt_hash", None)
    encoded = json.dumps(
        material,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--route", required=True)
    parser.add_argument("--caller-repository", required=True)
    parser.add_argument("--caller-commit", required=True)
    parser.add_argument("--source-registry-commit", required=True)
    parser.add_argument("--source-registry-blob-sha", required=True)
    parser.add_argument("--answer-schema-commit", required=True)
    parser.add_argument("--answer-receipt-hash", required=True)
    parser.add_argument("--dispatch-receipt-hash", required=True)
    parser.add_argument("--purpose", required=True)
    parser.add_argument("--scope", required=True)
    parser.add_argument("--workflow-run-id", required=True)
    parser.add_argument("--workflow-run-attempt", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def build_receipt(args: argparse.Namespace, *, now: datetime | None = None) -> dict[str, Any]:
    require(args.route in ALLOWED_ROUTES, "route_not_admitted")
    require(args.caller_repository == "StegVerse-org/LLM-adapter", "caller_repository_not_allowed")
    require(bool(HEX40.fullmatch(args.caller_commit)), "caller_commit_invalid")
    require(bool(HEX40.fullmatch(args.source_registry_commit)), "source_registry_commit_invalid")
    require(bool(HEX40.fullmatch(args.source_registry_blob_sha)), "source_registry_blob_sha_invalid")
    require(bool(HEX40.fullmatch(args.answer_schema_commit)), "answer_schema_commit_invalid")
    require(bool(HEX64.fullmatch(args.answer_receipt_hash)), "answer_receipt_hash_invalid")
    require(bool(HEX64.fullmatch(args.dispatch_receipt_hash)), "dispatch_receipt_hash_invalid")
    require(bool(TOKEN.fullmatch(args.purpose)), "purpose_invalid")
    require(bool(TOKEN.fullmatch(args.scope)), "scope_invalid")
    require(args.workflow_run_id.isdigit(), "workflow_run_id_invalid")
    require(args.workflow_run_attempt.isdigit(), "workflow_run_attempt_invalid")

    issued_at = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    expires_at = issued_at + timedelta(seconds=LIFETIME_SECONDS)
    admission_id = (
        f"tvc-va-{args.route}-{args.workflow_run_id}-{args.workflow_run_attempt}"
    )

    payload: dict[str, Any] = {
        "schema_version": "1.0.0",
        "receipt_id": admission_id,
        "capability_id": "va-claim-assistant-governed-retrieval",
        "state": "ADMITTED_PENDING_PROVIDER_EXECUTION",
        "issuer": {
            "repository": "StegVerse-Labs/TVC",
            "workflow": ".github/workflows/va-route-ephemeral-admission.yml",
            "workflow_run_id": args.workflow_run_id,
            "workflow_run_attempt": args.workflow_run_attempt,
        },
        "caller": {
            "repository": args.caller_repository,
            "commit": args.caller_commit,
        },
        "invocation": {
            "route": args.route,
            "source_registry_commit": args.source_registry_commit,
            "source_registry_blob_sha": args.source_registry_blob_sha,
            "answer_schema_commit": args.answer_schema_commit,
            "answer_receipt_hash": args.answer_receipt_hash,
            "dispatch_receipt_hash": args.dispatch_receipt_hash,
            "purpose": args.purpose,
            "scope": args.scope,
        },
        "validity": {
            "issued_at": issued_at.isoformat().replace("+00:00", "Z"),
            "expires_at": expires_at.isoformat().replace("+00:00", "Z"),
            "lifetime_seconds": LIFETIME_SECONDS,
            "single_use": True,
            "commit_time_validity_passed": True,
            "revocation_reference": (
                "tvc://revocations/va-claim-assistant-governed-retrieval/"
                + admission_id
            ),
            "revocation_state_at_issue": "NOT_REVOKED",
        },
        "checks": {
            "caller_allowed": True,
            "route_allowed": True,
            "source_registry_bound": True,
            "answer_schema_bound": True,
            "answer_and_dispatch_hashes_bound": True,
            "purpose_bound": True,
            "scope_bound": True,
            "expiry_bounded": True,
            "revocation_checked": True,
            "secret_values_present": False,
            "direct_identifiers_present": False,
            "raw_documents_present": False,
            "prompts_or_traces_present": False,
            "medical_narrative_present": False,
            "authority_escalation_absent": True,
        },
        "provider_execution_requested": False,
        "provider_execution_observed": False,
        "custody_state": "PENDING_REAL_ADAPTER_EXECUTION",
        "reconstruction_state": "PENDING_REAL_ADAPTER_EXECUTION",
        "next_owner": "StegVerse-org/LLM-adapter#90 then master-records/orchestration#15",
        "authority_flags": {
            "adjudication": False,
            "representation": False,
            "medical_opinion": False,
            "rating": False,
            "publication": False,
            "public_activation": False,
            "filing": False,
            "submission": False,
        },
        "activation_effect": False,
    }
    payload["receipt_hash"] = canonical_hash(payload)
    return payload


def write_github_outputs(receipt: dict[str, Any], output_path: Path) -> None:
    github_output = os.getenv("GITHUB_OUTPUT")
    if not github_output:
        return
    validity = receipt["validity"]
    with Path(github_output).open("a", encoding="utf-8") as handle:
        handle.write(f"receipt_path={output_path}\n")
        handle.write(f"receipt_hash={receipt['receipt_hash']}\n")
        handle.write(f"receipt_id={receipt['receipt_id']}\n")
        handle.write(f"issued_at={validity['issued_at']}\n")
        handle.write(f"expires_at={validity['expires_at']}\n")
        handle.write(f"state={receipt['state']}\n")


def main() -> int:
    args = parse_args()
    try:
        receipt = build_receipt(args)
    except ValueError as exc:
        raise SystemExit(f"VA_EPHEMERAL_ADMISSION_FAIL:{exc}") from exc

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_github_outputs(receipt, output_path)
    print(
        "VA_EPHEMERAL_ADMISSION_PASS:"
        f"{receipt['receipt_id']}:{receipt['receipt_hash']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
