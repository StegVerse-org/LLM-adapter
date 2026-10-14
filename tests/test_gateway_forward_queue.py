"""An unreachable same-host receiver queues the forward; it never refuses on liveness."""
from __future__ import annotations

import base64
import collections
import hashlib
import importlib
import io
import json
import os
import shutil
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock
from urllib import error as urlerror

from llm_adapter.web import FastAPI
from llm_adapter.web.testclient import TestClient

from llm_adapter import gateway_forward_queue as queue
from llm_adapter.deployed_gateway import app

evaluator = importlib.import_module("llm_adapter.service_gateway_evaluator_intr")
sv002 = importlib.import_module("llm_adapter.service_gateway_sv002_observation")
hil_intr = importlib.import_module("llm_adapter.service_gateway_hil_intr")
receiver = importlib.import_module("llm_adapter.service_gateway_hil_receiver_proxy")


def refuse(*_args, **_kwargs):
    raise urlerror.URLError(ConnectionRefusedError(111, "Connection refused"))


def isolated_db(monkeypatch, tmp_path):
    monkeypatch.setenv(queue.DB_ENV, str(tmp_path / "forward.db"))


def evaluator_request(monkeypatch):
    monkeypatch.setenv("STEGVERSE_EVALUATOR_INTR_ENABLED", "true")
    monkeypatch.setenv("STEGVERSE_EVALUATOR_INTR_UPSTREAM", "http://127.0.0.1:8765/intr/evaluator")
    raw = json.dumps({
        "schema_version": "stegverse.evaluator_review.interlock_request.v1",
        "request_class": "EVALUATOR_REVIEW", "operation": "READ_REVIEW",
        "authority_ref": "PUBLIC_READ", "transport": "InTr", "payload": {},
        "bindings": {}, "authority_transfer": False,
    }).encode()
    headers = {
        "Origin": "https://stegverse.org", "Content-Type": "application/json",
        "X-StegVerse-Transport": "InTr", "X-StegVerse-Authorization-Id": "PUBLIC_READ",
        "X-StegVerse-Payload-SHA256": hashlib.sha256(raw).hexdigest(),
    }
    return raw, headers


def receiver_client(monkeypatch):
    monkeypatch.setenv(receiver.ENABLED_ENV, "true")
    monkeypatch.setenv(receiver.UPSTREAM_ENV, "http://127.0.0.1:8877")
    monkeypatch.setattr(receiver.urlrequest, "urlopen", refuse)
    local = FastAPI()
    local.add_middleware(receiver.HILMachineReceiverProxyMiddleware)
    return TestClient(local, base_url="https://stegverse.org")


_Captured = collections.namedtuple("CaptureResult", "out err")


