"""Bounded distributed LLM execution adapter for Ecosystem Chat.

This module consumes a validated DistributedLLMWorkload and explicitly injected
ProviderClient instances. It executes only the bounded modes whose prompt/input
semantics are already defined by the workload contract: single, parallel, and
fallback. Sequential and challenge modes fail closed until a separately governed
derived-input contract exists.

The executor is not a provider broker, governance engine, route authority,
credential authority, WorkerCoordinator, heartbeat, or custody service.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional, Sequence

from .distributed_workload import (
    DistributedLLMWorkload,
    LLMContribution,
    build_contribution,
    build_source_provider_request,
    validate_workload,
)
from .provider_client import ProviderClient, ProviderResponse
from .provider_request import ProviderMessage, stable_hash, utc_now_iso


EXECUTION_SCHEMA_VERSION = "stegverse.ecosystem_chat.distributed_llm_execution.v1"
SUPPORTED_EXECUTION_MODES = frozenset({"single", "parallel", "fallback"})
UNSUPPORTED_DERIVED_INPUT_MODES = frozenset({"sequential", "challenge"})


class ProviderRefusalError(RuntimeError):
    """Explicit provider refusal retained as contribution evidence."""


@dataclass(frozen=True)
class DistributedExecutionSummary:
    workload_id: str
    workload_hash: str
    routing_mode: str
    attempted_source_ids: tuple[str, ...]
    returned_source_ids: tuple[str, ...]
    refused_source_ids: tuple[str, ...]
    failed_source_ids: tuple[str, ...]
    skipped_source_ids: tuple[str, ...]
    contribution_hashes: tuple[str, ...]
    created_at: str
    schema_version: str = EXECUTION_SCHEMA_VERSION

    def payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "workload_id": self.workload_id,
            "workload_hash": self.workload_hash,
            "routing_mode": self.routing_mode,
            "attempted_source_ids": list(self.attempted_source_ids),
            "returned_source_ids": list(self.returned_source_ids),
            "refused_source_ids": list(self.refused_source_ids),
            "failed_source_ids": list(self.failed_source_ids),
            "skipped_source_ids": list(self.skipped_source_ids),
            "contribution_hashes": list(self.contribution_hashes),
            "created_at": self.created_at,
            "authority": {
                "provider_broker_authority": False,
                "governance_authority": False,
                "route_authority": False,
                "credential_authority": False,
                "custody_authority": False,
                "execution_admission_authority": False,
            },
        }

    @property
    def execution_hash(self) -> str:
        return stable_hash(self.payload())

    def to_dict(self) -> dict[str, Any]:
        data = self.payload()
        data["execution_hash"] = self.execution_hash
        return data


@dataclass(frozen=True)
class DistributedExecutionResult:
    summary: DistributedExecutionSummary
    contributions: tuple[LLMContribution, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": self.summary.to_dict(),
            "contributions": [contribution.to_dict() for contribution in self.contributions],
        }


def _fail(reason: str) -> None:
    raise ValueError(f"FAIL_CLOSED: {reason}")


def _usage_refs(response: Optional[ProviderResponse]) -> tuple[str, ...]:
    if response is None:
        return ()
    metadata = dict(response.metadata)
    refs = metadata.get("usage_refs")
    if refs is None:
        single = metadata.get("usage_ref")
        return (str(single),) if single else ()
    if not isinstance(refs, (list, tuple)):
        _fail("provider response usage_refs must be a list/tuple when present")
    return tuple(str(ref) for ref in refs if str(ref))


def _provenance_refs(
    workload: DistributedLLMWorkload,
    source_id: str,
    request_hash: str,
    response: Optional[ProviderResponse],
) -> tuple[str, ...]:
    refs = [
        f"workload:{workload.workload_id}",
        f"source:{source_id}",
        f"provider-request:{request_hash}",
    ]
    if response is not None:
        refs.append(f"provider-response:{response.response_hash}")
    return tuple(refs)


def _validate_clients(workload: DistributedLLMWorkload, clients: Mapping[str, ProviderClient]) -> None:
    declared = {source.source_id for source in workload.sources}
    supplied = set(clients)
    undeclared = sorted(supplied - declared)
    if undeclared:
        _fail(f"provider client supplied for undeclared source(s): {undeclared}")
    missing_required = sorted(
        source.source_id
        for source in workload.sources
        if source.required and source.source_id not in supplied
    )
    if missing_required:
        _fail(f"missing required provider client(s): {missing_required}")


def _execute_one(
    workload: DistributedLLMWorkload,
    source_id: str,
    client: Optional[ProviderClient],
    messages: Sequence[Mapping[str, str] | ProviderMessage],
    *,
    allowed_sources: Sequence[str],
    temperature: float,
    request_metadata: Optional[Mapping[str, Any]],
    created_at: str,
) -> LLMContribution:
    descriptor = workload.source(source_id)
    request = build_source_provider_request(
        workload,
        source_id,
        messages,
        allowed_sources=allowed_sources,
        temperature=temperature,
        metadata=request_metadata,
    )

    if client is None:
        if descriptor.required:
            _fail(f"required source client missing during execution: {source_id}")
        return build_contribution(
            workload,
            source_id=source_id,
            request=request,
            response=None,
            status="FAILED",
            provenance_refs=_provenance_refs(workload, source_id, request.request_hash, None),
            evidence_refs=(f"source-unavailable:{source_id}",),
            uncertainty_notes=("optional named source had no injected ProviderClient",),
            metadata={"failure_class": "OPTIONAL_SOURCE_CLIENT_UNAVAILABLE"},
            created_at=created_at,
        )

    try:
        response = client.complete(request)
    except ProviderRefusalError as exc:
        return build_contribution(
            workload,
            source_id=source_id,
            request=request,
            response=None,
            status="REFUSED",
            provenance_refs=_provenance_refs(workload, source_id, request.request_hash, None),
            evidence_refs=(f"provider-refusal:{source_id}",),
            uncertainty_notes=(str(exc) or "provider refused request",),
            metadata={"failure_class": "PROVIDER_REFUSAL"},
            created_at=created_at,
        )
    except Exception as exc:  # provider failure is evidence, not silent substitution
        return build_contribution(
            workload,
            source_id=source_id,
            request=request,
            response=None,
            status="FAILED",
            provenance_refs=_provenance_refs(workload, source_id, request.request_hash, None),
            evidence_refs=(f"provider-failure:{source_id}",),
            uncertainty_notes=(f"{type(exc).__name__}: {exc}",),
            metadata={"failure_class": "PROVIDER_EXCEPTION", "exception_type": type(exc).__name__},
            created_at=created_at,
        )

    return build_contribution(
        workload,
        source_id=source_id,
        request=request,
        response=response,
        status="RETURNED",
        provenance_refs=_provenance_refs(workload, source_id, request.request_hash, response),
        usage_refs=_usage_refs(response),
        metadata={"provider_response_metadata_present": bool(response.metadata)},
        created_at=created_at,
    )


def execute_distributed_workload(
    workload: DistributedLLMWorkload,
    clients: Mapping[str, ProviderClient],
    messages: Sequence[Mapping[str, str] | ProviderMessage],
    *,
    allowed_sources: Sequence[str] = ("model_knowledge",),
    temperature: float = 0.0,
    request_metadata: Optional[Mapping[str, Any]] = None,
    created_at: Optional[str] = None,
) -> DistributedExecutionResult:
    """Execute a bounded named-source workload.

    `parallel` means independent fan-out semantics: each named source receives the
    same canonical message set and no contribution is fed into another source. The
    implementation intentionally preserves deterministic workload order rather than
    claiming concurrent scheduling authority.
    """

    validate_workload(workload)
    _validate_clients(workload, clients)
    timestamp = created_at or utc_now_iso()

    if workload.routing_mode in UNSUPPORTED_DERIVED_INPUT_MODES:
        _fail(
            f"routing_mode {workload.routing_mode} requires a governed derived-input contract; "
            "executor will not invent sequential/challenge prompt semantics"
        )
    if workload.routing_mode not in SUPPORTED_EXECUTION_MODES:
        _fail(f"unsupported execution routing_mode {workload.routing_mode}")

    contributions: list[LLMContribution] = []
    attempted: list[str] = []
    skipped: list[str] = []

    for index, descriptor in enumerate(workload.sources):
        source_id = descriptor.source_id

        if workload.routing_mode == "fallback" and any(item.status == "RETURNED" for item in contributions):
            skipped.extend(source.source_id for source in workload.sources[index:])
            break

        attempted.append(source_id)
        contribution = _execute_one(
            workload,
            source_id,
            clients.get(source_id),
            messages,
            allowed_sources=allowed_sources,
            temperature=temperature,
            request_metadata=request_metadata,
            created_at=timestamp,
        )
        contributions.append(contribution)

        if workload.routing_mode == "single":
            break

    returned = tuple(item.source_id for item in contributions if item.status == "RETURNED")
    refused = tuple(item.source_id for item in contributions if item.status == "REFUSED")
    failed = tuple(item.source_id for item in contributions if item.status == "FAILED")

    summary = DistributedExecutionSummary(
        workload_id=workload.workload_id,
        workload_hash=workload.workload_hash,
        routing_mode=workload.routing_mode,
        attempted_source_ids=tuple(attempted),
        returned_source_ids=returned,
        refused_source_ids=refused,
        failed_source_ids=failed,
        skipped_source_ids=tuple(skipped),
        contribution_hashes=tuple(item.contribution_hash for item in contributions),
        created_at=timestamp,
    )
    validate_execution_result(workload, DistributedExecutionResult(summary, tuple(contributions)))
    return DistributedExecutionResult(summary, tuple(contributions))


def validate_execution_result(workload: DistributedLLMWorkload, result: DistributedExecutionResult) -> bool:
    summary = result.summary
    if summary.schema_version != EXECUTION_SCHEMA_VERSION:
        _fail("unsupported distributed execution summary schema")
    if summary.workload_id != workload.workload_id or summary.workload_hash != workload.workload_hash:
        _fail("execution summary workload binding mismatch")
    if summary.routing_mode != workload.routing_mode:
        _fail("execution summary routing mode mismatch")
    if tuple(item.contribution_hash for item in result.contributions) != summary.contribution_hashes:
        _fail("execution summary contribution hash mismatch")
    if tuple(item.source_id for item in result.contributions) != summary.attempted_source_ids:
        _fail("execution summary attempted source binding mismatch")
    declared = {source.source_id for source in workload.sources}
    for collection_name, values in (
        ("returned", summary.returned_source_ids),
        ("refused", summary.refused_source_ids),
        ("failed", summary.failed_source_ids),
        ("skipped", summary.skipped_source_ids),
    ):
        unknown = set(values) - declared
        if unknown:
            _fail(f"execution summary {collection_name} references unknown sources: {sorted(unknown)}")
    if any(summary.to_dict()["authority"].values()):
        _fail("distributed execution summary cannot grant authority")
    return True


__all__ = [
    "EXECUTION_SCHEMA_VERSION",
    "SUPPORTED_EXECUTION_MODES",
    "UNSUPPORTED_DERIVED_INPUT_MODES",
    "ProviderRefusalError",
    "DistributedExecutionSummary",
    "DistributedExecutionResult",
    "execute_distributed_workload",
    "validate_execution_result",
]
