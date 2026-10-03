"""The LLM-adapter's ingress boundary: where a signal arrives and becomes a node.

Establishing a healthy node *is* ingress, so this is where the recording starts.
Nothing upstream of here emitted anything: a device registered, standing was
resolved, instructions were issued, and the ecosystem kept no record that any of
it happened.

This is a boundary, not a route handler, and the distinction decides the shape.
A receipt minted inside the registration handler would be a property of that
handler and therefore of HTTP. The ingress record is a property of the crossing:
`transport` names how the signal arrived, and the record is the same record
whichever transport carried it. HTTP is the transport today. The next stage puts
an external ingress point -- an ephemeral StegBrowser, a StegNode, or a device
that already understands the manifest protocol -- on the far side of
Interlock/InTr with its egress at this boundary. That swaps the transport and
leaves this boundary, and this record, unchanged.

The order is the one the organization boundary already uses, for the same
reason. Standing and class are resolved first, and only an admitted signal mints
a receipt: a refused registration established no node, so it must not leave a
chain implying one was admitted. A refusal is still answered as a disposition.

What the record carries is what makes this the record of ingress -- the node's
declared identity and class, the chain position the boundary issued it, the
health it was told about, and the continuation it was instructed to use. A
reader of the chain can see which node arrived, over what, and what it was told
to do next.

Non-authorizing. Admission here is structural, not authenticated: the caller
still supplies its own identity, `attestation_owner_state` stays `NOT_PROVEN`,
and the receipt records that rather than letting a chain entry read as proof of
who arrived.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any, Callable, Mapping

from . import node_standing

ROOT = Path(__file__).resolve().parents[1]
BOUNDARY = "LLM_ADAPTER_INGRESS_BOUNDARY"
TRANSITION_CLASS = "NODE_INGRESS_ADMITTED"
RECORD_SCHEMA = "stegverse.node-ingress-record/v1"

#: The transports this boundary can be reached over. HTTP is installed;
#: Interlock/InTr is the next stage and is named so a reader can see that the
#: boundary is the constant and the transport is not.
HTTP = "HTTP"
INTERLOCK_INTR = "INTERLOCK_INTR"
TRANSPORTS = {HTTP: "INSTALLED", INTERLOCK_INTR: "NOT_YET_ENABLED"}


def _ledger():
    """This repository's own transition ledger, loaded as the module it is."""
    spec = importlib.util.spec_from_file_location(
        "repo_transition_emit", ROOT / ".stegverse/transition-ledger/emit.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha(value: Any) -> str:
    return "sha256:" + hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"),
                   ensure_ascii=False).encode("utf-8")).hexdigest()


def transport_state(transport: str) -> str:
    state = TRANSPORTS.get(transport)
    if state is None:
        raise node_standing.StandingRefused(
            node_standing.FAIL_CLOSED, "unsupported ingress transport: " + str(transport))
    return state


def ingress_record(signal: Mapping[str, Any], disposition: Mapping[str, Any],
                   profile: str, node_class: str, transport: str,
                   health: Mapping[str, Any] | None) -> dict[str, Any]:
    """What this crossing recorded about the node that arrived.

    Boundary-issued fields are kept apart from caller-declared ones, because a
    caller writing `recognized` about itself is the fabricated-identity bypass
    and a chain that mixed the two would make the distinction unreadable.
    """
    issued = disposition["manifest_fields"]
    return {
        "schema": RECORD_SCHEMA,
        "boundary": BOUNDARY,
        "transport": transport,
        "transport_state": transport_state(transport),
        # Who arrived, as the boundary recognized them.
        "node_endpoint": issued["node_endpoint"],
        "node_class": node_class,
        "node_standing_mode": issued["node_standing_mode"],
        "generation": issued["generation"],
        "predecessor": issued["predecessor"],
        "manifest_fields_are_boundary_issued_not_caller_asserted": True,
        # What the node was told, so the record shows what it was instructed to do.
        "continuation_profile": profile,
        "healthy_node_established": True,
        "node_health_status": (health or {}).get("status"),
        # What arrived, by digest, without copying a caller's payload into the chain.
        "signal_sha256": _sha(dict(signal)),
        # Recorded as declared and selecting nothing.
        **node_standing.declared_ingress(signal),
        # An admitted crossing is not an authenticated one.
        "structural_standing_is_authenticated_standing": False,
        "attestation_owner_state": disposition["attestation_owner_state"],
        "caller_supplied_identity_is_not_authenticated": True,
        "authority_effect": "NONE_INGRESS_RECORD_ONLY",
    }


def admit(signal: Mapping[str, Any], *, transport: str = HTTP,
          health: Callable[[], Mapping[str, Any]] | None = None,
          hb_epoch: int | None = None) -> dict[str, Any]:
    """Admit a signal at this boundary, record the ingress, and return the packet.

    Raises `StandingRefused` for a signal that establishes no node. Nothing is
    recorded in that case -- the refusal is the answer, and the chain stays free
    of an entry implying a node was admitted.
    """
    transport_state(transport)
    # Resolved before anything is minted, so a refusal leaves no chain entry.
    disposition = node_standing.resolve(signal)
    node_class = node_standing.node_class(signal)
    profile = node_standing.continuation_profile(signal)
    observed = health() if health is not None else None

    record = ingress_record(signal, disposition, profile, node_class, transport, observed)
    receipt = _ledger().append(
        # The node's own reference names the transition, so the chain is
        # searchable by the node that arrived.
        TRANSITION_CLASS + ":" + record["node_endpoint"]["node_id"],
        TRANSITION_CLASS,
        # Before: the signal as it arrived. After: the ingress this boundary issued.
        record["signal_sha256"],
        _sha(record),
        record,
        "NONE",
        hb_epoch=hb_epoch)
    return {
        "disposition": disposition,
        "node_class": node_class,
        "continuation_profile": profile,
        "ingress_record": record,
        # Returned so the node can cite its own ingress rather than assert it.
        "ingress_receipt_sha256": receipt["receipt_sha256"],
        "ingress_transition_id": receipt["transition_id"],
        "ingress_recorded_at_boundary": BOUNDARY,
        "ingress_ordering": receipt["ordering"],
    }


__all__ = ["BOUNDARY", "HTTP", "INTERLOCK_INTR", "TRANSPORTS", "TRANSITION_CLASS",
           "RECORD_SCHEMA", "admit", "ingress_record", "transport_state"]
