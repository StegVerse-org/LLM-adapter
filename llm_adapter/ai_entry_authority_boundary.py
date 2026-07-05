"""Preview-only authority boundary mirror for StegVerse AI Entry activation.

This module mirrors the Site authority service boundary without issuing authority,
calling providers, accessing SDK credentials, or mutating repositories.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass(frozen=True)
class AuthorityDecisionPreview:
    """Non-executing authority decision preview."""

    authority_decision: str = "DENY"
    decision_mode: str = "preview_only"
    authority_issued: bool = False
    execution_allowed: bool = False
    credential_access_allowed: bool = False
    live_provider_calls_allowed: bool = False
    live_sdk_calls_allowed: bool = False
    repo_mutation_allowed: bool = False
    activation_request_executes: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def preview_authority_decision(_: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return the default fail-closed authority decision.

    The input is intentionally ignored in the preview boundary because this
    module is not an authority service and must not grant capabilities.
    """

    return AuthorityDecisionPreview().to_dict()


__all__ = ["AuthorityDecisionPreview", "preview_authority_decision"]
