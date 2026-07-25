#!/usr/bin/env python3
"""Run a bounded HIL cycle across two real gateway processes.

This produces GitHub-hosted evidence only. It grants no production deployment,
publication, execution, or Master Record authority.
"""
from __future__ import annotations

import hashlib
import json
import os
import secrets
import signal
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE = "http://127.0.0.1:8011"
PRIMARY = "52102cccb9ba9016c76434a64e22031b6a8c3edd3b8806e7b664e609216b2946"
PROMPT = "0ebe215318b4eeeb8ed6422e0954372c314fadc8fac9254e452bc7670a1b9922"
ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports" / "hil-process-cycle"
DATA = ROOT / ".hil-process-cycle-data"


def request_json(path: str, *, method: str = "GET", headers: dict[str, str] | None = None,
                 body: bytes | None = None, content_type: str | None = None) -> dict:
    request_headers = dict(headers or {})
    if content_type:
        request_headers["Content-Type"] = content_type
    req = Request(BASE + path, data=body, headers=request_headers, method=method)
    try:
        with urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {path} failed: {exc.code}: {detail}") from exc
    except URLError as exc:
        raise RuntimeError(f"{method} {path} failed: {exc}") from exc


def multipart(fields: dict[str, str], files: dict[str, tuple[str, bytes, str]]) -> tuple[bytes, str]:
    boundary = "----stegverse-" + secrets.token_hex(18)
    chunks: list[bytes] = []
    for name, value in fields.items():
        chunks.extend([
            f"--{boundary}\r\n".encode(),
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode(),
            value.encode(), b"\r\n",
        ])
    for name, (filename, payload, media_type) in files.items():
        chunks.extend([
            f"--{boundary}\r\n".encode(),
            f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'.encode(),
            f"Content-Type: {media_type}\r\n\r\n".encode(),
            payload, b"\r\n",
        ])
    chunks.append(f"--{boundary}--\r\n".encode())
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def start_gateway(log_name: str, env: dict[str, str]) -> tuple[subprocess.Popen[bytes], object]:
    log = (REPORTS / log_name).open("wb")
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "llm_adapter.combined_gateway:app",
         "--host", "127.0.0.1", "--port", "8011"],
        cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT,
    )
    for _ in range(40):
        if process.poll() is not None:
            log.close()
            raise RuntimeError(f"gateway exited early; inspect {log_name}")
        try:
            readiness = request_json("/api/hil/readiness")
            if readiness:
                return process, log
        except RuntimeError:
            time.sleep(0.25)
    stop_gateway(process, log)
    raise RuntimeError("gateway readiness timeout")


def stop_gateway(process: subprocess.Popen[bytes], log: object) -> None:
    if process.poll() is None:
        process.send_signal(signal.SIGTERM)
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
    log.close()


