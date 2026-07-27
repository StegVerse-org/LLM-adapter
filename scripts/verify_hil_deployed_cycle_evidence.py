#!/usr/bin/env python3
"""Validate evidence for an externally deployed HIL v1.1 controlled cycle."""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

PRIMARY = "a7b1c62e336b4e244ecf7fdcd10af195401f6c44328de32615b073d2a5c3c462"
PROMPT = "cdff8d2266bb3eefbb6e5d28d9adc548e6c8dfc039debd72fe404f1d0249912c"
HEX64 = set("0123456789abcdef")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def canonical_hash(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def digest(value: object, field: str) -> str:
    require(isinstance(value, str) and len(value) == 64 and set(value) <= HEX64, f"{field} must be lowercase SHA-256")
    return value


def main() -> int:
    evidence_path = Path(os.getenv("HIL_DEPLOYED_CYCLE_EVIDENCE", "reports/hil-deployed-cycle-evidence.json"))
    require(evidence_path.is_file(), f"missing deployed-cycle evidence: {evidence_path}")
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    require(isinstance(evidence, dict), "evidence must be a JSON object")
    require(evidence.get("schema_version") == "HIL-DEPLOYED-CYCLE-EVIDENCE-v1", "schema mismatch")

    origin = evidence.get("receiver_origin")
    parsed = urlparse(origin if isinstance(origin, str) else "")
    require(parsed.scheme == "https" and parsed.hostname, "receiver_origin must be HTTPS")
    require(not parsed.username and not parsed.password and not parsed.query and not parsed.fragment, "unsafe receiver_origin")
    require(parsed.path in {"", "/"}, "receiver_origin must not contain a path")

    expected = {
        "primary_version": "v1.1",
        "primary_sha256": PRIMARY,
        "protocol_version": "HIL-PROTOCOL-v1.1",
        "prompt_version": "HIL-PROMPT-v1.1",
        "prompt_sha256": PROMPT,
        "provenance_schema": "HIL-RESPONSE-PROVENANCE-v1.1",
        "receipt_schema": "HIL-RECEIVER-RECEIPT-v2",
        "readiness_before_upload": "READY",
        "readiness_after_restart": "READY",
        "controlled_upload_completed": True,
        "exact_response_bytes_persisted": True,
        "provenance_manifest_persisted": True,
        "actual_service_restart_or_replacement": True,
        "private_review_decision": "ACCEPT_PRIVATE",
        "append_only_publication_state": "PUBLISHED_APPEND_ONLY",
        "stable_public_lookup_completed": True,
        "site_import_completed": False,
        "master_record_release_completed": False,
        "execution_authority": False,
        "publication_authority_granted_by_evidence": False,
        "master_record_append_authority_granted_by_evidence": False,
        "authority_effect": "NONE",
    }
    for field, value in expected.items():
        require(evidence.get(field) == value, f"evidence mismatch for {field}")

    for field in (
        "response_sha256",
        "provenance_manifest_sha256",
        "receiver_receipt_sha256",
        "private_review_receipt_sha256",
        "publication_record_sha256",
        "readiness_probe_sha256",
    ):
        digest(evidence.get(field), field)

    require(isinstance(evidence.get("submission_id"), str) and evidence["submission_id"], "submission_id required")
    require(isinstance(evidence.get("response_id"), str) and evidence["response_id"].startswith("HIL-RESP-"), "response_id invalid")
    require(evidence.get("storage_scope") == "EXTERNAL_DURABLE_SERVICE", "storage_scope must be external durable service")
    require(evidence.get("observation_scope") == "DEPLOYED_CONTROLLED_CYCLE", "observation_scope mismatch")

    claimed = digest(evidence.get("evidence_sha256"), "evidence_sha256")
    unsigned = dict(evidence)
    unsigned.pop("evidence_sha256", None)
    require(claimed == canonical_hash(unsigned), "evidence_sha256 mismatch")
    print("HIL_DEPLOYED_CYCLE_EVIDENCE=PASS")
    print(f"HIL_DEPLOYED_CYCLE_EVIDENCE_SHA256={claimed}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"HIL_DEPLOYED_CYCLE_EVIDENCE=FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
