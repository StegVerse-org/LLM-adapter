from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

from llm_adapter.web.testclient import TestClient

from llm_adapter.combined_gateway import app
from llm_adapter.hil_intake_v1_1_api import (
    _build_profile_intent,
    _digest_uri,
    _hil_payload_binding,
    _validate_manifest,
)

PRIMARY = "a7b1c62e336b4e244ecf7fdcd10af195401f6c44328de32615b073d2a5c3c462"
PROMPT = "cdff8d2266bb3eefbb6e5d28d9adc548e6c8dfc039debd72fe404f1d0249912c"


def _manifest(pdf: bytes) -> dict:
    return {
        "schema_version": "HIL-RESPONSE-PROVENANCE-v1.1",
        "primary_version": "v1.1",
        "primary_sha256": PRIMARY,
        "protocol_version": "HIL-PROTOCOL-v1.1",
        "prompt_version": "HIL-PROMPT-v1.1",
        "prompt_sha256": PROMPT,
        "response_sha256": hashlib.sha256(pdf).hexdigest(),
        "model": "test-model",
        "provider": "test-provider",
        "generated_at": None,
        "conversation_reference": None,
        "producer_signature": {"state": "UNAVAILABLE", "scheme": None, "value": None, "key_id": None},
    }


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


def _configure(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("STEGVERSE_HIL_INTAKE_ENABLED", "true")
    monkeypatch.setenv("STEGVERSE_HIL_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("STEGVERSE_STORAGE_DURABLE_ACROSS_RESTARTS", "true")
    monkeypatch.setenv("STEGVERSE_HIL_REVIEW_TOKEN", "review-secret")
    monkeypatch.setenv("STEGVERSE_HIL_PUBLICATION_TOKEN", "publication-secret")


def _submit(client: TestClient, consent: str = "public") -> str:
    pdf = b"%PDF-1.7\n1 0 obj\n<< /Type /Catalog >>\nendobj\n%%EOF\n"
    manifest = _manifest(pdf)
    transport_intent = _transport_intent(pdf, manifest)
    response = client.post(
        "/api/hil/submissions",
        files={
            "response_pdf": ("response.pdf", pdf, "application/pdf"),
            "provenance_manifest": ("response.provenance.json", json.dumps(manifest), "application/json"),
            "intr_transport_intent": ("response.intr.json", json.dumps(transport_intent), "application/json"),
        },
        data={
            "participant_identifier": "Participant One",
            "publication_consent": consent,
            "primary_sha256": PRIMARY,
            "model_response_declared_unedited": "true",
            "participant_consent_authority_acknowledged": "true",
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["submission_id"]


def _review(client: TestClient, submission_id: str, decision: str = "ACCEPT_PRIVATE") -> None:
    response = client.post(
        f"/api/hil/submissions/{submission_id}/review-decisions",
        headers={"X-SteGVerse-HIL-Review-Token": "review-secret"},
        data={"decision": decision, "reviewer": "reviewer", "notes": "checked"},
    )
    assert response.status_code == 200, response.text


def _publish(client: TestClient, submission_id: str, response_id: str = "HIL-RESP-2026-0001"):
    return client.post(
        f"/api/hil/submissions/{submission_id}/publication-decisions",
        headers={"X-SteGVerse-HIL-Publication-Token": "publication-secret"},
        data={
            "response_id": response_id,
            "publisher": "authorized-publisher",
            "participant_display_name": "Participant One",
            "artifact_public_path": f"data/hil-responses/{response_id}.pdf",
        },
    )


class HilPublicationApiTests(unittest.TestCase):
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

    def _monkeypatch(self):
        """The monkeypatch methods the module helpers call, each undone after the test."""
        return types.SimpleNamespace(setenv=self._setenv)

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

    def test_publication_requires_private_acceptance(self):
        monkeypatch = self._monkeypatch()
        tmp_path = self._tmp_path()
        _configure(monkeypatch, tmp_path)
        client = TestClient(app)
        submission_id = _submit(client)
        response = _publish(client, submission_id)
        assert response.status_code == 409
        assert response.json()["detail"] == "hil_private_acceptance_required"

    def test_publication_requires_public_or_anonymous_consent(self):
        monkeypatch = self._monkeypatch()
        tmp_path = self._tmp_path()
        _configure(monkeypatch, tmp_path)
        client = TestClient(app)
        submission_id = _submit(client, consent="private")
        _review(client, submission_id)
        response = _publish(client, submission_id)
        assert response.status_code == 409
        assert response.json()["detail"] == "hil_publication_consent_required"

    def test_publication_is_append_only_and_publicly_readable(self):
        monkeypatch = self._monkeypatch()
        tmp_path = self._tmp_path()
        _configure(monkeypatch, tmp_path)
        client = TestClient(app)
        submission_id = _submit(client)
        _review(client, submission_id)
        response = _publish(client, submission_id)
        assert response.status_code == 200, response.text
        record = response.json()
        assert record["schema_version"] == "HIL-PUBLICATION-RECORD-v1"
        assert record["response_id"] == "HIL-RESP-2026-0001"
        assert record["authority"]["public_projection_authorized"] is True
        assert record["authority"]["execution"] is False
        assert record["authority"]["master_record_append"] is False
        assert record["publication_record_sha256"]

        fetched = client.get("/api/hil/publications/HIL-RESP-2026-0001")
        assert fetched.status_code == 200
        assert fetched.json()["publication_record_sha256"] == record["publication_record_sha256"]

        duplicate = _publish(client, submission_id, response_id="HIL-RESP-2026-0002")
        assert duplicate.status_code == 409
        reused_id_submission = _submit(client)
        _review(client, reused_id_submission)
        reused = _publish(client, reused_id_submission, response_id="HIL-RESP-2026-0001")
        assert reused.status_code == 409

    def test_anonymous_publication_suppresses_display_name(self):
        monkeypatch = self._monkeypatch()
        tmp_path = self._tmp_path()
        _configure(monkeypatch, tmp_path)
        client = TestClient(app)
        submission_id = _submit(client, consent="anonymous")
        _review(client, submission_id)
        response = _publish(client, submission_id)
        assert response.status_code == 200
        assert response.json()["participant_display_name"] is None


if __name__ == "__main__":
    unittest.main()
