"""
Executor for stegverse.intr.anthropic.transport.v1.

Orchestrates exactly one governed transaction:

  StegVerse ProviderRequest
    -> external Interlock/InTr ingress ALLOW (verified, never generated)
    -> exact request-hash-bound Anthropic transport envelope
    -> TV/TVC credential/route resolution (ephemeral, execution-scoped)
    -> deterministic Anthropic Messages API projection
    -> Claude inference (injected wire transport)
    -> normalized non-authoritative ProviderResponse
    -> provider-usage evidence
    -> Master Records custody/reconstruction
    -> external Interlock/InTr egress evaluation
    -> exact response-hash-bound ALLOW
    -> downstream consequence (caller's, gated on EGRESS_ADMITTED)

No automatic fallback to another Claude delivery platform or another provider
exists anywhere in this module, by construction.

Governance lineage: adapted from llm_adapter/zai_intr_executor.py
(StegVerse-org/LLM-adapter).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Optional, Tuple

from .anthropic_intr_transport import (
    AUTHORITY_EFFECT,
    CREDENTIAL_AUTHORITY,
    PROTOCOL_VERSION,
    PROVIDER,
    EgressDecision,
    EphemeralCredential,
    FailClosed,
    IngressDecision,
    ProviderRequest,
    TransportConfig,
    assert_no_credential_material,
    build_master_records_handoff,
    build_transport_envelope,
    build_transport_evidence,
    envelope_hash,
    map_request_to_anthropic,
    normalize_provider_response,
    project_usage,
    resolve_credential,
    verify_egress,
    verify_endpoint,
    verify_ingress,
    verify_master_records_receipt,
)

# (method, url, headers, body_bytes) -> (status_code, parsed_json)
HttpTransport = Callable[[str, str, Mapping[str, str], bytes], Tuple[int, Any]]

# Supplied by StegVerse; the adapter only verifies what comes back.
EgressResolver = Callable[[Mapping[str, Any]], EgressDecision]

# Master Records client: handoff -> receipt
MasterRecordsClient = Callable[[Mapping[str, Any]], Mapping[str, Any]]


class ProviderTransportError(FailClosed):
    code = "PROVIDER_TRANSPORT_ERROR"


@dataclass
class TransactionResult:
    state: str
    envelope: dict
    envelope_hash: str
    wire_request: dict
    provider_response: dict
    evidence: dict
    usage_event: dict
    master_records_handoff: dict
    master_records_receipt: dict
    egress_verification: dict
    authority_effect: str = AUTHORITY_EFFECT
    protocol_version: str = PROTOCOL_VERSION

    def durable_artifacts(self) -> dict:
        return {
            "transport_envelope": self.envelope,
            "provider_response": self.provider_response,
            "transport_evidence": self.evidence,
            "usage_event": self.usage_event,
            "master_records_handoff": self.master_records_handoff,
            "master_records_receipt": self.master_records_receipt,
            "egress_verification": self.egress_verification,
        }


def redacted_log_record(envelope: Mapping[str, Any], stage: str, extra: Optional[Mapping[str, Any]] = None) -> dict:
    """The only log shape this adapter emits. Structurally credential-free."""
    record = {
        "protocol_version": PROTOCOL_VERSION,
        "stage": stage,
        "transport_id": envelope.get("transport_id"),
        "transition_id": envelope.get("transition_id"),
        "provider": PROVIDER,
        "model": envelope.get("model"),
        "credential_authority": CREDENTIAL_AUTHORITY,
        "credential_material_present": False,
        "authority_effect": AUTHORITY_EFFECT,
    }
    if extra:
        record["detail"] = dict(extra)
    assert_no_credential_material(record, label="log_record")
    return record


def execute_governed_transaction(
    *,
    provider_request: ProviderRequest,
    ingress_decision: IngressDecision,
    config: TransportConfig,
    credential_resolver: Callable[[Mapping[str, Any]], str],
    transport: HttpTransport,
    master_records: MasterRecordsClient,
    egress_resolver: EgressResolver,
    logger: Optional[Callable[[Mapping[str, Any]], None]] = None,
) -> TransactionResult:
    log = logger or (lambda record: None)

    # 1-2. Ingress admission + endpoint/API-version admission (pre-network).
    verify_ingress(ingress_decision, provider_request)
    endpoint = verify_endpoint(config, provider_request)

    # 3. Deterministic envelope + transport identity.
    envelope = build_transport_envelope(provider_request, ingress_decision, config)
    env_hash = envelope_hash(envelope)
    log(redacted_log_record(envelope, "envelope_sealed", {"envelope_hash": env_hash}))

    # 4. Deterministic projection onto Anthropic Messages semantics.
    wire_request = map_request_to_anthropic(provider_request, config)
    body = json.dumps(wire_request, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")

    # 5. TV/TVC credential resolution — ephemeral, execution-scoped only.
    credential = resolve_credential(
        credential_resolver,
        {
            "credential_authority": CREDENTIAL_AUTHORITY,
            "carrier_ref": envelope["carrier_ref"],
            "transition_id": envelope["transition_id"],
            "transport_id": envelope["transport_id"],
            "provider": PROVIDER,
            "endpoint_profile": envelope["endpoint_profile"],
        },
    )
    try:
        headers = credential.headers(endpoint["anthropic_api_version"])
        log(redacted_log_record(envelope, "provider_call_start"))
        status, raw = transport(endpoint["method"], endpoint["url"], headers, body)
        if status != 200:
            # No fallback platform, no fallback model, no retry against a
            # substituted endpoint.
            raise ProviderTransportError(
                "Anthropic returned a non-success status; failing closed",
                {"status": status, "error_type": _error_type(raw)},
            )

        # 6. Deterministic normalization -> non-authoritative ProviderResponse.
        provider_response = normalize_provider_response(raw, envelope, endpoint, config)

        # 7. Response hashing / transport evidence.
        evidence = build_transport_evidence(envelope, env_hash, provider_response)

        # 8. Usage projection.
        usage_event = project_usage(
            provider_response, envelope, evidence, provider_request.session_id
        )

        # 9. Master Records custody/reconstruction. Custody != authorization.
        handoff = build_master_records_handoff(envelope, evidence, provider_response, usage_event)
        receipt = verify_master_records_receipt(master_records(handoff))

        # 10. Credential non-persistence check across every durable artifact,
        #     performed while the secret is still known.
        credential.assert_absent_from(
            {
                "transport_envelope": envelope,
                "anthropic_wire_request": wire_request,
                "provider_response": provider_response,
                "transport_evidence": evidence,
                "usage_event": usage_event,
                "master_records_handoff": handoff,
                "master_records_receipt": receipt,
            }
        )
    finally:
        credential.clear()

    # 11. Mandatory external egress evaluation, verified against the exact
    #     locally computed response_hash.
    egress_decision = egress_resolver(dict(evidence))
    egress_verification = verify_egress(evidence, egress_decision)
    log(redacted_log_record(envelope, "egress_admitted", {"response_hash": evidence["response_hash"]}))

    return TransactionResult(
        state=egress_verification["state"],
        envelope=envelope,
        envelope_hash=env_hash,
        wire_request=wire_request,
        provider_response=provider_response,
        evidence=evidence,
        usage_event=usage_event,
        master_records_handoff=handoff,
        master_records_receipt=receipt,
        egress_verification=egress_verification,
    )


def _error_type(raw: Any) -> Optional[str]:
    if isinstance(raw, Mapping):
        err = raw.get("error")
        if isinstance(err, Mapping):
            t = err.get("type")
            if isinstance(t, str):
                return t
    return None


# ---------------------------------------------------------------------------
# Reference wire transport (runtime use only; never exercised by tests)
# ---------------------------------------------------------------------------


def urllib_transport(timeout: float = 120.0) -> HttpTransport:
    """Minimal stdlib transport against the native Anthropic endpoint.

    Kept deliberately thin: it performs no retries, no endpoint rewriting and
    no provider fallback. Tests inject a stub instead of calling the network.
    """
    import urllib.error
    import urllib.request

    def _call(method: str, url: str, headers: Mapping[str, str], body: bytes):
        req = urllib.request.Request(url, data=body, method=method)
        for k, v in headers.items():
            req.add_header(k, v)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.status, json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:  # pragma: no cover - runtime path
            try:
                payload = json.loads(exc.read().decode("utf-8"))
            except Exception:
                payload = None
            return exc.code, payload

    return _call