def canonical_hash(payload: dict) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def main() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    DATA.mkdir(parents=True, exist_ok=True)
    review_token = secrets.token_urlsafe(48)
    publication_token = secrets.token_urlsafe(48)
    assert review_token != publication_token
    env = os.environ.copy()
    env.update({
        "STEGVERSE_HIL_INTAKE_ENABLED": "true",
        "STEGVERSE_STORAGE_DURABLE_ACROSS_RESTARTS": "true",
        "STEGVERSE_HIL_DATA_DIR": str(DATA.resolve()),
        "STEGVERSE_HIL_REVIEW_TOKEN": review_token,
        "STEGVERSE_HIL_PUBLICATION_TOKEN": publication_token,
        "STEGVERSE_ALLOWED_ORIGINS": BASE,
    })

    pdf = b"%PDF-1.7\n1 0 obj\n<< /Type /Catalog >>\nendobj\n%%EOF\n"
    response_hash = hashlib.sha256(pdf).hexdigest()
    manifest = {
        "schema_version": "HIL-RESPONSE-PROVENANCE-v1",
        "primary_version": "v0.5",
        "primary_sha256": PRIMARY,
        "protocol_version": "HIL-PROTOCOL-v1.0",
        "prompt_version": "HIL-PROMPT-v1.0",
        "prompt_sha256": PROMPT,
        "response_sha256": response_hash,
        "model": "github-process-cycle-model",
        "provider": "github-process-cycle-provider",
        "generated_at": "2026-07-25T00:00:00Z",
        "conversation_reference": "github-process-cycle",
        "producer_signature": {"state": "UNAVAILABLE", "scheme": None, "value": None, "key_id": None},
    }

    first, first_log = start_gateway("gateway-first.log", env)
    try:
        readiness_before = request_json("/api/hil/readiness")
        body, content_type = multipart(
            {
                "participant_identifier": "GitHub Controlled Participant",
                "publication_consent": "public",
                "primary_sha256": PRIMARY,
                "model_response_declared_unedited": "true",
                "participant_consent_authority_acknowledged": "true",
            },
            {
                "response_pdf": ("response.pdf", pdf, "application/pdf"),
                "provenance_manifest": ("response.provenance.json", json.dumps(manifest).encode(), "application/json"),
            },
        )
        receiver = request_json("/api/hil/submissions", method="POST", body=body, content_type=content_type)
    finally:
        stop_gateway(first, first_log)

    second, second_log = start_gateway("gateway-restart.log", env)
    try:
        readiness_after = request_json("/api/hil/readiness")
        submission_id = receiver["submission_id"]
        persisted = request_json(
            f"/api/hil/submissions/{submission_id}/review-state",
            headers={"X-SteGVerse-HIL-Review-Token": review_token},
        )
        body, content_type = multipart(
            {"decision": "ACCEPT_PRIVATE", "reviewer": "github-process-reviewer", "notes": "bounded proof"}, {}
        )
        review = request_json(
            f"/api/hil/submissions/{submission_id}/review-decisions", method="POST",
            headers={"X-SteGVerse-HIL-Review-Token": review_token}, body=body, content_type=content_type,
        )
        body, content_type = multipart(
            {
                "response_id": "HIL-RESP-GITHUB-PROCESS-0001",
                "publisher": "github-process-publisher",
                "participant_display_name": "GitHub Controlled Participant",
                "artifact_public_path": "data/hil-responses/HIL-RESP-GITHUB-PROCESS-0001.pdf",
            }, {},
        )
        publication = request_json(
            f"/api/hil/submissions/{submission_id}/publication-decisions", method="POST",
            headers={"X-SteGVerse-HIL-Publication-Token": publication_token}, body=body, content_type=content_type,
        )
        lookup = request_json("/api/hil/publications/HIL-RESP-GITHUB-PROCESS-0001")
    finally:
        stop_gateway(second, second_log)

    original = next((DATA / "originals").glob("*.pdf")).read_bytes()
    provenance = json.loads(next((DATA / "provenance").glob("*.json")).read_text())
    evidence = {
        "schema_version": "HIL-PROCESS-RESTART-CONTROLLED-CYCLE-v1",
        "observation_scope": "GITHUB_HOSTED_REAL_PROCESS_CONTROLLED_CYCLE",
        "commit_sha": os.environ.get("GITHUB_SHA"),
        "run_id": os.environ.get("GITHUB_RUN_ID"),
        "readiness_before": readiness_before,
        "readiness_after": readiness_after,
        "credential_separation_verified": True,
        "receiver_receipt": receiver,
        "restart_performed": True,
        "post_restart_submission_state": persisted,
        "exact_byte_persistence_verified": original == pdf,
        "provenance_persistence_verified": provenance.get("response_sha256") == response_hash,
        "private_review_receipt": review,
        "publication_record": publication,
        "stable_public_lookup": lookup,
        "production_deployment_claimed": False,
        "site_import_authorized": False,
        "master_record_append_authorized": False,
        "public_acquisition_authorized": False,
        "authority_granted": False,
    }
    required = (
        readiness_before.get("state") == "READY",
        readiness_after.get("state") == "READY",
        receiver.get("schema_version") == "HIL-RECEIVER-RECEIPT-v2",
        evidence["exact_byte_persistence_verified"],
        evidence["provenance_persistence_verified"],
        review.get("schema_version") == "HIL-PRIVATE-REVIEW-RECEIPT-v1",
        publication.get("schema_version") == "HIL-PUBLICATION-RECORD-v1",
        lookup.get("publication_record_sha256") == publication.get("publication_record_sha256"),
    )
    if not all(required):
        raise SystemExit("HIL real-process controlled cycle failed")
    evidence["evidence_sha256"] = canonical_hash(evidence)
    (REPORTS / "hil-process-restart-controlled-cycle.json").write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("HIL_PROCESS_RESTART_CONTROLLED_CYCLE=PASS")
    print(f"HIL_EVIDENCE_SHA256={evidence['evidence_sha256']}")
    print("HIL_AUTHORITY=NONE")


if __name__ == "__main__":
    main()
