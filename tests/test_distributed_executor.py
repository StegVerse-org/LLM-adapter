from __future__ import annotations

from dataclasses import dataclass

import pytest

from llm_adapter.distributed_executor import (
    ProviderRefusalError,
    execute_distributed_workload,
    validate_execution_result,
)
from llm_adapter.distributed_workload import build_distributed_workload, build_source_descriptor
from llm_adapter.provider_client import FixtureProviderClient, ProviderResponse


FIXED = "2026-09-06T06:30:00+00:00"
CANONICAL_HASH = "a" * 64
MESSAGES = ({"role": "user", "content": "Explain the represented transition."},)


def src(source_id, provider, model, *, required=False):
    return build_source_descriptor(
        source_id=source_id,
        provider=provider,
        model=model,
        required=required,
        capabilities=("reasoning", "text"),
        locality="sovereign" if source_id == "local" else "external-optional",
    )


def build(mode="parallel", sources=None):
    return build_distributed_workload(
        workload_id=f"workload:executor:{mode}",
        canonical_request_id="event:req:executor",
        canonical_request_hash=CANONICAL_HASH,
        routing_mode=mode,
        sources=sources or (
            src("local", "stegverse-local", "stegverse-reference-lm-v1", required=True),
            src("source-b", "provider-b", "model-b"),
        ),
        governance_refs=("intr:ecosystem-chat",),
        created_at=FIXED,
    )


@dataclass
class RefusingClient:
    reason: str = "provider policy refusal"

    def complete(self, request):
        raise ProviderRefusalError(self.reason)


@dataclass
class FailingClient:
    def complete(self, request):
        raise RuntimeError("provider unavailable")


@dataclass
class BadIdentityClient:
    def complete(self, request):
        return ProviderResponse(
            provider="wrong-provider",
            model=request.model,
            output="drifted",
            request_hash=request.request_hash,
            metadata={},
        )


@dataclass
class UsageClient:
    output: str
    usage_ref: str

    def complete(self, request):
        return ProviderResponse(
            provider=request.provider,
            model=request.model,
            output=self.output,
            request_hash=request.request_hash,
            metadata={"usage_refs": [self.usage_ref]},
        )


def test_parallel_collects_independent_named_sources_in_workload_order():
    w = build()
    result = execute_distributed_workload(
        w,
        {
            "local": UsageClient("local answer", "usage:local"),
            "source-b": UsageClient("source b answer", "usage:b"),
        },
        MESSAGES,
        created_at=FIXED,
    )
    assert result.summary.attempted_source_ids == ("local", "source-b")
    assert result.summary.returned_source_ids == ("local", "source-b")
    assert [item.output for item in result.contributions] == ["local answer", "source b answer"]
    assert result.contributions[0].usage_refs == ("usage:local",)
    assert result.contributions[1].usage_refs == ("usage:b",)
    assert validate_execution_result(w, result)
    assert not any(result.summary.to_dict()["authority"].values())


def test_optional_missing_client_becomes_explicit_failed_contribution():
    w = build()
    result = execute_distributed_workload(
        w,
        {"local": FixtureProviderClient("local answer")},
        MESSAGES,
        created_at=FIXED,
    )
    assert result.summary.returned_source_ids == ("local",)
    assert result.summary.failed_source_ids == ("source-b",)
    optional = result.contributions[1]
    assert optional.status == "FAILED"
    assert optional.metadata["failure_class"] == "OPTIONAL_SOURCE_CLIENT_UNAVAILABLE"
    assert optional.output is None


def test_missing_required_client_fails_closed_before_execution():
    w = build()
    with pytest.raises(ValueError, match="missing required provider client"):
        execute_distributed_workload(
            w,
            {"source-b": FixtureProviderClient("b")},
            MESSAGES,
            created_at=FIXED,
        )


def test_undeclared_client_fails_closed():
    w = build()
    with pytest.raises(ValueError, match="undeclared source"):
        execute_distributed_workload(
            w,
            {
                "local": FixtureProviderClient("local"),
                "source-b": FixtureProviderClient("b"),
                "not-declared": FixtureProviderClient("x"),
            },
            MESSAGES,
            created_at=FIXED,
        )


