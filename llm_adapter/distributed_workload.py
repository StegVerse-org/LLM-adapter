"""Distributed named-source LLM workload contract for Ecosystem Chat.

This module is deliberately transport-neutral and non-authorizing.  It composes the
existing ProviderRequest / ProviderResponse envelopes into a deterministic workload,
contribution, reconciliation, and governed-result evidence chain.

It does *not* execute network calls, choose truth by model vote, create a governance
engine, mint route/credential authority, or replace the canonical sovereign local
model path.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Optional, Sequence

from .provider_client import ProviderResponse
from .provider_request import (
    ProviderMessage,
    ProviderRequest,
    build_provider_request,
    stable_hash,
    utc_now_iso,
)


WORKLOAD_SCHEMA_VERSION = "stegverse.ecosystem_chat.distributed_llm_workload.v1"
CONTRIBUTION_SCHEMA_VERSION = "stegverse.ecosystem_chat.llm_contribution.v1"
RECONCILIATION_SCHEMA_VERSION = "stegverse.ecosystem_chat.llm_reconciliation_request.v1"
GOVERNED_RESULT_SCHEMA_VERSION = "stegverse.ecosystem_chat.governed_llm_result.v1"

ROUTING_MODES = frozenset({"single", "parallel", "sequential", "challenge", "fallback"})
CONTRIBUTION_STATUSES = frozenset({"RETURNED", "REFUSED", "FAILED"})
RESULT_DISPOSITIONS = frozenset({"ADMITTED", "DENIED", "DEFERRED"})

_SECRET_KEYS = frozenset(
    {
        "token",
        "api_key",
        "apikey",
        "password",
        "secret",
        "authorization",
        "bearer_token",
        "access_token",
        "refresh_token",
        "private_key",
    }
)


def _fail(reason: str) -> None:
    raise ValueError(f"FAIL_CLOSED: {reason}")


def _tuple_str(values: Sequence[str] | None) -> tuple[str, ...]:
    return tuple(str(value) for value in (values or ()))


def _require_sha256(value: str, label: str) -> None:
    if len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value.lower()):
        _fail(f"{label} must be a 64-character sha256 hex digest")


def _reject_embedded_secrets(value: Any, path: str = "metadata") -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            normalized = str(key).strip().lower()
            if normalized in _SECRET_KEYS or normalized.endswith(("_token", "_password", "_secret", "_api_key")):
                _fail(f"embedded provider credential field prohibited at {path}.{key}")
            _reject_embedded_secrets(nested, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, nested in enumerate(value):
            _reject_embedded_secrets(nested, f"{path}[{index}]")


@dataclass(frozen=True)
class SourceDescriptor:
    """A named LLM source that may contribute to a distributed workload."""

    source_id: str
    provider: str
    model: str
    capabilities: tuple[str, ...] = ()
    required: bool = False
    locality: str = "unspecified"
    sovereignty: str = "unspecified"
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "provider": self.provider,
            "model": self.model,
            "capabilities": list(self.capabilities),
            "required": self.required,
            "locality": self.locality,
            "sovereignty": self.sovereignty,
            "metadata": dict(self.metadata),
            "authority": {
                "model_output_authority": False,
                "route_authority": False,
                "credential_authority": False,
                "governance_authority": False,
                "custody_authority": False,
                "execution_authority": False,
            },
        }


@dataclass(frozen=True)
class DistributedLLMWorkload:
    """Deterministic description of a named-source LLM workload."""

    workload_id: str
    canonical_request_id: str
    canonical_request_hash: str
    routing_mode: str
    sources: tuple[SourceDescriptor, ...]
    purpose: str = "answer"
    required_capabilities: tuple[str, ...] = ()
    policy_refs: tuple[str, ...] = ()
    governance_refs: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now_iso)
    schema_version: str = WORKLOAD_SCHEMA_VERSION

    def payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "workload_id": self.workload_id,
            "canonical_request_id": self.canonical_request_id,
            "canonical_request_hash": self.canonical_request_hash,
            "routing_mode": self.routing_mode,
            "sources": [source.to_dict() for source in self.sources],
            "purpose": self.purpose,
            "required_capabilities": list(self.required_capabilities),
            "policy_refs": list(self.policy_refs),
            "governance_refs": list(self.governance_refs),
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
            "authority": {
                "grants_admission": False,
                "grants_execution": False,
                "grants_credentials": False,
                "grants_custody": False,
                "grants_governance": False,
            },
        }

    @property
    def workload_hash(self) -> str:
        return stable_hash(self.payload())

    def to_dict(self) -> dict[str, Any]:
        data = self.payload()
        data["workload_hash"] = self.workload_hash
        return data

    def source(self, source_id: str) -> SourceDescriptor:
        for descriptor in self.sources:
            if descriptor.source_id == source_id:
                return descriptor
        _fail(f"unknown source_id {source_id}")
        raise AssertionError("unreachable")


@dataclass(frozen=True)
class LLMContribution:
    """Normalized evidence envelope for one named-source contribution."""

    workload_id: str
    workload_hash: str
    source_id: str
    provider: str
    model: str
    status: str
    provider_request_hash: str
    provider_response_hash: Optional[str]
    output: Optional[str]
    provenance_refs: tuple[str, ...]
    evidence_refs: tuple[str, ...] = ()
    usage_refs: tuple[str, ...] = ()
    uncertainty_notes: tuple[str, ...] = ()
    disagreement_refs: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now_iso)
    schema_version: str = CONTRIBUTION_SCHEMA_VERSION

    def payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "workload_id": self.workload_id,
            "workload_hash": self.workload_hash,
            "source_id": self.source_id,
            "provider": self.provider,
            "model": self.model,
            "status": self.status,
            "provider_request_hash": self.provider_request_hash,
            "provider_response_hash": self.provider_response_hash,
            "output": self.output,
            "provenance_refs": list(self.provenance_refs),
            "evidence_refs": list(self.evidence_refs),
            "usage_refs": list(self.usage_refs),
            "uncertainty_notes": list(self.uncertainty_notes),
            "disagreement_refs": list(self.disagreement_refs),
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
            "authority": {
                "model_output_authority": False,
                "grants_admission": False,
                "grants_execution": False,
                "grants_credentials": False,
                "grants_custody": False,
                "grants_governance": False,
            },
        }

    @property
    def contribution_hash(self) -> str:
        return stable_hash(self.payload())

    def to_dict(self) -> dict[str, Any]:
        data = self.payload()
        data["contribution_hash"] = self.contribution_hash
        return data


@dataclass(frozen=True)
class ReconciliationRequest:
    """Evidence package handed to the existing governance path.

    The reconciliation request does not decide which model is correct.  It binds the
    workload and named-source contribution set so the existing governance system can
    evaluate them.
    """

    workload_id: str
    workload_hash: str
    source_ids: tuple[str, ...]
    contribution_hashes: tuple[str, ...]
    governance_refs: tuple[str, ...]
    policy_refs: tuple[str, ...] = ()
    created_at: str = field(default_factory=utc_now_iso)
    schema_version: str = RECONCILIATION_SCHEMA_VERSION

    def payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "workload_id": self.workload_id,
            "workload_hash": self.workload_hash,
            "source_ids": list(self.source_ids),
            "contribution_hashes": list(self.contribution_hashes),
            "governance_refs": list(self.governance_refs),
            "policy_refs": list(self.policy_refs),
            "created_at": self.created_at,
            "reconciliation_role": "EVIDENCE_FOR_EXISTING_GOVERNANCE",
            "authority": {
                "creates_governance_engine": False,
                "grants_admission": False,
                "grants_execution": False,
                "grants_credentials": False,
                "grants_custody": False,
            },
        }

    @property
    def reconciliation_hash(self) -> str:
        return stable_hash(self.payload())

    def to_dict(self) -> dict[str, Any]:
        data = self.payload()
        data["reconciliation_hash"] = self.reconciliation_hash
        return data


@dataclass(frozen=True)
class GovernedLLMResult:
    """Result envelope after an existing governance path supplies a disposition."""

    workload_id: str
    workload_hash: str
    reconciliation_hash: str
    disposition: str
    result_text: Optional[str]
    source_ids: tuple[str, ...]
    contribution_hashes: tuple[str, ...]
    governance_refs: tuple[str, ...]
    decision_refs: tuple[str, ...]
    provenance_refs: tuple[str, ...]
    evidence_refs: tuple[str, ...] = ()
    created_at: str = field(default_factory=utc_now_iso)
    schema_version: str = GOVERNED_RESULT_SCHEMA_VERSION

    def payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "workload_id": self.workload_id,
            "workload_hash": self.workload_hash,
            "reconciliation_hash": self.reconciliation_hash,
            "disposition": self.disposition,
            "result_text": self.result_text,
            "source_ids": list(self.source_ids),
            "contribution_hashes": list(self.contribution_hashes),
            "governance_refs": list(self.governance_refs),
            "decision_refs": list(self.decision_refs),
            "provenance_refs": list(self.provenance_refs),
            "evidence_refs": list(self.evidence_refs),
            "created_at": self.created_at,
            "authority": {
                "model_output_authority": False,
                "result_grants_transition_authority": False,
                "result_grants_route_authority": False,
                "result_grants_credential_authority": False,
                "result_grants_custody_authority": False,
                "result_grants_execution_authority": False,
            },
        }

    @property
    def result_hash(self) -> str:
        return stable_hash(self.payload())

    def to_dict(self) -> dict[str, Any]:
        data = self.payload()
        data["result_hash"] = self.result_hash
        return data


def build_source_descriptor(
    *,
    source_id: str,
    provider: str,
    model: str,
    capabilities: Sequence[str] = (),
    required: bool = False,
    locality: str = "unspecified",
    sovereignty: str = "unspecified",
    metadata: Optional[Mapping[str, Any]] = None,
) -> SourceDescriptor:
    descriptor = SourceDescriptor(
        source_id=str(source_id).strip(),
        provider=str(provider).strip(),
        model=str(model).strip(),
        capabilities=_tuple_str(capabilities),
        required=bool(required),
        locality=str(locality).strip() or "unspecified",
        sovereignty=str(sovereignty).strip() or "unspecified",
        metadata=metadata or {},
    )
    if not descriptor.source_id:
        _fail("source_id is required")
    if not descriptor.provider:
        _fail(f"provider is required for source {descriptor.source_id}")
    if not descriptor.model:
        _fail(f"model is required for source {descriptor.source_id}")
    _reject_embedded_secrets(descriptor.metadata, f"source[{descriptor.source_id}].metadata")
    return descriptor


def build_distributed_workload(
    *,
    workload_id: str,
    canonical_request_id: str,
    canonical_request_hash: str,
    routing_mode: str,
    sources: Sequence[SourceDescriptor],
    purpose: str = "answer",
    required_capabilities: Sequence[str] = (),
    policy_refs: Sequence[str] = (),
    governance_refs: Sequence[str] = (),
    metadata: Optional[Mapping[str, Any]] = None,
    created_at: Optional[str] = None,
) -> DistributedLLMWorkload:
    mode = str(routing_mode).strip().lower()
    if mode not in ROUTING_MODES:
        _fail(f"unsupported routing_mode {routing_mode}")
    descriptors = tuple(sources)
    if not descriptors:
        _fail("at least one named source is required")
    source_ids = [source.source_id for source in descriptors]
    if len(source_ids) != len(set(source_ids)):
        _fail("duplicate source_id")
    if mode == "single" and len(descriptors) != 1:
        _fail("single routing_mode requires exactly one source")
    if mode == "fallback" and len(descriptors) < 2:
        _fail("fallback routing_mode requires at least two ordered sources")
    _require_sha256(canonical_request_hash, "canonical_request_hash")
    if not str(workload_id).strip():
        _fail("workload_id is required")
    if not str(canonical_request_id).strip():
        _fail("canonical_request_id is required")
    workload_metadata = metadata or {}
    _reject_embedded_secrets(workload_metadata)
    workload = DistributedLLMWorkload(
        workload_id=str(workload_id),
        canonical_request_id=str(canonical_request_id),
        canonical_request_hash=canonical_request_hash.lower(),
        routing_mode=mode,
        sources=descriptors,
        purpose=str(purpose),
        required_capabilities=_tuple_str(required_capabilities),
        policy_refs=_tuple_str(policy_refs),
        governance_refs=_tuple_str(governance_refs),
        metadata=workload_metadata,
        created_at=created_at or utc_now_iso(),
    )
    validate_workload(workload)
    return workload


def validate_workload(workload: DistributedLLMWorkload) -> bool:
    if workload.schema_version != WORKLOAD_SCHEMA_VERSION:
        _fail("unsupported workload schema")
    _require_sha256(workload.canonical_request_hash, "canonical_request_hash")
    if workload.routing_mode not in ROUTING_MODES:
        _fail("unsupported workload routing_mode")
    if not workload.sources:
        _fail("workload has no sources")
    source_ids = [source.source_id for source in workload.sources]
    if len(source_ids) != len(set(source_ids)):
        _fail("duplicate source_id")
    for source in workload.sources:
        build_source_descriptor(
            source_id=source.source_id,
            provider=source.provider,
            model=source.model,
            capabilities=source.capabilities,
            required=source.required,
            locality=source.locality,
            sovereignty=source.sovereignty,
            metadata=source.metadata,
        )
    _reject_embedded_secrets(workload.metadata)
    authority = workload.to_dict()["authority"]
    if any(authority.values()):
        _fail("distributed workload cannot grant authority")
    return True


def build_source_provider_request(
    workload: DistributedLLMWorkload,
    source_id: str,
    messages: Sequence[Mapping[str, str] | ProviderMessage],
    *,
    allowed_sources: Sequence[str] = ("model_knowledge",),
    temperature: float = 0.0,
    metadata: Optional[Mapping[str, Any]] = None,
) -> ProviderRequest:
    """Build one normalized provider request bound to the distributed workload."""

    validate_workload(workload)
    descriptor = workload.source(source_id)
    caller_metadata = dict(metadata or {})
    _reject_embedded_secrets(caller_metadata, "provider_request.metadata")
    bound_metadata = {
        **caller_metadata,
        "distributed_workload_id": workload.workload_id,
        "distributed_workload_hash": workload.workload_hash,
        "distributed_source_id": descriptor.source_id,
        "canonical_request_id": workload.canonical_request_id,
        "canonical_request_hash": workload.canonical_request_hash,
    }
    return build_provider_request(
        provider=descriptor.provider,
        model=descriptor.model,
        messages=messages,
        purpose=workload.purpose,
        allowed_sources=allowed_sources,
        temperature=temperature,
        metadata=bound_metadata,
    )


def build_contribution(
    workload: DistributedLLMWorkload,
    *,
    source_id: str,
    request: ProviderRequest,
    response: Optional[ProviderResponse],
    status: str = "RETURNED",
    provenance_refs: Sequence[str],
    evidence_refs: Sequence[str] = (),
    usage_refs: Sequence[str] = (),
    uncertainty_notes: Sequence[str] = (),
    disagreement_refs: Sequence[str] = (),
    metadata: Optional[Mapping[str, Any]] = None,
    created_at: Optional[str] = None,
) -> LLMContribution:
    validate_workload(workload)
    descriptor = workload.source(source_id)
    normalized_status = str(status).strip().upper()
    if normalized_status not in CONTRIBUTION_STATUSES:
        _fail(f"unsupported contribution status {status}")
    if not provenance_refs:
        _fail("contribution provenance_refs are required")
    if request.provider != descriptor.provider or request.model != descriptor.model:
        _fail("provider request identity does not match declared source")
    request_metadata = dict(request.metadata)
    if request_metadata.get("distributed_workload_id") != workload.workload_id:
        _fail("provider request workload_id binding mismatch")
    if request_metadata.get("distributed_workload_hash") != workload.workload_hash:
        _fail("provider request workload_hash binding mismatch")
    if request_metadata.get("distributed_source_id") != descriptor.source_id:
        _fail("provider request source_id binding mismatch")
    _reject_embedded_secrets(request_metadata, "provider_request.metadata")

    response_hash: Optional[str] = None
    output: Optional[str] = None
    if response is not None:
        if response.provider != descriptor.provider or response.model != descriptor.model:
            _fail("provider response identity does not match declared source")
        if response.request_hash != request.request_hash:
            _fail("provider response request_hash mismatch")
        response_hash = response.response_hash
        output = response.output
    elif normalized_status == "RETURNED":
        _fail("RETURNED contribution requires a provider response")

    if normalized_status == "RETURNED" and not output:
        _fail("RETURNED contribution requires non-empty output")

    contribution_metadata = metadata or {}
    _reject_embedded_secrets(contribution_metadata, "contribution.metadata")
    contribution = LLMContribution(
        workload_id=workload.workload_id,
        workload_hash=workload.workload_hash,
        source_id=descriptor.source_id,
        provider=descriptor.provider,
        model=descriptor.model,
        status=normalized_status,
        provider_request_hash=request.request_hash,
        provider_response_hash=response_hash,
        output=output,
        provenance_refs=_tuple_str(provenance_refs),
        evidence_refs=_tuple_str(evidence_refs),
        usage_refs=_tuple_str(usage_refs),
        uncertainty_notes=_tuple_str(uncertainty_notes),
        disagreement_refs=_tuple_str(disagreement_refs),
        metadata=contribution_metadata,
        created_at=created_at or utc_now_iso(),
    )
    validate_contribution(workload, contribution)
    return contribution


def validate_contribution(workload: DistributedLLMWorkload, contribution: LLMContribution) -> bool:
    validate_workload(workload)
    if contribution.schema_version != CONTRIBUTION_SCHEMA_VERSION:
        _fail("unsupported contribution schema")
    if contribution.workload_id != workload.workload_id or contribution.workload_hash != workload.workload_hash:
        _fail("contribution workload binding mismatch")
    descriptor = workload.source(contribution.source_id)
    if contribution.provider != descriptor.provider or contribution.model != descriptor.model:
        _fail("contribution source identity mismatch")
    if contribution.status not in CONTRIBUTION_STATUSES:
        _fail("unsupported contribution status")
    if not contribution.provenance_refs:
        _fail("contribution provenance_refs are required")
    _require_sha256(contribution.provider_request_hash, "provider_request_hash")
    if contribution.provider_response_hash is not None:
        _require_sha256(contribution.provider_response_hash, "provider_response_hash")
    if contribution.status == "RETURNED":
        if not contribution.provider_response_hash or not contribution.output:
            _fail("RETURNED contribution missing response hash or output")
    _reject_embedded_secrets(contribution.metadata, "contribution.metadata")
    if any(contribution.to_dict()["authority"].values()):
        _fail("model contribution cannot grant authority")
    return True


def build_reconciliation_request(
    workload: DistributedLLMWorkload,
    contributions: Sequence[LLMContribution],
    *,
    governance_refs: Sequence[str],
    policy_refs: Sequence[str] = (),
    created_at: Optional[str] = None,
) -> ReconciliationRequest:
    validate_workload(workload)
    if not governance_refs:
        _fail("governance_refs are required for reconciliation")
    by_source: dict[str, LLMContribution] = {}
    for contribution in contributions:
        validate_contribution(workload, contribution)
        if contribution.source_id in by_source:
            _fail(f"duplicate contribution for source {contribution.source_id}")
        by_source[contribution.source_id] = contribution

    for source in workload.sources:
        if source.required and source.source_id not in by_source:
            _fail(f"required source contribution missing: {source.source_id}")

    ordered = [by_source[source.source_id] for source in workload.sources if source.source_id in by_source]
    if not ordered:
        _fail("at least one contribution is required for reconciliation")

    request = ReconciliationRequest(
        workload_id=workload.workload_id,
        workload_hash=workload.workload_hash,
        source_ids=tuple(item.source_id for item in ordered),
        contribution_hashes=tuple(item.contribution_hash for item in ordered),
        governance_refs=_tuple_str(governance_refs),
        policy_refs=_tuple_str(policy_refs or workload.policy_refs),
        created_at=created_at or utc_now_iso(),
    )
    validate_reconciliation_request(workload, ordered, request)
    return request


def validate_reconciliation_request(
    workload: DistributedLLMWorkload,
    contributions: Sequence[LLMContribution],
    request: ReconciliationRequest,
) -> bool:
    if request.schema_version != RECONCILIATION_SCHEMA_VERSION:
        _fail("unsupported reconciliation schema")
    if request.workload_id != workload.workload_id or request.workload_hash != workload.workload_hash:
        _fail("reconciliation workload binding mismatch")
    if not request.governance_refs:
        _fail("reconciliation governance_refs missing")
    expected_sources = tuple(item.source_id for item in contributions)
    expected_hashes = tuple(item.contribution_hash for item in contributions)
    if request.source_ids != expected_sources:
        _fail("reconciliation source order/binding mismatch")
    if request.contribution_hashes != expected_hashes:
        _fail("reconciliation contribution hash mismatch")
    if any(request.to_dict()["authority"].values()):
        _fail("reconciliation request cannot grant authority")
    return True


def build_governed_result(
    workload: DistributedLLMWorkload,
    reconciliation: ReconciliationRequest,
    contributions: Sequence[LLMContribution],
    *,
    disposition: str,
    result_text: Optional[str],
    governance_refs: Sequence[str],
    decision_refs: Sequence[str],
    provenance_refs: Sequence[str],
    evidence_refs: Sequence[str] = (),
    created_at: Optional[str] = None,
) -> GovernedLLMResult:
    ordered = tuple(contributions)
    validate_reconciliation_request(workload, ordered, reconciliation)
    normalized_disposition = str(disposition).strip().upper()
    if normalized_disposition not in RESULT_DISPOSITIONS:
        _fail(f"unsupported governed result disposition {disposition}")
    if normalized_disposition == "ADMITTED" and not (result_text or "").strip():
        _fail("ADMITTED governed result requires result_text")
    if not governance_refs:
        _fail("governed result requires governance_refs")
    if not decision_refs:
        _fail("governed result requires decision_refs from the existing governance path")
    if not provenance_refs:
        _fail("governed result requires provenance_refs")

    result = GovernedLLMResult(
        workload_id=workload.workload_id,
        workload_hash=workload.workload_hash,
        reconciliation_hash=reconciliation.reconciliation_hash,
        disposition=normalized_disposition,
        result_text=result_text,
        source_ids=reconciliation.source_ids,
        contribution_hashes=reconciliation.contribution_hashes,
        governance_refs=_tuple_str(governance_refs),
        decision_refs=_tuple_str(decision_refs),
        provenance_refs=_tuple_str(provenance_refs),
        evidence_refs=_tuple_str(evidence_refs),
        created_at=created_at or utc_now_iso(),
    )
    validate_governed_result(workload, reconciliation, result)
    return result


def validate_governed_result(
    workload: DistributedLLMWorkload,
    reconciliation: ReconciliationRequest,
    result: GovernedLLMResult,
) -> bool:
    if result.schema_version != GOVERNED_RESULT_SCHEMA_VERSION:
        _fail("unsupported governed result schema")
    if result.workload_id != workload.workload_id or result.workload_hash != workload.workload_hash:
        _fail("governed result workload binding mismatch")
    if result.reconciliation_hash != reconciliation.reconciliation_hash:
        _fail("governed result reconciliation hash mismatch")
    if result.source_ids != reconciliation.source_ids:
        _fail("governed result source binding mismatch")
    if result.contribution_hashes != reconciliation.contribution_hashes:
        _fail("governed result contribution binding mismatch")
    if result.disposition not in RESULT_DISPOSITIONS:
        _fail("unsupported governed result disposition")
    if result.disposition == "ADMITTED" and not (result.result_text or "").strip():
        _fail("ADMITTED governed result requires result_text")
    if not result.governance_refs or not result.decision_refs or not result.provenance_refs:
        _fail("governed result governance/decision/provenance refs missing")
    if any(result.to_dict()["authority"].values()):
        _fail("governed result envelope cannot grant authority")
    return True


__all__ = [
    "WORKLOAD_SCHEMA_VERSION",
    "CONTRIBUTION_SCHEMA_VERSION",
    "RECONCILIATION_SCHEMA_VERSION",
    "GOVERNED_RESULT_SCHEMA_VERSION",
    "ROUTING_MODES",
    "CONTRIBUTION_STATUSES",
    "RESULT_DISPOSITIONS",
    "SourceDescriptor",
    "DistributedLLMWorkload",
    "LLMContribution",
    "ReconciliationRequest",
    "GovernedLLMResult",
    "build_source_descriptor",
    "build_distributed_workload",
    "build_source_provider_request",
    "build_contribution",
    "build_reconciliation_request",
    "build_governed_result",
    "validate_workload",
    "validate_contribution",
    "validate_reconciliation_request",
    "validate_governed_result",
]
