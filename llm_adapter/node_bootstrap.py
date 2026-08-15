"""Materialize a portable StegVerse node profile without platform-specific setup."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
from typing import Any


def default_node_root(env: dict[str, str] | None = None) -> Path:
    values = dict(os.environ if env is None else env)
    override = values.get("STEGVERSE_NODE_ROOT")
    if override:
        return Path(override).expanduser().resolve()
    system = platform.system().lower()
    if system == "windows":
        base = Path(values.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif system == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(values.get("XDG_STATE_HOME", Path.home() / ".local" / "state"))
    return (base / "stegverse" / "portable-node").resolve()


def _canonical_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def bootstrap(root: Path | None = None) -> dict[str, Any]:
    node_root = (root or default_node_root()).resolve()
    capability_dir = node_root / "capabilities"
    state_dir = node_root / "state"
    receipt_dir = node_root / "receipts"
    for directory in (capability_dir, state_dir, receipt_dir):
        directory.mkdir(parents=True, exist_ok=True)

    capability = {
        "schema": "stegverse.capability.v1",
        "capability_id": "ecosystem-chat-gateway",
        "version": "1.4.0",
        "lifecycle": "reconstruct-on-demand",
        "authority_effect": "RUNTIME_ONLY",
        "entrypoint": [
            "python", "-m", "uvicorn", "llm_adapter.deployed_gateway:app",
            "--host", "${HOST}", "--port", "${PORT}"
        ],
        "health": {"path": "/health", "timeout_seconds": 3, "attempts": 30},
        "routes": {
            "ecosystem_chat": "/api/ecosystem-chat",
            "math_solver_readiness": "/api/math-solver/v1/readiness",
            "math_solver_solve": "/api/math-solver/v1/solve",
            "node_advertisement": "/api/stegverse-node",
            "hil_readiness": "/api/hil/readiness",
            "hil_submission": "/api/hil/submissions",
            "user_llm": "/user-llm"
        },
        "state": {
            "durable_root": str(state_dir),
            "required_paths": ["stegverse-ecosystem-chat.db", "stegverse-external-review.db"]
        },
        "environment_defaults": {
            "HOST": "127.0.0.1",
            "PORT": "8000",
            "STEGVERSE_DATA_DIR": str(state_dir),
            "STEGVERSE_STORAGE_DURABLE_ACROSS_RESTARTS": "true",
            "STEGVERSE_PROVIDER_ENABLED": "false",
            "STEGVERSE_EXTERNAL_MUTATION_ENABLED": "false"
        },
        "preflight": [["python", "-m", "llm_adapter.custody_worker"]],
        "receipt": {
            "required": True,
            "hash": "sha256",
            "path": str(receipt_dir / "ecosystem-chat-gateway.latest.json")
        },
        "backends": ["process", "wasm", "container", "browser", "peer"],
        "default_backend": "process",
        "portability": {
            "platform_specific_paths_forbidden": True,
            "manual_backend_selection_required": False,
            "durable_state_external_to_executor": True,
            "authorized_host_binding_supported": True
        },
        "credential_boundary": {
            "credential_authority": "TV/TVC",
            "github_token_runtime_authority": "NONE",
            "provider_credentials_in_manifest": False
        },
        "node": {"auto_start": True}
    }
    profile = {
        "schema": "stegverse.portable-node-profile.v1",
        "node_id": "ecosystem-chat-portable-node",
        "capabilities": ["ecosystem-chat-gateway"],
        "manual_capability_selection_required": False,
        "reconstruct_missing_capabilities": True
    }

    capability_path = capability_dir / "ecosystem-chat-gateway.json"
    profile_path = node_root / "node-profile.json"
    capability_path.write_text(json.dumps(capability, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    profile_path.write_text(json.dumps(profile, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    receipt = {
        "schema": "stegverse.portable-node-bootstrap-receipt.v1",
        "node_root": str(node_root),
        "profile": str(profile_path),
        "capability_manifest": str(capability_path),
        "platform": platform.system().lower(),
        "architecture": platform.machine().lower(),
        "manual_action_required": False,
        "authority_effect": "MATERIALIZATION_ONLY"
    }
    receipt["receipt_sha256"] = _canonical_hash(receipt)
    receipt_path = receipt_dir / "bootstrap.latest.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description="Zero-touch StegVerse portable-node bootstrap")
    parser.add_argument("command", nargs="?", default="bootstrap", choices=("bootstrap", "status"))
    parser.add_argument("--root", type=Path)
    args = parser.parse_args()
    root = (args.root or default_node_root()).resolve()
    if args.command == "bootstrap":
        print(json.dumps(bootstrap(root), indent=2, sort_keys=True))
        return 0
    receipt = root / "receipts" / "bootstrap.latest.json"
    if not receipt.exists():
        print(json.dumps({"state": "UNBOOTSTRAPPED", "node_root": str(root)}))
        return 1
    print(receipt.read_text(encoding="utf-8"), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
