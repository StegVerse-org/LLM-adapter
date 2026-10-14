# Platform-agnostic user-LLM capability test

Render is not part of the activation or test path, and neither is a container framework.

The canonical sovereign local-model discovery, launch, inference and proof live in `StegVerse-002/micro-node-runtime`. This repository keeps the bounded user-LLM surface and its smoke test.

## Start

Set the local HIL tokens and the explicit non-authoritative user-LLM fixture transport, then start the gateway on the host-native launcher:

```bash
export STEGVERSE_HIL_REVIEW_TOKEN=local-review-token
export STEGVERSE_HIL_PUBLICATION_TOKEN=local-publication-token
export STEGVERSE_USER_LLM_TEST_MODE=true
python scripts/stegdeploy_native_gateway.py start --port 8000
```

The mounted surface is:

- `http://127.0.0.1:8000/user-llm/healthz`
- `http://127.0.0.1:8000/user-llm/readyz`
- `http://127.0.0.1:8000/user-llm/v1/user-llm/activation-proof`
- `http://127.0.0.1:8000/user-llm/v1/user-llm/requests`

## Verify

```bash
STEGVERSE_USER_LLM_BASE_URL=http://127.0.0.1:8000/user-llm \
python scripts/user_llm_smoke_test.py
```

Expected result:

- health `OK`
- readiness `READY`
- activation `ACTIVATED`
- `authority_attached` is `false`
- test mode remains explicit
- downstream execution remains unverified

This test validates the portable service boundary and governed request-return path. It does not claim execution, publication, continuity, or Master Records organization-record authority.
