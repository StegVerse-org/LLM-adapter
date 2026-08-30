from __future__ import annotations

import hashlib
import json
import os
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest.mock import patch

from fastapi.testclient import TestClient

from llm_adapter.deployed_gateway import app
from llm_adapter import service_gateway_sv002_observation as mod


class _LoopbackCaptureHandler(BaseHTTPRequestHandler):
    body = None
    headers_seen = None

    def do_POST(self):
        if self.path != "/intr/sv002-observe":
            self.send_response(404)
            self.end_headers()
            return
        length = int(self.headers.get("Content-Length") or "0")
        type(self).body = self.rfile.read(length)
        type(self).headers_seen = {k.lower(): v for k, v in self.headers.items()}
        raw = b'{"schema":"bounded-loopback-response","ok":true}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, fmt, *args):
        return


class SV002ObservationGatewayTests(unittest.TestCase):
    def setUp(self):
        self.old = dict(os.environ)
        os.environ[mod.ENABLED_ENV] = "true"
        os.environ[mod.UPSTREAM_ENV] = mod.LOOPBACK_UPSTREAM
        self.client = TestClient(app)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self.old)

    def body(self):
        return {
            "schema_version": "stegverse.sv002.public_observation.interlock_request.v1",
            "request_class": "SV002_PUBLIC_OBSERVE",
            "operation": "READ_OBSERVATION",
            "authority_ref": "PUBLIC_READ",
            "transport": "InTr",
            "observer": {
                "node_id": "n",
                "interlock_id": "i",
                "registration_receipt_sha256": "a" * 64,
                "genesis_receipt": {},
            },
            "bindings": {
                "experiment_id": "STEGVERSE-002-SELF-CHARACTERIZATION-001",
                "observation_projection": "PUBLIC_READ_ONLY",
            },
            "payload": {},
            "authority_transfer": False,
            "request_sha256": "b" * 64,
        }

    def headers(self, raw):
        return {
            "Origin": "https://stegverse.org",
            "Content-Type": "application/json",
            "X-StegVerse-Transport": "InTr",
            "X-StegVerse-Authorization-Id": "PUBLIC_READ",
            "X-StegVerse-Payload-SHA256": hashlib.sha256(raw).hexdigest(),
        }

    def test_readiness_authority_neutral(self):
        r = self.client.get("/intr/sv002-observe/readiness")
        self.assertEqual(r.status_code, 200)
        b = r.json()
        self.assertEqual(b["state"], "READY")
        self.assertFalse(b["gateway_receipt_authority"])
        self.assertFalse(b["gateway_experiment_authority"])

    def test_exact_bytes_forwarded(self):
        raw = json.dumps(self.body(), separators=(",", ":")).encode()
        returned = b'{"ok":true}'
        with patch.object(mod, "_forward", return_value=(200, returned, "application/json")) as f:
            r = self.client.post("/intr/sv002-observe", content=raw, headers=self.headers(raw))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.content, returned)
        self.assertEqual(f.call_args.args[0], raw)

    def test_real_loopback_forward_observed(self):
        _LoopbackCaptureHandler.body = None
        _LoopbackCaptureHandler.headers_seen = None
        server = HTTPServer(("127.0.0.1", 0), _LoopbackCaptureHandler)
        thread = threading.Thread(target=server.handle_request, daemon=True)
        thread.start()
        try:
            port = server.server_address[1]
            os.environ[mod.UPSTREAM_ENV] = f"http://127.0.0.1:{port}/intr/sv002-observe"
            raw = json.dumps(self.body(), separators=(",", ":")).encode()
            headers = self.headers(raw)
            r = self.client.post("/intr/sv002-observe", content=raw, headers=headers)
            thread.join(timeout=3)
            self.assertFalse(thread.is_alive(), "loopback upstream did not receive request")
            self.assertEqual(r.status_code, 200)
            self.assertEqual(r.json(), {"schema": "bounded-loopback-response", "ok": True})
            self.assertEqual(_LoopbackCaptureHandler.body, raw)
            seen = _LoopbackCaptureHandler.headers_seen or {}
            self.assertEqual(seen.get("origin"), "https://stegverse.org")
            self.assertEqual(seen.get("x-stegverse-transport"), "InTr")
            self.assertEqual(seen.get("x-stegverse-authorization-id"), "PUBLIC_READ")
            self.assertEqual(seen.get("x-stegverse-payload-sha256"), hashlib.sha256(raw).hexdigest())
            self.assertNotIn("authorization", seen)
            self.assertNotIn("cookie", seen)
        finally:
            server.server_close()

    def test_credentials_rejected(self):
        raw = json.dumps(self.body()).encode()
        h = self.headers(raw)
        h["Authorization"] = "Bearer no"
        self.assertEqual(
            self.client.post("/intr/sv002-observe", content=raw, headers=h).status_code,
            400,
        )

    def test_wrong_request_class_rejected(self):
        body = self.body()
        body["request_class"] = "EVALUATOR_REVIEW"
        raw = json.dumps(body).encode()
        self.assertEqual(
            self.client.post("/intr/sv002-observe", content=raw, headers=self.headers(raw)).status_code,
            400,
        )

    def test_remote_upstream_rejected(self):
        os.environ[mod.UPSTREAM_ENV] = "https://remote.example/intr/sv002-observe"
        with self.assertRaises(ValueError):
            mod._upstream()

    def test_disabled_fails_closed(self):
        os.environ[mod.ENABLED_ENV] = "false"
        raw = json.dumps(self.body()).encode()
        self.assertEqual(
            self.client.post("/intr/sv002-observe", content=raw, headers=self.headers(raw)).status_code,
            503,
        )


if __name__ == "__main__":
    unittest.main()
