"$PYTHON_BIN" - <<'PY'
from pathlib import Path
workflow = Path('tools/tasks/folded/capability-runtime.yml').read_text(encoding='utf-8')
assert 'permissions: {}' in workflow
forbidden = [
    'actions/' + 'checkout@',
    'actions/' + 'setup-python@',
    'persist-' + 'credentials',
]
assert all(marker not in workflow for marker in forbidden), forbidden
assert 'cancel-in-progress: true' in workflow
assert 'github_token_runtime_authority' in Path('llm_adapter/node_bootstrap.py').read_text(encoding='utf-8')
print('CAPABILITY_RUNTIME_CREDENTIAL_AUTHORITY=TV_TVC')
print('CAPABILITY_RUNTIME_GITHUB_TOKEN_AUTHORITY=NONE')
print('CAPABILITY_RUNTIME_ACTIVATION_EFFECT=NONE')
PY
