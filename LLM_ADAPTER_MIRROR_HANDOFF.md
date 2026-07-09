# LLM Adapter Mirror Handoff

## Current source of truth

This file is the handoff source of truth for `StegVerse-org/LLM-adapter` until superseded.

## Active goal

Goal 9: corrected HPS sibling-input alignment for LLM-origin requests.

Goal 8 HPS adapter consumption is preserved below as installed prior context. Goal 9 corrects the architectural wording: the LLM adapter does not consume SDK route decisions as upstream authority. The LLM adapter is one sibling input nest that consumes HPS-runtime, hybrid-collab-bridge, and Ecosystem-Delegation contracts.

## Goal 9 corrected architecture

```text
Admissible-Existence/HPS
  -> standing-vector formalism

StegVerse-org/HPS-runtime
  -> executable runtime state, standing-vector registers, phases, epochs, capability windows

SDK input            \
LLM-adapter input     \
Site input             -> StegVerse-Labs/hybrid-collab-bridge -> StegVerse-Labs/Ecosystem-Delegation -> next governed boundary
External adapter      /
Manual review        /

master-records/orchestration
  -> cycle state, receipts, participant records, reconstruction references
```

## Goal 9 LLM-adapter role

```text
StegVerse-org/LLM-adapter is an LLM-origin input nest.
It may emit LLM-origin HPS route candidates.
It may block adapter-mediated consequences when HPS route/delegation state denies or fails closed.
It does not grant execution authority.
It does not grant delegation authority.
It does not consume SDK route decisions as upstream authority.
It does not own ecosystem-wide HPS orchestration.
```

## Goal 9 consumption rule

LLM-origin requests should consume:

```text
StegVerse-org/HPS-runtime
  -> runtime state and standing-vector registers

StegVerse-Labs/hybrid-collab-bridge
  -> sibling input route normalization

StegVerse-Labs/Ecosystem-Delegation
  -> governed authority delegation decision

master-records/orchestration
  -> receipts, observation state, reconstruction references
```

`ALLOW`, `ALLOW_NEXT_BOUNDARY`, or `ALLOW_DELEGATION` only permits the LLM-origin route to continue to the next governed boundary. It is not execution authority.

## Goal 9 installed by handoff update

```text
LLM_ADAPTER_MIRROR_HANDOFF.md updated to correct LLM-adapter role from SDK route consumer to sibling input consumer.
```

## Goal 9 remaining work

```text
- Update docs/HPS_ADAPTER_CONSUMPTION.md to match the corrected sibling-input architecture.
- Update examples/verifier later only if bridge/delegation runtime contracts require a different LLM-origin route shape.
- Observe LLM-adapter workflow/test result and replace pending observation receipt.
```

---

## Preserved Goal 8 context

Goal 8: HPS adapter consumption.

Goal 7 bounded free-tier trust activation is preserved below as completed prior context. Goal 8 added bounded HPS adapter behavior before adapter-mediated consequence.

## Superseded Goal 8 upstream wording

The prior wording said Goal 8 consumed SDK HPS route decisions before adapter-mediated consequence. That is now superseded by the corrected architecture:

```text
HPS-runtime owns executable runtime semantics.
hybrid-collab-bridge owns sibling route normalization.
Ecosystem-Delegation owns governed delegation evaluation.
SDK is one sibling input nest.
LLM-adapter is one sibling input nest.
master-records/orchestration owns ecosystem cycle records and receipts.
```

## Goal 8 route consumption rule

```text
Adapter output is not execution.
HPS route ALLOW is not execution authority.
HPS route DENY or FAIL_CLOSED must block adapter-mediated consequence.
```

## Installed for Goal 8

```text
docs/HPS_ADAPTER_CONSUMPTION.md
examples/hps_adapter_route_allowed.json
examples/hps_adapter_route_denied.json
examples/hps_adapter_route_fail_closed.json
scripts/verify_hps_adapter_consumption.py
tests/test_hps_adapter_consumption.py
LLM_ADAPTER_MIRROR_HANDOFF.md updated
```

## Goal 8 verification commands

```bash
python scripts/verify_hps_adapter_consumption.py examples/hps_adapter_route_allowed.json
python scripts/verify_hps_adapter_consumption.py examples/hps_adapter_route_denied.json
python scripts/verify_hps_adapter_consumption.py examples/hps_adapter_route_fail_closed.json
pytest tests/test_hps_adapter_consumption.py -v
```

## Corrected downstream sync targets

```text
StegVerse-org/HPS-runtime
  -> supplies runtime state and standing-vector registers

StegVerse-Labs/hybrid-collab-bridge
  -> consumes LLM-origin route candidates as sibling input

StegVerse-Labs/Ecosystem-Delegation
  -> evaluates governed authority delegation after bridge normalization

StegVerse-Labs/Site
  -> consumes HPS visualization status and adapter consumption state

StegVerse-Labs/admissibility-wiki
  -> explains HPS route/delegation consumption after Site/adapter records align

master-records/orchestration
  -> preserves HPS runtime, bridge, delegation, SDK, adapter, Site, and mirror receipts
```

---

## Preserved Goal 7 context

Goal 7: bounded free-tier trust activation for the StegVerse governed LLM entry point.

Goal 4 proved the micro-node governed return-path fixture. Goal 6 provided the adapter-side pieces needed by the StegVerse AI Entry Point: provider comparison boundary, backend response scaffold, pure endpoint function, and service wrapper scaffold. Goal 7 added the free-tier trust policy, quota evaluation boundary, receipt/replay/reconstruction limit boundary, Site-facing response metadata, aggregate verification wiring, README/status documentation, and machine-readable capability manifest support so a public user can build confidence through bounded live governed inquiries rather than static demonstration material.

