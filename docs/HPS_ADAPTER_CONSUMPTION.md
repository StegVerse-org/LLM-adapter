# HPS Adapter Consumption

## Purpose

This document defines how `StegVerse-org/LLM-adapter` consumes Harmonic Principle of Standing (HPS) route decisions.

HPS is canonical in:

```text
Admissible-Existence/HPS
```

The SDK route contract is owned by:

```text
StegVerse-org/StegVerse-SDK
```

Ecosystem-wide orchestration is owned by:

```text
master-records/orchestration
```

The adapter consumes HPS route decisions before adapter-mediated consequence.

## Core rule

```text
Adapter output is not execution.
SDK route ALLOW is not execution authority.
HPS route DENY or FAIL_CLOSED must block adapter-mediated consequence.
```

## Adapter-mediated consequences

HPS route consumption applies before:

- tool use;
- memory commit;
- publication handoff;
- execution handoff;
- external API action;
- long-lived retention;
- public attribution or claim production.

## Decision mapping

```text
ALLOW
  Adapter may continue to the next governed boundary.
  This does not grant execution authority.

DENY
  Adapter must not proceed with the requested consequence.
  Adapter may return bounded explanation and receipt reference.

REVIEW
  Adapter must route to review or bounded non-executing response.

FAIL_CLOSED
  Adapter must block consequence and preserve failure evidence.
```

## Required invariant

```text
hps_route_decision_is_execution_authority == false
adapter_output_is_execution_authority == false
provider_output_is_authority == false
route_deny_blocks_consequence == true
route_fail_closed_blocks_consequence == true
route_review_blocks_automatic_consequence == true
route_allow_only_allows_next_boundary == true
```

## Canonical adapter statement

```text
The LLM adapter consumes HPS as a route governor.
It does not execute because HPS says ALLOW.
It only proceeds to the next governed boundary while preserving non-authority, receipts, and reconstruction posture.
```
