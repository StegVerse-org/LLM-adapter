"""End-to-end governed LLM proof pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .governed_adapter import GovernedAdapterResult, GovernedLLMAdapter
from .provider import LLMProviderClient
from .retrieval import InMemoryRetrievalIndex, default_fixture_index


@dataclass(frozen=True)
class PipelineInput:
    query: str
    allowed_sources: tuple[str, ...] = ("receipt_index", "policy_index")
    purpose: Optional[str] = None
    transition_class: str = "candidate_response"


class GovernedLLMPipeline:
    """Retrieval + provider candidate + governed adapter result."""

    def __init__(
        self,
        provider: LLMProviderClient,
        retrieval_index: Optional[InMemoryRetrievalIndex] = None,
    ) -> None:
        self.provider = provider
        self.retrieval_index = retrieval_index or default_fixture_index()
        self.adapter = GovernedLLMAdapter(
            default_provider=provider.provider_name,
            default_model=provider.model_name,
        )

    def run(self, pipeline_input: PipelineInput) -> GovernedAdapterResult:
        evidence = self.retrieval_index.search(
            pipeline_input.query,
            pipeline_input.allowed_sources,
        )
        candidate = self.provider.complete(pipeline_input.query)
        return self.adapter.govern_response(
            query=pipeline_input.query,
            candidate_output=candidate.text,
            allowed_sources=pipeline_input.allowed_sources,
            evidence=evidence,
            purpose=pipeline_input.purpose,
            transition_class=pipeline_input.transition_class,
            model_provider=candidate.provider,
            model_name=candidate.model,
            policy={"policy": "fixture-read-only"},
            delegation={"adapter": "read"},
        )


def run_fixture_pipeline(query: str, candidate_text: str) -> dict:
    """Run the default proof path and return a plain dictionary."""

    from .provider import StaticProviderClient

    pipeline = GovernedLLMPipeline(StaticProviderClient(candidate_text))
    result = pipeline.run(PipelineInput(query=query))
    return result.to_dict()


__all__ = [
    "GovernedLLMPipeline",
    "PipelineInput",
    "run_fixture_pipeline",
]
