from __future__ import annotations

import contextlib
import importlib.util
import json
import os
import shutil
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "probe_hil_https_receiver.py"


def load_probe_module():
    spec = importlib.util.spec_from_file_location("hil_https_receiver_probe", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def patch_public_dns(monkeypatch, module, address: str = "203.0.113.10") -> None:
    monkeypatch.setattr(
        module.socket,
        "getaddrinfo",
        lambda host, port, type: [(module.socket.AF_INET, type, 6, "", (address, port))],
    )


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


class HilHttpsReceiverProbeTests(unittest.TestCase):
    @contextlib.contextmanager
    def _case(self):
        """A fresh tmp_path and cleanups for each parametrized case."""
        with contextlib.ExitStack() as stack:
            self._stack, self._tmp = stack, None
            try:
                yield
            finally:
                self._stack, self._tmp = None, None

    def _cleanup(self, function, *args, **kwargs):
        stack = getattr(self, "_stack", None)
        if stack is not None:
            stack.callback(function, *args, **kwargs)
        else:
            self.addCleanup(function, *args, **kwargs)

    def _tmp_path(self):
        """tmp_path equivalent: a fresh directory for this test, removed afterwards."""
        if getattr(self, "_tmp", None) is None:
            self._tmp = Path(tempfile.mkdtemp())
            self._cleanup(shutil.rmtree, self._tmp, ignore_errors=True)
        return self._tmp

    def _setattr(self, target, *args, raising=True):
        """monkeypatch.setattr equivalent: dotted-path or (object, name) form, undone after the test."""
        if isinstance(target, str):
            patcher = mock.patch(target, *args, create=not raising)
        else:
            patcher = mock.patch.object(target, *args, create=not raising)
        patcher.start()
        self._cleanup(patcher.stop)

    def _setenv(self, name, value):
        """monkeypatch.setenv equivalent: os.environ is restored after the test."""
        patcher = mock.patch.dict(os.environ, {name: str(value)})
        patcher.start()
        self._cleanup(patcher.stop)

    def _monkeypatch(self):
        """The monkeypatch methods the module helpers call, each undone after the test."""
        return types.SimpleNamespace(setattr=self._setattr, setenv=self._setenv)

    def test_probe_accepts_exact_origin_bound_contract(self) -> None:
        monkeypatch = self._monkeypatch()
        tmp_path = self._tmp_path()
        module = load_probe_module()
        readiness_url = "https://receiver.example/api/hil/readiness"
        response = FakeResponse(readiness_url, conforming_payload(module))
        opener = FakeOpener(response)
        output = tmp_path / "probe.json"

        self._setenv("STEGVERSE_HIL_RECEIVER_BASE_URL", "https://receiver.example/")
        self._setenv("HIL_PROBE_OUTPUT", str(output))
        patch_public_dns(monkeypatch, module, "8.8.8.8")
        self._setattr(module, "build_opener", lambda *handlers: opener)

        assert module.main() == 0
        evidence = json.loads(output.read_text(encoding="utf-8"))
        assert evidence["receiver_origin"] == "https://receiver.example"
        assert evidence["resolved_public_addresses"] == ["8.8.8.8"]
        assert evidence["readiness_path"] == "/api/hil/readiness"
        assert evidence["redirects_followed"] is False
        assert evidence["mutation_performed"] is False
        assert evidence["authority_effect"] == "NONE"
        assert len(evidence["evidence_sha256"]) == 64
        assert opener.request.full_url == readiness_url

    def test_probe_rejects_unsafe_receiver_origins(self) -> None:
        for base_url in [
            "http://receiver.example",
            "https://user:secret@receiver.example",
            "https://receiver.example/other",
            "https://receiver.example?next=elsewhere",
            "https://receiver.example#fragment",
            "https://localhost",
        ]:
            with self.subTest(base_url=base_url), self._case():
                tmp_path = self._tmp_path()
                module = load_probe_module()
                self._setenv("STEGVERSE_HIL_RECEIVER_BASE_URL", base_url)
                self._setenv("HIL_PROBE_OUTPUT", str(tmp_path / "probe.json"))
                with self.assertRaises(RuntimeError):
                    module.main()

    def test_probe_rejects_non_public_resolved_addresses(self) -> None:
        for address in ["127.0.0.1", "10.0.0.7", "169.254.169.254", "::1", "fc00::1"]:
            with self.subTest(address=address), self._case():
                monkeypatch = self._monkeypatch()
                tmp_path = self._tmp_path()
                module = load_probe_module()
                self._setenv("STEGVERSE_HIL_RECEIVER_BASE_URL", "https://receiver.example")
                self._setenv("HIL_PROBE_OUTPUT", str(tmp_path / "probe.json"))
                patch_public_dns(monkeypatch, module, address)
                with self.assertRaisesRegex(RuntimeError, "non-public address"):
                    module.main()

    def test_probe_rejects_changed_response_url(self) -> None:
        monkeypatch = self._monkeypatch()
        tmp_path = self._tmp_path()
        module = load_probe_module()
        response = FakeResponse("https://other.example/api/hil/readiness", conforming_payload(module))
        self._setenv("STEGVERSE_HIL_RECEIVER_BASE_URL", "https://receiver.example")
        self._setenv("HIL_PROBE_OUTPUT", str(tmp_path / "probe.json"))
        patch_public_dns(monkeypatch, module, "8.8.8.8")
        self._setattr(module, "build_opener", lambda *handlers: FakeOpener(response))
        with self.assertRaisesRegex(RuntimeError, "origin or path changed"):
            module.main()

    def test_probe_rejects_non_json_content_type(self) -> None:
        monkeypatch = self._monkeypatch()
        tmp_path = self._tmp_path()
        module = load_probe_module()
        url = "https://receiver.example/api/hil/readiness"
        response = FakeResponse(url, conforming_payload(module), content_type="text/html")
        self._setenv("STEGVERSE_HIL_RECEIVER_BASE_URL", "https://receiver.example")
        self._setenv("HIL_PROBE_OUTPUT", str(tmp_path / "probe.json"))
        patch_public_dns(monkeypatch, module, "8.8.8.8")
        self._setattr(module, "build_opener", lambda *handlers: FakeOpener(response))
        with self.assertRaisesRegex(RuntimeError, "content type mismatch"):
            module.main()

    def test_redirect_handler_fails_closed(self) -> None:
        module = load_probe_module()
        handler = module.RejectRedirects()
        with self.assertRaisesRegex(RuntimeError, "redirect rejected"):
            handler.redirect_request(None, None, 302, "Found", {}, "https://other.example")


if __name__ == "__main__":
    unittest.main()
