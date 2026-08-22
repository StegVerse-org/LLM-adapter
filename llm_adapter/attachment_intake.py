from __future__ import annotations

"""Shared governed attachment intake and bounded math-image review.

This module owns no provider, model, custody, publication, or execution authority.
It preserves exact uploaded bytes and creates deterministic interpretation inputs.
"""

import colorsys
import hashlib
import json
import math
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
import re
from typing import Any, Iterable
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field
from PIL import Image, ImageOps, UnidentifiedImageError

try:
    from pillow_heif import register_heif_opener

    register_heif_opener()
except ImportError:  # pragma: no cover - HEIF is optional outside service installs
    pass


ATTACHMENT_SCHEMA = "stegverse.attachment-receipt.v1"
MATH_REVIEW_SCHEMA = "stegverse.math-image-review.v1"
FEATURE_SCHEMA = "stegverse.normalized-region-features/v1"
MATH_IMAGE_PROFILE = "math-image-v1"
MAX_MATH_IMAGE_BYTES = 25 * 1024 * 1024
MAX_MATH_IMAGE_PIXELS = 80_000_000
ATTACHMENT_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,95}$")
FEATURE_NAMES = (
    "mean_r",
    "mean_g",
    "mean_b",
    "saturation",
    "luminance",
    "edge_density",
    "texture_variance",
    "region_solidity",
)
FORMAT_MEDIA_TYPES = {
    "PNG": "image/png",
    "JPEG": "image/jpeg",
    "WEBP": "image/webp",
    "HEIF": "image/heif",
    "HEIC": "image/heic",
}
MEDIA_EXTENSIONS = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/webp": ".webp",
    "image/heif": ".heif",
    "image/heic": ".heic",
}

router = APIRouter(tags=["shared-attachments", "math-image-review"])


@dataclass(frozen=True)
class DecodedImage:
    image: Image.Image
    media_type: str
    width: int
    height: int


class MathImageReviewRequest(BaseModel):
    attachment_id: str = Field(min_length=1, max_length=96)


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _data_root() -> Path:
    # Reuse the same durable service-gateway storage plane already used by HIL.
    configured = os.getenv("STEGVERSE_ATTACHMENT_DATA_DIR", "").strip()
    if not configured:
        configured = os.getenv("STEGVERSE_HIL_DATA_DIR", "/tmp/stegverse-hil").strip()
    return Path(configured).expanduser().resolve()


def _durable_declared() -> bool:
    return os.getenv("STEGVERSE_STORAGE_DURABLE_ACROSS_RESTARTS", "false").strip().lower() == "true"


def _safe_attachment_id(value: str | None = None) -> str:
    identifier = (value or f"ATT-{uuid4().hex[:20].upper()}").strip()
    if not ATTACHMENT_ID_RE.fullmatch(identifier):
        raise HTTPException(status_code=422, detail="attachment_id_invalid")
    return identifier


def _paths(attachment_id: str) -> tuple[Path, Path, Path]:
    root = _data_root()
    attachment_dir = root / "attachments" / attachment_id
    receipt_path = root / "attachment-receipts" / f"{attachment_id}.json"
    review_path = root / "math-image-reviews" / f"{attachment_id}.json"
    return attachment_dir, receipt_path, review_path


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _variance(values: Iterable[float]) -> float:
    rows = tuple(float(value) for value in values)
    if not rows:
        return 0.0
    mean = sum(rows) / len(rows)
    return sum((value - mean) ** 2 for value in rows) / len(rows)


