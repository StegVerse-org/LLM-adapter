"$PYTHON_BIN" - <<'PY'
from pathlib import Path
workflow = Path('tools/tasks/folded/validate-kimi-intr.yml').read_text(encoding='utf-8')
assert 'permissions: {}' in workflow
assert 'KIMI_API_KEY' in workflow
assert 'MOONSHOT_API_KEY' in workflow
assert 'STEGVERSE_MASTER_RECORDS_TOKEN' in workflow
forbidden = ['actions/' + 'checkout@', 'actions/' + 'setup-python@', 'git ' + 'push', 'schedule' + ':']
assert all(marker not in workflow for marker in forbidden), forbidden
print('KIMI_INTR_VALIDATION_AUTHORITY=NONE')
print('KIMI_INTR_CREDENTIAL_AUTHORITY=TV_TVC')
print('KIMI_INTR_RUNTIME_EFFECT=NONE')
PY
