# HIL InTr Shared Service Gateway Mirror Handoff

Updated: 2026-08-29
Repository: `StegVerse-org/LLM-adapter`
Parent HIL activation: `StegVerse-Labs/.github#246`

## Goal

Expose the existing HIL Universal InTr materialization ingress through the existing shared StegVerse Service Gateway without creating a second public gateway, a HIL-specific tunnel authority, or a new execution/receipt/custody authority.

## Topology

```text
StegOS Node browser outbox
-> https://stegverse.org/intr/materialization
-> shared Service Gateway HIL transport adapter
-> exact-byte same-host loopback HTTP
-> sovereign HIL InTr ingress /intr/materialization
-> INGRESS_ADMITTED receipt from receiving subsystem
-> event/resident HIL execution path
```

The Gateway is transport capacity only. It does not mint the HIL ingress receipt and does not interpret it as runtime activation.

## Source

```text
llm_adapter/service_gateway_hil_intr.py
llm_adapter/deployed_gateway.py
tests/test_service_gateway_hil_intr.py
```

## Runtime configuration

```text
STEGVERSE_HIL_INTR_ENABLED=true
STEGVERSE_HIL_INTR_UPSTREAM=http://127.0.0.1:<port>/intr/materialization
```

The upstream is fail-closed to same-host loopback HTTP and the exact `/intr/materialization` path. Arbitrary remote proxy destinations are rejected.

## Authority invariants

```text
credential_authority: TV/TVC
github_token_runtime_authority: NONE
gateway_receipt_authority: false
gateway_execution_authority: false
gateway_custody_authority: false
g18_completion_required: false
second_user_device_required: false
authority_effect: NONE
```

For `STEGOS_NODE_OUTBOX`, an `X-StegVerse-Authorization-Id` is rejected. For `TVC_RELAY_EGRESS`, a separate authorization id remains required. Payload SHA-256 and InTr transport/origin headers are verified before exact-byte forwarding.

## Non-claims

Source, CI, merge, or Gateway readiness do not prove:

- public Service Gateway runtime activation;
- loopback sovereign HIL ingress active;
- authentic Node delivery;
- `INGRESS_ADMITTED` receipt;
- WorkerCoordinator claim/fence;
- HIL receiver READY;
- exact PDF custody/reconstruction;
- TVC HIL lifecycle admission.

Those remain authentic runtime evidence gates.
