# StegDeploy: Render Replacement

This repository contains the canonical provider-neutral primary runtime path for the Ecosystem Chat / Service Gateway surface. Third-party hosting such as Render is fallback compatibility only.

## What it replaces

The StegDeploy path removes Render-specific build pipelines, Blueprint state, pipeline-minute accounting, and Render hostnames from the primary runtime contract. The gateway runs as a host-native Python process with persistent storage and a hashed start receipt. The container path (Dockerfile, Compose files, `scripts/stegdeploy_bootstrap.py`, `scripts/container-entrypoint.sh`) has been retired; no container framework is required.

## Autonomous deployment

The complete deployment is one command:

```bash
python scripts/stegdeploy_native_gateway.py start
```

The launcher:

1. refuses hosted runtimes;
2. binds durable stores beneath the durable root;
3. spawns the gateway process, which runs the downstream-recording worker and the gateway forward-queue drain once each and then serves `llm_adapter.deployed_gateway:app`; and
4. writes the start receipt (`LOCAL_NATIVE_GATEWAY_STARTED`) when the process is spawned.

Health is not awaited. `python scripts/stegdeploy_native_gateway.py status` observes it once; an unanswered probe is recorded as `NOT_AUTHENTICALLY_OBSERVED` with that command as the reconciliation entrypoint. In the resident stack, StegVerse-Labs `scripts/activate_resident_stack.py` materializes the organization control bundle and invokes this launcher.

No Render API, Render billing entitlement, Render Blueprint, or Render build minutes are required.

## Runtime ownership

The runtime remains provider-neutral. It can execute on a StegVerse-owned server, a development machine, a self-hosted runner, or any infrastructure that runs Python. Moving between those environments does not change the application source or deployment contract.

## Current authority posture

Provider execution, optional downstream Master Records recording, and external mutation remain disabled by default. Their credentials and endpoints can be supplied through environment variables without changing the source. The start receipt grants no execution, review, publication, provider, or custody authority.

## Files

- `scripts/stegdeploy_native_gateway.py` — host-native start, serve, status and stop; start receipt; TLS material validation.
- `scripts/verify_stegdeploy_runtime.py` — asserts the native contract and that the retired container paths stay absent.

## Primary versus fallback runtime policy

```text
primary runtime: StegDeploy host-native launcher on StegVerse-owned / sovereign substrate
fallback compatibility: Render or another third-party host
fallback authority: NONE
credential authority: TV/TVC
production continuity dependency on Render: false
```

The primary StegDeploy process serves `llm_adapter.deployed_gateway:app`, which includes the governed Ecosystem Chat, External Review, HIL, KnowledgeVault onboarding, and Coinbase SKAP/InTr Service Gateway routes.

Coinbase SKAP staging uses the same durable StegDeploy root through:

```text
STEGVERSE_SERVICE_GATEWAY_STORAGE_ROOT=<durable root>
```

and accepts only the no-value TVC decision receipt injected into:

```text
STEGVERSE_COINBASE_SKAP_TVC_DECISION_RECEIPT
```

Absence of that TVC receipt keeps Coinbase SKAP readiness fail-closed. StegDeploy does not generate provider credentials, SKAP private keys, or authorization receipts.

Render outages, quotas, billing state, deployment state, or hostname availability therefore must never block primary StegVerse runtime readiness.
