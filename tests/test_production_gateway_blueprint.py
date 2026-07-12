from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BLUEPRINT = ROOT / "render-production.yaml"


def test_production_gateway_uses_persistent_storage_and_custody_contract() -> None:
    text = BLUEPRINT.read_text(encoding="utf-8")
    for marker in [
        "plan: starter",
        "mountPath: /var/data",
        "STEGVERSE_TRANSITION_DB",
        "/var/data/stegverse-ecosystem-chat.db",
        "STEGVERSE_STORAGE_DURABLE_ACROSS_RESTARTS",
        'value: "true"',
        "STEGVERSE_MASTER_RECORDS_ENDPOINT",
        "STEGVERSE_MASTER_RECORDS_TOKEN",
        "STEGVERSE_MASTER_RECORDS_ALLOWED_HOSTS",
        "python -m llm_adapter.custody_worker",
    ]:
        assert marker in text


def test_free_validation_blueprint_remains_explicitly_non_durable() -> None:
    text = (ROOT / "render.yaml").read_text(encoding="utf-8")
    assert "plan: free" in text
    assert "/tmp/stegverse-ecosystem-chat.db" in text
    assert 'STEGVERSE_STORAGE_DURABLE_ACROSS_RESTARTS' in text
    assert 'value: "false"' in text
