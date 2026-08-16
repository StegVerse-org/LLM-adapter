# Chat LLM Profiles Mirror Handoff

## Source of truth

This is the authoritative continuation record for the released Chat LLM profile layer established by issue `StegVerse-org/LLM-adapter#102`, PR #103, and task `LLMA-CHAT-LLM-PROFILES-009`. Repository-wide authority remains `docs/LLM_ADAPTER_MIRROR_HANDOFF.md`.

## Governing product decision

```text
Ecosystem Chat contains StegVerse Chat.
Ecosystem Chat is a full-function LLM product surface.
VA Claims Chat is also a full-function LLM product surface.
The two products differ by purpose and factual-source policy, not by LLM capability.
```

Governance constrains consequence, authority, custody, publication, deployment, filing, and other side effects. It does not silently reduce conversational, analytical, retrieval, creative, structured-output, multimodal, planning, or tool-candidate capability.

## Released profiles

```text
profiles/ecosystem-chat-llm.v1.json
  profile_id: ecosystem-chat-llm
  LLM surface: FULL_PROVIDER_SUPPORTED
  source mode: GENERAL_ADMITTED
  state: RELEASED_COMPLETE

profiles/va-claims-chat-llm.v1.json
  profile_id: va-claims-chat-llm
  LLM surface: FULL_PROVIDER_SUPPORTED
  source mode: OFFICIAL_VA_ONLY
  state: RELEASED_COMPLETE
```

Both declare the same 19/19 canonical LLM feature set. Ecosystem Chat requires admitted sources. VA Claims Chat allows factual grounding from genuine `va.gov`/`*.va.gov` sources and privacy-approved, consent-bound, hash-bound user records; general web, model memory, lookalike hosts, and unapproved user records are denied as factual sources. Provider output and user records do not become authority.

## Authoritative implementation

```text
llm_adapter/chat_profiles.py
profiles/ecosystem-chat-llm.v1.json
profiles/va-claims-chat-llm.v1.json
contracts/chat-llm-profile.schema.json
tests/test_chat_llm_profiles.py
scripts/verify_chat_llm_profiles.py
tasks/LLMA-CHAT-LLM-PROFILES-009.json
receipts/chat-llm-profiles-validation.json
docs/CHAT_LLM_PROFILES_MIRROR_HANDOFF.md
```

The runtime-neutral profile engine performs no network request, provider execution, custody submission, Site mutation, publication, or external action.

## Historical release evidence

The original release remains valid historical compatibility evidence and is not rewritten by workflow consolidation:

```text
implementation PR: #103
validated head: aec79bca47951116564bba34401fb4bbd7363025
merge commit: 18a49b8856a34d03d94955637adb4a53c9ccfe81
historical workflow run: 30928497409
Python 3.9: PASS
Python 3.11: PASS
Python 3.12: PASS
policy tests per runtime: 16 PASS
receipt generation per runtime: PASS
historical artifact: 8900112614
artifact digest: sha256:5c289bdd81df013d1e33dff0563a78641f689328a1fee8a9db25348eeb217d90
retained receipt: receipts/chat-llm-profiles-validation.json
retained receipt commit: 008f56f0de5941c30747c7d0893b57440f60b9bc
receipt hash: 85a98e57b3a8e50fa13de3d24e2fcd39aaff99ea7071f3318719519f78275287
```

Validated retained result remains:

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

## Current verification automation

The historical standalone `.github/workflows/validate-chat-llm-profiles.yml` is being consolidated under workflow-cleanup claim `LLMA-WORKFLOW-CONSOLIDATE-CHAT-PROFILES-039`. The current validation carrier is the shared credential-clean dispatcher:

```text
workflow: .github/workflows/validate.yml
credential authority: NONE
runtime credential authority: TV/TVC
checkout/setup/artifact transport: NONE
repository writeback: NONE
activation effect: NONE
```

The shared dispatcher runs:

```bash
$PYTHON_BIN -m pytest tests/test_chat_llm_profiles.py -q
$PYTHON_BIN scripts/verify_chat_llm_profiles.py --write-receipt
```

This preserves deterministic policy and receipt validation on the dispatcher Python 3.11 lane. It does **not** claim that ongoing validation still executes the historical Python 3.9/3.11/3.12 matrix; that matrix remains release evidence above. The retained canonical receipt remains repository evidence; current dispatcher receipt generation is workspace-local validation and is not uploaded or written back by GitHub Actions.

Required negative checks remain: missing canonical feature fails; unadmitted source denies; Claims Chat non-VA source denies; VA lookalike denies; general web cannot masquerade as VA evidence; model memory cannot be a Claims factual source; user record without privacy PASS/consent/hash denies; authority-policy escalation fails.

## Integration continuation

```text
Ecosystem Chat runtime binding owner: StegVerse-org/LLM-adapter#18 or canonical successor
VA Claims Chat runtime binding owner: StegVerse-org/LLM-adapter#90 or canonical successor
Site projection owner: StegVerse-Labs/Site after machine admission
Master Records: operational receipt custody only after real runtime execution under its existing owner
```

Profile validation is not provider execution, custody, Site activation, publication, filing, or release authority.

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
original implementation PR: #103
profile-layer state: RELEASED_COMPLETE
implementation: INSTALLED ON MAIN
retained receipt: PASS
historical 3-runtime compatibility evidence: PASS
current deterministic validation carrier: .github/workflows/validate.yml
workflow consolidation claim: LLMA-WORKFLOW-CONSOLIDATE-CHAT-PROFILES-039
live provider binding: PENDING UNDER ISSUES #18 AND #90
authority effect: false
activation effect: false
manual user action required: false
```

## Completion metrics

```text
profile developed files: COMPLETE
scaffolding or stubs: 0
canonical LLM feature declaration: 19/19 for both profiles
source-policy implementation: 100 percent
historical negative tests: 16/16 per Python runtime
historical hosted runtime matrix: 3/3
mainline profile-layer release: 100 percent
live product activation: pending under existing owners
```

## Archive condition

The originating profile-layer workload remains complete, released, validated, merged, and durably receipted; its originating chat can remain archived. Workflow consolidation is a separate repository-maintenance claim and does not reopen the profile-layer implementation. Broader Ecosystem Chat and VA Claims Chat live activation remains owned by issues #18 and #90.
