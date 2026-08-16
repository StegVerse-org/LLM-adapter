# StegDeploy Publication Mirror Handoff

## Canonical source of truth

```text
.github/workflows/stegdeploy-image.yml
receipts/stegdeploy-image-publication.json
receipts/stegdeploy-image-verification-pull.log
status/stegdeploy-image-publication-readiness.json
tasks/LLMA-PUBLICATION-ACTIVATION-013.json
data/llm-adapter-orchestration-state.json
StegVerse-org/LLM-adapter#18
StegVerse-Labs/StegVerse-Healer/docs/HEALER_MIRROR_HANDOFF.md
```

Live Git history, workflow jobs and logs, the current committed v2 receipt, and its matching readiness projection supersede earlier snapshots. The older August 4 digest remains historical evidence but is not the current publication receipt.

## Released publication task

```text
task_id: LLMA-PUBLICATION-ACTIVATION-013
claim_state: COMPLETE
claimant: none
released_at: 2026-08-04T21:01:00-05:00
canonical_issue: StegVerse-org/LLM-adapter#18
scheduler_owner: StegVerse-Labs/StegVerse-Healer
```

## Current retained canonical image evidence

The most recent committed publication evidence was produced by successful `StegDeploy image` run `31922279115` for source commit `c9f561254ec5671c2329c3deb7ce0bfb511331ab` and retained on main by commit `1920f54dbc77d507cd5344c4aeff0f6a8917cce9`.

```text
image: ghcr.io/stegverse-org/llm-adapter:main
source commit: c9f561254ec5671c2329c3deb7ce0bfb511331ab
publication run: 31922279115
publication attempt: 1
digest: sha256:a599fc154f4bde14ab9adc140feb1285b43af3da4ea9214804b007fb9ff38f19
receipt schema: stegdeploy.image-publication.v2
receipt state: PUBLISHED
receipt blockers: []
receipt sha256: 67feb640e7be9489ca52438c9c7c609eeeae90c8e1e5409ea5c8fac6a38ef122
consumer pull verified: true
repository retained: true
readiness state: READY
readiness observed digest: sha256:a599fc154f4bde14ab9adc140feb1285b43af3da4ea9214804b007fb9ff38f19
provider execution authorized: false
persistent deployment authorized: false
custody authorized: false
site activation authorized: false
```

The receipt records successful registry login, build/publish, attestation, and fresh verification pull. The matching readiness projection remains non-authorizing and fail-closed for provider execution, persistent deployment, custody, and Site activation.

## Superseded publication snapshot

The August 4 publication remains historical evidence:

```text
source commit: f7ca640d44a5e7703e9d3f599717375bfae2e183
publication run: 30967973138
digest: sha256:ae309681c4b1411c39860bcb349acc5cf727b70f8876a9e61fccfbb9e767a901
receipt sha256: d70f19a0a3afd9a34f313b3e0a4959e3343b00194c86fd85e3cdec5b3c0a7d87
state: SUPERSEDED_BY_LATER_SUCCESSFUL_COMMITTED_RECEIPT
```

It must not be used as the current digest after later successful publication evidence was committed. This correction reconciles the handoff with live repository state; it does not authorize a new publication or alter runtime authority.

## Stable runtime-only trigger

PR #116 established the runtime-affecting publication trigger surfaces:

```text
Dockerfile
pyproject.toml
llm_adapter/**
scripts/container-entrypoint.sh
compose.stegdeploy.yaml
.github/workflows/stegdeploy-image.yml
```

Documentation, receipts, status projections, and validation-only scripts do not themselves establish runtime/provider authority. Explicit workflow dispatch remains a repository publication mechanism; managed recurrence remains owned by StegVerse-Healer until that surface is separately classified under the workflow-minimization program.

## Healer observer

```text
repository: StegVerse-Labs/StegVerse-Healer
workflow: .github/workflows/stegdeploy-publication-relay.yml
state: BLOCKED
observed result: HTTP 403
release condition: HEALER_GH_TOKEN creates the bounded workflow-dispatch event without exposing the token
effect on completed publication: none
```

This historical observer description does not make a non-TV/TVC token production/runtime authority. Credential/route authority for StegVerse runtime remains TV/TVC, and workflow/token remediation must classify this publication recurrence separately rather than silently expanding it.

## Remaining activation boundary

Publication is not provider execution, persistent deployment, custody, reconstruction, Site activation, downstream ingestion, release authority, or sovereign platform retirement. All corresponding authority projections in the current readiness record remain false.

Issue `StegVerse-org/LLM-adapter#18` owns consumption only after its machine-observable authority boundaries clear:

```text
authorized provider configuration and scoped execution grant
persistent endpoint
authenticated Master Records custody configuration
```

## Consolidation state

The publication task remains released. The current retained receipt/readiness pair is the authoritative publication evidence; the earlier fixed-digest snapshot is superseded. No provider/runtime authority is inferred from this correction.

MERGED INTO: `StegVerse-org/LLM-adapter#18` and the currently documented StegVerse-Healer publication-continuation surface, subject to the active StegVerse-only workflow/token-remediation program.
