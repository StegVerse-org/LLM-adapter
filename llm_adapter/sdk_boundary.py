"""Expose the SDK at the adapter boundary, machine-readably, behind standing.

A node that establishes standing is told the SDK is where it builds its
manifest -- and until now it was told that about Python functions it had no way
to call. `stegverse.manifest_builder.build_manifest` and
`governed_manifest_ingress.process_manifest` are source-callable, which the
SDK's own contract says plainly:

    receiving_surface_state: SOURCE_CALLABLE_REQUIRES_EXISTING_AUTHENTIC_ENDPOINT_BINDING
    missing_binding_disposition: FAIL_CLOSED

So the instructions named a continuation that no caller could reach over the
transport it arrived on. This module is that binding.

What it deliberately does not do is restate the SDK. No schema is copied here,
no parameter list, no capability vocabulary. The caller is told to discover the
boundary, and the boundary answers -- because the SDK's refusals are generated
by the code that enforces them and therefore cannot drift from it. A declared
copy of a shape alongside the code that checks it would be a second authority
on that shape, and the stale one.

Discovery is free, which is what makes this work: validation takes a manifest
and returns, touching nothing. A caller may build, be refused, correct and
retry as many times as it needs without submitting anything, minting a receipt
or causing a transition. Only submission has consequence, and it happens once
the manifest is already accepted.

Standing is re-declared on every call rather than exchanged for a token. The
micronode policy prefers one-shot operation and denies durable coupling, so
there is no session to hold and nothing to expire; each request proves its own
standing or is refused as `direct_bypass_without_standing: FAIL_CLOSED`.

Nothing here grants authority. The boundary builds, checks and carries. It
decides no processing -- that remains the manifest's declared capability bound
to its declared route.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any, Mapping

from stegverse.machine_contract import sdk_machine_contract

from . import node_standing
from stegverse.manifest_contract import validate_ingress_manifest as sdk_validate_manifest

from .governed_manifest_ingress import ALLOWED_MODES, process_manifest

ROOT = Path(__file__).resolve().parents[1]

BOUNDARY_SCHEMA = "stegverse.sdk-boundary.v1"
REJECTION_SCHEMA = "stegverse.sdk-boundary-rejection.v1"
RECORD_SCHEMA = "stegverse.sdk-boundary-crossing-record/v1"
BOUNDARY = "LLM_ADAPTER_SDK_BOUNDARY"

#: What each surface is, and whether crossing it changes ecosystem state.
#:
#: `organization_scope_rule` is that every state transition within the
#: organization emits a receipt, so every crossing of this boundary is recorded.
#: Two of these surfaces are reads: the contract is the SDK's own declaration
#: and validation is side-effect-free, which is why a caller may retry them
#: freely. Recording them as transitions would claim a read mutated something,
#: so the record says which it was rather than flattening the difference.
SURFACES: Mapping[str, Mapping[str, Any]] = {
    "CONTRACT": {"transition_class": "SDK_CONTRACT_DISCOVERED", "state_changed": False},
    "MANIFEST_BUILD": {"transition_class": "SDK_MANIFEST_BUILT", "state_changed": True},
    "MANIFEST_VALIDATE": {"transition_class": "SDK_MANIFEST_VALIDATED", "state_changed": False},
    # Submit returns a handoff, not a runtime result. The class says so, because
    # a receipt reading SUBMITTED would imply the transition completed here.
    "MANIFEST_SUBMIT": {"transition_class": "SDK_MANIFEST_HANDED_OFF", "state_changed": True},
}


def require_standing(payload: Any) -> dict[str, Any]:
    """Resolve the standing this request declares, or refuse it.

    Raised refusals carry the contract's own disposition, so a caller that
    skipped standing is told that is what it did.
    """
    standing = payload.get("standing") if isinstance(payload, Mapping) else None
    if not isinstance(standing, Mapping):
        raise node_standing.StandingRefused(
            node_standing.FAIL_CLOSED,
            "declare standing on every call: direct_bypass_without_standing is FAIL_CLOSED")
    return node_standing.resolve(standing)


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


def crossing_record(surface: str, standing: Mapping[str, Any],
                    payload: Mapping[str, Any], result: Mapping[str, Any]) -> dict[str, Any]:
    """What a crossing of this boundary recorded.

    Digests, not payloads. A caller's arguments and a manifest's contents are
    its own; what the chain needs is that this node crossed this surface and
    what came back, bound so neither can be swapped afterwards.
    """
    declared = SURFACES[surface]
    issued = standing["manifest_fields"]
    accepted = result.get("accepted")
    return {
        "schema": RECORD_SCHEMA,
        "boundary": BOUNDARY,
        "surface": surface,
        "node_endpoint": issued["node_endpoint"],
        "generation": issued["generation"],
        "predecessor": issued["predecessor"],
        "request_sha256": _sha(dict(payload)),
        "result_sha256": _sha(dict(result)),
        # A surface that only reads is not a transition of ecosystem state, and
        # neither is a refused crossing of one that otherwise would be: a build
        # that was refused produced no manifest. The declared capability of the
        # surface and what this crossing actually changed are different claims.
        "state_changed": bool(declared["state_changed"]) and accepted is not False,
        "surface_can_change_state": declared["state_changed"],
        "surface_is_side_effect_free": not declared["state_changed"],
        "accepted": accepted if isinstance(accepted, bool) else None,
        # A refused crossing is still a crossing: the caller learns the shape by
        # being refused, and a chain that dropped refusals would show only the
        # attempts that happened to succeed.
        "refusal_stage": result.get("stage") if accepted is False else None,
        "sdk_refusal_is_verbatim": result.get("rejection_is_verbatim_from_the_sdk"),
        "structural_standing_is_authenticated_standing": False,
        "attestation_owner_state": standing["attestation_owner_state"],
        "authority_effect": "NONE_CROSSING_RECORD_ONLY",
    }


def record(surface: str, standing: Mapping[str, Any], payload: Mapping[str, Any],
           result: Mapping[str, Any], *, hb_epoch: int | None = None) -> dict[str, Any]:
    """Append this crossing to the repository's transition ledger."""
    if surface not in SURFACES:
        raise ValueError("unrecorded SDK boundary surface: " + str(surface))
    crossing = crossing_record(surface, standing, payload, result)
    return _ledger().append(
        SURFACES[surface]["transition_class"] + ":" + crossing["node_endpoint"]["node_id"],
        SURFACES[surface]["transition_class"],
        crossing["request_sha256"], crossing["result_sha256"],
        crossing, "NONE", hb_epoch=hb_epoch)


