from __future__ import annotations

import hashlib
import json
import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from llm_adapter.deployed_gateway import app
from llm_adapter import service_gateway_evaluator_intr as mod


class EvaluatorInTrServiceGatewayTests(unittest.TestCase):
    def setUp(self):
        self.old = dict(os.environ)
        os.environ["STEGVERSE_EVALUATOR_INTR_ENABLED"] = "true"
        os.environ["STEGVERSE_EVALUATOR_INTR_UPSTREAM"] = "http://127.0.0.1:8765/intr/evaluator"
        self.client = TestClient(app)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self.old)

    def request_body(self):
        return {
            "schema_version":"stegverse.evaluator_review.interlock_request.v1",
            "request_class":"EVALUATOR_REVIEW",
            "operation":"READ_REVIEW",
            "authority_ref":"PUBLIC_READ",
            "transport":"InTr",
            "payload":{"testId":"t1","revision":2,"manifestHash":"a"*64},
            "bindings":{"test_id":"t1","revision":2,"manifest_hash":"a"*64},
            "authority_transfer":False,
        }

    def headers(self, raw: bytes):
        return {
            "Origin":"https://stegverse.org",
            "Content-Type":"application/json",
            "X-StegVerse-Transport":"InTr",
            "X-StegVerse-Authorization-Id":"PUBLIC_READ",
            "X-StegVerse-Payload-SHA256":hashlib.sha256(raw).hexdigest(),
        }

    def test_readiness_is_authority_neutral(self):
        r=self.client.get("/intr/evaluator/readiness")
        self.assertEqual(r.status_code,200)
        body=r.json()
        self.assertEqual(body["state"],"READY")
        self.assertEqual(body["credential_authority"],"TV/TVC")
        self.assertFalse(body["gateway_receipt_authority"])
        self.assertFalse(body["gateway_evaluator_authority"])

    def test_exact_bytes_and_intr_headers_are_forwarded(self):
        raw=json.dumps(self.request_body(),separators=(",",":")).encode()
        returned=b'{"ok":true,"transport_receipts":{"ingress":{},"egress":{}}}'
        with patch.object(mod,"_forward",return_value=(200,returned,"application/json")) as forward:
            r=self.client.post("/intr/evaluator",content=raw,headers=self.headers(raw))
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.content,returned)
        sent_body,sent_headers=forward.call_args.args
        self.assertEqual(sent_body,raw)
        self.assertEqual(sent_headers["origin"],"https://stegverse.org")
        self.assertEqual(sent_headers["x-stegverse-transport"],"InTr")
        self.assertEqual(sent_headers["x-stegverse-authorization-id"],"PUBLIC_READ")
        self.assertEqual(sent_headers["x-stegverse-payload-sha256"],hashlib.sha256(raw).hexdigest())
        self.assertNotIn("authorization",sent_headers)
        self.assertNotIn("cookie",sent_headers)

    def test_cookie_or_authorization_is_rejected(self):
        raw=json.dumps(self.request_body()).encode()
        headers=self.headers(raw)
        headers["Authorization"]="Bearer no"
        r=self.client.post("/intr/evaluator",content=raw,headers=headers)
        self.assertEqual(r.status_code,400)

    def test_untrusted_origin_is_rejected(self):
        raw=json.dumps(self.request_body()).encode()
        headers=self.headers(raw); headers["Origin"]="https://example.com"
        r=self.client.post("/intr/evaluator",content=raw,headers=headers)
        self.assertEqual(r.status_code,403)

    def test_bad_body_hash_is_rejected(self):
        raw=json.dumps(self.request_body()).encode()
        headers=self.headers(raw); headers["X-StegVerse-Payload-SHA256"]="0"*64
        r=self.client.post("/intr/evaluator",content=raw,headers=headers)
        self.assertEqual(r.status_code,400)

    def test_remote_upstream_is_rejected(self):
        os.environ["STEGVERSE_EVALUATOR_INTR_UPSTREAM"]="https://remote.example/intr/evaluator"
        with self.assertRaises(ValueError):
            mod._upstream()

    def test_disabled_by_default_fails_closed(self):
        os.environ["STEGVERSE_EVALUATOR_INTR_ENABLED"]="false"
        raw=json.dumps(self.request_body()).encode()
        r=self.client.post("/intr/evaluator",content=raw,headers=self.headers(raw))
        self.assertEqual(r.status_code,503)


if __name__=="__main__":
    unittest.main()
