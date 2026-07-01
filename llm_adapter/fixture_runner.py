"""Fixture runner for governed LLM adapter tests and demos."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .governed_adapter import GovernedLLMAdapter
from .provider_request import build_provider_request
from .retrieval_evidence import evidence_list_from_fixtures


def run_fixture(fixture: Mapping[str, Any]) -> dict[str, Any]:
    """Run a governed response fixture and return a plain result dictionary."""

    provider_request = fixture["provider_request"]
    request = build_provider_request(
        provider=str(provider_request["provider"]),
        model=str(provider_request["model"]),
        messages=provider_request["messages"],
        purpose=str(provider_request.get("purpose", "answer")),
        allowed_sources=provider_request.get("allowed_sources", ("model_knowledge",)),
        temperature=float(provider_request.get("temperature", 0.0)),
        metadata=provider_request.get("metadata", {}),
    )
    evidence = evidence_list_from_fixtures(fixture.get("evidence", ()))
    adapter = GovernedLLMAdapter(default_provider=request.provider, default_model=request.model)
    result = adapter.govern_response(
        query=request.user_query,
        candidate_output=str(fixture["candidate_output"]),
        allowed_sources=request.allowed_sources,
        evidence=evidence,
        purpose=request.purpose,
        policy=fixture.get("policy", {}),
        delegation=fixture.get("delegation", {}),
        model_provider=request.provider,
        model_name=request.model,
    ).to_dict()
    result["provider_request_hash"] = request.request_hash
    return result


def run_fixture_file(path: str | Path) -> dict[str, Any]:
    """Load and run a JSON fixture file."""

    fixture = json.loads(Path(path).read_text(encoding="utf-8"))
    return run_fixture(fixture)


__all__ = ["run_fixture", "run_fixture_file"]
