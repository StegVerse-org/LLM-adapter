#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "data" / "ecosystem-chat-service-adoption.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> None:
    data = json.loads(CONTRACT.read_text(encoding="utf-8"))
    require(data["schema"] == "stegverse.ecosystem_chat.service_sovereignty.v2", "schema mismatch")
    require(data["target_state"] == "ZERO_EXTERNAL_PLATFORM_DEPENDENCIES", "sovereign target missing")

    policy = data["policy"]
    require(policy["external_platform_dependency_allowed_at_completion"] is False, "external dependency allowed at completion")
    require(policy["temporary_external_platform_use_allowed_during_migration"] is True, "migration posture missing")
    require(policy["temporary_platform_must_have_absorption_plan"] is True, "absorption plan not required")
    require(policy["stegverse_must_own_runtime_control_plane"] is True, "runtime ownership missing")
    require(policy["stegverse_must_own_dns_and_routing_control_plane"] is True, "routing ownership missing")
    require(policy["stegverse_must_own_persistence_and_custody"] is True, "custody ownership missing")
    require(policy["stegverse_must_own_model_execution_or_federated_node_contract"] is True, "model sovereignty missing")
    require(policy["credentials_must_remain_out_of_repository"] is True, "credential boundary weakened")

    surfaces = data["temporary_transition_surfaces"]
    require(surfaces, "transition surface inventory missing")
    require(all(item["absorption_required"] is True for item in surfaces), "non-absorbed platform accepted")
    require(all(item.get("completion_condition") for item in surfaces), "platform completion condition missing")

    components = set(data["stegverse_replacement_components"])
    required_components = {
        "micro-node-runtime",
        "core-lite",
        "StegGuardian",
        "admissibility-gateway",
        "capability-registry",
        "TVC",
        "Master Records",
    }
    require(required_components.issubset(components), "replacement component inventory incomplete")

    units = data["activation_units"]
    require(units["stegverse_owned_compute_and_control_plane"] in {"MISSING", "PARTIAL", "COMPLETE"}, "compute ownership state invalid")
    require(units["external_platform_retirement"] in {"MISSING", "PARTIAL", "COMPLETE"}, "retirement state invalid")
    require(data["manual_user_action_required"] is False, "manual user task introduced")
    require(data["archive_directive_applies_to_this_goal"] is False, "archive directive leaked into active goal")
    print("PASS: Ecosystem Chat zero-external-dependency sovereignty contract")


if __name__ == "__main__":
    main()
