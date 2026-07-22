from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_owner_artifact_intake_is_hash_bound_and_fail_closed():
    entrypoint = (ROOT / "scripts/container-entrypoint.sh").read_text()
    dockerfile = (ROOT / "Dockerfile").read_text()
    pyproject = (ROOT / "pyproject.toml").read_text()

    for required in (
        "STEGVERSE_SIWE_ENABLED",
        "STEGVERSE_SIWE_OWNER_DIR",
        "STEGVERSE_SIWE_OWNER_WHEEL",
        "STEGVERSE_SIWE_OWNER_WHEEL_SHA256",
        "stegwallet_siwe_owner_wheel_required",
        "stegwallet_siwe_owner_wheel_missing",
        "stegwallet_siwe_owner_wheel_sha256_required",
        "stegwallet_siwe_owner_wheel_sha256_mismatch",
        "hashlib.sha256",
        'export PYTHONPATH="$OWNER_WHEEL',
        "from stegwallet import SiwePolicy, SiweStore, recover_with_eth_account",
        "STEGVERSE_SIWE_DB",
    ):
        assert required in entrypoint

    assert "python -m pip install '.[service,siwe-runtime]'" in dockerfile
    assert '"eth-account>=0.13,<0.14"' in pyproject
    assert "curl" not in entrypoint
    assert "git clone" not in entrypoint
    assert "github.com" not in entrypoint
    assert "pip install" not in entrypoint


def test_siwe_is_not_enabled_by_default():
    entrypoint = (ROOT / "scripts/container-entrypoint.sh").read_text()
    assert 'SIWE_ENABLED="${STEGVERSE_SIWE_ENABLED:-false}"' in entrypoint
    assert "export STEGVERSE_SIWE_ENABLED=true" not in entrypoint