def decode_math_image(image_bytes: bytes) -> DecodedImage:
    if not image_bytes:
        raise ValueError("image_bytes_empty")
    try:
        with Image.open(BytesIO(image_bytes)) as source:
            detected_format = str(source.format or "").upper()
            media_type = FORMAT_MEDIA_TYPES.get(detected_format)
            if media_type is None:
                raise ValueError("unsupported_image_format")
            raw_width, raw_height = source.size
            if raw_width < 1 or raw_height < 1:
                raise ValueError("image_dimensions_invalid")
            if raw_width * raw_height > MAX_MATH_IMAGE_PIXELS:
                raise ValueError("image_pixel_count_exceeded")
            corrected = ImageOps.exif_transpose(source)
            corrected.load()
            rgb = corrected.convert("RGB").copy()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise ValueError("image_decode_failed") from exc
    width, height = rgb.size
    if width < 1 or height < 1:
        raise ValueError("image_dimensions_invalid")
    if width * height > MAX_MATH_IMAGE_PIXELS:
        raise ValueError("image_pixel_count_exceeded")
    return DecodedImage(image=rgb, media_type=media_type, width=width, height=height)


def extract_normalized_visual_features(image: Image.Image) -> dict[str, float]:
    """Return the canonical eight-feature visual-evidence vector for one frame."""
    crop = image.copy().convert("RGB")
    crop.thumbnail((96, 96))
    pixels = list(crop.getdata())
    if not pixels:
        raise ValueError("image_contains_no_pixels")

    rs = [value[0] / 255.0 for value in pixels]
    gs = [value[1] / 255.0 for value in pixels]
    bs = [value[2] / 255.0 for value in pixels]
    luminance = [0.2126 * r + 0.7152 * g + 0.0722 * b for r, g, b in zip(rs, gs, bs)]
    saturations = [colorsys.rgb_to_hsv(r, g, b)[1] for r, g, b in zip(rs, gs, bs)]

    width, height = crop.size
    edge_hits = 0
    comparisons = 0
    for y in range(height):
        for x in range(width):
            current = luminance[y * width + x]
            if x + 1 < width:
                edge_hits += abs(current - luminance[y * width + x + 1]) >= 0.12
                comparisons += 1
            if y + 1 < height:
                edge_hits += abs(current - luminance[(y + 1) * width + x]) >= 0.12
                comparisons += 1
    edge_density = edge_hits / comparisons if comparisons else 0.0

    corners = [pixels[0], pixels[width - 1], pixels[(height - 1) * width], pixels[-1]]
    background = tuple(sorted(c[channel] for c in corners)[len(corners) // 2] / 255.0 for channel in range(3))
    foreground = 0
    for r, g, b in zip(rs, gs, bs):
        distance = math.sqrt(
            (r - background[0]) ** 2 + (g - background[1]) ** 2 + (b - background[2]) ** 2
        )
        foreground += distance >= 0.10

    raw = {
        "mean_r": sum(rs) / len(rs),
        "mean_g": sum(gs) / len(gs),
        "mean_b": sum(bs) / len(bs),
        "saturation": sum(saturations) / len(saturations),
        "luminance": sum(luminance) / len(luminance),
        "edge_density": edge_density,
        "texture_variance": min(1.0, _variance(luminance) * 12.0),
        "region_solidity": foreground / len(pixels),
    }
    return {name: round(_clamp(raw[name]), 8) for name in FEATURE_NAMES}


def _quality_review(decoded: DecodedImage, features: dict[str, float]) -> dict[str, Any]:
    flags: list[str] = []
    if min(decoded.width, decoded.height) < 128:
        flags.append("LOW_SPATIAL_RESOLUTION")
    if features["luminance"] < 0.06:
        flags.append("VERY_DARK")
    if features["luminance"] > 0.97:
        flags.append("VERY_BRIGHT")
    if features["edge_density"] < 0.003:
        flags.append("LOW_EDGE_INFORMATION")
    return {
        "state": "PASS" if not flags else "REVIEW_RECOMMENDED",
        "flags": flags,
        "semantic_math_readability_established": False,
        "ocr_or_equation_transcription_performed": False,
    }


def review_math_image_bytes(
    image_bytes: bytes,
    *,
    attachment_id: str,
    content_hash: str | None = None,
) -> dict[str, Any]:
    decoded = decode_math_image(image_bytes)
    features = extract_normalized_visual_features(decoded.image)
    digest = content_hash or _sha256(image_bytes)
    review: dict[str, Any] = {
        "schema": MATH_REVIEW_SCHEMA,
        "attachment_id": attachment_id,
        "reviewed_at": _now(),
        "source_image": {
            "state": "source_image",
            "content_hash": f"sha256:{digest}",
            "media_type": decoded.media_type,
            "width": decoded.width,
            "height": decoded.height,
            "exact_uploaded_bytes_preserved": True,
        },
        "visual_features": {
            "schema": FEATURE_SCHEMA,
            "region": "whole_frame",
            "feature_names": list(FEATURE_NAMES),
            "features": features,
        },
        "quality_review": _quality_review(decoded, features),
        "interpreted_mathematical_transcription": {
            "state": "NOT_PRODUCED",
            "content": None,
            "is_source_fact": False,
            "correction_creates_successor_state": True,
            "source_image_remains_immutable": True,
        },
        "vision_runtime_binding": {
            "canonical_input_schema": FEATURE_SCHEMA,
            "released_reference_runtime": "StegVerse-002/micro-node-runtime:SOVEREIGN-LOCAL-VISION-RUNTIME-003",
            "reference_model": "stegverse-reference-visual-evidence-v1",
            "reference_model_accepts_raw_images": False,
            "reference_model_math_transcription_capable": False,
            "model_output_authority": "NONE",
        },
        "next_stage": "MATH_CAPABLE_VISUAL_TRANSCRIPTION_REQUIRED",
        "authority": {
            "execution": False,
            "provider": False,
            "publication": False,
            "custody": False,
            "mathematical_truth": False,
        },
    }
    review["review_sha256"] = _sha256(_canonical_json(review))
    return review


def _load_receipt(attachment_id: str) -> dict[str, Any]:
    _, receipt_path, _ = _paths(attachment_id)
    if not receipt_path.exists():
        raise HTTPException(status_code=404, detail="attachment_not_found")
    return json.loads(receipt_path.read_text(encoding="utf-8"))


def _load_attachment_bytes(receipt: dict[str, Any]) -> bytes:
    attachment_id = str(receipt["attachment_id"])
    attachment_dir, _, _ = _paths(attachment_id)
    artifact_name = str(receipt.get("artifact_name") or "")
    if not artifact_name or Path(artifact_name).name != artifact_name:
        raise HTTPException(status_code=409, detail="attachment_receipt_artifact_invalid")
    path = attachment_dir / artifact_name
    if not path.exists():
        raise HTTPException(status_code=409, detail="attachment_bytes_missing")
    data = path.read_bytes()
    digest = _sha256(data)
    if receipt.get("content_hash") != f"sha256:{digest}":
        raise HTTPException(status_code=409, detail="attachment_hash_reconstruction_failed")
    return data


@router.get("/api/attachments/v1/readiness")
def attachment_readiness() -> dict[str, Any]:
    root = _data_root()
    return {
        "schema": "stegverse.attachment-intake-readiness.v1",
        "state": "READY" if _durable_declared() else "CONFIGURATION_REQUIRED",
        "blockers": [] if _durable_declared() else ["durable_storage_not_declared"],
        "service": "stegverse-shared-attachment-intake",
        "storage_root_absolute": root.is_absolute(),
        "profiles": {
            MATH_IMAGE_PROFILE: {
                "maximum_size_bytes": MAX_MATH_IMAGE_BYTES,
                "maximum_decoded_pixels": MAX_MATH_IMAGE_PIXELS,
                "accepted_media_types": sorted(MEDIA_EXTENSIONS),
                "exact_bytes_preserved": True,
                "review_endpoint": "/api/math-solver/v1/image-review",
            }
        },
        "hil_legacy_intake_remains_compatible": True,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "authority_granted": False,
    }


@router.post("/api/attachments/v1/intake")
async def attachment_intake(
    artifact: UploadFile = File(...),
    profile: str = Form(MATH_IMAGE_PROFILE),
    attachment_id: str | None = Form(None),
    declared_sha256: str | None = Form(None),
) -> dict[str, Any]:
    if profile != MATH_IMAGE_PROFILE:
        raise HTTPException(status_code=422, detail="attachment_profile_unsupported")
    identifier = _safe_attachment_id(attachment_id)
    attachment_dir, receipt_path, _ = _paths(identifier)

    data = await artifact.read(MAX_MATH_IMAGE_BYTES + 1)
    if not data or len(data) > MAX_MATH_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="math_image_size_invalid")
    try:
        decoded = decode_math_image(data)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    digest = _sha256(data)
    if declared_sha256:
        declared = declared_sha256.removeprefix("sha256:").lower()
        if declared != digest:
            raise HTTPException(status_code=422, detail="attachment_hash_mismatch")

    if receipt_path.exists():
        existing = json.loads(receipt_path.read_text(encoding="utf-8"))
        if (
            existing.get("profile") == profile
            and existing.get("content_hash") == f"sha256:{digest}"
            and existing.get("media_type") == decoded.media_type
        ):
            return existing
        raise HTTPException(status_code=409, detail="attachment_id_content_conflict")
    if attachment_dir.exists():
        raise HTTPException(status_code=409, detail="attachment_exists_without_receipt")

    attachment_dir.mkdir(parents=True, exist_ok=False)
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    extension = MEDIA_EXTENSIONS[decoded.media_type]
    artifact_name = f"source{extension}"
    (attachment_dir / artifact_name).write_bytes(data)
    metadata = {
        "profile": profile,
        "original_filename": Path(artifact.filename or "").name or None,
        "declared_content_type": artifact.content_type,
        "detected_media_type": decoded.media_type,
        "width": decoded.width,
        "height": decoded.height,
    }
    (attachment_dir / "metadata.json").write_bytes(_canonical_json(metadata) + b"\n")

    receipt: dict[str, Any] = {
        "schema": ATTACHMENT_SCHEMA,
        "state": "ACCEPTED",
        "attachment_id": identifier,
        "profile": profile,
        "received_at": _now(),
        "media_type": decoded.media_type,
        "content_hash": f"sha256:{digest}",
        "size_bytes": len(data),
        "artifact_name": artifact_name,
        "metadata_hash": f"sha256:{_sha256(_canonical_json(metadata))}",
        "storage_class": "service-gateway-durable-storage" if _durable_declared() else "service-gateway-local-storage",
        "artifact_state": "EXACT_BYTES_PRESERVED",
        "review_state": "PENDING_PROFILE_REVIEW",
        "provider_processing": "not_required_for_acceptance",
        "master_records_custody": "not_required_for_acceptance",
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "authority": {
            "execution": False,
            "provider": False,
            "publication": False,
            "custody": False,
        },
    }
    receipt["receipt_sha256"] = _sha256(_canonical_json(receipt))
    receipt_path.write_bytes(_canonical_json(receipt) + b"\n")
    return receipt


@router.post("/api/math-solver/v1/image-review")
def math_image_review(request: MathImageReviewRequest) -> dict[str, Any]:
    attachment_id = _safe_attachment_id(request.attachment_id)
    receipt = _load_receipt(attachment_id)
    if receipt.get("profile") != MATH_IMAGE_PROFILE or receipt.get("state") != "ACCEPTED":
        raise HTTPException(status_code=409, detail="attachment_not_admitted_for_math_review")
    data = _load_attachment_bytes(receipt)
    _, _, review_path = _paths(attachment_id)
    if review_path.exists():
        existing = json.loads(review_path.read_text(encoding="utf-8"))
        if existing.get("source_image", {}).get("content_hash") == receipt.get("content_hash"):
            return existing
        raise HTTPException(status_code=409, detail="math_image_review_source_drift")

    try:
        review = review_math_image_bytes(
            data,
            attachment_id=attachment_id,
            content_hash=str(receipt["content_hash"]).removeprefix("sha256:"),
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    review_path.parent.mkdir(parents=True, exist_ok=True)
    review_path.write_bytes(_canonical_json(review) + b"\n")
    return review
