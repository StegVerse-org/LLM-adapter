"""StegVerse-owned loopback language-model runtime and discovery contract."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = ROOT / "models/stegverse-local-reference-v1"
MANIFEST_PATH = MODEL_DIR / "manifest.json"
WEIGHTS_PATH = MODEL_DIR / "weights.json"
TOKEN_RE = re.compile(r"[a-z0-9_-]+|[.!?]", re.I)
DEFAULT_URL = "http://127.0.0.1:18991"


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def load_model() -> tuple[dict[str, Any], dict[str, Any]]:
    manifest = json.loads(MANIFEST_PATH.read_text())
    weights = json.loads(WEIGHTS_PATH.read_text())
    expected = manifest["weights_sha256"]
    actual = hashlib.sha256((json.dumps(weights, indent=2, sort_keys=True) + "\n").encode()).hexdigest()
    if actual != expected:
        raise RuntimeError(f"local model weights hash mismatch:{actual}")
    return manifest, weights


def complete(prompt: str, *, max_tokens: int = 24) -> dict[str, Any]:
    manifest, weights = load_model()
    tokens = [x.lower() for x in TOKEN_RE.findall(prompt)]
    current = next((t for t in reversed(tokens) if t in weights["transitions"]), None)
    if current is None:
        current = sorted(weights["starts"], key=lambda t: (-weights["starts"][t], t))[0]
    generated: list[str] = []
    for _ in range(max_tokens):
        choices = weights["transitions"].get(current, {})
        if not choices:
            break
        nxt = sorted(choices, key=lambda t: (-choices[t], t))[0]
        if nxt == "<eos>":
            break
        generated.append(nxt)
        current = nxt
    output = " ".join(generated)
    receipt = {
        "protocol": "stegverse.local-runtime.v1",
        "model_id": manifest["model_id"],
        "model_class": manifest["model_class"],
        "input_hash": hashlib.sha256(prompt.encode()).hexdigest(),
        "output": output,
        "output_hash": hashlib.sha256(output.encode()).hexdigest(),
        "weights_sha256": manifest["weights_sha256"],
        "authority_attached": False,
        "execution_authority": False,
    }
    receipt["receipt_hash"] = canonical_hash(receipt)
    return receipt


def _get_json(url: str, timeout: float = 0.5) -> dict[str, Any] | None:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            if response.status != 200:
                return None
            value = json.loads(response.read())
            return value if isinstance(value, dict) else None
    except (OSError, urllib.error.URLError, ValueError):
        return None


def discover_local_runtime(candidates: tuple[str, ...] = (DEFAULT_URL, "http://127.0.0.1:11434")) -> dict[str, Any]:
    observations = []
    for base in candidates:
        steg = _get_json(base + "/v1/runtime-identity")
        if steg and steg.get("protocol") == "stegverse.local-runtime.v1":
            return {"state": "DISCOVERED", "runtime": "stegverse-local", "base_url": base, "identity": steg, "observations": observations}
        ollama = _get_json(base + "/api/tags")
        if ollama and isinstance(ollama.get("models"), list) and ollama["models"]:
            return {"state": "DISCOVERED", "runtime": "ollama", "base_url": base, "identity": {"protocol": "ollama", "models": [x.get("name") for x in ollama["models"]]}, "observations": observations}
        observations.append({"base_url": base, "reachable_conforming_runtime": False})
    return {"state": "NOT_FOUND", "observations": observations}


@dataclass
class LaunchedRuntime:
    process: subprocess.Popen[str]
    base_url: str
    launched_by_discovery: bool = True

    def stop(self) -> None:
        self.process.terminate()
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill()


def launch_reference_runtime(port: int = 18991, *, timeout: float = 8.0) -> LaunchedRuntime:
    process = subprocess.Popen([sys.executable, "-m", "llm_adapter.local_model_runtime", "serve", str(port)], cwd=ROOT, text=True)
    base = f"http://127.0.0.1:{port}"
    deadline = time.time() + timeout
    while time.time() < deadline:
        identity = _get_json(base + "/v1/runtime-identity")
        if identity and identity.get("protocol") == "stegverse.local-runtime.v1":
            return LaunchedRuntime(process, base)
        if process.poll() is not None:
            raise RuntimeError(f"local runtime exited early:{process.returncode}")
        time.sleep(0.1)
    process.terminate()
    raise RuntimeError("local runtime launch readiness timeout")


def ensure_local_runtime() -> tuple[dict[str, Any], LaunchedRuntime | None]:
    discovery = discover_local_runtime()
    if discovery["state"] == "DISCOVERED":
        return discovery, None
    launched = launch_reference_runtime()
    rediscovered = discover_local_runtime((launched.base_url,))
    if rediscovered["state"] != "DISCOVERED":
        launched.stop()
        raise RuntimeError("launched runtime was not rediscoverable")
    rediscovered["state"] = "LAUNCHED_AND_DISCOVERED"
    rediscovered["launch_reason"] = "no conforming local runtime discovered"
    return rediscovered, launched


def _serve(port: int) -> None:
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    manifest, _ = load_model()

    class Handler(BaseHTTPRequestHandler):
        def _send(self, code: int, value: dict[str, Any]) -> None:
            raw = json.dumps(value, sort_keys=True).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def log_message(self, *_: Any) -> None:
            return

        def do_GET(self) -> None:
            if self.path in {"/health", "/healthz"}:
                self._send(200, {"status": "OK", "state": "READY", "local": True, "authority_attached": False, "model": manifest["model_id"], "model_hash": manifest["weights_sha256"], "private_endpoint_only": True, "third_party_inference_required": False})
                return
            if self.path == "/v1/runtime-identity":
                self._send(200, {"protocol": "stegverse.local-runtime.v1", "runtime": "repository-owned-python-loopback", "model_id": manifest["model_id"], "weights_sha256": manifest["weights_sha256"], "network_required": False, "authority_attached": False})
                return
            if self.path == "/v1/models":
                self._send(200, {"object": "list", "data": [{"id": manifest["model_id"], "object": "model", "owned_by": "StegVerse"}], "models": [manifest]})
                return
            self._send(404, {"error": "not_found"})

        def do_POST(self) -> None:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length) or b"{}")
            if self.path == "/v1/completions":
                prompt = payload.get("prompt")
                if not isinstance(prompt, str) or not prompt.strip():
                    self._send(400, {"error": "prompt_required"})
                    return
                self._send(200, complete(prompt, max_tokens=min(int(payload.get("max_tokens", 24)), 64)))
                return
            if self.path != "/v1/chat/completions":
                self._send(404, {"error": "not_found"})
                return
            messages = payload.get("messages") or []
            prompt = "\n".join(str(item.get("content", "")) for item in messages if isinstance(item, dict))
            if not prompt.strip():
                self._send(400, {"error": "messages_must_contain_content"})
                return
            started = time.perf_counter()
            result = complete(prompt, max_tokens=min(int(payload.get("max_tokens", 24)), 64))
            latency_ms = round((time.perf_counter() - started) * 1000, 4)
            prompt_tokens = len(TOKEN_RE.findall(prompt))
            completion_tokens = len(TOKEN_RE.findall(result["output"]))
            usage = {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
                "latency_ms": latency_ms,
            }
            self._send(200, {
                "id": "chatcmpl-" + result["receipt_hash"][:20],
                "object": "chat.completion",
                "created": int(time.time()),
                "model": manifest["model_id"],
                "choices": [{"index": 0, "message": {"role": "assistant", "content": result["output"]}, "finish_reason": "stop"}],
                "usage": usage,
                "stegverse": {
                    "protocol": "stegverse.local-runtime.v1",
                    "model_hash": manifest["weights_sha256"],
                    "runtime_receipt_hash": result["receipt_hash"],
                    "training": {"external_training_service_required": False, "repository_local_weights": True},
                    "third_party_inference_required": False,
                    "authority_effect": "NONE",
                },
            })

    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) == 2 and args[0] == "serve":
        _serve(int(args[1]))
        return 0
    print(json.dumps(complete("governed inference"), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
