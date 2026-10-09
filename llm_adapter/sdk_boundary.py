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

from .governed_manifest_ingress import ALLOWED_MODES, NON_ALLOW_FIELDS, process_manifest

ROOT = Path(__file__).resolve().parents[1]

BOUNDARY_SCHEMA = "stegverse.sdk-boundary.v1"
REJECTION_SCHEMA = "stegverse.sdk-boundary-rejection.v1"
RECORD_SCHEMA = "stegverse.sdk-boundary-crossing-record/v1"
BOUNDARY = "LLM_ADAPTER_SDK_BOUNDARY"

#: The intended action each surface carries.
#:
#: A state transition is the disposition of an intended action, not only a
#: successful one, so every crossing of this boundary is a transition and every
#: crossing is recorded. An earlier version of this file asked a second
#: question -- did some store change? -- and used it to mark a contract read and
#: a refused build as not transitions. That is a definition the ecosystem does
#: not hold: the disposition *is* the transition, and a record saying otherwise
#: understates the chain.
SURFACES: Mapping[str, Mapping[str, Any]] = {
    "CONTRACT": {"transition_class": "SDK_CONTRACT_DISCOVERED",
                 "intended_action": "DISCOVER_THE_SDK_CONTRACT"},
    "MANIFEST_BUILD": {"transition_class": "SDK_MANIFEST_BUILT",
                       "intended_action": "BUILD_A_CANONICAL_MANIFEST"},
    "MANIFEST_VALIDATE": {"transition_class": "SDK_MANIFEST_VALIDATED",
                          "intended_action": "VALIDATE_A_CANONICAL_MANIFEST"},
    # Submit returns a handoff, not a runtime result. The class says so, because
    # a receipt reading SUBMITTED would imply the transition completed here.
    "MANIFEST_SUBMIT": {"transition_class": "SDK_MANIFEST_HANDED_OFF",
                        "intended_action": "HAND_A_MANIFEST_TO_THE_INSTALLED_RUNTIME"},
}

#: The disposition vocabulary this boundary resolves an intended action to.
ALLOW = "ALLOW"
DENY = "DENY"

#: A crossing refused for want of standing. The intended action still arrived
#: and still has a disposition, so it is still a transition; it is recorded
#: under its own class because a reader must not mistake it for a crossing that
#: the standing boundary let through.
REFUSED_CLASS = "SDK_CROSSING_REFUSED_FOR_WANT_OF_STANDING"


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
        # The transition is the disposition of the intended action. A refused
        # build is a transition whose disposition is DENY, not an absence.
        "intended_action": declared["intended_action"],
        "disposition": DENY if accepted is False else ALLOW,
        "transition_is_the_disposition_of_the_intended_action": True,
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


def standing_refusal_record(surface: str, error: node_standing.StandingRefused,
                            payload: Mapping[str, Any]) -> dict[str, Any]:
    """What a crossing refused for want of standing recorded.

    No node endpoint, generation or predecessor appears: the standing boundary
    issued none, and a record naming them would read as a crossing that had
    standing. What the chain needs is that something tried to cross this
    surface, what it sent by digest, and why it was refused.
    """
    declared = SURFACES[surface]
    return {
        "schema": RECORD_SCHEMA,
        "boundary": BOUNDARY,
        "surface": surface,
        "request_sha256": _sha(dict(payload) if isinstance(payload, Mapping) else payload),
        "intended_action": declared["intended_action"],
        "disposition": DENY,
        "transition_is_the_disposition_of_the_intended_action": True,
        "refused_for_want_of_standing": True,
        "standing_disposition": error.disposition,
        "refusal_reason": error.reason,
        "refusal_is_verbatim": True,
        "surface_was_run": False,
        "structural_standing_is_authenticated_standing": False,
        "attestation_owner_state": "NOT_PROVEN",
        "authority_effect": "NONE_CROSSING_RECORD_ONLY",
    }


