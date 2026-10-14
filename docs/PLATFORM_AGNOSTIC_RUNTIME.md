# Platform-Agnostic Runtime Contract

## Architectural rule

`LLM-adapter` does not depend on Render or any other hosting provider. The application consumes a provider-neutral process and storage contract. Provider-specific deployment records are historical evidence only.

## Required capabilities

A conforming runtime provides:

1. A Python process runtime (the host-native launcher; no container framework).
2. A configurable listening port through `PORT`.
3. A durable mount at `/var/lib/stegverse`, or an equivalent path supplied through `STEGVERSE_DATA_DIR`.
4. Runtime environment and secret injection without committing secrets to GitHub.
5. HTTPS termination directly or through a documented reverse proxy.
6. Access to `/health`, `/api/stegverse-node`, `/api/hil/readiness`, and `/api/hil/publication-readiness`.
7. Restart and redeploy operations that preserve the mounted data directory.
8. Exportable logs and controlled-cycle evidence.

No application code may depend on a provider API, provider metadata endpoint, provider filesystem convention, or provider-specific manifest.

## Canonical native execution

```sh
cp docs/runtime-environment.example .env
# Replace both example credentials with distinct secret values.
set -a; . ./.env; set +a
python scripts/stegdeploy_native_gateway.py start --port 8000
python scripts/stegdeploy_native_gateway.py status
```

`start` closes when the gateway process is spawned. `status` observes health once; an unanswered probe is recorded as `NOT_AUTHENTICALLY_OBSERVED` with a reconciliation entrypoint and never gates the start. Before the gateway serves, the launcher runs the downstream-recording worker and the gateway forward-queue drain once each; neither waits on a receiver.

## Durable state

The launcher maps persistent state beneath its durable root (`STEGVERSE_DATA_DIR`), unless an operator names a store explicitly:

```text
/var/lib/stegverse/
  stegverse-ecosystem-chat.db
  stegverse-external-review.db
  hil/
    hil-intake.db
    originals/
    provenance/
```

`STEGVERSE_STORAGE_DURABLE_ACROSS_RESTARTS=true` is a runtime declaration, not proof. Proof requires a controlled submission, recorded hashes, a real restart or redeploy, and successful reconstruction of the same bytes and manifest afterward.

## Credential boundary

Private-review and publication credentials must be separate values:

```text
STEGVERSE_HIL_REVIEW_TOKEN
STEGVERSE_HIL_PUBLICATION_TOKEN
```

They must be injected by the runtime and never persisted in repository files, images, logs, receipts, or public responses. The host is transport and storage infrastructure; it does not become an authority source.

## Portability acceptance test

A runtime tranche passes portability only when:

1. the same repository revision starts on the native launcher with only the documented environment contract;
2. readiness reports the expected Primary and prompt hashes;
3. state survives a stop and start with the same durable root;
4. no provider-specific or container-framework code or configuration is necessary;
5. the resulting evidence identifies the repository revision, runtime contract version, storage persistence test, and readiness output.

PR validation may execute this contract in GitHub Actions, but the portability result is produced by the repository source, environment variables, health/readiness endpoints, and durable root rather than any hosting-provider service.

## Authority boundary

Process start is not deployment. Deployment is not durable-state proof. Readiness is not activation authority. A receiver receipt is not private acceptance. Private acceptance is not publication. Publication is not Master Record custody.
