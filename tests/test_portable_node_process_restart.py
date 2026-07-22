from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _json_request(url: str, payload: dict | None = None) -> dict:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "X-SteGVerse-Session": "restart-proof-session"},
        method="GET" if payload is None else "POST",
    )
    with urlopen(request, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def _start_node(port: int, data_dir: Path) -> subprocess.Popen[str]:
    env = os.environ.copy()
    env.update(
        {
            "PORT": str(port),
            "STEGVERSE_DATA_DIR": str(data_dir),
            "STEGVERSE_TRANSITION_DB": str(data_dir / "stegverse-ecosystem-chat.db"),
            "STEGVERSE_EXTERNAL_REVIEW_DB": str(data_dir / "stegverse-external-review.db"),
            "STEGVERSE_STORAGE_DURABLE_ACROSS_RESTARTS": "true",
            "STEGVERSE_PROVIDER_ENABLED": "false",
            "STEGVERSE_MASTER_RECORDS_ENDPOINT": "",
            "STEGVERSE_MASTER_RECORDS_TOKEN": "",
        }
    )
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "llm_adapter.combined_gateway:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=Path(__file__).resolve().parents[1],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    health_url = f"http://127.0.0.1:{port}/health"
    deadline = time.time() + 20
    last_error: Exception | None = None
    while time.time() < deadline:
        if process.poll() is not None:
            output = process.stdout.read() if process.stdout else ""
            raise AssertionError(f"portable node exited before health readiness: {output}")
        try:
            health = _json_request(health_url)
            if health.get("status") == "ok":
                return process
        except (URLError, TimeoutError, ConnectionError) as exc:
            last_error = exc
        time.sleep(0.2)
    process.terminate()
    process.wait(timeout=5)
    raise AssertionError(f"portable node health did not become ready: {last_error}")


def _stop_node(process: subprocess.Popen[str]) -> None:
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def test_transition_survives_real_process_restart(tmp_path: Path) -> None:
    port = _free_port()
    transition_id = "portable-node-process-restart"
    request_payload = {
        "message": "Persist this governed request across a portable-node process restart.",
        "session_id": "restart-proof-session",
        "requested_route": "Site",
        "transition_intent": "bounded_information_request",
        "transition_destination": "ecosystem_chat",
        "goal": "prove transition persistence across a real portable-node process restart",
        "execution_model": "allowlisted_task_request_only",
        "raw_shell_allowed": False,
        "authority_required": True,
        "rate_limit_required": True,
        "receipt_required_for_execution": True,
        "interaction_profile": {},
        "interaction_bands": [],
        "math_solver_supported": True,
        "transition_identity": {
            "transition_id": transition_id,
            "run_id": "portable-node-process-restart-run",
            "event_id": "portable-node-process-restart-event",
            "origin_manifest_id": "portable-node-process-restart-origin",
            "parent_transition_id": None,
            "previous_receipt_id": None,
        },
    }

    first = _start_node(port, tmp_path)
    try:
        health = _json_request(f"http://127.0.0.1:{port}/health")
        assert health["storage_durable_across_restarts"] is True
        created = _json_request(f"http://127.0.0.1:{port}/api/ecosystem-chat", request_payload)
        assert created["transition_id"] == transition_id
        assert created["sqlite_persisted"] is True
        assert created["storage_durable_across_restarts"] is True
        original_receipt = created["final_receipt_id"]
        assert original_receipt
    finally:
        _stop_node(first)

    assert (tmp_path / "stegverse-ecosystem-chat.db").exists()

    second = _start_node(port, tmp_path)
    try:
        recovered = _json_request(f"http://127.0.0.1:{port}/api/transitions/{transition_id}")
        assert recovered["transition_id"] == transition_id
        assert recovered["run_id"] == request_payload["transition_identity"]["run_id"]
        assert recovered["lifecycle_state"] == "COMPLETED"
        assert recovered["final_receipt_id"] == original_receipt
        assert recovered["sqlite_persisted"] is True
        assert recovered["storage_durable_across_restarts"] is True
        assert recovered["local_persistence_is_custody"] is False
    finally:
        _stop_node(second)
