# StegDeploy Publication Mirror Handoff

## Canonical authority

```text
repository: StegVerse-org/LLM-adapter
credential_authority: TV/TVC
github_actions_publication_authority: NONE
github_token_production_authority: NONE
github_oidc_publication_authority: NONE
third_party_registry_required_for_production_continuity: false
runtime_image_source: LOCAL_BUILD
historical_ghcr_receipt_retained: true
canonical_runtime_consumer: StegVerse-org/LLM-adapter#18
primary_runtime: STEGDEPLOY_SOVEREIGN
third_party_hosting_policy: FALLBACK_ONLY
render_required_for_production_continuity: false
canonical_scheduler: resident sovereign heartbeat + healer-sovereign-scheduler-worker
healer_handoff: StegVerse-Labs/StegVerse-Healer/docs/HEALER_MIRROR_HANDOFF.md
```

## Hosted publication retirement

The following GitHub-hosted production/publication surfaces are superseded and removed under `LLMA-WORKFLOW-RETIRE-GITHUB-IMAGE-PUBLICATION-054`:

```text
.github/workflows/publish-portable-node-image.yml
.github/workflows/stegdeploy-image.yml
```

They previously used GitHub package credentials, `GITHUB_TOKEN`, OIDC/attestation authority, repository writeback, artifact transport, and GHCR publication/pull. Those mechanics are not compatible with the current StegVerse-only production boundary and are no longer a required continuity path.

No replacement GitHub workflow is authorized. TV/TVC protected credentials must not be exported into GitHub Actions to reproduce the retired behavior.

## Sovereign local runtime path

```text
source tree
-> Dockerfile
-> compose.stegdeploy.yaml local build
-> image stegverse/llm-adapter:local
-> pull_policy: never
-> scripts/stegdeploy_bootstrap.py
-> llm_adapter.deployed_gateway:app
-> locally running gateway
-> health proof
-> stegdeploy.deployment-receipt.v2
-> resident sovereign heartbeat / Healer observation
-> local core-node intake only when exact local image proof exists
```

`scripts/stegdeploy_bootstrap.py` does not generate provider, Master Records, review, or receipt credentials. Protected values are injected only by TV/TVC when an admitted capability needs them. Missing protected values leave optional privileged capabilities disabled/fail-closed.

`compose.stegdeploy.yaml` no longer requires GHCR for runtime continuity. The default image is locally built and registry pulling is disabled.

## Machine-owned continuation

Canonical Healer handoff records:

```text
owner: StegVerse-Labs/.github resident sovereign heartbeat
worker: healer-sovereign-scheduler-worker
process: healer-sovereign-scheduler-v1
manual execution allowed: false
StegDeploy relay: StegVerse-Labs/StegVerse-Healer/app/relay_stegdeploy_publication.py
local intake: StegVerse-org/core-node-runtime-demo/tools/stegdeploy_runtime_intake_local.py
release condition: admitted resident-heartbeat execution emits current no-token scheduler/local-image evidence
```

The Healer relay consumes materialized local state. Core-node intake accepts an exact digest only when that image is already present in the local Docker image store; it does not log in to or pull from GHCR. No chat/session competes with this machine-owned runtime lane.

## Historical GHCR evidence — retained, non-current authority

The last successful hosted publication remains immutable historical evidence only:

```text
image: ghcr.io/stegverse-org/llm-adapter:main
source commit: c9f561254ec5671c2329c3deb7ce0bfb511331ab
publication run: 31922279115
digest: sha256:a599fc154f4bde14ab9adc140feb1285b43af3da4ea9214804b007fb9ff38f19
receipt schema: stegdeploy.image-publication.v2
receipt state: PUBLISHED
receipt sha256: 67feb640e7be9489ca52438c9c7c609eeeae90c8e1e5409ea5c8fac6a38ef122
consumer pull verified: true
```

Retained locations:

```text
receipts/stegdeploy-image-publication.json
receipts/stegdeploy-image-verification-pull.log
status/stegdeploy-image-publication-readiness.json
```

