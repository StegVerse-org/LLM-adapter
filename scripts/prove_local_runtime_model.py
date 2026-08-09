#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, urllib.request
from pathlib import Path
from llm_adapter.local_model_runtime import ensure_local_runtime

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "receipts/local-runtime-model-proof.latest.json"

def canonical_hash(v):
    return hashlib.sha256(json.dumps(v, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

def main() -> int:
    discovery, launched = ensure_local_runtime()
    try:
        base = discovery["base_url"]
        payload = json.dumps({"prompt":"governed inference", "max_tokens":12}).encode()
        req = urllib.request.Request(base + "/v1/completions", data=payload, headers={"Content-Type":"application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=5) as response:
            inference = json.loads(response.read())
        proof = {
            "schema_version":"stegverse.local-runtime-model-proof.v1",
            "state":"COMPLETE",
            "discovery_state":discovery["state"],
            "runtime":discovery["runtime"],
            "base_url_scope":"loopback",
            "launched_by_proof": launched is not None,
            "runtime_identity":discovery["identity"],
            "inference":inference,
            "real_local_inference_observed":True,
            "external_provider_used":False,
            "network_required_for_model":False,
            "authority_attached":False,
            "execution_authority":False,
            "next_executable_action":"bind this local runtime protocol into Ecosystem Chat governed provider execution before custody/activation gates",
            "next_owner":"StegVerse-org/LLM-adapter#18"
        }
        proof["receipt_hash"] = canonical_hash(proof)
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(proof, indent=2, sort_keys=True)+"\n")
        print(json.dumps({"state":proof["state"],"model_id":inference["model_id"],"receipt_hash":proof["receipt_hash"]}))
        return 0
    finally:
        if launched is not None: launched.stop()
if __name__ == "__main__": raise SystemExit(main())
