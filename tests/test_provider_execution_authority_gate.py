from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from scripts.validate_provider_execution_authority import canonical_sha256, validate

ROOT = Path(__file__).resolve().parents[1]


def approved_receipt(now: datetime) -> dict:
    payload = {
        "schema": "stegverse.provider_execution_authority.github_models.v1",
        "state": "APPROVED",
        "provider": "github-models",
        "protocol": "openai-chat-completions-v1",
        "endpoint": "https://models.github.ai/inference/chat/completions",
        "allowed_host": "models.github.ai",
        "scope": "ecosystem-chat-single-governed-execution",
        "approved_by": "StegVerse",
        "model": "openai/gpt-4.1",
        "issued_at": (now - timedelta(minutes=1)).isoformat(),
        "expires_at": (now + timedelta(hours=1)).isoformat(),
        "provider_output_is_authority": False,
        "external_mutation_authorized": False,
        "publication_authorized": False,
        "deployment_authorized": False,
        "release_authorized": False,
        "cost_expansion_authorized": False,
        "single_execution": True,
    }
    payload["authority_sha256"] = canonical_sha256(payload)
    return payload


def test_valid_authority_receipt_binds_exact_execution_contract() -> None:
    now = datetime.now(timezone.utc)
    result = validate(approved_receipt(now), now=now)
    assert result["provider"] == "github-models"
    assert result["protocol"] == "openai-chat-completions-v1"
    assert result["endpoint"] == "https://models.github.ai/inference/chat/completions"
    assert result["allowed_host"] == "models.github.ai"
    assert result["model"] == "openai/gpt-4.1"


def test_authority_receipt_fails_closed_on_hash_model_expiry_and_scope() -> None:
    now = datetime.now(timezone.utc)

    tampered = approved_receipt(now)
    tampered["model"] = "openai/other-model"
    with pytest.raises(ValueError, match="authority_sha256_mismatch"):
        validate(tampered, now=now)

    malformed_model = approved_receipt(now)
    malformed_model["model"] = "not-a-provider-qualified-model"
    malformed_model["authority_sha256"] = canonical_sha256(malformed_model)
    with pytest.raises(ValueError, match="model_invalid"):
        validate(malformed_model, now=now)

    expired = approved_receipt(now)
    expired["issued_at"] = (now - timedelta(hours=2)).isoformat()
    expired["expires_at"] = (now - timedelta(hours=1)).isoformat()
    expired["authority_sha256"] = canonical_sha256(expired)
    with pytest.raises(ValueError, match="authority_expired"):
        validate(expired, now=now)

    wrong_scope = approved_receipt(now)
    wrong_scope["scope"] = "general-model-execution"
    wrong_scope["authority_sha256"] = canonical_sha256(wrong_scope)
    with pytest.raises(ValueError, match="authority_field_invalid:scope"):
        validate(wrong_scope, now=now)


def test_request_template_is_explicitly_non_authorizing() -> None:
    request = json.loads(
        (ROOT / "authority/provider-execution-authority.github-models.request.json").read_text()
    )
    assert request["state"] == "REQUESTED_NOT_APPROVED"
    assert request["request_is_execution_authority"] is False
    assert request["manual_secret_entry_required"] is False
    assert request["single_execution"] is True
    assert "model" in request["required_decisions"]


def test_permission_bearing_workflow_is_receipt_triggered_and_single_use() -> None:
    gated = (ROOT / ".github/workflows/ecosystem-chat-github-models-execution.yml").read_text()
    scheduled = (ROOT / ".github/workflows/ecosystem-chat-live-activation.yml").read_text()

    for required in (
        "provider-execution-authority.github-models.v1.json",
        "branches:",
        "- main",
        "validate-authority:",
        "execute-single-governed-request:",
        "needs: validate-authority",
        "models: read",
        "validate_provider_execution_authority.py",
        "Refuse reused authority receipt",
        "Consume authority before provider execution",
        "provider-execution-authority.github-models.consumed.json",
        "STEGVERSE_PROVIDER_TOKEN: ${{ github.token }}",
        "STEGVERSE_PROVIDER_DAILY_REQUEST_LIMIT: '1'",
        "STEGVERSE_EXTERNAL_MUTATION_ENABLED: 'false'",
        "scripts/verify_authorized_provider_activation.py",
    ):
        assert required in gated

    assert "schedule:" not in gated
    assert "workflow_dispatch:" not in gated
    assert "models: read" not in scheduled
    assert "github.token" not in scheduled
