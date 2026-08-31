#!/usr/bin/env python3
"""Native sovereign Service Gateway launcher.

This is the host-native primary topology for deployment-local StegVerse runtime
composition. Docker Compose remains a compatibility/fallback method.

The launcher never turns local process start or local TLS health into a public
route claim. TV/TVC retains credential authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import ssl
import subprocess
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
PROTECTED_KEYS = (
    "STEGVERSE_EXTERNAL_REVIEW_SUBMIT_TOKEN",
    "STEGVERSE_EXTERNAL_REVIEW_RECEIPT_KEY",
    "STEGVERSE_MASTER_RECORDS_TOKEN",
    "STEGVERSE_PROVIDER_TOKEN",
)
HOSTED_ENV = ("GITHUB_ACTIONS","RENDER","RENDER_SERVICE_ID","VERCEL","CF_PAGES","CLOUDFLARE_WORKERS")


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in ("", "0", "false", "no")


def state_root(env: dict[str, str] | None = None) -> Path:
    values = os.environ if env is None else env
    override = values.get("STEGVERSE_SERVICE_GATEWAY_NATIVE_STATE_ROOT")
    if override:
        return Path(override).expanduser().resolve()
    if sys.platform == "win32":
        base = Path(values.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local")))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(values.get("XDG_STATE_HOME", str(Path.home() / ".local" / "state")))
    return (base / "stegverse" / "service-gateway").resolve()


def paths(env: dict[str, str] | None = None) -> tuple[Path, Path, Path]:
    root = state_root(env)
    return root / "native.pid", root / "native.log", root / "native-deployment-receipt.json"


def reject_hosted(env: dict[str, str] | None = None) -> None:
    values = os.environ if env is None else env
    found = [name for name in HOSTED_ENV if truthy(values.get(name))]
    if found:
        raise RuntimeError("hosted_runtime_forbidden:" + ",".join(found))


def _inside_repo(path: Path) -> bool:
    try:
        path.resolve().relative_to(ROOT.resolve())
        return True
    except ValueError:
        return False


def validate_tls(cert_file: Path, key_file: Path) -> str:
    cert = cert_file.expanduser().resolve()
    key = key_file.expanduser().resolve()
    if not cert.is_file() or not key.is_file():
        raise RuntimeError("tls_material_missing")
    if _inside_repo(key):
        raise RuntimeError("tls_private_key_must_not_be_stored_in_repository")
    if key.stat().st_mode & 0o077:
        raise RuntimeError("tls_private_key_permissions_must_be_owner_only")
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    try:
        context.load_cert_chain(certfile=str(cert), keyfile=str(key))
    except Exception as exc:
        raise RuntimeError("tls_certificate_private_key_pair_invalid") from exc
    pem = cert.read_text(encoding="utf-8")
    start = pem.find("-----BEGIN CERTIFICATE-----")
    end_marker = "-----END CERTIFICATE-----"
    end = pem.find(end_marker, start)
    if start < 0 or end < 0:
        raise RuntimeError("tls_certificate_pem_invalid")
    der = ssl.PEM_cert_to_DER_cert(pem[start:end + len(end_marker)])
    return "sha256:" + hashlib.sha256(der).hexdigest()


def child_env(
    *,
    durable_root: Path,
    evaluator_enabled: bool,
    evaluator_upstream: str,
    tls_cert: Path | None,
    tls_key: Path | None,
    env: dict[str, str] | None = None,
) -> dict[str, str]:
    values = dict(os.environ if env is None else env)
    values.update({
        "STEGVERSE_DATA_DIR": str(durable_root),
        "STEGVERSE_SERVICE_GATEWAY_STORAGE_ROOT": str(durable_root),
        "STEGVERSE_RUNTIME_PROFILE": "sovereign-carrier",
        "STEGVERSE_SOVEREIGN_STATE_DURABLE": "true",
        "STEGVERSE_SOVEREIGN_STATE_DIR": str(durable_root),
        "STEGVERSE_STORAGE_DURABLE_ACROSS_RESTARTS": "true",
        "STEGVERSE_RESIDENT_RENDEZVOUS_ENABLED": "true",
        "STEGVERSE_RESIDENT_RENDEZVOUS_ROOT": str(durable_root / "resident-rendezvous"),
        "STEGVERSE_EVALUATOR_INTR_ENABLED": "true" if evaluator_enabled else "false",
        "STEGVERSE_EVALUATOR_INTR_UPSTREAM": evaluator_upstream if evaluator_enabled else "",
    })
    if tls_cert and tls_key:
        values["STEGDEPLOY_NATIVE_TLS_CERT_FILE"] = str(tls_cert.expanduser().resolve())
        values["STEGDEPLOY_NATIVE_TLS_KEY_FILE"] = str(tls_key.expanduser().resolve())
    else:
        values.pop("STEGDEPLOY_NATIVE_TLS_CERT_FILE", None)
        values.pop("STEGDEPLOY_NATIVE_TLS_KEY_FILE", None)
    return values


def local_health(port: int, tls: bool) -> dict:
    url = ("https" if tls else "http") + f"://127.0.0.1:{port}/health"
    context = ssl._create_unverified_context() if tls else None
    last = "not_attempted"
    for _ in range(30):
        try:
            with urllib.request.urlopen(url, timeout=3, context=context) as response:
                return {"url": url, "status": response.status, "body": json.loads(response.read().decode("utf-8"))}
        except Exception as exc:
            last = str(exc)
            time.sleep(1)
    raise RuntimeError("native_gateway_health_failed:" + last)


def write_receipt(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = dict(value)
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
    body["receipt_sha256"] = hashlib.sha256(canonical).hexdigest()
    path.write_text(json.dumps(body, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _pid_alive(pid: int) -> bool:
    if pid <= 1:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def read_pid(pid_file: Path) -> int | None:
    try:
        pid = int(pid_file.read_text(encoding="utf-8").strip())
        return pid if _pid_alive(pid) else None
    except Exception:
        return None


def start(
    *,
    host: str,
    port: int,
    durable_root: Path,
    evaluator_enabled: bool,
    evaluator_upstream: str,
    tls_cert: Path | None = None,
    tls_key: Path | None = None,
) -> dict:
    reject_hosted()
    if not 1 <= port <= 65535:
        raise RuntimeError("port_invalid")
    if bool(tls_cert) != bool(tls_key):
        raise RuntimeError("tls_cert_key_pair_required")
    fingerprint = validate_tls(tls_cert, tls_key) if tls_cert and tls_key else None

    pid_file, log_file, receipt_file = paths()
    pid_file.parent.mkdir(parents=True, exist_ok=True)
    existing = read_pid(pid_file)
    if existing:
        raise RuntimeError("native_gateway_already_running")

    durable_root = durable_root.expanduser().resolve()
    durable_root.mkdir(parents=True, exist_ok=True)
    env = child_env(
        durable_root=durable_root,
        evaluator_enabled=evaluator_enabled,
        evaluator_upstream=evaluator_upstream,
        tls_cert=tls_cert,
        tls_key=tls_key,
    )
    log_handle = log_file.open("ab", buffering=0)
    process = subprocess.Popen(
        [sys.executable, str(Path(__file__).resolve()), "serve", "--host", host, "--port", str(port)],
        cwd=ROOT,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        start_new_session=True,
        close_fds=True,
    )
    pid_file.write_text(str(process.pid) + "\n", encoding="utf-8")
    try:
        health = local_health(port, bool(tls_cert))
    except Exception:
        try:
            os.kill(process.pid, signal.SIGTERM)
        except OSError:
            pass
        raise
    receipt = {
        "schema": "stegdeploy.native-sovereign-gateway-receipt/v1",
        "state": "LOCAL_NATIVE_GATEWAY_READY",
        "runtime": "HOST_NATIVE_PYTHON_UVICORN",
        "process_id": process.pid,
        "host": host,
        "port": port,
        "health": health,
        "durable_storage": True,
        "durable_root": str(durable_root),
        "resident_rendezvous_enabled": True,
        "resident_rendezvous_root": str(durable_root / "resident-rendezvous"),
        "resident_rendezvous_execution_authority": "NONE",
        "evaluator_intr_enabled": evaluator_enabled,
        "evaluator_intr_upstream": evaluator_upstream if evaluator_enabled else None,
        "same_host_evaluator_loopback": evaluator_enabled and evaluator_upstream.startswith("http://127.0.0.1:"),
        "tls_enabled": bool(tls_cert),
        "tls_certificate_sha256": fingerprint,
        "tls_private_key_material_recorded": False,
        "tls_private_key_path_recorded": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "docker_required": False,
        "third_party_runtime_required": False,
        "production_public_route_observed": False,
        "public_certificate_hostname_verified": False,
        "authority_effect": "LOCAL_NATIVE_RUNTIME_ONLY",
    }
    write_receipt(receipt_file, receipt)
    return receipt


def stop() -> dict:
    pid_file, _, receipt_file = paths()
    pid = read_pid(pid_file)
    if pid:
        os.kill(pid, signal.SIGTERM)
        for _ in range(50):
            if not _pid_alive(pid):
                break
            time.sleep(0.1)
    try:
        pid_file.unlink()
    except FileNotFoundError:
        pass
    return {"state":"STOPPED","prior_pid":pid,"receipt_ref":str(receipt_file)}


def status() -> dict:
    pid_file, log_file, receipt_file = paths()
    pid = read_pid(pid_file)
    receipt = None
    try:
        receipt = json.loads(receipt_file.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {"state":"RUNNING" if pid else "STOPPED","pid":pid,"log_ref":str(log_file),"receipt":receipt}


def serve(host: str, port: int) -> None:
    import uvicorn
    cert = os.environ.get("STEGDEPLOY_NATIVE_TLS_CERT_FILE")
    key = os.environ.get("STEGDEPLOY_NATIVE_TLS_KEY_FILE")
    uvicorn.run(
        "llm_adapter.deployed_gateway:app",
        host=host,
        port=port,
        ssl_certfile=cert,
        ssl_keyfile=key,
        proxy_headers=False,
        server_header=False,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    start_p = sub.add_parser("start")
    start_p.add_argument("--host", default="127.0.0.1")
    start_p.add_argument("--port", type=int, default=8000)
    start_p.add_argument("--durable-root", type=Path, default=state_root() / "data")
    start_p.add_argument("--enable-evaluator-intr", action="store_true", default=truthy(os.environ.get("STEGVERSE_EVALUATOR_INTR_ENABLED")))
    start_p.add_argument("--evaluator-upstream", default=os.environ.get("STEGVERSE_EVALUATOR_INTR_UPSTREAM", "http://127.0.0.1:8765/intr/evaluator"))
    start_p.add_argument("--tls-cert-file", type=Path, default=Path(os.environ["STEGDEPLOY_NATIVE_TLS_CERT_FILE"]) if os.environ.get("STEGDEPLOY_NATIVE_TLS_CERT_FILE") else None)
    start_p.add_argument("--tls-key-file", type=Path, default=Path(os.environ["STEGDEPLOY_NATIVE_TLS_KEY_FILE"]) if os.environ.get("STEGDEPLOY_NATIVE_TLS_KEY_FILE") else None)

    serve_p = sub.add_parser("serve")
    serve_p.add_argument("--host", required=True)
    serve_p.add_argument("--port", required=True, type=int)

    sub.add_parser("status")
    sub.add_parser("stop")
    args = parser.parse_args()

    if args.command == "start":
        print(json.dumps(start(
            host=args.host, port=args.port, durable_root=args.durable_root,
            evaluator_enabled=args.enable_evaluator_intr,
            evaluator_upstream=args.evaluator_upstream,
            tls_cert=args.tls_cert_file, tls_key=args.tls_key_file,
        ), indent=2, sort_keys=True))
    elif args.command == "serve":
        serve(args.host, args.port)
    elif args.command == "status":
        print(json.dumps(status(), indent=2, sort_keys=True))
    else:
        print(json.dumps(stop(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
