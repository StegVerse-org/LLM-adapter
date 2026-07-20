# Render-independent Ecosystem Chat runtime

This runtime removes Render-specific build and startup requirements from the Ecosystem Chat gateway.

## Runtime contract

- Build from the repository `Dockerfile`.
- Start through `scripts/start_gateway.sh`.
- Serve HTTP on `PORT` (default `8080`).
- Expose `/health` for readiness and liveness checks.
- Run the custody worker once before the HTTP process starts.
- Persist SQLite state beneath `/var/lib/stegverse`.
- Run as the unprivileged `stegverse` user.
- Keep provider, external mutation, and Master-Records authority disabled unless separately configured.

## Portable execution

`compose.yaml` is the reference sovereign runtime definition. It can run on any Docker-compatible host without changing application code or relying on Render Blueprints, Render pipeline minutes, or provider-specific build controls.

## Authority posture

The default composition grants no provider authority, no external mutation authority, and no remote custody authority. Enabling those capabilities requires explicit environment configuration and remains subject to the gateway's existing validation and receipt rules.

## Replacement boundary

Render is now an optional adapter rather than the runtime owner. The portable container, startup contract, persistent data path, and health check are authoritative for future deployment targets.
