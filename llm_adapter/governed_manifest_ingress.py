"""Governed machine-manifest ingress/egress for external LLM frameworks.

The adapter validates transport framing and delegates governance to an injected
canonical handler. It does not implement or replace StegGate authority.

The manifest may request how transition evidence is projected back to the
external caller. That projection never suppresses the Master Records organization
record or alters the governed transition history.

Manifest validity is the SDK's to decide, not this adapter's. The adapter used
to keep its own copy of the ingress rules, and the copy was stricter than the
owner: it demanded a candidate on every manifest, where the SDK requires one
only when the declared processing is governance. So an SDK-built
non-governance manifest was refused here and never reached the SDK at all.
`validate_ingress_manifest` now delegates to
`stegverse.manifest_contract.validate_ingress_manifest` and adds only this
adapter's own bookkeeping.

Every non-ALLOW this module returns is a state transition carrying the six
standard fields (`failure_code`, `failed_predicate`,
`required_evidence_or_repair`, `retry_entrypoint`, `owning_existing_goal`,
`next_attempt`), so a refused caller is told what to repair and where to
retry rather than being left to wait on anything.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from typing import Any, Callable, Mapping

from stegverse.manifest_contract import validate_ingress_manifest as sdk_validate_ingress_manifest

INGRESS_SCHEMA = "stegverse.ingress-manifest.v1"
RESULT_SCHEMA = "stegverse.llm-adapter.governed-result.v1"
ALLOWED_STATES = {"ALLOW", "DENY", "REVIEW", "FAIL_CLOSED"}
ALLOWED_MODES = {"TEST", "LIVE_STREAM"}
RETURN_PROJECTION_MODES = {"ALL", "SELECTED", "NONE"}

#: The existing goal that owns every non-ALLOW this adapter path emits.
OWNING_EXISTING_GOAL = "LLMA-DECLARED-PATH-CONFORMANCE-368"
#: The six fields every non-ALLOW disposition carries.
NON_ALLOW_FIELDS = (
    "failure_code", "failed_predicate", "required_evidence_or_repair",
    "retry_entrypoint", "owning_existing_goal", "next_attempt",
)
SUBMIT_ENTRYPOINT = "POST /api/sdk/manifest/submit"
VALIDATE_ENTRYPOINT = "POST /api/sdk/manifest/validate"
STANDING_ENTRYPOINT = "POST /api/node-standing"


def non_allow_fields(*, failure_code: str, failed_predicate: str,
                     required_evidence_or_repair: str, retry_entrypoint: str,
                     next_attempt: str) -> dict[str, str]:
    """The six standard fields of a non-ALLOW disposition.

    A non-ALLOW is a state transition with a named predicate and repair, not a
    wait on any external machine, receiver or observer.
    """
    return {
        "failure_code": failure_code,
        "failed_predicate": failed_predicate,
        "required_evidence_or_repair": required_evidence_or_repair,
        "retry_entrypoint": retry_entrypoint,
        "owning_existing_goal": OWNING_EXISTING_GOAL,
        "next_attempt": next_attempt,
    }


def _hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def _normalize_return_projection(value: Mapping[str, Any] | None) -> dict[str, Any]:
    projection = dict(value or {})
    mode = str(projection.get("mode") or "ALL").strip().upper()
    if mode not in RETURN_PROJECTION_MODES:
        raise ValueError("manifest_return_projection_mode_invalid")
    selected = projection.get("transition_classes") or []
    if not isinstance(selected, list) or not all(isinstance(item, str) and item.strip() for item in selected):
        raise ValueError("manifest_return_projection_classes_invalid")
    selected = list(dict.fromkeys(item.strip() for item in selected))
    if mode == "SELECTED" and not selected:
        raise ValueError("manifest_return_projection_selected_requires_classes")
    if mode != "SELECTED" and selected:
        raise ValueError("manifest_return_projection_classes_only_for_selected")
    return {
        "mode": mode,
        "transition_classes": selected,
        "controls_user_return_only": True,
        "suppresses_master_records_organization_record": False,
        "erases_ecosystem_transitions": False,
        "grants_authority": False,
    }


STANDING_MODES = ("ESTABLISH_GENESIS", "VERIFY_EXISTING")

# What this adapter adds for its own bookkeeping. The SDK runtime refuses
# unknown top-level manifest fields, so these are named explicitly and stripped
# before handoff rather than guessed at.
ADAPTER_ADDED_FIELDS = (
    "node_standing_mode",
    "external_manifest_valid",
    "external_manifest_grants_authority",
    "master_records_transition_custody_independent_of_return_projection",
    "adapter_ingress_hash",
    "sdk_declared_processing",
)


def wire_manifest(canonical: Mapping[str, Any]) -> dict[str, Any]:
    """The manifest as the SDK built it, without this adapter's bookkeeping."""
    return {key: value for key, value in canonical.items() if key not in ADAPTER_ADDED_FIELDS}


