"""Bind the existing HIL v1.1 intake to the StegVerse sovereign carrier."""
from __future__ import annotations

import os
from pathlib import Path
from typing import MutableMapping

PROFILE_SCHEMA = "stegverse.hil.sovereign-receiver-profile.v1"


class SovereignHILProfileError(RuntimeError):
    pass


def apply_sovereign_hil_receiver_profile(environ: MutableMapping[str, str] | None = None) -> dict:
    env = environ if environ is not None else os.environ
    if env.get("STEGVERSE_RUNTIME_PROFILE", "").strip() != "sovereign-carrier":
        return {
            "schema": PROFILE_SCHEMA,
            "state": "INACTIVE_NON_SOVEREIGN_RUNTIME",
            "participant_machine_required": False,
            "developer_machine_required": False,
            "github_hosted_runtime_required": False,
            "third_party_runtime_required": False,
            "authority_granted": False
        }

    if env.get("STEGVERSE_SOVEREIGN_STATE_DURABLE", "").strip().lower() != "true":
        raise SovereignHILProfileError("sovereign_state_durability_not_attested")

    raw_root = env.get("STEGVERSE_SOVEREIGN_STATE_DIR", "").strip()
    if not raw_root:
        raise SovereignHILProfileError("sovereign_state_dir_missing")
    root = Path(raw_root).expanduser().resolve()
    if str(root).startswith("/tmp/") or str(root) == "/tmp" or str(root).startswith("/var/tmp/") or str(root) == "/var/tmp":
        raise SovereignHILProfileError("sovereign_state_dir_must_not_be_temporary")

    hil_root = root / "hil-v1.1"
    env["STEGVERSE_HIL_INTAKE_ENABLED"] = "true"
    env["STEGVERSE_HIL_DATA_DIR"] = str(hil_root)
    env["STEGVERSE_STORAGE_DURABLE_ACROSS_RESTARTS"] = "true"

    return {
        "schema": PROFILE_SCHEMA,
        "state": "ACTIVE_SOVEREIGN_RECEIVER",
        "runtime_profile": "sovereign-carrier",
        "credential_authority": "TV/TVC",
        "credential_requirement": "NONE_FOR_PARTICIPANT_INTAKE",
        "participant_machine_required": False,
        "developer_machine_required": False,
        "github_hosted_runtime_required": False,
        "third_party_runtime_required": False,
        "render_runtime_required": False,
        "publication_authority": False,
        "private_review_authority": False,
        "master_record_authority": False,
        "authority_granted": False
    }
