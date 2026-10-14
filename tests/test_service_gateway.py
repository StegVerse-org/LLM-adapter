import contextlib
import hashlib
import json
import os
import shutil
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

from fastapi.testclient import TestClient

from llm_adapter import service_gateway
from llm_adapter.service_gateway import app

HIL_ROUTE = "stegverse.route.hil-intake.v1"


def _tvc_receipt():
    return {
        "role": "service_gateway_intake",
        "admissible": True,
        "binding_matched": True,
        "allowed_keys": [
            "service-gateway/hil-intake/storage-root",
            "service-gateway/hil-intake/receipt-key",
        ],
        "denied_keys": [],
        "decision_id": "sha256:test-decision",
        "policy_hash": "sha256:test-policy",
    }


def _plant_env_credentials(monkeypatch, tmp_path):
    """What used to configure the gateway. It must now be ignored."""
    monkeypatch.setenv("STEGVERSE_TVC_DECISION_RECEIPT", json.dumps(_tvc_receipt()))
    monkeypatch.setenv("STEGVERSE_HIL_STORAGE_ROOT", str(tmp_path))
    monkeypatch.setenv("STEGVERSE_HIL_RECEIPT_KEY", "x" * 64)


def _bind_tvc_source(monkeypatch, tmp_path):
    """A TV/TVC-sourced credential binding, which this repository does not have."""
    monkeypatch.setattr(service_gateway, "_tvc_credentials", lambda: {
        "tvc": _tvc_receipt(), "key": b"x" * 64, "storage_root": str(tmp_path)})


def _no_network(monkeypatch):
    def refuse(*_args, **_kwargs):
        raise AssertionError("the HIL gateway must not open a network connection")
    monkeypatch.setattr("urllib.request.urlopen", refuse)


PDF = b"%PDF-1.7\nfixture\n%%EOF\n"


def _intake(client, pdf=PDF):
    metadata = {
        "packet_id": "research-packet-001",
        "document_hash": "sha256:" + hashlib.sha256(pdf).hexdigest(),
        "protocol": "HIL-RESPONSE-PACKET-v1",
    }
    return client.post("/v1/hil/intake", files={"document": ("experiment.pdf", pdf, "application/pdf")},
                       data={"metadata": json.dumps(metadata)})


def _site_submission(client, pdf=b"%PDF-1.7\nsite fixture\n%%EOF\n"):
    manifest = {
        "schema_version": "HIL-RESPONSE-PROVENANCE-v1.1",
        "primary_version": "v1.1",
        "primary_sha256": "a7b1c62e336b4e244ecf7fdcd10af195401f6c44328de32615b073d2a5c3c462",
        "protocol_version": "HIL-PROTOCOL-v1.1",
        "prompt_version": "HIL-PROMPT-v1.1",
        "prompt_sha256": "cdff8d2266bb3eefbb6e5d28d9adc548e6c8dfc039debd72fe404f1d0249912c",
        "response_sha256": hashlib.sha256(pdf).hexdigest(),
    }
    return client.post(
        "/api/hil/submissions",
        files={
            "response_pdf": ("response.pdf", pdf, "application/pdf"),
            "provenance_manifest": ("response.pdf.provenance.json", json.dumps(manifest), "application/json"),
        },
        data={
            "participant_identifier": "not_provided",
            "publication_consent": "not_provided",
            "primary_sha256": manifest["primary_sha256"],
            "prompt_sha256": manifest["prompt_sha256"],
            "model_response_declared_unedited": "true",
            "participant_consent_authority_acknowledged": "true",
        },
    ), manifest


