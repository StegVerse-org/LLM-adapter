#!/bin/sh
set -eu

DATA_DIR="${STEGVERSE_DATA_DIR:-/var/lib/stegverse}"
PORT="${PORT:-8000}"
SIWE_ENABLED="${STEGVERSE_SIWE_ENABLED:-false}"
SIWE_OWNER_DIR="${STEGVERSE_SIWE_OWNER_DIR:-$DATA_DIR/extensions}"

mkdir -p "$DATA_DIR" "$SIWE_OWNER_DIR"

export STEGVERSE_TRANSITION_DB="${STEGVERSE_TRANSITION_DB:-$DATA_DIR/stegverse-ecosystem-chat.db}"
export STEGVERSE_EXTERNAL_REVIEW_DB="${STEGVERSE_EXTERNAL_REVIEW_DB:-$DATA_DIR/stegverse-external-review.db}"
export STEGVERSE_SIWE_DB="${STEGVERSE_SIWE_DB:-$DATA_DIR/stegwallet-siwe.db}"
export STEGVERSE_STORAGE_DURABLE_ACROSS_RESTARTS="${STEGVERSE_STORAGE_DURABLE_ACROSS_RESTARTS:-true}"

if [ "$(printf '%s' "$SIWE_ENABLED" | tr '[:upper:]' '[:lower:]')" = "true" ]; then
  OWNER_WHEEL="${STEGVERSE_SIWE_OWNER_WHEEL:-}"
  EXPECTED_SHA256="${STEGVERSE_SIWE_OWNER_WHEEL_SHA256:-}"

  if [ -z "$OWNER_WHEEL" ]; then
    set -- "$SIWE_OWNER_DIR"/stegwallet_governance-*.whl
    if [ "$#" -ne 1 ] || [ ! -f "$1" ]; then
      echo 'stegwallet_siwe_owner_wheel_required' >&2
      exit 1
    fi
    OWNER_WHEEL="$1"
  fi
  if [ ! -f "$OWNER_WHEEL" ]; then
    echo 'stegwallet_siwe_owner_wheel_missing' >&2
    exit 1
  fi
  if [ -z "$EXPECTED_SHA256" ]; then
    echo 'stegwallet_siwe_owner_wheel_sha256_required' >&2
    exit 1
  fi

  ACTUAL_SHA256="$(python - "$OWNER_WHEEL" <<'PY'
import hashlib
import sys
from pathlib import Path
path = Path(sys.argv[1])
digest = hashlib.sha256()
with path.open('rb') as handle:
    for chunk in iter(lambda: handle.read(1024 * 1024), b''):
        digest.update(chunk)
print(digest.hexdigest())
PY
)"
  NORMALIZED_EXPECTED="${EXPECTED_SHA256#sha256:}"
  if [ "$ACTUAL_SHA256" != "$NORMALIZED_EXPECTED" ]; then
    echo 'stegwallet_siwe_owner_wheel_sha256_mismatch' >&2
    exit 1
  fi

  export PYTHONPATH="$OWNER_WHEEL${PYTHONPATH:+:$PYTHONPATH}"
  python - <<'PY'
from stegwallet import SiwePolicy, SiweStore, recover_with_eth_account
assert SiwePolicy and SiweStore and recover_with_eth_account
print('StegWallet SIWE owner artifact verified and importable.')
PY
fi

python -m llm_adapter.custody_worker

exec uvicorn llm_adapter.combined_gateway:app \
  --host 0.0.0.0 \
  --port "$PORT" \
  --proxy-headers \
  --forwarded-allow-ips='*'
