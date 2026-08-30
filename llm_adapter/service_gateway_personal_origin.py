"""Read-only stegverse.me virtual-origin adapter for the shared Service Gateway.

This adapter serves only a deployment-local public bundle on admitted personal
origin Host values. It does not read private KV, derive identity, mint routes,
issue certificates, mutate DNS, or grant runtime authority.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path

from fastapi import Request
from fastapi.responses import Response

MANIFEST_NAME = "stegverse-me-origin-manifest.json"
MANIFEST_SCHEMA = "stegverse.personal-origin.public-bundle/v1"
MAX_FILE_BYTES = 4 * 1024 * 1024
OPAQUE = r"sv1_[A-Za-z0-9_-]{43}"
NODE_ROUTE = re.compile(rf"^/n/(?P<opaque>{OPAQUE})/(?P<asset>[^/]*)$")
NODE_FILES = {
    "": "node.html",
    "services.html": "services.html",
    "stegverse-me-opaque-resolver.js": "stegverse-me-opaque-resolver.js",
    "services-state.js": "services-state.js",
    "services.js": "services.js",
    "kv-readiness-snapshot.json": "kv-readiness-snapshot.json",
}
CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".json": "application/json",
    ".css": "text/css; charset=utf-8",
}


class PersonalOriginError(RuntimeError):
    pass


def admitted_hosts() -> set[str]:
    raw = os.getenv("STEGVERSE_PERSONAL_ORIGIN_HOSTS", "stegverse.me,www.stegverse.me")
    return {value.strip().lower() for value in raw.split(",") if value.strip()}


def request_host(request: Request) -> str:
    value = request.headers.get("host", "").split(":", 1)[0].strip().lower()
    return value


def bundle_root() -> Path:
    raw = os.getenv("STEGVERSE_PERSONAL_ORIGIN_BUNDLE_ROOT", "").strip()
    if not raw:
        raise PersonalOriginError("personal_origin_bundle_root_not_configured")
    candidate = Path(raw).expanduser()
    if candidate.is_symlink():
        raise PersonalOriginError("personal_origin_bundle_root_invalid")
    root = candidate.resolve()
    if not root.is_dir():
        raise PersonalOriginError("personal_origin_bundle_root_invalid")
    return root


def _manifest(root: Path) -> dict:
    path = root / MANIFEST_NAME
    if not path.is_file() or path.is_symlink():
        raise PersonalOriginError("personal_origin_manifest_missing")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise PersonalOriginError("personal_origin_manifest_invalid") from exc
    if value.get("schema") != MANIFEST_SCHEMA:
        raise PersonalOriginError("personal_origin_manifest_schema_invalid")
    if value.get("authority_effect") != "NONE" or value.get("private_kv_included") is not False:
        raise PersonalOriginError("personal_origin_manifest_authority_invalid")
    files = value.get("files")
    if not isinstance(files, dict) or not files:
        raise PersonalOriginError("personal_origin_manifest_files_invalid")
    return value


def _logical_file(path: str) -> str | None:
    if path == "/":
        return "index.html"
    match = NODE_ROUTE.fullmatch(path)
    if not match:
        return None
    return NODE_FILES.get(match.group("asset"))


def _read_verified(root: Path, logical: str) -> tuple[bytes, str]:
    manifest = _manifest(root)
    expected = manifest["files"].get(logical)
    if not isinstance(expected, str) or not re.fullmatch(r"sha256:[a-f0-9]{64}", expected):
        raise PersonalOriginError("personal_origin_file_not_manifested")
    path = root / logical
    if not path.is_file() or path.is_symlink():
        raise PersonalOriginError("personal_origin_file_invalid")
    resolved = path.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise PersonalOriginError("personal_origin_path_escape") from exc
    data = resolved.read_bytes()
    if len(data) > MAX_FILE_BYTES:
        raise PersonalOriginError("personal_origin_file_too_large")
    actual = "sha256:" + hashlib.sha256(data).hexdigest()
    if actual != expected:
        raise PersonalOriginError("personal_origin_file_hash_mismatch")
    return data, CONTENT_TYPES.get(path.suffix.lower(), "application/octet-stream")


async def personal_origin_middleware(request: Request, call_next):
    host = request_host(request)
    if host not in admitted_hosts():
        return await call_next(request)

    if request.method != "GET":
        return Response(
            status_code=405,
            headers={
                "Allow": "GET",
                "Cache-Control": "no-store",
                "X-StegVerse-Authority-Effect": "NONE",
            },
        )

    logical = _logical_file(request.url.path)
    if logical is None:
        return Response(
            status_code=404,
            headers={
                "Cache-Control": "no-store",
                "X-StegVerse-Authority-Effect": "NONE",
            },
        )
    try:
        data, content_type = _read_verified(bundle_root(), logical)
    except PersonalOriginError as exc:
        return Response(
            content=json.dumps({"state": "FAIL_CLOSED", "reason": str(exc)}),
            status_code=503,
            media_type="application/json",
            headers={
                "Cache-Control": "no-store",
                "X-StegVerse-Credential-Authority": "TV/TVC",
                "X-StegVerse-Authority-Effect": "NONE",
                "X-StegVerse-Activation-Effect": "false",
            },
        )
    return Response(
        content=data,
        status_code=200,
        media_type=content_type.split(";", 1)[0],
        headers={
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
            "X-StegVerse-Credential-Authority": "TV/TVC",
            "X-StegVerse-Authority-Effect": "NONE",
            "X-StegVerse-Activation-Effect": "false",
            "X-StegVerse-Route-Possession-Grants-Access": "false",
            "X-StegVerse-Private-KV-Readback": "false",
        },
    )
