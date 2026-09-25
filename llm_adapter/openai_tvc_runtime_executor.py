"""Task-bound OpenAI Responses through the EXISTING TVC non-exportable broker.

The provider-specific edge never opens a credential, a browser, a worker, or an
InTr connection. Its caller supplies externally verified current admission,
a task-bound TVC lease and existing org receipt/usage custody callbacks.
No fallback to environment-key HTTP clients or a measurement-purpose lease.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Mapping

from .provider_client import ProviderResponse
from .provider_request import ProviderRequest, stable_hash
from .provider_usage import ProviderMetric, build_provider_usage_event
from .master_records_usage_submission import submit_provider_usage_to_master_records

PROTOCOL = "stegverse.intr.openai.responses.v1"
TASK_ID = "EPHEMERAL-STEGBROWSER-EXTERNAL-AI-ACTIVATION-001"
RUNTIME_PROFILE_ID = "stegverse:runtime-profile:llm-adapter-openai:v1"
TVC_REQUEST_SCHEMA = "stegverse.vault.non_exportable_operation_request.v1"
TVC_LEASE_SCHEMA = "stegverse.tvc.ephemeral-openai-capability-lease/v1"
TVC_SECRET_REF = "vault://tvc/providers/openai/api-key"
TVC_CAPABILITY = "llm.ephemeral.openai"
TVC_OPERATION = "chat_completion_with_usage"
SHA256 = re.compile(r"^[0-9a-f]{64}$")


class OpenAIEphemeralExecutionError(RuntimeError):
    pass


def _hash(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(json.dumps(dict(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def _prompt(request: ProviderRequest) -> str:
    if not request.messages:
        raise OpenAIEphemeralExecutionError("OpenAI prompt messages required")
    if any(m.role not in ("user", "assistant", "system", "developer") or not m.content for m in request.messages):
        raise OpenAIEphemeralExecutionError("OpenAI prompt role/content invalid")
    return "\n".join(f"{m.role}: {m.content}" for m in request.messages)


def openai_wire_request_hash(request: ProviderRequest, *, max_output_tokens: int = 2048) -> str:
    """Hash EXACT prompt/model/token profile sent to the existing TVC operation.

    This canonical payload must match the pure equivalent in TVC. The bound
    request is the broker-facing operation, not an invented HTTP transcript.
    """
    if request.provider.lower().strip() not in ("openai", "chatgpt", "openai_http"):
        raise OpenAIEphemeralExecutionError("OpenAI request required")
    if request.temperature != 0.0:
        raise OpenAIEphemeralExecutionError("non-default sampling not in this pinned profile")
    if type(max_output_tokens) is not int or not 1 <= max_output_tokens <= 16384:
        raise OpenAIEphemeralExecutionError("invalid output limit")
    wire = {
        "protocol": PROTOCOL, "provider": "openai",
        "endpoint_profile": "openai_responses",
        "payload": {
            "model": request.model, "input": _prompt(request),
            "max_output_tokens": max_output_tokens,
        },
    }
    return _hash(wire)


def _datetime(value: Any) -> datetime:
    if not isinstance(value, str):
        raise OpenAIEphemeralExecutionError("TVC lease timestamp missing")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise OpenAIEphemeralExecutionError("TVC lease timestamp malformed") from exc
    if parsed.tzinfo is None:
        raise OpenAIEphemeralExecutionError("TVC lease timestamp missing offset")
    return parsed.astimezone(timezone.utc)


def verify_tvc_lease(
    lease: Mapping[str, Any],
    request: ProviderRequest,
    *,
    session_id: str,
    transition_id: str,
    ingress_receipt_hash: str,
    carrier_ref: str,
    current_admission_verifier: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None,
) -> None:
    wire_hash = openai_wire_request_hash(request)
    expected = {
        "schema": TVC_LEASE_SCHEMA, "decision": "ALLOW_CAPABILITY_LEASE",
        "provider": "openai", "capability": TVC_CAPABILITY,
        "operation": TVC_OPERATION, "task_id": TASK_ID, "model": request.model,
        "request_hash": wire_hash, "transition_id": transition_id,
        "ingress_receipt_hash": ingress_receipt_hash, "carrier_ref": carrier_ref,
        "browser_lease_id": session_id,
    }
    for field, value in expected.items():
        if lease.get(field) != value:
            raise OpenAIEphemeralExecutionError("task-bound TVC lease mismatch:" + field)
    for field in ("invocation_id", "worker_claim_ref", "fence_ref",
                  "browser_lease_commitment", "authenticated_admission_receipt_ref",
                  "request_nonce", "lease_id"):
        if not isinstance(lease.get(field), str) or not lease[field]:
            raise OpenAIEphemeralExecutionError("TVC lease binding missing:" + field)
    if not SHA256.fullmatch(wire_hash) or not SHA256.fullmatch(ingress_receipt_hash):
        raise OpenAIEphemeralExecutionError("invalid ingress digest")
    for field, value in (
        ("credential_authority", "TV/TVC"),
        ("credential_material_present", False), ("single_use", True),
        ("secret_values_exported", False), ("protected_values_exposed", False),
        ("authority_granted", False), ("second_machine_required", False),
    ):
        if lease.get(field) != value:
            raise OpenAIEphemeralExecutionError("TVC lease safety mismatch:" + field)
    body = dict(lease)
    receipt_sha = body.pop("receipt_sha256", None)
    if receipt_sha != "sha256:" + _hash(body):
        raise OpenAIEphemeralExecutionError("TVC lease receipt hash mismatch")
    current = datetime.now(timezone.utc)
    if _datetime(lease.get("issued_at_utc")) > current or _datetime(lease.get("expiry_utc")) <= current:
        raise OpenAIEphemeralExecutionError("TVC capability lease outside current time")
    # A freely recomputable digest cannot authenticate a WorkerCoordinator fence.
    # The EXISTING resident custody owner supplies a read-only, current-invocation
    # verifier. Its issuer receipt lookup and exact fence check are out of this
    # provider adapter's authority; no source-only fallback is permitted.
    if not callable(current_admission_verifier):
        raise OpenAIEphemeralExecutionError("authentic current claim/fence/lease verifier required")
    verified = current_admission_verifier(dict(lease))
    if not isinstance(verified, Mapping) or verified.get("verified") is not True:
        raise OpenAIEphemeralExecutionError("current admission not authentically verified")
    if verified.get("authority") != "TV/TVC+WorkerCoordinator+Interlock/InTr+StegBrowser":
        raise OpenAIEphemeralExecutionError("current admission verifier authority mismatch")
    for field in (
        "task_id", "invocation_id", "worker_claim_ref", "fence_ref",
        "browser_lease_id", "browser_lease_commitment", "transition_id",
        "ingress_receipt_hash", "request_hash", "carrier_ref",
        "authenticated_admission_receipt_ref", "lease_id", "receipt_sha256",
    ):
        if not isinstance(verified.get(field), str) or verified[field] != lease.get(field):
            raise OpenAIEphemeralExecutionError("current admission exact binding mismatch:" + field)
    if verified.get("current_fence_active") is not True or verified.get("browser_lease_active") is not True:
        raise OpenAIEphemeralExecutionError("claim/fence or browser lease no longer active")


def _operation(
    request: ProviderRequest,
    lease: Mapping[str, Any],
    *,
    max_output_tokens: int,
) -> dict[str, Any]:
    exact_fields = ("transition_id", "ingress_receipt_hash", "request_hash",
                    "carrier_ref", "invocation_id", "worker_claim_ref",
                    "fence_ref", "browser_lease_id", "browser_lease_commitment")
    return {
        "schema": TVC_REQUEST_SCHEMA,
        "secret_ref": TVC_SECRET_REF,
        "lease_receipt": dict(lease),
        "operation": {
            "provider": "openai", "operation": TVC_OPERATION, "model": request.model,
            "prompt": _prompt(request), "max_output_tokens": max_output_tokens,
            "response_format": "text", "purpose": "EPHEMERAL_STEGBROWSER_EXTERNAL_AI",
            "return_secret_material": False, "wallet_contacted": False,
            "signed": False, "broadcast": False,
        },
        "intr_binding": {name: lease[name] for name in exact_fields},
        "single_use": True, "export_allowed": False,
        "return_secret_material": False,
        "runtime_profile_id": RUNTIME_PROFILE_ID,
        "authority_effect": "NONE",
    }


def _metric(value: Any, ref: str) -> ProviderMetric:
    if type(value) is int and value >= 0:
        return ProviderMetric(value=str(value), unit="tokens", evidence_class="MEASURED", source_ref=ref)
    return ProviderMetric(value=None, unit="tokens", evidence_class="UNAVAILABLE", source_ref=ref)


@dataclass(frozen=True)
class OpenAIEphemeralExecution:
    response: ProviderResponse
    response_hash: str
    envelope: Mapping[str, Any]
    egress_handoff: Mapping[str, Any]
    org_receipt: Mapping[str, Any]
    provider_usage_event: Mapping[str, Any]
    master_records_usage: Mapping[str, Any]
    runtime_profile_id: str = RUNTIME_PROFILE_ID
    authority_effect: str = "NONE"

    def evidence(self) -> dict[str, Any]:
        return {
            "provider": "openai",
            "transition_id": self.envelope["transition_id"],
            "request_hash": self.envelope["request_hash"],
            "response_hash": self.response_hash,
            "organization_receipt_sha256": self.org_receipt["receipt_sha256"],
            "provider_usage_event_sha256": self.provider_usage_event["event_sha256"],
            "runtime_profile_id": RUNTIME_PROFILE_ID, "authority_effect": "NONE",
        }


def execute_governed_openai_via_tvc_runtime(
    request: ProviderRequest, *, session_id: str, transition_id: str,
    measurement_id: str, ingress_disposition: str, ingress_receipt_hash: str,
    carrier_ref: str, lease_receipt: Mapping[str, Any],
    broker_submitter: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    org_transition_recorder: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    org_chain_verifier: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None = None,
    current_admission_verifier: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None = None,
    usage_submitter: Callable[[dict[str, Any]], dict[str, Any]] = submit_provider_usage_to_master_records,
    max_output_tokens: int = 2048, response_format: str = "text",
) -> OpenAIEphemeralExecution:
    if ingress_disposition != "ALLOW" or not all(
        isinstance(x, str) and x for x in (session_id, transition_id, measurement_id, carrier_ref)
    ):
        raise OpenAIEphemeralExecutionError("current external ingress/task identity required")
    if max_output_tokens != 2048 or response_format != "text":
        raise OpenAIEphemeralExecutionError("pinned exact wire profile required")
    if not all(callable(x) for x in (broker_submitter, org_transition_recorder, org_chain_verifier, usage_submitter)):
        raise OpenAIEphemeralExecutionError("existing broker/org/org-chain/usage callback required")
    verify_tvc_lease(
        lease_receipt, request, session_id=session_id,
        transition_id=transition_id,
        ingress_receipt_hash=ingress_receipt_hash, carrier_ref=carrier_ref,
        current_admission_verifier=current_admission_verifier,
    )
    wire_hash = openai_wire_request_hash(request)
    operation = _operation(request, lease_receipt, max_output_tokens=max_output_tokens)
    reply = broker_submitter(operation)
    if not isinstance(reply, Mapping) or reply.get("decision") != "ALLOW_OPERATION_RESULT":
        raise OpenAIEphemeralExecutionError("TVC did not return authorized provider result")
    normalized = reply.get("measurement_evidence")
    use_receipt = reply.get("use_receipt")
    if not isinstance(normalized, Mapping) or not isinstance(use_receipt, Mapping):
        raise OpenAIEphemeralExecutionError("TVC provider evidence/use receipt absent")
    # TVC must reject protected fields at its own broker boundary. Also fail
    # closed on any such material passed through a misconfigured callback;
    # a claimed zero-leak flag alone is not evidence of a sanitized result.
    forbidden_fields = {
        "authorization", "api_key", "apikey", "bearer_token",
        "credential", "credentials", "password", "secret", "secret_value",
        "provider_key", "provider_api_key", "private_key",
    }
    def reject_protected(value: Any) -> None:
        if isinstance(value, Mapping):
            for key, child in value.items():
                if str(key).lower().replace("-", "_") in forbidden_fields:
                    raise OpenAIEphemeralExecutionError("provider evidence contains protected material")
                reject_protected(child)
        elif isinstance(value, (list, tuple)):
            for child in value:
                reject_protected(child)
        elif isinstance(value, str) and value.lstrip().lower().startswith(("sk-", "bearer ", "ghp_", "github_pat_")):
            raise OpenAIEphemeralExecutionError("provider evidence contains protected material")
    reject_protected(normalized)
    reject_protected(use_receipt)
    if normalized.get("provider") != "openai" or normalized.get("model") != request.model:
        raise OpenAIEphemeralExecutionError("provider/model attribution mismatch")
    if normalized.get("provider_api_key_transferred_to_consumer") is not False or normalized.get("secret_material_returned") is not False:
        raise OpenAIEphemeralExecutionError("TVC provider response exposed credentials")
    for field in ("secret_material_returned", "secret_material_logged",
                  "secret_material_retained", "wallet_contacted", "signed",
                  "broadcast"):
        if use_receipt.get(field) is not False:
            raise OpenAIEphemeralExecutionError("TVC use receipt violation:" + field)
    if use_receipt.get("single_use_consumed") is not True:
        raise OpenAIEphemeralExecutionError("TVC single-use receipt missing")
    # This result must come from the real existing vault broker's independently
    # authenticated, durable consumption path. An injected TVC-only fixture or
    # local forwarding-client approval cannot substitute for its broker receipt.
    for field, expected in (
        ("task_id", TASK_ID),
        ("invocation_id", lease_receipt["invocation_id"]),
        ("request_hash", wire_hash),
        ("authenticated_admission_receipt_ref", lease_receipt["authenticated_admission_receipt_ref"]),
    ):
        if use_receipt.get(field) != expected:
            raise OpenAIEphemeralExecutionError("existing vault broker receipt mismatch:" + field)
    consumption_ref = use_receipt.get("durable_consumption_receipt_ref")
    if not isinstance(consumption_ref, str) or not consumption_ref:
        raise OpenAIEphemeralExecutionError("durable TVC capability consumption unverified")

    output = normalized.get("candidate_output")
    usage = normalized.get("normalized_usage")
    response_id = normalized.get("provider_response_id")
    if not isinstance(output, str) or not output.strip() or not isinstance(usage, Mapping) or not response_id:
        raise OpenAIEphemeralExecutionError("genuine provider output/usage missing")
    if not isinstance(response_id, str) or not response_id.strip():
        raise OpenAIEphemeralExecutionError("provider response id invalid")
    for field in ("input_tokens", "output_tokens", "total_tokens"):
        if type(usage.get(field)) is not int or usage[field] < 0:
            raise OpenAIEphemeralExecutionError("measured OpenAI usage invalid:" + field)
    if usage["input_tokens"] == 0 or usage["output_tokens"] == 0 or usage["total_tokens"] != usage["input_tokens"] + usage["output_tokens"]:
        raise OpenAIEphemeralExecutionError("provider usage incomplete or internally inconsistent")
    response = ProviderResponse(
        provider="openai", model=request.model, output=output,
        request_hash=wire_hash,
        metadata={
            "provider_mode": "openai_tvc_non_exportable_operation",
            "runtime_profile_id": RUNTIME_PROFILE_ID,
            "provider_response_id": response_id,
            "usage": dict(usage),
            "tvc_use_receipt_hash": stable_hash(dict(use_receipt)),
            "credential_authority": "TV/TVC",
            "credential_material_present": False,
            "egress_intr_required": True, "authority_effect": "NONE",
        },
    )
    envelope = {
        "protocol": PROTOCOL, "task_id": TASK_ID,
        "invocation_id": lease_receipt["invocation_id"],
        "worker_claim_ref": lease_receipt["worker_claim_ref"],
        "fence_ref": lease_receipt["fence_ref"],
        "browser_lease_id": session_id,
        "browser_lease_commitment": lease_receipt["browser_lease_commitment"],
        "transition_id": transition_id, "request_hash": wire_hash,
        "ingress_receipt_hash": ingress_receipt_hash,
        "carrier_ref": carrier_ref, "provider": "openai",
        "model": request.model, "response_hash": response.response_hash,
        "tvc_use_receipt_hash": response.metadata["tvc_use_receipt_hash"],
        "credential_material_present": False, "authority_effect": "NONE",
    }
    # The existing organization ledger must acknowledge the exact transition
    # before any optional global custody. No second recording store is created.
    source = {
        "schema": "stegverse.external-provider-result-transition/v1",
        "subject_or_correlation_id": TASK_ID,
        "transition_id": transition_id,
        "invocation_id": lease_receipt["invocation_id"],
        "worker_claim_ref": lease_receipt["worker_claim_ref"],
        "fence_ref": lease_receipt["fence_ref"],
        "browser_lease_id": session_id,
        "provider": "openai", "model": request.model,
        "request_hash": wire_hash, "response_hash": response.response_hash,
        "provider_response_id": response_id,
        "ingress_receipt_hash": ingress_receipt_hash,
        "tvc_use_receipt_hash": response.metadata["tvc_use_receipt_hash"],
        "authority_effect": "NONE",
    }
    org = org_transition_recorder(dict(source))
    expected_hash = "sha256:" + _hash(source)
    # Only the EXISTING canonical-state-transition receipt is accepted by the
    # organization ledger. The callback wraps this exact provider-event digest
    # into that canonical receipt, then appends it to the existing org ledger.
    # It must return the actual org receipt, not a self-asserted adapter event.
    if not isinstance(org, Mapping) or org.get("source_receipt_schema") != "stegverse.canonical-state-transition-receipt/v1":
        raise OpenAIEphemeralExecutionError("canonical org receipt missing")
    if org.get("subject_or_correlation_id") != TASK_ID or org.get("org_transition_class") != "ORGANIZATION_STATE_TRANSITION":
        raise OpenAIEphemeralExecutionError("organization transition identity mismatch")
    if not isinstance(org.get("boundary_evidence"), Mapping) or org["boundary_evidence"].get("provider_event_sha256") != expected_hash:
        raise OpenAIEphemeralExecutionError("canonical org provider-event binding mismatch")
    if org.get("canonical_state_transition_receipt_sha256") != org.get("source_transition_sha256"):
        raise OpenAIEphemeralExecutionError("canonical org source digest mismatch")
    previous = org.get("previous_receipt_sha256")
    if not isinstance(previous, str) or not previous.startswith("sha256:") or not SHA256.fullmatch(previous[7:]):
        raise OpenAIEphemeralExecutionError("exact organization predecessor digest missing")

    body = dict(org)
    org_hash = body.pop("receipt_sha256", None)
    if org.get("organization") != "StegVerse-org" or org_hash != "sha256:" + _hash(body):
        raise OpenAIEphemeralExecutionError("organization receipt integrity/owner mismatch")
    # Reuse the EXISTING organization ledger readback/replay interface. A local
    # adapter cannot authenticate a predecessor by hashing a supplied JSON blob.
    # The owner must read back this receipt AND its exact immediately preceding
    # retained receipt from independent existing org custody before usage/egress.
    chain = org_chain_verifier(dict(org))
    if (not isinstance(chain, Mapping) or chain.get("verified") is not True
        or chain.get("organization") != "StegVerse-org"
        or chain.get("receipt_sha256") != org_hash
        or chain.get("previous_receipt_sha256") != previous
        or chain.get("predecessor_verified") is not True
        or chain.get("source_event_sha256") != expected_hash):
        raise OpenAIEphemeralExecutionError("authenticated organization predecessor replay unavailable or mismatched")
    ref = f"openai:tvc:{lease_receipt['lease_id']}"
    metrics = {
        "prompt_tokens": _metric(usage.get("input_tokens"), ref),
        "completion_tokens": _metric(usage.get("output_tokens"), ref),
        "total_tokens": _metric(usage.get("total_tokens"), ref),
    }
    event = build_provider_usage_event(
        measurement_id=measurement_id, session_id=session_id,
        transition_id=transition_id, origin_entry_point="stegbrowser",
        interaction_type="governed_ephemeral_openai_inference",
        provider="openai", model=request.model,
        metrics=metrics,
        receipt_refs=[ingress_receipt_hash, org_hash, response.response_hash],
    )
    custody = usage_submitter(event)
    if not isinstance(custody, Mapping):
        raise OpenAIEphemeralExecutionError("usage custody reply malformed")
    if custody.get("custody_recorded") is not True or custody.get("status") != "CUSTODY_RECORDED":
        raise OpenAIEphemeralExecutionError("explicit usage custody incomplete")
    if custody.get("event_sha256") != event["event_sha256"] or custody.get("session_id") != session_id:
        raise OpenAIEphemeralExecutionError("usage custody exact event mismatch")
    if custody.get("authority_granted") is not False:
        raise OpenAIEphemeralExecutionError("usage custody authority escalation")
    handoff = {
        "schema": "stegverse.llm_adapter.openai_tvc_runtime_egress_handoff/v1",
        **envelope,
        "organization_receipt_sha256": org_hash,
        "provider_usage_event_sha256": event["event_sha256"],
        "master_records_usage_status": "CUSTODY_RECORDED",
        "requested_disposition": "ALLOW",
        "egress_intr_required": True,
    }
    return OpenAIEphemeralExecution(
        response=response, response_hash=response.response_hash,
        envelope=envelope, egress_handoff=handoff,
        org_receipt=dict(org), provider_usage_event=event,
        master_records_usage=dict(custody),
    )


def admit_openai_tvc_runtime_egress(
    execution: OpenAIEphemeralExecution, *, egress_disposition: str,
    egress_receipt_hash: str, admitted_response_hash: str,
) -> dict[str, Any]:
    if egress_disposition != "ALLOW" or not SHA256.fullmatch(egress_receipt_hash):
        raise OpenAIEphemeralExecutionError("exact egress InTr ALLOW required")
    if admitted_response_hash != execution.response_hash:
        raise OpenAIEphemeralExecutionError("egress response hash mismatch")
    return {
        "state": "EGRESS_ADMITTED", "provider": "openai",
        "transition_id": execution.envelope["transition_id"],
        "response_hash": execution.response_hash,
        "egress_receipt_hash": egress_receipt_hash,
        "organization_receipt_sha256": execution.org_receipt["receipt_sha256"],
        "transition_authority": "Interlock/InTr",
        "authority_effect": "NONE_LOCAL",
    }
