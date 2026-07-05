"""Preview-only recovery boundary mirror for StegVerse AI Entry.

The mirror returns a disabled decision object. It performs no network calls,
no provider calls, no SDK calls, and no side effects.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class RecoveryPreview:
    """Disabled recovery preview."""

    decision: str = "DENY"
    mode: str = "preview_only"
    recovery_confirmed: bool = False
    activation_allowed: bool = False
    execution_allowed: bool = False
    live_provider_calls_allowed: bool = False
    live_sdk_calls_allowed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def preview_recovery(_: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return a disabled recovery preview."""

    return RecoveryPreview().to_dict()


__all__ = ["RecoveryPreview", "preview_recovery"]
