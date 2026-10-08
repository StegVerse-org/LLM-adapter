# LLM-adapter Purpose, Boundary, and Capability Specification

Status: **DRAFT FOR OWNER REVIEW**  
Normative effect: **NONE until approved and merged**  
Goal context: `SHWP-ECOSYSTEM-CHAT-INFERENCE-001`

## 1. Purpose

LLM-adapter is the LLM-accessible ingress adapter to the existing StegVerse SDK.

Its purpose is to allow an eligible source operating as a registered healthy StegVerse Node to cross the existing governed Node/LLM boundary and address the existing SDK. The established relationship is:

```text
registered healthy Node/source
        |
        v
    LLM-adapter
        |
        v
   StegVerse SDK
        |
        v
SDK-selected processing / installed runtime / downstream governed operation
        |
        v
 disposition + receipts + retained evidence / result return
```

This specification does **not** redefine whether that path exists. Successful ingress through LLM-adapter to the SDK and beyond is an established system capability and is a preservation requirement for future work.

## 2. Source neutrality

LLM-adapter does not define one privileged source type.

Potential sources include, without limitation:

- StegBrowser when it is operating as an eligible registered healthy Node;
- another machine operating as an eligible registered healthy Node;
- another StegNode;
- an Ecosystem Chat execution surface when it satisfies the same applicable Node/standing requirements.

Source identity is provenance and admission context. It does not by itself select a processing capability, route, execution owner, provider, or disposition.

## 3. Boundary

LLM-adapter terminates the LLM-accessible Node crossing and exposes the existing SDK behind that crossing.

It MUST NOT become:

- a second SDK;
- an alternate SDK ingress that bypasses the canonical SDK boundary;
- an independent authority plane;
- a general-purpose external-AI broker;
- a capability registry that competes with the SDK capability map;
- a route-selection authority independent of the SDK;
- a persistent credential authority;
- a new Node class;
- a device prerequisite;
- an execution owner merely because a request entered through it.

Once admission/standing requirements are satisfied, SDK-owned contracts determine the requested SDK operation and its downstream consequences.

## 4. Required admission capabilities

Before an actionable SDK crossing, the adapter must be able to consume or verify the existing evidence required by canonical Node/standing contracts. At minimum the architecture requires:

1. **Registered Node identity** — the source is represented through the existing Node-registration mechanism.
2. **Healthy Node state** — the applicable existing health/standing predicate is satisfied for the crossing.
3. **Non-caller-editable standing evidence** — standing is obtained from the existing authoritative mechanism; the adapter does not synthesize it.
4. **Ingress disposition** — every attempted boundary crossing terminates in the existing disposition vocabulary, including non-ALLOW outcomes when admission requirements are not satisfied.
5. **Receipt/provenance preservation** — source identity, request correlation, standing/admission evidence and resulting SDK crossing evidence remain attributable.

The exact canonical schemas and producers remain owned by their existing contracts. This document does not create replacements.

## 5. SDK capabilities exposed through the adapter

The adapter must make the existing SDK machine-facing lifecycle addressable to an admitted LLM/Node source as applicable to the requested operation.

The required generic capability set is:

### 5.1 Discover / explain

The source can obtain sufficient SDK-owned machine contract and capability information to determine how an applicable request is represented.

Discovery is not manifest construction, submission or execution.

### 5.2 Build

When requested, caller/source-native input can be supplied to the existing SDK Manifest Builder using the applicable SDK-defined processor/capability inputs.

Manifest construction does not imply submission.

### 5.3 Validate

A constructed or supplied manifest can be passed through the existing SDK validation contract.

Validation does not imply submission or execution.

### 5.4 Submit

An explicitly requested manifest can cross the existing SDK submission boundary.

Submission preserves the manifest-selected capability and route and must not silently substitute another capability or execution context.

A submission/handoff response must not be embellished into a runtime result.

### 5.5 Result/evidence return

When the existing SDK/runtime returns authentic result evidence, LLM-adapter must preserve the SDK/runtime disposition and evidence identity rather than reinterpret it as a different transition.

The governing disposition vocabulary remains:

- `ALLOW`
- `DENY`
- `FAIL_CLOSED`

Any observation state required by an applicable existing contract remains distinct from an invented success claim.

## 6. Capability and route ownership

LLM-adapter does not infer downstream execution from the source type.

