# Micro-Node Governed Return-Path Proof

This document defines how `LLM-adapter` consumes the portable micro-node contract from `StegVerse-002/micro-node-runtime` without becoming the micro-node runtime itself.

## Compatibility claim

`LLM-adapter` is compatible with the micro-node return-path contract when it can:

1. package an external LLM interaction as a governed transition request,
2. preserve the original customer return path,
3. receive a terminal decision of `ALLOW`, `DENY`, or `FAIL_CLOSED`,
4. preserve the micro-node receipt hash,
5. return governed output to the original path without granting execution authority.

## Boundary

```text
external LLM / UI
-> LLM-adapter
-> micro-node-compatible transition request
-> transition-table role evaluation
-> terminal decision + receipt
-> governed return payload
-> original customer path
```

## Non-claims

This proof does not activate a live provider, live continuity service, repository mutation, public posting, email sending, production trust-kernel execution, or execution authority.

## Required output fields

```text
transition_id
origin_system
return_path
decision
receipt_hash
returned_to_origin
execution_authority_granted
provider_output_is_authority
```

## Goal 4 verification

The Goal 4 verifier checks only fixture-bound compatibility evidence. It does not call the live `micro-node-runtime` package. The live package can be called in a later SDK-mediated integration goal after the micro-node contract is stable on main.
