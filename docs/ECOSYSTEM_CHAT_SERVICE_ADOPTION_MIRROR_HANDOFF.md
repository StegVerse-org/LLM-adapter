# Ecosystem Chat Service Adoption Mirror Handoff

## Active goal

Make Ecosystem Chat a fully functioning StegVerse utility chat and LLM product. Any required external service must either be eliminated or adopted behind a StegVerse-owned, replaceable interface with credentials retained only in protected runtime configuration.

```text
goal_id: LLMA-ECOSYSTEM-CHAT-SERVICE-ADOPTION-012
canonical_owner: StegVerse-org/LLM-adapter#18
branch: goal/ecosystem-chat-service-adoption
state: ACTIVE_BLOCKED_CONFIGURATION
archive_directive_applies: false
manual_user_action_required: false
```

## Verified progress

The previously recorded Render `no-server` state is superseded. The current `stegverse-ecosystem-chat-gateway` deployment built successfully, is marked live, and repeatedly returned HTTP 200 from `/health`.

The StegVerse-owned Render workspace also contains:

```text
stegverse-hil-receiver — persistent disk-backed HIL receiver
TVC — admission service
stegverse-va-claim-guide — Site surface
SCW API, worker, and UI — StegVerse compute services
```

These are adopted infrastructure, not automatic execution, custody, publication, or provider authority.

## Dependency rule

```text
unnamed third-party dependency: forbidden
adopted infrastructure: permitted only behind StegVerse-owned interface and governance
provider: replaceable through the provider-neutral contract
credentials: protected runtime configuration only
provider output: never authority
local persistence: never custody
custody: never publication authority
```

## Current activation units

```text
1. Full LLM profile: COMPLETE
2. Provider-neutral session binding: COMPLETE
3. Persistent public gateway: COMPLETE
4. Authorized provider execution: BLOCKED_CONFIGURATION
5. Custody, reconstruction, Site and downstream activation: BLOCKED_CONFIGURATION_AND_EVIDENCE
```

## Remaining execution

Issue #18 remains the sole owner. Continue by binding or deploying an authorized provider endpoint behind the StegVerse provider interface, binding an authenticated StegVerse Master Records endpoint, executing one governed request, retaining provider usage and custody evidence, reconstructing the transition, emitting an immutable zero-blocker receipt, then activating Site and downstream ingestion.

Do not substitute the HIL receiver for Master Records without protocol evidence. Do not place secrets in repository content, logs, receipts, artifacts, issues, or pull requests.

## Durable records

```text
data/ecosystem-chat-service-adoption.json
scripts/check_ecosystem_chat_service_adoption.py
.github/workflows/ecosystem-chat-service-adoption.yml
tasks/LLMA-ECOSYSTEM-CHAT-SERVICE-ADOPTION-012.json
```