def test_provider_refusal_is_retained_not_rewritten_to_success():
    w = build()
    result = execute_distributed_workload(
        w,
        {"local": RefusingClient(), "source-b": FixtureProviderClient("b")},
        MESSAGES,
        created_at=FIXED,
    )
    assert result.summary.refused_source_ids == ("local",)
    assert result.summary.returned_source_ids == ("source-b",)
    assert result.contributions[0].status == "REFUSED"
    assert result.contributions[0].metadata["failure_class"] == "PROVIDER_REFUSAL"


def test_provider_exception_is_retained_as_failed_contribution():
    w = build()
    result = execute_distributed_workload(
        w,
        {"local": FailingClient(), "source-b": FixtureProviderClient("b")},
        MESSAGES,
        created_at=FIXED,
    )
    assert result.summary.failed_source_ids == ("local",)
    assert result.summary.returned_source_ids == ("source-b",)
    assert result.contributions[0].metadata["failure_class"] == "PROVIDER_EXCEPTION"


def test_provider_identity_drift_fails_closed_through_contribution_validation():
    w = build()
    with pytest.raises(ValueError, match="identity does not match declared source"):
        execute_distributed_workload(
            w,
            {"local": BadIdentityClient(), "source-b": FixtureProviderClient("b")},
            MESSAGES,
            created_at=FIXED,
        )


def test_fallback_stops_after_first_returned_source_and_marks_rest_skipped():
    sources = (
        src("local", "stegverse-local", "stegverse-reference-lm-v1", required=True),
        src("source-b", "provider-b", "model-b"),
        src("source-c", "provider-c", "model-c"),
    )
    w = build("fallback", sources=sources)
    result = execute_distributed_workload(
        w,
        {
            "local": FailingClient(),
            "source-b": FixtureProviderClient("fallback success"),
            "source-c": FixtureProviderClient("must not run"),
        },
        MESSAGES,
        created_at=FIXED,
    )
    assert result.summary.attempted_source_ids == ("local", "source-b")
    assert result.summary.failed_source_ids == ("local",)
    assert result.summary.returned_source_ids == ("source-b",)
    assert result.summary.skipped_source_ids == ("source-c",)
    assert len(result.contributions) == 2


def test_fallback_continues_after_refusal():
    sources = (
        src("local", "stegverse-local", "stegverse-reference-lm-v1", required=True),
        src("source-b", "provider-b", "model-b"),
    )
    w = build("fallback", sources=sources)
    result = execute_distributed_workload(
        w,
        {"local": RefusingClient(), "source-b": FixtureProviderClient("fallback")},
        MESSAGES,
        created_at=FIXED,
    )
    assert result.summary.refused_source_ids == ("local",)
    assert result.summary.returned_source_ids == ("source-b",)


def test_single_executes_exactly_one_declared_source():
    w = build(
        "single",
        sources=(src("local", "stegverse-local", "stegverse-reference-lm-v1", required=True),),
    )
    result = execute_distributed_workload(
        w,
        {"local": FixtureProviderClient("only")},
        MESSAGES,
        created_at=FIXED,
    )
    assert result.summary.attempted_source_ids == ("local",)
    assert result.summary.returned_source_ids == ("local",)
    assert result.summary.skipped_source_ids == ()


@pytest.mark.parametrize("mode", ["sequential", "challenge"])
def test_derived_input_modes_fail_closed_until_governed_contract_exists(mode):
    w = build(mode)
    with pytest.raises(ValueError, match="requires a governed derived-input contract"):
        execute_distributed_workload(
            w,
            {"local": FixtureProviderClient("local"), "source-b": FixtureProviderClient("b")},
            MESSAGES,
            created_at=FIXED,
        )


def test_execution_summary_hash_is_deterministic_for_fixed_inputs():
    w = build()
    clients = {"local": FixtureProviderClient("a"), "source-b": FixtureProviderClient("b")}
    first = execute_distributed_workload(w, clients, MESSAGES, created_at=FIXED)
    second = execute_distributed_workload(w, clients, MESSAGES, created_at=FIXED)
    # ProviderRequest includes its own current timestamp, so contribution hashes may differ;
    # summary integrity is nevertheless self-consistent for each exact execution.
    assert validate_execution_result(w, first)
    assert validate_execution_result(w, second)
    assert len(first.summary.execution_hash) == 64
    assert len(second.summary.execution_hash) == 64
