from __future__ import annotations

from pathlib import Path

from llm_adapter.hil_sovereign_receiver_profile import apply_sovereign_hil_receiver_profile

ROOT = Path(__file__).resolve().parents[1]


def test_sovereign_profile_activates_existing_hil_intake_on_durable_state(tmp_path):
    durable = tmp_path / "durable"
    env = {
        "STEGVERSE_RUNTIME_PROFILE": "sovereign-carrier",
        "STEGVERSE_SOVEREIGN_STATE_DURABLE": "true",
        "STEGVERSE_SOVEREIGN_STATE_DIR": str(durable),
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
    assert env["STEGVERSE_HIL_DATA_DIR"] == str((durable / "hil-v1.1").resolve())
    assert env["STEGVERSE_STORAGE_DURABLE_ACROSS_RESTARTS"] == "true"


def test_stegdeploy_compose_declares_sovereign_profile_before_gateway_import():
    text = (ROOT / "compose.stegdeploy.yaml").read_text(encoding="utf-8")
    assert "STEGVERSE_RUNTIME_PROFILE: sovereign-carrier" in text
    assert 'STEGVERSE_SOVEREIGN_STATE_DURABLE: "true"' in text
    assert "STEGVERSE_SOVEREIGN_STATE_DIR: /var/lib/stegverse" in text
    assert "stegverse_gateway_data:/var/lib/stegverse" in text


def test_profile_does_not_require_second_hil_public_process():
    combined = (ROOT / "llm_adapter/combined_gateway.py").read_text(encoding="utf-8")
    deployed = (ROOT / "llm_adapter/deployed_gateway.py").read_text(encoding="utf-8")
    assert "app.include_router(hil_intake_router)" in combined
    assert "from llm_adapter.combined_gateway import app" in deployed
