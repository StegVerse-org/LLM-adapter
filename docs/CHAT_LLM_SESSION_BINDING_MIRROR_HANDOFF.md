# Chat LLM Session Binding Mirror Handoff

## Source of truth

This is the authoritative continuation record for the released provider-neutral session-binding layer established by issue `StegVerse-org/LLM-adapter#105`, PR #106, and task `LLMA-CHAT-SESSION-BINDING-010`. Repository-wide orchestration remains governed by `docs/LLM_ADAPTER_MIRROR_HANDOFF.md` and `data/llm-adapter-orchestration-state.json`.

## Released goal

Both full-function LLM profiles use one deterministic provider-neutral session contract:

```text
profile + messages + requested features + candidate tools + source metadata
-> profile validation
-> message and capability validation
-> source-policy decisions
-> fail-closed grounding gate
-> deterministic provider-neutral envelope
-> provider candidate response
-> citation / fact-label / tool-status / authority validation
-> candidate acceptance or rejection receipt
```

This layer prepares and validates LLM interactions. It does not call an LLM provider.

## Product behavior and authority boundary

```text
Ecosystem Chat: admitted source classes allowed by its profile; candidate tools only
VA Claims Chat: official va.gov/*.va.gov factual sources plus privacy-PASS, consent-bound, hash-bound user records
required denied source: BLOCKED_SOURCE_POLICY before provider envelope creation
privacy_guarded_dispatch: required before VA Claims provider transmission
provider configuration attached: false
provider permission requested: false
provider call performed: false
tools executed: false
custody submitted: false
Site mutated: false
filing/publication/deployment/activation: false
provider-neutral envelope readiness != provider execution
candidate acceptance != authority or admissibility
```

Candidate responses must cite only admitted sources, use exact fact labels, cite declared factual claims, call only declared candidate tools, mark tools `CANDIDATE_NOT_EXECUTED`, preserve `side_effects_executed=false`, and preserve `authority_claimed=false`.

## Authoritative implementation

```text
llm_adapter/chat_session_binding.py
contracts/chat-llm-session-envelope.schema.json
tests/test_chat_session_binding.py
scripts/verify_chat_session_binding.py
tasks/LLMA-CHAT-SESSION-BINDING-010.json
receipts/chat-llm-session-binding-validation.json
docs/CHAT_LLM_SESSION_BINDING_MIRROR_HANDOFF.md
```

The implementation hashes the profile manifest, source metadata, normalized request projection, provider-neutral envelope, candidate projection, preparation receipt, and candidate validation receipt. No source body, credential, provider token, raw private document, or rejected PII is required by the contract.

## Historical release evidence

The original release remains valid historical compatibility evidence and is not rewritten by workflow consolidation:

```text
implementation PR: #106
validated head: 45ba9cabcca412836a51ee6b5a4b2342b29957d9
merge commit: 5ee90dd1f1cc3d6b20ecb3bce3991d8b59d869e5
historical workflow run: 30929473927
Python 3.9: PASS
Python 3.11: PASS
Python 3.12: PASS
tests per runtime: 17 PASS
receipt generation per runtime: PASS
historical artifact: 8900506930
artifact digest: sha256:5458d91baf79c4287b25034f58e6f174f27e64032837483229cb9597cbc307b3
retained receipt: receipts/chat-llm-session-binding-validation.json
retained receipt commit: 66222a09d05377727f0273674ca29917ebcbc99a
receipt hash: b1f9f56e8dc087ee04c49a011d351855a762030e2886d484def025a29e2e09b0
```

Validated release result remains:

```text
state: PASS
Ecosystem session: READY_FOR_PROVIDER_BINDING
Claims session: READY_FOR_PROVIDER_BINDING
Claims source mode: official VA only
Required non-VA Claims source: BLOCKED_SOURCE_POLICY
Provider envelope created for blocked request: false
Valid candidate: ACCEPT_CANDIDATE
Side-effect/unknown-citation candidate: REJECT_CANDIDATE
provider call performed: false
authority effect: false
activation effect: false
```

## Current verification automation

The historical standalone `.github/workflows/validate-chat-session-binding.yml` is being consolidated under cleanup claim `LLMA-WORKFLOW-CONSOLIDATE-CHAT-SESSION-BINDING-040`.

Current validation carrier:

```text
workflow: .github/workflows/validate.yml
workflow role: token-clean deterministic repository validation only
workflow credential authority: NONE
runtime credential authority: TV/TVC
checkout/setup/artifact transport: NONE
repository writeback: NONE
activation effect: NONE
```

The shared dispatcher runs:

```bash
$PYTHON_BIN -m pytest tests/test_chat_session_binding.py -q
$PYTHON_BIN scripts/verify_chat_session_binding.py --write-receipt
```

Current ongoing validation accurately claims the dispatcher Python 3.11 lane only. The historical 3.9/3.11/3.12 matrix remains release evidence above. Receipt generation in the dispatcher is workspace-local and is neither uploaded nor committed by GitHub Actions.

## Next integration owners

```text
Ecosystem Chat live-provider/runtime owner: issue #18 or canonical successor
VA Claims Chat live-provider/runtime owner: issue #90 or canonical successor
VA Claims privacy gate: privacy_guarded_dispatch remains mandatory
Site projection: waits for Site machine admission
Master Records custody: only after authorized real runtime execution under its existing owner
```

No provider credentials are accessed and no provider/custody/Site/filing/publication/deployment/activation authority is granted by this validation layer.

## Current state

```text
issue: StegVerse-org/LLM-adapter#105
original PR: #106
session-binding layer: RELEASED_COMPLETE
implementation: INSTALLED ON MAIN
retained receipt: PASS
historical 3-runtime compatibility evidence: PASS
current deterministic validation carrier: .github/workflows/validate.yml
workflow consolidation claim: LLMA-WORKFLOW-CONSOLIDATE-CHAT-SESSION-BINDING-040
provider execution: false
authority effect: false
activation effect: false
manual user action required: false
```

## Archive condition

The originating session-binding workload remains complete, released, validated, merged, and durably receipted; its originating chat can remain archived. Workflow consolidation is separate repository maintenance and does not reopen provider execution or product activation, which remain owner-gated under issues #18 and #90.
