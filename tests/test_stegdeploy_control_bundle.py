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
    persisted = json.loads((root / ".stegverse-source-manifest.json").read_text())
    assert persisted["schema"] == "stegverse.sovereign-control-plane-bundle/v1"


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


def test_activate_resident_binds_vendor_stegos_cvk_and_durable_kv_root(monkeypatch, tmp_path: Path) -> None:
    state = tmp_path / "state"
    control = tmp_path / "control"
    (control / "scripts").mkdir(parents=True)
    (control / "scripts" / "bootstrap_sovereign_runtime.py").write_text("# bootstrap\n")
    (control / ".stegverse-source-manifest.json").write_text(json.dumps({"schema":"stegverse.sovereign-control-plane-bundle/v1"}) + "\n")
    (control / "vendor" / "StegOS" / "stegos").mkdir(parents=True)
    (control / "vendor" / "StegOS" / "stegos" / "intr_backbone.py").write_text("# intr\n")
    (control / "vendor" / "continuity-vault-kit" / "runtime").mkdir(parents=True)
    (control / "vendor" / "continuity-vault-kit" / "runtime" / "kv_interlock_endpoint.py").write_text("# kv\n")
    (control / "vendor" / "StegVerse-Healer" / "app").mkdir(parents=True)
    (control / "vendor" / "StegVerse-Healer" / "data").mkdir(parents=True)
    (control / "vendor" / "StegVerse-Healer" / "docs").mkdir(parents=True)
    (control / "vendor" / "StegVerse-Healer" / "app" / "dispatch_orchestrators.py").write_text("# dispatch\n")
    (control / "vendor" / "StegVerse-Healer" / "data" / "orchestrator_targets.json").write_text("{}\n")
    (control / "vendor" / "StegVerse-Healer" / "docs" / "HEALER_MIRROR_HANDOFF.md").write_text("# handoff\n")
    (control / "vendor" / "TV" / "scripts").mkdir(parents=True)
    (control / "vendor" / "TV" / "docs").mkdir(parents=True)
    (control / "vendor" / "TV" / "scripts" / "tv_run_resident_operational_proof.py").write_text("# proof\n")
    (control / "vendor" / "TV" / "docs" / "TV_OPERATIONAL_PROOF_SCHEMA.json").write_text("{}\n")
    (control / "vendor" / "TVC" / "scripts").mkdir(parents=True)
    (control / "vendor" / "TVC" / "tools").mkdir(parents=True)
    (control / "vendor" / "TVC" / "TVC_MIRROR_HANDOFF.md").write_text("# handoff\n")
    (control / "vendor" / "TVC" / "scripts" / "activate_coinbase_intr_resident.py").write_text("# activate\n")
    (control / "vendor" / "TVC" / "tools" / "hil_intr_lifecycle_intake.py").write_text("# intake\n")
    monkeypatch.setattr(mod, "STATE_DIR", state)
    monkeypatch.setattr(mod, "_resident_control_root", lambda: control)

    observed = {}
    def fake_run(command, **kwargs):
        observed["env"] = kwargs["env"]
        return type("Result", (), {
            "returncode": 0,
            "stdout": json.dumps({"state":"COMPLETE"}) + "\n",
            "stderr": "",
        })()

    monkeypatch.setattr(mod.subprocess, "run", fake_run)
    result = mod._activate_resident_control_plane()

    assert result["state"] == "COMPLETE"
    assert result["stegos_source_bound"] is True
    assert result["kv_source_bound"] is True
    assert result["healer_source_bound"] is True
    assert result["tv_source_bound"] is True
    assert result["tvc_source_bound"] is True
    assert result["repository_root_map_bound"] is True
    assert result["resident_source_manifest_bound"] is True
    assert result["kv_root_bound"] is True
    assert observed["env"]["STEGVERSE_STEGOS_ROOT"] == str(control / "vendor" / "StegOS")
    assert observed["env"]["STEGVERSE_KV_SOURCE_ROOT"] == str(control / "vendor" / "continuity-vault-kit")
    assert observed["env"]["STEGVERSE_HEALER_ROOT"] == str(control / "vendor" / "StegVerse-Healer")
    assert observed["env"]["STEGVERSE_TV_ROOT"] == str(control / "vendor" / "TV")
    assert observed["env"]["STEGVERSE_TVC_ROOT"] == str(control / "vendor" / "TVC")
    roots = json.loads(observed["env"]["STEGVERSE_REPO_ROOTS_JSON"])
    assert roots["StegVerse-Labs/StegVerse-Healer"] == str(control / "vendor" / "StegVerse-Healer")
    assert roots["StegVerse-Labs/TV"] == str(control / "vendor" / "TV")
    assert roots["StegVerse-Labs/TVC"] == str(control / "vendor" / "TVC")
    assert roots["StegVerse-Labs/StegOS"] == str(control / "vendor" / "StegOS")
    assert observed["env"]["STEGVERSE_KV_ROOT"] == str((state / "resident-kv").resolve())
    assert observed["env"]["STEGVERSE_HEARTBEAT_SOURCE_ROOT"] == str(control)
    assert observed["env"]["STEGVERSE_LLM_ADAPTER_ROOT"] == str(mod.ROOT)
    assert observed["env"]["STEGVERSE_RESIDENT_SOURCE_MANIFEST"] == str(control / ".stegverse-source-manifest.json")
    assert result["heartbeat_source_root_bound"] is True
    assert result["llm_adapter_root_bound"] is True
