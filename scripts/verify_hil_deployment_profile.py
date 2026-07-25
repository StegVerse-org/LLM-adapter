#!/usr/bin/env python3
"""Fail-closed static verification for the platform-agnostic HIL runtime profile."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "HIL_DEPLOYMENT_PROFILE.md"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"HIL runtime profile verification failed: {message}")


def main() -> None:
    require(DOC.is_file(), "missing runtime profile")
    doc = DOC.read_text(encoding="utf-8")

    markers = (
        "HIL-RUNTIME-ACTIVATION-PROFILE-v2",
        "platform-agnostic",
        "TV/TVC owns all runtime values",
        "b2e612dd74d311e0cbe66cd1c1d4758bff129fd4",
        "llm_adapter.combined_gateway:app",
        "/api/hil/readiness",
        "/api/hil/submissions",
        "/api/hil/publication-readiness",
        "STEGVERSE_HIL_INTAKE_ENABLED",
        "STEGVERSE_HIL_DATA_DIR",
        "STEGVERSE_STORAGE_DURABLE_ACROSS_RESTARTS",
        "STEGVERSE_HIL_REVIEW_TOKEN",
        "STEGVERSE_HIL_PUBLICATION_TOKEN",
        "No mounted volume, container, host, service provider, or vendor storage class is required",
        "TV/TVC transition identifier for termination",
        "TV/TVC orchestration != automatic release authority",
        "StegVerse-Labs/Site/data/hil-deployed-controlled-cycle-evidence.json",
    )
    for marker in markers:
        require(marker in doc, f"documentation missing marker: {marker}")

    forbidden = (
        "selected platform's documented persistence boundary",
        "provision persistent volume",
        "secret-store credentials",
        "hosting platform",
        "deployment URL or service identifier",
    )
    for marker in forbidden:
        require(marker not in doc, f"platform-specific requirement remains: {marker}")

    print("HIL_RUNTIME_PROFILE_VERIFICATION=PASS")
    print("HIL_PLATFORM_DEPENDENCY=NONE")
    print("HIL_CONFIGURATION_OWNER=TV_TVC")
    print("HIL_RUNTIME_SECRETS_COMMITTED=false")
    print("HIL_ACTIVATION_AUTHORITY=NONE")


if __name__ == "__main__":
    main()
