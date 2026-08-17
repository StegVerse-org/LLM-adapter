#!/usr/bin/env python3
"""Bootstrap, launch, verify, and receipt the sovereign local StegDeploy runtime."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = ROOT / ".stegdeploy"
ENV_FILE = STATE_DIR / "runtime.env"
RECEIPT_FILE = STATE_DIR / "deployment-receipt.json"
COMPOSE_FILE = ROOT / "compose.stegdeploy.yaml"

PROTECTED_KEYS = (
    "STEGVERSE_EXTERNAL_REVIEW_SUBMIT_TOKEN",
    "STEGVERSE_EXTERNAL_REVIEW_RECEIPT_KEY",
    "STEGVERSE_MASTER_RECORDS_TOKEN",
    "STEGVERSE_PROVIDER_TOKEN",
)


def _run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, check=check, text=True, capture_output=True)


def _prepare_env_file() -> None:
    """Create only a non-secret compose env file.

    Protected credentials are never generated here. When a protected capability is
    admitted, TV/TVC must inject its value into the process environment. Missing
    protected values leave the corresponding optional capability disabled/fail-closed.
    """
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    if ENV_FILE.exists():
        protected_on_disk: list[str] = []
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key in PROTECTED_KEYS and value:
                protected_on_disk.append(key)
        if protected_on_disk:
            raise RuntimeError(
                "protected credentials must be injected by TV/TVC at runtime, not stored in .stegdeploy/runtime.env: "
                + ",".join(sorted(protected_on_disk))
            )
    ENV_FILE.write_text(
        "# Non-secret StegDeploy compose defaults only.\n"
        "# Protected values are injected by TV/TVC into the process environment.\n",
        encoding="utf-8",
    )
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
    _prepare_env_file()
    _compose("build")
    _compose("up", "--detach", "--remove-orphans")
    health = _health(url)
    image_id = _compose("images", "--quiet").stdout.strip()
    source = _run("git", "rev-parse", "HEAD", check=False).stdout.strip() or "unknown"
    tv_tvc_protected_values_present = sorted(key for key in PROTECTED_KEYS if os.environ.get(key))
    receipt = {
        "schema": "stegdeploy.deployment-receipt.v2",
        "runtime": "stegverse-local-docker-compose",
        "source_commit": source,
        "image_id": image_id,
        "image_source": "LOCAL_BUILD",
        "registry_pull_required": False,
        "health_url": url,
        "health": health,
        "durable_storage": True,
        "render_dependency": False,
        "manual_build_required": False,
        "manual_credentials_required": False,
        "credential_authority": "TV/TVC",
        "generated_credentials": False,
        "protected_values_injected_by_tvc": tv_tvc_protected_values_present,
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
        _prepare_env_file()
        print(_compose("ps").stdout)
        if RECEIPT_FILE.exists():
            print(RECEIPT_FILE.read_text(encoding="utf-8"))
    else:
        _prepare_env_file()
        _compose("down")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
