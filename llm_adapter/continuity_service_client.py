"""Service-backed continuity search seam.

This module defines an optional HTTP continuity-search client. It fails closed
when no endpoint is configured and returns the same ContinuitySearchResult shape
used by the fixture continuity search path.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Mapping, Optional, Sequence

import requests

from .continuity_search import ContinuitySearchResult
from .retrieval_evidence import evidence_list_from_fixtures


class ContinuityServiceConfigurationError(RuntimeError):
    """Raised when continuity service lookup is requested without configuration."""


@dataclass(frozen=True)
class ContinuityServiceClient:
    """HTTP continuity-search client.

    Expected service response shape:

    {
      "freshness_status": "current|stale|superseded|revoked|mixed|unresolved",
      "evidence": [
        {
          "source_type": "receipt",
          "pointer": "master-records://...",
          "content_hash": "...",
          "retrieved_at": "...",
          "freshness": "current",
          "authority_scope": "read",
          "notes": "..."
        }
      ],
      "reconstruction_notes": ["..."]
    }
    """

    endpoint: Optional[str] = None
    api_key: Optional[str] = None
    timeout_seconds: int = 30

    def search(self, query: str) -> ContinuitySearchResult:
        endpoint = self.endpoint or os.getenv("STEGVERSE_CONTINUITY_SEARCH_URL")
        if not endpoint:
            raise ContinuityServiceConfigurationError(
                "STEGVERSE_CONTINUITY_SEARCH_URL is required for ContinuityServiceClient"
            )

        api_key = self.api_key or os.getenv("STEGVERSE_CONTINUITY_SEARCH_KEY")
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = "Bearer {}".format(api_key)

        response = requests.post(
            endpoint,
            headers=headers,
            json={"query": query},
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        body = response.json()
        return continuity_result_from_service_body(query=query, body=body)


def continuity_result_from_service_body(
    *,
    query: str,
    body: Mapping[str, Any],
) -> ContinuitySearchResult:
    """Convert service JSON into the local continuity result type."""

    evidence = evidence_list_from_fixtures(body.get("evidence", ()))
    notes = tuple(str(note) for note in body.get("reconstruction_notes", ()))
    return ContinuitySearchResult(
        query=query,
        evidence=evidence,
        freshness_status=str(body.get("freshness_status", "unresolved")),
        reconstruction_notes=notes,
    )


__all__ = [
    "ContinuityServiceClient",
    "ContinuityServiceConfigurationError",
    "continuity_result_from_service_body",
]