This historical receipt does not authorize a fresh GHCR publication, provider execution, persistent deployment, custody, reconstruction, Site activation, downstream ingestion, release, or wallet/trade action.

## Released historical publication task

```text
task_id: LLMA-PUBLICATION-ACTIVATION-013
state: COMPLETE
claimant: none
canonical_issue: StegVerse-org/LLM-adapter#18
```

Task 013 proves a historical image was published successfully. It does not require keeping GitHub-hosted publication authority alive.

## Validation contract

Repository validation now proves:

1. both hosted publication workflows are absent;
2. local compose uses `stegverse/llm-adapter:local` and `pull_policy: never`;
3. bootstrap performs local build instead of registry pull;
4. bootstrap generates no protected credentials;
5. credential authority is TV/TVC;
6. historical GHCR receipt remains hash-valid and clearly historical;
7. provider/deployment/custody/Site authority remains false unless separately proven.

Validation surfaces:

```text
scripts/verify_stegdeploy_runtime.py
scripts/check_stegdeploy_image_receipt_retention.py
scripts/check_stegdeploy_image_publication_readiness.py
scripts/verify_goal4_full.py
```

## Remaining activation boundary

Local source/runtime readiness is not governed product activation. Live completion still requires the canonical resident carrier, admitted TV/TVC authority where needed, same-execution evidence, Master Records reconstruction where applicable, and downstream activation receipts.

MERGED INTO: `StegVerse-Labs/.github/handoffs/SHWP-HEALER-SOVEREIGN-SCHEDULER-001.json`, `StegVerse-Labs/StegVerse-Healer/docs/HEALER_MIRROR_HANDOFF.md`, and `StegVerse-org/LLM-adapter#18`.


## Coinbase SKAP/InTr primary-runtime binding — 2026-08-27

The sovereign StegDeploy path is now the canonical primary runtime carrier for the Coinbase SKAP/InTr public Service Gateway routes.

```text
container entrypoint: llm_adapter.deployed_gateway:app
durable staging root: /var/lib/stegverse
TVC no-value decision input: STEGVERSE_COINBASE_SKAP_TVC_DECISION_RECEIPT
credential authority: TV/TVC
render dependency: false
third-party hosting: fallback only
```

This change consumes the already-validated deployed-gateway Coinbase readiness/ingress handlers from LLM-adapter PR #204. It does not grant StegDeploy credential, decryption, provider, trading, governance, publication, or custody authority beyond bounded ciphertext staging already defined by the Service Gateway contract.

A StegVerse-owned runtime still must actually execute this image and expose the resulting HTTPS route before production route observation can be claimed.


## Primary-runtime merge evidence — 2026-08-27

```text
LLM-adapter PR #205
merge: 0ec44419ada49147feb1866abfa6fe4fb4d0bbb2
primary runtime: STEGDEPLOY_SOVEREIGN
render: FALLBACK_ONLY
production continuity depends on Render: false
```

Hosted validation for the exact source tree passed in Coinbase SKAP and repository-wide lanes. This establishes source/runtime-contract readiness only; a resident sovereign execution receipt is still required for activation.


## Native sovereign TLS runtime closure — 2026-08-27

The sovereign StegDeploy image now has an optional native TLS mode without adding a third-party ingress dependency.

```text
LLM-adapter PR #209
merge: 10a6f6247771b2a85b07f5f19810403c3acde513
TLS termination: UVICORN_NATIVE
TLS delivery: Docker Compose runtime secrets
certificate/private-key authority: TV/TVC
reverse proxy required: false
Render required: false
Cloudflare required: false
public route automatically claimed: false
```

The existing Healer scheduler target and resident worker can carry the path-only TLS configuration through merges `7aa88c39d5e46402e3368b5ebd81d27a773ce93d` and `583f3277c7eee9f0d12ab63280d31fbbc278aa85`.

This closes the software transport gap. Production still requires a real eligible sovereign node, runtime-materialized TV/TVC TLS files, native runtime execution, and independent public HTTPS/certificate-hostname observation.

