# HIL InTr Shared Service Gateway Mirror Handoff

Updated: 2026-08-29
Repository: `StegVerse-org/LLM-adapter`
Parent HIL activation: `StegVerse-Labs/.github#246`

## Goal

Use the existing shared StegVerse Service Gateway as the single public HTTPS surface for HIL without creating a second public gateway, HIL-specific tunnel authority, participant-operated host, or GitHub-hosted production runtime.

## Corrected runtime topology

The deployed Gateway already imports `llm_adapter.combined_gateway:app`. That application already mounts the canonical HIL v1.1 intake router and sovereign receiver profile. Therefore the production participant path does **not** require a second loopback HIL web receiver behind the Gateway.

```text
participant browser / Site
-> https://stegverse.org/api/hil/submissions
-> shared Service Gateway / deployed_gateway
-> existing canonical HIL v1.1 intake router
-> exact PDF + provenance + Universal InTr intent validation
-> durable /var/lib/stegverse/hil-v1.1 state
-> HIL-RECEIVER-RECEIPT-v2
-> HIL custody Interlock receipt chain
-> durable TVC HIL-lifecycle InTr queue
```

StegDeploy now declares:

```text
STEGVERSE_RUNTIME_PROFILE=sovereign-carrier
STEGVERSE_SOVEREIGN_STATE_DURABLE=true
STEGVERSE_SOVEREIGN_STATE_DIR=/var/lib/stegverse
```

`apply_sovereign_hil_receiver_profile()` consequently activates the already-mounted HIL intake and binds its state to `/var/lib/stegverse/hil-v1.1`, inside the existing durable StegDeploy volume. No second participant/developer machine and no second HIL HTTP process are required.

## Materialization-trigger compatibility path

The separate `/intr/materialization` adapter remains a non-authorizing compatibility path for the StegOS Node materialization trigger lane. It must not be confused with the actual PDF custody path. Its earlier literal loopback-forwarding topology is not required for participant HIL intake and must not be used to claim receiver activation.

```text
StegOS Node outbox trigger
-> /intr/materialization
-> non-authorizing materialization compatibility lane
-> WorkerCoordinator/runtime activation evidence when independently observed
```

The browser PDF remains transported only by the canonical HIL intake endpoint with its Universal InTr intent; the materialization trigger carries no PDF/provenance bytes.

## Source

```text
llm_adapter/combined_gateway.py
llm_adapter/deployed_gateway.py
llm_adapter/hil_intake_v1_1_api.py
llm_adapter/hil_sovereign_receiver_profile.py
llm_adapter/service_gateway_hil_intr.py
compose.stegdeploy.yaml
tests/test_hil_intake_api.py
tests/test_service_gateway_hil_intr.py
scripts/verify_stegdeploy_runtime.py
```

## Authority invariants

```text
credential_authority: TV/TVC
participant_intake_credential_requirement: NONE
github_token_runtime_authority: NONE
gateway_execution_authority: false
gateway_publication_authority: false
gateway_master_record_authority: false
g18_completion_required: false
second_user_device_required: false
third_party_runtime_required: false
```

The HIL receiver receipt proves exact intake/custody state only. It does not grant review, publication, Master Records, WorkerCoordinator claim/fence, or TVC lifecycle authority.

## What this source correction closes

- removes the false requirement for a second loopback HIL public receiver in the StegDeploy participant path;
- binds the already-built HIL receiver to durable sovereign Gateway state;
- keeps the participant endpoint on the same public Service Gateway surface;
- retains event-triggered / no-second-device / TV-TVC-only semantics;
- avoids a Docker container-to-host loopback dependency for actual PDF intake.

## Runtime evidence still required

Source/CI/merge do not prove the sovereign Gateway is currently running the corrected image. Authentic completion still requires direct observation of:

1. public `/api/hil/readiness` returning the active v1.1 receiver contract;
2. public `/api/hil/sovereign-receiver-profile` returning `ACTIVE_SOVEREIGN_RECEIVER`;
3. one exact participant-equivalent PDF submission returning `HIL-RECEIVER-RECEIPT-v2`;
4. durable exact-byte readback/reconstruction across controlled runtime restart/replacement;
5. TVC admission of the generated HIL lifecycle InTr queue;
6. WorkerCoordinator claim/fence evidence only where the resident activation/control lane requires it.

No lifecycle state is advanced from source validation alone.
