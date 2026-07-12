# LLM Adapter Entry-Point Role

## Primary role

The StegVerse LLM Adapter is the machine-readable translation and interoperability boundary for LLMs, agents, tools, and external frameworks.

It can support the same broad classes of intake, testing, comparison, and module interaction available through the SDK, but its distinguishing responsibility is conversion into canonical StegVerse structures.

```text
external prompt / provider output / agent trace / tool trace
-> canonical intent
-> transition identity
-> manifest and evidence references
-> route and governance posture
-> provider-neutral telemetry
-> machine-readable result
-> receipt handoff
```

## Related roles

- provider abstraction;
- external-system compatibility bridge;
- recursive-call and token telemetry capture;
- model-output normalization;
- agent-trace conversion;
- machine-readable governance packaging;
- return-path normalization.

## Relationship to other entry points

The SDK is the developer-native contract surface. Ecosystem Chat is the universal browser-based guidance, discovery, governed-chat, development, and orchestration surface. The LLM Adapter translates between external model activity and the contracts consumed by those surfaces and by governed runtimes.

No strict sequence is required. Each entry point may route directly to an authorized ecosystem service while preserving the same session and transition lineage.

## Shared continuity requirements

Every adapter event participating in a cross-entry session must preserve:

```text
session_id
transition_id
parent_transition_id
origin_entry_point
current_processor = llm_adapter
interaction_type
measurement_id
metric_owner
receipt_refs
```

## Usage ownership

The adapter owns only measurements it directly observes or receives from a provider under a declared evidence class. Typical adapter-owned measurements include provider calls, provider tokens, provider latency, recursive calls, tool calls, retries, and adapter translation overhead.

The adapter must not duplicate SDK, runtime, Site, or Master-Records measurements. Configured or modeled values must not be labeled `MEASURED`.

## Authority boundary

```text
adapter acceptance != authority
format conversion != admissibility
provider output != authority
telemetry capture != validation of correctness
receipt generation != publication or execution authority
```

The canonical cross-entry role schema is maintained in `StegVerse-org/StegVerse-SDK/schemas/entry_point_role.schema.json` until a separately governed ecosystem schema registry supersedes it.
