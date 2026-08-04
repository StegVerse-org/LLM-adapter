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
    require(data["schema"] == "stegverse.ecosystem_chat.service_adoption.v1", "schema mismatch")
    policy = data["policy"]
    require(policy["unnamed_third_party_dependency_allowed"] is False, "unnamed third-party dependency enabled")
    require(policy["dependency_must_be_eliminated_or_adopted"] is True, "eliminate-or-adopt policy missing")
    require(policy["provider_must_be_replaceable"] is True, "provider replacement boundary missing")
    require(policy["credentials_must_remain_out_of_repository"] is True, "credential boundary weakened")

    services = {entry["role"]: entry for entry in data["services"]}
    required_roles = {
        "public_gateway",
        "persistent_hil_receiver",
        "admission_service",
        "provider",
        "master_records_custody",
    }
    require(required_roles == set(services), "service role inventory mismatch")
    require(services["public_gateway"]["runtime_state"] == "LIVE_HEALTH_VERIFIED", "gateway not live")
    require(services["provider"]["adoption_state"] == "INTERFACE_IMPLEMENTED_PROVIDER_UNBOUND", "provider posture mismatch")
    require(services["master_records_custody"]["adoption_state"] == "INTERFACE_IMPLEMENTED_ENDPOINT_UNBOUND", "custody posture mismatch")
    require(data["manual_user_action_required"] is False, "manual user task introduced")
    require(data["archive_directive_applies_to_this_goal"] is False, "archive directive leaked into active goal")
    print("PASS: Ecosystem Chat service adoption contract")


if __name__ == "__main__":
    main()
