"""Preview-only provider capture boundary for StegVerse AI Entry.

This module defines the shape of a future provider capture record while keeping
all provider calls disabled. Importing and calling this module has no network
access and no side effects.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ProviderCapturePreview:
    """Disabled provider capture preview."""

    capture_id: str = "provider-capture-preview"
    mode: str = "preview_only"
    provider_call_performed: bool = False
    provider_output_captured: bool = False
    provider_authority: bool = False
    persisted: bool = False
    live_calls_allowed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def preview_provider_capture(_: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return a disabled provider capture preview."""

    return ProviderCapturePreview().to_dict()


__all__ = ["ProviderCapturePreview", "preview_provider_capture"]
