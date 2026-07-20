"""Reconstruct and supervise ephemeral StegVerse capabilities from manifests."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
from typing import Any
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


class CapabilityError(RuntimeError):
    pass


def _expand(value: str, env: dict[str, str]) -> str:
    result = value
    for key, replacement in env.items():
        result = result.replace("${" + key + "}", replacement)
    return result


def load_manifest(path: str | Path) -> dict[str, Any]:
    manifest_path = Path(path)
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    required = {"schema", "capability_id", "entrypoint", "state", "receipt"}
    missing = sorted(required - data.keys())
    if missing:
        raise CapabilityError(f"manifest missing fields: {missing}")
    if data["schema"] != "stegverse.capability.v1":
        raise CapabilityError("unsupported capability schema")
    return data


def resolve_environment(manifest: dict[str, Any], overrides: dict[str, str] | None = None) -> dict[str, str]:
    env = dict(os.environ)
    for key, value in manifest.get("environment_defaults", {}).items():
        env.setdefault(key, str(value))
    if overrides:
        env.update({key: str(value) for key, value in overrides.items()})
    data_root = Path(_expand(manifest["state"]["durable_root"], env))
    if not data_root.is_absolute():
        data_root = ROOT / data_root
    data_root.mkdir(parents=True, exist_ok=True)
    env["STEGVERSE_DATA_DIR"] = str(data_root)
    env.setdefault("STEGVERSE_TRANSITION_DB", str(data_root / "stegverse-ecosystem-chat.db"))
    env.setdefault("STEGVERSE_EXTERNAL_REVIEW_DB", str(data_root / "stegverse-external-review.db"))
    return env


def _command(parts: list[str], env: dict[str, str]) -> list[str]:
    return [_expand(str(part), env) for part in parts]


def _health(url: str, attempts: int, timeout: int) -> dict[str, Any]:
    last_error = "unknown"
    for _ in range(attempts):
        try:
            with urllib.request.urlopen(url, timeout=timeout) as response:
                body = response.read().decode("utf-8")
                return {"status": response.status, "body": json.loads(body)}
        except Exception as exc:  # noqa: BLE001
            last_error = str(exc)
            time.sleep(1)
    raise CapabilityError(f"capability health check failed: {last_error}")


def write_receipt(manifest: dict[str, Any], payload: dict[str, Any]) -> Path:
    receipt_path = ROOT / manifest["receipt"]["path"]
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    payload["receipt_sha256"] = hashlib.sha256(canonical).hexdigest()
    receipt_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt_path


def reconstruct_process(manifest_path: str | Path, overrides: dict[str, str] | None = None) -> subprocess.Popen[str]:
    manifest = load_manifest(manifest_path)
    env = resolve_environment(manifest, overrides)
    for command in manifest.get("preflight", []):
        subprocess.run(_command(command, env), cwd=ROOT, env=env, check=True, text=True)
    process = subprocess.Popen(
        _command(manifest["entrypoint"], env),
        cwd=ROOT,
        env=env,
        text=True,
    )
    health = manifest["health"]
    url = f"http://127.0.0.1:{env['PORT']}{health['path']}"
    try:
        health_result = _health(url, int(health["attempts"]), int(health["timeout_seconds"]))
    except Exception:
        process.terminate()
        process.wait(timeout=10)
        raise
    write_receipt(
        manifest,
        {
            "schema": "stegverse.capability-reconstruction-receipt.v1",
            "capability_id": manifest["capability_id"],
            "capability_version": manifest["version"],
            "backend": "process",
            "pid": process.pid,
            "health": health_result,
            "durable_root": env["STEGVERSE_DATA_DIR"],
            "ephemeral_execution": True,
            "authority_effect": manifest["authority_effect"],
        },
    )
    return process
