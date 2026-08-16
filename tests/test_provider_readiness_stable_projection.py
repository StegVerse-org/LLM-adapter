from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LIVE_WORKFLOW = ROOT / ".github/workflows/ecosystem-chat-live-activation.yml"
GITHUB_MODELS_WORKFLOW = ROOT / ".github/workflows/ecosystem-chat-github-models-execution.yml"
HANDOFF = ROOT / "docs/WORKFLOW_CONSOLIDATION_MIRROR_HANDOFF.md"
ORG_HANDOFF_POINTER = "StegVerse-Labs/.github/docs/ORG_MIRROR_HANDOFF.md"


def test_hosted_provider_activation_paths_are_retired() -> None:
    assert not LIVE_WORKFLOW.exists()
    assert not GITHUB_MODELS_WORKFLOW.exists()


def test_provider_readiness_is_owned_by_tvc_and_sovereign_carrier() -> None:
    source = HANDOFF.read_text(encoding="utf-8")
    for required in (
        "credential_authority: TV/TVC",
        "github_token_runtime_authority: NONE",
        "GitHub token as provider credential: prohibited",
        "repository secrets for provider/Master Records production path: prohibited",
        "resident sovereign carrier",
        ORG_HANDOFF_POINTER,
    ):
        assert required in source