## 2026-08-31 local resident-control bootstrap hook

StegDeploy now closes the post-health resident-runtime trigger seam locally.

After the gateway becomes healthy, `scripts/stegdeploy_bootstrap.py` searches only already-materialized local control-plane roots (explicit `STEGVERSE_ORG_CONTROL_ROOT`, adjacent repository layouts, or canonical local StegVerse roots). When it finds `StegVerse-Labs/.github/scripts/bootstrap_sovereign_runtime.py`, it invokes that bootstrap on the same sovereign substrate with `--skip-post-bootstrap-stegfin`.

Properties:
- no network source fetch;
- no GitHub Actions execution;
- no GitHub token runtime authority;
- no provider credential generation or forwarding;
- TV/TVC remains sole credential authority;
- the hook itself grants no claim/fence/runtime authority;
- the `.github` WorkerCoordinator remains the admission authority for G18 and all successor tasks;
- absence of a local control-plane checkout is recorded as `CONTROL_PLANE_NOT_MATERIALIZED` rather than fabricated activation.

The StegDeploy deployment receipt now carries `resident_control_plane_bootstrap`, making the deployment -> resident-bootstrap transition reconstructable.

Combined with the `.github` bootstrap successor binding, the intended live sequence is now:

```text
StegDeploy local deploy
-> gateway health
-> local .github sovereign bootstrap
-> G18 activation verification
-> immediate independent TVC/SKAP activation cycle
-> READY_FOR_OWNER_INGRESS when TVC predicates pass
```

## 2026-08-31 portable resident control-plane intake

StegDeploy no longer depends on an adjacent `.github` checkout. A local portable control-plane bundle may be supplied through:

`STEGVERSE_ORG_CONTROL_BUNDLE=/path/to/sovereign-control-plane.zip`

Before any resident bootstrap is attempted, StegDeploy:
- rejects missing bundles;
- rejects absolute paths, path traversal, and symlink entries;
- requires schema `stegverse.sovereign-control-plane-bundle/v1`;
- requires `network_fetch_required=false`;
- requires TV/TVC credential authority and GitHub-token runtime authority NONE;
- requires `bundle_grants_authority=false`;
- verifies the exact manifest file set, byte sizes, and SHA-256 digest of every bundled source file;
- materializes the verified source under `.stegdeploy/resident-control-plane`;
- requires `scripts/bootstrap_sovereign_runtime.py` to exist before returning the control root.

After verification, the already-merged post-health hook invokes the canonical resident bootstrap from that local materialization.

Validation:
- `tests/test_stegdeploy_control_bundle.py`

This makes the deployment chain independent of a GitHub runtime, registry pull, or repository adjacency while preserving `.github` as canonical source provenance and WorkerCoordinator as execution-admission authority.

## 2026-08-31 portable resident control-plane intake

StegDeploy no longer depends on an adjacent `.github` checkout. A local portable control-plane bundle may be supplied through:

`STEGVERSE_ORG_CONTROL_BUNDLE=/path/to/sovereign-control-plane.zip`

Before any resident bootstrap is attempted, StegDeploy:
- rejects missing bundles;
- rejects absolute paths, path traversal, and symlink entries;
- requires schema `stegverse.sovereign-control-plane-bundle/v1`;
- requires `network_fetch_required=false`;
- requires TV/TVC credential authority and GitHub-token runtime authority NONE;
- requires `bundle_grants_authority=false`;
- verifies the exact manifest file set, byte sizes, and SHA-256 digest of every bundled source file;
- materializes the verified source under `.stegdeploy/resident-control-plane`;
- requires `scripts/bootstrap_sovereign_runtime.py` to exist before returning the control root.

After verification, the already-merged post-health hook invokes the canonical resident bootstrap from that local materialization.

Validation:
- `tests/test_stegdeploy_control_bundle.py`

This makes the deployment chain independent of a GitHub runtime, registry pull, or repository adjacency while preserving `.github` as canonical source provenance and WorkerCoordinator as execution-admission authority.
