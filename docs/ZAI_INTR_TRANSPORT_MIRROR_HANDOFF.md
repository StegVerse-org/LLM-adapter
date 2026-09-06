# Z.ai Interlock/InTr Transport Mirror Handoff

Updated: 2026-09-06
Repository: `StegVerse-org/LLM-adapter`
Issue: `#276`
Branch: `feat/zai-intr-transport-276`
State: `SOURCE_IMPLEMENTED / VALIDATION_AND_MERGE_PENDING`
Authority effect: `NONE_TRANSPORT_ONLY`

## Source of truth

This is the scoped continuation record for `LLMA-ZAI-INTR-TRANSPORT-276`. It is subordinate to `LLM_ADAPTER_MIRROR_HANDOFF.md`, the organization runtime authority in `StegVerse-Labs/.github/docs/ORG_MIRROR_HANDOFF.md`, and the canonical resident carrier / Interlock/InTr authority split.

The existing canonical sovereign local route remains independently sufficient and unchanged. This lane is optional hosted-provider interoperability only.

## Machine preflight

PASS for bounded source implementation with these constraints:

```text
canonical sovereign route replaced: false
new heartbeat/oscillator: false
new WorkerCoordinator/scheduler: false
new route authority: false
new transition authority: false
new credential authority: false
new custody authority: false
GitHub token runtime authority: false
provider output authority: NONE
README impact: REQUIRED_AND_SATISFIED
```

README change is required because this lane adds provider-interface, transport, failure, credential-boundary, and egress-governance semantics. That README change is included in this branch.

## Protocol

Protocol identifier:

`stegverse.intr.zai.transport.v1`

Canonical sequence:

```text
exact ProviderRequest
-> contemporaneous Interlock/InTr ingress evaluation
-> DENY: no transport / no provider call
-> ALLOW: bind transition_id + exact request_hash + ingress receipt hash + carrier ref
-> TV/TVC resolves provider credential outside serialized artifacts
-> Z.ai OpenAI-compatible transport
-> provider response with authority_effect NONE
-> retain request/response/transport evidence without credential material
-> separate Interlock/InTr egress evaluation
-> only an admitted downstream transition may create a consequence/state change
```

The ingress ALLOW is not standing authority. It admits only the exact request hash and transport envelope. The provider response cannot reuse ingress authority as egress authority.

## Official Z.ai endpoint profiles

Observed from official Z.ai documentation on 2026-09-06:

```text
general: https://api.z.ai/api/paas/v4
coding:  https://api.z.ai/api/coding/paas/v4
```

The implementation allowlists only these base URLs and sends OpenAI-compatible chat completions to `/chat/completions`.

Endpoint selection is part of the admitted envelope. A runtime configured for one profile cannot execute an envelope admitted for the other.

## Credential boundary

Hosted Z.ai execution requires a provider credential, but this transport does not own or persist that credential.

```text
credential_authority: TV/TVC
credential_class: TV_TVC_PROVIDER_SECRET
credential serialized in envelope: false
credential serialized in evidence: false
credential serialized in response metadata: false
```

The `ZAIHTTPTransport` receives credential material only at execution time from the existing authority path. No environment variable, repository secret, workload artifact, contribution artifact, receipt, or handoff is made credential authority by this implementation.

## Implemented source

```text
llm_adapter/zai_intr_transport.py
schemas/zai-intr-transport-envelope.schema.json
tests/test_zai_intr_transport.py
tasks/LLMA-ZAI-INTR-TRANSPORT-276.json
docs/ZAI_INTR_TRANSPORT_MIRROR_HANDOFF.md
README.md
```

## Fail-closed predicates

1. ingress disposition must equal exact `ALLOW`;
2. ingress receipt must be an exact lowercase SHA-256;
3. ProviderRequest provider must explicitly identify Z.ai;
4. ProviderRequest hash must equal the admitted envelope request hash;
5. endpoint base URL must be one of the two approved official Z.ai profiles;
6. runtime endpoint profile must equal the profile admitted in the envelope;
7. credential class must remain `TV_TVC_PROVIDER_SECRET` under `TV/TVC`;
8. transport envelope must retain `authority_effect=NONE`;
9. transport result must retain `egress_intr_required=true`;
10. credential material must never be serialized into envelope/evidence/response metadata.

## Evidence semantics

Source tests and repository validation can prove deterministic transport binding and fail-closed behavior. They do not prove:

- live Z.ai execution;
- valid/current TV/TVC credential materialization;
- route admission for a production workload;
- canonical resident WorkerCoordinator execution;
- provider-usage Master Records custody/reconstruction;
- egress InTr ALLOW;
- Ecosystem Chat activation;
- Site activation or downstream publication.

## README completeness

README change is mandatory in this same change set because the new protocol changes optional provider interface semantics and explicitly adds two-stage ingress/egress governance around an external provider call. The branch README contains those semantics and associated validation command.

## Remaining work

1. repository validation on the exact PR head;
2. merge only if validation and authority-boundary checks pass;
3. no live-provider or activation claim from merge;
4. separately governed runtime observation may later exercise this lane only if a current task admits Z.ai as an optional source and TV/TVC supplies the required credential;
5. any authentic provider usage must enter the existing Master Records provider-usage custody/reconstruction lane;
6. downstream Site/Publisher/wiki propagation occurs only when a capability/release gate explicitly requires it.

## Completion accounting

```text
protocol design: COMPLETE
source implementation: COMPLETE
schema: COMPLETE
deterministic tests: IMPLEMENTED / EXECUTION PENDING
README: COMPLETE IN BRANCH
PR validation: PENDING
merge: PENDING
live Z.ai execution: NOT CLAIMED
product activation: NOT CLAIMED
scaffolding/stubs in protocol files: 0
```
