"""HIL intake is manifest-bound transport (SDK-MANIFEST-COLLAB-INGRESS-CONFORMANCE-001).

Each HIL entry translates its upload into the SDK's
`stegverse.route.hil-intake.v1` manifest, hands it to
`stegverse.manifest_execution.execute_manifest` through `sdk_boundary`, and
returns the SDK's disposition. Without the canonical organization boundary that
disposition is FAIL_CLOSED, and nothing is persisted.
"""
from __future__ import annotations

import hashlib
import inspect
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from llm_adapter.web.testclient import TestClient

from llm_adapter import collab_ingress, hil_intake_v1_1_api, service_gateway, service_gateway_hil_intr
from llm_adapter.combined_gateway import app
from llm_adapter.generated_intr import hil_submission_connector as canonical_intr

PRIMARY = hil_intake_v1_1_api.PRIMARY_SHA256
PROMPT = hil_intake_v1_1_api.PROMPT_SHA256
HIL_ROUTE = "stegverse.route.hil-intake.v1"
PDF = b"%PDF-1.7\nconformance fixture\n%%EOF\n"
PLANTED = {
    "STEGVERSE_TVC_DECISION_RECEIPT": '{"role": "service_gateway_intake", "planted": "tvc-env"}',
    "STEGVERSE_HIL_RECEIPT_KEY": "planted-receipt-key-" + "k" * 32,
    "STEGVERSE_PROVIDER_TOKEN": "planted-provider-token",
    "GITHUB_TOKEN": "ghp_planted",
}


def _canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def _manifest() -> dict:
    return {
        "schema_version": "HIL-RESPONSE-PROVENANCE-v1.1", "primary_version": "v1.1",
        "primary_sha256": PRIMARY, "protocol_version": "HIL-PROTOCOL-v1.1",
        "prompt_version": "HIL-PROMPT-v1.1", "prompt_sha256": PROMPT,
        "response_sha256": hashlib.sha256(PDF).hexdigest(),
        "producer_signature": {"state": "UNAVAILABLE", "scheme": None, "value": None, "key_id": None},
    }


def _intent(manifest: dict) -> dict:
    normalized = hil_intake_v1_1_api._validate_manifest(dict(manifest), manifest["response_sha256"])
    binding = hil_intake_v1_1_api._hil_payload_binding(
        manifest["response_sha256"], hil_intake_v1_1_api._digest_uri(normalized))
    return canonical_intr.build_intent("hil-submission", _canonical(binding),
                                       operation="SUBMIT", operation_id="HIL-CONFORMANCE-001")


def _submit(client: TestClient):
    manifest = _manifest()
    return client.post(
        "/api/hil/submissions",
        files={
            "response_pdf": ("response.pdf", PDF, "application/pdf"),
            "provenance_manifest": ("p.json", json.dumps(manifest).encode(), "application/json"),
            "intr_transport_intent": ("i.json", json.dumps(_intent(manifest)).encode(), "application/json"),
        },
        data={"primary_sha256": PRIMARY, "prompt_sha256": PROMPT,
              "participant_identifier": "participant-private-name"},
    )


