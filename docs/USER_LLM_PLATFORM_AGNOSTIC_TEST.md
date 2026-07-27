# Platform-agnostic user-LLM capability test

Render is not part of the activation or test path.

The bounded user-LLM surface is exercised through the repository-owned Dockerfile and `compose.yaml` contract.

## Start

Set required local HIL tokens and start the portable node:

```bash
export STEGVERSE_HIL_REVIEW_TOKEN=local-review-token
export STEGVERSE_HIL_PUBLICATION_TOKEN=local-publication-token
docker compose up --build -d
```

The compose service enables the explicit non-authoritative user-LLM fixture transport and exposes the mounted surface at:

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

This test validates the portable service boundary and governed request-return path. It does not claim execution, publication, continuity, or Master-Records custody authority.
