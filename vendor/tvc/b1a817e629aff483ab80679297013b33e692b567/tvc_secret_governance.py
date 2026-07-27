"""
TVC portable governance core for secret-read requests.

This is server-free. It answers one question:

    "Is this role permitted to read these keys, from this repo/workflow/branch?"

using only the canonical governance definitions:

  - roles.yml     : role -> kv:read scopes (+ ttl)
  - issuers.yml   : OIDC binding repo/workflow/branch -> allowed roles

Secret VALUES never pass through here. Governance only.
Usage records (receipts) are emitted by the caller to TV, not here.
"""
from __future__ import annotations

import fnmatch
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import yaml  # PyYAML
except Exception:  # pragma: no cover
    yaml = None


DEFAULT_REQUIRED_BINDING_KEYS = ("org", "repo", "workflow", "branch")


def now_text() -> str:
    """Canonical TVC timestamp: UTC, second precision, trailing Z."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_json(data: Dict[str, Any]) -> str:
    raw = json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


class GovernanceError(Exception):
    """Raised when policy files are missing, malformed, or structurally invalid."""


def _load_yaml(path: Path) -> Dict[str, Any]:
    if yaml is None:
        raise GovernanceError("PyYAML is required to read governance policy files.")
    if not path.exists():
        raise GovernanceError(f"governance_file_missing:{path}")
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


@dataclass
class BindingResult:
    """OIDC binding evaluation result. Does not contain secret values."""

    matched: bool
    reason: str
    binding_index: Optional[int] = None
    partial_match_allowed: bool = False


@dataclass
class GovernanceDecision:
    admissible: bool
    role: str
    requested_keys: List[str]
    allowed_keys: List[str]
    denied_keys: List[str]
    ttl_minutes: Optional[int]
    binding_matched: bool
    decision_id: str
    reasons: List[str] = field(default_factory=list)

    def to_receipt(self, *, policy_dir: Path, source: str) -> Dict[str, Any]:
        """A usage-governance record (no values) suitable for TV's chainlog."""
        body = {
            "schema": {"name": "stegverse.tv.secret_read_decision", "version": "0.2.0"},
            "ts": now_text(),
            "event": "secret_read",
            "decision_id": self.decision_id,
            "role": self.role,
            "admissible": self.admissible,
            "requested_keys": sorted(self.requested_keys),
            "allowed_keys": sorted(self.allowed_keys),
            "denied_keys": sorted(self.denied_keys),
            "binding_matched": self.binding_matched,
            "value_source": source,
            "reasons": self.reasons,
            "policy_hash": policy_hash(policy_dir),
        }
        body["receipt_hash"] = sha256_json(body)
        return body


def policy_hash(policy_dir: Path) -> str:
    """Hash the governing policy set so a receipt proves which policy applied."""
    parts: Dict[str, Any] = {}
    for name in ("roles.yml", "issuers.yml", "warrant_issuers.yml"):
        p = policy_dir / name
        if p.exists():
            parts[name] = hashlib.sha256(p.read_bytes()).hexdigest()
    return sha256_json(parts)


def _scope_for_role(roles_doc: Dict[str, Any], role: str) -> Tuple[List[str], Optional[int]]:
    roles = (roles_doc or {}).get("roles", {})
    if role not in roles:
        raise GovernanceError(f"unknown_role:{role}")
    spec = roles[role] or {}
    perms = (spec.get("permissions") or {}).get("kv:read", []) or []
    ttl = spec.get("ttl_minutes")
    return list(perms), ttl


def _binding_allows(
    issuers_doc: Dict[str, Any],
    role: str,
    ctx: Dict[str, str],
    *,
    required_match_keys: Tuple[str, ...] = DEFAULT_REQUIRED_BINDING_KEYS,
) -> BindingResult:
    """
    issuers.yml binds OIDC subject context to allowed roles.

    Strict default: each production binding must match org, repo, workflow, and branch.
    A policy may intentionally allow narrower bindings by setting:

        allow_partial_match: true

    on that specific binding. Empty match blocks are never admissible.
    """
    gh = (issuers_doc or {}).get("github_oidc", {})
    bindings = gh.get("bindings", []) or []
    if not ctx:
        return BindingResult(False, "oidc_context_missing")

    for idx, binding in enumerate(bindings):
        match = binding.get("match", {}) or {}
        allow_partial = bool(binding.get("allow_partial_match", False))

        if not match:
            continue

        missing_required = [key for key in required_match_keys if key not in match]
        if missing_required and not allow_partial:
            continue

        if all(str(expected) == str(ctx.get(key, "")) for key, expected in match.items()):
            if role in (binding.get("allow_roles", []) or []):
                return BindingResult(True, "ok", idx, allow_partial)
            return BindingResult(False, "role_not_allowed_by_binding", idx, allow_partial)

    return BindingResult(False, "oidc_binding_unmatched")


def _key_allowed(requested: str, patterns: List[str]) -> bool:
    """Supports exact keys and glob scopes like "osint/*"."""
    return any(fnmatch.fnmatch(requested, pat) for pat in patterns)


def _decision_id_payload(
    *,
    role: str,
    requested_keys: List[str],
    allowed_keys: List[str],
    denied_keys: List[str],
    binding_matched: bool,
    policy_dir: Path,
) -> Dict[str, Any]:
    return {
        "schema": {"name": "stegverse.tvc.secret_read_decision_id", "version": "0.1.0"},
        "role": role,
        "requested_keys": sorted(requested_keys),
        "allowed_keys": sorted(allowed_keys),
        "denied_keys": sorted(denied_keys),
        "binding_matched": binding_matched,
        "policy_hash": policy_hash(policy_dir),
    }


def evaluate(
    *,
    role: str,
    requested_keys: List[str],
    policy_dir: Path,
    oidc_ctx: Optional[Dict[str, str]] = None,
    require_binding: bool = True,
    required_match_keys: Tuple[str, ...] = DEFAULT_REQUIRED_BINDING_KEYS,
) -> GovernanceDecision:
    """
    Core admissibility check. Returns a decision; raises GovernanceError only for
    structural problems (missing files, unknown role), not for ordinary denials.
    """
    roles_doc = _load_yaml(policy_dir / "roles.yml")
    issuers_doc = _load_yaml(policy_dir / "issuers.yml") if (policy_dir / "issuers.yml").exists() else {}

    scopes, ttl = _scope_for_role(roles_doc, role)

    allowed, denied = [], []
    for key in requested_keys:
        (allowed if _key_allowed(key, scopes) else denied).append(key)

    binding = _binding_allows(
        issuers_doc,
        role,
        oidc_ctx or {},
        required_match_keys=required_match_keys,
    )

    reasons: List[str] = []
    admissible = True
    if denied:
        admissible = False
        reasons.append(f"keys_out_of_scope:{','.join(sorted(denied))}")
    if require_binding and not binding.matched:
        admissible = False
        reasons.append(binding.reason)
    if admissible:
        reasons.append("ok")

    decision_payload = _decision_id_payload(
        role=role,
        requested_keys=requested_keys,
        allowed_keys=allowed,
        denied_keys=denied,
        binding_matched=binding.matched,
        policy_dir=policy_dir,
    )

    return GovernanceDecision(
        admissible=admissible,
        role=role,
        requested_keys=list(requested_keys),
        allowed_keys=allowed,
        denied_keys=denied,
        ttl_minutes=ttl,
        binding_matched=binding.matched,
        decision_id=sha256_json(decision_payload),
        reasons=reasons,
    )