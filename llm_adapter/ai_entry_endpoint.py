"""Endpoint packaging scaffold for the StegVerse AI Entry interim backend.

This is a pure function interface suitable for wrapping with HTTP later. It
keeps the current build non-networked and side-effect free.
"""
from __future__ import annotations

from typing import Any

from llm_adapter.ai_entry_backend_service import build_ai_entry_backend_response


def handle_ai_entry_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a backend response for a Site AI Entry request payload.

    Expected payload shape:
        {"message": "..."}

    The handler accepts missing or non-string messages by normalizing them to an
    empty string. It performs no live calls and returns the same bounded preview
    response shape as the interim backend service.
    """
    raw_message = payload.get("message", "") if isinstance(payload, dict) else ""
    message = raw_message if isinstance(raw_message, str) else ""
    response = build_ai_entry_backend_response(message).to_dict()
    response["endpoint"] = {
        "mode": "pure_function_preview",
        "http_server_started": False,
        "live_calls_performed": False,
        "side_effects_performed": False,
    }
    return response


def main() -> int:
    import json
    import sys

    message = " ".join(sys.argv[1:])
    print(json.dumps(handle_ai_entry_payload({"message": message}), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
