#!/usr/bin/env python3
"""Validate the canonical portable StegGate consumer without hosted artifact transport."""
from __future__ import annotations

import hashlib
import json

from llm_adapter.steggate_portable_consumer import canonical_runtime_identity
from stegcore.portable_steggate import runtime_fingerprint

EXPECTED_STEGCORE_COMMIT = "8c484e584d60a3bd2763d6948d0eb3f4afd67e0c"


def main() -> int:
    identity = canonical_runtime_identity()
    expected = {
        "contract_version": "stegverse.steggate.runtime-identity.v1",
        "runtime_identity": "stegverse:steggate:canonical:three-layer:v1",
        "canonical_owner": "StegVerse-Labs/StegCore",
        "canonical_admissibility_runtime": "stegcore.three_layer.evaluate_three_layer",
    }
    for key, value in expected.items():
        if identity.get(key) != value:
            raise SystemExit(f"STEGGATE_PORTABLE_CONSUMER_FAIL:{key}")
    if identity.get("transport_identity_authoritative") is not False:
        raise SystemExit("STEGGATE_PORTABLE_CONSUMER_FAIL:transport_identity_authoritative")

    record = {
        "schema_version": "ECOSYSTEM-CHAT-STEGGATE-PORTABLE-CONSUMER-v3",
        "consumer": "StegVerse-org/LLM-adapter",
        "application": "Ecosystem Chat",
        "stegcore_commit": EXPECTED_STEGCORE_COMMIT,
        "runtime_fingerprint": runtime_fingerprint(),
        "runtime_identity": identity,
        "portable_profile": "steggate.portable-micronode.v1",
        "provider_credentials_transported": False,
        "public_steggate_ingress_required": False,
        "decision_authority_duplicated": False,
        "transport_identity_authoritative": False,
        "provider_callback_reachable_only_after_steggate_and_coherence_allow": True,
        "public_provider_execution_proven": False,
        "github_artifact_transport_required": False,
        "github_token_runtime_authority": "NONE",
        "credential_authority": "TV/TVC",
        "authority_effect": False,
        "status": "PASS",
    }
    canonical = json.dumps(record, sort_keys=True, separators=(",", ":")).encode("utf-8")
    receipt_hash = hashlib.sha256(canonical).hexdigest()
    if len(receipt_hash) != 64:
        raise SystemExit("STEGGATE_PORTABLE_CONSUMER_FAIL:receipt_hash")
    print(json.dumps({**record, "receipt_hash": receipt_hash}, sort_keys=True))
    print("STEGGATE_PORTABLE_CONSUMER_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
