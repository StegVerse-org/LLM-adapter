"""Explicit governed-session lifecycle binding for system-boundary evidence.

This module is intentionally not wired into the production gateway automatically.
Callers must opt in after a bounded governed response exists. Binding adds evidence
only; it does not grant execution authority, admissibility, custody, or publication.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from .system_boundary import build_system_boundary_declaration, default_adapter_system_boundary
from .system_boundary_receipt import (
    build_system_boundary_receipt,
    derive_declaration_id,
    verify_system_boundary_receipt,
)


def _required_text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} is required")
    return value


def _evidence_refs(payload: Mapping[str, Any], transition_id: str, run_id: str) -> tuple[str, ...]:
    refs = [f"transition://{transition_id}", f"run://{run_id}"]
    for key in ("final_receipt_id", "receipt_id"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            refs.append(value)
    return tuple(dict.fromkeys(refs))


def bind_system_boundary_to_lifecycle(
    payload: Mapping[str, Any],
    *,
    session_id: str,
    transition_id: str,
    run_id: str,
    generated_at: str,
    source_commit: str | None = None,
    previous_receipt_hash: str | None = None,
) -> dict[str, Any]:
    """Bind a deterministic declaration and receipt to a governed response.

    Replay of an already valid identical binding is idempotent. Existing invalid or
    conflicting binding fields fail closed rather than being overwritten.
    """
    if not isinstance(payload, Mapping):
        raise TypeError("payload must be a mapping")

    session_id = _required_text(session_id, "session_id")
    transition_id = _required_text(transition_id, "transition_id")
    run_id = _required_text(run_id, "run_id")
    generated_at = _required_text(generated_at, "generated_at")

    for key, expected in (("transition_id", transition_id), ("run_id", run_id)):
        existing = payload.get(key)
        if existing is not None and existing != expected:
            raise ValueError(f"payload {key} does not match lifecycle identity")

    existing_declaration = payload.get("system_boundary_declaration")
    existing_receipt = payload.get("system_boundary_declaration_receipt")
    existing_ref = payload.get("system_boundary_declaration_ref")
    present = [item is not None for item in (existing_declaration, existing_receipt, existing_ref)]
    if any(present) and not all(present):
        raise ValueError("partial system-boundary lifecycle binding is not allowed")
    if all(present):
        if not isinstance(existing_declaration, Mapping) or not isinstance(existing_receipt, Mapping):
            raise ValueError("existing system-boundary binding must contain objects")
        if not verify_system_boundary_receipt(existing_declaration, existing_receipt):
            raise ValueError("existing system-boundary receipt verification failed")
        if not isinstance(existing_ref, Mapping):
            raise ValueError("existing system_boundary_declaration_ref must be an object")
        if existing_ref.get("declaration_id") != existing_receipt.get("declaration_id"):
            raise ValueError("existing declaration reference conflicts with receipt")
        return deepcopy(dict(payload))

    refs = _evidence_refs(payload, transition_id, run_id)
    config = default_adapter_system_boundary(
        session_ref=f"session://{session_id}",
        receipt_refs=refs,
    )

    provisional = build_system_boundary_declaration(
        config,
        declaration_id="pending-canonical-identity",
        generated_at=generated_at,
    )
    declaration_id = derive_declaration_id(provisional)
    declaration = build_system_boundary_declaration(
        config,
        declaration_id=declaration_id,
        generated_at=generated_at,
    )
    receipt = build_system_boundary_receipt(
        declaration,
        source_commit=source_commit,
        previous_receipt_hash=previous_receipt_hash,
    )

    result = deepcopy(dict(payload))
    result["system_boundary_declaration"] = declaration
    result["system_boundary_declaration_receipt"] = receipt
    result["system_boundary_declaration_ref"] = {
        "algorithm": "sha256",
        "digest": receipt["declaration_hash"].removeprefix("sha256:"),
        "declaration_id": declaration_id,
        "receipt_hash": receipt["receipt_hash"],
        "authorizing": False,
        "custody_transferred": False,
        "admissibility_determined": False,
        "production_binding_enabled": False,
    }
    result.setdefault("authority", {})["system_boundary_declaration_is_execution_authority"] = False
    result["authority"]["system_boundary_receipt_is_master_records_custody"] = False
    return result
