#!/usr/bin/env python3
"""Native GUI entrypoint for the governed HIL submission client."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from hil_submit_client import (
    DEFAULT_BASE_URL,
    SubmissionError,
    build_manifest,
    request_json,
    save_artifacts,
    sha256_file,
    submit_packet,
    validate_pdf,
)


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

    frame = ttk.Frame(root, padding=16)
    frame.pack(fill="both", expand=True)
    frame.columnconfigure(1, weight=1)
    frame.rowconfigure(8, weight=1)

    output = tk.Text(frame, wrap="word", height=15)

    ttk.Label(frame, text="Receiver").grid(row=0, column=0, sticky="w", pady=5)
    ttk.Entry(frame, textvariable=base_url).grid(row=0, column=1, columnspan=2, sticky="ew", pady=5)

    ttk.Label(frame, text="Response PDF").grid(row=1, column=0, sticky="w", pady=5)
    ttk.Entry(frame, textvariable=pdf_path).grid(row=1, column=1, sticky="ew", pady=5)

    def choose_pdf() -> None:
        selected = filedialog.askopenfilename(
            title="Select HIL response PDF",
            filetypes=[("PDF files", "*.pdf")],
        )
        if selected:
            pdf_path.set(selected)
            status.set("PDF selected. Review consent declarations, then submit.")

    ttk.Button(frame, text="Choose PDF", command=choose_pdf).grid(
        row=1, column=2, padx=(8, 0), pady=5
    )

    ttk.Label(frame, text="Participant identifier").grid(row=2, column=0, sticky="w", pady=5)
    ttk.Entry(frame, textvariable=participant).grid(
        row=2, column=1, columnspan=2, sticky="ew", pady=5
    )

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

    ttk.Label(frame, textvariable=status).grid(
        row=6, column=0, columnspan=3, sticky="w", pady=(10, 5)
    )

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
        except Exception as exc:
            status.set("Submission did not complete.")
            output.insert("1.0", str(exc))
            messagebox.showerror("HIL submission failed", str(exc))

    ttk.Button(frame, text="Build manifest and submit", command=submit).grid(
        row=7, column=0, columnspan=3, sticky="ew", pady=(8, 0)
    )
    output.grid(row=8, column=0, columnspan=3, sticky="nsew", pady=(8, 0))

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
