# HIL Triggered Ephemeral Runtime Mirror Handoff

## Source of truth

```text
goal_id: LLMA-HIL-TRIGGERED-EPHEMERAL-RUNTIME-030
runtime_owner: StegVerse-Labs/.github#246
backend_owner: StegVerse-org/LLM-adapter
participant_surface_owner: StegVerse-Labs/Site
credential_authority: TV/TVC
github_token_runtime_authority: NONE
runtime_mode: TRIGGER_DRIVEN_EPHEMERAL
persistent_host_required: false
participant_machine_required: false
developer_machine_required: false
transport_authority_effect: false
```

This handoff corrects the superseded resident/always-on-host assumption for the HIL live-evidence lane. HIL does not require a permanently running WorkerCoordinator or a permanently hosted receiver. The bounded participant action creates a lease-scoped runtime opportunity and the runtime is released after the governed operation/evidence sequence.

## Canonical sequence

```text
user trigger: submit_response_packet
-> trigger admitted as non-authorizing bounded work
-> instantiate current HIL receiver source ephemerally
-> verify /api/hil/sovereign-receiver-profile = ACTIVE_SOVEREIGN_RECEIVER
-> verify /api/hil/readiness = READY with exact v1.1 identities
-> instantiate zero-credential lease-bound HTTPS tunnel
-> independently verify public profile/readiness through that tunnel
-> accept one governed response packet
-> preserve HIL-RECEIVER-RECEIPT-v2 / RECORDED / EXACT_BYTES_PERSISTED state
-> restart the receiver against the same admitted state root
-> prove the stored submission remains queryable and exact bytes retain the original SHA-256
-> release tunnel and runtime
-> continue package/receipt into existing TVC lifecycle
```

Historical StegGate tunnel-native operation is the architectural precedent: ephemeral public transport may supply reachability/capacity while retaining zero policy, execution, credential, publication, lifecycle, or custody authority. A historical tunnel endpoint never proves current liveness and every lease must be freshly resolved and verified.

## Installed bounded cycle

`.github/workflows/hil-triggered-ephemeral-cycle.yml` is the first executable controlled-cycle implementation of this corrected runtime model. It can be activated by an explicit workflow dispatch or by a bounded change to `control/hil-ephemeral-trigger.json`.

The workflow:

- checks out the current LLM-adapter source with persisted GitHub checkout credentials disabled;
- starts `llm_adapter.combined_gateway:app` only for the bounded cycle;
- uses a non-temporary workspace state root for process-restart continuity inside the cycle;
- launches a zero-credential Cloudflare quick tunnel as transport only;
- validates public sovereign profile and readiness before accepting work;
- waits for exactly one governed HIL submission;
- restarts the receiver and verifies status plus exact stored-byte SHA-256 from the persisted state;
- terminates the tunnel and receiver;
- uploads only bounded cycle evidence.

GitHub Actions may provide ephemeral compute capacity for this controlled cycle, exactly as the earlier tunnel-native StegGate proof did, but GitHub/GitHub Actions grants no HIL runtime authority. `github_token_runtime_authority=NONE` means the platform credential cannot authorize HIL execution/lifecycle decisions; it does not mean neutral transient compute capacity is forbidden.

## Current trigger

`control/hil-ephemeral-trigger.json` contains `HIL-EPHEMERAL-CYCLE-20260824-001`, action `submit_response_packet`. Merge of the workflow plus trigger file is intended to instantiate the first corrected ephemeral HIL runtime cycle automatically through the path-scoped push trigger.

## Evidence boundary

A successful workflow startup proves only trigger admission, ephemeral receiver startup, public HTTPS reachability, and exact readiness. Full controlled-cycle completion still requires one actual response packet to reach that live lease. The workflow then performs process restart and persisted-byte/hash verification before teardown.

The workflow does not perform private review, publication, Master Record release, or TVC lifecycle admission. Those remain separate governed transitions after the runtime evidence packet is preserved.
