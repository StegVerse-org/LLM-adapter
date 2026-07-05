"""Free-tier receipt export and replay/reconstruction limit contracts.

These evaluators are side-effect free. They evaluate supplied usage snapshots
against policy limits and do not persist counters, export receipts, replay data,
call providers, or reconstruct sessions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


DEFAULT_FREE_TIER_LIMIT_POLICY: dict[str, Any] = {
    "tier": "free",
    "receipt_exports_per_day": 1,
    "replays_per_day": 1,
    "reconstructions_per_day": 1,
    "reconstruction_scope": "recent_session_limited",
    "full_evidence_bundle_retention_enabled": False,
    "exportable_audit_packet_enabled": False,
    "cross_session_reconstruction_enabled": False,
}


@dataclass(frozen=True)
class ReceiptReplayUsage:
    """Caller-supplied receipt/replay counters and requested scope."""

    receipt_exports_today: int = 0
    replays_today: int = 0
    reconstructions_today: int = 0
    wants_full_evidence_bundle: bool = False
    wants_exportable_audit_packet: bool = False
    wants_cross_session_reconstruction: bool = False
    wants_long_term_retention: bool = False


@dataclass(frozen=True)
class LimitDecision:
    """Deterministic product-limit decision for non-authorizing free-tier actions."""

    status: str
    tier: str
    allowed: bool
    reasons: tuple[str, ...]
    upgrade_triggers: tuple[str, ...]
    remaining: Mapping[str, int]
    scope: Mapping[str, Any]
    non_claims: Mapping[str, bool]

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "tier": self.tier,
            "allowed": self.allowed,
            "reasons": list(self.reasons),
            "upgrade_triggers": list(self.upgrade_triggers),
            "remaining": dict(self.remaining),
            "scope": dict(self.scope),
            "non_claims": dict(self.non_claims),
        }


def _limit(policy: Mapping[str, Any], key: str, fallback: int) -> int:
    value = policy.get(key, fallback)
    if isinstance(value, bool):
        return fallback
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return fallback
    return max(parsed, 0)


def _remaining(limit: int, used: int) -> int:
    return max(limit - max(used, 0), 0)


def evaluate_receipt_replay_limits(
    usage: ReceiptReplayUsage,
    policy: Mapping[str, Any] | None = None,
) -> LimitDecision:
    """Evaluate free-tier receipt export, replay, and reconstruction limits.

    ``ALLOW_LIMIT`` means the request is inside product boundaries only. It does
    not authorize the receipt export itself, does not validate evidence, and does
    not establish commit-time standing.
    """

    active_policy = policy or DEFAULT_FREE_TIER_LIMIT_POLICY
    tier = str(active_policy.get("tier", "free"))

    receipt_limit = _limit(active_policy, "receipt_exports_per_day", 1)
    replay_limit = _limit(active_policy, "replays_per_day", 1)
    reconstruction_limit = _limit(active_policy, "reconstructions_per_day", 1)

    remaining = {
        "receipt_exports_today": _remaining(receipt_limit, usage.receipt_exports_today),
        "replays_today": _remaining(replay_limit, usage.replays_today),
        "reconstructions_today": _remaining(
            reconstruction_limit, usage.reconstructions_today
        ),
    }

    reasons: list[str] = []
    upgrade_triggers: list[str] = []

    if usage.receipt_exports_today >= receipt_limit:
        reasons.append("receipt_export_limit_exhausted")
        upgrade_triggers.append("receipt_export_capacity_needed")
    if usage.replays_today >= replay_limit:
        reasons.append("replay_limit_exhausted")
        upgrade_triggers.append("deeper_replay_needed")
    if usage.reconstructions_today >= reconstruction_limit:
        reasons.append("reconstruction_limit_exhausted")
        upgrade_triggers.append("deeper_reconstruction_needed")
    if usage.wants_full_evidence_bundle:
        reasons.append("full_evidence_bundle_disabled_on_free_tier")
        upgrade_triggers.append("evidence_bundle_retention_needed")
    if usage.wants_exportable_audit_packet:
        reasons.append("exportable_audit_packet_disabled_on_free_tier")
        upgrade_triggers.append("audit_packet_needed")
    if usage.wants_cross_session_reconstruction:
        reasons.append("cross_session_reconstruction_disabled_on_free_tier")
        upgrade_triggers.append("cross_session_reconstruction_needed")
    if usage.wants_long_term_retention:
        reasons.append("long_term_retention_disabled_on_free_tier")
        upgrade_triggers.append("longer_retention_needed")

    allowed = not reasons
    return LimitDecision(
        status="ALLOW_LIMIT" if allowed else "DENY_LIMIT",
        tier=tier,
        allowed=allowed,
        reasons=tuple(reasons),
        upgrade_triggers=tuple(dict.fromkeys(upgrade_triggers)),
        remaining=remaining,
        scope={
            "reconstruction_scope": active_policy.get(
                "reconstruction_scope", "recent_session_limited"
            ),
            "full_evidence_bundle_retention_enabled": bool(
                active_policy.get("full_evidence_bundle_retention_enabled", False)
            ),
            "exportable_audit_packet_enabled": bool(
                active_policy.get("exportable_audit_packet_enabled", False)
            ),
            "cross_session_reconstruction_enabled": bool(
                active_policy.get("cross_session_reconstruction_enabled", False)
            ),
        },
        non_claims={
            "limit_allow_is_admissibility": False,
            "limit_allow_is_execution_authority": False,
            "replay_grants_commit_time_standing": False,
            "reconstruction_grants_commit_time_standing": False,
            "receipt_export_is_permanent_retention": False,
        },
    )
