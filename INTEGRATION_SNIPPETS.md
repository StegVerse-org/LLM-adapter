# LLM-adapter Integration Snippets

Add this section to the root `README.md` near the governed runtime activation section.

```md
## End-to-end governed LLM demonstrator

This repository includes a fixture-first governed LLM demonstrator.

```text
fixture query
  -> provider request envelope
  -> fixture provider response
  -> continuity evidence pointers
  -> governed session packet
  -> action route
  -> commitment request
  -> authority decision
  -> disabled execution handoff
  -> demo report artifacts
  -> replay verification
  -> reconstruction verification
```

Run:

```bash
python scripts/run_end_to_end_demo.py --fixture examples/end_to_end/simple_query.json
python scripts/replay_demo.py --session-report examples/reports/simple_query.session.json
python scripts/reconstruct_demo.py --session-report examples/reports/simple_query.session.json
pytest tests/test_end_to_end_demo.py -v
```

See:

```text
docs/END_TO_END_DEMO.md
```

The demonstrator is fixture-first. It does not call live providers, mutate repositories, publish publicly, send messages, grant authority, or execute side effects.
```
