from __future__ import annotations

import importlib.util
from pathlib import Path

from scripts.verify_generated_hil_intr import verify


ROOT = Path(__file__).parents[1]
ARTIFACT = ROOT / "llm_adapter/generated_intr/hil_submission_connector.py"
MANIFEST = ROOT / "llm_adapter/generated_intr/hil_submission_connector.manifest.json"


def _module():
    spec = importlib.util.spec_from_file_location("generated_hil_intr_under_test", ARTIFACT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_generated_hil_intr_source_projection_is_hash_and_profile_bound():
    verify(ARTIFACT, MANIFEST)


def test_generated_hil_intr_covers_complete_pre_tvc_chain():
    connector = _module()
    binding = connector.canonical_json({"schema": "stegverse.hil.intr_payload_binding/v1"}).encode()
    ingress = connector.build_intent("hil-submission", binding, operation="SUBMIT", operation_id="HIL-TEST")
    received = connector.build_receipt(
        ingress, hop_index=1, receipt_id="R1", boundary_identity_ref="hil-ingress",
        recorded_at="2026-08-30T16:00:00Z", prior_receipt_hash=None,
    )
    custody = connector.build_intent(
        "hil-ingress-custody", binding, operation="ACCEPT_CUSTODY",
        operation_id="HIL-TEST:HIL_CUSTODY", prior_receipt_hash=received["receipt_hash"],
    )
    held = connector.build_receipt(
        custody, hop_index=1, receipt_id="R2", boundary_identity_ref="hil-custody",
        recorded_at="2026-08-30T16:00:01Z", prior_receipt_hash=received["receipt_hash"],
    )
    lifecycle = connector.build_intent(
        "hil-tvc-lifecycle", binding, operation="ADMIT_LIFECYCLE",
        operation_id="HIL-TEST:TVC_HIL_LIFECYCLE", prior_receipt_hash=held["receipt_hash"],
    )
    assert lifecycle["destination"]["subsystem"] == "TVC:HIL-Lifecycle"
    assert lifecycle["authority"]["credential_authority"] == "TV/TVC"
    assert lifecycle["authority"]["authority_transfer"] is False
