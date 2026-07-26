import json
from pathlib import Path

from scripts.validate_stack_conformance import validate_manifest, validate_registry

ROOT = Path(__file__).resolve().parents[1]


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_canonical_manifest_and_registry_pass():
    manifest = load("stegverse.component.json")
    registry = load("registry/components.json")
    assert validate_manifest(manifest) == []
    assert validate_registry(registry, manifest) == []


def test_authority_overlap_fails_closed():
    manifest = load("stegverse.component.json")
    manifest["authority"]["owns"].append("execution")
    errors = validate_manifest(manifest)
    assert any("owns/excludes overlap" in error for error in errors)


def test_duplicate_component_id_is_rejected():
    manifest = load("stegverse.component.json")
    registry = load("registry/components.json")
    registry["components"].append(dict(registry["components"][0]))
    errors = validate_registry(registry, manifest)
    assert any("duplicate component IDs" in error for error in errors)


def test_registry_and_local_authority_must_match():
    manifest = load("stegverse.component.json")
    registry = load("registry/components.json")
    manifest["authority"]["owns"] = ["provider_brokerage"]
    errors = validate_registry(registry, manifest)
    assert "local manifest authority.owns does not match registry" in errors
