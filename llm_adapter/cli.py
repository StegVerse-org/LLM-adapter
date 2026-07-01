"""Command-line entry point for governed LLM adapter fixtures."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping

from .governed_session import run_governed_session


def load_json(path: str) -> Mapping[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def run_session_fixture(fixture: Mapping[str, Any]) -> dict[str, Any]:
    """Run a governed session fixture through the full disabled-execution path."""

    provider_request = dict(fixture.get("provider_request", {}))
    if not provider_request:
        raise ValueError("fixture requires provider_request")

    return run_governed_session(
        provider=str(provider_request["provider"]),
        model=str(provider_request["model"]),
        messages=provider_request["messages"],
        candidate_output=str(fixture["candidate_output"]),
        evidence_fixtures=fixture.get("evidence", ()),
        purpose=str(provider_request.get("purpose", "answer")),
        allowed_sources=provider_request.get("allowed_sources", ("model_knowledge",)),
        policy=fixture.get("policy", {}),
        delegation=fixture.get("delegation", {}),
        temperature=float(provider_request.get("temperature", 0.0)),
        metadata=provider_request.get("metadata", {}),
        action_target=str(fixture.get("action_target", "unresolved")),
    ).to_dict()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a governed LLM adapter fixture.")
    parser.add_argument("fixture", help="Path to a governed session JSON fixture.")
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = run_session_fixture(load_json(args.fixture))
    except Exception as exc:  # pragma: no cover - CLI surface
        print(json.dumps({"status": "ERROR", "error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 1

    indent = 2 if args.pretty else None
    print(json.dumps(result, sort_keys=True, indent=indent))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
