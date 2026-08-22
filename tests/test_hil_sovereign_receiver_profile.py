from __future__ import annotations

from llm_adapter.hil_sovereign_receiver_profile import (
    SovereignHILProfileError,
    apply_sovereign_hil_receiver_profile,
)


def test_non_sovereign_runtime_is_inert_and_machine_independent():
    env = {}
    result = apply_sovereign_hil_receiver_profile(env)
    assert result["state"] == "INACTIVE_NON_SOVEREIGN_RUNTIME"
    assert result["participant_machine_required"] is False
    assert result["developer_machine_required"] is False
    assert "STEGVERSE_HIL_INTAKE_ENABLED" not in env


def test_sovereign_runtime_maps_carrier_state_into_hil_receiver():
    env = {
        "STEGVERSE_RUNTIME_PROFILE": "sovereign-carrier",
        "STEGVERSE_SOVEREIGN_STATE_DURABLE": "true",
        "STEGVERSE_SOVEREIGN_STATE_DIR": "/var/lib/stegverse",
    }
    result = apply_sovereign_hil_receiver_profile(env)
    assert result["state"] == "ACTIVE_SOVEREIGN_RECEIVER"
    assert env["STEGVERSE_HIL_INTAKE_ENABLED"] == "true"
    assert env["STEGVERSE_HIL_DATA_DIR"] == "/var/lib/stegverse/hil-v1.1"
    assert env["STEGVERSE_STORAGE_DURABLE_ACROSS_RESTARTS"] == "true"
    assert result["credential_authority"] == "TV/TVC"
    assert result["third_party_runtime_required"] is False


def test_sovereign_runtime_fails_closed_without_durability_attestation():
    env = {
        "STEGVERSE_RUNTIME_PROFILE": "sovereign-carrier",
        "STEGVERSE_SOVEREIGN_STATE_DIR": "/var/lib/stegverse",
    }
    try:
        apply_sovereign_hil_receiver_profile(env)
    except SovereignHILProfileError as exc:
        assert str(exc) == "sovereign_state_durability_not_attested"
    else:
        raise AssertionError("expected fail-closed durability error")


def test_sovereign_runtime_rejects_temporary_state_root():
    env = {
        "STEGVERSE_RUNTIME_PROFILE": "sovereign-carrier",
        "STEGVERSE_SOVEREIGN_STATE_DURABLE": "true",
        "STEGVERSE_SOVEREIGN_STATE_DIR": "/tmp/stegverse",
    }
    try:
        apply_sovereign_hil_receiver_profile(env)
    except SovereignHILProfileError as exc:
        assert str(exc) == "sovereign_state_dir_must_not_be_temporary"
    else:
        raise AssertionError("expected temporary-state rejection")
