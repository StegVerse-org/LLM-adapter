from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from llm_adapter.web.testclient import TestClient

from llm_adapter.deployed_gateway import app


def _tvc_receipt() -> dict:
    return {
        "role": "service_gateway_coinbase_skap_ciphertext_intake",
        "admissible": True,
        "binding_matched": True,
        "allowed_keys": [],
        "denied_keys": [],
        "credential_values_available": False,
        "decision_id": "sha256:deployed-gateway-coinbase-stage-decision",
        "policy_hash": "sha256:deployed-gateway-coinbase-stage-policy",
    }


class DeployedGatewayCoinbaseSkapTests(unittest.TestCase):
    def _tmp_path(self):
        """tmp_path equivalent: a fresh directory for this test, removed afterwards."""
        if getattr(self, "_tmp", None) is None:
            self._tmp = Path(tempfile.mkdtemp())
            self.addCleanup(shutil.rmtree, self._tmp, ignore_errors=True)
        return self._tmp

    def _setenv(self, name, value):
        """monkeypatch.setenv equivalent: os.environ is restored after the test."""
        patcher = mock.patch.dict(os.environ, {name: str(value)})
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_deployed_gateway_exposes_coinbase_skap_readiness(self) -> None:
        tmp_path = self._tmp_path()
        self._setenv(
            "STEGVERSE_COINBASE_SKAP_TVC_DECISION_RECEIPT",
            json.dumps(_tvc_receipt()),
        )
        self._setenv("STEGVERSE_SERVICE_GATEWAY_STORAGE_ROOT", str(tmp_path))

        response = TestClient(app).get("/api/coinbase/skap/readiness")
        assert response.status_code == 200
        body = response.json()
        assert body["state"] == "READY"
        assert body["service_id"] == "stegverse-service-gateway"
        assert body["adapter"] == "coinbase-skap-ciphertext-staging"
        assert body["transport_protocol"] == "InTr"
        assert body["completed_boundary"] == "DEVICE_TO_KV"
        assert body["credential_authority"] == "TV/TVC"
        assert body["gateway_credential_value_access"] is False
        assert body["gateway_decryption_authority"] is False
        assert body["gateway_execution_authority"] == "NONE"
        assert body["tvc_admission_completed"] is False
        assert body["skap_vault_admission_completed"] is False
        assert body["next_required_transition"] == "KV_SKAP_VAULT_INTERLOCK_ADMISSION"

    def test_deployed_gateway_route_registration_is_bounded(self) -> None:
        paths = {getattr(route, "path", "") for route in app.routes}
        assert "/api/coinbase/skap/readiness" in paths
        assert "/api/coinbase/skap/ingress" in paths


if __name__ == "__main__":
    unittest.main()