class ServiceGatewayTests(unittest.TestCase):
    @contextlib.contextmanager
    def _case(self):
        """A fresh tmp_path and cleanups for each parametrized case."""
        with contextlib.ExitStack() as stack:
            self._stack, self._tmp = stack, None
            try:
                yield
            finally:
                self._stack, self._tmp = None, None

    def _cleanup(self, function, *args, **kwargs):
        stack = getattr(self, "_stack", None)
        if stack is not None:
            stack.callback(function, *args, **kwargs)
        else:
            self.addCleanup(function, *args, **kwargs)

    def _tmp_path(self):
        """tmp_path equivalent: a fresh directory for this test, removed afterwards."""
        if getattr(self, "_tmp", None) is None:
            self._tmp = Path(tempfile.mkdtemp())
            self._cleanup(shutil.rmtree, self._tmp, ignore_errors=True)
        return self._tmp

    def _setattr(self, target, *args, raising=True):
        """monkeypatch.setattr equivalent: dotted-path or (object, name) form, undone after the test."""
        if isinstance(target, str):
            patcher = mock.patch(target, *args, create=not raising)
        else:
            patcher = mock.patch.object(target, *args, create=not raising)
        patcher.start()
        self._cleanup(patcher.stop)

    def _setenv(self, name, value):
        """monkeypatch.setenv equivalent: os.environ is restored after the test."""
        patcher = mock.patch.dict(os.environ, {name: str(value)})
        patcher.start()
        self._cleanup(patcher.stop)

    def _monkeypatch(self):
        """The monkeypatch methods the module helpers call, each undone after the test."""
        return types.SimpleNamespace(setattr=self._setattr, setenv=self._setenv)

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

    def test_readiness_fails_closed_without_tvc_credential_source(self):
        monkeypatch = self._monkeypatch()
        tmp_path = self._tmp_path()
        _plant_env_credentials(monkeypatch, tmp_path)
        client = TestClient(app)
        for path in ("/ready", "/api/hil/readiness"):
            response = client.get(path)
            assert response.status_code == 503
            assert response.json()["detail"] == "TVC_CREDENTIAL_SOURCE_NOT_BOUND"

    def test_without_canonical_boundary_the_sdk_disposition_is_returned_and_nothing_persists(self):
        for submit in ["intake", "site"]:
            with self.subTest(submit=submit), self._case():
                monkeypatch = self._monkeypatch()
                tmp_path = self._tmp_path()
                _plant_env_credentials(monkeypatch, tmp_path)
                _no_network(monkeypatch)
                client = TestClient(app)
                response = _intake(client) if submit == "intake" else _site_submission(client)[0]
                assert response.status_code == 503
                body = response.json()
                assert body["disposition"] == "FAIL_CLOSED"
                assert body["failure_code"] == "SDK_RUNTIME_RESULT_NOT_ADMISSIBLE"
                assert body["route_id"] == HIL_ROUTE
                assert body["handed_off"] is True
                assert body["canonical_entrypoint"] == "stegverse.manifest_execution.execute_manifest"
                assert body["credential_read_from_environment"] is False
                assert list(tmp_path.iterdir()) == []

    def test_admitted_manifest_still_fails_closed_without_tvc_credential_source(self):
        for submit in ["intake", "site"]:
            with self.subTest(submit=submit), self._case():
                monkeypatch = self._monkeypatch()
                tmp_path = self._tmp_path()
                organization_admits_manifests = self._organization_admits_manifests()
                _plant_env_credentials(monkeypatch, tmp_path)
                _no_network(monkeypatch)
                client = TestClient(app)
                response = _intake(client) if submit == "intake" else _site_submission(client)[0]
                assert response.status_code == 503
                body = response.json()
                assert body["disposition"] == "FAIL_CLOSED"
                assert body["failure_code"] == "TVC_CREDENTIAL_SOURCE_NOT_BOUND"
                assert body["sdk_disposition"] == "ALLOW"
                assert "x" * 64 not in response.text
                assert list(tmp_path.iterdir()) == []
                [manifest] = organization_admits_manifests
                assert manifest["processing"]["route_id"] == HIL_ROUTE

    def test_pdf_intake_is_durable_and_idempotent_once_admitted_and_tvc_bound(self):
        monkeypatch = self._monkeypatch()
        tmp_path = self._tmp_path()
        organization_admits_manifests = self._organization_admits_manifests()
        _bind_tvc_source(monkeypatch, tmp_path)
        client = TestClient(app)
        first = _intake(client)
        assert first.status_code == 200
        receipt = first.json()
        assert receipt["status"] == "SUBMISSION_ACCEPTED"
        assert receipt["document_hash"] == "sha256:" + hashlib.sha256(PDF).hexdigest()
        assert receipt["signature"].startswith("hmac-sha256:")
        assert (tmp_path / "packets" / "research-packet-001" / "document.pdf").read_bytes() == PDF
        assert (tmp_path / "receipts" / "research-packet-001.json").exists()

        duplicate = _intake(client)
        assert duplicate.status_code == 200
        assert duplicate.json() == receipt
        assert len(organization_admits_manifests) == 2

    def test_site_submission_contract_once_admitted_and_tvc_bound(self):
        monkeypatch = self._monkeypatch()
        tmp_path = self._tmp_path()
        organization_admits_manifests = self._organization_admits_manifests()
        _bind_tvc_source(monkeypatch, tmp_path)
        response, manifest = _site_submission(TestClient(app))
        assert response.status_code == 200
        receipt = response.json()
        assert receipt["schema_version"] == "HIL-RECEIVER-RECEIPT-v2"
        assert receipt["submitted_file_sha256"] == manifest["response_sha256"]
        assert receipt["chain_validation_state"] == "PRIMARY_PROMPT_RESPONSE_CHAIN_VERIFIED"
        assert receipt["receiver_signature"].startswith("hmac-sha256:")
        material = dict(receipt)
        receipt_hash = material.pop("receipt_sha256")
        assert receipt_hash == hashlib.sha256(
            json.dumps(material, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

    def test_intake_scope_cannot_use_provider_keys(self):
        receipt = _tvc_receipt()
        receipt["allowed_keys"].append("service-gateway/provider/token")
        receipt["denied_keys"] = ["service-gateway/provider/token"]
        with self.assertRaisesRegex(RuntimeError, "tvc_intake_scope_invalid"):
            service_gateway._validate_tvc_receipt(receipt)


if __name__ == "__main__":
    unittest.main()
