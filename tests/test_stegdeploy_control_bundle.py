from __future__ import annotations

import hashlib
import json
from pathlib import Path
import zipfile

import pytest

from scripts import stegdeploy_bootstrap as mod


def _write_bundle(path: Path, *, tamper: bool = False) -> None:
    files = {
        "scripts/bootstrap_sovereign_runtime.py": b"# bootstrap\n",
        "scripts/run_worker_runtime.py": b"# worker\n",
    }
    manifest = {
        "schema": "stegverse.sovereign-control-plane-bundle/v1",
        "file_count": len(files),
        "files": [
            {
                "path": name,
                "sha256": hashlib.sha256(data).hexdigest(),
                "size": len(data),
            }
            for name, data in sorted(files.items())
        ],
        "network_fetch_required": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "heartbeat_grants_execution_authority": False,
        "bundle_grants_authority": False,
        "authority_effect": "NONE_SOURCE_TRANSPORT_ONLY",
    }
    with zipfile.ZipFile(path, "w") as archive:
        for name, data in files.items():
            archive.writestr(name, (b"tampered\n" if tamper and name.endswith("run_worker_runtime.py") else data))
        archive.writestr(
            "stegverse-control-plane-manifest.json",
            json.dumps(manifest),
        )


def test_materialize_control_bundle_verifies_and_extracts(monkeypatch, tmp_path: Path) -> None:
    state = tmp_path / "state"
    bundle = tmp_path / "control.zip"
    _write_bundle(bundle)
    monkeypatch.setattr(mod, "STATE_DIR", state)

    root = mod._materialize_control_bundle(bundle)

    assert root == (state / "resident-control-plane").resolve()
    assert (root / "scripts" / "bootstrap_sovereign_runtime.py").is_file()


def test_materialize_control_bundle_rejects_digest_tamper(monkeypatch, tmp_path: Path) -> None:
    state = tmp_path / "state"
    bundle = tmp_path / "control.zip"
    _write_bundle(bundle, tamper=True)
    monkeypatch.setattr(mod, "STATE_DIR", state)

    with pytest.raises(RuntimeError, match="digest_mismatch"):
        mod._materialize_control_bundle(bundle)


def test_resident_control_root_prefers_explicit_local_bundle(monkeypatch, tmp_path: Path) -> None:
    state = tmp_path / "state"
    bundle = tmp_path / "control.zip"
    _write_bundle(bundle)
    monkeypatch.setattr(mod, "STATE_DIR", state)
    monkeypatch.setenv("STEGVERSE_ORG_CONTROL_BUNDLE", str(bundle))
    monkeypatch.delenv("STEGVERSE_ORG_CONTROL_ROOT", raising=False)

    root = mod._resident_control_root()

    assert root == (state / "resident-control-plane").resolve()
