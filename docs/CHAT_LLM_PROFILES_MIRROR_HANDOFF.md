# Chat LLM Profiles Mirror Handoff

## Source of truth

This document is the authoritative continuation record for issue `StegVerse-org/LLM-adapter#102` and task `LLMA-CHAT-LLM-PROFILES-009` until the work is merged or explicitly superseded.

The repository-wide source of truth remains `docs/LLM_ADAPTER_MIRROR_HANDOFF.md`. This workload is parallel-safe because it uses new profile, contract, test, verifier, workflow, task, and documentation paths and does not modify the exclusive live-provider lane owned by issue #18.

## Governing product decision

```text
Ecosystem Chat contains StegVerse Chat.
Ecosystem Chat is a full-function LLM product surface.
VA Claims Chat is also a full-function LLM product surface.
The two products differ by purpose and factual-source policy, not by LLM capability.
```

Governance constrains consequence, authority, custody, publication, deployment, filing, and other side effects. It must not silently reduce the model's conversational, analytical, retrieval, creative, structured-output, multimodal, planning, or tool-candidate capability.

## Parallel lanes

### Lane A — Ecosystem Chat / StegVerse Chat

```text
profile: profiles/ecosystem-chat-llm.v1.json
profile_id: ecosystem-chat-llm
LLM surface: FULL_PROVIDER_SUPPORTED
source mode: GENERAL_ADMITTED
```

The profile declares the complete canonical LLM feature set:

```text
multi-turn conversation
system / developer / user instruction layers
long context
streaming
structured output
function and tool calling
retrieval-augmented generation
web retrieval
file understanding
image understanding
audio understanding
code generation
artifact generation
multilingual generation
planning and multi-step reasoning
memory candidate generation
model routing
citation and provenance output
candidate action generation
```

External sources still require admission. Model output and tool candidates remain non-authorizing until downstream transition governance independently admits consequence.

### Lane B — VA Claims Chat LLM

```text
profile: profiles/va-claims-chat-llm.v1.json
profile_id: va-claims-chat-llm
LLM surface: FULL_PROVIDER_SUPPORTED
source mode: OFFICIAL_VA_ONLY
```

VA Claims Chat exposes the same complete LLM feature set. Its purpose boundary applies to factual grounding:

```text
admitted official source at va.gov or a genuine *.va.gov subdomain
  -> allowed as va_source_fact

privacy-approved, consent-bound, hash-bound user record
  -> allowed as user_record_fact
  -> never converted into VA authority

general web source
  -> denied as a Claims Chat factual source

model memory
  -> denied as a Claims Chat factual source

VA lookalike or redirect-trick hostname
  -> denied
```

The restriction does not disable conversation, analysis, document organization, multilingual output, structured output, tool-candidate generation, planning, or artifact generation. It controls what may support a factual VA claims answer.

## Implemented files

```text
llm_adapter/chat_profiles.py
profiles/ecosystem-chat-llm.v1.json
profiles/va-claims-chat-llm.v1.json
contracts/chat-llm-profile.schema.json
tests/test_chat_llm_profiles.py
scripts/verify_chat_llm_profiles.py
.github/workflows/validate-chat-llm-profiles.yml
tasks/LLMA-CHAT-LLM-PROFILES-009.json
docs/CHAT_LLM_PROFILES_MIRROR_HANDOFF.md
```

## Runtime-neutral profile engine

`llm_adapter/chat_profiles.py` provides:

```text
canonical FULL_LLM_FEATURES
strict manifest validation
paired-profile capability parity validation
URL/hostname normalization
official va.gov boundary validation
source admission decisions
privacy-approved user-record decisions
deterministic manifest hashing
deterministic capability matrix generation
```

The engine performs no network request, provider execution, custody submission, Site mutation, or external action.

## Verification contract

Run locally or in CI:

```bash
python -m pytest tests/test_chat_llm_profiles.py -q
python scripts/verify_chat_llm_profiles.py --write-receipt
```

The hosted workflow validates Python 3.9, 3.11, and 3.12 and retains:

```text
receipts/chat-llm-profiles-validation.json
```

Required negative checks include:

```text
missing canonical LLM feature -> fail
unadmitted external source -> deny
non-VA external source in Claims Chat -> deny
VA lookalike hostname -> deny
general-web source typed as VA evidence -> deny
model memory used as VA factual source -> deny
user record without privacy PASS, consent, or hash -> deny
any authority policy set true -> fail
```

## Integration sequence after profile validation

### Existing adapter owner

Issue #18 or its canonical successor may bind `ecosystem-chat-llm` into the existing provider runtime only after its independent provider, persistent endpoint, persistence, custody, reconstruction, and activation gates pass.

Issue #90 or its canonical successor may bind `va-claims-chat-llm` into the existing privacy-guarded Claims runtime only after its independent TVC, provider authority, Master Records, and execution-evidence gates pass.

### Site owner

`StegVerse-Labs/Site` currently rejects external session ownership through its orchestration state. No Site paths are claimed by this task. After adapter validation and Site machine admission, Site should project:

```text
product profile identity
full LLM feature matrix
source-policy mode
source-decision labels
false authority and activation flags
receipt hash and validation state
```

### Master Records owner

Future operational receipts may be submitted only through the existing custody owner. Profile validation itself is not custody and must not be represented as an operational Master Record.

## Authority boundary

```text
full LLM capability != execution authority
reasoning != consequence
conversation != admissibility
retrieval != source admission
source admission != transition admissibility
provider output != VA authority
user record != VA authority
tool candidate != tool execution
artifact generation != publication
Claims Chat answer != claim adjudication
Claims Chat package != signature or filing
profile validation != live activation
```

## Current state

```text
issue: StegVerse-org/LLM-adapter#102
branch: goal/chat-llm-profiles
task: LLMA-CHAT-LLM-PROFILES-009
implementation: COMPLETE ON BRANCH
hosted validation: PENDING
merge: PENDING
live provider binding: NOT PART OF THIS PARALLEL-SAFE SLICE
Site projection: BLOCKED BY SITE ORCHESTRATION AND FUTURE MACHINE ADMISSION
authority effect: false
activation effect: false
manual user action required: false
```

## Completion metrics

```text
developed files: 9/9
scaffolding or stubs: 0
canonical LLM feature declaration: 19/19 for both profiles
source-policy implementation: complete on branch
negative tests: implemented
hosted validation: pending
mainline integration: pending
live product activation: pending under existing owners
```

## Archive condition

This workload becomes repository-archive-ready after hosted checks pass, the pull request merges to `main`, the task is changed to `RELEASED_COMPLETE`, and this handoff records the merge and validation evidence. Broader Ecosystem Chat and VA Claims Chat live activation remains owned by issues #18 and #90 and is not completed by profile installation alone.
