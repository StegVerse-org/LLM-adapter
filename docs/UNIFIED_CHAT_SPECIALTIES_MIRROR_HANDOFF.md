# Unified Chat Specialties Mirror Handoff

## Source of truth

```text
goal_id: LLMA-UNIFIED-SPECIALTY-PROFILES-180
repository: StegVerse-org/LLM-adapter
canonical_issue: #180 CLOSED_COMPLETED
parent_site_goal: StegVerse-Labs/Site#239
canonical_full_llm_profile: ecosystem-chat-llm
runtime_owner: StegVerse-org/LLM-adapter#18
vacc_route_owner: StegVerse-org/LLM-adapter#90/#142
math_site_owner: StegVerse-Labs/Site#240
source_state: COMPLETE_RELEASED_SOURCE
release_pr: #181
release_commit: 878c5b4c30214da9a74f5bf0a2ca0fe38cb25a12
```

## Product correction

The canonical conversational topology is one full LLM surface with specialty capability profiles layered on top:

```text
ecosystem-chat-llm
  -> VACC specialty
  -> mathematics educator specialty
  -> future specialty profiles
```

A specialty profile contributes context, source policy, response behavior, input modalities, and candidate tools. It does not create another provider/runtime, conversation history, execution authority, custody path, or credential plane.

## Released source slice

```text
contracts/chat-specialty-profile.schema.json
profiles/vacc-specialty.v1.json
profiles/math-educator-specialty.v1.json
llm_adapter/chat_specialties.py
tests/test_chat_specialty_profiles.py
tasks/LLMA-UNIFIED-SPECIALTY-PROFILES-180.json
```

### VACC

The VACC specialty consumes `ecosystem-chat-llm`, references the already released broad public-information profile and the stricter claims profile, treats disability claims as one deep subdomain rather than the whole specialty, and keeps private-record use behind separate privacy admission.

### Mathematics educator

The mathematics specialty consumes the same full LLM surface, supports text/image/file input, broad mathematics including history/foundations/philosophy, and educator behaviors such as hints, guided solutions, checking work, alternate methods, prerequisite explanation, and difficulty variation.

For photographed problems these remain different states:

```text
source_image
interpreted_mathematical_transcription
```

The transcription is interpretation, not source fact. Correction creates a successor transcription state; the original image is preserved. The deterministic solver and verifier are candidate tools only. Tool candidacy does not execute them and successful calculation is not mathematical proof authority.

## Preserved released work

Do not reopen or duplicate:
- `docs/CHAT_LLM_PROFILES_MIRROR_HANDOFF.md` released full LLM profile layer;
- `docs/CHAT_LLM_SESSION_BINDING_MIRROR_HANDOFF.md` provider-neutral session layer;
- `docs/VACC_PUBLIC_INFORMATION_PROFILE_MIRROR_HANDOFF.md` broad VACC source-policy layer;
- issue #18 provider/runtime path;
- issue #90/#142 VACC governed retrieval/runtime;
- Master Records custody/reconstruction authority.

## Validation evidence

Focused validation against implementation head `21a650e4eda96c4122a18d41a10e6a6ff952924a`:

```text
specialty invariants: 6/6 PASS
JSON Schema Draft 2020-12 meta-validation: PASS
VACC specialty manifest against schema: PASS
mathematics specialty manifest against schema: PASS
canonical base LLM for both specialties: ecosystem-chat-llm
math source_image != interpreted_mathematical_transcription: PASS
candidate tool execution_authority=false: PASS
provider-runtime duplication rejection: PASS
full-LLM inheritance loss rejection: PASS
math transcription promotion to source fact rejection: PASS
```

Global dispatcher run `32553959905` failed before project tests at `Install validation dependencies`. The credential-clean job attempted the existing `.[dev]` direct Git dependency on `StegVerse-Labs/StegCore` and could not anonymously clone the current protected/private source. This failure predates and is outside the specialty source slice. It is the same repository-source/public-distribution defect already owned by the StegVerse SDK + TVC portable-artifact publication chain. This handoff does not authorize a GitHub-token workaround, repository visibility change, or parallel artifact publisher.

```text
specialty source validation: PASS
main integration: COMPLETE
source claim: RELEASED
repository-wide credential-clean validation: BLOCKED_ON_EXISTING_DISTRIBUTION_DEPENDENCY
provider/runtime activation effect: NONE
Site activation effect: NONE
```

## Authority boundary

```text
credential authority: TV/TVC
GitHub token runtime authority: NONE
NON-TV/TVC secret/token required: false
specialty selection authority effect: false
model output execution authority: false
candidate tool execution authority: false
provider/runtime duplication: false
custody-path duplication: false
Site mutation authority: false
Render production dependency: NONE
```

## Continuation

This source goal is complete/released. Product continuation remains open downstream:
- issue #142 consumes the VACC specialty on the sovereign provider path;
- Site#239 consumes the specialty contract after `TASK-2026-0007` machine admission;
- Site#240 replaces the independent/hardcoded hosted math path with the shared conversation + governed tool-candidate path;
- issue #18 remains the sole provider/runtime owner.

Source completion is not provider execution, Site activation, tool execution, custody, publication, or product activation.
