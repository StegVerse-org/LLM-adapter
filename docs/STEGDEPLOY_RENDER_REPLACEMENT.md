# StegDeploy: Render Replacement

This repository contains the canonical provider-neutral primary runtime path for the Ecosystem Chat / Service Gateway surface. Third-party hosting such as Render is fallback compatibility only.

## What it replaces

The StegDeploy path removes Render-specific build pipelines, Blueprint state, pipeline-minute accounting, and Render hostnames from the primary runtime contract. The gateway is packaged as a standard OCI container and launched through Docker Compose with persistent storage, generated local secrets, health verification, and a hashed deployment receipt.

## Autonomous deployment

On any Docker-compatible runtime, the complete deployment is one command:

```bash
python scripts/stegdeploy_bootstrap.py deploy
```

The bootstrap process:

1. creates protected runtime secrets when absent;
2. builds the gateway image from the repository;
3. creates the persistent data volume;
4. runs the custody worker once before startup;
5. starts the combined gateway;
6. waits for `/health` to return successfully; and
7. writes `.stegdeploy/deployment-receipt.json` with the source commit, image identifier, health result, durability declaration, and receipt hash.

No Render API, Render billing entitlement, Render Blueprint, or Render build minutes are required.

## Runtime ownership

The runtime remains provider-neutral. It can execute on a StegVerse-owned server, a development machine, a self-hosted runner, or any infrastructure capable of running OCI containers. Moving between those environments does not change the application image or deployment contract.

## Current authority posture

Provider execution, Master-Records custody, and external mutation remain disabled by default. Their credentials and endpoints can be supplied through environment variables without changing the image. The deployment receipt grants no execution, review, publication, provider, or custody authority.

## Files

- `Dockerfile` — hardened non-root OCI image with persistent data path and health check.
- `scripts/container-entrypoint.sh` — startup sequence for custody processing and gateway execution.
- `compose.stegdeploy.yaml` — provider-neutral service, volume, environment, and health definition.
- `scripts/stegdeploy_bootstrap.py` — autonomous build, launch, verification, stop, status, secret generation, and receipt creation.


## Primary versus fallback runtime policy

```text
primary runtime: StegDeploy on StegVerse-owned / sovereign OCI-capable substrate
fallback compatibility: Render or another third-party host
fallback authority: NONE
credential authority: TV/TVC
production continuity dependency on Render: false
```

The primary StegDeploy container starts `llm_adapter.deployed_gateway:app`, which includes the governed Ecosystem Chat, External Review, HIL, KnowledgeVault onboarding, and Coinbase SKAP/InTr Service Gateway routes.

Coinbase SKAP staging uses the same durable StegDeploy volume through:

```text
STEGVERSE_SERVICE_GATEWAY_STORAGE_ROOT=/var/lib/stegverse
```

and accepts only the no-value TVC decision receipt injected into:

```text
STEGVERSE_COINBASE_SKAP_TVC_DECISION_RECEIPT
```

Absence of that TVC receipt keeps Coinbase SKAP readiness fail-closed. StegDeploy does not generate provider credentials, SKAP private keys, or authorization receipts.

Render outages, quotas, billing state, deployment state, or hostname availability therefore must never block primary StegVerse runtime readiness.
