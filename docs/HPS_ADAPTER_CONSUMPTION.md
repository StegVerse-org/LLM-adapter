# HPS Adapter Consumption

## Purpose

This document defines how `StegVerse-org/LLM-adapter` participates in the corrected Harmonic Principle of Standing (HPS) runtime/bridge/delegation architecture.

HPS formalism is canonical in:

```text
Admissible-Existence/HPS
```

Executable runtime semantics are owned by:

```text
StegVerse-org/HPS-runtime
```

Sibling input route normalization is owned by:

```text
StegVerse-Labs/hybrid-collab-bridge
```

Governed authority delegation evaluation is owned by:

```text
StegVerse-Labs/Ecosystem-Delegation
```

Ecosystem-wide cycle records and reconstruction receipts are owned by:

```text
master-records/orchestration
```

The LLM adapter does not consume SDK route decisions as upstream authority. The LLM adapter is an LLM-origin input nest that reads runtime standing state, emits LLM-origin route candidates, and blocks adapter-mediated consequences when route/delegation state denies, reviews, or fails closed.

## Corrected architecture

```text
Admissible-Existence/HPS
  -> standing-vector formalism

StegVerse-org/HPS-runtime
  -> runtime state, standing-vector registers, phases, epochs, capability windows

SDK input            \
LLM-adapter input     \
Site input             -> hybrid-collab-bridge -> Ecosystem-Delegation -> next governed boundary
External adapter      /
Manual review        /
```

## Core rule

```text
Adapter output is not execution.
LLM-adapter is a sibling input nest.
SDK route ALLOW is not adapter authority.
HPS route DENY or FAIL_CLOSED must block adapter-mediated consequence.
Delegation DENY or FAIL_CLOSED must block adapter-mediated consequence.
```

## Adapter-mediated consequences

HPS route and delegation consumption applies before:

- tool use;
- memory commit;
- publication handoff;
- execution handoff;
- external API action;
- long-lived retention;
- public attribution or claim production.

## Decision mapping

```text
ALLOW / ALLOW_NEXT_BOUNDARY / ALLOW_DELEGATION
  Adapter may continue to the next governed boundary.
  This does not grant execution, publication, or delegation authority.

DENY / DENY_DELEGATION
  Adapter must not proceed with the requested consequence.
  Adapter may return bounded explanation and receipt reference.

REVIEW / REVIEW_DELEGATION
  Adapter must route to review or bounded non-executing response.

FAIL_CLOSED
  Adapter must block consequence and preserve failure evidence.
```

## Relationship to SDK

`StegVerse-org/StegVerse-SDK` is a sibling input nest, not upstream authority for the LLM adapter.

```text
SDK-origin request -> bridge -> delegation -> next governed boundary
LLM-origin request -> bridge -> delegation -> next governed boundary
```

Both input paths consume shared runtime, bridge, delegation, and orchestration contracts.

## Required invariant

```text
hps_route_decision_is_execution_authority == false
adapter_output_is_execution_authority == false
provider_output_is_authority == false
sdk_route_allow_is_adapter_authority == false
llm_adapter_consumes_sdk_route_authority == false
sdk_and_llm_adapter_are_sibling_input_nests == true
route_deny_blocks_consequence == true
route_fail_closed_blocks_consequence == true
route_review_blocks_automatic_consequence == true
route_allow_only_allows_next_boundary == true
delegation_deny_blocks_consequence == true
delegation_fail_closed_blocks_consequence == true
delegation_allow_only_allows_next_boundary == true
```

## Canonical adapter statement

```text
The LLM adapter consumes HPS as an LLM-origin sibling input nest.
It reads runtime standing state, emits bounded LLM-origin route candidates, and does not grant execution, delegation, or publication authority.
It only proceeds to the next governed boundary while preserving non-authority, receipts, and reconstruction posture.
```
