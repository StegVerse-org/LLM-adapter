from __future__ import annotations
import hashlib,json,os,unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from llm_adapter.deployed_gateway import app
from llm_adapter import service_gateway_sv002_observation as mod

class SV002ObservationGatewayTests(unittest.TestCase):
    def setUp(self):
        self.old=dict(os.environ); os.environ[mod.ENABLED_ENV]="true"; os.environ[mod.UPSTREAM_ENV]=mod.LOOPBACK_UPSTREAM; self.client=TestClient(app)
    def tearDown(self): os.environ.clear(); os.environ.update(self.old)
    def body(self):
        return {"schema_version":"stegverse.sv002.public_observation.interlock_request.v1","request_class":"SV002_PUBLIC_OBSERVE","operation":"READ_OBSERVATION","authority_ref":"PUBLIC_READ","transport":"InTr","observer":{"node_id":"n","interlock_id":"i","registration_receipt_sha256":"a"*64,"genesis_receipt":{}},"bindings":{"experiment_id":"STEGVERSE-002-SELF-CHARACTERIZATION-001","observation_projection":"PUBLIC_READ_ONLY"},"payload":{},"authority_transfer":False,"request_sha256":"b"*64}
    def headers(self,raw):
        return {"Origin":"https://stegverse.org","Content-Type":"application/json","X-StegVerse-Transport":"InTr","X-StegVerse-Authorization-Id":"PUBLIC_READ","X-StegVerse-Payload-SHA256":hashlib.sha256(raw).hexdigest()}
    def test_readiness_authority_neutral(self):
        r=self.client.get("/intr/sv002-observe/readiness"); self.assertEqual(r.status_code,200); b=r.json(); self.assertEqual(b["state"],"READY"); self.assertFalse(b["gateway_receipt_authority"]); self.assertFalse(b["gateway_experiment_authority"])
    def test_exact_bytes_forwarded(self):
        raw=json.dumps(self.body(),separators=(",",":")).encode(); returned=b'{"ok":true}'
        with patch.object(mod,"_forward",return_value=(200,returned,"application/json")) as f: r=self.client.post("/intr/sv002-observe",content=raw,headers=self.headers(raw))
        self.assertEqual(r.status_code,200); self.assertEqual(r.content,returned); self.assertEqual(f.call_args.args[0],raw)
    def test_credentials_rejected(self):
        raw=json.dumps(self.body()).encode(); h=self.headers(raw); h["Authorization"]="Bearer no"; self.assertEqual(self.client.post("/intr/sv002-observe",content=raw,headers=h).status_code,400)
    def test_wrong_request_class_rejected(self):
        body=self.body(); body["request_class"]="EVALUATOR_REVIEW"; raw=json.dumps(body).encode(); self.assertEqual(self.client.post("/intr/sv002-observe",content=raw,headers=self.headers(raw)).status_code,400)
    def test_remote_upstream_rejected(self):
        os.environ[mod.UPSTREAM_ENV]="https://remote.example/intr/sv002-observe"
        with self.assertRaises(ValueError): mod._upstream()
    def test_disabled_fails_closed(self):
        os.environ[mod.ENABLED_ENV]="false"; raw=json.dumps(self.body()).encode(); self.assertEqual(self.client.post("/intr/sv002-observe",content=raw,headers=self.headers(raw)).status_code,503)
if __name__=="__main__": unittest.main()
