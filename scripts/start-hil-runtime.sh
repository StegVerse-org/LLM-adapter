#!/bin/sh
# Start the governed HIL v1.1 receiver on the host-native launcher.
# The start closes when the gateway process is spawned. Readiness is observed
# once afterwards and reported; it is never awaited and never gates the start.
set -eu

ENV_FILE="${HIL_ENV_FILE:-.env.hil.local}"
PORT="${PORT:-8000}"
BASE_URL="${HIL_BASE_URL:-http://127.0.0.1:${PORT}}"

if [ ! -f "$ENV_FILE" ]; then
  umask 077
  REVIEW_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
  PUBLICATION_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
  cat > "$ENV_FILE" <<EOF
PORT=${PORT}
STEGVERSE_NODE_ID=${STEGVERSE_NODE_ID:-ecosystem-chat-portable-node}
STEGVERSE_ALLOWED_ORIGINS=${STEGVERSE_ALLOWED_ORIGINS:-http://localhost:8000,http://127.0.0.1:8000,https://stegverse-labs.github.io}
STEGVERSE_HIL_INTAKE_ENABLED=true
STEGVERSE_HIL_REVIEW_TOKEN=$REVIEW_TOKEN
STEGVERSE_HIL_PUBLICATION_TOKEN=$PUBLICATION_TOKEN
EOF
  echo "Created $ENV_FILE with distinct local review and publication secrets."
fi

set -a
. "./$ENV_FILE"
set +a

python scripts/stegdeploy_native_gateway.py start --port "$PORT"

python - "$BASE_URL" <<'PY'
import json, sys, urllib.request
base = sys.argv[1].rstrip('/')
report = {"gates_start": False, "reconciliation_entrypoint": "GET " + base + "/api/hil/readiness"}
try:
    with urllib.request.urlopen(base + '/api/hil/readiness', timeout=5) as response:
        payload = json.load(response)
    report["consequence_observation"] = "OBSERVED"
    report["readiness"] = payload
    report["v1_1_hashes_match"] = (
        payload.get('state') == 'READY'
        and payload.get('primary_sha256') == 'a7b1c62e336b4e244ecf7fdcd10af195401f6c44328de32615b073d2a5c3c462'
        and payload.get('prompt_sha256') == 'cdff8d2266bb3eefbb6e5d28d9adc548e6c8dfc039debd72fe404f1d0249912c'
        and payload.get('provenance_manifest_required') is True
    )
except Exception as exc:
    report["consequence_observation"] = "NOT_AUTHENTICALLY_OBSERVED"
    report["reason"] = "hil_readiness_not_observed:" + type(exc).__name__
print(json.dumps(report, indent=2, sort_keys=True))
PY

echo "Secrets remain in $ENV_FILE; do not commit that file."
