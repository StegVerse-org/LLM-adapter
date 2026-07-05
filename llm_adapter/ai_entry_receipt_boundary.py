"""Preview-only receipt issuer boundary mirror for StegVerse AI Entry.

This module mirrors the SDK receipt issuer boundary without issuing,
persisting, or reconstructing real receipts. It is safe to import because it
performs no provider calls, SDK calls, credential access, or side effects.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ReceiptPreview:
    """Non-issuing receipt preview returned by the adapter boundary."""

    receipt_id: str = "preview-not-issued"
    status: str = "NOT_ISSUED"
    mode: str = "preview_only"
    real_receipt_issued: bool = False
    receipt_persisted: bool = False
    reconstruction_available: bool = False
    authority_issued: bool = False
    execution_allowed: bool = False
    live_calls_allowed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def preview_receipt(_: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return a fail-closed receipt preview.

    The input is intentionally ignored because this boundary is not a real
    issuer and must not persist or certify receipt data.
    """

    return ReceiptPreview().to_dict()


__all__ = ["ReceiptPreview", "preview_receipt"]
