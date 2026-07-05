"""Side-effect-free free-tier quota evaluator for StegVerse AI Entry.

The evaluator does not persist counters, call providers, read credentials, or mutate
receipts. It only evaluates a supplied usage snapshot against a supplied policy.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


DEFAULT_FREE_TIER_POLICY: dict[str, Any] = {
    "tier": "free",
    "governed_inquiries_per_day": 5,
    "trial_governed_inquiries_total": 25,
    "receipt_exports_per_day": 1,
    "replays_per_day": 1,
    "reconstruction_scope": "recent_session_limited",
    "private_connectors_enabled": False,
    "sample_connectors_enabled": True,
    "premium_models_enabled": False,
    "byo_provider_key": "allowed_if_separately_governed",
}


@dataclass(frozen=True)
class FreeTierUsage:
    """Caller-supplied usage counters for a single quota evaluation."""

    governed_inquiries_today: int = 0
    trial_governed_inquiries_total: int = 0
    receipt_exports_today: int = 0
    replays_today: int = 0
    wants_private_connector: bool = False
    wants_premium_model: bool = False
    wants_full_evidence_bundle_retention: bool = False
    wants_exportable_audit_packet: bool = False
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class FreeTierQuotaDecision:
    """Deterministic quota decision returned to the adapter boundary."""

    status: str
    tier: str
    allowed: bool
    reasons: tuple[str, ...]
    upgrade_triggers: tuple[str, ...]
    remaining: Mapping[str, int]
    non_claims: Mapping[str, bool]

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "tier": self.tier,
            "allowed": self.allowed,
            "reasons": list(self.reasons),
            "upgrade_triggers": list(self.upgrade_triggers),
            "remaining": dict(self.remaining),
            "non_claims": dict(self.non_claims),
        }


def _int_policy(policy: Mapping[str, Any], key: str, fallback: int) -> int:
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


def evaluate_free_tier_quota(
    usage: FreeTierUsage,
    policy: Mapping[str, Any] | None = None,
) -> FreeTierQuotaDecision:
    """Evaluate a supplied free-tier usage snapshot.

    The result is intentionally non-authorizing. An ``ALLOW`` here means the
    request is within product quota only; it does not grant admissibility,
    execution authority, provider authority, or commit-time standing.
    """

    active_policy: Mapping[str, Any] = policy or DEFAULT_FREE_TIER_POLICY
    tier = str(active_policy.get("tier", "free"))

    inquiry_daily_limit = _int_policy(active_policy, "governed_inquiries_per_day", 5)
    trial_total_limit = _int_policy(active_policy, "trial_governed_inquiries_total", 25)
    receipt_export_limit = _int_policy(active_policy, "receipt_exports_per_day", 1)
    replay_limit = _int_policy(active_policy, "replays_per_day", 1)

    remaining = {
        "governed_inquiries_today": _remaining(
            inquiry_daily_limit, usage.governed_inquiries_today
        ),
        "trial_governed_inquiries_total": _remaining(
            trial_total_limit, usage.trial_governed_inquiries_total
        ),
        "receipt_exports_today": _remaining(
            receipt_export_limit, usage.receipt_exports_today
        ),
        "replays_today": _remaining(replay_limit, usage.replays_today),
    }

    reasons: list[str] = []
    upgrade_triggers: list[str] = []

    if usage.governed_inquiries_today >= inquiry_daily_limit:
        reasons.append("daily_governed_inquiry_quota_exhausted")
        upgrade_triggers.append("quota_needed")
    if usage.trial_governed_inquiries_total >= trial_total_limit:
        reasons.append("trial_governed_inquiry_quota_exhausted")
        upgrade_triggers.append("quota_needed")
    if usage.receipt_exports_today >= receipt_export_limit:
        reasons.append("receipt_export_quota_exhausted")
        upgrade_triggers.append("longer_retention_or_export_needed")
    if usage.replays_today >= replay_limit:
        reasons.append("replay_quota_exhausted")
        upgrade_triggers.append("deeper_replay_needed")
    if usage.wants_private_connector:
        reasons.append("private_connectors_disabled_on_free_tier")
        upgrade_triggers.append("private_connector_needed")
    if usage.wants_premium_model:
        reasons.append("premium_models_disabled_on_free_tier")
        upgrade_triggers.append("premium_model_needed")
    if usage.wants_full_evidence_bundle_retention:
        reasons.append("full_evidence_bundle_retention_disabled_on_free_tier")
        upgrade_triggers.append("longer_retention_needed")
    if usage.wants_exportable_audit_packet:
        reasons.append("exportable_audit_packet_disabled_on_free_tier")
        upgrade_triggers.append("audit_packet_needed")

    allowed = not reasons
    return FreeTierQuotaDecision(
        status="ALLOW_QUOTA" if allowed else "DENY_QUOTA",
        tier=tier,
        allowed=allowed,
        reasons=tuple(reasons),
        upgrade_triggers=tuple(dict.fromkeys(upgrade_triggers)),
        remaining=remaining,
        non_claims={
            "quota_allow_is_admissibility": False,
            "quota_allow_is_execution_authority": False,
            "provider_response_is_authority": False,
            "upgrade_changes_admissibility_requirements": False,
        },
    )
