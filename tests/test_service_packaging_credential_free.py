import subprocess
import sys
import tomllib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ServicePackagingCredentialFreeTests(unittest.TestCase):
    def test_service_extra_is_credential_free_and_stegcore_stays_explicit(self):
        data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        extras = data["project"]["optional-dependencies"]
        service = extras["service"]
        stegcore = extras["stegcore-integration"]

        assert not any("git+" in dependency for dependency in service)
        assert not any("StegCore" in dependency or "stegcore @" in dependency for dependency in service)
        assert any("stegcore @ git+https://github.com/StegVerse-Labs/StegCore.git@" in dependency for dependency in stegcore)

    def test_core_install_carries_no_third_party_package(self):
        """A plain install carries only the pinned StegVerse SDK, and no extra
        brings back a web framework: the service surfaces run on llm_adapter/web."""
        data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        core = data["project"]["dependencies"]
        assert len(core) == 1 and core[0].startswith("stegverse-sdk @ git+https://github.com/StegVerse-org/StegVerse-SDK.git@")
        extras = data["project"]["optional-dependencies"]
        frameworks = ("fastapi", "starlette", "pydantic", "uvicorn", "httpx", "python-multipart", "requests")
        for name, packages in extras.items():
            for package in packages:
                assert not package.lower().startswith(frameworks), (name, package)

    def test_package_import_does_not_load_pydantic(self):
        probe = "import sys, llm_adapter; sys.exit(1 if 'pydantic' in sys.modules else 0)"
        assert subprocess.run([sys.executable, "-c", probe], cwd=ROOT).returncode == 0


if __name__ == "__main__":
    unittest.main()
