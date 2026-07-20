#!/usr/bin/env python3
"""Bootstrap, launch, verify, and receipt the provider-neutral StegDeploy runtime."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = ROOT / ".stegdeploy"
ENV_FILE = STATE_DIR / "runtime.env"
RECEIPT_FILE = STATE_DIR / "deployment-receipt.json"
COMPOSE_FILE = ROOT / "compose.stegdeploy.yaml"


def _run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, check=check, text=True, capture_output=True)


def _write_env() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    existing: dict[str, str] = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                existing[key] = value
    generated = {
        "STEGVERSE_EXTERNAL_REVIEW_SUBMIT_TOKEN": existing.get("STEGVERSE_EXTERNAL_REVIEW_SUBMIT_TOKEN") or secrets.token_urlsafe(32),
        "STEGVERSE_EXTERNAL_REVIEW_RECEIPT_KEY": existing.get("STEGVERSE_EXTERNAL_REVIEW_RECEIPT_KEY") or secrets.token_urlsafe(48),
        "STEGVERSE_MASTER_RECORDS_TOKEN": existing.get("STEGVERSE_MASTER_RECORDS_TOKEN") or secrets.token_urlsafe(32),
        "STEGVERSE_PROVIDER_TOKEN": existing.get("STEGVERSE_PROVIDER_TOKEN") or secrets.token_urlsafe(32),
    }
    ENV_FILE.write_text("\n".join(f"{k}={v}" for k, v in generated.items()) + "\n", encoding="utf-8")
    os.chmod(ENV_FILE, 0o600)


def _compose(*args: str) -> subprocess.CompletedProcess[str]:
    return _run("docker", "compose", "--env-file", str(ENV_FILE), "-f", str(COMPOSE_FILE), *args)


def _health(url: str, attempts: int = 30) -> dict[str, object]:
    last_error = "unknown"
    for _ in range(attempts):
        try:
            with urllib.request.urlopen(url, timeout=3) as response:
                body = response.read().decode("utf-8")
                return {"status": response.status, "body": json.loads(body)}
        except Exception as exc:  # noqa: BLE001
            last_error = str(exc)
            time.sleep(2)
    raise RuntimeError(f"health check failed: {last_error}")


def deploy(url: str) -> None:
    _write_env()
    _compose("up", "--build", "--detach", "--remove-orphans")
    health = _health(url)
    image_id = _compose("images", "--quiet").stdout.strip()
    source = _run("git", "rev-parse", "HEAD", check=False).stdout.strip() or "unknown"
    receipt = {
        "schema": "stegdeploy.deployment-receipt.v1",
        "runtime": "provider-neutral-docker-compose",
        "source_commit": source,
        "image_id": image_id,
        "health_url": url,
        "health": health,
        "durable_storage": True,
        "render_dependency": False,
        "authority_effect": "RUNTIME_DEPLOYMENT_ONLY",
    }
    canonical = json.dumps(receipt, sort_keys=True, separators=(",", ":")).encode()
    receipt["receipt_sha256"] = hashlib.sha256(canonical).hexdigest()
    RECEIPT_FILE.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("deploy", "status", "stop"))
    parser.add_argument("--health-url", default="http://127.0.0.1:8000/health")
    args = parser.parse_args()
    if args.command == "deploy":
        deploy(args.health_url)
    elif args.command == "status":
        print(_compose("ps").stdout)
        if RECEIPT_FILE.exists():
            print(RECEIPT_FILE.read_text(encoding="utf-8"))
    else:
        _compose("down")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
