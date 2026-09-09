from pathlib import Path
import tomllib


ROOT = Path(__file__).resolve().parents[1]


def test_service_extra_is_credential_free_and_stegcore_stays_explicit():
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    extras = data["project"]["optional-dependencies"]
    service = extras["service"]
    stegcore = extras["stegcore-integration"]

    assert not any("git+" in dependency for dependency in service)
    assert not any("StegCore" in dependency or "stegcore @" in dependency for dependency in service)
    assert any("stegcore @ git+https://github.com/StegVerse-Labs/StegCore.git@" in dependency for dependency in stegcore)
