# Chat LLM Session Binding Mirror Handoff

## Source of truth

This is the authoritative continuation record for the released provider-neutral session-binding layer established by issue `StegVerse-org/LLM-adapter#105`, pull request `#106`, and task `LLMA-CHAT-SESSION-BINDING-010`.

Repository-wide orchestration remains governed by `docs/LLM_ADAPTER_MIRROR_HANDOFF.md` and `data/llm-adapter-orchestration-state.json`. This integration was parallel-safe: it created new paths and performed no provider execution, permission request, custody submission, Site mutation, publication, filing, deployment, or activation.

## Dependency

```text
profile task: LLMA-CHAT-LLM-PROFILES-009
profile state: RELEASED_COMPLETE
profile merge: 18a49b8856a34d03d94955637adb4a53c9ccfe81
profile receipt: receipts/chat-llm-profiles-validation.json
profile receipt hash: 85a98e57b3a8e50fa13de3d24e2fcd39aaff99ea7071f3318719519f78275287
```

## Released goal

Both full-function LLM profiles now use the same deterministic provider-neutral session contract:

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

## Ecosystem Chat behavior

```text
profile: ecosystem-chat-llm
LLM surface: FULL_PROVIDER_SUPPORTED
sources: any admitted source class allowed by the profile
tools: candidate-only
provider binding: separate downstream action
state: RELEASED_COMPLETE
```

The envelope carries multi-turn messages, any requested subset of the 19 canonical LLM capabilities, response format, admitted grounding metadata, and candidate tool definitions.

## VA Claims Chat behavior

```text
profile: va-claims-chat-llm
LLM surface: FULL_PROVIDER_SUPPORTED
external factual source: admitted official va.gov or genuine *.va.gov only
user record: privacy PASS + consent + content hash
user record label: user_record_fact
user record authority: false
general web as VA factual support: denied
model memory as VA factual support: denied
required denied source: blocks before provider envelope creation
state: RELEASED_COMPLETE
```

Operational consumption under issue #90 must call `privacy_guarded_dispatch` before this session envelope can be sent to a provider. This integration does not modify or bypass that path.

## Installed files

```text
llm_adapter/chat_session_binding.py
contracts/chat-llm-session-envelope.schema.json
tests/test_chat_session_binding.py
scripts/verify_chat_session_binding.py
.github/workflows/validate-chat-session-binding.yml
tasks/LLMA-CHAT-SESSION-BINDING-010.json
docs/CHAT_LLM_SESSION_BINDING_MIRROR_HANDOFF.md
receipts/chat-llm-session-binding-validation.json
```

## Session preparation states

```text
READY_FOR_PROVIDER_BINDING
  validated profile
  at least one user message
  requested features belong to profile
  required factual grounding satisfied
  no provider configuration attached
  no provider permission requested
  no provider call performed

BLOCKED_SOURCE_POLICY
  a required source was denied
  or factual grounding was required with no allowed source
  provider envelope is absent
```

## Candidate response validation

Accepted candidates must:

```text
contain non-empty text
cite only source IDs admitted into the envelope
use the exact source decision fact_label for factual claims
cite every declared factual claim
call only declared candidate tools
mark every tool call CANDIDATE_NOT_EXECUTED
keep side_effects_executed false
keep authority_claimed false
make no publication or custody claim
```

The result is `ACCEPT_CANDIDATE` or `REJECT_CANDIDATE`. Acceptance is not authority, admissibility, publication, custody, filing, or activation.

## Hosted validation evidence

```text
implementation PR: #106
validated head: 45ba9cabcca412836a51ee6b5a4b2342b29957d9
merge commit: 5ee90dd1f1cc3d6b20ecb3bce3991d8b59d869e5
workflow: Validate Chat Session Binding
workflow run: 30929473927
Python 3.9: PASS
Python 3.11: PASS
Python 3.12: PASS
tests per runtime: 17 PASS
receipt generation per runtime: PASS
Architecture Guard: PASS
repository validate: PASS
Platform-Agnostic Runtime: PASS
Validate Provider-Owned Usage Event: PASS
Portable User-LLM Execution Receipt: PASS
HIL managed receiver validation: PASS
artifact: 8900506930
artifact digest: sha256:5458d91baf79c4287b25034f58e6f174f27e64032837483229cb9597cbc307b3
retained receipt: receipts/chat-llm-session-binding-validation.json
retained receipt commit: 66222a09d05377727f0273674ca29917ebcbc99a
receipt hash: b1f9f56e8dc087ee04c49a011d351855a762030e2886d484def025a29e2e09b0
```

