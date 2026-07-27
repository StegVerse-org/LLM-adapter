"""Run a bounded smoke test against a deployed StegVerse user-LLM endpoint."""

from __future__ import annotations

import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def _get_json(base_url: str, path: str) -> dict:
    request = Request(f"{base_url.rstrip('/')}{path}", headers={"Accept": "application/json"})
    with urlopen(request, timeout=10) as response:  # noqa: S310 - operator-provided endpoint
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    base_url = os.getenv("STEGVERSE_USER_LLM_BASE_URL")
    if not base_url:
        print("STEGVERSE_USER_LLM_BASE_URL is required", file=sys.stderr)
        return 2

    try:
        health = _get_json(base_url, "/healthz")
        readiness = _get_json(base_url, "/readyz")
        activation = _get_json(base_url, "/v1/user-llm/activation-proof")
    except HTTPError as exc:
        print(f"HTTP failure: {exc.code} {exc.reason}", file=sys.stderr)
        return 1
    except (URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
        print(f"Smoke test failed: {exc}", file=sys.stderr)
        return 1

    result = {
        "health": health.get("status"),
        "readiness": readiness.get("state"),
        "activation": activation.get("state"),
        "proof_hash": activation.get("proof_hash"),
        "authority_attached": activation.get("authority_attached"),
    }
    print(json.dumps(result, sort_keys=True))

    if result["health"] != "OK":
        return 1
    if result["readiness"] != "READY":
        return 1
    if result["activation"] != "ACTIVATED":
        return 1
    if result["authority_attached"] is not False:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
