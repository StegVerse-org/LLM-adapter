# VACC Public Information Profile Mirror Handoff

## Goal

```text
goal_id: LLMA-VACC-PUBLIC-INFORMATION-PROFILE-022
originating_goal: VACC is an interactive Department of Veterans Affairs companion with broad admitted VA/federal public information access through LLM-adapter
repository: StegVerse-org/LLM-adapter
canonical_issue: #141
parent_runtime_issue: #90
state: COMPLETE_VALIDATED_SOURCE_PROFILE
claim_state: RELEASED
```

## Existing boundary preserved

`profiles/va-claims-chat-llm.v1.json` remains unchanged. Claim-specific external factual grounding remains official-VA-only plus separately labeled privacy-approved user-record facts. This public-information profile does not relax that rule.

## Authoritative implementation

```text
profiles/vacc-public-information-llm.v1.json
llm_adapter/vacc_public_information.py
tests/test_vacc_public_information.py
tasks/LLMA-VACC-PUBLIC-INFORMATION-PROFILE-022.json
docs/VACC_PUBLIC_INFORMATION_PROFILE_MIRROR_HANDOFF.md
```

The profile points to the canonical Site registry `StegVerse-Labs/Site/data/va-claim-assistant/source-registry.json` and permits admitted public sources from authority classes defined there, including VA operational and controlling federal sources. Initial host classes include `va.gov`, `benefits.va.gov`, `uscode.house.gov`, `ecfr.gov`, `uscourts.cavc.gov`, and `federalregister.gov`.

The evaluator fails closed for unadmitted, non-public, stale-when-required, disallowed-class, or private VAwatchdog material. VAwatchdog may contribute only through a separately admitted sanitized/public projection; experiential material never becomes government authority and cannot establish law or medical nexus.

## Informational expansion target

```text
disability claims
healthcare/program navigation
education/GI Bill
home loans
burial/memorial
caregiver programs
facilities/contact/navigation
forms and official procedures
appeals/decision review
federal statutes/regulations
CAVC/BVA context
VA rulemaking/notices
```

Actual route generators not yet represented under issue #90 remain a parent-runtime implementation dependency. This source-policy profile does not masquerade as complete route execution.

## Authority / credential boundary

```text
credential_authority: TV/TVC
non_tv_tvc_secret_or_token_required: false
github_token_runtime_authority: NONE
adjudication authority: false
representation authority: false
medical opinion authority: false
rating authority: false
filing/signature/submission authority: false
publication authority: false
```

## Historical release validation

The original combined source-validation evidence remains historical release evidence:

```text
historical_workflow: .github/workflows/public-knowledge-vacc-source-validation.yml
workflow_run: 31875248198
job: 94989892925
result: SUCCESS
focused tests in combined Ecosystem/VACC run: 11/11 PASS
credential-empty assertions: GITHUB_TOKEN, GH_TOKEN, OPENAI_API_KEY, ANTHROPIC_API_KEY
source materialization: anonymous exact-SHA archive
compile: PASS
marker: PUBLIC_KNOWLEDGE_VACC_SOURCE_VALIDATION_PASS
manual workflow dispatch: NO
```

## Current deterministic validation

Workflow consolidation claim `LLMA-WORKFLOW-CONSOLIDATE-PUBLIC-KNOWLEDGE-VACC-041` transfers continuing source validation to the shared credential-clean dispatcher:

```text
current_workflow: .github/workflows/validate.yml
workflow_credential_authority: NONE
runtime_credential_authority: TV/TVC
checkout/setup/artifact transport: NONE
repository writeback: NONE
activation effect: NONE
```

The dispatcher compiles the public-knowledge/VACC source surfaces and executes:

```bash
$PYTHON_BIN -m unittest -q tests.test_public_knowledge tests.test_vacc_public_information
```

The credential-refusal step explicitly includes `GITHUB_TOKEN`, `GH_TOKEN`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, TV/TVC protected values, and other credential-bearing environment values. No provider execution, custody submission, filing, publication, or Site mutation occurs.

## Continuation

Issue #141 owns source-profile history and bounded profile-policy corrections. Issue #90 owns VACC governed retrieval/runtime execution and broad route execution. Site#113 and Site orchestration own Site projection. The Site source registry remains canonical. VAwatchdog owns its own source-tier evidence and never automatically becomes public VACC grounding.

The originating source-profile slice is complete, validated, and released. Workflow consolidation is repository maintenance and does not prove broad informational route execution or live provider/custody activation.
