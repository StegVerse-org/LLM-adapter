"""Provider abstraction for governed LLM candidates.

This module keeps provider execution separate from governance.  Providers return
candidate text; `GovernedLLMAdapter` decides whether that candidate may be
returned, denied, or quarantined.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class CandidateResponse:
    """Raw candidate returned by a model provider before governance."""

    provider: str
    model: str
    text: str


class LLMProviderClient(Protocol):
    """Small provider protocol for adapter integrations."""

    provider_name: str
    model_name: str

    def complete(self, prompt: str) -> CandidateResponse:
        """Return a candidate response for the prompt."""


@dataclass(frozen=True)
class StaticProviderClient:
    """Deterministic provider fixture used for tests and local proof paths."""

    text: str
    provider_name: str = "static-fixture"
    model_name: str = "static-candidate"

    def complete(self, prompt: str) -> CandidateResponse:
        return CandidateResponse(
            provider=self.provider_name,
            model=self.model_name,
            text=self.text,
        )


__all__ = [
    "CandidateResponse",
    "LLMProviderClient",
    "StaticProviderClient",
]
