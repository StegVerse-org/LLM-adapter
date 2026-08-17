#!/usr/bin/env python3
"""Deterministic local architecture-manifest validation.

This replaces the former hosted Architecture Guard workflow. It reads only the
repository checkout, uses no credentials or remote validator, and exits nonzero
when a strict architecture manifest is violated.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "stegverse.architecture.json"
SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv"}


def _load_manifest() -> dict:
    if not MANIFEST_PATH.is_file():
        raise SystemExit("ARCHITECTURE_GUARD_FAIL: stegverse.architecture.json missing")
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def _required_path_violations(manifest: dict) -> list[str]:
    violations: list[str] = []

    def check_path(rel_path: str, spec: dict, base: Path = ROOT) -> None:
        full = base / rel_path.rstrip("/")
        is_dir = rel_path.endswith("/")
        exists = full.is_dir() if is_dir else full.is_file()
        if spec.get("required", False) and not exists:
            violations.append(f"MISSING required: {rel_path}")
        if exists and "subdirs" in spec:
            for sub, subspec in spec["subdirs"].items():
                check_path(sub, subspec, full)

    for rel_path, spec in manifest.get("expected_structure", {}).items():
        check_path(rel_path, spec)
    return violations


def _forbidden_pattern_hits(manifest: dict) -> list[str]:
    hits: list[str] = []
    patterns = [re.compile(p) for p in manifest.get("file_rules", {}).get("forbidden_patterns", [])]
    for root, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        root_path = Path(root)
        for filename in files:
            rel = (root_path / filename).relative_to(ROOT).as_posix()
            for pattern in patterns:
                if pattern.search(rel):
                    hits.append(f"FORBIDDEN pattern '{pattern.pattern}' matched: {rel}")
    return hits


def _naming_issues() -> list[str]:
    issues: list[str] = []
    for root, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for filename in files:
            if filename.endswith(".py") and not filename.startswith("test_") and filename != "__init__.py":
                if not re.fullmatch(r"[a-z0-9_]+\.py", filename):
                    issues.append(f"NAMING: {filename} (expected snake_case)")
    return issues


def _syntax_filename_issues(manifest: dict) -> list[str]:
    migration = manifest.get("migration_rules", {})
    review_dir = migration.get("review_needed_path", "review_needed/").rstrip("/")
    legacy_dir = migration.get("legacy_path", "legacy/").rstrip("/")
    patterns = [re.compile(p) for p in migration.get("syntax_issue_patterns", [])]
    issues: list[str] = []
    for root, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS | {review_dir, legacy_dir}]
        root_path = Path(root)
        for filename in files:
            rel = (root_path / filename).relative_to(ROOT).as_posix()
            for pattern in patterns:
                if pattern.search(filename):
                    issues.append(f"SYNTAX ISSUE in filename: {rel}")
                    break
    return issues


def main() -> int:
    manifest = _load_manifest()
    violations = _required_path_violations(manifest)
    naming = _naming_issues()
    syntax = _syntax_filename_issues(manifest)
    forbidden = _forbidden_pattern_hits(manifest)
    issues = violations + naming + syntax + forbidden

    print("ARCHITECTURE_GUARD_REPO=" + str(manifest.get("repo_id", "unknown")))
    print("ARCHITECTURE_GUARD_ENFORCEMENT=" + str(manifest.get("enforcement", "warn")))
    print(f"ARCHITECTURE_GUARD_ISSUES={len(issues)}")
    for issue in issues:
        print(issue)

    if issues and manifest.get("enforcement") == "strict":
        print("ARCHITECTURE_GUARD=FAIL")
        return 1
    print("ARCHITECTURE_GUARD=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
