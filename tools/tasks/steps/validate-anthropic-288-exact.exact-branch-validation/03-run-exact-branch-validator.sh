python3 scripts/validate_anthropic_intr.py --branch feat/anthropic-intr-runtime-fix-288 --json > /tmp/validation-288.json
cat /tmp/validation-288.json
python3 - <<'PY'
import json
report=json.load(open('/tmp/validation-288.json'))
assert report['check_count']==43
assert report['outcome']=='PASS'
assert report['merge_permitted'] is True
assert report['attests_live_claude_execution'] is False
assert report['attests_custody_acceptance'] is False
assert report['attests_egress_allow'] is False
print('ANTHROPIC_288_EXACT_BRANCH_VALIDATION=PASS')
PY
