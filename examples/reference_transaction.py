#!/usr/bin/env python3
"""Offline reference transaction for stegverse.intr.anthropic.transport.v1.

No network access and no real credential. Demonstrates exact ingress binding,
provider normalization, Master Records handoff, and exact-response egress check.
"""
from __future__ import annotations

import json

from llm_adapter.anthropic_intr_executor import execute_governed_transaction
from llm_adapter.anthropic_intr_transport import (
    EgressDecision, IngressDecision, ProviderRequest, TransportConfig,
    compute_request_hash,
)


def main() -> int:
    draft = ProviderRequest(
        "anthropic", "claude-sonnet-5", "anthropic_messages",
        {"messages": [{"role": "user", "content": "Return exactly: pong"}], "max_tokens": 16},
        "0" * 64, "reference-tx-001", "reference-session-001",
    )
    request = ProviderRequest(
        draft.provider, draft.model, draft.endpoint_profile, draft.payload,
        compute_request_hash(draft), draft.transition_id, draft.session_id,
    )
    ingress = IngressDecision("ALLOW", request.request_hash, request.transition_id, "a" * 64, "carrier://reference")

    def transport(method, url, headers, body):
        assert method == "POST"
        assert url == "https://api.anthropic.com/v1/messages"
        return 200, {
            "id": "msg_reference",
            "model": request.model,
            "content": [{"type": "text", "text": "pong"}],
            "stop_reason": "end_turn",
            "stop_sequence": None,
            "usage": {"input_tokens": 8, "output_tokens": 2},
        }

    result = execute_governed_transaction(
        provider_request=request,
        ingress_decision=ingress,
        config=TransportConfig(),
        credential_resolver=lambda _: "offline-fixture-secret",
        transport=transport,
        master_records=lambda _: {"accepted": True, "authority_effect": "NONE", "receipt_id": "mr-offline-reference"},
        egress_resolver=lambda evidence: EgressDecision("ALLOW", evidence["response_hash"], "b" * 64),
    )
    print(json.dumps({
        "state": result.state,
        "transport_id": result.envelope["transport_id"],
        "request_hash": result.envelope["request_hash"],
        "response_hash": result.evidence["response_hash"],
        "authority_effect": result.authority_effect,
        "credential_material_present": False,
        "live_provider_execution": False,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
