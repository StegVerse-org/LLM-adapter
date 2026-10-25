set -euo pipefail
# Pin the transitive install set, build backend included, to the SDK's own
# constraints at the commit pyproject.toml installs (tests/test_sdk_install_constraints.py).
constraint="$(python3 scripts/sdk_install_constraint.py)"
export PIP_CONSTRAINT="$constraint"
python3 -m pip install --disable-pip-version-check -q -e '.[dev]'
