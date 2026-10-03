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

from typing import Any, Mapping

from stegverse.machine_contract import sdk_machine_contract

from . import node_standing
from .governed_manifest_ingress import ALLOWED_MODES, process_manifest, validate_ingress_manifest

BOUNDARY_SCHEMA = "stegverse.sdk-boundary.v1"
REJECTION_SCHEMA = "stegverse.sdk-boundary-rejection.v1"


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
        canonical = validate_ingress_manifest(manifest)
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


def submit(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Submit an accepted manifest, or say why submission cannot happen here.

    `process_manifest` requires a bound far-side receiver, and the SDK contract
    records that the binding does not exist:
    `missing_binding_disposition: FAIL_CLOSED`. So this refuses rather than
    inventing a receiver, and names what is missing instead of failing
    obscurely. Build and validate work today; submission waits on that binding.
    """
    manifest = payload.get("manifest")
    if not isinstance(manifest, Mapping):
        return rejected("manifest must be an object", stage="ARGUMENTS")
    mode = str(payload.get("mode") or "").upper()
    if mode not in ALLOWED_MODES:
        return rejected("mode must be one of " + ", ".join(sorted(ALLOWED_MODES)), stage="ARGUMENTS")
    try:
        validate_ingress_manifest(manifest)
    except ValueError as exc:
        return rejected(str(exc), stage="VALIDATE")
    return {
        "schema": BOUNDARY_SCHEMA,
        "surface": "MANIFEST_SUBMIT",
        "accepted": False,
        "disposition": "FAIL_CLOSED",
        "reason": "no_authentic_far_side_receiver_is_bound",
        "missing_binding": "governed_manifest_ingress.process_manifest(sdk_manifest_endpoint=...)",
        "sdk_contract_states": "SOURCE_CALLABLE_REQUIRES_EXISTING_AUTHENTIC_ENDPOINT_BINDING",
        "manifest_was_accepted_by_validation": True,
        "what_this_means": "the manifest is well-formed and would submit; the receiver does not exist yet",
        "authority_effect": "NONE_REFUSAL_ONLY",
    }


__all__ = ["require_standing", "contract", "build", "validate", "submit",
           "process_manifest", "BOUNDARY_SCHEMA", "REJECTION_SCHEMA"]
