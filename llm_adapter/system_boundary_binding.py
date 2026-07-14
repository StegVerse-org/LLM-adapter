"""Legacy-compatible binding of system-boundary declarations to adapter payloads.

The binder copies the source payload and adds declaration metadata without
performing execution, persistence, custody transfer, or admissibility decisions.
"""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from typing import Any, Mapping

from .system_boundary import SystemBoundaryConfig, build_system_boundary_declaration


def canonical_sha256(value: Mapping[str, Any]) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return sha256(encoded).hexdigest()


def bind_system_boundary_declaration(
    payload: Mapping[str, Any],
    *,
    config: SystemBoundaryConfig,
    declaration_id: str,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Return a copied payload with a declaration and deterministic reference.

    Existing payloads remain valid because this function is opt-in. It refuses to
    overwrite either reserved field, preventing ambiguous or conflicting binding.
    """

    if not isinstance(payload, Mapping):
        raise TypeError("payload must be a mapping")
    if "system_boundary_declaration" in payload:
        raise ValueError("payload already contains system_boundary_declaration")
    if "system_boundary_declaration_ref" in payload:
        raise ValueError("payload already contains system_boundary_declaration_ref")

    declaration = build_system_boundary_declaration(
        config,
        declaration_id=declaration_id,
        generated_at=generated_at,
    )
    digest = canonical_sha256(declaration)

    result = deepcopy(dict(payload))
    result["system_boundary_declaration"] = declaration
    result["system_boundary_declaration_ref"] = {
        "algorithm": "sha256",
        "digest": digest,
        "declaration_id": declaration_id,
        "authorizing": False,
        "custody_transferred": False,
        "admissibility_determined": False,
    }
    return result


def verify_system_boundary_binding(payload: Mapping[str, Any]) -> list[str]:
    """Return validation errors for a bound payload, or an empty list on success."""

    errors: list[str] = []
    declaration = payload.get("system_boundary_declaration")
    reference = payload.get("system_boundary_declaration_ref")
    if not isinstance(declaration, Mapping):
        return ["system_boundary_declaration must be an object"]
    if not isinstance(reference, Mapping):
        return ["system_boundary_declaration_ref must be an object"]

    if reference.get("algorithm") != "sha256":
        errors.append("system_boundary_declaration_ref.algorithm must be sha256")
    if reference.get("digest") != canonical_sha256(declaration):
        errors.append("system_boundary_declaration_ref.digest mismatch")
    if reference.get("declaration_id") != declaration.get("declaration_id"):
        errors.append("system_boundary_declaration_ref.declaration_id mismatch")
    for key in ("authorizing", "custody_transferred", "admissibility_determined"):
        if reference.get(key) is not False:
            errors.append(f"system_boundary_declaration_ref.{key} must be false")
    if declaration.get("authority", {}).get("model_has_execution_authority") is not False:
        errors.append("model_has_execution_authority must be false")
    for key in ("consciousness_claim", "personhood_claim", "welfare_claim"):
        if declaration.get("claims_boundary", {}).get(key) != "not_evaluated":
            errors.append(f"claims_boundary.{key} must remain not_evaluated")
    return errors
