from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "probe_hil_https_receiver.py"


def load_probe_module():
    spec = importlib.util.spec_from_file_location("hil_https_receiver_probe", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeHeaders:
    def __init__(self, content_type: str = "application/json") -> None:
        self.content_type = content_type

    def get_content_type(self) -> str:
        return self.content_type


class FakeResponse:
    def __init__(self, url: str, payload: object, *, content_type: str = "application/json") -> None:
        self.status = 200
        self.url = url
        self.headers = FakeHeaders(content_type)
        self.body = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def geturl(self) -> str:
        return self.url

    def read(self, size: int = -1) -> bytes:
        return self.body if size < 0 else self.body[:size]


class FakeOpener:
    def __init__(self, response: FakeResponse) -> None:
        self.response = response
        self.request = None

    def open(self, request, timeout: int):
        self.request = request
        assert timeout == 20
        return self.response


def conforming_payload(module) -> dict:
    return {
        "schema": "stegverse.hil_intake_readiness.v3",
        "state": "READY",
        "blockers": [],
        "maximum_size_bytes": 10 * 1024 * 1024,
        "accepted_media_type": "application/pdf",
        "provenance_manifest_required": True,
        "provenance_manifest_schema": module.PROVENANCE,
        "participant_metadata_required": False,
        "primary_version": "v1.1",
        "primary_sha256": module.PRIMARY,
        "protocol_version": module.PROTOCOL,
        "prompt_version": module.PROMPT_VERSION,
        "prompt_sha256": module.PROMPT,
        "private_review_configured": False,
        "execution_authority": False,
        "publication_authority": False,
        "master_record_append_authority": False,
    }


def test_probe_accepts_exact_origin_bound_contract(monkeypatch, tmp_path: Path) -> None:
    module = load_probe_module()
    readiness_url = "https://receiver.example/api/hil/readiness"
    response = FakeResponse(readiness_url, conforming_payload(module))
    opener = FakeOpener(response)
    output = tmp_path / "probe.json"

    monkeypatch.setenv("STEGVERSE_HIL_RECEIVER_BASE_URL", "https://receiver.example/")
    monkeypatch.setenv("HIL_PROBE_OUTPUT", str(output))
    monkeypatch.setattr(module, "build_opener", lambda *handlers: opener)

    assert module.main() == 0
    evidence = json.loads(output.read_text(encoding="utf-8"))
    assert evidence["receiver_origin"] == "https://receiver.example"
    assert evidence["readiness_path"] == "/api/hil/readiness"
    assert evidence["redirects_followed"] is False
    assert evidence["mutation_performed"] is False
    assert evidence["authority_effect"] == "NONE"
    assert len(evidence["evidence_sha256"]) == 64
    assert opener.request.full_url == readiness_url


@pytest.mark.parametrize(
    "base_url",
    [
        "http://receiver.example",
        "https://user:secret@receiver.example",
        "https://receiver.example/other",
        "https://receiver.example?next=elsewhere",
        "https://receiver.example#fragment",
    ],
)
def test_probe_rejects_unsafe_receiver_origins(monkeypatch, tmp_path: Path, base_url: str) -> None:
    module = load_probe_module()
    monkeypatch.setenv("STEGVERSE_HIL_RECEIVER_BASE_URL", base_url)
    monkeypatch.setenv("HIL_PROBE_OUTPUT", str(tmp_path / "probe.json"))
    with pytest.raises(RuntimeError):
        module.main()


def test_probe_rejects_changed_response_url(monkeypatch, tmp_path: Path) -> None:
    module = load_probe_module()
    response = FakeResponse("https://other.example/api/hil/readiness", conforming_payload(module))
    monkeypatch.setenv("STEGVERSE_HIL_RECEIVER_BASE_URL", "https://receiver.example")
    monkeypatch.setenv("HIL_PROBE_OUTPUT", str(tmp_path / "probe.json"))
    monkeypatch.setattr(module, "build_opener", lambda *handlers: FakeOpener(response))
    with pytest.raises(RuntimeError, match="origin or path changed"):
        module.main()


def test_probe_rejects_non_json_content_type(monkeypatch, tmp_path: Path) -> None:
    module = load_probe_module()
    url = "https://receiver.example/api/hil/readiness"
    response = FakeResponse(url, conforming_payload(module), content_type="text/html")
    monkeypatch.setenv("STEGVERSE_HIL_RECEIVER_BASE_URL", "https://receiver.example")
    monkeypatch.setenv("HIL_PROBE_OUTPUT", str(tmp_path / "probe.json"))
    monkeypatch.setattr(module, "build_opener", lambda *handlers: FakeOpener(response))
    with pytest.raises(RuntimeError, match="content type mismatch"):
        module.main()


def test_redirect_handler_fails_closed() -> None:
    module = load_probe_module()
    handler = module.RejectRedirects()
    with pytest.raises(RuntimeError, match="redirect rejected"):
        handler.redirect_request(None, None, 302, "Found", {}, "https://other.example")
