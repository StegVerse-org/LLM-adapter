import hashlib
import json

from fastapi.testclient import TestClient

from llm_adapter.combined_gateway import app


def _digest(payload: dict) -> str:
    material = dict(payload)
    material.pop("advertisement_sha256", None)
    return hashlib.sha256(
        json.dumps(material, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def test_node_advertisement_is_health_bound_and_non_authorizing(monkeypatch) -> None:
    monkeypatch.setenv("STEGVERSE_NODE_ID", "test-portable-node")
    monkeypatch.setenv("STEGVERSE_PROVIDER_ENABLED", "true")
    monkeypatch.setenv("STEGVERSE_STORAGE_DURABLE_ACROSS_RESTARTS", "true")
    monkeypatch.setenv("STEGVERSE_MASTER_RECORDS_ENDPOINT", "https://master-records.example")
    monkeypatch.setenv("STEGVERSE_MASTER_RECORDS_TOKEN", "server-only-token")
    monkeypatch.setenv("STEGVERSE_MASTER_RECORDS_ALLOWED_HOSTS", "master-records.example")

    response = TestClient(app).get("/api/stegverse-node")

    assert response.status_code == 200
    payload = response.json()
    assert payload["schema"] == "stegverse.node.endpoint-advertisement.v1"
    assert payload["node_id"] == "test-portable-node"
    assert payload["capability_id"] == "ecosystem-chat-gateway"
    assert payload["endpoint"].endswith("/api/ecosystem-chat")
    assert payload["health_endpoint"].endswith("/health")
    assert payload["stegbrowser_master_records_state_transition_endpoint"].endswith("/api/master-records/state-transitions")
    assert payload["stegbrowser_master_records_state_transition_owner"] == "master-records/orchestration"
    assert payload["stegbrowser_master_records_state_transition_credential_authority"] == "TV/TVC"
    assert payload["stegbrowser_master_records_state_transition_browser_credential_required"] is False
    assert payload["stegbrowser_master_records_state_transition_gateway_authority"] == "NONE"
    assert payload["coinbase_skap_readiness_endpoint"].endswith("/api/coinbase/skap/readiness")
    assert payload["coinbase_skap_ingress_endpoint"].endswith("/api/coinbase/skap/ingress")
    assert payload["coinbase_skap_completed_boundary"] == "DEVICE_TO_KV"
    assert payload["coinbase_skap_next_required_transition"] == "KV_SKAP_VAULT_INTERLOCK_ADMISSION"
    assert payload["coinbase_skap_credential_authority"] == "TV/TVC"
    assert payload["coinbase_skap_gateway_execution_authority"] == "NONE"
    assert payload["math_solver_readiness_endpoint"].endswith("/api/math-solver/v1/readiness")
    assert payload["math_solver_solve_endpoint"].endswith("/api/math-solver/v1/solve")
    assert payload["health_bound"] is True
    assert payload["node_standing_contract"] == "ALL_EXTERNAL_ECOSYSTEM_INGRESS_REQUIRES_CANONICAL_NODE_STANDING"
    assert payload["node_standing_modes"] == ["ESTABLISH_GENESIS", "VERIFY_EXISTING"]
    assert payload["node_standing_predecessor_key_required"] is True
    assert payload["node_standing_failed_verification_silent_reenrollment"] is False
    assert payload["canonical_ingress_contract_single"] is True
    assert payload["canonical_ingress_host_single"] is False
    assert payload["continuation_mapping"]["PUBLIC_BOUNDED_CHAT"].endswith("/api/ecosystem-chat")
    assert payload["continuation_mapping"]["RESIDENT_NODE_RENDEZVOUS_REQUEST"].endswith("/api/resident-rendezvous/v1/requests")
    assert payload["continuation_mapping"]["ORGANIZATION_INTR_FRAME"].endswith("/api/org-federation/v1/frames")
    assert payload["continuation_mapping"]["EVALUATOR_INTR"].endswith("/intr/evaluator")
    assert payload["continuation_mapping_is_authority"] is False
    # The advertisement names where standing is crossed and says the
    # continuation is withheld until it is. It must not carry the continuation
    # itself: an instruction set reachable without standing makes
    # `standing_required` a sentence rather than a gate.
    assert payload["node_standing_readiness_endpoint"].endswith("/api/node-standing/readiness")
    assert payload["node_standing_endpoint"].endswith("/api/node-standing")
    assert payload["machine_readable_instructions_released_only_on"] == "ALLOW"
    assert payload["machine_readable_instructions_available_unauthenticated"] is False
    assert "machine_readable_instructions" not in payload
    assert payload["provider_enabled"] is True
    assert payload["durable_storage"] is True
    assert payload["credential_authority"] == "TV/TVC"
    assert payload["github_token_runtime_authority"] == "NONE"
    assert payload["authority_granted"] is False
    assert payload["publication_authority"] is False
    assert payload["execution_authority"] is False
    assert payload["advertisement_sha256"] == _digest(payload)


def test_default_cors_allows_stegverse_site() -> None:
    response = TestClient(app).options(
        "/api/stegverse-node",
        headers={
            "Origin": "https://stegverse.org",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://stegverse.org"


def _genesis() -> dict:
    return {"mode": "ESTABLISH_GENESIS", "node_ref": "external-reviewer-node", "predecessor": None}


def test_instructions_are_released_only_after_standing_resolves_allow() -> None:
    client = TestClient(app)

    refused = client.post("/api/node-standing", json={"mode": "ESTABLISH_GENESIS",
                                                     "node_ref": "external-reviewer-node"})
    assert refused.status_code == 422
    detail = refused.json()["detail"]
    assert detail["disposition"] == "FAIL_CLOSED"
    assert detail["instructions_released"] is False
    assert "machine_readable_instructions" not in detail

    allowed = client.post("/api/node-standing", json=_genesis())
    assert allowed.status_code == 200
    body = allowed.json()
    assert body["disposition"] == "ALLOW"
    assert body["generation"] == 1
    assert body["instructions_released"] is True
    # Standing is structural here, and the released instructions still grant
    # nothing. Both statements have to survive on the same response.
    assert body["structural_standing_is_authenticated_standing"] is False
    assert body["machine_readable_instructions_authority_effect"] == "NONE_INSTRUCTIONS_ONLY"

    llm = body["machine_readable_instructions"]["LLM_MACHINE_CONTINUATION"]
    assert llm["standing_required"] is True
    assert llm["receiving_owner"] == "llm_adapter.governed_manifest_ingress"
    assert llm["processing_selector"] == "manifest.processing.capability + manifest.processing.route_id"
    assert llm["direct_bypass_without_standing"] == "FAIL_CLOSED"
    framework = body["machine_readable_instructions"]["EXTERNAL_FRAMEWORK_MANIFEST_CONTINUATION"]
    assert framework["sdk_builder_api"] == "stegverse.manifest_builder.build_manifest"
    assert framework["sdk_builder_cli"] == "stegverse manifest build"
    assert framework["sdk_framework_api"] == "stegverse.external_framework_runner.manifest_external_framework_submission"
    assert framework["sdk_framework_cli"] == "stegverse external-run"
    assert framework["enclosed_validation_is_canonical"] is False


def test_standing_readiness_publishes_the_requirement_without_granting_it() -> None:
    readiness = TestClient(app).get("/api/node-standing/readiness").json()
    assert readiness["schema"] == "stegverse.node-standing-readiness.v1"
    assert readiness["standing_modes"] == ["ESTABLISH_GENESIS", "VERIFY_EXISTING"]
    assert readiness["predecessor_key_required"] is True
    assert readiness["absent_predecessor_key_disposition"] == "FAIL_CLOSED"
    assert readiness["instructions_released_only_on"] == "ALLOW"
    assert readiness["readiness_is_not_standing"] is True
    assert readiness["authority_effect"] == "NONE_READINESS_ONLY"
    assert "machine_readable_instructions" not in readiness
