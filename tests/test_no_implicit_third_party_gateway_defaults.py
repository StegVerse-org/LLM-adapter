from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACTIVE = (
    "scripts/write_live_activation_status.py",
    "scripts/verify_live_ecosystem_chat_activation.py",
    "scripts/verify_external_publication_staging.py",
)
HOST_MARKERS = ("onrender.com", "vercel.app", "netlify.app")


def test_active_gateway_tools_have_no_hosted_provider_default() -> None:
    for rel in ACTIVE:
        source = (ROOT / rel).read_text(encoding="utf-8")
        for marker in HOST_MARKERS:
            assert marker not in source, f"{rel} contains implicit hosted provider marker {marker}"


def test_live_verifiers_require_explicit_runtime_gateway() -> None:
    live = (ROOT / "scripts/verify_live_ecosystem_chat_activation.py").read_text(encoding="utf-8")
    staging = (ROOT / "scripts/verify_external_publication_staging.py").read_text(encoding="utf-8")
    status = (ROOT / "scripts/write_live_activation_status.py").read_text(encoding="utf-8")

    assert 'os.getenv("STEGVERSE_GATEWAY_BASE_URL", "")' in live
    assert "explicit_gateway_base_url_required" in live
    assert '"implicit_third_party_gateway": False' in live

    assert 'os.getenv("STEGVERSE_GATEWAY_BASE_URL", "")' in staging
    assert "live staging verification requires explicit STEGVERSE_GATEWAY_BASE_URL" in staging

    assert "DEFAULT_GATEWAY" not in status
    assert '"gateway_selection": "OBSERVATION_EXPLICIT_ONLY"' in status
    assert '"implicit_third_party_gateway": False' in status
