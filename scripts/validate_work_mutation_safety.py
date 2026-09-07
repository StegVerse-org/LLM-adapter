#!/usr/bin/env python3
"""Fail-closed structural safety gate for Work-authored functional mutations.

This validator grants no execution or governance authority. It prevents a pull
request from being considered structurally safe unless a fresh mutation manifest
covers the functional diff, resolves the canonical handoff/task/coordination
surfaces, records semantic-reuse discovery, and satisfies README completeness.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

SCHEMA = "stegverse.work-mutation-safety/v1"
ALLOWED_REUSE = {"REUSE", "EXTEND", "REFACTOR", "MOVE", "VERSION", "CREATE_NEW"}
DOCUMENTARY_SUFFIXES = {".md", ".txt", ".rst", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".pdf"}


def _git(*args: str) -> list[str]:
    return subprocess.check_output(["git", *args], text=True).splitlines()


def _functional(path: str) -> bool:
    if path.startswith("receipts/work-safety/"):
        return False
    return Path(path).suffix.lower() not in DOCUMENTARY_SUFFIXES


def _nonempty_list(value) -> bool:
    return isinstance(value, list) and any(str(item).strip() for item in value)


def _local_handoff_exists(repository: str, refs: list[str]) -> bool:
    for raw in refs:
        ref = str(raw).strip()
        if not ref:
            continue
        if ":" in ref:
            owner_repo, local = ref.split(":", 1)
            if owner_repo != repository:
                continue
        else:
            local = ref
        local = local.split("#", 1)[0]
        if local.endswith("_MIRROR_HANDOFF.md") and Path(local).is_file():
            return True
    return False


def validate_manifest(path: Path, *, repository: str, changed: set[str]) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != SCHEMA:
        raise ValueError(f"{path}: unsupported schema")
    if not str(data.get("task_id") or "").strip():
        raise ValueError(f"{path}: task_id required")
    if data.get("authority_effect") not in ("NONE", "NONE_PREFLIGHT_ONLY"):
        raise ValueError(f"{path}: authority_effect must remain NONE")

    handoffs = data.get("canonical_handoff_refs")
    if not _nonempty_list(handoffs) or not _local_handoff_exists(repository, handoffs):
        raise ValueError(f"{path}: at least one existing local *_MIRROR_HANDOFF.md is required")

    if not _nonempty_list(data.get("task_registry_refs")):
        raise ValueError(f"{path}: task_registry_refs required")

    master = data.get("master_records_review")
    if not isinstance(master, dict) or not isinstance(master.get("applicable"), bool):
        raise ValueError(f"{path}: master_records_review.applicable boolean required")
    if master["applicable"]:
        if not _nonempty_list(master.get("refs")):
            raise ValueError(f"{path}: applicable Master Records require refs")
    elif not str(master.get("reason") or "").strip():
        raise ValueError(f"{path}: non-applicable Master Records require reason")

    coordination = data.get("cross_task_coordination")
    if not isinstance(coordination, dict) or coordination.get("checked") is not True:
        raise ValueError(f"{path}: cross_task_coordination.checked=true required")
    if not _nonempty_list(coordination.get("refs")):
        raise ValueError(f"{path}: cross-task coordination refs required")

    semantic = data.get("semantic_scan")
    if not isinstance(semantic, dict) or semantic.get("completed") is not True:
        raise ValueError(f"{path}: semantic_scan.completed=true required")
    repos = semantic.get("repositories_searched")
    if not isinstance(repos, list) or repository not in repos:
        raise ValueError(f"{path}: semantic scan must include {repository}")
    if not _nonempty_list(semantic.get("evidence_refs")):
        raise ValueError(f"{path}: semantic scan evidence_refs required")

    decision = str(data.get("reuse_decision") or "")
    if decision not in ALLOWED_REUSE:
        raise ValueError(f"{path}: invalid reuse_decision")
    if data.get("existing_equivalent_found") is True and decision == "CREATE_NEW":
        raise ValueError(f"{path}: CREATE_NEW forbidden when an equivalent implementation was found")

    collision = data.get("active_owner_collision")
    if not isinstance(collision, dict) or collision.get("checked") is not True:
        raise ValueError(f"{path}: active_owner_collision.checked=true required")
    if not isinstance(collision.get("collision_found"), bool):
        raise ValueError(f"{path}: active_owner_collision.collision_found boolean required")
    if collision["collision_found"] and decision == "CREATE_NEW":
        if collision.get("intentional_parallel_versioning") is not True or not str(collision.get("reconciliation_ref") or "").strip():
            raise ValueError(f"{path}: CREATE_NEW blocked by active-owner collision")

    impact = data.get("readme_impact")
    if not isinstance(impact, dict) or not isinstance(impact.get("material_function_change"), bool):
        raise ValueError(f"{path}: readme_impact.material_function_change boolean required")
    if impact["material_function_change"]:
        readme_path = str(impact.get("readme_path") or "README.md")
        if impact.get("readme_updated_in_change_set") is not True or readme_path not in changed:
            raise ValueError(f"{path}: material functional change requires README update in same change set")
        if not _nonempty_list(impact.get("evidence_refs")):
            raise ValueError(f"{path}: material README decision requires evidence_refs")
    else:
        if not str(impact.get("no_readme_update_reason") or "").strip():
            raise ValueError(f"{path}: nonmaterial README determination requires reason")
        if not _nonempty_list(impact.get("evidence_refs")):
            raise ValueError(f"{path}: nonmaterial README determination requires evidence_refs")

    if not isinstance(data.get("covered_paths"), list):
        raise ValueError(f"{path}: covered_paths list required")
    new_files = data.get("new_files")
    if not isinstance(new_files, list):
        raise ValueError(f"{path}: new_files list required")
    for entry in new_files:
        if not isinstance(entry, dict):
            raise ValueError(f"{path}: each new_files entry must be an object")
        new_path = str(entry.get("path") or "")
        if not new_path:
            raise ValueError(f"{path}: new file path required")
        if not str(entry.get("semantic_responsibility") or "").strip():
            raise ValueError(f"{path}: semantic responsibility required for {new_path}")
        new_decision = str(entry.get("decision") or "")
        if new_decision not in ALLOWED_REUSE:
            raise ValueError(f"{path}: invalid new-file decision for {new_path}")
        if not str(entry.get("closest_existing_implementation") or "").strip():
            raise ValueError(f"{path}: closest existing implementation/search result required for {new_path}")
        if new_decision == "CREATE_NEW":
            if not str(entry.get("justification") or "").strip():
                raise ValueError(f"{path}: CREATE_NEW justification required for {new_path}")
            if not str(entry.get("canonical_owner") or "").strip():
                raise ValueError(f"{path}: CREATE_NEW canonical_owner required for {new_path}")
            if not _nonempty_list(entry.get("evidence_refs")):
                raise ValueError(f"{path}: CREATE_NEW evidence_refs required for {new_path}")
    return data


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--repository", required=True)
    args = parser.parse_args()

    changed = {p for p in _git("diff", "--name-only", args.base, args.head) if p}
    added = {p for p in _git("diff", "--name-only", "--diff-filter=A", args.base, args.head) if p}
    functional_changed = sorted(p for p in changed if _functional(p))
    functional_added = sorted(p for p in added if _functional(p))
    if not functional_changed:
        print("WORK_MUTATION_SAFETY_DOCUMENTATION_ONLY_PASS")
        return 0

    manifest_paths = sorted(
        p for p in changed if p.startswith("receipts/work-safety/") and p.endswith(".json")
    )
    if not manifest_paths:
        raise SystemExit("functional mutation requires a fresh receipts/work-safety/*.json manifest in the same change set")

    manifests = [
        validate_manifest(Path(p), repository=args.repository, changed=changed)
        for p in manifest_paths
    ]
    covered = {str(p) for m in manifests for p in m.get("covered_paths", [])}
    missing_coverage = [p for p in functional_changed if p not in covered]
    if missing_coverage:
        raise SystemExit("functional changed paths missing from fresh work-safety manifest: " + ", ".join(missing_coverage))

    declared_new = {
        str(entry.get("path"))
        for m in manifests
        for entry in m.get("new_files", [])
        if isinstance(entry, dict)
    }
    missing_new = [p for p in functional_added if p not in declared_new]
    if missing_new:
        raise SystemExit("new functional files missing semantic reuse decision: " + ", ".join(missing_new))

    print(json.dumps({
        "schema": "stegverse.work-mutation-safety-validation/v1",
        "repository": args.repository,
        "functional_changed_paths": functional_changed,
        "functional_added_paths": functional_added,
        "manifest_paths": manifest_paths,
        "decision": "PASS_STRUCTURAL_MUTATION_SAFETY",
        "authority_effect": "NONE",
        "runtime_authority": "NONE",
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
