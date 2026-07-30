#!/usr/bin/env python3
"""Validate observed deployment evidence for the canonical HIL receiver."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.parse import urlparse

EXPECTED = {
    "primary_version": "v1.1",
    "primary_sha256": "a7b1c62e336b4e244ecf7fdcd10af195401f6c44328de32615b073d2a5c3c462",
    "protocol_version": "HIL-PROTOCOL-v1.1",
    "prompt_version": "HIL-PROMPT-v1.1",
    "prompt_sha256": "cdff8d2266bb3eefbb6e5d28d9adc548e6c8dfc039debd72fe404f1d0249912c",
    "provenance_manifest_required": True,
    "provenance_manifest_schema": "HIL-RESPONSE-PROVENANCE-v1.1",
    "participant_metadata_required": False,
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"HIL receiver deployment evidence failed: {message}")


def is_hex(value: object, length: int) -> bool:
    return isinstance(value, str) and len(value) == length and all(c in "0123456789abcdef" for c in value)


def is_sha256(value: object) -> bool:
    return is_hex(value, 64)


def main() -> None:
    require(len(sys.argv) == 2, "usage: verify_hil_receiver_deployment_evidence.py <evidence.json>")
    path = Path(sys.argv[1])
    require(path.is_file(), f"missing evidence file: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))

    require(data.get("schema_version") == "HIL-RECEIVER-DEPLOYMENT-EVIDENCE-v1", "schema mismatch")
    parsed = urlparse(data.get("receiver_base_url", ""))
    require(parsed.scheme == "https" and parsed.hostname == "receiver.stegverse.com" and not parsed.query and not parsed.fragment, "receiver URL mismatch")
    require(is_hex(data.get("repository_revision"), 40), "deployed repository revision must be a full lowercase Git SHA")

    require(data["dns"]["publicly_resolved"] is True and data["dns"]["addresses"], "public DNS not established")
    require(data["tls"]["verified"] is True, "TLS not verified")
    require(data["tls"]["redirects_followed"] is False, "readiness evidence must not depend on redirects")

    readiness = data["readiness"]
    require(readiness.get("http_status") == 200 and readiness.get("state") == "READY", "receiver is not READY over HTTP 200")
    for key, value in EXPECTED.items():
        require(readiness.get(key) == value, f"readiness mismatch: {key}")

    submission = data["controlled_submission"]
    require(submission.get("performed") is True, "controlled submission not observed")
    require(is_sha256(submission.get("response_pdf_sha256")), "response PDF hash missing")
    require(is_sha256(submission.get("provenance_manifest_sha256")), "manifest hash missing")
    require(submission.get("receipt_schema_version") == "HIL-RECEIVER-RECEIPT-v2", "receipt schema mismatch")
    require(is_sha256(submission.get("receipt_sha256")), "receipt hash missing")
    require(submission.get("chain_validation_state") in {
        "PRIMARY_PROMPT_RESPONSE_CHAIN_VERIFIED",
        "PRIMARY_PROMPT_RESPONSE_SIGNATURE_CHAIN_VERIFIED",
    }, "submission chain not verified")

    durability = data["durability"]
    for key in ("restart_observed", "same_submission_reconstructed_after_restart", "artifact_bytes_match", "manifest_bytes_match"):
        require(durability.get(key) is True, f"durability evidence missing: {key}")

    require(data["site"].get("canonical_upload_url") == "https://stegverse.org/hil/upload/", "canonical Site URL mismatch")
    require(data["site"].get("upload_enabled_observed") is True, "public upload control not observed enabled")
    require(data["master_records"].get("custody_state") == "RECORDED", "Master-Records custody not recorded")
    require(data["master_records"].get("reconstruction_state") == "PASS", "Master-Records reconstruction not PASS")
    require(is_sha256(data["master_records"].get("receipt_sha256")), "Master-Records receipt hash missing")
    require(all(value is False for value in data["authority"].values()), "deployment evidence must not grant authority")

    print("HIL_RECEIVER_DEPLOYMENT_EVIDENCE=PASS")
    print("HIL_RECEIVER=https://receiver.stegverse.com")
    print("HIL_SITE_UPLOAD=https://stegverse.org/hil/upload/")
    print("HIL_AUTHORITY=NONE")


if __name__ == "__main__":
    main()
