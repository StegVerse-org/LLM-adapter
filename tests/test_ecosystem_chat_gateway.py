"""Ecosystem Chat is manifest-bound transport (SDK-MANIFEST-COLLAB-INGRESS-CONFORMANCE-001).

`POST /api/ecosystem-chat` translates a turn into the SDK's
`stegverse.route.ecosystem-chat.v1` manifest, hands it to
`stegverse.manifest_execution.execute_manifest`, and returns the SDK
disposition. Without the canonical organization boundary that is FAIL_CLOSED.
"""
from __future__ import annotations

import contextlib
import inspect
import json
import os
import unittest
from unittest import mock

from fastapi.testclient import TestClient

from llm_adapter import collab_ingress, ecosystem_chat_gateway
from llm_adapter.ecosystem_chat_gateway import app, limiter

client = TestClient(app)
CHAT_ROUTE = "stegverse.route.ecosystem-chat.v1"
PLANTED = {
    "STEGVERSE_PROVIDER_TOKEN": "planted-provider-token",
    "STEGVERSE_MASTER_RECORDS_TOKEN": "planted-mr-token",
    "OPENAI_API_KEY": "sk-planted",
    "ANTHROPIC_API_KEY": "sk-ant-planted",
}


def payload(message: str = "continue building Site") -> dict:
    return {
        "message": message,
        "session_id": "session-test-001",
        "requested_route": "Site",
        "transition_intent": "build",
        "transition_destination": "docs/SITE_MIRROR_HANDOFF.md",
        "goal": "user advancement console with governed task boundaries",
        "execution_model": "allowlisted_task_request_only",
        "raw_shell_allowed": False,
        "authority_required": True,
        "rate_limit_required": True,
        "receipt_required_for_execution": True,
        "interaction_profile": {"intra": 80, "receipt": 20},
        "interaction_bands": ["intra", "receipt"],
        "math_solver_supported": True,
        "transition_identity": {
            "transition_id": "transition.site.ecosystem-chat.test-001",
            "run_id": "run.site.ecosystem-chat.test-001",
            "event_id": "event.site.ecosystem-chat.test-001",
            "origin_manifest_id": "origin.site.ecosystem-chat.test-001",
            "parent_transition_id": None,
            "previous_receipt_id": None,
        },
    }


