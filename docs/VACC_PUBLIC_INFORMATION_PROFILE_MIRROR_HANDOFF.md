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
```

The companion profile points to the canonical Site registry:

```text
StegVerse-Labs/Site/data/va-claim-assistant/source-registry.json
```

and permits admitted public sources from authority classes already defined there, including VA operational sources and controlling federal sources. The initial host classes include `va.gov`, `benefits.va.gov`, `uscode.house.gov`, `ecfr.gov`, `uscourts.cavc.gov`, and `federalregister.gov`.

The policy evaluator fails closed when a source is unadmitted, non-public, stale when freshness is required, outside the profile allowlist, or attempts to use private VAwatchdog content as public grounding.

VAwatchdog can contribute only through a separately admitted sanitized/public projection. Such experiential material never becomes government authority and cannot establish law or medical nexus.

## Informational expansion target

The new profile explicitly preserves future VACC coverage for:

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

## Validation state

```text
profile installed: YES
source-policy evaluator installed: YES
focused tests installed: YES
automatic repository workflows observed after source commits: YES
focused test execution result: PENDING INSPECTION
real VA provider execution / custody / Site projection: issue #90 machine/runtime continuation
```

## Continuation

- issue #141 owns this public-information profile/source-policy slice;
- issue #90 owns VA governed retrieval/runtime execution;
- Site#113 and Site orchestration own Site projection;
- Site source registry remains the canonical source list;
- VAwatchdog owns its own evidence/source-tier repository and does not automatically become public VACC grounding.
