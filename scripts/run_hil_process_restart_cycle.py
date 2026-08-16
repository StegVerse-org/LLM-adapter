#!/usr/bin/env python3
"""Run a bounded HIL cycle across two real gateway processes.

This produces validation evidence only. It grants no production deployment,
publication, execution, or Master Record authority. Authentication material for
production HIL execution is owned by TV/TVC; this controlled validation lane uses
non-authorizing process-local fixture values and does not export them.
"""
from __future__ import annotations

import hashlib
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE = "http://127.0.0.1:8011"
PRIMARY = "a7b1c62e336b4e244ecf7fdcd10af195401f6c44328de32615b073d2a5c3c462"
PROMPT = "cdff8d2266bb3eefbb6e5d28d9adc548e6c8dfc039debd72fe404f1d0249912c"
ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports" / "hil-process-cycle"
DATA = ROOT / ".hil-process-cycle-data"

# Validation fixtures are not credentials and are intentionally non-secret. They
# exist only inside the loopback controlled-cycle process. Production HIL review
# and publication credentials MUST be issued/managed by TV/TVC.
VALIDATION_REVIEW_FIXTURE = "HIL-VALIDATION-REVIEW-NONAUTH"
VALIDATION_PUBLICATION_FIXTURE = "HIL-VALIDATION-PUBLICATION-NONAUTH"


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
    boundary = "----stegverse-validation-boundary"
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
    env = os.environ.copy()
    env.update({
        "STEGVERSE_HIL_INTAKE_ENABLED": "true",
        "STEGVERSE_STORAGE_DURABLE_ACROSS_RESTARTS": "true",
        "STEGVERSE_HIL_DATA_DIR": str(DATA.resolve()),
        "STEGVERSE_HIL_REVIEW_TOKEN": VALIDATION_REVIEW_FIXTURE,
        "STEGVERSE_HIL_PUBLICATION_TOKEN": VALIDATION_PUBLICATION_FIXTURE,
        "STEGVERSE_ALLOWED_ORIGINS": BASE,
    })

    pdf = b"%PDF-1.7\n1 0 obj\n<< /Type /Catalog >>\nendobj\n%%EOF\n"
    response_hash = hashlib.sha256(pdf).hexdigest()
    manifest = {
        "schema_version": "HIL-RESPONSE-PROVENANCE-v1.1",
        "primary_version": "v1.1",
        "primary_sha256": PRIMARY,
        "protocol_version": "HIL-PROTOCOL-v1.1",
        "prompt_version": "HIL-PROMPT-v1.1",
        "prompt_sha256": PROMPT,
        "response_sha256": response_hash,
        "model": "stegverse-controlled-cycle-validation",
        "provider": "stegverse-loopback-validation",
        "generated_at": "2026-07-25T00:00:00Z",
        "conversation_reference": "stegverse-controlled-cycle",
        "producer_signature": {"state": "UNAVAILABLE", "scheme": None, "value": None, "key_id": None},
    }

    first, first_log = start_gateway("gateway-first.log", env)
    try:
        readiness_before = request_json("/api/hil/readiness")
        body, content_type = multipart(
            {
                "participant_identifier": "StegVerse Controlled Participant",
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
            headers={"X-SteGVerse-HIL-Review-Token": VALIDATION_REVIEW_FIXTURE},
        )
        body, content_type = multipart(
            {"decision": "ACCEPT_PRIVATE", "reviewer": "stegverse-process-reviewer", "notes": "bounded proof"}, {}
        )
        review = request_json(
            f"/api/hil/submissions/{submission_id}/review-decisions", method="POST",
            headers={"X-SteGVerse-HIL-Review-Token": VALIDATION_REVIEW_FIXTURE}, body=body, content_type=content_type,
        )
        body, content_type = multipart(
            {
                "response_id": "HIL-RESP-STEGVERSE-PROCESS-0001",
                "publisher": "stegverse-process-publisher",
                "participant_display_name": "StegVerse Controlled Participant",
                "artifact_public_path": "data/hil-responses/HIL-RESP-STEGVERSE-PROCESS-0001.pdf",
            }, {},
        )
        publication = request_json(
            f"/api/hil/submissions/{submission_id}/publication-decisions", method="POST",
            headers={"X-SteGVerse-HIL-Publication-Token": VALIDATION_PUBLICATION_FIXTURE}, body=body, content_type=content_type,
        )
        lookup = request_json("/api/hil/publications/HIL-RESP-STEGVERSE-PROCESS-0001")
    finally:
        stop_gateway(second, second_log)

    original = next((DATA / "originals").glob("*.pdf")).read_bytes()
    provenance = json.loads(next((DATA / "provenance").glob("*.json")).read_text())
    evidence = {
        "schema_version": "HIL-PROCESS-RESTART-CONTROLLED-CYCLE-v1",
        "observation_scope": "STEGVERSE_LOOPBACK_REAL_PROCESS_CONTROLLED_CYCLE",
        "commit_sha": os.environ.get("GITHUB_SHA"),
        "run_id": os.environ.get("GITHUB_RUN_ID"),
        "readiness_before": readiness_before,
        "readiness_after": readiness_after,
        "credential_authority": "TV/TVC",
        "validation_fixture_values_are_production_credentials": False,
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
