import json
from pathlib import Path

from llm_adapter.system_boundary_lifecycle import bind_system_boundary_to_lifecycle
from llm_adapter.system_boundary_receipt import verify_system_boundary_receipt


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures/adapter_system_boundary_sdk_packet.v0.1.json"


def _base_packet():
    return {
        "provider_request": {"provider": "fixture", "model": "fixture", "messages": []},
        "provider_request_hash": "request-hash",
        "provider_response": {
            "provider": "fixture",
            "model": "fixture",
            "output": "read only output",
            "request_hash": "request-hash",
            "response_hash": "response-hash",
        },
        "continuity": {"freshness_status": "current", "evidence": []},
        "adapter_result": {
            "decision": "ALLOW",
            "admissibility_status": "allowed_read_only_candidate",
            "reconstruction": {"decision": "ALLOW"},
        },
        "action_route": {"route_status": "no_action_route_required", "action_candidates": []},
        "commitment_request": {"status": "no_commitment_request_required"},
        "authority_decision": {"decision": "NOT_REQUIRED", "authority_decision_hash": "authority-hash"},
        "execution_handoff": {"status": "not_executable", "execution_handoff_hash": "handoff-hash"},
        "transition_id": "transition-sbd-001",
        "run_id": "run-sbd-001",
        "receipt_id": "receipt://adapter/001",
    }


def test_fixture_is_exact_adapter_lifecycle_output():
    expected = json.loads(FIXTURE.read_text(encoding="utf-8"))
    observed = bind_system_boundary_to_lifecycle(
        _base_packet(),
        session_id="sdk-roundtrip-001",
        transition_id="transition-sbd-001",
        run_id="run-sbd-001",
        generated_at="2026-07-14T15:00:00Z",
        source_commit="adapter-fixture-v1",
    )

    assert observed == expected
    assert verify_system_boundary_receipt(
        observed["system_boundary_declaration"],
        observed["system_boundary_declaration_receipt"],
    )
    assert observed["system_boundary_declaration_ref"]["authorizing"] is False
    assert observed["system_boundary_declaration_ref"]["custody_transferred"] is False
    assert observed["system_boundary_declaration_ref"]["admissibility_determined"] is False
    assert observed["system_boundary_declaration_ref"]["production_binding_enabled"] is False
