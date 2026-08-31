# Organization Federation Rendezvous Service Gateway Mirror Handoff

Updated: 2026-08-31
Repository: StegVerse-org/LLM-adapter
State: ACTIVE_IMPLEMENTATION
Authority effect: NONE

## Goal

Provide the network rendezvous required for organization .github resident kernels to exchange exact governed Interlock/InTr carrier frames without making the Service Gateway a scheduler, WorkerCoordinator, execution authority, credential authority, route authority, or runtime owner.

## Topology

origin <ORG>/.github resident kernel
  -> exact HB-derived InTr carrier frame
  -> shared Service Gateway /api/org-federation/v1/frames
  -> durable destination-organized rendezvous
  -> destination <ORG>/.github outbound poll
  -> exact frame recovery/validation by destination kernel
  -> local org-control consumption / local admission
  -> governed response frame
  -> same rendezvous
  -> origin outbound poll

## Invariants

- frame transport grants no admission, execution, credential, routing, transition, receiving, publication, or release authority;
- Gateway does not interpret application semantics beyond exact frame/packet integrity and destination identity;
- destination organization must be one of the canonical 14 organization identities;
- write-once frame identity; conflicting duplicate bytes fail closed;
- resident poll is outbound-only;
- acknowledgement is transport observation only;
- GitHub token/runtime authority: NONE;
- credential authority: TV/TVC.

## Canonical surfaces

- llm_adapter/org_federation_rendezvous_api.py
- llm_adapter/combined_gateway.py
- tests/test_org_federation_rendezvous_api.py
- this handoff

## Runtime configuration

- STEGVERSE_ORG_FEDERATION_RENDEZVOUS_ENABLED=true
- STEGVERSE_ORG_FEDERATION_RENDEZVOUS_ROOT=<durable path>

Source/merge does not prove deployed/public activation or authentic resident polling.
