"""Disabled-by-default provider boundary for StegVerse AI Entry.

This module intentionally performs no live provider calls. It exists so the
Site AI Entry Point and future backend service can share a stable adapter
contract before any provider credentials or live calls are introduced.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Iterable

DEFAULT_PROVIDERS = ("ChatGPT", "Claude", "Other LLM")


@dataclass(frozen=True)
class ProviderComparison:
    provider: str
    enabled: bool
    live_call_allowed: bool
    authority: bool
    comparison_only: bool
    response: str


@dataclass(frozen=True)
class ProviderBoundaryResult:
    live_provider_calls_enabled: bool
    credential_surface_enabled: bool
    provider_secret_required_for_tests: bool
    provider_output_is_authority: bool
    receipt_capture_required_before_live_activation: bool
    comparisons: list[ProviderComparison]

    def to_dict(self) -> dict:
        data = asdict(self)
        data["comparisons"] = [asdict(item) for item in self.comparisons]
        return data


def build_disabled_provider_boundary(providers: Iterable[str] = DEFAULT_PROVIDERS) -> ProviderBoundaryResult:
    comparisons = [
        ProviderComparison(
            provider=provider,
            enabled=False,
            live_call_allowed=False,
            authority=False,
            comparison_only=True,
            response="Comparison placeholder pending governed provider adapter activation.",
        )
        for provider in providers
    ]
    return ProviderBoundaryResult(
        live_provider_calls_enabled=False,
        credential_surface_enabled=False,
        provider_secret_required_for_tests=False,
        provider_output_is_authority=False,
        receipt_capture_required_before_live_activation=True,
        comparisons=comparisons,
    )


def main() -> int:
    import json

    print(json.dumps(build_disabled_provider_boundary().to_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
