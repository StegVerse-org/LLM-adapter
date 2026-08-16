#!/usr/bin/env python3
"""Fail-closed static verification for the HIL v1.1 compatibility profile.

This validator proves only that the LLM-adapter compatibility documentation is
aligned with the canonical TVC-owned HIL architecture. It grants no runtime,
credential, private-review, publication, custody, Master Record, or release authority.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "HIL_DEPLOYMENT_PROFILE.md"

PRIMARY = "a7b1c62e336b4e244ecf7fdcd10af195401f6c44328de32615b073d2a5c3c462"
PROMPT = "cdff8d2266bb3eefbb6e5d28d9adc548e6c8dfc039debd72fe404f1d0249912c"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"HIL compatibility profile verification failed: {message}")


def main() -> None:
    require(DOC.is_file(), "missing compatibility profile")
    doc = DOC.read_text(encoding="utf-8")

    markers = (
        "HIL-RUNTIME-COMPATIBILITY-PROFILE-v3",
        "StegVerse-Labs/TVC/docs/HIL_TVC_MIRROR_HANDOFF.md",
        "backend: tvc.experiment.controlled-cycle.v1",
        "private_review_owner: StegVerse-Labs/TVC#8",
        "credential_authority: TV/TVC",
        "github_token_runtime_authority: NONE",
        "third_party_runtime_dependency: NONE_ALLOWED",
        "llm_adapter.combined_gateway:app",
        "/api/hil/readiness",
        "/api/hil/submissions",
        "/api/hil/publication-readiness",
        PRIMARY,
        PROMPT,
        "STEGVERSE_HIL_INTAKE_ENABLED",
        "STEGVERSE_HIL_DATA_DIR",
        "STEGVERSE_STORAGE_DURABLE_ACROSS_RESTARTS",
        "STEGVERSE_HIL_REVIEW_TOKEN",
        "STEGVERSE_HIL_PUBLICATION_TOKEN",
        "GitHub token != HIL runtime authority",
        "LLM-adapter != production credential authority",
        "2/7",
        "master-records/orchestration#13",
    )
    for marker in markers:
        require(marker in doc, f"documentation missing marker: {marker}")

    stale_or_prohibited = (
        "52102cccb9ba9016c76434a64e22031b6a8c3edd3b8806e7b664e609216b2946",
        "0ebe215318b4eeeb8ed6422e0954372c314fadc8fac9254e452bc7670a1b9922",
        "b2e612dd74d311e0cbe66cd1c1d4758bff129fd4",
        "STEGVERSE_PROVIDER_TOKEN",
        "github-models",
        "models.github.ai",
        "Render",
    )
    for marker in stale_or_prohibited:
        require(marker not in doc, f"stale/prohibited compatibility requirement remains: {marker}")

    require("TV/TVC" in doc, "TV/TVC authority not declared")
    require("TVC#8" in doc, "canonical private-review owner not declared")

    print("HIL_COMPATIBILITY_PROFILE_VERIFICATION=PASS")
    print("HIL_CANONICAL_RUNTIME_OWNER=TVC")
    print("HIL_CREDENTIAL_AUTHORITY=TV_TVC")
    print("HIL_GITHUB_TOKEN_RUNTIME_AUTHORITY=NONE")
    print("HIL_THIRD_PARTY_RUNTIME_REQUIRED=false")
    print("HIL_ACTIVATION_EFFECT=NONE")


if __name__ == "__main__":
    main()
