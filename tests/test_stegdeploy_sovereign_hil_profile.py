from __future__ import annotations

import unittest
from pathlib import Path

from llm_adapter.hil_sovereign_receiver_profile import (
    SovereignHILProfileError,
    apply_sovereign_hil_receiver_profile,
)

ROOT = Path(__file__).resolve().parents[1]
PRODUCTION_DURABLE_ROOT = Path("/var/lib/stegverse")


class StegdeploySovereignHilProfileTests(unittest.TestCase):
    def test_sovereign_profile_activates_existing_hil_intake_on_production_durable_state(self):
        env = {
            "STEGVERSE_RUNTIME_PROFILE": "sovereign-carrier",
            "STEGVERSE_SOVEREIGN_STATE_DURABLE": "true",
            "STEGVERSE_SOVEREIGN_STATE_DIR": str(PRODUCTION_DURABLE_ROOT),
        }
        profile = apply_sovereign_hil_receiver_profile(env)
        assert profile["state"] == "ACTIVE_SOVEREIGN_RECEIVER"
        assert profile["credential_authority"] == "TV/TVC"
        assert profile["credential_requirement"] == "NONE_FOR_PARTICIPANT_INTAKE"
        assert profile["participant_machine_required"] is False
        assert profile["developer_machine_required"] is False
        assert profile["github_hosted_runtime_required"] is False
        assert profile["third_party_runtime_required"] is False
        assert env["STEGVERSE_HIL_INTAKE_ENABLED"] == "true"
        assert env["STEGVERSE_HIL_DATA_DIR"] == "/var/lib/stegverse/hil-v1.1"
        assert env["STEGVERSE_STORAGE_DURABLE_ACROSS_RESTARTS"] == "true"

    def test_temporary_state_root_remains_rejected(self):
        env = {
            "STEGVERSE_RUNTIME_PROFILE": "sovereign-carrier",
            "STEGVERSE_SOVEREIGN_STATE_DURABLE": "true",
            "STEGVERSE_SOVEREIGN_STATE_DIR": "/tmp/hil-must-fail",
        }
        try:
            apply_sovereign_hil_receiver_profile(env)
        except SovereignHILProfileError as exc:
            assert str(exc) == "sovereign_state_dir_must_not_be_temporary"
        else:
            raise AssertionError("temporary HIL custody root must fail closed")

    def test_native_launcher_declares_sovereign_profile_before_gateway_import(self):
        from scripts import stegdeploy_native_gateway as native
        durable = Path("/var/lib/stegverse")
        native_env = native.child_env(durable_root=durable, evaluator_enabled=False, evaluator_upstream="",
                                      tls_cert=None, tls_key=None, env={})
        assert native_env["STEGVERSE_RUNTIME_PROFILE"] == "sovereign-carrier"
        assert native_env["STEGVERSE_SOVEREIGN_STATE_DURABLE"] == "true"
        assert native_env["STEGVERSE_SOVEREIGN_STATE_DIR"] == str(durable)
        assert native_env["STEGVERSE_SERVICE_GATEWAY_STORAGE_ROOT"] == str(durable)

    def test_profile_does_not_require_second_hil_public_process(self):
        combined = (ROOT / "llm_adapter/combined_gateway.py").read_text(encoding="utf-8")
        deployed = (ROOT / "llm_adapter/deployed_gateway.py").read_text(encoding="utf-8")
        assert "app.include_router(hil_intake_router)" in combined
        assert "from llm_adapter.combined_gateway import app" in deployed


if __name__ == "__main__":
    unittest.main()
