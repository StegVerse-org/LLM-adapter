# VACC Public Information Profile Mirror Handoff

## Goal

```text
goal_id: LLMA-VACC-PUBLIC-INFORMATION-PROFILE-022
originating_goal: VACC is an interactive Department of Veterans Affairs companion with broad admitted VA/federal public information access through LLM-adapter
repository: StegVerse-org/LLM-adapter
branch: main
canonical_issue: #141
parent_runtime_issue: #90
```

## Existing boundary preserved

The existing `profiles/va-claims-chat-llm.v1.json` remains unchanged. Claim-specific external factual grounding remains official-VA-only plus separately labeled privacy-approved user-record facts. This new profile does not relax that rule.

## Installed source

```text
profiles/vacc-public-information-llm.v1.json
llm_adapter/vacc_public_information.py
tests/test_vacc_public_information.py
tasks/LLMA-VACC-PUBLIC-INFORMATION-PROFILE-022.json
docs/VACC_PUBLIC_INFORMATION_PROFILE_MIRROR_HANDOFF.md
.github/workflows/public-knowledge-vacc-source-validation.yml
```

The companion profile points to the canonical Site registry:

```text
StegVerse-Labs/Site/data/va-claim-assistant/source-registry.json
```

and permits admitted public sources from authority classes already defined there, including VA operational sources and controlling federal sources. The initial host classes include `va.gov`, `benefits.va.gov`, `uscode.house.gov`, `ecfr.gov`, `uscourts.cavc.gov`, and `federalregister.gov`.

The policy evaluator fails closed when a source is unadmitted, non-public, stale when freshness is required, outside the profile allowlist, or attempts to use private VAwatchdog content as public grounding.

VAwatchdog can contribute only through a separately admitted sanitized/public projection. Such experiential material never becomes government authority and cannot establish law or medical nexus.

## Informational expansion target

The profile explicitly preserves VACC coverage for:

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

Actual route generators for categories not yet represented in issue #90 remain a parent-runtime implementation dependency; this profile is the source-policy prerequisite and does not masquerade as complete route execution.

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

## Validation evidence

Credential-free source workflow:

```text
workflow: .github/workflows/public-knowledge-vacc-source-validation.yml
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

Current source state:

```text
profile installed: YES
source-policy evaluator installed: YES
focused source validation: COMPLETE
task state: COMPLETE_VALIDATED_SOURCE_PROFILE
claim state: RELEASED
real VA provider execution / Master Records custody / Site projection: issue #90 machine/runtime continuation
```

## Continuation

- issue #141 owns source-profile history and any bounded profile-policy correction;
- issue #90 owns VA governed retrieval/runtime execution and broad route execution;
- Site#113 and Site orchestration own Site projection;
- Site source registry remains the canonical source list;
- VAwatchdog owns its own evidence/source-tier repository and does not automatically become public VACC grounding.

The source-profile slice is complete, validated, and released. This does not prove VACC's broad informational route execution or live provider/custody activation.
