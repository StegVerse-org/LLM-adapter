"$PYTHON_BIN" - <<'PY'
import json
from pathlib import Path

capability = json.loads(Path('capability/stegverse-intr-zai-transport.capability.json').read_text(encoding='utf-8'))
schema = json.loads(Path('schemas/zai-intr-transport-envelope.schema.json').read_text(encoding='utf-8'))

assert capability['capability_id'] == 'stegverse.intr.zai.transport.v1'
assert capability['provider'] == 'z.ai'
assert capability['authority']['authority_effect'] == 'NONE'
assert capability['authority']['synthesizes_allow'] is False
assert capability['authority']['ingress_decision_point'] == 'external:StegVerse-Interlock/InTr'
assert capability['authority']['egress_decision_point'] == 'external:StegVerse-Interlock/InTr'
assert capability['credential']['credential_authority'] == 'TV/TVC'
assert capability['credential']['credential_class'] == 'TV_TVC_PROVIDER_SECRET'
assert capability['credential']['credential_material_present'] is False
assert capability['credential']['persisted'] is False
assert capability['credential']['redaction_guard'] is True
assert capability['independence']['canonical_sovereign_route_replaced'] is False
assert capability['independence']['hosted_provider_required'] is False
assert capability['independence']['optional'] is True
assert capability['activation']['live'] is False
assert schema['properties']['transport_id']['pattern'] == '^zait-[0-9a-f]{64}$'
assert schema['properties']['authority_effect']['const'] == 'NONE'
assert schema['properties']['egress_intr_required']['const'] is True
assert schema['properties']['credential_material_present']['const'] is False
print('ZAI_INTR_CAPABILITY_DECLARATION=VALID')
print('ZAI_INTR_ACTIVATION_LIVE=false')
PY