class HilIntakeManifestConformanceTests(unittest.TestCase):
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

    def _environment(self):
        tmp_path = self._tmp_path()
        self._setenv("STEGVERSE_HIL_INTAKE_ENABLED", "true")
        self._setenv("STEGVERSE_HIL_DATA_DIR", str(tmp_path))
        self._setenv("STEGVERSE_STORAGE_DURABLE_ACROSS_RESTARTS", "true")
        for key, value in PLANTED.items():
            self._setenv(key, value)

        def refuse(*_args, **_kwargs):
            raise AssertionError("HIL intake must not open a network connection")

        self._setattr("urllib.request.urlopen", refuse)
        self._setattr("socket.create_connection", refuse)
        return tmp_path

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

    def test_refused_without_an_admitted_manifest_and_nothing_persists(self):
        environment = self._environment()
        response = _submit(TestClient(app))
        assert response.status_code == 503
        body = response.json()
        assert body["disposition"] == "FAIL_CLOSED"
        assert body["failure_code"] == collab_ingress.ORGANIZATION_RECEIPT_NOT_OBSERVED
        assert body["failed_predicate"] == collab_ingress.ORGANIZATION_RECEIPT_NOT_OBSERVED_PREDICATE
        for key in ("required_evidence_or_repair", "retry_entrypoint", "next_attempt", "owning_existing_goal"):
            assert body[key], key
        assert body["route_id"] == HIL_ROUTE
        assert body["manifest_bound_before_processing"] is True
        assert body["master_records_gating"] is False
        assert body["local_receipt_is_organization_observation"] is False
        assert body["disposition"] != "ALLOW"
        assert list(environment.iterdir()) == []

    def test_manifest_is_bound_before_any_processing(self):
        environment = self._environment()
        organization_admits_manifests = self._organization_admits_manifests()
        observed = []
        real = hil_intake_v1_1_api._connect

        def connect():
            observed.append(len(organization_admits_manifests))
            return real()

        self._setattr(hil_intake_v1_1_api, "_connect", connect)
        response = _submit(TestClient(app))
        assert response.status_code == 200, response.text
        assert observed and observed[0] == 1
        [manifest] = organization_admits_manifests
        assert manifest["processing"] == {"capability": "hil_intake", "route_id": HIL_ROUTE}
        request = manifest["extensions"]["stegverse_hil_intake_request"]
        assert request["session_ref"] == "HIL-CONFORMANCE-001"
        assert "participant-private-name" not in json.dumps(manifest)
        receipt = response.json()
        assert receipt["sdk_manifest_disposition"]["route_id"] == HIL_ROUTE
        assert receipt["receipt_is_organization_observation"] is False

    def test_canonical_execute_manifest_path_is_used(self):
        environment = self._environment()
        import stegverse.manifest_execution as canonical

        calls = []
        real = canonical.execute_manifest

        def spy(manifest, **kwargs):
            calls.append(manifest)
            return real(manifest, **kwargs)

        self._setattr(canonical, "execute_manifest", spy)
        response = _submit(TestClient(app))
        assert response.json()["canonical_entrypoint"] == "stegverse.manifest_execution.execute_manifest"
        [manifest] = calls
        assert manifest["processing"]["route_id"] == HIL_ROUTE

    def test_no_environment_credential_is_read_or_echoed(self):
        environment = self._environment()
        response = _submit(TestClient(app))
        for value in PLANTED.values():
            assert value not in response.text
        assert response.json()["credential_read_from_environment"] is False
        for function in (collab_ingress.build, collab_ingress.submit, collab_ingress.execute,
                         service_gateway._tvc_credentials, service_gateway._runtime,
                         service_gateway_hil_intr._hil_materialization_disposition):
            source = inspect.getsource(function)
            for marker in ("os.environ", "getenv", "STEGVERSE_HIL_RECEIPT_KEY", "STEGVERSE_TVC_DECISION_RECEIPT"):
                assert marker not in source, (function.__name__, marker)

    def test_caller_cannot_select_processing(self):
        environment = self._environment()
        organization_admits_manifests = self._organization_admits_manifests()
        manifest = _manifest()
        response = TestClient(app).post(
            "/api/hil/submissions",
            files={
                "response_pdf": ("response.pdf", PDF, "application/pdf"),
                "provenance_manifest": ("p.json", json.dumps(manifest).encode(), "application/json"),
                "intr_transport_intent": ("i.json", json.dumps(_intent(manifest)).encode(), "application/json"),
            },
            data={"primary_sha256": PRIMARY, "prompt_sha256": PROMPT,
                  "requested_route": "stegverse.route.ecosystem-chat.v1", "route_id": "caller-route"},
        )
        assert response.status_code == 200
        [handed] = organization_admits_manifests
        assert handed["processing"]["route_id"] == HIL_ROUTE
        assert "caller-route" not in json.dumps(handed)


if __name__ == "__main__":
    unittest.main()