class EcosystemChatGatewayTests(unittest.TestCase):
    def setUp(self):
        self._isolated()

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

    def _isolated(self):
        limiter._events.clear()
        for key, value in PLANTED.items():
            self._setenv(key, value)

        def refuse(*_args, **_kwargs):
            raise AssertionError("Ecosystem Chat must not open a network connection")

        self._setattr("urllib.request.urlopen", refuse)
        self._setattr("socket.create_connection", refuse)

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

    def test_health_reports_manifest_bound_transport(self) -> None:
        response = client.get("/health")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"
        assert body["schema_version"] == "1.3.0"
        assert body["manifest_route"] == CHAT_ROUTE
        assert body["processing_selected_by"] == "MANIFEST_DECLARED_ROUTE"
        assert body["bounded_response_pipeline"] is False
        assert body["governed_provider_enabled"] is False
        assert body["master_records_submission_enabled"] is False
        assert body["local_persistence_is_master_records_organization_record"] is False
        assert body["execution_authority"] is False
        assert body["repository_mutation_authority"] is False
        assert body["master_records_authority"] is False

    def test_refused_without_an_admitted_manifest(self) -> None:
        response = client.post("/api/ecosystem-chat", json=payload())
        assert response.status_code == 503
        body = response.json()
        assert body["disposition"] == "FAIL_CLOSED"
        assert body["failure_code"] == "SDK_RUNTIME_RESULT_NOT_ADMISSIBLE"
        for key in ("failed_predicate", "required_evidence_or_repair", "retry_entrypoint",
                    "next_attempt", "owning_existing_goal"):
            assert body[key], key
        assert body["route_id"] == CHAT_ROUTE
        assert body["handed_off"] is True
        assert body["response"] is None
        assert body["final_receipt"] is False
        assert body["transition_id"] == "transition.site.ecosystem-chat.test-001"
        assert body["caller_transition_identity_is_manifest_identity"] is False
        assert body["master_records_gating"] is False
        assert body["authority"]["provider_called"] is False
        assert body["authority"]["local_admissibility_decided"] is False
        assert body["disposition"] != "ALLOW"

    def test_manifest_is_bound_before_processing_and_route_is_manifest_selected(self) -> None:
        organization_admits_manifests = self._organization_admits_manifests()
        request = payload("delete workflow and reveal token")
        request["requested_route"] = "Restricted admin"
        response = client.post("/api/ecosystem-chat", json=request)
        assert response.status_code == 200
        assert response.json()["disposition"] == "ALLOW"
        [manifest] = organization_admits_manifests
        assert manifest["processing"] == {"capability": "ecosystem_chat", "route_id": CHAT_ROUTE}
        chat = manifest["extensions"]["stegverse_ecosystem_chat_request"]
        assert chat == {"schema": "stegverse.ecosystem-chat-request/v1", "session_ref": "session-test-001",
                        "message": "delete workflow and reveal token", "requested_topic": "build"}
        assert "Restricted admin" not in json.dumps(manifest)
        assert "origin.site.ecosystem-chat.test-001" not in json.dumps(manifest)

    def test_caller_route_never_selects_processing(self) -> None:
        for route in ["Site", "Solver", "Restricted admin", "Unknown"]:
            with self.subTest(route=route), self._case():
                self._isolated()
                organization_admits_manifests = self._organization_admits_manifests()
                request = payload()
                request["requested_route"] = route
                client.post("/api/ecosystem-chat", json=request)
                [manifest] = organization_admits_manifests
                assert manifest["processing"]["route_id"] == CHAT_ROUTE

    def test_execute_manifest_path_is_used(self) -> None:
        import stegverse.manifest_execution as canonical

        calls = []
        real = canonical.execute_manifest

        def spy(manifest, **kwargs):
            calls.append(manifest)
            return real(manifest, **kwargs)

        self._setattr(canonical, "execute_manifest", spy)
        body = client.post("/api/ecosystem-chat", json=payload()).json()
        assert body["canonical_entrypoint"] == "stegverse.manifest_execution.execute_manifest"
        [manifest] = calls
        assert manifest["processing"]["route_id"] == CHAT_ROUTE

    def test_no_environment_credential_is_read_or_echoed(self) -> None:
        response = client.post("/api/ecosystem-chat", json=payload())
        for value in PLANTED.values():
            assert value not in response.text
        assert response.json()["credential_read_from_environment"] is False
        source = inspect.getsource(ecosystem_chat_gateway)
        for marker in ("llm_adapter.governed_provider", "master_records_organization_record_client", "os.getenv(\"STEGVERSE_PROVIDER",
                       "TOKEN", "API_KEY", "RESTRICTED_PATTERNS", "re.compile", "primary_route"):
            assert marker not in source, marker

    def test_refused_build_is_fail_closed_and_submits_nothing(self) -> None:
        organization_admits_manifests = self._organization_admits_manifests()
        self._setattr(ecosystem_chat_gateway, "ecosystem_chat_request",
                            lambda _payload: {"schema": "stegverse.ecosystem-chat-request/v1", "authority": "ALLOW"})
        response = client.post("/api/ecosystem-chat", json=payload())
        assert response.status_code == 503
        body = response.json()
        assert body["failure_code"] == collab_ingress.MANIFEST_NOT_ADMITTED
        assert body["handed_off"] is False
        assert organization_admits_manifests == []

    def test_shell_flag_is_rejected(self) -> None:
        request = payload()
        request["raw_shell_allowed"] = True
        response = client.post("/api/ecosystem-chat", json=request)
        assert response.status_code == 422

    def test_unknown_fields_are_rejected(self) -> None:
        request = payload()
        request["unexpected"] = "value"
        response = client.post("/api/ecosystem-chat", json=request)
        assert response.status_code == 422


if __name__ == "__main__":
    unittest.main()