def rejected(reason: str, *, stage: str) -> dict[str, Any]:
    """Return the SDK's own refusal, verbatim.

    The message is not summarised or reworded. It is how a caller discovers the
    shape it got wrong, and paraphrasing it would put this boundary between the
    caller and the only authority on that shape.
    """
    return {
        "schema": REJECTION_SCHEMA,
        "accepted": False,
        "stage": stage,
        "sdk_rejection": reason,
        "rejection_is_verbatim_from_the_sdk": True,
        "discovery_is_side_effect_free": True,
        "retry_permitted": True,
        "authority_effect": "NONE_REJECTION_ONLY",
    }


def contract() -> dict[str, Any]:
    """Serve the SDK's own machine contract: what a caller may ask for."""
    return {
        "schema": BOUNDARY_SCHEMA,
        "surface": "SDK_MACHINE_CONTRACT",
        "sdk_machine_contract": sdk_machine_contract(),
        "contract_is_the_sdk_declaration_not_a_copy": True,
        "discover_request_shape_by_validating": True,
        "authority_effect": "NONE_DISCLOSURE_ONLY",
    }


def build(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Build a manifest from the caller's arguments, or return why it could not.

    Arguments are passed to the SDK builder as given. This boundary does not
    check them first: the builder is the authority on its own parameters, and a
    check here would be a second one.
    """
    from stegverse.manifest_builder import build_manifest

    arguments = payload.get("arguments")
    if not isinstance(arguments, Mapping):
        return rejected("arguments must be an object of builder parameters; "
                        "see sdk_machine_contract.builder.required_parameters",
                        stage="ARGUMENTS")
    try:
        manifest = build_manifest(**dict(arguments))
    except TypeError as exc:
        return rejected(str(exc), stage="BUILD")
    except ValueError as exc:
        return rejected(str(exc), stage="BUILD")
    return {
        "schema": BOUNDARY_SCHEMA,
        "surface": "MANIFEST_BUILD",
        "accepted": True,
        "manifest": manifest,
        "nothing_was_submitted": True,
        "authority_effect": "NONE_CONSTRUCTION_ONLY",
    }


def validate(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Check a manifest and return the SDK's verdict. Touches nothing."""
    manifest = payload.get("manifest")
    if not isinstance(manifest, Mapping):
        return rejected("manifest must be an object", stage="ARGUMENTS")
    try:
        canonical = sdk_validate_manifest(manifest)
    except ValueError as exc:
        return rejected(str(exc), stage="VALIDATE")
    return {
        "schema": BOUNDARY_SCHEMA,
        "surface": "MANIFEST_VALIDATE",
        "accepted": True,
        "canonical_manifest": canonical,
        "declared_processing": canonical.get("processing"),
        "nothing_was_submitted": True,
        "authority_effect": "NONE_VALIDATION_ONLY",
    }


def installed_runtime(transfer: Mapping[str, Any]) -> dict[str, Any]:
    """Hand the transfer's manifest to the runtime the SDK says is installed.

    Every published route declares `runtime_installed: true` bound to
    `stegverse.manifest_state_transition_runtime.execute_manifest`, so the
    receiver was never missing -- it was simply never bound. The destination is
    not chosen here: `DESTINATION_RESOLUTION_SOURCE` is
    `CANONICAL_CONNECTOR_CAPABILITY_OVERLAY`, so the capability overlay
    resolves it and this boundary carries the manifest to the runtime that asks
    the overlay.
    """
    from stegverse.manifest_state_transition_runtime import execute_manifest

    return execute_manifest(transfer["manifest"])


def submit(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Hand an accepted manifest to the installed runtime and return the handoff.

    What comes back is a handoff disposition, not a result. The SDK states why:
    it does not perform the transition and does not wait for one, and a result
    arrives separately through `admit_runtime_result`. So a caller that reads
    this as a result has misread it, and the response says which it is.

    That asynchrony is the reason a chain is required rather than optional.
    Handoff is one transition and the result arriving is another; between them
    sits a gap that a response body cannot represent. When the receiver is
    unavailable the SDK's own disposition is
    `DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION` -- the work persists or
    re-materializes rather than being dropped.
    """
    manifest = payload.get("manifest")
    if not isinstance(manifest, Mapping):
        return rejected("manifest must be an object", stage="ARGUMENTS")
    mode = str(payload.get("mode") or "").upper()
    if mode not in ALLOWED_MODES:
        return rejected("mode must be one of " + ", ".join(sorted(ALLOWED_MODES)), stage="ARGUMENTS")

    envelope = process_manifest(manifest, mode=mode,
                                standing=payload.get("standing_evidence") or {},
                                sdk_manifest_endpoint=installed_runtime)
    return {
        "schema": BOUNDARY_SCHEMA,
        "surface": "MANIFEST_SUBMIT",
        "handed_off": True,
        "result_is_a_handoff_not_a_runtime_result": True,
        "result_arrives_separately_through": "stegverse.manifest_state_transition_runtime.admit_runtime_result",
        "destination_resolution_source": "CANONICAL_CONNECTOR_CAPABILITY_OVERLAY",
        "receiver_unavailable_disposition": "DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION",
        "envelope": envelope,
        "authority_effect": "NONE_HANDOFF_ONLY",
    }


__all__ = ["require_standing", "contract", "build", "validate", "submit",
           "installed_runtime", "process_manifest", "record", "crossing_record",
           "BOUNDARY", "BOUNDARY_SCHEMA", "RECORD_SCHEMA", "REJECTION_SCHEMA", "SURFACES"]
