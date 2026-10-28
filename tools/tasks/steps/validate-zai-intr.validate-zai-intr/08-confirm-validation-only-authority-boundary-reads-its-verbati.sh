"$PYTHON_BIN" - <<'PY'
from pathlib import Path
workflow = Path('tools/tasks/folded/validate-zai-intr.yml').read_text(encoding='utf-8')
assert 'permissions: {}' in workflow
assert 'ZAI_API_KEY' in workflow
assert 'STEGVERSE_MASTER_RECORDS_TOKEN' in workflow
assert 'tests/test_zai_intr_transport.py' in workflow
assert 'tests/test_zai_intr_executor.py' in workflow
assert 'capability/stegverse-intr-zai-transport.capability.json' in workflow
forbidden = [
    'actions/' + 'checkout@',
    'actions/' + 'setup-python@',
    'git ' + 'push',
    'schedule' + ':',
]
assert all(marker not in workflow for marker in forbidden), forbidden
print('ZAI_INTR_VALIDATION_AUTHORITY=NONE')
print('ZAI_INTR_CREDENTIAL_AUTHORITY=TV_TVC')
print('ZAI_INTR_RUNTIME_EFFECT=NONE')
PY