class GatewayForwardQueueTests(unittest.TestCase):
    def _tmp_path(self):
        """tmp_path equivalent: a fresh directory for this test, removed afterwards."""
        if getattr(self, "_tmp", None) is None:
            self._tmp = Path(tempfile.mkdtemp())
            self.addCleanup(shutil.rmtree, self._tmp, ignore_errors=True)
        return self._tmp

    def _setattr(self, target, *args, raising=True):
        """monkeypatch.setattr equivalent: dotted-path or (object, name) form, undone after the test."""
        if isinstance(target, str):
            patcher = mock.patch(target, *args, create=not raising)
        else:
            patcher = mock.patch.object(target, *args, create=not raising)
        patcher.start()
        self.addCleanup(patcher.stop)

    def _setenv(self, name, value):
        """monkeypatch.setenv equivalent: os.environ is restored after the test."""
        patcher = mock.patch.dict(os.environ, {name: str(value)})
        patcher.start()
        self.addCleanup(patcher.stop)

    def _monkeypatch(self):
        """The monkeypatch methods the module helpers call, each undone after the test."""
        return types.SimpleNamespace(setattr=self._setattr, setenv=self._setenv)

    def _capsys(self):
        """capsys equivalent: sys.stdout and sys.stderr are captured for the rest of the test."""
        streams = {"stdout": io.StringIO(), "stderr": io.StringIO()}
        for name, stream in streams.items():
            patcher = mock.patch.object(sys, name, stream)
            patcher.start()
            self.addCleanup(patcher.stop)

        def readouterr():
            captured = _Captured(streams["stdout"].getvalue(), streams["stderr"].getvalue())
            for stream in streams.values():
                stream.seek(0)
                stream.truncate()
            return captured

        return types.SimpleNamespace(readouterr=readouterr)

    def test_unreachable_evaluator_receiver_queues_instead_of_503(self):
        monkeypatch = self._monkeypatch()
        tmp_path = self._tmp_path()
        isolated_db(monkeypatch, tmp_path)
        self._setattr(evaluator.urlrequest, "urlopen", refuse)
        raw, headers = evaluator_request(monkeypatch)
        response = TestClient(app).post("/intr/evaluator", content=raw, headers=headers)
        assert response.status_code == 202
        body = response.json()
        assert body["schema"] == queue.QUEUED_SCHEMA
        assert body["state"] == "QUEUED"
        assert body["receiver_unavailable_disposition"] == "DURABLE_QUEUE"
        assert body["destination_liveness_is_transition_predicate"] is False
        assert body["external_machine_awaited"] is False
        assert body["consequence_observation"] == "NOT_AUTHENTICALLY_OBSERVED"
        assert body["reconciliation_entrypoint"] == "GET " + body["status_path"]
        assert body["authority_effect"] == "NONE_TRANSPORT_ONLY"
        status = TestClient(app).get(body["status_path"]).json()
        assert status["state"] == "QUEUED"
        assert status["receiver_response"] is None

    def test_startup_drain_delivers_exact_bytes_and_keeps_receiver_answer(self):
        monkeypatch = self._monkeypatch()
        tmp_path = self._tmp_path()
        isolated_db(monkeypatch, tmp_path)
        self._setattr(evaluator.urlrequest, "urlopen", refuse)
        raw, headers = evaluator_request(monkeypatch)
        queued = TestClient(app).post("/intr/evaluator", content=raw, headers=headers).json()
        seen = {}

        def live(target, body, forwarded):
            seen.update(target=target, body=body, headers=forwarded)
            return 200, b'{"receiver":"answered"}', "application/json"

        results = queue.process_pending(send=live)
        assert results == [{"forward_id": queued["forward_id"], "state": "FORWARDED", "response_status": 200}]
        assert seen["target"] == "http://127.0.0.1:8765/intr/evaluator"
        assert seen["body"] == raw
        assert seen["headers"]["x-stegverse-payload-sha256"] == hashlib.sha256(raw).hexdigest()
        status = queue.status(queued["forward_id"])
        assert status["state"] == "FORWARDED"
        assert base64.b64decode(status["receiver_response"]["body_base64"]) == b'{"receiver":"answered"}'
        # Delivered once: nothing left to drain.
        assert queue.process_pending(send=live) == []

    def test_failed_drain_stays_queued_as_retry(self):
        monkeypatch = self._monkeypatch()
        tmp_path = self._tmp_path()
        isolated_db(monkeypatch, tmp_path)
        identity = queue.enqueue("evaluator_intr", "http://127.0.0.1:1/intr/evaluator", b"{}", {}, error="URLError")
        assert queue.enqueue("evaluator_intr", "http://127.0.0.1:1/intr/evaluator", b"{}", {}, error="URLError") == identity

        def down(*_args):
            raise ConnectionRefusedError()

        assert queue.process_pending(send=down)[0]["state"] == "RETRY"
        assert queue.status(identity)["state"] == "RETRY"
        assert queue.status(identity)["attempts"] == 3

    def test_live_event_drains_queued_forwards_of_the_same_gateway(self):
        monkeypatch = self._monkeypatch()
        tmp_path = self._tmp_path()
        isolated_db(monkeypatch, tmp_path)
        earlier = queue.enqueue("sv002_observation", "http://127.0.0.1:8766/intr/sv002-observe", b"{}", {}, error="URLError")
        other = queue.enqueue("evaluator_intr", "http://127.0.0.1:8765/intr/evaluator", b"{}", {}, error="URLError")
        self._setattr(queue, "_send", lambda *_a: (200, b"{}", "application/json"))
        queue.drain_after_live_event("sv002_observation")
        assert queue.status(earlier)["state"] == "FORWARDED"
        assert queue.status(other)["state"] == "QUEUED"

    def test_unreachable_sv002_receiver_queues(self):
        monkeypatch = self._monkeypatch()
        tmp_path = self._tmp_path()
        isolated_db(monkeypatch, tmp_path)
        self._setenv(sv002.ENABLED_ENV, "true")
        self._setenv(sv002.UPSTREAM_ENV, sv002.LOOPBACK_UPSTREAM)
        self._setattr(sv002.urlrequest, "urlopen", refuse)
        raw = json.dumps({
            "schema_version": "stegverse.sv002.public_observation.interlock_request.v1",
            "request_class": "SV002_PUBLIC_OBSERVE", "operation": "READ_OBSERVATION",
            "transport": "InTr", "authority_transfer": False,
        }).encode()
        response = TestClient(app).post("/intr/sv002-observe", content=raw, headers={
            "Origin": "https://stegverse.org", "Content-Type": "application/json",
            "X-StegVerse-Transport": "InTr", "X-StegVerse-Authorization-Id": "PUBLIC_READ",
            "X-StegVerse-Payload-SHA256": hashlib.sha256(raw).hexdigest(),
        })
        assert response.status_code == 202
        assert response.json()["gateway"] == "sv002_observation"

    def test_unreachable_device_kv_receiver_queues(self):
        monkeypatch = self._monkeypatch()
        tmp_path = self._tmp_path()
        isolated_db(monkeypatch, tmp_path)
        self._setenv("STEGVERSE_HIL_INTR_ENABLED", "true")
        self._setenv("STEGVERSE_HIL_INTR_UPSTREAM", "http://127.0.0.1:8765/intr/materialization")
        self._setattr(hil_intr, "_read_profile", lambda: {
            "schema": "stegverse.universal-intr-profiled-ingress/v1",
            "state": "ACTIVE_SOVEREIGN_INTR_INGRESS", "protocol": "InTr",
            "profile_path": "/intr/profile", "materialization_path": "/intr/materialization",
            "device_kv_result_path": "/intr/device-kv/result",
            "profiles": ["HIL:Ingress", "KV:KnowledgeVaultInterlock"],
            "supported_origins": ["STEGOS_NODE_OUTBOX"], "event_triggered": True,
            "always_on_application_receiver_required": False, "second_user_device_required": False,
            "g18_required": False, "tls_enabled": False, "credential_authority": "TV/TVC",
            "github_token_runtime_authority": "NONE", "execution_authority": "NONE",
            "authority_effect": "NONE_DISCOVERY_EVIDENCE_ONLY",
        })
        self._setattr(hil_intr.urlrequest, "urlopen", refuse)
        local = FastAPI()
        local.include_router(hil_intr.router)
        body = b'{"schema":"stegverse.device-kv.query-result-request/v1"}'
        response = TestClient(local, base_url="https://stegverse.org").post("/intr/device-kv/result", content=body, headers={
            "Origin": "https://stegverse.org", "Content-Type": "application/json",
            "X-StegVerse-Transport": "InTr", "X-StegVerse-Transport-Origin": "STEGOS_NODE_OUTBOX",
            "X-StegVerse-Payload-SHA256": hashlib.sha256(body).hexdigest(),
        })
        assert response.status_code == 202
        assert response.json()["gateway"] == "intr_device_kv_result"

    def test_unreachable_hil_receiver_queues_post(self):
        monkeypatch = self._monkeypatch()
        tmp_path = self._tmp_path()
        isolated_db(monkeypatch, tmp_path)
        response = receiver_client(monkeypatch).post("/api/hil/submissions", content=b"multipart-bytes",
                                                     headers={"Content-Type": "multipart/form-data; boundary=x"})
        assert response.status_code == 202
        assert response.json()["gateway"] == "hil_receiver"

    def test_unreachable_hil_receiver_read_has_nothing_to_queue(self):
        monkeypatch = self._monkeypatch()
        tmp_path = self._tmp_path()
        isolated_db(monkeypatch, tmp_path)
        response = receiver_client(monkeypatch).get("/api/hil/readiness")
        assert response.status_code == 503
        assert response.json()["detail"] == "hil_machine_receiver_unavailable"

    def test_status_rejects_malformed_and_unknown_ids(self):
        monkeypatch = self._monkeypatch()
        tmp_path = self._tmp_path()
        isolated_db(monkeypatch, tmp_path)
        client = TestClient(app)
        assert client.get("/intr/forward-queue/not-an-id").status_code == 400
        assert client.get("/intr/forward-queue/fwd-" + "0" * 64).status_code == 404

    def test_startup_drain_never_gates(self):
        monkeypatch = self._monkeypatch()
        tmp_path = self._tmp_path()
        capsys = self._capsys()
        isolated_db(monkeypatch, tmp_path)
        self._setattr(queue, "process_pending", lambda **_k: (_ for _ in ()).throw(OSError("disk")))
        assert queue.main() == 0
        report = json.loads(capsys.readouterr().out)
        assert report["gates_startup"] is False
        assert report["failure_code"].startswith("gateway_forward_queue_drain_failed")


if __name__ == "__main__":
    unittest.main()
