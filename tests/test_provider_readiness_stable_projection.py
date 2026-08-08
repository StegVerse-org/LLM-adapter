from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/ecosystem-chat-live-activation.yml"


def _provider_projection_block(source: str) -> str:
    start = source.index("      - name: Evaluate authorized provider configuration")
    end = source.index("      - name: Install canonical service dependencies", start)
    return source[start:end]


def test_repository_retained_provider_readiness_is_semantic_not_clock_driven() -> None:
    source = WORKFLOW.read_text(encoding="utf-8")
    block = _provider_projection_block(source)

    for required in (
        '"state": "READY_FOR_EXECUTION" if ready else "CONFIGURATION_REQUIRED"',
        '"blockers": [f"authorized_configuration_missing:{name}" for name in missing]',
        '"configuration": {',
        '"runtime_path": [',
        '"result_sha256"',
        "receipts/ecosystem-chat-authorized-provider-activation.latest.json",
    ):
        assert required in block

    for prohibited in (
        '"observed_at"',
        "datetime.now",
        "timezone.utc",
        "from datetime import",
    ):
        assert prohibited not in block


def test_provider_readiness_transition_is_still_durably_retained() -> None:
    source = WORKFLOW.read_text(encoding="utf-8")
    assert "Persist authorized provider activation evidence" in source
    assert "git add receipts/ecosystem-chat-authorized-provider-activation.latest.json" in source
    assert 'echo "Authorized provider activation evidence unchanged."' in source
    assert 'git commit -m "chore: retain authorized provider activation evidence [skip ci]"' in source
    assert "actions/upload-artifact@v4" in source
    assert "ecosystem-chat-authorized-provider-activation-${{ github.run_id }}-${{ github.run_attempt }}" in source
