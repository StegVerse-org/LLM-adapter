# StegDeploy: Render Replacement

This repository now contains a provider-neutral runtime path for the Ecosystem Chat gateway.

## What it replaces

The StegDeploy path removes the Render-specific build pipeline, Blueprint, pipeline-minute accounting, and Render hostname from the runtime contract. The gateway is packaged as a standard OCI container and launched through Docker Compose with persistent storage, generated local secrets, health verification, and a hashed deployment receipt.

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
