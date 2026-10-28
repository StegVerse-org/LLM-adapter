python3 -m unittest tests/test_hil_intake_api.py
python3 - <<'PY'
import json
from pathlib import Path
task = json.loads(Path('tasks/LLMA-HIL-SITE-RECEIPT-COMPAT-030.json').read_text())
assert task['credential_authority'] == 'TV/TVC'
assert task['github_token_runtime_authority'] == 'NONE'
assert task['participant_machine_required'] is False
assert task['developer_machine_required'] is False
assert task['third_party_runtime_required'] is False
contract = task['required_receipt_contract']
assert contract['custody_state'] == 'EXACT_BYTES_PERSISTED'
assert contract['registry_state'] == 'RECORDED'
source = Path('llm_adapter/hil_intake_v1_1_api.py').read_text()
assert '"custody_state": "EXACT_BYTES_PERSISTED"' in source
assert '"registry_state": "RECORDED"' in source
assert 'hil_submission_registry_hash_mismatch' in source
assert 'hil_submission_persistence_verification_failed' in source
print('HIL_SITE_RECEIPT_COMPAT=PASS')
print('CREDENTIAL_AUTHORITY=TV/TVC')
print('PRODUCTION_AUTHORITY_EFFECT=NONE')
PY
