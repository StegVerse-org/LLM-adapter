#!/usr/bin/env python3
"""Fail-closed validation for TV/TVC service return packages."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"TV/TVC service return validation failed: {message}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle", type=Path)
    parser.add_argument("ledger_receipt", type=Path)
    args = parser.parse_args()
    bundle = json.loads(args.bundle.read_text(encoding="utf-8"))
    ledger = json.loads(args.ledger_receipt.read_text(encoding="utf-8"))
    for field in (
        "request",
        "canonical_request_sha256",
        "estimate_line",
        "authority_evidence",
        "admissibility_result",
        "service_receipt",
        "actual_invoice_line",
        "requester_return",
        "bundle_sha256",
    ):
        require(field in bundle, f"bundle missing {field}")
    recompute = dict(bundle)
    claimed_bundle_hash = recompute.pop("bundle_sha256")
    require(digest(recompute) == claimed_bundle_hash, "bundle hash mismatch")
    request_hash = digest(bundle["request"])
    require(request_hash == bundle["canonical_request_sha256"], "request hash mismatch")
    receipt = bundle["service_receipt"]
    claimed_receipt_hash = receipt["receipt_sha256"]
    receipt_body = dict(receipt)
    receipt_body.pop("receipt_sha256")
    require(digest(receipt_body) == claimed_receipt_hash, "service receipt hash mismatch")
    require(bundle["actual_invoice_line"].get("service_receipt_sha256") == claimed_receipt_hash,
            "actual invoice line is not receipt-bound")
    require(ledger.get("bundle_sha256") == claimed_bundle_hash, "ledger receipt references another bundle")
    require(claimed_receipt_hash in {bundle["requester_return"].get("receipt_sha256"),
                                    bundle["actual_invoice_line"].get("service_receipt_sha256")},
            "return package is not receipt-bound")
    require(receipt.get("master_record_authorized") is False,
            "service return must not imply Master Record authority")
    print("TV_TVC_SERVICE_RETURN_VALIDATION=PASS")
    print(f"REQUEST_ID={bundle['request']['request_id']}")
    print(f"SERVICE_ID={bundle['request']['service_id']}")


if __name__ == "__main__":
    main()
