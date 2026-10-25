"$PYTHON_BIN" - <<'PY'
import json
from pathlib import Path
capability = json.loads(Path('capability/stegverse-intr-kimi-transport.capability.json').read_text(encoding='utf-8'))
schema = json.loads(Path('schemas/kimi-intr-transport-envelope.schema.json').read_text(encoding='utf-8'))
runtime = json.loads(Path('config/kimi-runtime-profile.json').read_text(encoding='utf-8'))
assert capability['capability_id'] == 'stegverse.intr.kimi.transport.v1'
assert capability['provider'] == 'kimi'
assert capability['authority']['authority_effect'] == 'NONE'
assert capability['authority']['synthesizes_allow'] is False
assert capability['credential']['credential_authority'] == 'TV/TVC'
assert capability['credential']['credential_material_present'] is False
assert capability['credential']['direct_credential_resolver_production_allowed'] is False
assert capability['activation']['live'] is False
assert capability['transport']['endpoint_profiles']['moonshot_openai_compatible'] == 'https://api.moonshot.ai/v1'
assert capability['transport']['supported_models'] == ['kimi-k3']
assert schema['properties']['transport_id']['pattern'] == '^kmit-[0-9a-f]{64}$'
assert schema['properties']['authority_effect']['const'] == 'NONE'
assert schema['properties']['egress_intr_required']['const'] is True
assert runtime['profile_id'] == 'stegverse:runtime-profile:llm-adapter-kimi:v1'
assert runtime['base_profile'] == 'stegverse:runtime-profile:hb-intr-resident:v1'
assert runtime['provider_execution']['tvc_profile'] == 'kimi'
assert runtime['provider_execution']['credential_material_in_llm_adapter'] is False
assert runtime['provider_execution']['direct_credential_resolver_production_allowed'] is False
assert runtime['physical_runtime']['another_physical_machine_required'] is False
print('KIMI_INTR_CAPABILITY_DECLARATION=VALID')
print('KIMI_RUNTIME_PROFILE_BINDING=VALID')
print('KIMI_INTR_ACTIVATION_LIVE=false')
PY
