from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_production_render_blueprint_uses_durable_contract() -> None:
    blueprint = (ROOT / "render-production.yaml").read_text(encoding="utf-8")

    required_fragments = (
        "name: stegverse-master-records-custody",
        "type: pserv",
        "plan: starter",
        "mountPath: /var/data",
        "MASTER_RECORDS_STORAGE_DURABLE_ACROSS_RESTARTS",
        'value: "true"',
        "name: stegverse-ecosystem-chat-gateway",
        "STEGVERSE_TRANSITION_DB",
        "/var/data/stegverse-ecosystem-chat.db",
        "STEGVERSE_USAGE_SESSION_DB",
        "/var/data/stegverse-usage-sessions.db",
        "STEGVERSE_STORAGE_DURABLE_ACROSS_RESTARTS",
        "STEGVERSE_MASTER_RECORDS_HOSTPORT",
        "fromService:",
        "STEGVERSE_PROVIDER_ENDPOINT",
        "sync: false",
        "healthCheckPath: /health",
    )
    for fragment in required_fragments:
        assert fragment in blueprint, f"missing production Render contract fragment: {fragment}"


def test_production_render_blueprint_contains_no_embedded_provider_secret() -> None:
    blueprint = (ROOT / "render-production.yaml").read_text(encoding="utf-8")

    provider_token_block = blueprint.split("- key: STEGVERSE_PROVIDER_TOKEN", 1)[1].split("- key:", 1)[0]
    assert "sync: false" in provider_token_block
    assert "value:" not in provider_token_block
    assert "generateValue:" not in provider_token_block


def test_default_render_blueprint_remains_fail_closed_until_approved() -> None:
    blueprint = (ROOT / "render.yaml").read_text(encoding="utf-8")

    assert 'STEGVERSE_STORAGE_DURABLE_ACROSS_RESTARTS\n        value: "false"' in blueprint
    assert 'STEGVERSE_PROVIDER_ENABLED\n        value: "false"' in blueprint
    assert "http://127.0.0.1:9" in blueprint
