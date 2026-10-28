set -eu
cd /tmp/source
python -m unittest tests/test_southbound_sdk_return.py
echo 'SOUTHBOUND_SDK_RETURN_SOURCE_VALIDATION=PASS'
echo 'INTERLOCK_INTR_RUNTIME_EGRESS_OBSERVED=false'
echo 'FAR_SIDE_TRANSITION_OBSERVED=false'
echo 'COMMUNICATION_COMPLETE=false'
