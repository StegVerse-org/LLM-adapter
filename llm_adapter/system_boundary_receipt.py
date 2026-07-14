"""Deterministic receipt support for adapter system-boundary declarations.

Receipts bind a declaration to canonical content. They are evidence records only;
they do not grant execution authority, custody, admissibility, or standing.
"""

from __future__ import annotations

import json
from hashlib import sha256
from typing import Any, Mapping


def canonical_json(value: Mapping[str, Any]) -> str:
    """Return stable JSON suitable for hashing and replay comparison."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def declaration_content_view(declaration: Mapping[str, Any]) -> dict[str, Any]:
    """Return identity-bearing declaration content without observation metadata."""
    required = {
        "schema_version",
        "system_id",
        "surfaces",
        "continuity",
        "authority",
        "claims_boundary",
    }
    missing = sorted(required - set(declaration))
    if missing:
        raise ValueError(f"declaration missing identity fields: {', '.join(missing)}")

    authority = declaration.get("authority")
    claims = declaration.get("claims_boundary")
    if not isinstance(authority, Mapping) or authority.get("model_has_execution_authority") is not False:
        raise ValueError("declaration must preserve model_has_execution_authority=false")
    if not isinstance(claims, Mapping):
        raise ValueError("declaration claims_boundary is required")
    for key in ("consciousness_claim", "personhood_claim", "welfare_claim"):
        if claims.get(key) != "not_evaluated":
            raise ValueError(f"declaration must preserve {key}=not_evaluated")

    return {key: declaration[key] for key in sorted(required)}


def derive_declaration_id(declaration: Mapping[str, Any]) -> str:
    """Derive a replay-stable declaration identifier from canonical content."""
    digest = sha256(canonical_json(declaration_content_view(declaration)).encode("utf-8")).hexdigest()
    return f"sbd:sha256:{digest}"


def build_system_boundary_receipt(
    declaration: Mapping[str, Any],
    *,
    source_commit: str | None = None,
    previous_receipt_hash: str | None = None,
) -> dict[str, Any]:
    """Build a deterministic, non-authorizing receipt for a declaration."""
    content = declaration_content_view(declaration)
    declaration_id = derive_declaration_id(declaration)
    supplied_id = declaration.get("declaration_id")
    if supplied_id and supplied_id != declaration_id:
        raise ValueError("supplied declaration_id does not match canonical content")

    receipt_body: dict[str, Any] = {
        "schema_version": "system_boundary_declaration_receipt.v1",
        "declaration_id": declaration_id,
        "declaration_hash": f"sha256:{sha256(canonical_json(content).encode('utf-8')).hexdigest()}",
        "system_id": declaration["system_id"],
        "evidence_refs": list(declaration.get("continuity", {}).get("evidence_refs", [])),
        "source_commit": source_commit,
        "previous_receipt_hash": previous_receipt_hash,
        "authority_boundary": {
            "receipt_is_execution_authority": False,
            "receipt_is_admissibility": False,
            "receipt_is_custody": False,
            "declaration_proves_consciousness": False,
        },
    }
    receipt_hash = sha256(canonical_json(receipt_body).encode("utf-8")).hexdigest()
    return {**receipt_body, "receipt_hash": f"sha256:{receipt_hash}"}


def verify_system_boundary_receipt(
    declaration: Mapping[str, Any], receipt: Mapping[str, Any]
) -> bool:
    """Verify a receipt by deterministic reconstruction."""
    expected = build_system_boundary_receipt(
        declaration,
        source_commit=receipt.get("source_commit"),
        previous_receipt_hash=receipt.get("previous_receipt_hash"),
    )
    return dict(receipt) == expected
