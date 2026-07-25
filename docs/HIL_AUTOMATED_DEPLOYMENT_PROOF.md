# HIL Automated Deployment Proof

This repository includes `.github/workflows/hil-automated-deployment-proof.yml` to remove manual credential setup and restart testing from the bounded proof path.

The workflow generates distinct masked review and publication credentials, runs the governed-cycle tests, starts the combined gateway against a declared durable directory, restarts the process against the same directory, rechecks intake and publication readiness, and emits `HIL-LIVE-READINESS-OBSERVATION-v2`.

The receipt scope is `GITHUB_HOSTED_EPHEMERAL_DEPLOYMENT_PROOF`. It proves automated configuration, separated credentials, process restart, durable-path reuse, and readiness behavior within the hosted runner. It does not claim external production deployment, publication authority, or Master Record append authority.