def record_standing_refusal(surface: str, error: node_standing.StandingRefused,
                            payload: Mapping[str, Any], *,
                            hb_epoch: int | None = None) -> dict[str, Any]:
    """Append a crossing refused for want of standing to the transition ledger."""
    if surface not in SURFACES:
        raise ValueError("unrecorded SDK boundary surface: " + str(surface))
    crossing = standing_refusal_record(surface, error, payload)
    return _ledger().append(
        REFUSED_CLASS + ":" + surface + ":" + crossing["request_sha256"],
        REFUSED_CLASS,
        crossing["request_sha256"], _sha(crossing),
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


ECOSYSTEM_CHAT_CAPABILITY_WORK_CLASSES = ("text", "reasoning", "code", "image", "video", "audio", "science", "research", "data", "other")
ECOSYSTEM_CHAT_TEXT_REASONING_PROCESSING = {
    "capability": "stegbrowser",
    "route_id": "stegverse.route.stegbrowser.v1",
}
ECOSYSTEM_CHAT_ENTITLEMENT_NON_ALLOW = ("UPGRADE_REQUIRED", "PURCHASE_REQUIRED")


def resolve_ecosystem_chat_capability_descriptor(value: Mapping[str, Any]) -> dict[str, Any]:
    """Map canonical Ecosystem Chat capability metadata to an existing route only.

    This boundary never invents a route and never changes provider choice.  The
    generic descriptor is non-authoritative selection input.  Text/reasoning
    external-AI work can use the already-published StegBrowser ephemeral route;
    other work classes remain independently extensible and are refused here
    until an existing compatible adapter is actually installed.
    """
    if not isinstance(value, Mapping):
        raise ValueError("capability_descriptor_must_be_an_object")
    work_class = str(value.get("work_class") or "").strip().lower()
    capability_id = str(value.get("capability_id") or "").strip()
    provider = str(value.get("provider") or "").strip()
    routing_disposition = str(value.get("routing_disposition") or "").strip().upper()
    entitlement_state = str(value.get("entitlement_state") or "").strip().upper()
    evidence_return = str(value.get("evidence_return") or "").strip()
    authority_effect = str(value.get("authority_effect") or "").strip()
    if not capability_id or not provider:
        raise ValueError("capability_descriptor_identity_required")
    if work_class not in ECOSYSTEM_CHAT_CAPABILITY_WORK_CLASSES:
        raise ValueError("capability_descriptor_work_class_invalid")
    if authority_effect != "NONE":
        raise ValueError("capability_descriptor_must_be_non_authoritative")
    if evidence_return != "RETAINED_OBSERVATION_REQUIRED":
        raise ValueError("capability_descriptor_retained_observation_required")
    if routing_disposition in ECOSYSTEM_CHAT_ENTITLEMENT_NON_ALLOW:
        return {
            "accepted": False,
            "stage": "CAPABILITY_ENTITLEMENT",
            "routing_disposition": routing_disposition,
            "entitlement_state": entitlement_state,
            "required_tier": value.get("required_tier"),
            "capability_id": capability_id,
            "work_class": work_class,
            "provider": provider,
            "provider_execution_performed": False,
            "fallback_selected": False,
            "authority_effect": "NONE_REJECTION_ONLY",
        }
    if routing_disposition != "AVAILABLE":
        return {
            "accepted": False,
            "stage": "CAPABILITY_AVAILABILITY",
            "routing_disposition": routing_disposition or "ENTITLEMENT_UNKNOWN",
            "entitlement_state": entitlement_state or "UNKNOWN",
            "capability_id": capability_id,
            "work_class": work_class,
            "provider": provider,
            "provider_execution_performed": False,
            "fallback_selected": False,
            "authority_effect": "NONE_REJECTION_ONLY",
        }
    constraints = value.get("execution_constraints") or {}
    if not isinstance(constraints, Mapping):
        raise ValueError("capability_descriptor_execution_constraints_invalid")
    if work_class not in {"text", "reasoning"}:
        return {
            "accepted": False,
            "stage": "CAPABILITY_ADAPTER",
            "routing_disposition": "NO_COMPATIBLE_EXECUTION_ADAPTER",
            "entitlement_state": entitlement_state,
            "capability_id": capability_id,
            "work_class": work_class,
            "provider": provider,
            "provider_execution_performed": False,
            "fallback_selected": False,
            "authority_effect": "NONE_REJECTION_ONLY",
        }
    if constraints.get("ephemeral_surface") is not True:
        return {
            "accepted": False,
            "stage": "CAPABILITY_EXECUTION_SURFACE",
            "routing_disposition": "EXISTING_NON_EPHEMERAL_ROUTE_OWNED_ELSEWHERE",
            "entitlement_state": entitlement_state,
            "capability_id": capability_id,
            "work_class": work_class,
            "provider": provider,
            "provider_execution_performed": False,
            "fallback_selected": False,
            "authority_effect": "NONE_REJECTION_ONLY",
        }
    return {
        "accepted": True,
        "capability_id": capability_id,
        "work_class": work_class,
        "provider": provider,
        "model": value.get("model"),
        "processing": dict(ECOSYSTEM_CHAT_TEXT_REASONING_PROCESSING),
        "execution_owner": "StegBrowser",
        "execution_owner_binding": "stegbrowser.llm_browser_execution.execute_manifested_llm_browser_operation",
        "external_llm_connection_role": "SEPARATE_PROVIDER_NEUTRAL_TEXT_REASONING_PRIMITIVE_NOT_SELECTED_BY_THIS_ROUTE",
        "retained_observation_required": True,
        "fallback_selected": False,
        "authority_effect": "NONE_SELECTION_ONLY",
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
    arguments = dict(arguments)
    selection = None
    if payload.get("capability_descriptor") is not None:
        try:
            selection = resolve_ecosystem_chat_capability_descriptor(payload["capability_descriptor"])
        except ValueError as exc:
            return {
                "schema": REJECTION_SCHEMA,
                "accepted": False,
                "stage": "CAPABILITY_DESCRIPTOR",
                "sdk_rejection": str(exc),
                "rejection_is_verbatim_from_the_sdk": False,
                "provider_execution_performed": False,
                "fallback_selected": False,
                "authority_effect": "NONE_REJECTION_ONLY",
            }
        if selection["accepted"] is False:
            return {
                "schema": REJECTION_SCHEMA,
                **selection,
                "sdk_rejection": selection["routing_disposition"],
                "rejection_is_verbatim_from_the_sdk": False,
                "retry_permitted": selection["routing_disposition"] in ECOSYSTEM_CHAT_ENTITLEMENT_NON_ALLOW,
            }
        mapped = selection["processing"]
        declared_process = str(arguments.get("process") or "").strip().lower()
        request = arguments.get("processor_request")
        if isinstance(request, Mapping):
            if str(request.get("provider") or "").strip() not in {"", selection["provider"]}:
                return {
                    "schema": REJECTION_SCHEMA,
                    "accepted": False,
                    "stage": "CAPABILITY_PROVIDER_MISMATCH",
                    "sdk_rejection": "processor request provider does not match selected capability provider",
                    "rejection_is_verbatim_from_the_sdk": False,
                    "provider_execution_performed": False,
                    "fallback_selected": False,
                    "authority_effect": "NONE_REJECTION_ONLY",
                }
            selected_model = selection.get("model")
            if selected_model is not None and str(request.get("model") or "").strip() not in {"", str(selected_model)}:
                return {
                    "schema": REJECTION_SCHEMA,
                    "accepted": False,
                    "stage": "CAPABILITY_MODEL_MISMATCH",
                    "sdk_rejection": "processor request model does not match selected capability model",
                    "rejection_is_verbatim_from_the_sdk": False,
                    "provider_execution_performed": False,
                    "fallback_selected": False,
                    "authority_effect": "NONE_REJECTION_ONLY",
                }
        # Descriptor metadata may supply a default, never override declared processing.
        if not declared_process:
            arguments["process"] = mapped["capability"]
    try:
        manifest = build_manifest(**arguments)
    except TypeError as exc:
        return rejected(str(exc), stage="BUILD")
    except ValueError as exc:
        return rejected(str(exc), stage="BUILD")
    response = {
        "schema": BOUNDARY_SCHEMA,
        "surface": "MANIFEST_BUILD",
        "accepted": True,
        "manifest": manifest,
        "nothing_was_submitted": True,
        "authority_effect": "NONE_CONSTRUCTION_ONLY",
    }
    if selection is not None:
        processing = manifest.get("processing") if isinstance(manifest, Mapping) else None
        if not str(payload.get("arguments", {}).get("process") or "").strip() and processing != selection["processing"]:
            return {
                "schema": REJECTION_SCHEMA,
                "accepted": False,
                "stage": "CAPABILITY_ROUTE_MISMATCH",
                "sdk_rejection": "built manifest did not preserve selected existing capability route",
                "rejection_is_verbatim_from_the_sdk": False,
                "provider_execution_performed": False,
                "fallback_selected": False,
                "authority_effect": "NONE_REJECTION_ONLY",
            }
        response["capability_selection"] = selection
    return response


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

    Whether the manifest was handed off, and with what disposition, is read
    off the envelope rather than asserted: a manifest refused before the
    runtime was not handed off, and a non-ALLOW carries the six standard
    fields naming its predicate, repair and retry entrypoint. Nothing here
    waits on an external receiver; the disposition is the transition.
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
    disposition = str(envelope.get("governance_state") or "FAIL_CLOSED")
    response = {
        "schema": BOUNDARY_SCHEMA,
        "surface": "MANIFEST_SUBMIT",
        "handed_off": envelope.get("reached_sdk_runtime") is True,
        "disposition": disposition,
        "result_is_a_handoff_not_a_runtime_result": True,
        "result_arrives_separately_through": "stegverse.manifest_state_transition_runtime.admit_runtime_result",
        "destination_resolution_source": "CANONICAL_CONNECTOR_CAPABILITY_OVERLAY",
        "envelope": envelope,
        "authority_effect": "NONE_HANDOFF_ONLY",
    }
    if disposition != "ALLOW":
        response.update({key: envelope.get(key) for key in NON_ALLOW_FIELDS})
    return response


__all__ = ["require_standing", "contract", "build", "validate", "submit",
           "installed_runtime", "process_manifest", "record", "crossing_record",
           "record_standing_refusal", "standing_refusal_record",
           "ALLOW", "DENY", "BOUNDARY", "BOUNDARY_SCHEMA", "RECORD_SCHEMA",
           "REFUSED_CLASS", "REJECTION_SCHEMA", "SURFACES",
           "resolve_ecosystem_chat_capability_descriptor"]
