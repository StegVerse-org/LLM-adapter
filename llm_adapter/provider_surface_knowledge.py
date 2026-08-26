"""Fail-closed resolver for canonical KV provider/access-surface capability facts."""
from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
from typing import Any, Mapping

REGISTRY_ENV = "STEGVERSE_KV_PROVIDER_SURFACE_REGISTRY"
SCHEMA = "stegverse.kv.provider-surface-capability-registry/v1"
PROVIDER_ALIASES = {
    "icloud": "icloud",
    "google drive": "google_drive",
    "drive": "google_drive",
    "onedrive": "microsoft_onedrive",
    "one drive": "microsoft_onedrive",
    "microsoft": "microsoft_onedrive",
    "aws": "aws_object_storage",
    "s3": "aws_object_storage",
    "self hosted": "self_hosted_private_cloud",
    "private cloud": "self_hosted_private_cloud",
    "stegcloud": "stegcloud",
}
SURFACE_ALIASES = {
    "safari": "browser", "chrome": "browser", "firefox": "browser", "edge": "browser",
    "browser": "browser", "native app": "native_provider_app", "app": "native_provider_app",
    "files": "os_file_provider", "file provider": "os_file_provider",
    "api": "direct_api", "sync client": "sync_client", "stegverse native": "stegverse_native",
}
DEVICE_TERMS = ("iphone","ipad","mac","windows","android","linux","node")
QUESTION_TERMS = ("why","issue","problem","slow","slower","offline","sync","background","browser","app","native","files","drive","icloud","onedrive","aws","stegcloud")

class ProviderSurfaceKnowledgeError(ValueError):
    pass

@dataclass(frozen=True)
class ProviderSurfaceAnswer:
    answer: str
    source_ref: str
    match_state: str

def _norm(text: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text.lower()).split())

def looks_like_provider_surface_question(question: str) -> bool:
    n = _norm(question)
    return any(term in n for term in QUESTION_TERMS) and any(alias in n for alias in PROVIDER_ALIASES)

def load_registry(path: str | Path | None = None) -> Mapping[str, Any]:
    selected = Path(path or os.environ.get(REGISTRY_ENV, ""))
    if not str(selected):
        raise ProviderSurfaceKnowledgeError("canonical_provider_surface_registry_not_mounted")
    try:
        data = json.loads(selected.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ProviderSurfaceKnowledgeError(f"canonical_provider_surface_registry_unavailable:{exc}") from exc
    except json.JSONDecodeError as exc:
        raise ProviderSurfaceKnowledgeError("canonical_provider_surface_registry_invalid_json") from exc
    if data.get("schema") != SCHEMA or data.get("authority_effect") != "NONE":
        raise ProviderSurfaceKnowledgeError("canonical_provider_surface_registry_invalid_boundary")
    if not isinstance(data.get("observations"), list):
        raise ProviderSurfaceKnowledgeError("canonical_provider_surface_registry_observations_invalid")
    return data

def resolve_provider_surface_question(question: str, *, path: str | Path | None = None) -> ProviderSurfaceAnswer | None:
    if not looks_like_provider_surface_question(question):
        return None
    n = _norm(question)
    provider = next((canonical for alias, canonical in PROVIDER_ALIASES.items() if alias in n), None)
    surface = next((canonical for alias, canonical in SURFACE_ALIASES.items() if alias in n), None)
    device = next((term for term in DEVICE_TERMS if term in n), None)
    data = load_registry(path)
    matches = []
    for obs in data["observations"]:
        if provider and obs.get("provider") != provider:
            continue
        if surface and obs.get("access_surface") != surface:
            continue
        hay = _norm(f"{obs.get('device_class','')} {obs.get('platform','')}")
        if device and device not in hay:
            continue
        matches.append(obs)
    source = "StegVerse-Labs/continuity-vault-kit/specs/kv-provider-surface-capability-registry.v1.json"
    if not matches:
        return ProviderSurfaceAnswer(
            answer="StegVerse has no admitted provider/device/platform/access-surface observation for that combination yet. I will not infer the behavior from model memory or provider marketing.",
            source_ref=source,
            match_state="UNKNOWN_UNVERIFIED",
        )
    obs = matches[0]
    limitations = "; ".join(obs.get("limitations", [])) or "No specific limitation is recorded."
    answer = (
        f"Canonical capability state: {obs.get('knowledge_state')}. "
        f"Preferred route: {obs.get('preferred_route') or 'not established'}. "
        f"Fallback route: {obs.get('fallback_route') or 'not established'}. "
        f"Recorded limitations: {limitations}"
    )
    return ProviderSurfaceAnswer(answer=answer, source_ref=source, match_state=str(obs.get("knowledge_state")))

__all__ = ["ProviderSurfaceAnswer","ProviderSurfaceKnowledgeError","load_registry","looks_like_provider_surface_question","resolve_provider_surface_question"]
