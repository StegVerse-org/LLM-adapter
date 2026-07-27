from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import File, Form, HTTPException, Query, UploadFile

from . import service_gateway as gateway

app = gateway.app

# Replace the original Site compatibility route while preserving the public
# browser contract and the RTG attempt-notification fields.
app.router.routes[:] = [
    route for route in app.router.routes
    if getattr(route, "path", None) != "/api/hil/submissions"
]


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _latest_submission_notification(root: Path, submission_id: str) -> Optional[Dict[str, Any]]:
    matches = []
    for path in (root / "notifications").glob("*.json"):
        try:
            notification = _load_json(path)
        except (OSError, ValueError):
            continue
        if notification.get("submission_id") == submission_id:
            matches.append((notification.get("attempted_at") or "", notification))
    if not matches:
        return None
    matches.sort(key=lambda item: item[0], reverse=True)
    return matches[0][1]


def _recipient_states(root: Path, attempt_id: str) -> Dict[str, str]:
    path = root / "notification-outbox" / f"{attempt_id}.json"
    if not path.exists():
        return {}
    envelope = _load_json(path)
    return {
        str(result.get("role")): str(result.get("state"))
        for result in envelope.get("delivery_results") or []
        if result.get("role") and result.get("state")
    }


@app.post("/api/hil/submissions")
async def site_hil_submission(
    response_pdf: UploadFile = File(...),
    provenance_manifest: UploadFile = File(...),
    participant_identifier: str = Form("not_provided"),
    publication_consent: str = Form("not_provided"),
    primary_sha256: str = Form(...),
    prompt_sha256: str = Form(...),
    model_response_declared_unedited: str = Form("false"),
    participant_consent_authority_acknowledged: str = Form("false"),
    participant_notification_requested: str = Form("false"),
    participant_notification_email: str = Form("not_provided"),
    participant_notification_scope: str = Form("NONE"),
) -> Dict[str, Any]:
    receipt = await gateway.site_hil_submission(
        response_pdf=response_pdf,
        provenance_manifest=provenance_manifest,
        participant_identifier=participant_identifier,
        publication_consent=publication_consent,
        primary_sha256=primary_sha256,
        prompt_sha256=prompt_sha256,
        model_response_declared_unedited=model_response_declared_unedited,
        participant_consent_authority_acknowledged=participant_consent_authority_acknowledged,
        participant_notification_requested=participant_notification_requested,
        participant_notification_email=participant_notification_email,
        participant_notification_scope=participant_notification_scope,
    )
    # The base gateway now emits the browser-compatible receipt hash. Recompute
    # defensively so this wrapper remains compatible with older gateway builds.
    unsigned = dict(receipt)
    unsigned.pop("receipt_sha256", None)
    receipt["receipt_sha256"] = gateway.sha256_hex(gateway.canonical_json(unsigned))

    runtime = gateway._runtime()
    receipt_path = runtime["root"] / "receipts" / f"{receipt['submission_id']}.json"
    receipt_path.write_bytes(gateway.canonical_json(receipt) + b"\n")
    return receipt


@app.get("/api/hil/submissions/{submission_id}/status")
def site_hil_submission_status(
    submission_id: str,
    receipt_id: str = Query(..., min_length=16, max_length=64),
) -> Dict[str, Any]:
    if not submission_id.startswith("HIL-SUBMISSION-") or len(submission_id) > 64:
        raise HTTPException(status_code=404, detail="submission_status_not_found")
    runtime = gateway._runtime()
    receipt_path = runtime["root"] / "receipts" / f"{submission_id}.json"
    if not receipt_path.exists():
        raise HTTPException(status_code=404, detail="submission_status_not_found")

    receipt = _load_json(receipt_path)
    if receipt.get("receipt_id") != receipt_id:
        raise HTTPException(status_code=404, detail="submission_status_not_found")

    notification = _latest_submission_notification(runtime["root"], submission_id)
    recipient_states = _recipient_states(
        runtime["root"], str(notification.get("attempt_id"))
    ) if notification else {}

    return {
        "schema_version": "HIL-SUBMISSION-STATUS-v1",
        "submission_id": submission_id,
        "receipt_id": receipt.get("receipt_id"),
        "submission_state": "ACCEPTED",
        "chain_validation_state": receipt.get("chain_validation_state"),
        "review_state": receipt.get("review_state"),
        "publication_state": receipt.get("publication_state"),
        "notification_delivery_state": (
            notification.get("notification_delivery_state") if notification else "UNKNOWN"
        ),
        "recipient_address_retention_state": (
            notification.get("recipient_address_retention_state")
            if notification else "UNKNOWN"
        ),
        "required_recipient_delivery_state": recipient_states.get(
            "STEGVERSE_STUDY_AUTHORITY", "PENDING"
        ),
        "participant_copy_requested": bool(
            notification and notification.get("participant_copy_requested")
        ),
        "participant_copy_delivery_state": (
            recipient_states.get("PARTICIPANT_ATTEMPT_COPY", "PENDING")
            if notification and notification.get("participant_copy_requested")
            else "NOT_REQUESTED"
        ),
        "recipient_addresses_exposed": False,
        "notification_delivery_changes_submission_outcome": False,
    }


def main() -> None:
    import uvicorn

    uvicorn.run(
        "llm_adapter.service_gateway_site:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8080")),
    )


if __name__ == "__main__":
    main()
