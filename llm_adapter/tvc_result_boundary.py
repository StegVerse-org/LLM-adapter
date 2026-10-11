"""Shared fail-closed credential-key guard for TVC provider operation results.

A clean TVC use receipt cannot override credential material embedded in the result
the broker returns, so every TVC broker refuses a result whose mapping keys name
credential material at any depth. No authority is created here.
"""
from __future__ import annotations

import re
from typing import Any, Mapping

# Keys are compared after lowercasing and dropping non-alphanumerics, so spelling
# variants (apiKey, x-api-key, deepseek_api_key) cannot slip past the guard.
CREDENTIAL_RESULT_KEYS = frozenset({"apikey", "xapikey", "accesstoken", "refreshtoken", "bearertoken", "secret",
                                    "secretvalue", "credentialmaterial", "authorization", "password"})
MAX_RESULT_DEPTH = 64


def credential_key(key: Any) -> bool:
    if not isinstance(key, str):
        return False
    normalized = re.sub(r"[^a-z0-9]", "", key.lower())
    return normalized in CREDENTIAL_RESULT_KEYS or normalized.endswith("apikey")


def _contains(value: Any, depth: int, error: type[Exception], label: str) -> bool:
    if depth > MAX_RESULT_DEPTH:
        raise error(f"{label} exceeds nesting limit")
    if isinstance(value, Mapping):
        return any(credential_key(k) or _contains(v, depth + 1, error, label) for k, v in value.items())
    if isinstance(value, (list, tuple)):
        return any(_contains(v, depth + 1, error, label) for v in value)
    return False


def reject_credential_fields(value: Any, *, error: type[Exception], label: str) -> None:
    """Raise ``error`` when any mapping key at any depth of ``value`` names credential material."""
    if _contains(value, 0, error, label):
        raise error(f"{label} contains credential material")


__all__ = ["CREDENTIAL_RESULT_KEYS", "MAX_RESULT_DEPTH", "credential_key", "reject_credential_fields"]
