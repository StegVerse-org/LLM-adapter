from __future__ import annotations

import os
import re
import stat
from pathlib import Path

from fastapi import HTTPException
from fastapi.responses import PlainTextResponse

DEFAULT_CHALLENGE_ROOT = Path("/var/lib/stegverse/tvc/http01")
TOKEN_RE = re.compile(r"^[A-Za-z0-9_-]{1,128}$")
MAX_CHALLENGE_BYTES = 512


class HTTP01ProjectionError(ValueError):
    pass


def challenge_root() -> Path:
    raw = os.getenv("STEGVERSE_TVC_HTTP01_CHALLENGE_ROOT", "").strip()
    root = Path(raw).expanduser() if raw else DEFAULT_CHALLENGE_ROOT
    if not root.is_absolute():
        raise HTTP01ProjectionError("challenge_root_must_be_absolute")
    if root.is_symlink():
        raise HTTP01ProjectionError("challenge_root_symlink_forbidden")
    return root.resolve()


def read_http01_challenge(token: str, *, root: Path | None = None) -> str:
    if not TOKEN_RE.fullmatch(token or ""):
        raise HTTP01ProjectionError("http01_token_invalid")
    boundary = (root or challenge_root()).expanduser()
    if not boundary.is_absolute():
        raise HTTP01ProjectionError("challenge_root_must_be_absolute")
    if boundary.is_symlink():
        raise HTTP01ProjectionError("challenge_root_symlink_forbidden")
    boundary = boundary.resolve()
    candidate = boundary / token
    if candidate.is_symlink():
        raise HTTP01ProjectionError("http01_challenge_symlink_forbidden")
    try:
        resolved = candidate.resolve(strict=True)
    except FileNotFoundError as exc:
        raise HTTP01ProjectionError("http01_challenge_not_found") from exc
    try:
        resolved.relative_to(boundary)
    except ValueError as exc:
        raise HTTP01ProjectionError("http01_challenge_path_escape") from exc
    st = resolved.lstat()
    if not stat.S_ISREG(st.st_mode):
        raise HTTP01ProjectionError("http01_challenge_not_regular")
    if st.st_size < 1 or st.st_size > MAX_CHALLENGE_BYTES:
        raise HTTP01ProjectionError("http01_challenge_size_invalid")
    value = resolved.read_text(encoding="ascii").strip()
    if not value or len(value.encode("ascii")) > MAX_CHALLENGE_BYTES:
        raise HTTP01ProjectionError("http01_challenge_value_invalid")
    if any(ch.isspace() for ch in value):
        raise HTTP01ProjectionError("http01_challenge_whitespace_forbidden")
    return value


def http01_challenge_response(token: str) -> PlainTextResponse:
    try:
        value = read_http01_challenge(token)
    except HTTP01ProjectionError as exc:
        reason = str(exc)
        status = 404 if reason == "http01_challenge_not_found" else 400
        raise HTTPException(status_code=status, detail=reason) from exc
    return PlainTextResponse(
        value,
        status_code=200,
        headers={
            "Cache-Control": "no-store",
            "X-StegVerse-Credential-Authority": "TV/TVC",
            "X-StegVerse-Authority-Effect": "NONE",
        },
    )
