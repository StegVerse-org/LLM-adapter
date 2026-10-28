python - <<'PY'
import json
from pathlib import Path
packet = json.loads(Path('internal_tests/artifacts/governed-reference-results.json').read_text())
assert packet['execution_class'] == 'INTERNAL_EXECUTION'
assert packet['public_replayable'] is True
assert packet['independently_reproduced'] is False
assert packet['production_observed'] is False
assert packet['summary']['failed'] == 0
assert packet['packet_sha256'].startswith('sha256:')
print('EVIDENCE_BOUNDARY=PASS')
PY
