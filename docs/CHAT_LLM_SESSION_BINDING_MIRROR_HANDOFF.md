# Chat LLM Session Binding Mirror Handoff

## Source of truth

This is the authoritative continuation record for issue `StegVerse-org/LLM-adapter#105` and task `LLMA-CHAT-SESSION-BINDING-010` until merged or superseded.

Repository-wide orchestration remains governed by `docs/LLM_ADAPTER_MIRROR_HANDOFF.md` and `data/llm-adapter-orchestration-state.json`. This integration is parallel-safe because it creates new paths and performs no provider execution, permission request, custody submission, Site mutation, publication, filing, deployment, or activation.

## Dependency

```text
profile task: LLMA-CHAT-LLM-PROFILES-009
profile state: RELEASED_COMPLETE
profile merge: 18a49b8856a34d03d94955637adb4a53c9ccfe81
profile receipt: receipts/chat-llm-profiles-validation.json
profile receipt hash: 85a98e57b3a8e50fa13de3d24e2fcd39aaff99ea7071f3318719519f78275287
```

## Goal

Convert both released full-function LLM profiles into the same deterministic provider-neutral session contract.

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
```

The envelope may carry multi-turn messages, any requested subset of the 19 canonical LLM capabilities, response format, admitted grounding metadata, and candidate tool definitions.

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
```

Operational binding under issue #90 must call `privacy_guarded_dispatch` before this session envelope can be sent to a provider. This slice does not modify or bypass that path.

## Installed files

```text
llm_adapter/chat_session_binding.py
contracts/chat-llm-session-envelope.schema.json
tests/test_chat_session_binding.py
scripts/verify_chat_session_binding.py
.github/workflows/validate-chat-session-binding.yml
tasks/LLMA-CHAT-SESSION-BINDING-010.json
docs/CHAT_LLM_SESSION_BINDING_MIRROR_HANDOFF.md
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

Hosted workflow matrix:

```text
Python 3.9
Python 3.11
Python 3.12
```

Expected retained artifact after successful validation:

```text
receipts/chat-llm-session-binding-validation.json
```

## Collision boundaries

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
```

## Current state

```text
issue: StegVerse-org/LLM-adapter#105
branch: goal/chat-session-binding
task: LLMA-CHAT-SESSION-BINDING-010
implementation: COMPLETE ON BRANCH
hosted validation: PENDING
merge: PENDING
provider execution: false
authority effect: false
activation effect: false
manual user action required: false
```

## Completion metrics

```text
developed files: 7/7
scaffolding or stubs: 0
session preparation implementation: complete on branch
VA source enforcement: complete on branch
candidate response enforcement: complete on branch
deterministic verifier: complete on branch
hosted validation: pending
mainline integration: pending
live provider runtime consumption: pending under issues #18 and #90
```

## Archive condition

This session-binding workload becomes archive-ready after hosted checks pass, its pull request merges to `main`, the validation receipt is retained, and the task is released complete. Live provider execution and product activation remain separate owner-gated work.
