#!/usr/bin/env python3
"""Run a complete non-authorizing HIL intake/review/publication cycle across a real restart."""
from __future__ import annotations

import hashlib
import json
import os
import signal
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

PRIMARY = "a7b1c62e336b4e244ecf7fdcd10af195401f6c44328de32615b073d2a5c3c462"
PROMPT = "cdff8d2266bb3eefbb6e5d28d9adc548e6c8dfc039debd72fe404f1d0249912c"
BASE = "http://127.0.0.1:8000"


def canonical_hash(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def start_gateway(log_path: Path) -> subprocess.Popen:
    handle = log_path.open("wb")
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "llm_adapter.combined_gateway:app", "--host", "127.0.0.1", "--port", "8000"],
        stdout=handle,
        stderr=subprocess.STDOUT,
        env=os.environ.copy(),
    )
    for _ in range(40):
        try:
            response = httpx.get(f"{BASE}/api/hil/readiness", timeout=1.0)
            if response.status_code == 200:
                return proc
        except Exception:
            pass
        time.sleep(0.5)
    proc.terminate()
    raise RuntimeError(f"gateway failed to become ready; see {log_path}")


def stop_gateway(proc: subprocess.Popen) -> None:
    if proc.poll() is None:
        proc.send_signal(signal.SIGTERM)
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> None:
    reports = Path(os.getenv("HIL_REPORT_DIR", "reports"))
    reports.mkdir(parents=True, exist_ok=True)
    data_dir = Path(os.environ["STEGVERSE_HIL_DATA_DIR"]).resolve()
    data_dir.mkdir(parents=True, exist_ok=True)

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
        "model": "automated-full-cycle-model",
        "provider": "github-actions-bounded-proof",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "conversation_reference": "HIL-AUTOMATED-FULL-CYCLE-v1",
        "producer_signature": {"state": "UNAVAILABLE", "scheme": None, "value": None, "key_id": None},
    }

    first = start_gateway(reports / "gateway-first.log")
    try:
        readiness_before = httpx.get(f"{BASE}/api/hil/readiness", timeout=10).json()
        submitted = httpx.post(
            f"{BASE}/api/hil/submissions",
            files={
                "response_pdf": ("response.pdf", pdf, "application/pdf"),
                "provenance_manifest": ("response.provenance.json", json.dumps(manifest).encode(), "application/json"),
            },
            data={
                "participant_identifier": "Automated Controlled Participant",
                "publication_consent": "public",
                "primary_sha256": PRIMARY,
                "prompt_sha256": PROMPT,
                "model_response_declared_unedited": "true",
                "participant_consent_authority_acknowledged": "true",
            },
            timeout=20,
        )
        require(submitted.status_code == 200, submitted.text)
        receiver = submitted.json()
        submission_id = receiver["submission_id"]
        require(receiver["submitted_file_sha256"] == response_hash, "receiver hash mismatch")
    finally:
        stop_gateway(first)

    second = start_gateway(reports / "gateway-restart.log")
    try:
        readiness_after = httpx.get(f"{BASE}/api/hil/readiness", timeout=10).json()
        review_state = httpx.get(
            f"{BASE}/api/hil/submissions/{submission_id}/review-state",
            headers={"X-SteGVerse-HIL-Review-Token": os.environ["STEGVERSE_HIL_REVIEW_TOKEN"]},
            timeout=10,
        )
        require(review_state.status_code == 200, review_state.text)
        require(review_state.json()["submission"]["submitted_file_sha256"] == response_hash, "restart lost response hash")

        reviewed = httpx.post(
            f"{BASE}/api/hil/submissions/{submission_id}/review-decisions",
            headers={"X-SteGVerse-HIL-Review-Token": os.environ["STEGVERSE_HIL_REVIEW_TOKEN"]},
            data={"decision": "ACCEPT_PRIVATE", "reviewer": "automated-reviewer", "notes": "bounded proof acceptance"},
            timeout=10,
        )
        require(reviewed.status_code == 200, reviewed.text)
        private_receipt = reviewed.json()

        response_id = "HIL-RESP-AUTOMATED-0001"
        published = httpx.post(
            f"{BASE}/api/hil/submissions/{submission_id}/publication-decisions",
            headers={"X-SteGVerse-HIL-Publication-Token": os.environ["STEGVERSE_HIL_PUBLICATION_TOKEN"]},
            data={
                "response_id": response_id,
                "publisher": "automated-publisher",
                "participant_display_name": "Automated Controlled Participant",
                "artifact_public_path": f"data/hil-responses/{response_id}.pdf",
            },
            timeout=10,
        )
        require(published.status_code == 200, published.text)
        publication = published.json()
        fetched = httpx.get(f"{BASE}/api/hil/publications/{response_id}", timeout=10)
        require(fetched.status_code == 200, fetched.text)
        require(fetched.json()["publication_record_sha256"] == publication["publication_record_sha256"], "stable lookup mismatch")
    finally:
        stop_gateway(second)

    originals = list((data_dir / "originals").glob("*.pdf"))
    manifests = list((data_dir / "provenance").glob("*.json"))
    require(len(originals) == 1 and originals[0].read_bytes() == pdf, "exact response bytes not preserved")
    require(len(manifests) == 1, "provenance manifest not preserved")
    persisted_manifest = json.loads(manifests[0].read_text(encoding="utf-8"))
    require(persisted_manifest["response_sha256"] == response_hash, "persisted provenance hash mismatch")

    with sqlite3.connect(data_dir / "hil-intake.db") as connection:
        counts = {
            "submissions": connection.execute("SELECT COUNT(*) FROM submissions").fetchone()[0],
            "reviews": connection.execute("SELECT COUNT(*) FROM submission_reviews").fetchone()[0],
            "publications": connection.execute("SELECT COUNT(*) FROM publications").fetchone()[0],
        }
    require(counts == {"submissions": 1, "reviews": 1, "publications": 1}, f"unexpected durable counts: {counts}")

    receipt = {
        "schema_version": "HIL-AUTOMATED-FULL-CYCLE-RECEIPT-v1",
        "observation_scope": "GITHUB_HOSTED_EPHEMERAL_FULL_CYCLE_PROOF",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "commit_sha": os.getenv("GITHUB_SHA"),
        "run_id": os.getenv("GITHUB_RUN_ID"),
        "submission_id": submission_id,
        "response_id": response_id,
        "response_sha256": response_hash,
        "provenance_manifest_sha256": canonical_hash(persisted_manifest),
        "receiver_receipt_id": receiver["receipt_id"],
        "private_review_receipt_sha256": private_receipt["review_receipt_sha256"],
        "publication_record_sha256": publication["publication_record_sha256"],
        "readiness_before_restart": readiness_before["state"],
        "readiness_after_restart": readiness_after["state"],
        "actual_process_restart": True,
        "exact_response_bytes_persisted": True,
        "provenance_manifest_persisted": True,
        "accept_private_completed": True,
        "append_only_publication_completed": True,
        "stable_public_lookup_completed": True,
        "durable_counts": counts,
        "external_production_deployment_claimed": False,
        "master_record_release_claimed": False,
        "orchestration_authority_granted": False,
        "authority_effect": "NONE",
    }
    receipt["receipt_sha256"] = canonical_hash(receipt)
    (reports / "hil-automated-full-cycle-receipt-v1.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("HIL_AUTOMATED_FULL_CYCLE=PASS")
    print(f"HIL_RECEIPT_SHA256={receipt['receipt_sha256']}")


if __name__ == "__main__":
    main()
