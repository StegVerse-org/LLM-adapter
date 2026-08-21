#!/usr/bin/env python3
"""Validate the LLM-adapter component version declaration without granting release or runtime authority."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = ROOT / "VERSION.json"
HANDOFF = ROOT / "docs/ECOSYSTEM_CHAT_MIRROR_HANDOFF.md"


def fail(message: str) -> None:
    raise SystemExit(f"LLM_ADAPTER_COMPONENT_VERSION=FAIL\n- {message}")


def main() -> None:
    data = json.loads(VERSION.read_text(encoding="utf-8"))
    handoff = HANDOFF.read_text(encoding="utf-8")

    if data.get("schema_version") != "1.0.0":
        fail("schema_version must be 1.0.0")
    if data.get("component_id") != "STEGVERSE-LLM-ADAPTER-ECOSYSTEM-CHAT-RUNTIME":
        fail("component_id mismatch")
    if data.get("repository") != "StegVerse-org/LLM-adapter":
        fail("repository mismatch")
    if data.get("source_of_truth") != "docs/ECOSYSTEM_CHAT_MIRROR_HANDOFF.md":
        fail("source_of_truth must remain the Ecosystem Chat mirror handoff")
    if data.get("authority_effect") != "NONE":
        fail("VERSION.json must not grant authority")
    if data.get("credential_authority") != "TV/TVC":
        fail("credential authority must remain TV/TVC")
    if data.get("github_token_runtime_authority") is not False:
        fail("GitHub token runtime authority must remain false")
    if data.get("third_party_production_authority") is not False:
        fail("third-party production authority must remain false")

    stage = data.get("version_stage")
    if stage not in {"DEVELOPMENT", "RELEASE_CANDIDATE", "RELEASED"}:
        fail(f"unsupported version_stage: {stage}")
    release = data.get("release", {})
    if stage == "RELEASED":
        if not release.get("tag") or not release.get("commit") or not release.get("release_evidence"):
            fail("RELEASED requires exact tag, commit, and release evidence")
    else:
        if release.get("tag") is not None or release.get("commit") is not None:
            fail("non-released component must not claim release tag or commit")

    capabilities = {entry.get("capability_id"): entry for entry in data.get("released_capabilities", [])}
    binding = capabilities.get("LLMA-SOVEREIGN-LOCAL-MODEL-BINDING-019")
    if not binding:
        fail("released sovereign binding capability is missing")
    expected = {
        "state": "COMPLETE_RELEASED",
        "merge_commit": "8be63bfd2eddae4092b945032de956e4e9a63576",
        "workflow_run": 31342485740,
        "artifact_id": 9046241885,
    }
    for key, value in expected.items():
        if binding.get(key) != value:
            fail(f"released binding evidence drift: {key}")

    runtime = data.get("runtime", {})
    activation = data.get("activation", {})
    if runtime.get("state") != "PENDING":
        fail("runtime state must remain PENDING until same-execution proof exists")
    if runtime.get("next_required_state") != "RECOVERY_THEN_SAME_EXECUTION_PROOF":
        fail("runtime next-required-state drift")
    if activation.get("state") != "PENDING":
        fail("activation must remain PENDING until verified receipt exists")
    if activation.get("required_receipt") != "receipts/ecosystem-chat-live-activation.verified.json":
        fail("activation receipt contract drift")

    required_handoff_markers = [
        "production_activation_state: ACTIVE_MACHINE_CONTINUATION_RECOVERY_THEN_SAME_EXECUTION_PROOF",
        "LLMA-SOVEREIGN-LOCAL-MODEL-BINDING-019 COMPLETE_RELEASED",
        "github_token_required: false",
        "credential_authority: TV/TVC",
    ]
    for marker in required_handoff_markers:
        if marker not in handoff:
            fail(f"handoff marker missing: {marker}")

    print("LLM_ADAPTER_COMPONENT_VERSION=PASS")
    print(f"COMPONENT_VERSION={data['component_version']}")
    print(f"VERSION_STAGE={stage}")
    print("RUNTIME_STATE=PENDING")
    print("ACTIVATION_STATE=PENDING")
    print("AUTHORITY_EFFECT=NONE")


if __name__ == "__main__":
    main()