## Goal 6 proof path

```text
Site AI Entry request
-> LLM-adapter endpoint wrapper
-> backend response scaffold
-> provider comparison boundary
-> preview metadata
-> response shape for Site
```

## Goal 7 trust path

```text
public user inquiry
-> bounded free-tier quota envelope
-> governed LLM adapter request
-> Site-visible free-tier trust metadata
-> transition receipt inspection
-> bounded receipt export / replay / reconstruction limits
-> machine-readable capability discovery
-> aggregate verifier coverage
-> upgrade only for scale, retention, connectors, premium models, or API depth
```

## Installed baseline already present

```text
adapter.capabilities.json
docs/ACTIVATION_STATUS.md
docs/GOVERNED_LLM_RUNTIME.md
fixtures/governed_response_fixture.json
llm_adapter/
scripts/smoke_governed_session.py
tests/
README.md
```

## Installed for Goal 4

```text
docs/MICRO_NODE_RETURN_PATH.md
examples/micro_node_return_path/request.json
examples/micro_node_return_path/governed_return.json
scripts/verify_micro_node_return_path.py
tests/test_micro_node_return_path.py
```

## Installed for Goal 6

```text
docs/AI_ENTRY_PROVIDER_BOUNDARY.md
llm_adapter/ai_entry_provider_boundary.py
llm_adapter/ai_entry_backend_service.py
llm_adapter/ai_entry_endpoint.py
llm_adapter/ai_entry_service_wrapper.py
scripts/verify_ai_entry_provider_boundary.py
scripts/verify_ai_entry_backend_service.py
scripts/verify_ai_entry_endpoint.py
scripts/verify_ai_entry_service_wrapper.py
tests/test_ai_entry_provider_boundary.py
tests/test_ai_entry_backend_service.py
tests/test_ai_entry_backend_preview_marker.py
tests/test_ai_entry_endpoint.py
tests/test_ai_entry_service_wrapper.py
scripts/verify_goal4.py updated to include Goal 6 checks
```

## Installed for Goal 7

```text
docs/FREE_TIER_TRUST_POLICY.md
examples/free_tier_trust_policy.json
llm_adapter/free_tier_quota.py
llm_adapter/free_tier_limits.py
llm_adapter/ai_entry_backend_service.py updated with free_tier_trust metadata
adapter.capabilities.json updated with free-tier trust fields
scripts/verify_free_tier_quota.py
scripts/verify_free_tier_limits.py
scripts/verify_ai_entry_free_tier_metadata.py
scripts/verify_free_tier_capability_manifest.py
scripts/verify_goal4.py updated to include Goal 7 checks
tests/test_free_tier_quota.py
tests/test_free_tier_limits.py
tests/test_ai_entry_free_tier_trust_metadata.py
README.md updated with free-tier trust boundary
docs/ACTIVATION_STATUS.md updated with Goal 7 status
```

## Required invariant

```text
provider_output_is_authority == false
comparison_only == true
live_provider_call_enabled == false
credential_surface_enabled == false
provider_secret_required_for_tests == false
receipt_capture_preview_only == true
endpoint_side_effects_performed == false
service_wrapper_live_calls_enabled == false
fixture_mode_default == true
returned_to_origin == true
free_tier_is_bounded_live_use == true
static_demo_is_sufficient_trust_proof == false
site_metadata_exposes_free_tier_trust == true
capability_manifest_exposes_free_tier_trust == true
aggregate_verifier_covers_goal7 == true
quota_allow_is_admissibility == false
quota_allow_is_execution_authority == false
limit_allow_is_admissibility == false
limit_allow_is_execution_authority == false
replay_grants_commit_time_standing == false
reconstruction_grants_commit_time_standing == false
receipt_export_is_permanent_retention == false
upgrade_changes_admissibility_requirements == false
hps_route_decision_is_execution_authority == false
adapter_output_is_execution_authority == false
route_deny_blocks_consequence == true
route_fail_closed_blocks_consequence == true
route_allow_only_allows_next_boundary == true
sdk_and_llm_adapter_are_sibling_input_nests == true
llm_adapter_consumes_sdk_route_authority == false
```

## Canonical verification command

```bash
python scripts/verify_goal4.py
```

Additional Goal 8 verification:

```bash
python scripts/verify_hps_adapter_consumption.py examples/hps_adapter_route_allowed.json
python scripts/verify_hps_adapter_consumption.py examples/hps_adapter_route_denied.json
python scripts/verify_hps_adapter_consumption.py examples/hps_adapter_route_fail_closed.json
python -m pytest tests/test_hps_adapter_consumption.py -v
```

## Remaining files or modules to install

```text
StegVerse-org/LLM-adapter:
  - docs/HPS_ADAPTER_CONSUMPTION.md wording alignment to corrected sibling-input architecture
  - observed LLM-adapter HPS workflow/test receipt

StegVerse-org/StegVerse-SDK:
  - aligned handoff/docs so it consumes runtime + bridge + delegation as sibling input, not as adapter authority

master-records/orchestration:
  - replace pending LLM-adapter observation receipt when workflow/test output is observed

StegVerse-Labs/Site:
  - public HPS visualization / ecosystem chat integration after Site handoff review
```

## Archive posture

This handoff preserves Goal 9 corrected HPS sibling-input alignment, Goal 8 HPS adapter consumption state, and prior Goal 7 bounded free-tier trust activation state so the complete thread can be archived without needing additional context to continue.
