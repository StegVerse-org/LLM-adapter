from __future__ import annotations

import hashlib
import json
from io import BytesIO
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

from llm_adapter.attachment_intake import (
    FEATURE_NAMES,
    FEATURE_SCHEMA,
    MATH_IMAGE_PROFILE,
    decode_math_image,
    extract_normalized_visual_features,
    review_math_image_bytes,
    router,
)


def _png_bytes(size: tuple[int, int] = (320, 200)) -> bytes:
    image = Image.new("RGB", size, "white")
    draw = ImageDraw.Draw(image)
    draw.text((20, 40), "x^2 + 3x = 10", fill="black")
    draw.line((15, 90, 290, 90), fill="black", width=2)
    stream = BytesIO()
    image.save(stream, format="PNG")
    return stream.getvalue()


def _client(tmp_path: Path, monkeypatch) -> TestClient:
    monkeypatch.setenv("STEGVERSE_ATTACHMENT_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("STEGVERSE_STORAGE_DURABLE_ACROSS_RESTARTS", "true")
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_real_png_decode_and_canonical_feature_vector() -> None:
    data = _png_bytes()
    decoded = decode_math_image(data)
    assert decoded.media_type == "image/png"
    assert (decoded.width, decoded.height) == (320, 200)
    features = extract_normalized_visual_features(decoded.image)
    assert tuple(features) == FEATURE_NAMES
    assert all(0.0 <= value <= 1.0 for value in features.values())
    assert features["edge_density"] > 0.0


def test_review_keeps_source_image_distinct_from_transcription() -> None:
    data = _png_bytes()
    digest = hashlib.sha256(data).hexdigest()
    review = review_math_image_bytes(data, attachment_id="math-image-test", content_hash=digest)
    assert review["source_image"]["state"] == "source_image"
    assert review["source_image"]["content_hash"] == f"sha256:{digest}"
    assert review["visual_features"]["schema"] == FEATURE_SCHEMA
    transcription = review["interpreted_mathematical_transcription"]
    assert transcription["state"] == "NOT_PRODUCED"
    assert transcription["content"] is None
    assert transcription["is_source_fact"] is False
    assert transcription["source_image_remains_immutable"] is True
    assert review["vision_runtime_binding"]["reference_model_math_transcription_capable"] is False
    assert review["next_stage"] == "MATH_CAPABLE_VISUAL_TRANSCRIPTION_REQUIRED"
    assert all(value is False for value in review["authority"].values())


def test_shared_intake_persists_exact_bytes_and_review_is_idempotent(tmp_path: Path, monkeypatch) -> None:
    client = _client(tmp_path, monkeypatch)
    data = _png_bytes()
    digest = hashlib.sha256(data).hexdigest()

    response = client.post(
        "/api/attachments/v1/intake",
        data={"profile": MATH_IMAGE_PROFILE, "attachment_id": "MATH-IMG-001", "declared_sha256": digest},
        files={"artifact": ("equation.png", data, "image/png")},
    )
    assert response.status_code == 200, response.text
    receipt = response.json()
    assert receipt["state"] == "ACCEPTED"
    assert receipt["content_hash"] == f"sha256:{digest}"
    assert receipt["artifact_state"] == "EXACT_BYTES_PRESERVED"
    assert receipt["authority"] == {
        "execution": False,
        "provider": False,
        "publication": False,
        "custody": False,
    }

    stored = tmp_path / "attachments" / "MATH-IMG-001" / receipt["artifact_name"]
    assert stored.read_bytes() == data

    review_response = client.post(
        "/api/math-solver/v1/image-review", json={"attachment_id": "MATH-IMG-001"}
    )
    assert review_response.status_code == 200, review_response.text
    review = review_response.json()
    assert review["source_image"]["content_hash"] == receipt["content_hash"]
    assert review["interpreted_mathematical_transcription"]["state"] == "NOT_PRODUCED"

    second = client.post(
        "/api/math-solver/v1/image-review", json={"attachment_id": "MATH-IMG-001"}
    )
    assert second.status_code == 200
    assert second.json() == review


def test_declared_hash_mismatch_fails_before_persistence(tmp_path: Path, monkeypatch) -> None:
    client = _client(tmp_path, monkeypatch)
    data = _png_bytes()
    response = client.post(
        "/api/attachments/v1/intake",
        data={"profile": MATH_IMAGE_PROFILE, "attachment_id": "MATH-IMG-002", "declared_sha256": "0" * 64},
        files={"artifact": ("equation.png", data, "image/png")},
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "attachment_hash_mismatch"
    assert not (tmp_path / "attachments" / "MATH-IMG-002").exists()


def test_content_type_spoof_does_not_override_real_decode(tmp_path: Path, monkeypatch) -> None:
    client = _client(tmp_path, monkeypatch)
    data = _png_bytes()
    response = client.post(
        "/api/attachments/v1/intake",
        data={"profile": MATH_IMAGE_PROFILE, "attachment_id": "MATH-IMG-003"},
        files={"artifact": ("fake.jpg", data, "image/jpeg")},
    )
    assert response.status_code == 200
    assert response.json()["media_type"] == "image/png"


def test_non_image_and_unknown_profile_fail_closed(tmp_path: Path, monkeypatch) -> None:
    client = _client(tmp_path, monkeypatch)
    response = client.post(
        "/api/attachments/v1/intake",
        data={"profile": MATH_IMAGE_PROFILE},
        files={"artifact": ("not-image.png", b"not an image", "image/png")},
    )
    assert response.status_code == 422

    response = client.post(
        "/api/attachments/v1/intake",
        data={"profile": "unowned-profile-v1"},
        files={"artifact": ("equation.png", _png_bytes(), "image/png")},
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "attachment_profile_unsupported"


def test_readiness_exposes_shared_profile_without_claiming_authority(tmp_path: Path, monkeypatch) -> None:
    client = _client(tmp_path, monkeypatch)
    response = client.get("/api/attachments/v1/readiness")
    assert response.status_code == 200
    payload = response.json()
    assert payload["state"] == "READY"
    assert MATH_IMAGE_PROFILE in payload["profiles"]
    assert payload["hil_legacy_intake_remains_compatible"] is True
    assert payload["credential_authority"] == "TV/TVC"
    assert payload["github_token_runtime_authority"] == "NONE"
    assert payload["authority_granted"] is False


def test_persisted_receipt_reconstructs_hash(tmp_path: Path, monkeypatch) -> None:
    client = _client(tmp_path, monkeypatch)
    data = _png_bytes()
    response = client.post(
        "/api/attachments/v1/intake",
        data={"profile": MATH_IMAGE_PROFILE, "attachment_id": "MATH-IMG-004"},
        files={"artifact": ("equation.png", data, "image/png")},
    )
    receipt = response.json()
    receipt_path = tmp_path / "attachment-receipts" / "MATH-IMG-004.json"
    persisted = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert persisted == receipt
    without_hash = dict(persisted)
    receipt_hash = without_hash.pop("receipt_sha256")
    canonical = json.dumps(without_hash, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    assert receipt_hash == hashlib.sha256(canonical).hexdigest()
