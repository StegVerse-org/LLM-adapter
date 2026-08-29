# Evaluator InTr Shared Service Gateway Mirror Handoff

Updated: 2026-08-29
Repository: StegVerse-org/LLM-adapter
Issue: #216
Parent Service Gateway: #72
Branch: feature/evaluator-intr-service-gateway-216

## Goal

Expose the evaluator browser Interlock/InTr lane through the existing shared Service Gateway without creating a second public gateway or moving evaluator/receipt authority into LLM-adapter.

## Topology

Site browser
-> existing public Service Gateway /intr/evaluator
-> exact-byte loopback proxy
-> StegVerse-Labs/.github evaluator READ_REVIEW sovereign runtime
-> canonical StegOS Universal InTr receipts
-> exact response passthrough
-> browser manifest/receipt report

## Authority

credential_authority: TV/TVC
gateway_receipt_authority: false
gateway_evaluator_authority: false
gateway_review_authority: false
gateway_freeze_authority: false
gateway_execution_authority: false
github_token_runtime_authority: NONE
authority_effect: NONE

## Source

- llm_adapter/service_gateway_evaluator_intr.py
- llm_adapter/deployed_gateway.py
- llm_adapter/combined_gateway.py
- tests/test_service_gateway_evaluator_intr.py

The adapter is disabled by default. When enabled, its upstream must be exact same-host loopback HTTP at /intr/evaluator. It rejects Authorization and Cookie headers, non-canonical origins, non-InTr transport, missing opaque authority reference, mismatched body SHA-256, non-JSON payloads, authority transfer, and arbitrary remote proxy destinations.

The Gateway forwards only Content-Type and the three X-StegVerse InTr carrier headers. It returns runtime response bytes without interpreting or minting ingress/egress receipts.

## Runtime non-claims

Source/CI/merge do not prove:
- shared Gateway public HTTPS activation;
- evaluator adapter enabled;
- loopback evaluator listener active;
- authentic browser request;
- authentic ingress or egress receipt;
- manifest/receipt UI OBSERVED state.

Those remain runtime gates owned by Service Gateway #72, StegVerse-Labs/.github#431, StegOS#94, and Site#643.
