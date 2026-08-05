# HIL Automated Full Cycle

The workflow `.github/workflows/hil-automated-full-cycle.yml` executes the bounded HIL path without user-entered credentials or manual restart handling.

It generates separate masked review and publication credentials, starts the real gateway, submits exact PDF bytes with a provenance manifest, stops the process, restarts it against the same data path, verifies the preserved response, records `ACCEPT_PRIVATE`, performs append-only publication, verifies stable lookup, and emits `HIL-AUTOMATED-FULL-CYCLE-RECEIPT-v1`.

The receipt is scoped to `GITHUB_HOSTED_EPHEMERAL_FULL_CYCLE_PROOF`. It does not claim external production deployment, Master Record release, orchestration authority, endorsement, or execution authority.
