#!/usr/bin/env python3
import copy
import importlib.util
import json
import sys
from pathlib import Path

MODULE = Path('va_claim_assistant/governed_retrieval.py')
spec = importlib.util.spec_from_file_location('governed_retrieval_dispatch', MODULE)
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

common = {
    'registry': registry,
    'registry_commit': 'e69e8421084b1343a9dc809fdb2a579089d37813',
    'answer_schema_commit': 'ae64a81df7ac91a9b2df00e9b8ff1a8358fcb9ab',
}

answer_ready = module.dispatch_governed_question(
    question='What evidence is needed for my disability claim?',
    session_id='va-dispatch-evidence-001',
    **common,
)
module.validate_dispatch(answer_ready, registry)
assert answer_ready['state'] == 'ANSWER_READY_PENDING_TVC_AND_CUSTODY'
assert answer_ready['classification']['selected_route'] == 'evidence_requirement'
assert answer_ready['answer']['route'] == 'evidence_requirement'
assert answer_ready['next_required_evidence'] == [
    'tvc_capability_receipt',
    'master_records_custody_receipt',
    'reconstruction_receipt',
]
assert not any(answer_ready['authority_flags'].values())

unimplemented = module.dispatch_governed_question(
    question='What is the effective date for back pay?',
    session_id='va-dispatch-effective-date-001',
    **common,
)
module.validate_dispatch(unimplemented, registry)
assert unimplemented['state'] == 'NOT_IMPLEMENTED_FAIL_CLOSED'
assert unimplemented['classification']['selected_route'] == 'effective_date'
assert unimplemented['answer'] is None
assert unimplemented['blocker'] == 'route_not_implemented:effective_date'

review_required = module.dispatch_governed_question(
    question='Please review this for me.',
    session_id='va-dispatch-review-001',
    **common,
)
module.validate_dispatch(review_required, registry)
assert review_required['state'] == 'REVIEW_REQUIRED'
assert review_required['answer'] is None
assert review_required['classification']['selected_route'] is None

urgent = module.dispatch_governed_question(
    question='I am in immediate danger and need to know what evidence is needed.',
    session_id='va-dispatch-urgent-001',
    **common,
)
module.validate_dispatch(urgent, registry)
assert urgent['state'] == 'NOT_IMPLEMENTED_FAIL_CLOSED'
assert urgent['classification']['selected_route'] == 'urgent_safety'
assert urgent['answer'] is None

escalated = copy.deepcopy(answer_ready)
escalated['authority_flags']['rating'] = True
escalated['receipt_hash'] = module.canonical_hash({k: v for k, v in escalated.items() if k != 'receipt_hash'})
try:
    module.validate_dispatch(escalated, registry)
except ValueError as exc:
    assert 'authority escalation' in str(exc)
else:
    raise AssertionError('dispatch authority escalation was not rejected')

Path('receipts').mkdir(exist_ok=True)
receipt = {
    'schema': 'stegverse.va_claim_assistant.governed_dispatch_validation.v1',
    'result': 'PASS',
    'states_verified': [
        'ANSWER_READY_PENDING_TVC_AND_CUSTODY',
        'NOT_IMPLEMENTED_FAIL_CLOSED',
        'REVIEW_REQUIRED',
    ],
    'implemented_routes': ['evidence_requirement'],
    'unimplemented_routes_fail_closed': True,
    'authority_granted': False,
    'activation_granted': False,
    'evidence_dispatch_receipt_hash': answer_ready['receipt_hash'],
    'unimplemented_dispatch_receipt_hash': unimplemented['receipt_hash'],
    'review_dispatch_receipt_hash': review_required['receipt_hash'],
    'urgent_dispatch_receipt_hash': urgent['receipt_hash'],
}
receipt['receipt_hash'] = module.canonical_hash(receipt)
Path('receipts/va-claim-assistant-governed-dispatch-validation.json').write_text(
    json.dumps(receipt, indent=2) + '\n', encoding='utf-8'
)
print(json.dumps({'result': 'PASS', 'receipt_hash': receipt['receipt_hash']}))
