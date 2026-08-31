#!/usr/bin/env python3
"""Bootstrap, launch, verify, and receipt the sovereign local StegDeploy runtime."""
from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import shutil
import ssl
import stat
import subprocess
import time
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = ROOT / ".stegdeploy"
ENV_FILE = STATE_DIR / "runtime.env"
RECEIPT_FILE = STATE_DIR / "deployment-receipt.json"
COMPOSE_FILE = ROOT / "compose.stegdeploy.yaml"
TLS_COMPOSE_FILE = ROOT / "compose.stegdeploy.tls.yaml"

PROTECTED_KEYS = (
    "STEGVERSE_EXTERNAL_REVIEW_SUBMIT_TOKEN",
    "STEGVERSE_EXTERNAL_REVIEW_RECEIPT_KEY",
    "STEGVERSE_MASTER_RECORDS_TOKEN",
    "STEGVERSE_PROVIDER_TOKEN",
)


def _run(*args: str, check: bool = True, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, check=check, text=True, capture_output=True, env=env)


def _prepare_env_file() -> None:
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


def _compose(*args: str, tls: bool = False, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    command = ["docker", "compose", "--env-file", str(ENV_FILE), "-f", str(COMPOSE_FILE)]
    if tls:
        command.extend(["-f", str(TLS_COMPOSE_FILE)])
    command.extend(args)
    return _run(*command, env=env)


def _health(url: str, attempts: int = 30, *, local_tls_probe: bool = False) -> dict[str, object]:
    last_error = "unknown"
    context = ssl._create_unverified_context() if local_tls_probe else None
    for _ in range(attempts):
        try:
            with urllib.request.urlopen(url, timeout=3, context=context) as response:
                return {"status": response.status, "body": json.loads(response.read().decode("utf-8"))}
        except Exception as exc:
            last_error = str(exc)
            time.sleep(2)
    raise RuntimeError(f"health check failed: {last_error}")


def _write_receipt(receipt: dict[str, object]) -> None:
    canonical = json.dumps(receipt, sort_keys=True, separators=(",", ":")).encode()
    receipt["receipt_sha256"] = hashlib.sha256(canonical).hexdigest()
    RECEIPT_FILE.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))


def _source_commit() -> str:
    return _run("git", "rev-parse", "HEAD", check=False).stdout.strip() or "unknown"


def _protected_values_present() -> list[str]:
    return sorted(key for key in PROTECTED_KEYS if os.environ.get(key))


def _materialize_control_bundle(bundle_path: Path) -> Path:
    bundle = bundle_path.expanduser().resolve()
    if not bundle.is_file():
        raise RuntimeError("resident_control_bundle_missing")
    target = STATE_DIR / "resident-control-plane"
    staging = STATE_DIR / "resident-control-plane.staging"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True, exist_ok=True)
    manifest_name = "stegverse-control-plane-manifest.json"
    with zipfile.ZipFile(bundle) as archive:
        infos = archive.infolist()
        names = [info.filename for info in infos]
        if manifest_name not in names:
            raise RuntimeError("resident_control_bundle_manifest_missing")
        for info in infos:
            path = Path(info.filename)
            if path.is_absolute() or ".." in path.parts:
                raise RuntimeError("resident_control_bundle_path_invalid")
            mode = (info.external_attr >> 16) & 0xFFFF
            if stat.S_ISLNK(mode):
                raise RuntimeError("resident_control_bundle_symlink_rejected")
        manifest = json.loads(archive.read(manifest_name).decode("utf-8"))
        if manifest.get("schema") != "stegverse.sovereign-control-plane-bundle/v1":
            raise RuntimeError("resident_control_bundle_schema_invalid")
        if manifest.get("network_fetch_required") is not False:
            raise RuntimeError("resident_control_bundle_network_policy_invalid")
        if manifest.get("credential_authority") != "TV/TVC":
            raise RuntimeError("resident_control_bundle_credential_authority_invalid")
        if manifest.get("github_token_runtime_authority") != "NONE":
            raise RuntimeError("resident_control_bundle_github_authority_invalid")
        if manifest.get("bundle_grants_authority") is not False:
            raise RuntimeError("resident_control_bundle_authority_invalid")
        declared = {entry.get("path"): entry for entry in manifest.get("files", []) if isinstance(entry, dict)}
        actual = {name for name in names if name != manifest_name and not name.endswith("/")}
        if set(declared) != actual:
            raise RuntimeError("resident_control_bundle_file_set_mismatch")
        for name in sorted(actual):
            data = archive.read(name)
            entry = declared[name]
            if len(data) != entry.get("size"):
                raise RuntimeError("resident_control_bundle_size_mismatch")
            if hashlib.sha256(data).hexdigest() != entry.get("sha256"):
                raise RuntimeError("resident_control_bundle_digest_mismatch")
            destination = staging / Path(name)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
    bootstrap = staging / "scripts" / "bootstrap_sovereign_runtime.py"
    if not bootstrap.is_file():
        raise RuntimeError("resident_control_bundle_bootstrap_missing")
    if target.exists():
        shutil.rmtree(target)
    staging.replace(target)
    return target.resolve()