The SDK remains authoritative for:

- capability discovery;
- manifest semantics;
- processor/capability selection;
- route compatibility and selection;
- validation;
- submission semantics;
- installed-runtime resolution;
- downstream execution ownership;
- result admission;
- receipt/evidence semantics.

Therefore:

```text
source_node_type != processing.capability
source_node_type != processing.route_id
source_node_type != execution_owner
```

A name appearing in an SDK capability or route identifier is not, by itself, evidence that the similarly named source owns execution.

## 7. External LLM/provider capability

External provider execution, where required by an SDK-selected capability, is subordinate to the SDK-selected operation.

`external_llm_connection` may serve as an existing provider-neutral text/reasoning primitive only where an applicable canonical capability/route actually resolves to that primitive.

It MUST NOT be treated as:

- the definition of LLM-adapter;
- an automatic consequence of every LLM-adapter ingress;
- an automatic consequence of a StegBrowser source;
- an independent provider broker outside SDK selection;
- a source of governance authority.

Provider responses remain evidence/output of the selected operation and do not acquire governance authority by being returned.

## 8. Ecosystem Chat relationship

Ecosystem Chat is the public first-class LLM conversational interface for StegVerse.

Its informational role is separate from SDK execution. An informational question does not cause a manifest build, validation, submission or execution merely because the conversation can access the SDK.

When the user explicitly requests an SDK operation, Ecosystem Chat may use the same admitted LLM-adapter -> SDK relationship available to other eligible registered healthy-node sources.

For SDK-oriented requests it must be possible, as applicable, to:

1. explain the applicable SDK capability and manifest requirements;
2. build the manifest when requested;
3. validate the manifest when requested;
4. submit the manifest when requested;
5. retain the machine-readable returned evidence;
6. report the result according to the manifest and exact SDK/runtime disposition.

Conversational explanation must remain distinguishable from governed machine evidence.

## 9. Preservation requirements

Any implementation change claiming conformance with this specification must preserve:

- the already-established LLM-adapter -> SDK -> downstream relationship;
- registered healthy-node admission;
- authoritative standing;
- canonical manifest validation;
- manifest-selected route semantics;
- InTr where required by the existing path;
- TV/TVC where required by the selected capability;
- receipt and provenance continuity;
- Master Records organization-record behavior where applicable;
- exact `ALLOW` / `DENY` / `FAIL_CLOSED` semantics;
- existing successful paths not implicated by the proposed change.

A scoped `NOT_PROVEN`, `NOT_OBSERVED`, source-only validation statement, or missing evidence for a new invocation MUST NOT be generalized into a claim that an independently established working capability does not exist.

## 10. Change-safety rule

Uncertainty is not authorization to mutate architecture.

Before changing an established boundary, route, execution owner, standing mechanism or SDK relationship, a change must identify concrete canonical evidence demonstrating that the existing behavior is incorrect or no longer applicable.

Local naming, a single source file, or a historical non-claim is insufficient by itself to redefine system architecture.

## 11. Required implementation capabilities summary

A conforming LLM-adapter/SDK integration therefore requires the existing system to provide, without duplicating authority:

- Node registration and health determination;
- standing readback/admission;
- LLM-adapter ingress crossing and receipt;
- SDK machine-contract/capability discovery;
- generic manifest construction;
- manifest validation;
- explicit manifest submission;
- SDK capability/route resolution;
- installed-runtime/downstream dispatch;
- capability-specific InTr and TV/TVC where applicable;
- result admission/readback;
- receipt, provenance and custody retention;
- machine-readable non-ALLOW evidence when a requested transition cannot proceed;
- conversational rendering that does not alter the underlying machine disposition.

## 12. Explicit non-goals

This specification does not propose:

- a new SDK;
- a new ingress;
- a new route;
- a new broker;
- a new runtime;
- a new capability registry;
- a new credential authority;
- a new device prerequisite;
- a new authority plane;
- a new external-AI Node identity;
- a StegBrowser-specific SDK architecture;
- migration of existing working paths solely to normalize naming.

## 13. Review questions

Owner review should answer only whether this document accurately captures the intended architecture and preservation requirements.

Implementation changes, if any are later demonstrated necessary, should be proposed separately and should cite the exact violated clause and repository evidence. Approval of this specification alone does not authorize runtime mutation.
