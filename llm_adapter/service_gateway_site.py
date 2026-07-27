from __future__ import annotations

import os
from typing import Any, Dict

from fastapi import File, Form, UploadFile

from . import service_gateway as gateway

app = gateway.app

# Replace the original Site compatibility route while preserving the public
# browser contract and the RTG attempt-notification fields.
app.router.routes[:] = [
    route for route in app.router.routes
    if getattr(route, "path", None) != "/api/hil/submissions"
]


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


def main() -> None:
    import uvicorn

    uvicorn.run(
        "llm_adapter.service_gateway_site:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8080")),
    )


if __name__ == "__main__":
    main()
