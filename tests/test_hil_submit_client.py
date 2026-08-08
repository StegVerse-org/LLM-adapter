from pathlib import Path

from scripts.hil_submit_client import build_manifest, encode_multipart


def readiness_fixture():
    return {
        "state": "READY",
        "provenance_manifest_schema": "HIL-RESPONSE-PROVENANCE-v1.1",
        "primary_version": "v1.1",
        "primary_sha256": "a" * 64,
        "protocol_version": "HIL-PROTOCOL-v1.1",
        "prompt_version": "HIL-PROMPT-v1.1",
        "prompt_sha256": "b" * 64,
    }


def test_build_manifest_uses_readiness_contract():
    manifest = build_manifest(readiness_fixture(), "c" * 64)
    assert manifest["schema_version"] == "HIL-RESPONSE-PROVENANCE-v1.1"
    assert manifest["primary_version"] == "v1.1"
    assert manifest["protocol_version"] == "HIL-PROTOCOL-v1.1"
    assert manifest["prompt_version"] == "HIL-PROMPT-v1.1"
    assert manifest["response_sha256"] == "c" * 64
    assert manifest["producer_signature"]["state"] == "UNAVAILABLE"


def test_encode_multipart_binds_pdf_manifest_and_consent(tmp_path: Path):
    pdf = tmp_path / "response.pdf"
    pdf.write_bytes(b"%PDF-1.4\ncontrolled-test\n")
    manifest = build_manifest(readiness_fixture(), "c" * 64)
    body, boundary = encode_multipart(
        pdf_path=pdf,
        manifest=manifest,
        participant_identifier="local-controlled-test-001",
        publication_consent="not_provided",
        model_response_declared_unedited=False,
        participant_consent_authority_acknowledged=False,
    )
    assert boundary.encode() in body
    assert b'name="response_pdf"' in body
    assert b'name="provenance_manifest"' in body
    assert b'HIL-RESPONSE-PROVENANCE-v1.1' in body
    assert b'local-controlled-test-001' in body
    assert b'name="model_response_declared_unedited"' in body
