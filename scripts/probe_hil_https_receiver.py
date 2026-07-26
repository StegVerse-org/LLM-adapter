#!/usr/bin/env python3
"""Probe a public HIL v1.1 receiver without mutating it."""
from __future__ import annotations

import hashlib
import json
import os
import ssl
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

PRIMARY = "a7b1c62e336b4e244ecf7fdcd10af195401f6c44328de32615b073d2a5c3c462"
PROMPT = "cdff8d2266bb3eefbb6e5d28d9adc548e6c8dfc039debd72fe404f1d0249912c"
PROTOCOL = "HIL-PROTOCOL-v1.1"
PROMPT_VERSION = "HIL-PROMPT-v1.1"
PROVENANCE = "HIL-RESPONSE-PROVENANCE-v1.1"


def canonical_hash(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> int:
    base = os.getenv("STEGVERSE_HIL_RECEIVER_BASE_URL", "").strip().rstrip("/")
    require(base, "STEGVERSE_HIL_RECEIVER_BASE_URL is required")
    parsed = urlparse(base)
    require(parsed.scheme == "https", "receiver must use HTTPS")
    require(parsed.netloc and not parsed.username and not parsed.password, "receiver URL is invalid")
    require(not parsed.query and not parsed.fragment, "receiver URL must not contain query or fragment")

    request = Request(f"{base}/api/hil/readiness", headers={"Accept": "application/json", "User-Agent": "StegVerse-HIL-v1.1-probe"})
    with urlopen(request, timeout=20, context=ssl.create_default_context()) as response:
        require(response.status == 200, f"readiness returned HTTP {response.status}")
        payload = json.loads(response.read().decode("utf-8"))

    expected = {
        "state": "READY",
        "primary_version": "v1.1",
        "primary_sha256": PRIMARY,
        "protocol_version": PROTOCOL,
        "prompt_version": PROMPT_VERSION,
        "prompt_sha256": PROMPT,
        "provenance_manifest_schema": PROVENANCE,
        "participant_metadata_required": False,
        "execution_authority": False,
        "publication_authority": False,
        "master_record_append_authority": False,
    }
    for key, value in expected.items():
        require(payload.get(key) == value, f"readiness mismatch for {key}")
    require(payload.get("blockers") == [], "receiver reports readiness blockers")
    require(payload.get("accepted_media_type") == "application/pdf", "receiver media type mismatch")
    require(payload.get("maximum_size_bytes") == 10 * 1024 * 1024, "receiver size limit mismatch")

    evidence = {
        "schema_version": "HIL-HTTPS-RECEIVER-PROBE-v1",
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "receiver_origin": f"{parsed.scheme}://{parsed.netloc}",
        "readiness_path": "/api/hil/readiness",
        "tls_verified": True,
        "http_status": 200,
        "contract_state": "CONFORMING_V1_1_READINESS_OBSERVED",
        "readiness": payload,
        "mutation_performed": False,
        "custody_claimed": False,
        "publication_authorized": False,
        "master_record_append_authorized": False,
        "authority_effect": "NONE",
    }
    evidence["evidence_sha256"] = canonical_hash(evidence)
    output = Path(os.getenv("HIL_PROBE_OUTPUT", "reports/hil-https-receiver-probe.json"))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("HIL_HTTPS_RECEIVER_PROBE=PASS")
    print(f"HIL_PROBE_SHA256={evidence['evidence_sha256']}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"HIL_HTTPS_RECEIVER_PROBE=FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
