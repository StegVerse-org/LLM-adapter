# Provider-Owned Usage Events

## Goal 8

The adapter records provider-owned usage evidence without treating provider identity, model output, measurements, or provenance references as authority.

```text
provider request
-> provider response / refusal / error
-> provider-owned usage event
-> deterministic event hash
-> return-to-origin receipt requirement
-> optional SDK aggregation
```

## Required boundary

```text
adapter_is_execution_authority == false
provider_response_is_admissibility == false
model_output_is_publication_authority == false
reasoning_provenance_is_full_chain_of_thought == false
usage_measurement_is_value_claim == false
provider_identity_is_actor_authority == false
```

A reasoning-provenance field may contain only a bounded reference. It must not contain or claim to expose private chain-of-thought. Usage measurements describe observed provider activity; they do not establish value, standing, admissibility, authority, attribution, or compensation.

## Event identity

Each event binds:

- provider, model, and model version;
- request and response identifiers and SHA-256 hashes;
- response, refusal, or provider-error state;
- token, latency, and optional compute measurements;
- bounded reasoning-provenance reference;
- origin event identifier and required return receipt;
- explicit non-authority assertions;
- deterministic event SHA-256.

## Verification

```bash
python scripts/verify_provider_usage_event.py
python -m pytest -q tests/test_provider_usage_event.py
```

The canonical fixture is:

```text
fixtures/provider_usage_event.json
```

The machine-readable schema is:

```text
schemas/provider_usage_event.schema.json
```

## SDK handoff posture

An SDK may validate, aggregate, and reference this event, but validation or aggregation does not transfer provider authority, execution authority, custody, publication authority, or admissibility.
