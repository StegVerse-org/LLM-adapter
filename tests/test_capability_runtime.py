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


def test_reconstruction_closes_on_spawn_and_never_waits_on_health(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    import urllib.error

    from llm_adapter import capability_runtime as mod

    calls = []

    def refuse(*args, **kwargs):
        calls.append(args)
        raise urllib.error.URLError(ConnectionRefusedError(111, "refused"))

    class Process:
        pid = 777

        def terminate(self):
            raise AssertionError("an unobserved capability must not be terminated")

    receipts = []
    monkeypatch.setattr(mod.urllib.request, "urlopen", refuse)
    real_popen = mod.subprocess.Popen

    def spawn(args, *rest, **kwargs):
        # Only the capability entrypoint is faked; anything else (e.g. the
        # platform module on Windows) gets a real process.
        if kwargs.get("cwd") == mod.ROOT and isinstance(args, list):
            return Process()
        return real_popen(args, *rest, **kwargs)

    monkeypatch.setattr(mod.subprocess, "Popen", spawn)
    real_load = mod.load_manifest

    def load_without_preflight(path):
        manifest = real_load(path)
        manifest["preflight"] = []
        return manifest

    monkeypatch.setattr(mod, "load_manifest", load_without_preflight)
    monkeypatch.setattr(mod, "write_receipt", lambda manifest, payload: receipts.append(payload))
    process = mod.reconstruct_process(MANIFEST, {"STEGVERSE_DATA_DIR": str(tmp_path), "PORT": "9123",
                                                 "STEGVERSE_EXECUTION_BACKEND": "process"})
    assert process.pid == 777
    assert len(calls) == 1
    health = receipts[0]["health"]
    assert health["consequence_observation"] == "NOT_AUTHENTICALLY_OBSERVED"
    assert health["reconciliation_entrypoint"] == "GET http://127.0.0.1:9123/health"
    assert health["gates_transition"] is False
    assert receipts[0]["destination_liveness_is_transition_predicate"] is False
