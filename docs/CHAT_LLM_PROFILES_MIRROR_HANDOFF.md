# Chat LLM Profiles Mirror Handoff

## Source of truth

This document is the authoritative continuation record for the released Chat LLM profile layer established by issue `StegVerse-org/LLM-adapter#102`, pull request `#103`, and task `LLMA-CHAT-LLM-PROFILES-009`.

The repository-wide source of truth remains `docs/LLM_ADAPTER_MIRROR_HANDOFF.md`. This workload was parallel-safe because it used new profile, contract, test, verifier, workflow, task, receipt, and documentation paths and did not modify the exclusive live-provider lane owned by issue #18.

## Governing product decision

```text
Ecosystem Chat contains StegVerse Chat.
Ecosystem Chat is a full-function LLM product surface.
VA Claims Chat is also a full-function LLM product surface.
The two products differ by purpose and factual-source policy, not by LLM capability.
```

Governance constrains consequence, authority, custody, publication, deployment, filing, and other side effects. It does not silently reduce conversational, analytical, retrieval, creative, structured-output, multimodal, planning, or tool-candidate capability.

## Released parallel lanes

### Lane A — Ecosystem Chat / StegVerse Chat

```text
profile: profiles/ecosystem-chat-llm.v1.json
profile_id: ecosystem-chat-llm
LLM surface: FULL_PROVIDER_SUPPORTED
source mode: GENERAL_ADMITTED
state: RELEASED_COMPLETE
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
state: RELEASED_COMPLETE
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

## Installed files

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
receipts/chat-llm-profiles-validation.json
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

## Hosted validation evidence

```text
implementation PR: #103
validated head: aec79bca47951116564bba34401fb4bbd7363025
merge commit: 18a49b8856a34d03d94955637adb4a53c9ccfe81
workflow: Validate Chat LLM Profiles
workflow run: 30928497409
Python 3.9: PASS
Python 3.11: PASS
Python 3.12: PASS
policy tests per runtime: 16 PASS
receipt generation per runtime: PASS
Architecture Guard: PASS
repository validate: PASS
Platform-Agnostic Runtime: PASS
Validate Provider-Owned Usage Event: PASS
Portable User-LLM Execution Receipt: PASS
HIL managed receiver validation: PASS
artifact: 8900112614
artifact digest: sha256:5c289bdd81df013d1e33dff0563a78641f689328a1fee8a9db25348eeb217d90
retained receipt: receipts/chat-llm-profiles-validation.json
retained receipt commit: 008f56f0de5941c30747c7d0893b57440f60b9bc
receipt hash: 85a98e57b3a8e50fa13de3d24e2fcd39aaff99ea7071f3318719519f78275287
```

Validated receipt result:

```text
state: PASS
feature sets equal: true
Ecosystem Chat features: 19/19
VA Claims Chat features: 19/19
Ecosystem admitted general source: ALLOW_ADMITTED_SOURCE
Claims official VA source: ALLOW_VA_SOURCE_FACT
Claims non-VA source: DENY_SOURCE
Claims privacy-approved user record: ALLOW_USER_RECORD_FACT
authority effect: false
activation effect: false
provider execution observed: false
Site activation observed: false
```

## Verification contract

```bash
python -m pytest tests/test_chat_llm_profiles.py -q
python scripts/verify_chat_llm_profiles.py --write-receipt
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

## Next integration goals

### Ecosystem Chat runtime binding

Owner: `StegVerse-org/LLM-adapter#18` or its canonical successor.

```text
bind ecosystem-chat-llm profile to the existing provider runtime
preserve full LLM feature projection
retain source-decision labels and profile hash
complete authorized persistent endpoint and real-provider gates
persist provider usage
obtain provider-usage and transition custody RECORDED
obtain both reconstruction results PASS
emit immutable zero-blocker VERIFIED activation receipt
```

### VA Claims Chat runtime binding

Owner: `StegVerse-org/LLM-adapter#90` or its canonical successor.

```text
bind va-claims-chat-llm after privacy_guarded_dispatch
require official-VA-only source decisions before factual generation
retain user-record facts as separately labeled non-authority records
consume fresh TVC admission and explicit provider authority
perform one bounded real provider request
obtain Master Records custody RECORDED and reconstruction PASS
project only receipt-verified capability to Site
```

### Site projection

`StegVerse-Labs/Site` rejected external session ownership when this task was executed, so no Site paths were claimed. After Site machine admission, its canonical owner should project:

```text
product profile identity
full LLM feature matrix
source-policy mode
source-decision labels
false authority and activation flags
profile and receipt hashes
validation and runtime states
```

### Master Records

Profile validation is not custody. Future operational receipts may be submitted only through the existing Master Records owner after real runtime execution.

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
pull request: #103
merge: COMPLETE
merge commit: 18a49b8856a34d03d94955637adb4a53c9ccfe81
task: LLMA-CHAT-LLM-PROFILES-009
state: RELEASED_COMPLETE
implementation: INSTALLED ON MAIN
hosted validation: PASS
receipt retained: PASS
live provider binding: PENDING UNDER ISSUES #18 AND #90
Site projection: PENDING FUTURE SITE MACHINE ADMISSION
authority effect: false
activation effect: false
manual user action required: false
```

## Completion metrics

```text
developed files: 10/10
scaffolding or stubs: 0
canonical LLM feature declaration: 19/19 for both profiles
source-policy implementation: 100 percent
negative tests: 16/16 per Python runtime
hosted runtime matrix: 3/3
repository-wide checks: 6/6
mainline integration: 100 percent
profile-layer release: 100 percent
live product activation: pending under existing owners
```

## Archive condition

The profile-layer workload is complete, released, validated, merged, and durably receipted. No unique implementation or continuation state remains in the originating chat for this slice. Broader Ecosystem Chat and VA Claims Chat live activation remains owned by issues #18 and #90.

ARCHIVE THIS PROFILE-LAYER WORKLOAD.
