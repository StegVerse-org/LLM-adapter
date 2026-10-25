python3 - <<'PY'
import json
from pathlib import Path
from llm_adapter.hil_sovereign_receiver_profile import SovereignHILProfileError, apply_sovereign_hil_receiver_profile

inactive = {}
result = apply_sovereign_hil_receiver_profile(inactive)
assert result['state'] == 'INACTIVE_NON_SOVEREIGN_RUNTIME'
assert result['participant_machine_required'] is False
assert result['developer_machine_required'] is False
assert result['github_hosted_runtime_required'] is False
assert result['third_party_runtime_required'] is False

active = {
    'STEGVERSE_RUNTIME_PROFILE': 'sovereign-carrier',
    'STEGVERSE_SOVEREIGN_STATE_DURABLE': 'true',
    'STEGVERSE_SOVEREIGN_STATE_DIR': '/var/lib/stegverse',
}
result = apply_sovereign_hil_receiver_profile(active)
assert result['state'] == 'ACTIVE_SOVEREIGN_RECEIVER'
assert active['STEGVERSE_HIL_INTAKE_ENABLED'] == 'true'
assert active['STEGVERSE_HIL_DATA_DIR'] == '/var/lib/stegverse/hil-v1.1'
assert active['STEGVERSE_STORAGE_DURABLE_ACROSS_RESTARTS'] == 'true'
assert result['credential_authority'] == 'TV/TVC'
assert result['credential_requirement'] == 'NONE_FOR_PARTICIPANT_INTAKE'

try:
    apply_sovereign_hil_receiver_profile({
        'STEGVERSE_RUNTIME_PROFILE': 'sovereign-carrier',
        'STEGVERSE_SOVEREIGN_STATE_DIR': '/var/lib/stegverse',
    })
except SovereignHILProfileError as exc:
    assert str(exc) == 'sovereign_state_durability_not_attested'
else:
    raise AssertionError('missing durability must fail closed')

try:
    apply_sovereign_hil_receiver_profile({
        'STEGVERSE_RUNTIME_PROFILE': 'sovereign-carrier',
        'STEGVERSE_SOVEREIGN_STATE_DURABLE': 'true',
        'STEGVERSE_SOVEREIGN_STATE_DIR': '/tmp/stegverse',
    })
except SovereignHILProfileError as exc:
    assert str(exc) == 'sovereign_state_dir_must_not_be_temporary'
else:
    raise AssertionError('temporary state root must fail closed')

task = json.loads(Path('tasks/LLMA-HIL-SOVEREIGN-RECEIVER-021.json').read_text())
assert task['participant_machine_required'] is False
assert task['developer_machine_required'] is False
assert task['third_party_runtime_required'] is False
assert task['credential_authority'] == 'TV/TVC'
assert task['github_token_runtime_authority'] == 'NONE'

reconstruction = json.loads(Path('tasks/LLMA-HIL-POST-SUBMIT-RECONSTRUCTION-029.json').read_text())
assert reconstruction['credential_authority'] == 'TV/TVC'
assert reconstruction['new_credential_or_token_minted'] is False
assert reconstruction['public_status_exposes_private_metadata'] is False
assert reconstruction['participant_machine_required'] is False
assert reconstruction['developer_machine_required'] is False
assert reconstruction['third_party_runtime_required'] is False

gateway = Path('llm_adapter/combined_gateway.py').read_text()
for marker in [
    '/api/hil/readiness',
    '/api/hil/submissions',
    '/api/hil/submissions/{{submission_id}}/status',
    '/api/hil/submissions/{{submission_id}}/exact-bytes',
    '/api/hil/sovereign-receiver-profile',
    'EXISTING_TV_TVC_REVIEW_AUTH_REQUIRED',
    'participant_machine_required',
    'developer_machine_required',
    'github_hosted_runtime_required',
    'third_party_runtime_required',
]:
    assert marker in gateway, marker

intake = Path('llm_adapter/hil_intake_v1_1_api.py').read_text()
for marker in [
    'HIL-SUBMISSION-STATUS-v1',
    'EXACT_BYTES_HASH_VERIFIED',
    'hil_exact_bytes_hash_mismatch',
    'hil_exact_bytes_size_mismatch',
    'hil_exact_bytes_storage_boundary_mismatch',
    '_review_token_required',
]:
    assert marker in intake, marker

print('HIL_SOVEREIGN_RECEIVER_SOURCE=PASS')
print('HIL_POST_SUBMIT_RECONSTRUCTION_SOURCE=PASS')
print('PARTICIPANT_MACHINE_REQUIRED=false')
print('DEVELOPER_MACHINE_REQUIRED=false')
print('GITHUB_HOSTED_RUNTIME_REQUIRED=false')
print('THIRD_PARTY_RUNTIME_REQUIRED=false')
print('CREDENTIAL_AUTHORITY=TV/TVC')
print('PRODUCTION_AUTHORITY_EFFECT=NONE')
PY
