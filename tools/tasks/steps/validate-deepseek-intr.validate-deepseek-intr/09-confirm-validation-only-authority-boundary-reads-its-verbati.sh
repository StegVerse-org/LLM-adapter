"$PYTHON_BIN" - <<'PY'
from pathlib import Path
workflow = Path('tools/tasks/folded/validate-deepseek-intr.yml').read_text(encoding='utf-8')
assert 'permissions: {}' in workflow
assert 'DEEPSEEK_API_KEY' in workflow
assert 'STEGVERSE_MASTER_RECORDS_TOKEN' in workflow
assert 'tests/test_deepseek_intr_transport.py' in workflow
assert 'tests/test_deepseek_intr_executor.py' in workflow
assert 'tests/test_deepseek_tvc_runtime.py' in workflow
forbidden = [
    'actions/' + 'checkout@',
    'actions/' + 'setup-python@',
    'git ' + 'push',
    'schedule' + ':',
]
assert all(marker not in workflow for marker in forbidden), forbidden
print('DEEPSEEK_INTR_VALIDATION_AUTHORITY=NONE')
print('DEEPSEEK_INTR_CREDENTIAL_AUTHORITY=TV_TVC')
print('DEEPSEEK_INTR_RUNTIME_EFFECT=NONE')
PY
