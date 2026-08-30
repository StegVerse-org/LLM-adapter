from __future__ import annotations

import hashlib
import json
from pathlib import Path

from fastapi.testclient import TestClient

from llm_adapter.deployed_gateway import app
from llm_adapter.service_gateway_personal_origin import MANIFEST_NAME, MANIFEST_SCHEMA


def _bundle(root: Path) -> None:
    files = {
        "index.html": b"<h1>personal root</h1>",
        "node.html": b"<h1>node</h1>",
        "services.html": b"<h1>services</h1>",
        "stegverse-me-opaque-resolver.js": b"globalThis.RESOLVER=true;",
        "services-state.js": b"globalThis.SERVICES_STATE=true;",
        "services.js": b"globalThis.SERVICES=true;",
        "kv-readiness-snapshot.json": b'{"schema":"test"}',
    }
    for name, data in files.items():
        (root / name).write_bytes(data)
    manifest = {
        "schema": MANIFEST_SCHEMA,
        "authority_effect": "NONE",
        "private_kv_included": False,
        "files": {name: "sha256:" + hashlib.sha256(data).hexdigest() for name, data in files.items()},
    }
    (root / MANIFEST_NAME).write_text(json.dumps(manifest), encoding="utf-8")


def _client(monkeypatch, tmp_path: Path) -> TestClient:
    _bundle(tmp_path)
    monkeypatch.setenv("STEGVERSE_PERSONAL_ORIGIN_BUNDLE_ROOT", str(tmp_path))
    monkeypatch.setenv("STEGVERSE_PERSONAL_ORIGIN_HOSTS", "stegverse.me,www.stegverse.me,personal.test")
    return TestClient(app)


def test_personal_origin_serves_only_bounded_routes(monkeypatch, tmp_path: Path) -> None:
    client = _client(monkeypatch, tmp_path)
    opaque = "sv1_" + "A" * 43
    for path in (
        "/",
        f"/n/{opaque}/",
        f"/n/{opaque}/services.html",
        f"/n/{opaque}/stegverse-me-opaque-resolver.js",
        f"/n/{opaque}/services-state.js",
        f"/n/{opaque}/services.js",
        f"/n/{opaque}/kv-readiness-snapshot.json",
    ):
        response = client.get(path, headers={"host": "personal.test"})
        assert response.status_code == 200
        assert response.headers["x-stegverse-authority-effect"] == "NONE"
        assert response.headers["x-stegverse-route-possession-grants-access"] == "false"
        assert response.headers["x-stegverse-private-kv-readback"] == "false"


def test_personal_origin_blocks_shared_gateway_api_surface(monkeypatch, tmp_path: Path) -> None:
    client = _client(monkeypatch, tmp_path)
    response = client.get("/api/stegverse-node", headers={"host": "personal.test"})
    assert response.status_code == 404


def test_personal_origin_rejects_bad_opaque_and_non_get(monkeypatch, tmp_path: Path) -> None:
    client = _client(monkeypatch, tmp_path)
    assert client.get("/n/not-opaque/", headers={"host": "personal.test"}).status_code == 404
    assert client.post("/", headers={"host": "personal.test"}).status_code == 405


def test_other_hosts_continue_to_shared_gateway(monkeypatch, tmp_path: Path) -> None:
    client = _client(monkeypatch, tmp_path)
    response = client.get("/api/stegverse-node", headers={"host": "gateway.test"})
    assert response.status_code == 200


def test_missing_or_tampered_bundle_fails_closed(monkeypatch, tmp_path: Path) -> None:
    client = _client(monkeypatch, tmp_path)
    (tmp_path / "node.html").write_text("tampered", encoding="utf-8")
    opaque = "sv1_" + "A" * 43
    response = client.get(f"/n/{opaque}/", headers={"host": "personal.test"})
    assert response.status_code == 503
    assert response.json()["state"] == "FAIL_CLOSED"
    assert response.headers["x-stegverse-activation-effect"] == "false"


def test_manifest_cannot_claim_kv_or_authority(monkeypatch, tmp_path: Path) -> None:
    _bundle(tmp_path)
    manifest = json.loads((tmp_path / MANIFEST_NAME).read_text())
    manifest["private_kv_included"] = True
    (tmp_path / MANIFEST_NAME).write_text(json.dumps(manifest))
    monkeypatch.setenv("STEGVERSE_PERSONAL_ORIGIN_BUNDLE_ROOT", str(tmp_path))
    monkeypatch.setenv("STEGVERSE_PERSONAL_ORIGIN_HOSTS", "personal.test")
    response = TestClient(app).get("/", headers={"host": "personal.test"})
    assert response.status_code == 503
    assert response.json()["reason"] == "personal_origin_manifest_authority_invalid"
