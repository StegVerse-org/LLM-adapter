# Reusable Resident Rendezvous Gateway Mirror Handoff

Updated: 2026-09-13
Repository: `StegVerse-org/LLM-adapter`
Goal Task: `GADI-RUNTIME-CLOSURE-001`
COSV: `10100000100000`
Reusable component: `RTC-RESIDENT-RENDEZVOUS-010`
Status: `SOURCE_IMPLEMENTED / VALIDATION_PENDING / RUNTIME_EVIDENCE_PENDING`

## Purpose

Extend the existing non-authorizing Service Gateway resident rendezvous rather than creating another gateway or transport. The gateway now uses explicit registered consumer profiles while preserving the legacy `stegos_kv_intr_chain` contract as the default.

## Profiles

`stegos_kv_intr_chain` preserves the existing exact resident request, request IDs, step allowlist, canonical node routing, and Node Receipt #1 provenance requirement for current request `003`. That legacy provenance rule is not promoted into user verification.

`gadi_runtime_observation` accepts only the exact canonical `RESIDENT-OBSERVE-GADI-RUNTIME-001` inner request and requires a `transport-correlation:sha256:<digest>` outer correlation reference. The correlation is transport metadata only and proves no user identity or authority.

## Routing

Advertisements and discovery are consumer-scoped. Pending requests may be filtered by consumer. The GET poll accepts an optional consumer; absent an explicit selector, the gateway may resolve a single fresh advertisement already posted by the target node and otherwise retains the legacy default. The gateway remains `gateway_execution_authority=NONE`.

## Authority

KV/SKAP Vault remains sole user-verification authority. Node refs and Node Receipt provenance are routing/provenance data only. WorkerCoordinator retains claim/fence authority; Interlock/InTr retains state-transition/admission authority; TV/TVC retains credential/provider/release authority; Master Records retains custody/reconstruction. This source change establishes none of those runtime events.

## Evidence boundary

Source and CI validate profile isolation, exact inner-request validation, consumer-scoped discovery/fetch, transport-only correlation, legacy compatibility, and non-authorizing gateway behavior. Authentic resident advertisement, request delivery, ACK, GADI consumption, InTr admission, WorkerCoordinator claim/fence, defensive execution, effect observation, and reconstruction remain runtime evidence predicates.

## Manual work

None.
