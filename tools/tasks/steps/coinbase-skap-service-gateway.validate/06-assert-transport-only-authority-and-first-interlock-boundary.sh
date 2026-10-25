python3 - <<'PY'
from pathlib import Path
source = Path('llm_adapter/service_gateway_coinbase_skap.py').read_text(encoding='utf-8')
api = Path('llm_adapter/service_gateway_composed.py').read_text(encoding='utf-8')
deployed = Path('llm_adapter/deployed_gateway.py').read_text(encoding='utf-8')
combined = Path('llm_adapter/combined_gateway.py').read_text(encoding='utf-8')
native = Path('scripts/stegdeploy_native_gateway.py').read_text(encoding='utf-8')
runtime = Path('llm_adapter/runtime_gateway.py').read_text(encoding='utf-8')
safe_log = Path('llm_adapter/query_safe_access_log.py').read_text(encoding='utf-8')
extcollab = Path('llm_adapter/service_gateway_external_collab_consent.py').read_text(encoding='utf-8')
assert 'gateway_credential_value_access": False' in source
assert 'gateway_decryption_authority": False' in source
assert 'gateway_execution_authority": "NONE"' in source
assert 'tvc_admission_completed": False' in source
assert 'KV_SKAP_VAULT_INTERLOCK_ADMISSION' in source
assert 'device_kv_interlock_receipt' in source
assert 'from_boundary": "DEVICE"' in source
assert 'to_boundary": "KV"' in source
assert 'connector": "InTr"' in source
assert 'prior_boundary_receipt_hash": None' in source
assert 'secret_plaintext_present": False' in source
assert 'authority_transfer": False' in source
assert 'credential_values_available' in source
assert 'allowed_keys' in source
assert 'authorization_header_forbidden' in api
assert 'cookie_header_forbidden' in api
assert '/api/coinbase/skap/ingress' in api
assert '/api/coinbase/skap/readiness' in deployed
assert '/api/coinbase/skap/ingress' in deployed
assert '/.well-known/acme-challenge/{token}' in deployed
http01 = Path('llm_adapter/service_gateway_http01.py').read_text(encoding='utf-8')
assert 'STEGVERSE_TVC_HTTP01_CHALLENGE_ROOT' in http01
assert 'TV/TVC' in http01
assert 'no-store' in http01
for forbidden in ('private_key', 'sign_jws', 'newAccount', 'newOrder', 'revokeCert', 'dns-01'):
    assert forbidden not in http01
assert 'coinbase_skap_readiness_endpoint' in combined
assert 'coinbase_skap_ingress_endpoint' in combined
assert 'coinbase_skap_gateway_execution_authority' in combined
assert 'STEGDEPLOY_NATIVE_TLS_CERT_FILE' in native
assert 'STEGDEPLOY_NATIVE_TLS_KEY_FILE' in native
assert 'ssl_keyfile=key' in native
assert 'access_log=False' in native
assert 'tls_private_key_material_recorded' in native
assert 'production_public_route_observed' in native
assert 'access_log=False' in runtime
assert 'QuerySecretSafeAccessLogMiddleware(_base_app)' in runtime
assert 'service_gateway_external_collab_consent' in runtime
assert 'UPSTREAM_ORIGIN = "http://127.0.0.1:8786"' in extcollab
assert 'session.trust_env = False' in extcollab
assert 'CALLBACK_ALLOWED_QUERY_KEYS' in extcollab
assert 'allow_redirects=False' in extcollab
for route in (
    '/tvc/external-collaboration/google-drive/consent/begin',
    '/tvc/google-drive/external-collaboration/callback',
    '/tvc/external-collaboration/google-drive/consent/health',
):
    assert route in extcollab
for forbidden in ('scope.get("query_string")', "scope['query_string']", 'scope.get("raw_path")', "scope['raw_path']", 'scope.get("headers")', "scope['headers']"):
    assert forbidden not in safe_log
print('COINBASE_SKAP_GATEWAY_VALIDATION_ONLY=true')
print('COINBASE_SKAP_GATEWAY_CREDENTIAL_AUTHORITY=NONE')
print('COINBASE_SKAP_GATEWAY_EXECUTION_AUTHORITY=NONE')
print('COINBASE_SKAP_DEVICE_KV_INTR_RECEIPT_REQUIRED=true')
print('COINBASE_SKAP_NEXT_TRANSITION=KV_SKAP_VAULT_INTERLOCK_ADMISSION')
print('SERVICE_GATEWAY_QUERY_SAFE_ACCESS_LOGGING=PASS')
print('EXTERNAL_COLLAB_CONSENT_ROUTE_SOURCE=PASS')
PY
