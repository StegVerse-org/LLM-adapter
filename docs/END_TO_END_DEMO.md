# End‑to‑End Governed LLM Demonstration

This document describes the end‑to‑end **governed LLM** demonstration packaged with the StegVerse LLM adapter.  The purpose of the demonstration is to showcase how a language model can operate within a fully governed workflow without obtaining execution authority.  All actions are simulated using static fixtures so that the demonstration can be run, replayed, and reconstructed deterministically.

## Demonstration Flow

Running the demo takes a single JSON fixture describing a user query and produces a sequence of governed artifacts:

```text
fixture query → provider request envelope
 → fixture provider response → continuity evidence pointers
 → governed session packet → action route
 → commitment request → authority decision
 → disabled execution handoff → SDK artifacts (intake, manifest, receipt)
 → demo report
```

The demonstration includes three example fixtures in `examples/end_to_end/`:

| Fixture | Description | Expected Outcome |
| --- | --- | --- |
| `simple_query.json` | A basic informational query (“What is the capital of France?”). | `ALLOW` |
| `action_commit_candidate.json` | Simulates a request that results in a commit‑time candidate (drafting a commit message). | `QUARANTINE` |
| `stale_evidence_query.json` | Uses the informational query but simulates stale evidence during reconstruction. | `QUARANTINE` |

## Running the Demo

To execute the demo, run the following command from the root of the LLM adapter repository:

```bash
python scripts/run_end_to_end_demo.py --fixture examples/end_to_end/simple_query.json
```

Replace `simple_query.json` with any of the other fixtures to exercise different paths.  The script prints the governed session packet, the SDK intake result, the manifest, and the receipt to the console and writes them as JSON files in a `reports/` directory adjacent to the fixture.

The scripts `replay_demo.py` and `reconstruct_demo.py` in the `scripts/` directory provide additional functionality:

* `replay_demo.py` replays a generated session report to verify that the original request hash and provider response can be reproduced from the stored query.
* `reconstruct_demo.py` simulates stale evidence by marking the evidence pointers as expired and shows how the authority decision changes when evidence is no longer fresh.

## Verifying the Demonstration

After running the demo, you can validate the resulting session packet and SDK artifacts using the verification scripts in the StegVerse SDK repository.  Follow the instructions in the SDK’s `examples/governed_llm_demo/README.md` to run the verification script against the generated session report.

Additionally, the admissibility‑wiki repository provides public documentation describing the demo and a script (`check_governed_llm_demo_docs.py`) to ensure that the documentation is correctly installed and linked.  See the wiki pages for details.

## Important Invariants

The demo enforces the following invariants to ensure safety and reproducibility:

1. **No live provider calls** – all provider outputs are returned from fixture classes, not external services.
2. **No live continuity service** – evidence pointers are generated locally and marked stale only during reconstruction.
3. **No repository mutation** – the demo does not commit changes or publish actions; commit and send actions are quarantined.
4. **No execution authority** – the disabled execution handoff prevents automatic execution of any actions.

These invariants allow the demonstration to be run repeatedly without side effects or network dependencies.
