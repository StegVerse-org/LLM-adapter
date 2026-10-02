"""Establish or verify canonical node standing, and gate the instructions behind it.

`CANONICAL-NODE-INGRESS-CONTRACT-001` makes the discovery host the
`PUBLIC_DISCOVERY_AND_NODE_STANDING_BOUNDARY` and states that every covered
ecosystem entry must cross the canonical ingress contract and either establish
explicit genesis standing or prove continuity from an existing canonical
predecessor. It also states what the continuation is for: *after* an external
machine establishes canonical node state, the ingress exposes the exact
machine-readable continuation needed to reach the adapter.

Until now the advertisement served those instructions to anyone who asked.
Reaching them required nothing, which made the standing requirement a
statement rather than a gate. This module is the gate.

Lineage semantics are not defined here. `lineage_contract.owner` is
`StegVerse-org/StegVerse-SDK` and `local_second_predecessor_semantics_permitted`
is false, so a second definition of a predecessor would itself violate the
contract this module implements. The predecessor field set is therefore read
off the owner's own `successor_predecessor_binding` at import rather than
written down again here: if the owner changes the binding, this boundary
changes with it or fails loudly, instead of quietly admitting a shape the owner
no longer produces.

What the owner's function cannot do from here is re-derive the binding. It
takes the predecessor *manifest and result* and computes their digests; a
standing request carries the digests only, which is the whole point -- the
caller does not ship the ecosystem its prior payloads to prove continuity. So
the check on a declared predecessor is structural: the owner's field set,
exactly, with digests shaped as digests and the generation one below the
successor's. That is a weaker claim than "the lineage was recomputed", and the
disposition says which one it is rather than letting the stronger reading
stand.

What this does not do is authenticate. Structural standing is not authenticated
standing: a caller still supplies its own identity, and
`attestation_owner_state` remains `NOT_PROVEN` with no owner able to furnish
non-caller-editable evidence. So an ALLOW here means the declaration is
well-formed and its lineage holds, not that the declarer is who it says. The
disposition says so in its own fields, and the instructions it releases carry
`NONE_INSTRUCTIONS_ONLY`.
"""
from __future__ import annotations

import re
from typing import Any, Mapping

from stegverse.external_interlock_bootstrap import (
    canonical_sha256,
    successor_predecessor_binding,
)

CONTRACT_ID = "ALL_EXTERNAL_ECOSYSTEM_INGRESS_REQUIRES_CANONICAL_NODE_STANDING"
READINESS_SCHEMA = "stegverse.node-standing-readiness.v1"
DISPOSITION_SCHEMA = "stegverse.node-standing-disposition.v1"

ESTABLISH_GENESIS = "ESTABLISH_GENESIS"
VERIFY_EXISTING = "VERIFY_EXISTING"
MODES = (ESTABLISH_GENESIS, VERIFY_EXISTING)

ALLOW = "ALLOW"
DENY = "DENY"
FAIL_CLOSED = "FAIL_CLOSED"

_HEX64 = re.compile(r"^[0-9a-f]{64}$")


def _owner_predecessor_fields() -> tuple[str, ...]:
    """Read the predecessor field set off the owner, by making it produce one.

    A minimal self-consistent predecessor manifest is enough: the owner's
    function validates it and returns the binding whose keys are the field set.
    Nothing about this probe is a lineage claim -- it is a schema read, and it
    runs once at import so a drifted owner surfaces at startup rather than on
    the first caller.
    """
    body = {"generation": 1}
    manifest = {**body, "manifest_sha256": canonical_sha256(body)}
    binding = successor_predecessor_binding(
        predecessor_manifest=manifest, predecessor_result=None, heartbeat_epoch=1)
    return tuple(binding)


PREDECESSOR_FIELDS = _owner_predecessor_fields()


class StandingRefused(Exception):
    """A refusal carrying its own disposition, so a caller is never left guessing."""

    def __init__(self, disposition: str, reason: str) -> None:
        super().__init__(reason)
        self.disposition = disposition
        self.reason = reason


def readiness() -> dict[str, Any]:
    """Say what standing requires, before anyone attempts it.

    Readiness is not standing. It publishes the requirement so a machine can
    satisfy it on the first attempt rather than discovering the shape by being
    refused, and it grants nothing.
    """
    return {
        "schema": READINESS_SCHEMA,
        "contract_id": CONTRACT_ID,
        "standing_modes": list(MODES),
        "predecessor_key_required": True,
        "null_predecessor_means": "EXPLICIT_GENESIS_ONLY",
        "absent_predecessor_key_disposition": FAIL_CLOSED,
        "predecessor_fields_for_verify_existing": list(PREDECESSOR_FIELDS),
        "ordering": "OSCILLATOR_HEARTBEAT_EPOCH_ONLY",
        "wall_clock_ordering_permitted": False,
        "lineage_owner": "StegVerse-org/StegVerse-SDK",
        "lineage_functions": [
            "stegverse.external_interlock_bootstrap.successor_predecessor_binding",
        ],
        "predecessor_field_set_source": "OWNER_DERIVED_NOT_LOCALLY_DECLARED",
        "declared_predecessor_lineage_recomputed": False,
        "silent_reenrollment_permitted": False,
        "failed_verification_becomes_genesis": False,
        "instructions_released_only_on": ALLOW,
        # Stated here so a reader does not mistake a structural ALLOW for an
        # authenticated one. No owner currently supplies non-caller-editable
        # evidence, and this boundary does not invent one.
        "structural_standing_is_authenticated_standing": False,
        "attestation_owner_state": "NOT_PROVEN",
        "caller_supplied_identity_is_not_authenticated": True,
        "readiness_is_not_standing": True,
        "authority_effect": "NONE_READINESS_ONLY",
    }


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise StandingRefused(FAIL_CLOSED, f"{field} is required")
    return value.strip()


