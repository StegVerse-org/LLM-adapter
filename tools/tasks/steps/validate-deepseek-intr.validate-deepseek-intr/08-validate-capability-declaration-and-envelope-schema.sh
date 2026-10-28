"$PYTHON_BIN" - <<'PY'
import json
from pathlib import Path

capability = json.loads(Path('capability/stegverse-intr-deepseek-transport.capability.json').read_text(encoding='utf-8'))
schema = json.loads(Path('schemas/deepseek-intr-transport-envelope.schema.json').read_text(encoding='utf-8'))
root = json.loads(Path('adapter.capabilities.json').read_text(encoding='utf-8'))
runtime = json.loads(Path('config/deepseek-runtime-profile.json').read_text(encoding='utf-8'))

assert capability['capability_id'] == 'stegverse.intr.deepseek.transport.v1'
assert capability['provider'] == 'deepseek'
assert capability['authority']['authority_effect'] == 'NONE'
assert capability['authority']['synthesizes_allow'] is False
assert capability['authority']['ingress_decision_point'] == 'external:StegVerse-Interlock/InTr'
assert capability['authority']['egress_decision_point'] == 'external:StegVerse-Interlock/InTr'
assert capability['credential']['credential_authority'] == 'TV/TVC'
assert capability['credential']['credential_class'] == 'TV_TVC_PROVIDER_SECRET'
assert capability['credential']['credential_material_present'] is False
assert capability['credential']['persisted'] is False
assert capability['independence']['canonical_sovereign_route_replaced'] is False
assert capability['activation']['live'] is False
assert capability['transport']['endpoint_profiles']['deepseek_openai_compatible'] == 'https://api.deepseek.com'
assert capability['transport']['supported_models'] == ['deepseek-v4-flash', 'deepseek-v4-pro']
assert schema['properties']['transport_id']['pattern'] == '^dsit-[0-9a-f]{64}$'
assert schema['properties']['authority_effect']['const'] == 'NONE'
assert schema['properties']['egress_intr_required']['const'] is True
assert schema['properties']['credential_material_present']['const'] is False
assert root['deepseek_intr_interoperability']['protocol'] == 'stegverse.intr.deepseek.transport.v1'
assert root['deepseek_intr_interoperability']['canonical_sovereign_route_replaced'] is False
assert runtime['profile_id'] == 'stegverse:runtime-profile:llm-adapter-deepseek:v1'
assert runtime['base_profile'] == 'stegverse:runtime-profile:hb-intr-resident:v1'
assert runtime['provider_execution']['credential_authority'] == 'TV/TVC'
assert runtime['provider_execution']['credential_material_in_llm_adapter'] is False
assert runtime['provider_execution']['direct_credential_resolver_production_allowed'] is False
assert runtime['physical_runtime']['another_physical_machine_required'] is False
assert runtime['physical_runtime']['linux_specific_runtime_required'] is False
print('DEEPSEEK_INTR_CAPABILITY_DECLARATION=VALID')
print('DEEPSEEK_RUNTIME_PROFILE_BINDING=VALID')
print('DEEPSEEK_INTR_ACTIVATION_LIVE=false')
PY