def _resident_control_root() -> Path | None:
    bundle = str(os.environ.get("STEGVERSE_ORG_CONTROL_BUNDLE") or "").strip()
    if bundle:
        return _materialize_control_bundle(Path(bundle))
    explicit = str(os.environ.get("STEGVERSE_ORG_CONTROL_ROOT") or "").strip()
    candidates = []
    if explicit:
        candidates.append(Path(explicit).expanduser())
    candidates.extend([
        ROOT.parent / ".github",
        ROOT.parent.parent / "StegVerse-Labs" / ".github",
        Path("/opt/stegverse/StegVerse-Labs/.github"),
        Path("/srv/stegverse/StegVerse-Labs/.github"),
    ])
    for candidate in candidates:
        try:
            root = candidate.resolve()
        except Exception:
            continue
        if (root / "scripts" / "bootstrap_sovereign_runtime.py").is_file():
            return root
    return None


def _activate_resident_control_plane() -> dict[str, object]:
    control_root = _resident_control_root()
    if control_root is None:
        return {
            "attempted": False,
            "state": "CONTROL_PLANE_NOT_MATERIALIZED",
            "authority_effect": "NONE",
            "network_fetch_performed": False,
            "github_token_runtime_authority": "NONE",
            "credential_authority": "TV/TVC",
        }

    command = [
        os.environ.get("PYTHON", "python3"),
        str(control_root / "scripts" / "bootstrap_sovereign_runtime.py"),
        "--source-root",
        str(control_root),
        "--skip-post-bootstrap-stegfin",
    ]
    completed = subprocess.run(
        command,
        cwd=control_root,
        check=False,
        text=True,
        capture_output=True,
        timeout=3600,
        env=os.environ.copy(),
    )
    result = None
    for line in reversed([line.strip() for line in (completed.stdout or "").splitlines() if line.strip()]):
        try:
            value = json.loads(line)
        except Exception:
            continue
        if isinstance(value, dict):
            result = value
            break
    return {
        "attempted": True,
        "state": (
            result.get("state")
            if isinstance(result, dict) and isinstance(result.get("state"), str)
            else ("COMPLETE" if completed.returncode == 0 else "INCOMPLETE")
        ),
        "returncode": completed.returncode,
        "control_root": str(control_root),
        "result": result,
        "network_fetch_performed": False,
        "github_token_runtime_authority": "NONE",
        "credential_authority": "TV/TVC",
        "authority_effect": "NONE_LOCAL_POST_DEPLOY_BOOTSTRAP_TRIGGER",
    }


def _inside_repo(path: Path) -> bool:
    try:
        path.relative_to(ROOT)
    except ValueError:
        return False
    return True


def _validate_tls_material(cert_file: Path, key_file: Path) -> str:
    cert_file = cert_file.expanduser().resolve()
    key_file = key_file.expanduser().resolve()
    for label, path in (("certificate", cert_file), ("private_key", key_file)):
        if not path.is_file():
            raise RuntimeError(f"tls_{label}_file_missing")
        if path.stat().st_size <= 0 or path.stat().st_size > 131072:
            raise RuntimeError(f"tls_{label}_file_size_invalid")
    if _inside_repo(key_file):
        raise RuntimeError("tls_private_key_must_not_be_stored_in_repository")
    if key_file.stat().st_mode & 0o077:
        raise RuntimeError("tls_private_key_permissions_must_be_owner_only")

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    try:
        context.load_cert_chain(certfile=str(cert_file), keyfile=str(key_file))
    except Exception as exc:
        raise RuntimeError("tls_certificate_private_key_pair_invalid") from exc

    pem = cert_file.read_text(encoding="utf-8")
    start = pem.find("-----BEGIN CERTIFICATE-----")
    end_marker = "-----END CERTIFICATE-----"
    end = pem.find(end_marker, start)
    if start < 0 or end < 0:
        raise RuntimeError("tls_certificate_pem_invalid")
    der = ssl.PEM_cert_to_DER_cert(pem[start : end + len(end_marker)])
    return "sha256:" + hashlib.sha256(der).hexdigest()


