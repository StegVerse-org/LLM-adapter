set -euo pipefail
# pip clones the pinned SDK by checking out its default branch first; on Windows that
# tree has paths beyond MAX_PATH, so let git create them (no-op on ubuntu/macos).
git config --global core.longpaths true
# Pin the transitive install set, build backend included, to the SDK's own
# constraints at the commit pyproject.toml installs (tests/test_sdk_install_constraints.py).
constraint="$("$PYTHON_BIN" scripts/sdk_install_constraint.py)"
export PIP_CONSTRAINT="$constraint"
"$PYTHON_BIN" -m pip install -e .
