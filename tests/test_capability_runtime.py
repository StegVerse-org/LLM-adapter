from __future__ import annotations

import json
from pathlib import Path

import pytest

from llm_adapter.capability_runtime import CapabilityError, load_manifest, resolve_environment, write_receipt

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "runtime/capabilities/ecosystem-chat-gateway.json"


def test_manifest_declares_ephemeral_reconstruction() -> None:
    manifest = load_manifest(MANIFEST)
    assert manifest["lifecycle"] == "reconstruct-on-demand"
    assert manifest["default_backend"] == "process"
    assert "container" in manifest["backends"]
    assert manifest["authority_effect"] == "RUNTIME_ONLY"


def test_environment_externalizes_durable_state(tmp_path: Path) -> None:
    manifest = load_manifest(MANIFEST)
    env = resolve_environment(manifest, {"STEGVERSE_DATA_DIR": str(tmp_path), "PORT": "9123"})
    assert env["STEGVERSE_DATA_DIR"] == str(tmp_path)
    assert env["STEGVERSE_TRANSITION_DB"].startswith(str(tmp_path))
    assert env["STEGVERSE_EXTERNAL_REVIEW_DB"].startswith(str(tmp_path))
    assert env["STEGVERSE_PROVIDER_ENABLED"] == "false"


def test_manifest_fails_closed_when_required_fields_missing(tmp_path: Path) -> None:
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps({"schema": "stegverse.capability.v1"}), encoding="utf-8")
    with pytest.raises(CapabilityError):
        load_manifest(path)


def test_receipt_is_hashed(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    manifest = load_manifest(MANIFEST)
    manifest["receipt"]["path"] = str(tmp_path / "receipt.json")
    monkeypatch.setattr("llm_adapter.capability_runtime.ROOT", Path("/"))
    path = write_receipt(manifest, {"schema": "test", "ephemeral_execution": True})
    receipt = json.loads(path.read_text(encoding="utf-8"))
    assert len(receipt["receipt_sha256"]) == 64
