python3 - <<'PY'
from pathlib import Path
p=Path('tools/tasks/folded/validate-external-llm-convergence.yml').read_text()
forbidden = ['git ' + 'push', 'persist-' + 'credentials', 'actions/' + 'checkout@']
assert 'permissions: {}' in p
assert all(marker not in p for marker in forbidden)
assert 'OPENAI_API_KEY' in p and 'ANTHROPIC_API_KEY' in p
print('EXTERNAL_LLM_CONVERGENCE_VALIDATION_ONLY=PASS')
PY
