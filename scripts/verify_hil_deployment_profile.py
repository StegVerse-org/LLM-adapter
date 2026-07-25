#!/usr/bin/env python3
"""Fail-closed static verification for the HIL deployment profile."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "HIL_DEPLOYMENT_PROFILE.md"
ENV = ROOT / "deploy" / "hil.env.example"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"HIL deployment profile verification failed: {message}")


def main() -> None:
    require(DOC.is_file(), "missing deployment profile")
    require(ENV.is_file(), "missing environment example")
    doc = DOC.read_text(encoding="utf-8")
    env = ENV.read_text(encoding="utf-8")

    markers = (
        "HIL-DEPLOYMENT-PROFILE-v1",
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
        "actual service restart",
        "deployment configured != public acquisition authorized",
        "StegVerse-Labs/Site/data/hil-deployed-controlled-cycle-evidence.json",
    )
    for marker in markers:
        require(marker in doc, f"documentation missing marker: {marker}")

    expected = {
        "STEGVERSE_HIL_INTAKE_ENABLED": "false",
        "STEGVERSE_HIL_DATA_DIR": "/var/lib/stegverse/hil",
        "STEGVERSE_STORAGE_DURABLE_ACROSS_RESTARTS": "false",
        "STEGVERSE_HIL_REVIEW_TOKEN": "REPLACE_IN_SECRET_STORE",
        "STEGVERSE_HIL_PUBLICATION_TOKEN": "REPLACE_IN_SECRET_STORE",
    }
    parsed: dict[str, str] = {}
    for line in env.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        require("=" in line, f"invalid environment line: {line}")
        key, value = line.split("=", 1)
        parsed[key] = value

    require(parsed == expected, "environment example must remain exact and fail closed")
    require(parsed["STEGVERSE_HIL_REVIEW_TOKEN"] == parsed["STEGVERSE_HIL_PUBLICATION_TOKEN"],
            "example placeholders should match without implying configured separation")
    require(not re.search(r"(?i)(token|secret)=[A-Za-z0-9_-]{24,}", env),
            "environment example appears to contain a real secret")
    require("STEGVERSE_HIL_INTAKE_ENABLED=true" not in env,
            "example must not enable intake by default")
    require("STEGVERSE_STORAGE_DURABLE_ACROSS_RESTARTS=true" not in env,
            "example must not declare durability by default")

    print("HIL_DEPLOYMENT_PROFILE_VERIFICATION=PASS")
    print("HIL_DEPLOYMENT_DEFAULT=FAIL_CLOSED")
    print("HIL_RUNTIME_SECRETS_COMMITTED=false")
    print("HIL_ACTIVATION_AUTHORITY=NONE")


if __name__ == "__main__":
    main()
