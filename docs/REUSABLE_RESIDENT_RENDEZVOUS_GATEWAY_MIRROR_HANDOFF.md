# Reusable Resident Rendezvous Gateway Mirror Handoff

Updated: 2026-09-13
Repository: `StegVerse-org/LLM-adapter`
Goal Task: `GADI-RUNTIME-CLOSURE-001`
COSV: `10100000100000`
Reusable component: `RTC-RESIDENT-RENDEZVOUS-010`
Status: `SOURCE_MERGED_VALIDATED / DURABLE_RUNTIME_UNOBSERVED / RUNTIME_EVIDENCE_PENDING`

## Purpose

Extend the existing non-authorizing Service Gateway resident rendezvous rather than creating another gateway or transport. The gateway uses explicit registered consumer profiles while preserving the legacy `stegos_kv_intr_chain` contract as the default.

## Canonical source state

Reusable Service Gateway profile implementation is merged through PR #335 at merge commit `c120a2d148f5ff9fa99161b59b2f8f9930343023` after exact-head validation passed. This source state is shared by the existing Service Gateway; no second gateway, listener, scheduler, credential path, WorkerCoordinator, InTr authority, or user-verification implementation was created.

Historical PR #255 proposed projecting resident-rendezvous discovery metadata through `/api/stegverse-node`. Under Reusable Task Component reconciliation that projection is not required for GADI: the canonical Site client uses the direct consumer-scoped `/api/resident-rendezvous/v1/discovery` contract. PR #255 is therefore closed without merge rather than reviving optional orchestration.

## Profiles

`stegos_kv_intr_chain` preserves the existing exact resident request, request IDs, step allowlist, canonical node routing, and Node Receipt #1 provenance requirement for current request `003`. That legacy provenance rule is routing/provenance metadata and is not user verification.

`gadi_runtime_observation` accepts only the exact canonical `RESIDENT-OBSERVE-GADI-RUNTIME-001` inner request and requires a `transport-correlation:sha256:<digest>` outer correlation reference. The correlation is transport metadata only and proves no user identity or authority.

## Routing

Advertisements and discovery are consumer-scoped. Pending requests may be filtered by consumer. The GET poll accepts an optional consumer; absent an explicit selector, the gateway may resolve a single fresh advertisement already posted by the target node and otherwise retains the legacy default. The gateway remains `gateway_execution_authority=NONE`.

The GADI browser producer is merged in `StegVerse-Labs/Site` PR #1290 and uses the direct consumer-scoped discovery endpoint. The resident-side registered consumer is merged in `StegVerse-Labs/.github` PR #1724. These source links establish addressability only.

## Runtime boundary

A live rendezvous requires an authentic Service Gateway runtime with:

```text
STEGVERSE_RESIDENT_RENDEZVOUS_ENABLED=true
STEGVERSE_RESIDENT_RENDEZVOUS_ROOT=<durable runtime root>
```

StegDeploy source profiles configure those values on the sovereign Gateway path, but no current durable Gateway runtime receipt, public resident-rendezvous route observation, fresh `gadi_runtime_observation` advertisement, request-store event, resident fetch, GADI consumption receipt, or correlated acknowledgement has been observed.

The first unresolved reusable-component runtime predicate is therefore:

`CURRENT_DURABLE_SERVICE_GATEWAY_RESIDENT_RENDEZVOUS_RUNTIME_OBSERVED`

followed by:

`CURRENT_GADI_DISCOVERY_AVAILABLE -> REQUEST_STORED -> RESIDENT_FETCH -> GADI_CONSUMPTION -> CORRELATED_ACK`

Source merge, CI, Site deployment, historical StegGate tunnel evidence, and GitHub-hosted heartbeat validation do not satisfy these predicates.

## Authority

KV/SKAP Vault remains sole user-verification authority. Node refs and Node Receipt provenance are routing/provenance data only. WorkerCoordinator retains claim/fence authority; Interlock/InTr retains state-transition/admission authority; TV/TVC retains credential/provider/release authority; Master Records retains custody/reconstruction. HeartBeat remains observability/timing/freshness only. GitHub remains source/evidence coordination only. This component grants none of those authorities.

## Evidence boundary

Merged source and CI validate profile isolation, exact inner-request validation, consumer-scoped discovery/fetch, transport-only correlation, legacy compatibility, and non-authorizing gateway behavior. Authentic resident advertisement, request delivery, ACK, GADI consumption, InTr admission, WorkerCoordinator claim/fence, defensive execution, effect observation, and reconstruction remain runtime evidence predicates.

## Next admissible work

Do not add another rendezvous implementation. Observe an existing durable Service Gateway instance first. Only after a current `gadi_runtime_observation` advertisement yields exactly one `AVAILABLE` routing node may the exact canonical GADI request be submitted once. Blind retry remains forbidden for ambiguous submission outcomes.

If authentic local resident delivery is observed first, use that path instead; `RTC-RESIDENT-RENDEZVOUS-010` is conditional, not mandatory.

## Manual work

None.
