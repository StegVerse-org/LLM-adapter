#!/usr/bin/env python3
"""Validate the canonical StegVerse LLM Communications Stack contract.

Uses only the Python standard library so it can run in constrained CI and
portable ecosystem nodes without dependency installation.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

STACK_ID = "STEGVERSE-LLM-COMMS-STACK-v1"
COMPONENT_ID = re.compile(r"^[a-z0-9][a-z0-9-]*$")
REPOSITORY = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
REQUIRED_MANIFEST_FIELDS = {
    "schema_version",
    "stack_id",
    "component_id",
    "repository",
    "role",
    "deployment_posture",
    "consumes",
    "produces",
    "authority",
}


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: {exc}") from exc


def require_string_list(value: Any, field: str, errors: list[str]) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        errors.append(f"{field} must be an array of non-empty strings")
        return []
    if len(value) != len(set(value)):
        errors.append(f"{field} contains duplicate values")
    return value


def validate_manifest(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing = sorted(REQUIRED_MANIFEST_FIELDS - manifest.keys())
    if missing:
        errors.append(f"manifest missing required fields: {', '.join(missing)}")

    if manifest.get("schema_version") != "1.0.0":
        errors.append("manifest schema_version must be 1.0.0")
    if manifest.get("stack_id") != STACK_ID:
        errors.append(f"manifest stack_id must be {STACK_ID}")

    component_id = manifest.get("component_id")
    if not isinstance(component_id, str) or not COMPONENT_ID.fullmatch(component_id):
        errors.append("manifest component_id is invalid")

    repository = manifest.get("repository")
    if not isinstance(repository, str) or not REPOSITORY.fullmatch(repository):
        errors.append("manifest repository must use owner/name form")

    if not isinstance(manifest.get("role"), str) or len(manifest.get("role", "")) < 3:
        errors.append("manifest role must be a non-empty bounded role")

    require_string_list(manifest.get("deployment_posture"), "deployment_posture", errors)
    require_string_list(manifest.get("consumes"), "consumes", errors)
    require_string_list(manifest.get("produces"), "produces", errors)
    require_string_list(manifest.get("upstream", []), "upstream", errors)
    require_string_list(manifest.get("downstream", []), "downstream", errors)

    authority = manifest.get("authority")
    if not isinstance(authority, dict):
        errors.append("authority must be an object")
    else:
        owns = set(require_string_list(authority.get("owns"), "authority.owns", errors))
        excludes = set(require_string_list(authority.get("excludes"), "authority.excludes", errors))
        overlap = sorted(owns & excludes)
        if overlap:
            errors.append(f"authority owns/excludes overlap: {', '.join(overlap)}")

    return errors


def validate_registry(registry: dict[str, Any], manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if registry.get("schema_version") != "1.0.0":
        errors.append("registry schema_version must be 1.0.0")
    if registry.get("stack_id") != STACK_ID:
        errors.append(f"registry stack_id must be {STACK_ID}")

    required = require_string_list(registry.get("required_components"), "required_components", errors)
    components = registry.get("components")
    if not isinstance(components, list):
        return errors + ["registry components must be an array"]

    ids: list[str] = []
    repositories: list[str] = []
    ownership: dict[str, list[str]] = {}
    by_id: dict[str, dict[str, Any]] = {}

    for index, component in enumerate(components):
        if not isinstance(component, dict):
            errors.append(f"components[{index}] must be an object")
            continue
        component_id = component.get("component_id")
        repository = component.get("repository")
        if not isinstance(component_id, str) or not COMPONENT_ID.fullmatch(component_id):
            errors.append(f"components[{index}].component_id is invalid")
            continue
        if not isinstance(repository, str) or not REPOSITORY.fullmatch(repository):
            errors.append(f"components[{index}].repository is invalid")
        ids.append(component_id)
        repositories.append(repository)
        by_id[component_id] = component
        for authority in require_string_list(component.get("owns"), f"components[{index}].owns", errors):
            ownership.setdefault(authority, []).append(component_id)
        require_string_list(component.get("excludes"), f"components[{index}].excludes", errors)

    duplicate_ids = sorted({item for item in ids if ids.count(item) > 1})
    if duplicate_ids:
        errors.append(f"duplicate component IDs: {', '.join(duplicate_ids)}")
    duplicate_repositories = sorted({item for item in repositories if repositories.count(item) > 1})
    if duplicate_repositories:
        errors.append(f"duplicate repositories: {', '.join(duplicate_repositories)}")

    missing = sorted(set(required) - set(ids))
    if missing:
        errors.append(f"required components missing from registry: {', '.join(missing)}")

    exclusive = set(require_string_list(registry.get("exclusive_authorities"), "exclusive_authorities", errors))
    for authority in sorted(exclusive):
        owners = ownership.get(authority, [])
        if len(owners) > 1:
            errors.append(f"exclusive authority {authority} has multiple owners: {', '.join(owners)}")

    manifest_id = manifest.get("component_id")
    registered = by_id.get(manifest_id)
    if registered is None:
        errors.append(f"local component {manifest_id!r} is not registered")
    else:
        for field in ("repository", "role"):
            if registered.get(field) != manifest.get(field):
                errors.append(f"local manifest {field} does not match registry")
        manifest_owns = set(manifest.get("authority", {}).get("owns", []))
        registry_owns = set(registered.get("owns", []))
        if manifest_owns != registry_owns:
            errors.append("local manifest authority.owns does not match registry")
        manifest_excludes = set(manifest.get("authority", {}).get("excludes", []))
        registry_excludes = set(registered.get("excludes", []))
        if manifest_excludes != registry_excludes:
            errors.append("local manifest authority.excludes does not match registry")

    known_ids = set(ids)
    for relation in ("upstream", "downstream"):
        unknown = sorted(set(manifest.get(relation, [])) - known_ids - {"stegverse-sdk", "continuity", "master-records"})
        if unknown:
            errors.append(f"manifest {relation} references unknown components: {', '.join(unknown)}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="stegverse.component.json")
    parser.add_argument("--registry", default="registry/components.json")
    parser.add_argument("--report", default=None)
    args = parser.parse_args()

    try:
        manifest = load_json(Path(args.manifest))
        registry = load_json(Path(args.registry))
        if not isinstance(manifest, dict) or not isinstance(registry, dict):
            raise ValueError("manifest and registry roots must be objects")
        errors = validate_manifest(manifest) + validate_registry(registry, manifest)
    except ValueError as exc:
        errors = [str(exc)]

    result = {
        "stack_id": STACK_ID,
        "status": "PASS" if not errors else "FAIL",
        "error_count": len(errors),
        "errors": errors,
    }
    rendered = json.dumps(result, indent=2, sort_keys=True)
    print(rendered)
    if args.report:
        Path(args.report).write_text(rendered + "\n", encoding="utf-8")
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
