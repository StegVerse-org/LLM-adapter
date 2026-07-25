# Platform-Agnostic Runtime Contract

## Architectural rule

`LLM-adapter` does not depend on Render or any other hosting provider. The application consumes a provider-neutral process and storage contract. Provider-specific deployment records are historical evidence only.

## Required capabilities

A conforming runtime provides:

1. OCI-compatible container execution or an equivalent Python process runtime.
2. A configurable listening port through `PORT`.
3. A durable mount at `/var/lib/stegverse`, or an equivalent path supplied through `STEGVERSE_DATA_DIR`.
4. Runtime environment and secret injection without committing secrets to GitHub.
5. HTTPS termination directly or through a documented reverse proxy.
6. Access to `/health`, `/api/stegverse-node`, `/api/hil/readiness`, and `/api/hil/publication-readiness`.
7. Restart and redeploy operations that preserve the mounted data directory.
8. Exportable logs and controlled-cycle evidence.

No application code may depend on a provider API, provider metadata endpoint, provider filesystem convention, or provider-specific manifest.

## Canonical container execution

```sh
cp .env.platform-agnostic.example .env
# Replace both example credentials with distinct secret values.
docker compose up --build -d
curl -fsS http://127.0.0.1:8000/health
curl -fsS http://127.0.0.1:8000/api/hil/readiness
curl -fsS http://127.0.0.1:8000/api/hil/publication-readiness
```

Podman may use the same image and environment contract. Kubernetes, Nomad, a generic VM, or self-hosted infrastructure may translate the container, volume, port, and secret declarations without changing application code.

## Durable state

The entrypoint maps persistent state beneath `STEGVERSE_DATA_DIR`:

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

1. the same repository revision builds as an OCI image;
2. the image starts with only the documented environment contract;
3. readiness reports the expected Primary and prompt hashes;
4. state survives container replacement while retaining the same mounted volume;
5. no provider-specific code or configuration is necessary;
6. the resulting evidence identifies the repository revision, image digest, runtime contract version, storage persistence test, and readiness output.

## Authority boundary

Container build success is not deployment. Deployment is not durable-state proof. Readiness is not activation authority. A receiver receipt is not private acceptance. Private acceptance is not publication. Publication is not Master Record custody.
