#!/usr/bin/env python3
import copy
import importlib.util
import json
import sys
from pathlib import Path

MODULE = Path('va_claim_assistant/route_classifier.py')
spec = importlib.util.spec_from_file_location('va_route_classifier', MODULE)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

cases = [
    ('What evidence do I need for my disability claim?', 'evidence_requirement'),
    ('How do I file a claim using the correct VA form?', 'procedural_filing'),
    ('What does service connection require?', 'service_connection'),
    ('How does the effective date affect back pay?', 'effective_date'),
    ('What should I expect at a C&P exam?', 'cp_examination'),
    ('How do I prepare a buddy statement?', 'lay_statement'),
    ('How can I find a VA-accredited representative?', 'representation_referral'),
]

receipts = []
for question, expected_route in cases:
    result = module.classify_question(question)
    module.validate_classification(result)
    assert result['state'] == 'CLASSIFIED'
    assert result['selected_route'] == expected_route
    assert not any(result['authority_flags'].values())
    receipts.append(result)

ambiguous = module.classify_question('What evidence do I need and how do I appeal?')
module.validate_classification(ambiguous)
assert ambiguous['state'] == 'REVIEW_REQUIRED'
assert ambiguous['selected_route'] is None
assert ambiguous['reason'] == 'multiple_governed_routes_match'

unsupported = module.classify_question('Please explain this situation to me.')
module.validate_classification(unsupported)
assert unsupported['state'] == 'REVIEW_REQUIRED'
assert unsupported['reason'] == 'no_supported_route_match'

urgent = module.classify_question('I need help filing a claim and I may hurt myself.')
module.validate_classification(urgent)
assert urgent['state'] == 'CLASSIFIED'
assert urgent['selected_route'] == 'urgent_safety'
assert urgent['reason'] == 'urgent_safety_priority'

escalated = copy.deepcopy(receipts[0])
escalated['authority_flags']['rating'] = True
escalated['receipt_hash'] = module.canonical_hash({k: v for k, v in escalated.items() if k != 'receipt_hash'})
try:
    module.validate_classification(escalated)
except ValueError as exc:
    assert 'authority escalation' in str(exc)
else:
    raise AssertionError('authority escalation was not rejected')

Path('receipts').mkdir(exist_ok=True)
summary = {
    'schema_version': '1.0.0',
    'result': 'PASS',
    'classified_cases': len(receipts),
    'ambiguous_state': ambiguous['state'],
    'unsupported_state': unsupported['state'],
    'urgent_route': urgent['selected_route'],
    'authority_granted': False,
    'receipt_hashes': [item['receipt_hash'] for item in receipts] + [
        ambiguous['receipt_hash'], unsupported['receipt_hash'], urgent['receipt_hash']
    ],
}
summary['receipt_hash'] = module.canonical_hash(summary)
Path('receipts/va-claim-assistant-route-classifier-validation.json').write_text(
    json.dumps(summary, indent=2) + '\n', encoding='utf-8'
)
print(json.dumps({'result': 'PASS', 'receipt_hash': summary['receipt_hash']}))
