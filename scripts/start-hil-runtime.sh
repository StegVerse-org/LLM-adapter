#!/bin/sh
set -eu

ENV_FILE="${HIL_ENV_FILE:-.env.hil.local}"
BASE_URL="${HIL_BASE_URL:-http://127.0.0.1:${PORT:-8000}}"

if ! command -v docker >/dev/null 2>&1; then
  echo "docker is required" >&2
  exit 1
fi
if ! docker compose version >/dev/null 2>&1; then
  echo "docker compose is required" >&2
  exit 1
fi

if [ ! -f "$ENV_FILE" ]; then
  umask 077
  REVIEW_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
  PUBLICATION_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
  cat > "$ENV_FILE" <<EOF
PORT=${PORT:-8000}
STEGVERSE_NODE_ID=${STEGVERSE_NODE_ID:-ecosystem-chat-portable-node}
STEGVERSE_ALLOWED_ORIGINS=${STEGVERSE_ALLOWED_ORIGINS:-http://localhost:8000,http://127.0.0.1:8000,https://stegverse-labs.github.io}
STEGVERSE_HIL_INTAKE_ENABLED=true
STEGVERSE_HIL_REVIEW_TOKEN=$REVIEW_TOKEN
STEGVERSE_HIL_PUBLICATION_TOKEN=$PUBLICATION_TOKEN
EOF
  echo "Created $ENV_FILE with distinct local review and publication secrets."
fi

docker compose --env-file "$ENV_FILE" up --build -d

attempt=0
until python - "$BASE_URL" <<'PY'
import json, sys, urllib.request
base = sys.argv[1].rstrip('/')
with urllib.request.urlopen(base + '/api/hil/readiness', timeout=5) as response:
    payload = json.load(response)
expected_primary = 'a7b1c62e336b4e244ecf7fdcd10af195401f6c44328de32615b073d2a5c3c462'
expected_prompt = 'cdff8d2266bb3eefbb6e5d28d9adc548e6c8dfc039debd72fe404f1d0249912c'
if payload.get('state') != 'READY':
    raise SystemExit(1)
if payload.get('primary_sha256') != expected_primary:
    raise SystemExit(1)
if payload.get('prompt_sha256') != expected_prompt:
    raise SystemExit(1)
if payload.get('provenance_manifest_required') is not True:
    raise SystemExit(1)
print(json.dumps(payload, indent=2, sort_keys=True))
PY
do
  attempt=$((attempt + 1))
  if [ "$attempt" -ge 30 ]; then
    echo "HIL runtime did not become ready. Inspect: docker compose --env-file $ENV_FILE logs" >&2
    exit 1
  fi
  sleep 2
done

echo "HIL receiver is ready at $BASE_URL"
echo "Secrets remain in $ENV_FILE; do not commit that file."
