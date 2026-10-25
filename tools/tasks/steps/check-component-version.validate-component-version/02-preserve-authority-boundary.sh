python - <<'PY'
import json
from pathlib import Path
d = json.loads(Path('VERSION.json').read_text())
assert d['authority_effect'] == 'NONE'
assert d['credential_authority'] == 'TV/TVC'
assert d['github_token_runtime_authority'] is False
assert d['third_party_production_authority'] is False
print('COMPONENT_VERSION_VALIDATION_AUTHORITY_EFFECT=NONE')
PY
