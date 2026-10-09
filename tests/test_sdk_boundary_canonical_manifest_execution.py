"""F14: the generic manifest surface reaches the SDK's canonical entrypoint.

`sdk_boundary.installed_runtime` used to call
`stegverse.manifest_state_transition_runtime.execute_manifest` with no
organization boundary, so it failed closed for a reason nobody named. It now
calls `stegverse.manifest_execution.execute_manifest`, which resolves the route
from the manifest and the boundary from the source the route binding fixes.
"""
from __future__ import annotations

import inspect
import os
import unittest
from unittest import mock

from stegverse.manifest_builder import build_manifest

from llm_adapter import sdk_boundary


def arguments():
    return {"data": {"probe": True}, "source_framework": "f14-test",
            "source_output_id": "sdk-boundary-canonical-execution",
            "processor_request": {"candidate": {"action": "inspect"}, "judgment": {},
                                  "signal": {}, "execution": {}, "capability": {},
                                  "continuity": {}, "approval": {},
                                  "permission_present": False},
            "created_at": "2026-10-09T00:00:00Z"}


def submit_payload(manifest, **extra):
    payload = {"manifest": manifest, "mode": "TEST", "standing_evidence": {
        "node_endpoint": {"node_id": "f14-node", "recognized": True},
        "generation": 1, "predecessor": None}}
    payload.update(extra)
    return payload


def _no_network(*_args, **_kwargs):
    raise AssertionError("the adapter must not open a network connection")


class CanonicalManifestExecutionTests(unittest.TestCase):
    def setUp(self):
        self.manifest = build_manifest(**arguments())
        patcher = mock.patch("urllib.request.urlopen", _no_network)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_canonical_entrypoint_is_used(self):
        import stegverse.manifest_execution as canonical

        calls = []
        real = canonical.execute_manifest

        def spy(manifest, **kwargs):
            calls.append((manifest, kwargs))
            return real(manifest, **kwargs)

        with mock.patch.object(canonical, "execute_manifest", spy):
            body = sdk_boundary.submit(submit_payload(self.manifest))
        self.assertEqual(len(calls), 1)
        self.assertEqual(sdk_boundary.CANONICAL_ENTRYPOINT,
                         "stegverse.manifest_execution.execute_manifest")
        self.assertEqual(body["canonical_entrypoint"], sdk_boundary.CANONICAL_ENTRYPOINT)
        self.assertIs(body["handed_off"], True)
        source = inspect.getsource(sdk_boundary.installed_runtime)
        self.assertIn("from stegverse.manifest_execution import execute_manifest", source)
        self.assertNotIn("manifest_state_transition_runtime import", source)

    def test_no_boundary_fails_closed_with_evidence(self):
        body = sdk_boundary.submit(submit_payload(self.manifest))
        self.assertEqual(body["disposition"], "FAIL_CLOSED")
        self.assertEqual(body["failure_code"],
                         "CANONICAL_ORGANIZATION_INGRESS_ENDPOINT_NOT_RESOLVED")
        self.assertEqual(body["failed_predicate"],
                         "REGISTERED_CAPABILITY_RESOLVES_TO_CANONICAL_ORGANIZATION_GITHUB_INGRESS_ENDPOINT")
        for key in ("required_evidence_or_repair", "retry_entrypoint", "next_attempt",
                    "owning_existing_goal"):
            self.assertTrue(body[key], key)
        evidence = body["envelope"]["far_side_disposition"]
        self.assertIn("LLM-adapter performs no network read",
                      evidence["canonical_organization_boundary_unavailable"])
        self.assertEqual(evidence["evaluation_boundary"],
                         "SDK_ORGANIZATION_DESTINATION_RESOLUTION")
        for key in ("canonical_manifest_sha256", "wire_manifest_sha256", "request_sha256",
                    "diagnostic_sha256"):
            self.assertTrue(evidence[key], key)
        self.assertIs(body["envelope"]["consequence_executed"], False)
        self.assertNotEqual(body["disposition"], "ALLOW")

    def test_caller_cannot_select_the_runtime_or_boundary(self):
        import stegverse.manifest_execution as canonical

        seen = []
        real = canonical.execute_manifest

        def spy(manifest, **kwargs):
            seen.append((dict(manifest), kwargs))
            return real(manifest, **kwargs)

        chosen = {
            "runtime_binding": "stegverse.manifest_state_transition_runtime.execute_manifest",
            "runtime": "caller-runtime",
            "organization_boundary": {"ingress_endpoint": "https://caller.example/ingress"},
            "canonical_source_fetcher": lambda _b: {"text": "{}"},
            "destination": "https://caller.example/ingress",
        }
        with mock.patch.object(canonical, "execute_manifest", spy):
            body = sdk_boundary.submit(submit_payload(self.manifest, **chosen))
        self.assertEqual(body["failure_code"],
                         "CANONICAL_ORGANIZATION_INGRESS_ENDPOINT_NOT_RESOLVED")
        manifest, kwargs = seen[0]
        self.assertEqual(set(kwargs), {"canonical_source_fetcher"})
        self.assertIs(kwargs["canonical_source_fetcher"],
                      sdk_boundary._no_network_boundary_source)
        for key in chosen:
            self.assertNotIn(key, manifest)
        self.assertNotIn("caller.example", repr(body))

    def test_no_env_derived_credential_or_endpoint(self):
        planted = {"GITHUB_TOKEN": "ghp_planted", "GH_TOKEN": "planted",
                   "STEGVERSE_ORGANIZATION_INGRESS_ENDPOINT": "https://env.example/ingress",
                   "STEGVERSE_ORGANIZATION_BOUNDARY": '{"ingress_endpoint": "https://env.example"}'}
        with mock.patch.dict(os.environ, planted):
            body = sdk_boundary.submit(submit_payload(self.manifest))
        self.assertEqual(body["failure_code"],
                         "CANONICAL_ORGANIZATION_INGRESS_ENDPOINT_NOT_RESOLVED")
        self.assertNotIn("env.example", repr(body))
        self.assertNotIn("planted", repr(body))
        for function in (sdk_boundary.installed_runtime,
                         sdk_boundary._no_network_boundary_source):
            source = inspect.getsource(function)
            for marker in ("os.environ", "getenv", "TOKEN", "Authorization"):
                self.assertNotIn(marker, source)


if __name__ == "__main__":
    unittest.main()
