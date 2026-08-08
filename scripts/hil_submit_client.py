#!/usr/bin/env python3
"""Dependency-absorbing HIL response submission client.

Uses only Python's standard library. The client reads receiver readiness,
selects a PDF, computes its SHA-256, builds the exact provenance manifest,
submits the multipart packet, and preserves the returned receipt locally.
"""
from __future__ import annotations

import hashlib
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_BASE_URL = "http://127.0.0.1:8000"
MAX_PDF_BYTES = 10 * 1024 * 1024


class SubmissionError(RuntimeError):
    """Raised when readiness, validation, or submission fails."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def request_json(url: str, *, timeout: int = 15) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SubmissionError(f"Receiver returned HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise SubmissionError(f"Receiver is unreachable: {exc.reason}") from exc
    try:
        value = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise SubmissionError("Receiver returned invalid JSON") from exc
    if not isinstance(value, dict):
        raise SubmissionError("Receiver returned an unexpected readiness shape")
    return value


def build_manifest(readiness: dict[str, Any], response_sha256: str) -> dict[str, Any]:
    required = {
        "provenance_manifest_schema",
        "primary_version",
        "primary_sha256",
        "protocol_version",
        "prompt_version",
        "prompt_sha256",
    }
    missing = sorted(required.difference(readiness))
    if missing:
        raise SubmissionError(f"Readiness omitted required fields: {', '.join(missing)}")
    return {
        "schema_version": readiness["provenance_manifest_schema"],
        "primary_version": readiness["primary_version"],
        "primary_sha256": readiness["primary_sha256"],
        "protocol_version": readiness["protocol_version"],
        "prompt_version": readiness["prompt_version"],
        "prompt_sha256": readiness["prompt_sha256"],
        "response_sha256": response_sha256,
        "producer_signature": {
            "state": "UNAVAILABLE",
            "scheme": None,
            "value": None,
            "key_id": None,
        },
    }


def _field(boundary: str, name: str, value: str) -> bytes:
    return (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
        f"{value}\r\n"
    ).encode("utf-8")


def _file_part(boundary: str, name: str, path: Path, media_type: str, data: bytes) -> bytes:
    return (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="{name}"; filename="{path.name}"\r\n'
        f"Content-Type: {media_type}\r\n\r\n"
    ).encode("utf-8") + data + b"\r\n"


def encode_multipart(
    *,
    pdf_path: Path,
    manifest: dict[str, Any],
    participant_identifier: str,
    publication_consent: str,
    model_response_declared_unedited: bool,
    participant_consent_authority_acknowledged: bool,
) -> tuple[bytes, str]:
    boundary = f"----stegverse-{uuid.uuid4().hex}"
    pdf_data = pdf_path.read_bytes()
    manifest_data = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    body = b"".join(
        [
            _file_part(boundary, "response_pdf", pdf_path, "application/pdf", pdf_data),
            _file_part(
                boundary,
                "provenance_manifest",
                Path("hil-provenance-manifest.json"),
                "application/json",
                manifest_data,
            ),
            _field(boundary, "participant_identifier", participant_identifier or "not_provided"),
            _field(boundary, "publication_consent", publication_consent),
            _field(boundary, "primary_sha256", str(manifest["primary_sha256"])),
            _field(boundary, "prompt_sha256", str(manifest["prompt_sha256"])),
            _field(
                boundary,
                "model_response_declared_unedited",
                str(model_response_declared_unedited).lower(),
            ),
            _field(
                boundary,
                "participant_consent_authority_acknowledged",
                str(participant_consent_authority_acknowledged).lower(),
            ),
            f"--{boundary}--\r\n".encode("utf-8"),
        ]
    )
    return body, boundary


def submit_packet(
    base_url: str,
    *,
    pdf_path: Path,
    manifest: dict[str, Any],
    participant_identifier: str,
    publication_consent: str,
    model_response_declared_unedited: bool,
    participant_consent_authority_acknowledged: bool,
) -> dict[str, Any]:
    body, boundary = encode_multipart(
        pdf_path=pdf_path,
        manifest=manifest,
        participant_identifier=participant_identifier,
        publication_consent=publication_consent,
        model_response_declared_unedited=model_response_declared_unedited,
        participant_consent_authority_acknowledged=participant_consent_authority_acknowledged,
    )
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/api/hil/submissions",
        data=body,
        method="POST",
        headers={
            "Accept": "application/json",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Content-Length": str(len(body)),
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SubmissionError(f"Submission rejected with HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise SubmissionError(f"Submission failed: {exc.reason}") from exc
    try:
        value = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise SubmissionError("Receiver returned invalid receipt JSON") from exc
    if not isinstance(value, dict):
        raise SubmissionError("Receiver returned an unexpected receipt shape")
    return value


def validate_pdf(path: Path) -> None:
    if not path.is_file():
        raise SubmissionError("Select an existing PDF file")
    if path.suffix.lower() != ".pdf":
        raise SubmissionError("The response file must use a .pdf extension")
    size = path.stat().st_size
    if size <= 0 or size > MAX_PDF_BYTES:
        raise SubmissionError("The response PDF must be between 1 byte and 10 MiB")
    with path.open("rb") as handle:
        if handle.read(5) != b"%PDF-":
            raise SubmissionError("The selected file does not have a valid PDF signature")


def save_artifacts(pdf_path: Path, manifest: dict[str, Any], receipt: dict[str, Any]) -> tuple[Path, Path]:
    stem = pdf_path.stem
    manifest_path = pdf_path.with_name(f"{stem}.hil-provenance.json")
    receipt_path = pdf_path.with_name(f"{stem}.hil-receipt.json")
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest_path, receipt_path


def run_gui() -> int:
    try:
        import tkinter as tk
        from tkinter import filedialog, messagebox, ttk
    except ImportError as exc:
        raise SubmissionError("Tkinter is unavailable in this Python installation") from exc

    root = tk.Tk()
    root.title("StegVerse HIL Submission")
    root.geometry("760x540")
    root.minsize(680, 480)

    base_url = tk.StringVar(value=os.getenv("STEGVERSE_HIL_BASE_URL", DEFAULT_BASE_URL))
    pdf_path = tk.StringVar()
    participant = tk.StringVar(value="local-controlled-test-001")
    consent = tk.StringVar(value="not_provided")
    unedited = tk.BooleanVar(value=False)
    authority_ack = tk.BooleanVar(value=False)
    status = tk.StringVar(value="Choose a PDF. The client will build the manifest automatically.")
    output = tk.Text(root, wrap="word", height=15)

    frame = ttk.Frame(root, padding=16)
    frame.pack(fill="both", expand=True)
    frame.columnconfigure(1, weight=1)

    ttk.Label(frame, text="Receiver").grid(row=0, column=0, sticky="w", pady=5)
    ttk.Entry(frame, textvariable=base_url).grid(row=0, column=1, columnspan=2, sticky="ew", pady=5)

    ttk.Label(frame, text="Response PDF").grid(row=1, column=0, sticky="w", pady=5)
    ttk.Entry(frame, textvariable=pdf_path).grid(row=1, column=1, sticky="ew", pady=5)

    def choose_pdf() -> None:
        selected = filedialog.askopenfilename(title="Select HIL response PDF", filetypes=[("PDF files", "*.pdf")])
        if selected:
            pdf_path.set(selected)
            status.set("PDF selected. Review consent declarations, then submit.")

    ttk.Button(frame, text="Choose PDF", command=choose_pdf).grid(row=1, column=2, padx=(8, 0), pady=5)

    ttk.Label(frame, text="Participant identifier").grid(row=2, column=0, sticky="w", pady=5)
    ttk.Entry(frame, textvariable=participant).grid(row=2, column=1, columnspan=2, sticky="ew", pady=5)

    ttk.Label(frame, text="Publication consent").grid(row=3, column=0, sticky="w", pady=5)
    ttk.Combobox(
        frame,
        textvariable=consent,
        state="readonly",
        values=("not_provided", "private", "anonymous", "public"),
    ).grid(row=3, column=1, columnspan=2, sticky="ew", pady=5)

    ttk.Checkbutton(
        frame,
        text="I declare that the model response PDF is unedited",
        variable=unedited,
    ).grid(row=4, column=0, columnspan=3, sticky="w", pady=5)
    ttk.Checkbutton(
        frame,
        text="I acknowledge authority for the participant consent selection",
        variable=authority_ack,
    ).grid(row=5, column=0, columnspan=3, sticky="w", pady=5)

    ttk.Label(frame, textvariable=status).grid(row=6, column=0, columnspan=3, sticky="w", pady=(10, 5))
    output.grid(row=8, column=0, columnspan=3, sticky="nsew", pady=(8, 0))
    frame.rowconfigure(8, weight=1)

    def submit() -> None:
        output.delete("1.0", "end")
        try:
            path = Path(pdf_path.get()).expanduser().resolve()
            validate_pdf(path)
            status.set("Checking receiver readiness...")
            root.update_idletasks()
            readiness = request_json(f"{base_url.get().rstrip('/')}/api/hil/readiness")
            if readiness.get("state") != "READY":
                raise SubmissionError(f"Receiver is not READY: {json.dumps(readiness, indent=2)}")
            response_hash = sha256_file(path)
            manifest = build_manifest(readiness, response_hash)
            status.set("Submitting governed packet...")
            root.update_idletasks()
            receipt = submit_packet(
                base_url.get(),
                pdf_path=path,
                manifest=manifest,
                participant_identifier=participant.get(),
                publication_consent=consent.get(),
                model_response_declared_unedited=unedited.get(),
                participant_consent_authority_acknowledged=authority_ack.get(),
            )
            manifest_path, receipt_path = save_artifacts(path, manifest, receipt)
            output.insert("1.0", json.dumps(receipt, indent=2, sort_keys=True))
            status.set(f"Submission accepted. Receipt saved: {receipt_path.name}")
            messagebox.showinfo(
                "HIL submission accepted",
                f"Manifest:\n{manifest_path}\n\nReceipt:\n{receipt_path}",
            )
        except Exception as exc:  # GUI boundary: report exact error without crashing
            status.set("Submission did not complete.")
            output.insert("1.0", str(exc))
            messagebox.showerror("HIL submission failed", str(exc))

    ttk.Button(frame, text="Build manifest and submit", command=submit).grid(
        row=7, column=0, columnspan=3, sticky="ew", pady=(8, 0)
    )

    root.mainloop()
    return 0


def main() -> int:
    try:
        return run_gui()
    except SubmissionError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
