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
