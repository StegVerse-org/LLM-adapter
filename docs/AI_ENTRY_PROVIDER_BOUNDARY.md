# AI Entry Provider Boundary

## Goal 6 role

`LLM-adapter` is the implementation boundary for external provider comparison panes used by the StegVerse AI Entry Point.

The Site may display comparison panes for ChatGPT, Claude, and other providers, but this repository must preserve the rule that external provider output is comparison-only unless passed through governed StegVerse evaluation.

## Boundary contract

```text
Site AI Entry request
-> LLM-adapter provider boundary
-> provider adapter declaration
-> disabled-by-default live call gate
-> comparison response placeholder or governed capture result
-> return to Site/API wrapper response shape
```

## Required default state

```text
live_provider_call_enabled == false
provider_output_is_authority == false
comparison_only == true
credential_surface_enabled == false
provider_secret_required_for_tests == false
receipt_capture_required_before_live_activation == true
```

## Activation requirements

Live provider calls must not be enabled until the following are installed:

1. governed provider adapter approval;
2. secret management boundary;
3. per-request provider capture receipt;
4. comparison-only label retention;
5. SDK or receipt handoff path where required;
6. replay/reconstruction metadata path.

## Non-claims

This boundary does not certify external providers, does not grant authority, does not expose credentials, does not perform live calls by default, and does not replace StegVerse governance.