Validated result:

```text
state: PASS
Ecosystem session: READY_FOR_PROVIDER_BINDING
Claims session: READY_FOR_PROVIDER_BINDING
Claims source mode: official VA only
Claims allowed labels: va_source_fact, user_record_fact
Required non-VA Claims source: BLOCKED_SOURCE_POLICY
Provider envelope created for blocked request: false
Valid candidate: ACCEPT_CANDIDATE
Side-effect/unknown-citation candidate: REJECT_CANDIDATE
provider configuration attached: false
provider permission requested: false
provider call performed: false
tools executed: false
custody submitted: false
Site mutated: false
authority effect: false
activation effect: false
```

## Deterministic evidence

The implementation hashes:

```text
profile manifest
source metadata
normalized request projection
provider-neutral envelope
candidate response projection
session preparation receipt
candidate validation receipt
```

No source body, credential, provider token, raw private document, or rejected PII is required by this contract.

## Verification

```bash
python -m pytest tests/test_chat_session_binding.py -q
python scripts/verify_chat_session_binding.py --write-receipt
```

## Next integration owners

### Ecosystem Chat

Owner: issue `#18` or its canonical successor.

```text
consume the released ecosystem-chat-llm envelope
attach authorized provider configuration only through the existing secret boundary
execute one real governed provider request when independently authorized
persist provider usage
obtain provider-usage and transition custody RECORDED
obtain reconstruction PASS for both chains
emit immutable zero-blocker VERIFIED receipt
```

### VA Claims Chat

Owner: issue `#90` or its canonical successor.

```text
run privacy_guarded_dispatch before envelope transmission
consume the released va-claims-chat-llm envelope
obtain fresh TVC admission and exact provider authority
execute one bounded real source-grounded request
submit only privacy-minimized evidence to Master Records
obtain custody RECORDED and reconstruction PASS
project only receipt-verified capability to Site
```

### Site

No Site paths were claimed because Site orchestration rejected external session ownership. Projection waits for Site machine admission.

## Collision and authority boundaries

```text
issue #18 live-provider and persistent endpoint paths: untouched
issue #90 authorized execution paths: untouched
privacy_guarded_dispatch: not bypassed
provider credentials: not accessed
provider permissions: not requested
provider call: not performed
Master Records custody: not submitted
Site paths: not claimed
filing / publication / deployment / activation: false
provider-neutral envelope readiness != provider execution
candidate acceptance != authority or admissibility
```

## Current state

```text
issue: StegVerse-org/LLM-adapter#105
pull request: #106
merge: COMPLETE
merge commit: 5ee90dd1f1cc3d6b20ecb3bce3991d8b59d869e5
task: LLMA-CHAT-SESSION-BINDING-010
state: RELEASED_COMPLETE
implementation: INSTALLED ON MAIN
hosted validation: PASS
receipt retained: PASS
provider execution: false
authority effect: false
activation effect: false
manual user action required: false
```

## Completion metrics

```text
developed files: 8/8
scaffolding or stubs: 0
session preparation implementation: 100 percent
VA source enforcement: 100 percent
candidate response enforcement: 100 percent
deterministic verifier: 100 percent
hosted runtime matrix: 3/3
session tests: 17/17 per runtime
repository-wide checks: 6/6
mainline integration: 100 percent
session-binding release: 100 percent
live provider runtime consumption: pending under issues #18 and #90
```

## Archive condition

The session-binding workload is complete, released, validated, merged, and durably receipted. No unique implementation or continuation state remains in the originating chat for this slice. Live provider execution and product activation remain separately owner-gated.

ARCHIVE THIS SESSION-BINDING WORKLOAD.
