#!/usr/bin/env python3
import copy
import importlib.util
import json
import sys
from pathlib import Path

MODULE = Path('va_claim_assistant/governed_retrieval.py')
spec = importlib.util.spec_from_file_location('governed_retrieval', MODULE)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

registry = {
    'sources': [
        {
            'source_id': 'VA-EVIDENCE-NEEDED',
            'authority_class': 'OFFICIAL_OPERATIONAL',
            'name': 'Evidence Needed for Your Disability Claim',
            'url': 'https://www.va.gov/disability/how-to-file-claim/evidence-needed/',
            'admitted': True,
        },
        {
            'source_id': 'VA-COMPENSATION-EVIDENCE',
            'authority_class': 'OFFICIAL_OPERATIONAL',
            'name': 'Compensation Evidence Requirements',
            'url': 'https://www.benefits.va.gov/compensation/evidence.asp',
            'admitted': True,
        },
    ]
}

answer = module.build_evidence_requirement_answer(
    question='What evidence is generally needed for a disability claim?',
    registry=registry,
    registry_commit='e69e8421084b1343a9dc809fdb2a579089d37813',
    answer_schema_commit='ae64a81df7ac91a9b2df00e9b8ff1a8358fcb9ab',
)
module.validate_answer(answer, registry)
assert answer['route'] == 'evidence_requirement'
assert answer['capability_state'] == 'SOURCE_GROUNDED_ASSISTANT'
assert not any(answer['authority_flags'].values())
assert len(answer['propositions']) == 2

escalated = copy.deepcopy(answer)
escalated['authority_flags']['rating'] = True
escalated['receipt_hash'] = module.canonical_hash({k: v for k, v in escalated.items() if k != 'receipt_hash'})
try:
    module.validate_answer(escalated, registry)
except ValueError as exc:
    assert 'authority escalation' in str(exc)
else:
    raise AssertionError('authority escalation was not rejected')

unsupported = copy.deepcopy(answer)
unsupported['propositions'][0]['support'] = []
unsupported['receipt_hash'] = module.canonical_hash({k: v for k, v in unsupported.items() if k != 'receipt_hash'})
try:
    module.validate_answer(unsupported, registry)
except ValueError as exc:
    assert 'unsupported proposition' in str(exc)
else:
    raise AssertionError('unsupported proposition was not rejected')

Path('receipts').mkdir(exist_ok=True)
Path('receipts/va-claim-assistant-public-source-fixture.json').write_text(
    json.dumps(answer, indent=2) + '\n', encoding='utf-8'
)
print(json.dumps({'result': 'PASS', 'receipt_hash': answer['receipt_hash']}))