def validate_standing(standing: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the standing a crossing declares, which is not a manifest field.

    Standing used to be required on the manifest, and that was wrong twice
    over. The SDK's runtime refuses `node_endpoint`, `predecessor`,
    `generation` and `node_standing_mode` as unknown top-level fields, so a
    manifest carrying them could not be handed off at all. And recognition is a
    property of the crossing rather than of the document: a manifest is
    portable and transport-independent, so a claim about whether the transport
    recognized its bearer does not belong inside it.

    The rules themselves are unchanged. `predecessor` must be present, null
    means explicit generation-1 genesis, a later generation requires the
    owner's four-field binding, and an unrecognized endpoint fails closed. Only
    where they are checked has moved.
    """
    if not isinstance(standing, Mapping):
        raise ValueError("crossing_standing_required")
    node_endpoint = standing.get("node_endpoint")
    if not isinstance(node_endpoint, Mapping) or not str(node_endpoint.get("node_id") or "").strip():
        raise ValueError("recognized_node_endpoint_required")
    if node_endpoint.get("recognized") is not True:
        raise ValueError("recognized_node_endpoint_required")
    if "predecessor" not in standing:
        raise ValueError("standing_missing_required_fields:predecessor")
    predecessor = standing["predecessor"]
    generation = standing.get("generation")
    if predecessor is None:
        if generation != 1:
            raise ValueError("genesis_requires_generation_one")
        standing_mode = "ESTABLISH_GENESIS"
    else:
        if not isinstance(generation, int) or isinstance(generation, bool) or generation < 2:
            raise ValueError("existing_node_requires_generation_beyond_one")
        if not isinstance(predecessor, Mapping):
            raise ValueError("existing_node_predecessor_invalid")
        required_predecessor = ("generation", "manifest_sha256", "result_sha256", "heartbeat_epoch")
        if set(predecessor) != set(required_predecessor):
            raise ValueError("existing_node_predecessor_fields_invalid")
        if predecessor.get("generation") != generation - 1:
            raise ValueError("existing_node_predecessor_generation_mismatch")
        for key in ("manifest_sha256", "result_sha256"):
            value = predecessor.get(key)
            if not isinstance(value, str) or len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
                raise ValueError(f"existing_node_predecessor_{key}_invalid")
        epoch = predecessor.get("heartbeat_epoch")
        if not isinstance(epoch, int) or isinstance(epoch, bool) or epoch < 1:
            raise ValueError("existing_node_predecessor_heartbeat_epoch_invalid")
        standing_mode = "VERIFY_EXISTING"
    return {"mode": standing_mode, "node_endpoint": dict(node_endpoint),
            "generation": generation, "predecessor": predecessor}


def validate_ingress_manifest(manifest: Mapping[str, Any]) -> dict[str, Any]:
    """Validate through the SDK, then add only this adapter's bookkeeping.

    The SDK's refusal message is raised verbatim. The wire manifest stays the
    manifest as the SDK built it; the processing the SDK resolved travels in
    `sdk_declared_processing`, which is stripped before handoff.
    """
    if not isinstance(manifest, Mapping):
        raise ValueError("manifest must be an object")
    sdk_canonical = sdk_validate_ingress_manifest(manifest)
    processing = sdk_canonical["processing"]
    normalized = dict(manifest)
    normalized["return_projection"] = _normalize_return_projection(manifest.get("return_projection"))
    normalized["sdk_declared_processing"] = {
        "capability": processing["capability"],
        "route_id": processing["route_id"],
    }
    normalized["external_manifest_valid"] = True
    normalized["external_manifest_grants_authority"] = False
    normalized["master_records_transition_custody_independent_of_return_projection"] = True
    normalized["adapter_ingress_hash"] = _hash(normalized)
    return normalized


#: What each refusal stage names, and where its caller retries.
_FAIL_CLOSED_STAGES: Mapping[str, Mapping[str, str]] = {
    "MODE": {
        "failure_code": "INGRESS_MODE_UNSUPPORTED",
        "required_evidence_or_repair": "declare mode TEST or LIVE_STREAM",
        "retry_entrypoint": SUBMIT_ENTRYPOINT,
        "next_attempt": "resubmit with a supported mode",
    },
    "STANDING": {
        "failure_code": "NODE_STANDING_NOT_ESTABLISHED",
        "required_evidence_or_repair": "declare recognized node standing: explicit genesis (generation 1, predecessor null) or the owner's predecessor binding",
        "retry_entrypoint": STANDING_ENTRYPOINT,
        "next_attempt": "establish standing, then resubmit the same manifest",
    },
    "MANIFEST": {
        "failure_code": "MANIFEST_REFUSED_BY_SDK_CONTRACT",
        "required_evidence_or_repair": "rebuild the manifest with the SDK builder and correct the field the SDK named",
        "retry_entrypoint": VALIDATE_ENTRYPOINT,
        "next_attempt": "validate (side-effect free) until accepted, then resubmit",
    },
    "HANDOFF": {
        "failure_code": "SDK_RUNTIME_HANDOFF_RAISED",
        "required_evidence_or_repair": "repair the installed SDK runtime binding named in the failed predicate",
        "retry_entrypoint": SUBMIT_ENTRYPOINT,
        "next_attempt": "resubmit the same manifest once the binding is repaired",
    },
    "RESULT": {
        "failure_code": "SDK_RUNTIME_RESULT_NOT_ADMISSIBLE",
        "required_evidence_or_repair": "a result whose state is ALLOW, DENY, REVIEW or FAIL_CLOSED, claiming no consequence unless ALLOW, and an organization transition receipt for ALLOW",
        "retry_entrypoint": SUBMIT_ENTRYPOINT,
        "next_attempt": "resubmit the same manifest; the runtime decides the transition again",
    },
    "STREAM": {
        "failure_code": "LIVE_STREAM_ORDERING_REFUSED",
        "required_evidence_or_repair": "the next expected sequence number and a fresh idempotency key for new input",
        "retry_entrypoint": SUBMIT_ENTRYPOINT,
        "next_attempt": "resubmit the unit at the expected sequence",
    },
}


def _fail_closed(*, mode: str, reason: str, stage: str, manifest: Mapping[str, Any] | None = None, stream_id: str | None = None, sequence: int | None = None) -> dict[str, Any]:
    declared = _FAIL_CLOSED_STAGES[stage]
    body: dict[str, Any] = {
        "schema": RESULT_SCHEMA,
        "mode": mode,
        "governance_state": "FAIL_CLOSED",
        "governed_result": None,
        "manifest_receipt_id": None,
        "consequence_executed": False,
        "reason": reason,
        "stream_id": stream_id,
        "sequence": sequence,
        "adapter_is_governance_authority": False,
        # Only a result the runtime returned and the adapter then refused was
        # handed off; every earlier stage stopped before the runtime.
        "reached_sdk_runtime": stage == "RESULT",
        **non_allow_fields(failed_predicate=reason, **declared),
    }
    if isinstance(manifest, Mapping):
        body["source_output_id"] = manifest.get("source_output_id")
    body["result_hash"] = _hash(body)
    return body


def _project_transition_evidence(governed: Mapping[str, Any], projection: Mapping[str, Any]) -> tuple[list[Any], list[str], list[str]]:
    mode = projection["mode"]
    evidence = list(governed.get("transition_evidence") or [])
    verification_refs = list(governed.get("verification_refs") or [])
    receipt_refs = list(governed.get("receipt_refs") or [])
    if mode == "NONE":
        return [], [], []
    if mode == "ALL":
        return evidence, verification_refs, receipt_refs
    selected = set(projection["transition_classes"])
    filtered: list[Any] = []
    for item in evidence:
        if isinstance(item, Mapping) and str(item.get("transition_class") or "") in selected:
            filtered.append(dict(item))
    return filtered, verification_refs, receipt_refs


def build_sdk_manifest_intr_transfer(canonical_manifest: Mapping[str, Any],
                                     standing: Mapping[str, Any]) -> dict[str, Any]:
    """Build the existing-boundary transfer into the distributed SDK manifest endpoint.

    This envelope is transport/framing only. The manifest's processing declaration,
    not source/provider identity and not this adapter, selects processing downstream.
    """
    processing = canonical_manifest["sdk_declared_processing"]
    node = standing["node_endpoint"]
    body = {
        "schema": "stegverse.sdk-manifest.intr-transfer/v1",
        "protocol": "InTr",
        "interlock_required": True,
        "source_node_id": node["node_id"],
        "source_node_recognized": True,
        "destination": "DISTRIBUTED_SDK_MANIFEST_ENDPOINT",
        # The manifest as the SDK built it. This adapter's bookkeeping is
        # stripped, because the receiving runtime refuses unknown top-level
        # manifest fields and that bookkeeping is not part of the wire manifest.
        "manifest": wire_manifest(canonical_manifest),
        "manifest_sha256": _hash(wire_manifest(canonical_manifest)),
        "adapter_ingress_hash": canonical_manifest.get("adapter_ingress_hash"),
        # Standing travels beside the manifest, which is where it already had a
        # home, rather than inside it.
        "canonical_node_standing": {
            "mode": standing["mode"],
            "generation": standing["generation"],
            "predecessor": standing["predecessor"],
        },
        "requested_processing": {
            "capability": processing["capability"],
            "route_id": processing["route_id"],
        },
        "adapter_selects_processing": False,
        "source_identity_selects_processing": False,
        "transport_grants_execution_authority": False,
        "authority_effect": "NONE",
    }
    body["transfer_sha256"] = _hash(body)
    return body


def process_manifest(
    manifest: Mapping[str, Any],
    *,
    mode: str,
    standing: Mapping[str, Any],
    sdk_manifest_endpoint: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    stream_id: str | None = None,
    sequence: int | None = None,
) -> dict[str, Any]:
    """Validate one machine manifest, delegate canonical governance, return a model-facing envelope."""
    mode = mode.upper()
    if mode not in ALLOWED_MODES:
        return _fail_closed(mode=mode, reason="unsupported_ingress_mode", stage="MODE", manifest=manifest, stream_id=stream_id, sequence=sequence)
    # Standing first: a crossing that has not established it must not reach the
    # question of whether its manifest is well-formed.
    try:
        resolved_standing = validate_standing(standing)
    except ValueError as exc:
        return _fail_closed(mode=mode, reason=str(exc), stage="STANDING", manifest=manifest, stream_id=stream_id, sequence=sequence)
    try:
        canonical_manifest = validate_ingress_manifest(manifest)
    except (ValueError, TypeError) as exc:
        return _fail_closed(mode=mode, reason=str(exc), stage="MANIFEST", manifest=manifest, stream_id=stream_id, sequence=sequence)
    try:
        governed = sdk_manifest_endpoint(
            build_sdk_manifest_intr_transfer(canonical_manifest, resolved_standing))
    except Exception as exc:
        return _fail_closed(mode=mode, reason=f"sdk_manifest_endpoint_failed:{type(exc).__name__}", stage="HANDOFF", manifest=canonical_manifest, stream_id=stream_id, sequence=sequence)
    state = str(governed.get("governance_state") or governed.get("disposition") or "")
    if state not in ALLOWED_STATES:
        return _fail_closed(mode=mode, reason="governance_result_state_invalid", stage="RESULT", manifest=canonical_manifest, stream_id=stream_id, sequence=sequence)

    # The receipt a transition emits is the organization's, not Master Records'.
    #
    # This required an `MR-` id, a Master Records organization-record id from the
    # end of the chain used as proof of its beginning. The organization ledger contract is
    # explicit about the order: it emits
    # `stegverse.organization-transition-receipt/v1`, its ledger root is the
    # runtime-reality locus, and `propagation_gates_organization_runtime_reality`
    # is false. Master Records is a propagation target that keeps the
    # organization record; the transition itself is admitted by Interlock/InTr. This adapter also declares
    # `master_records_authority: false`, so demanding an MR id was asserting an
    # authority it does not hold.
    #
    # The far side reports `organization_receipt_observed` for exactly this,
    # and that is what is carried.
    receipt_id = governed.get("manifest_receipt_id")
    organization_receipt_observed = bool(governed.get("organization_receipt_observed", False))
    consequence_executed = bool(governed.get("consequence_executed", False))
    if state != "ALLOW" and consequence_executed:
        return _fail_closed(mode=mode, reason="non_allow_result_claimed_consequence", stage="RESULT", manifest=canonical_manifest, stream_id=stream_id, sequence=sequence)
    if state == "ALLOW" and not organization_receipt_observed:
        # An admitted transition with no organization receipt would be a
        # consequence with nothing recording it.
        return _fail_closed(mode=mode, reason="organization_transition_receipt_not_observed", stage="RESULT", manifest=canonical_manifest, stream_id=stream_id, sequence=sequence)

    projection = canonical_manifest["return_projection"]
    transition_evidence, verification_refs, receipt_refs = _project_transition_evidence(governed, projection)
    body = {
        "schema": RESULT_SCHEMA,
        "mode": mode,
        "source_framework": canonical_manifest.get("source_framework"),
        "source_output_id": canonical_manifest.get("source_output_id"),
        "adapter_ingress_hash": canonical_manifest["adapter_ingress_hash"],
        "governance_state": state,
        "governed_result": governed.get("governed_result", governed.get("result")),
        "manifest_receipt_id": receipt_id,
        "organization_receipt_observed": organization_receipt_observed,
        # The far side's disposition, preserved. A FAIL_CLOSED handoff is a
        # valid outcome carrying its own named predicate and repair, and
        # replacing it with a generic adapter reason destroys the only
        # information a caller could act on.
        "far_side_disposition": {
            key: governed.get(key)
            for key in ("disposition", "state", "failed_predicate", "failure_code",
                        "required_evidence_or_repair", "next_attempt", "retry_entrypoint",
                        "destination_resolution_source", "canonical_task_id",
                        "canonical_manifest_sha256", "wire_manifest_sha256", "request_sha256",
                        "evaluation_boundary", "diagnostic_sha256",
                        "canonical_organization_boundary_unavailable")
            if governed.get(key) is not None
        },
        "return_projection": projection,
        "transition_evidence": transition_evidence,
        "verification_refs": verification_refs,
        "receipt_refs": receipt_refs,
        "consequence_executed": consequence_executed,
        "master_records_transition_custody_independent_of_return_projection": True,
        "stream_id": stream_id,
        "sequence": sequence,
        "adapter_is_governance_authority": False,
        "provider_output_grants_consequence_authority": False,
        "reached_sdk_runtime": True,
    }
    if state != "ALLOW":
        # A DENY, REVIEW or FAIL_CLOSED from the runtime is a transition with
        # its own predicate and repair. The far side's values are carried when
        # it named them; otherwise the adapter names the runtime's state.
        body.update(non_allow_fields(
            failure_code=str(governed.get("failure_code") or "SDK_RUNTIME_" + state),
            failed_predicate=str(governed.get("failed_predicate") or "sdk_runtime_disposition_is_allow"),
            required_evidence_or_repair=str(governed.get("required_evidence_or_repair")
                                            or "the repair the runtime's disposition names"),
            retry_entrypoint=str(governed.get("retry_entrypoint") or SUBMIT_ENTRYPOINT),
            next_attempt=str(governed.get("next_attempt")
                             or "resubmit once the named predicate holds"),
        ))
    body["result_hash"] = _hash(body)
    return body


@dataclass
class GovernedStreamSession:
    """Ordered per-unit governance wrapper for a live stream.

    Every unit keeps its own manifest and receipt identity. The stream provides
    continuity only; it never substitutes for per-unit governance.
    """

    stream_id: str
    sdk_manifest_endpoint: Callable[[Mapping[str, Any]], Mapping[str, Any]]
    standing: Mapping[str, Any] = field(default_factory=dict)
    _next_sequence: int = 0
    _seen: dict[str, dict[str, Any]] = field(default_factory=dict)

    def process(self, manifest: Mapping[str, Any], *, sequence: int, idempotency_key: str) -> dict[str, Any]:
        if not idempotency_key:
            return _fail_closed(mode="LIVE_STREAM", reason="idempotency_key_required", stage="STREAM", manifest=manifest, stream_id=self.stream_id, sequence=sequence)
        if idempotency_key in self._seen:
            previous = self._seen[idempotency_key]
            if previous.get("source_output_id") != manifest.get("source_output_id"):
                return _fail_closed(mode="LIVE_STREAM", reason="idempotency_key_reused_for_different_input", stage="STREAM", manifest=manifest, stream_id=self.stream_id, sequence=sequence)
            return dict(previous)
        if sequence != self._next_sequence:
            return _fail_closed(mode="LIVE_STREAM", reason=f"stream_sequence_expected:{self._next_sequence}", stage="STREAM", manifest=manifest, stream_id=self.stream_id, sequence=sequence)
        result = process_manifest(
            manifest,
            mode="LIVE_STREAM",
            standing=self.standing,
            sdk_manifest_endpoint=self.sdk_manifest_endpoint,
            stream_id=self.stream_id,
            sequence=sequence,
        )
        if result["governance_state"] != "FAIL_CLOSED" or result.get("manifest_receipt_id") is not None:
            self._seen[idempotency_key] = dict(result)
            self._next_sequence += 1
        return result
