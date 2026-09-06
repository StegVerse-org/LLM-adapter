# Anthropic / Claude Interlock-InTr Transport Mirror Handoff

Updated: 2026-09-06
Repository: `StegVerse-org/LLM-adapter`
Issue: `#288`
Branch: `feat/anthropic-intr-transport-288`
State: `SOURCE_IMPLEMENTED_LOCAL_VALIDATED / REPOSITORY_INTEGRATION_IN_PROGRESS`
Authority effect: `NONE_TRANSPORT_ONLY`

## Source of truth

This scoped handoff is subordinate to `LLM_ADAPTER_MIRROR_HANDOFF.md` and the organization runtime authority. It adds optional hosted-provider interoperability only. The canonical sovereign local model/runtime route remains independently sufficient and unchanged.

## Protocol

`stegverse.intr.anthropic.transport.v1`

```text
exact ProviderRequest
-> external Interlock/InTr ingress decision
-> exact ALLOW + request hash + transition ID + receipt hash + carrier binding
-> native Anthropic endpoint/profile verification
-> deterministic transport envelope
-> total native Messages API projection or fail closed
-> TV/TVC execution-scoped credential materialization
-> exactly one injected provider call; no retry and no fallback
-> order-preserving/lossless content-block normalization
-> response hash over blocks + normalized metadata
-> canonical/provider-native usage evidence
-> Master Records custody handoff without authority escalation
-> external Interlock/InTr egress decision
-> exact admitted response-hash verification
-> local EGRESS_ADMITTED report with authority_effect NONE_LOCAL
```

## Machine preflight

PASS for bounded source integration:

```text
canonical sovereign route replaced: false
hosted provider required: false
new heartbeat/oscillator: false
new scheduler/worker authority: false
new route authority: false
new transition authority: false
new credential authority: false
new custody authority: false
README impact: REQUIRED
```

## Current Anthropic contract reconciliation

The supplied package was internally green but contained time-sensitive provider drift. Before integration, the local source was reconciled against current Anthropic documentation observed 2026-09-06:

- `claude-opus-4-1-20250805` had retired on 2026-08-05 and is no longer admitted by default;
- `claude-opus-5` and `claude-sonnet-5` are current pinned direct-Claude API model IDs;
- Claude 4.6+ dateless IDs are pinned IDs, not moving aliases;
- Claude 5 uses adaptive thinking and rejects legacy manual thinking;
- Claude 4.6+ does not support assistant-message prefill;
- models released after Opus 4.6 reject non-default temperature/top-p and reject top-k; the adapter now fails closed locally rather than depending on provider rejection.

The default registry remains deliberately small. Unregistered models fail closed until their exact API semantics are explicitly admitted and tested.

## Credential boundary

```text
credential_authority: TV/TVC
credential_class: TV_TVC_PROVIDER_SECRET
credential material in envelope: false
credential material in wire body: false
credential material in provider response artifact: false
credential material in evidence/usage/custody: false
credential material in logs: false
```

The current v1 reference transport uses `x-api-key` as the injected credential header. The Claude API also supports bearer/WIF authorization, but that is not silently substituted into this profile; a separate explicitly admitted credential profile would be required.

## Source validation

```text
stdlib unittest: 90/90 PASS
compileall: PASS
schema JSON parse: PASS
offline reference transaction: PASS / NOT_LIVE
network calls during tests: NONE
```

## Live evidence boundary

Source/tests do not prove live Anthropic execution, valid/current TV/TVC credential materialization, resident WorkerCoordinator consumption, authentic Master Records custody/reconstruction, egress Interlock/InTr ALLOW, Ecosystem Chat activation, Site activation, or downstream publication.

## Remaining repository work

1. install the validated source/tests/schemas/capability/docs into the issue #288 branch;
2. update repository README in the same change set;
3. run exact-branch repository validation;
4. merge only on green validation and preserved authority boundaries;
5. do not tag/release or propagate to Site/Publisher/wikis unless an explicit release/capability gate authorizes it;
6. any later live provider use must enter existing TV/TVC, InTr, usage-evidence and Master Records paths.

## Completion accounting

```text
protocol design: COMPLETE
local source implementation: COMPLETE
provider-contract reconciliation: COMPLETE
local deterministic validation: 90/90 PASS
repository install: IN_PROGRESS
README reconciliation: PENDING_REPOSITORY_BRANCH
branch validation: PENDING
merge: PENDING
live Anthropic execution: NOT CLAIMED
product activation: NOT CLAIMED
scaffolding/stubs in production protocol source: 0
```
