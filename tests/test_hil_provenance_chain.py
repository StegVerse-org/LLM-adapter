from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from fastapi.testclient import TestClient

from llm_adapter.combined_gateway import app
from llm_adapter.hil_intake_v1_1_api import (
    _build_profile_intent,
    _digest_uri,
    _hil_payload_binding,
    _validate_manifest,
)

PRIMARY = "a7b1c62e336b4e244ecf7fdcd10af195401f6c44328de32615b073d2a5c3c462"
PROMPT = "cdff8d2266bb3eefbb6e5d28d9adc548e6c8dfc039debd72fe404f1d0249912c"


def _manifest(pdf: bytes, prompt_sha256: str = PROMPT) -> bytes:
    return json.dumps({
        "schema_version": "HIL-RESPONSE-PROVENANCE-v1.1",
        "primary_version": "v1.1",
        "primary_sha256": PRIMARY,
        "protocol_version": "HIL-PROTOCOL-v1.1",
        "prompt_version": "HIL-PROMPT-v1.1",
        "prompt_sha256": prompt_sha256,
        "response_sha256": hashlib.sha256(pdf).hexdigest(),
        "model": "test-model",
        "provider": "test-provider",
        "generated_at": "2026-07-23T00:00:00Z",
        "producer_signature": {
            "state": "UNAVAILABLE",
            "scheme": None,
            "value": None,
            "key_id": None,
        },
    }).encode("utf-8")


def _transport_intent(pdf: bytes, manifest: dict) -> dict:
    response_sha = hashlib.sha256(pdf).hexdigest()
    normalized = _validate_manifest(dict(manifest), response_sha)
    provenance_sha = _digest_uri(normalized)
    payload_binding = _hil_payload_binding(response_sha, provenance_sha)
    return _build_profile_intent(
        "hil-submission",
        payload_binding,
        operation="SUBMIT",
        operation_id="HIL-TEST-" + response_sha[:16],
        prior_receipt_hash=None,
    )


def _post(client: TestClient, pdf: bytes, manifest: bytes):
    manifest_obj = json.loads(manifest.decode("utf-8"))
    try:
        transport_intent = _transport_intent(pdf, manifest_obj)
    except Exception:
        transport_intent = _build_profile_intent(
            "hil-submission",
            _hil_payload_binding("0" * 64, "sha256:" + "0" * 64),
            operation="SUBMIT",
            operation_id="HIL-TEST-INVALID-MANIFEST",
            prior_receipt_hash=None,
        )
    return client.post(
        "/api/hil/submissions",
        files={
            "response_pdf": ("response.pdf", pdf, "application/pdf"),
            "provenance_manifest": ("response.provenance.json", manifest, "application/json"),
            "intr_transport_intent": ("response.intr.json", json.dumps(transport_intent).encode("utf-8"), "application/json"),
        },
        data={
            "participant_identifier": "tester",
            "publication_consent": "anonymous",
            "primary_sha256": PRIMARY,
            "model_response_declared_unedited": "true",
            "participant_consent_authority_acknowledged": "true",
        },
    )


class HilProvenanceChainTests(unittest.TestCase):
    def setUp(self):
        self._organization_admitted()

    def _tmp_path(self):
        """tmp_path equivalent: a fresh directory for this test, removed afterwards."""
        if getattr(self, "_tmp", None) is None:
            self._tmp = Path(tempfile.mkdtemp())
            self.addCleanup(shutil.rmtree, self._tmp, ignore_errors=True)
        return self._tmp

    def _setattr(self, target, *args, raising=True):
        """monkeypatch.setattr equivalent: dotted-path or (object, name) form, undone after the test."""
        if isinstance(target, str):
            patcher = mock.patch(target, *args, create=not raising)
        else:
            patcher = mock.patch.object(target, *args, create=not raising)
        patcher.start()
        self.addCleanup(patcher.stop)

    def _setenv(self, name, value):
        """monkeypatch.setenv equivalent: os.environ is restored after the test."""
        patcher = mock.patch.dict(os.environ, {name: str(value)})
        patcher.start()
        self.addCleanup(patcher.stop)

    def _organization_admitted(self):
        """Custody is exercised after an organization-admitted HIL manifest.

        The un-admitted path (FAIL_CLOSED, nothing persisted) is covered in
        tests/test_hil_intake_manifest_conformance.py.
        """
        organization_admits_manifests = self._organization_admits_manifests()
        return organization_admits_manifests

    def _organization_admits_manifests(self):
        """Stand in for an organization that admitted the manifest and recorded it.

        In this repository the canonical organization boundary is never resolved,
        so a collaborative-ingress surface correctly returns FAIL_CLOSED. Tests of
        what a surface does *after* an organization-admitted ALLOW use this far-side
        double. It still validates every manifest with the real SDK contract and
        records what it was handed, so a test can prove the manifest was bound
        before anything else ran.
        """
        from llm_adapter import sdk_boundary

        handed: list[dict] = []

        def admitted(payload):
            manifest = dict(payload["manifest"])
            verdict = sdk_boundary.validate({"manifest": manifest})
            assert verdict["accepted"] is True, verdict
            handed.append(manifest)
            return {
                "schema": sdk_boundary.BOUNDARY_SCHEMA,
                "surface": "MANIFEST_SUBMIT",
                "handed_off": True,
                "disposition": "ALLOW",
                "canonical_entrypoint": sdk_boundary.CANONICAL_ENTRYPOINT,
                "envelope": {"governance_state": "ALLOW", "organization_receipt_observed": True,
                             "reached_sdk_runtime": True, "consequence_executed": False},
                "test_double": "ORGANIZATION_ADMITTED_FAR_SIDE",
                "authority_effect": "NONE_HANDOFF_ONLY",
            }

        self._setattr(sdk_boundary, "submit", admitted)
        return handed

    def test_hil_chain_receipt_and_exact_storage(self):
        tmp_path = self._tmp_path()
        self._setenv("STEGVERSE_HIL_INTAKE_ENABLED", "true")
        self._setenv("STEGVERSE_HIL_DATA_DIR", str(tmp_path))
        self._setenv("STEGVERSE_STORAGE_DURABLE_ACROSS_RESTARTS", "true")
        client = TestClient(app)
        pdf = b"%PDF-1.7\n1 0 obj\n<< /Type /Catalog >>\nendobj\n%%EOF\n"
        response = _post(client, pdf, _manifest(pdf))
        assert response.status_code == 200, response.text
        receipt = response.json()
        assert receipt["schema_version"] == "HIL-RECEIVER-RECEIPT-v2"
        assert receipt["chain_validation_state"] == "PRIMARY_PROMPT_RESPONSE_CHAIN_VERIFIED"
        assert receipt["authority"]["publication"] is False
        assert list((tmp_path / "originals").glob("*.pdf"))[0].read_bytes() == pdf
        assert len(list((tmp_path / "provenance").glob("*.json"))) == 1

    def test_hil_chain_rejects_wrong_prompt(self):
        tmp_path = self._tmp_path()
        self._setenv("STEGVERSE_HIL_INTAKE_ENABLED", "true")
        self._setenv("STEGVERSE_HIL_DATA_DIR", str(tmp_path))
        self._setenv("STEGVERSE_STORAGE_DURABLE_ACROSS_RESTARTS", "true")
        client = TestClient(app)
        pdf = b"%PDF-1.7\n%%EOF\n"
        response = _post(client, pdf, _manifest(pdf, prompt_sha256="incorrect"))
        assert response.status_code == 400
        assert response.json()["detail"] == "provenance_prompt_sha256_mismatch"


if __name__ == "__main__":
    unittest.main()
