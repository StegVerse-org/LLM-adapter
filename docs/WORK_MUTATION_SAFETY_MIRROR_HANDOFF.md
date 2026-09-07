# Work Mutation Safety Mirror Handoff

Status: ACTIVE_IMPLEMENTATION
Repository: `StegVerse-org/LLM-adapter`
Task: `LLMA-WORK-MUTATION-SAFETY-320`
Issue: `#320`

## Authority

This scoped handoff is subordinate to `docs/LLM_ADAPTER_MIRROR_HANDOFF.md`, the StegVerse-Labs canonical work coordination system, existing Interlock/InTr transition authority, TV/TVC credential and route authority, the existing WorkerCoordinator/runtime owners, and Master Records custody/reconstruction.

The safety gate is validation-only. It grants no execution, transition, admission, route, credential, claim/fence, runtime, provider, publication, or custody authority.

## Installed safety boundary

Work-authored functional pull-request mutations are guarded at the repository mutation boundary by:

```text
scripts/validate_work_mutation_safety.py
.github/workflows/work-mutation-safety.yml
receipts/work-safety/*.json
```

A functional pull request must carry a fresh `stegverse.work-mutation-safety/v1` manifest in the same change set. The manifest must cover every functional changed path and must resolve the canonical handoff, task-registry reference, Master Records applicability, cross-task coordination, semantic reuse scan, active-owner collision review, and README impact.

Every newly added functional file must declare its semantic responsibility, nearest existing implementation or search result, and an explicit reuse decision. `CREATE_NEW` fails closed when an equivalent implementation is already known. `CREATE_NEW` also fails closed on an active-owner collision unless the manifest explicitly records intentional governed parallel versioning and a reconciliation reference.

The gate does not assert that the supplied semantic evidence is runtime truth. It structurally prevents Work from silently creating uncovered functional files or bypassing the required reuse/collision/README decisions.

## Existing responsibilities preserved

Do not duplicate or move into this gate:

- InTr / Interlock transition evaluation;
- TV/TVC credential or route authority;
- provider transport implementation;
- LLM identity or capability semantics;
- WorkerCoordinator / HeartBeat / resident runtime behavior;
- Master Records custody or reconstruction;
- live provider/runtime validation.

Those remain owned by their canonical components. This gate only blocks repository mutation when the pre-work safety record is incomplete or internally contradictory.

## README determination

`README_CHANGE_REQUIRED = NO` for this bounded change.

Reason: the installed gate changes repository development validation only. It does not change LLM-adapter runtime behavior, provider interfaces, ingress/egress semantics, governance or authority ownership, evidence meaning, runtime prerequisites, external capability meaning, or production failure behavior. This scoped handoff documents the development-control behavior itself.

## Release condition

Release only after the branch pull request passes:

1. the new Work Mutation Safety workflow;
2. unit tests for fail-closed semantic collision behavior;
3. existing repository validation applicable to the changed surfaces.

After merge, update `tasks/LLMA-WORK-MUTATION-SAFETY-320.json` to `COMPLETE_RELEASED` with merge and validation evidence. No Site, Publisher, admissibility-wiki, or stegguardian-wiki propagation is required unless this validation-only control is later promoted into externally meaningful capability semantics.
