"""Resolve StegVerse capabilities without binding them to one OS or runtime platform."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import os
import platform
import shutil
import sys
from typing import Mapping


@dataclass(frozen=True)
class RuntimeProfile:
    os: str
    architecture: str
    python: str
    process_available: bool
    container_available: bool
    wasm_available: bool
    browser_available: bool
    peer_available: bool


@dataclass(frozen=True)
class BackendResolution:
    backend: str
    reason: str
    profile: RuntimeProfile
    manual_action_required: bool = False

    def to_dict(self) -> dict[str, object]:
        value = asdict(self)
        value["profile"] = asdict(self.profile)
        return value


def detect_runtime_profile(env: Mapping[str, str] | None = None) -> RuntimeProfile:
    values = dict(os.environ if env is None else env)
    return RuntimeProfile(
        os=platform.system().lower() or "unknown",
        architecture=platform.machine().lower() or "unknown",
        python=sys.executable,
        process_available=bool(sys.executable),
        container_available=bool(shutil.which("docker") or shutil.which("podman")),
        wasm_available=bool(shutil.which("wasmtime") or shutil.which("wasmer")),
        browser_available=values.get("STEGVERSE_BROWSER_EXECUTOR_AVAILABLE", "false").lower() == "true",
        peer_available=bool(values.get("STEGVERSE_PEER_EXECUTOR_ENDPOINT")),
    )


def resolve_backend(
    supported: list[str],
    preferred: str | None = None,
    env: Mapping[str, str] | None = None,
) -> BackendResolution:
    profile = detect_runtime_profile(env)
    availability = {
        "process": profile.process_available,
        "wasm": profile.wasm_available,
        "container": profile.container_available,
        "browser": profile.browser_available,
        "peer": profile.peer_available,
    }
    order: list[str] = []
    if preferred:
        order.append(preferred)
    order.extend(name for name in supported if name not in order)
    for backend in order:
        if backend not in supported:
            continue
        if availability.get(backend, False):
            return BackendResolution(
                backend=backend,
                reason=f"selected available {backend} executor from capability declaration",
                profile=profile,
            )
    raise RuntimeError(
        "no admissible execution backend is available; capability remains unconstructed"
    )