def _verify_predecessor(predecessor: Any) -> dict[str, Any]:
    """Hold a declared predecessor to the owner's field set and digests."""
    if not isinstance(predecessor, Mapping):
        raise StandingRefused(FAIL_CLOSED, "a generation beyond the first declares its predecessor")
    unknown = sorted(set(predecessor) - set(PREDECESSOR_FIELDS))
    if unknown:
        raise StandingRefused(FAIL_CLOSED, "unknown predecessor fields: " + ", ".join(unknown))
    missing = [f for f in PREDECESSOR_FIELDS if f not in predecessor]
    if missing:
        raise StandingRefused(FAIL_CLOSED, "missing predecessor fields: " + ", ".join(missing))
    generation = predecessor["generation"]
    if not isinstance(generation, int) or isinstance(generation, bool) or generation < 1:
        raise StandingRefused(FAIL_CLOSED, "predecessor.generation must be an integer of at least 1")
    for field in ("manifest_sha256", "result_sha256"):
        if not _HEX64.match(str(predecessor[field])):
            raise StandingRefused(FAIL_CLOSED, f"predecessor.{field} must be a sha256 digest")
    epoch = predecessor["heartbeat_epoch"]
    if not isinstance(epoch, int) or isinstance(epoch, bool) or epoch < 1:
        raise StandingRefused(FAIL_CLOSED, "predecessor.heartbeat_epoch must be a positive oscillator count")
    return dict(predecessor)


def resolve(request: Any) -> dict[str, Any]:
    """Resolve a standing request to ALLOW, DENY or FAIL_CLOSED.

    ALLOW means the mode, the generation and the predecessor lineage are
    coherent. It does not mean the caller is authenticated, and a failed
    VERIFY_EXISTING never becomes a genesis.
    """
    if not isinstance(request, Mapping):
        raise StandingRefused(FAIL_CLOSED, "standing request must be an object")

    mode = _text(request.get("mode"), "mode")
    if mode not in MODES:
        raise StandingRefused(DENY, f"unsupported standing mode: {mode}")
    node_ref = _text(request.get("node_ref"), "node_ref")

    if "predecessor" not in request:
        # An absent key is an unstated chain position. Reading it as genesis is
        # exactly the defaulting the contract forbids.
        raise StandingRefused(FAIL_CLOSED, "predecessor must be declared, as null for explicit genesis")
    predecessor = request["predecessor"]
    generation = request.get("generation")

    if mode == ESTABLISH_GENESIS:
        if predecessor is not None:
            raise StandingRefused(DENY, "explicit genesis declares no predecessor")
        if generation is not None and generation != 1:
            raise StandingRefused(DENY, "explicit genesis is generation 1")
        resolved_generation = 1
        resolved_predecessor = None
    else:
        if not isinstance(generation, int) or isinstance(generation, bool) or generation < 2:
            raise StandingRefused(FAIL_CLOSED, "verified standing is generation 2 or beyond")
        resolved_predecessor = _verify_predecessor(predecessor)
        if resolved_predecessor["generation"] != generation - 1:
            # A failure here is a failure. It does not fall back to genesis.
            raise StandingRefused(FAIL_CLOSED, "predecessor.generation must be this generation less one")
        resolved_generation = generation

    return {
        "schema": DISPOSITION_SCHEMA,
        "contract_id": CONTRACT_ID,
        "disposition": ALLOW,
        "standing_mode": mode,
        "node_ref": node_ref,
        "generation": resolved_generation,
        "predecessor": resolved_predecessor,
        "structural_standing_only": True,
        "declared_predecessor_lineage_recomputed": False,
        "structural_standing_is_authenticated_standing": False,
        "attestation_owner_state": "NOT_PROVEN",
        "silent_reenrollment_occurred": False,
        "authority_effect": "NONE_STANDING_ONLY",
    }


def refusal(error: StandingRefused, *, mode: Any = None) -> dict[str, Any]:
    """Render a refusal as a disposition rather than an opaque error."""
    return {
        "schema": DISPOSITION_SCHEMA,
        "contract_id": CONTRACT_ID,
        "disposition": error.disposition,
        "standing_mode": mode if isinstance(mode, str) else None,
        "reason": error.reason,
        "instructions_released": False,
        "silent_reenrollment_occurred": False,
        "authority_effect": "NONE_REFUSAL_ONLY",
    }
