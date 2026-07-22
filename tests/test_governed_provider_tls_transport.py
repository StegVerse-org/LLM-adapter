from __future__ import annotations

import json
import os
import ssl
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from llm_adapter import governed_provider


class ProviderFixture(BaseHTTPRequestHandler):
    token = "transport-test-token"

    def log_message(self, *_args) -> None:
        return

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/generate":
            self.send_error(404)
            return
        if self.headers.get("Authorization") != f"Bearer {self.token}":
            self.send_error(401)
            return
        length = int(self.headers.get("Content-Length", "0"))
        request = json.loads(self.rfile.read(length).decode("utf-8"))
        metadata = request["metadata"]
        text = "StegVerse TLS provider transport verified."
        payload = {
            "text": text,
            "provider_request_id": "fixture-provider-request-1",
            "provider_receipt_id": "sha256:fixture-provider-receipt",
            "usage": {
                "input_chars": len(request["input"]),
                "output_chars": len(text),
            },
            "metadata": {
                "transition_id": metadata["transition_id"],
                "run_id": metadata["run_id"],
                "provider_output_is_authority": False,
                "execution_authority": False,
                "publication_authority": False,
            },
        }
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def generate_certificate(directory: Path) -> tuple[Path, Path]:
    key = directory / "provider.key"
    cert = directory / "provider.crt"
    config = directory / "openssl.cnf"
    config.write_text(
        """[req]\ndistinguished_name=dn\nx509_extensions=v3\nprompt=no\n[dn]\nCN=localhost\n[v3]\nsubjectAltName=DNS:localhost,IP:127.0.0.1\nbasicConstraints=CA:TRUE\nkeyUsage=digitalSignature,keyEncipherment,keyCertSign\n""",
        encoding="utf-8",
    )
    subprocess.run(
        [
            "openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes",
            "-days", "1", "-keyout", str(key), "-out", str(cert),
            "-config", str(config),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return cert, key


def test_tls_transport_auth_identity_receipt_and_ledger(monkeypatch, tmp_path: Path) -> None:
    cert, key = generate_certificate(tmp_path)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile=cert, keyfile=key)
    server = ThreadingHTTPServer(("127.0.0.1", 0), ProviderFixture)
    server.socket = context.wrap_socket(server.socket, server_side=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]

    monkeypatch.setenv("STEGVERSE_PROVIDER_ENABLED", "true")
    monkeypatch.setenv("STEGVERSE_PROVIDER_ENDPOINT", f"https://localhost:{port}/generate")
    monkeypatch.setenv("STEGVERSE_PROVIDER_ALLOWED_HOSTS", "localhost")
    monkeypatch.setenv("STEGVERSE_PROVIDER_TOKEN", ProviderFixture.token)
    monkeypatch.setenv("STEGVERSE_PROVIDER_MODEL", "stegverse-transport-fixture")
    monkeypatch.setenv("STEGVERSE_PROVIDER_NAME", "stegverse-owned-provider")
    monkeypatch.setenv("STEGVERSE_TRANSITION_DB", str(tmp_path / "provider-ledger.db"))
    monkeypatch.setenv("STEGVERSE_PROVIDER_MAX_INPUT_CHARS", "12000")
    monkeypatch.setenv("STEGVERSE_PROVIDER_MAX_OUTPUT_CHARS", "6000")
    monkeypatch.setenv("STEGVERSE_PROVIDER_DAILY_REQUEST_LIMIT", "10")
    monkeypatch.setenv("STEGVERSE_PROVIDER_DAILY_COST_LIMIT_USD", "5")
    monkeypatch.setenv("STEGVERSE_PROVIDER_MAX_REQUEST_COST_USD", "1")
    monkeypatch.setenv("REQUESTS_CA_BUNDLE", str(cert))

    try:
        result = governed_provider.generate(
            message="Verify the StegVerse-owned provider transport.",
            transition_id="transition.transport.0001",
            run_id="run.transport.0001",
        )
    finally:
        server.shutdown()
        thread.join(timeout=5)

    assert result.used is True
    assert result.status == "USED"
    assert result.provider_name == "stegverse-owned-provider"
    assert result.model == "stegverse-transport-fixture"
    assert result.provider_request_id == "fixture-provider-request-1"
    assert result.provider_receipt_id.startswith("provider-response-receipt:sha256:")
    assert result.fallback_required is False
    assert result.text == "StegVerse TLS provider transport verified."
    count, spent = governed_provider.ProviderUsageLedger().current("stegverse-owned-provider")
    assert count == 1
    assert spent > 0
