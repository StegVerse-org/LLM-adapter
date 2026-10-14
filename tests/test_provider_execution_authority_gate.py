from __future__ import annotations

import json
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

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


class ProviderExecutionAuthorityGateTests(unittest.TestCase):
    def test_valid_authority_receipt_binds_exact_execution_contract(self) -> None:
        now = datetime.now(timezone.utc)
        result = validate(approved_receipt(now), now=now)
        assert result["provider"] == "github-models"
        assert result["protocol"] == "openai-chat-completions-v1"
        assert result["endpoint"] == "https://models.github.ai/inference/chat/completions"
        assert result["allowed_host"] == "models.github.ai"
        assert result["model"] == "openai/gpt-4.1"

    def test_authority_receipt_fails_closed_on_hash_model_expiry_and_scope(self) -> None:
        now = datetime.now(timezone.utc)

        tampered = approved_receipt(now)
        tampered["model"] = "openai/other-model"
        with self.assertRaisesRegex(ValueError, "authority_sha256_mismatch"):
            validate(tampered, now=now)

        malformed_model = approved_receipt(now)
        malformed_model["model"] = "not-a-provider-qualified-model"
        malformed_model["authority_sha256"] = canonical_sha256(malformed_model)
        with self.assertRaisesRegex(ValueError, "model_invalid"):
            validate(malformed_model, now=now)

        expired = approved_receipt(now)
        expired["issued_at"] = (now - timedelta(hours=2)).isoformat()
        expired["expires_at"] = (now - timedelta(hours=1)).isoformat()
        expired["authority_sha256"] = canonical_sha256(expired)
        with self.assertRaisesRegex(ValueError, "authority_expired"):
            validate(expired, now=now)

        wrong_scope = approved_receipt(now)
        wrong_scope["scope"] = "general-model-execution"
        wrong_scope["authority_sha256"] = canonical_sha256(wrong_scope)
        with self.assertRaisesRegex(ValueError, "authority_field_invalid:scope"):
            validate(wrong_scope, now=now)

    def test_request_template_is_explicitly_non_authorizing(self) -> None:
        request = json.loads(
            (ROOT / "authority/provider-execution-authority.github-models.request.json").read_text()
        )
        assert request["state"] == "REQUESTED_NOT_APPROVED"
        assert request["request_is_execution_authority"] is False
        assert request["manual_secret_entry_required"] is False
        assert request["single_execution"] is True
        assert "model" in request["required_decisions"]

    def test_runner_hosted_provider_execution_stays_retired(self) -> None:
        """The GitHub Models execution workflow ran a provider on a hosted runner.

        It is retired (scripts/check_stegverse_live_baseline_provider_authority_binding.py
        requires its absence), so no workflow may grant model access or hand the
        runner token to a provider.
        """
        assert not (ROOT / ".github/workflows/ecosystem-chat-github-models-execution.yml").exists()
        assert not (ROOT / ".github/workflows/ecosystem-chat-live-activation.yml").exists()
        for workflow in sorted((ROOT / ".github/workflows").glob("*.yml")):
            text = workflow.read_text(encoding="utf-8")
            assert "models: read" not in text, workflow.name
            assert "STEGVERSE_PROVIDER_TOKEN: ${{ github.token }}" not in text, workflow.name


if __name__ == "__main__":
    unittest.main()