def _validate_public_bind(bind_address: str, port: int) -> None:
    try:
        address = ipaddress.ip_address(bind_address)
    except ValueError as exc:
        raise RuntimeError("stegdeploy_tls_bind_address_invalid") from exc
    if address.version != 4:
        raise RuntimeError("stegdeploy_tls_bind_address_ipv4_required")
    if address.is_loopback:
        raise RuntimeError("stegdeploy_tls_bind_address_must_not_be_loopback")
    if not 1 <= port <= 65535:
        raise RuntimeError("stegdeploy_tls_port_invalid")


def deploy(url: str) -> None:
    _prepare_env_file()
    _compose("build")
    _compose("up", "--detach", "--remove-orphans")
    health = _health(url)
    resident_bootstrap = _activate_resident_control_plane()
    receipt: dict[str, object] = {
        "schema": "stegdeploy.deployment-receipt.v2",
        "runtime": "stegverse-local-docker-compose",
        "source_commit": _source_commit(),
        "image_id": _compose("images", "--quiet").stdout.strip(),
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
        "protected_values_injected_by_tvc": _protected_values_present(),
        "tls_enabled": False,
        "resident_control_plane_bootstrap": resident_bootstrap,
        "authority_effect": "RUNTIME_DEPLOYMENT_ONLY",
    }
    _write_receipt(receipt)


def deploy_tls(*, cert_file: Path, key_file: Path, bind_address: str, port: int) -> None:
    _prepare_env_file()
    _validate_public_bind(bind_address, port)
    certificate_fingerprint = _validate_tls_material(cert_file, key_file)

    compose_env = os.environ.copy()
    compose_env.update(
        {
            "STEGDEPLOY_TLS_CERT_FILE": str(cert_file.expanduser().resolve()),
            "STEGDEPLOY_TLS_KEY_FILE": str(key_file.expanduser().resolve()),
            "STEGDEPLOY_BIND_ADDRESS": bind_address,
            "STEGDEPLOY_PORT": str(port),
        }
    )

    _compose("build", tls=True, env=compose_env)
    _compose("up", "--detach", "--remove-orphans", tls=True, env=compose_env)
    local_health_url = f"https://127.0.0.1:{port}/health"
    health = _health(local_health_url, local_tls_probe=True)
    resident_bootstrap = _activate_resident_control_plane()

    receipt: dict[str, object] = {
        "schema": "stegdeploy.deployment-receipt.v3",
        "runtime": "stegverse-local-docker-compose",
        "source_commit": _source_commit(),
        "image_id": _compose("images", "--quiet", tls=True, env=compose_env).stdout.strip(),
        "image_source": "LOCAL_BUILD",
        "registry_pull_required": False,
        "health_url": local_health_url,
        "health": health,
        "durable_storage": True,
        "render_dependency": False,
        "cloudflare_dependency": False,
        "reverse_proxy_required": False,
        "manual_build_required": False,
        "credential_authority": "TV/TVC",
        "generated_credentials": False,
        "protected_values_injected_by_tvc": _protected_values_present(),
        "tls_enabled": True,
        "tls_termination": "UVICORN_NATIVE",
        "tls_certificate_sha256": certificate_fingerprint,
        "tls_certificate_material_present": True,
        "tls_private_key_material_present": True,
        "tls_private_key_material_recorded": False,
        "tls_private_key_path_recorded": False,
        "tls_material_source": "TV_TVC_RUNTIME_FILES",
        "tls_compose_delivery": "DOCKER_COMPOSE_SECRETS",
        "bind_address": bind_address,
        "public_port": port,
        "local_tls_transport_observed": True,
        "public_certificate_hostname_verified": False,
        "production_public_route_observed": False,
        "resident_control_plane_bootstrap": resident_bootstrap,
        "gateway_execution_authority": "NONE",
        "authority_effect": "LOCAL_TLS_RUNTIME_DEPLOYMENT_ONLY",
    }
    _write_receipt(receipt)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("deploy", "deploy-tls", "status", "stop"))
    parser.add_argument("--health-url", default="http://127.0.0.1:8000/health")
    parser.add_argument("--tls-cert-file", type=Path)
    parser.add_argument("--tls-key-file", type=Path)
    parser.add_argument("--bind-address", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=443)
    args = parser.parse_args()

    if args.command == "deploy":
        deploy(args.health_url)
    elif args.command == "deploy-tls":
        if args.tls_cert_file is None or args.tls_key_file is None:
            parser.error("deploy-tls requires --tls-cert-file and --tls-key-file")
        deploy_tls(
            cert_file=args.tls_cert_file,
            key_file=args.tls_key_file,
            bind_address=args.bind_address,
            port=args.port,
        )
    elif args.command == "status":
        _prepare_env_file()
        print(_compose("ps").stdout)
        if RECEIPT_FILE.exists():
            print(RECEIPT_FILE.read_text(encoding="utf-8"))
    else:
        _prepare_env_file()
        print(_compose("down").stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
