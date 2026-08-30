#!/usr/bin/env python3
"""Verify the exact checked-in HIL InTr source projection without network access."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _digest(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def verify(artifact: Path, manifest_path: Path) -> None:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    raw = artifact.read_bytes()
    if manifest.get("artifact_sha256") != _digest(raw):
        raise ValueError("generated_hil_intr_artifact_hash_mismatch")
    spec = importlib.util.spec_from_file_location("verified_generated_hil_intr", artifact)
    if spec is None or spec.loader is None:
        raise ValueError("generated_hil_intr_import_spec_invalid")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    provenance = module.PROVENANCE
    for key in (
        "generator_schema",
        "source_repository",
        "registry_path",
        "registry_sha256",
        "profile_sha256",
        "credential_authority",
        "github_runtime_dependency",
        "pypi_dependency",
        "cdn_dependency",
        "third_party_package_authority",
        "authority_effect",
    ):
        if manifest.get(key) != provenance.get(key):
            raise ValueError(f"generated_hil_intr_provenance_mismatch:{key}")
    if manifest.get("profiles") != list(module.PROFILES):
        raise ValueError("generated_hil_intr_profile_order_mismatch")
    for profile_id, profile in module.PROFILES.items():
        if manifest["profile_sha256"].get(profile_id) != _digest(_canonical(profile)):
            raise ValueError(f"generated_hil_intr_profile_hash_mismatch:{profile_id}")
    if provenance.get("credential_authority") != "TV/TVC":
        raise ValueError("generated_hil_intr_credential_authority_invalid")
    for key in (
        "github_runtime_dependency",
        "pypi_dependency",
        "cdn_dependency",
        "third_party_package_authority",
    ):
        if provenance.get(key) is not False:
            raise ValueError(f"generated_hil_intr_forbidden_dependency:{key}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", type=Path, default=Path("llm_adapter/generated_intr/hil_submission_connector.py"))
    parser.add_argument("--manifest", type=Path, default=Path("llm_adapter/generated_intr/hil_submission_connector.manifest.json"))
    args = parser.parse_args()
    verify(args.artifact, args.manifest)
    print("GENERATED_HIL_INTR_VERIFIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
