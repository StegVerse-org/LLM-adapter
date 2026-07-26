# Internal Governed Reference Suite

This directory starts the StegVerse internally executed, publicly replayable test program.

## Evidence posture

Every run is labeled:

- `INTERNAL_EXECUTION`
- `public_replayable: true`
- `independently_reproduced: false`
- `production_observed: false`

Internal control of the runner is disclosed. The suite does not claim independent validation, live deployment, production assurance, or external audit.

## Initial vectors

The first tranche covers:

1. valid standing and unchanged policy;
2. delegation expiration at commit time;
3. delegation revocation before commit;
4. invalid commit-time standing;
5. policy mutation after review;
6. restricted-request fail-closed behavior;
7. deterministic receipt-chain replay;
8. transition-state serialization and restart simulation.

## Reproduce locally

```bash
python internal_tests/run_governed_reference_suite.py
```

The command writes `internal_tests/artifacts/governed-reference-results.json`.

A passing run establishes only deterministic reference behavior for the declared vectors and public replayability of the generated evidence packet. It does not establish deployed runtime operation, provider invocation, durable infrastructure persistence, HIL custody, independent reproduction, or production assurance.
