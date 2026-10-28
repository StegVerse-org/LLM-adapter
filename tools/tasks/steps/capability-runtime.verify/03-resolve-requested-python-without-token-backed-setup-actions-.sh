set -euo pipefail
wrapper="$PWD/.stegverse-python"
selected=""
if command -v "python${PYTHON_VERSION}" >/dev/null 2>&1; then
  selected="$(command -v "python${PYTHON_VERSION}")"
elif command -v py >/dev/null 2>&1; then
  printf '#!/usr/bin/env bash\nexec py -%q "$@"\n' "$PYTHON_VERSION" > "$wrapper"
else
  selected="$(find "${RUNNER_TOOL_CACHE:-/nonexistent}" \( -type f -o -type l \) \( -name python -o -name python.exe \) 2>/dev/null | grep -E "[/\\]Python[/\\]${PYTHON_VERSION}([./\\]|$)" | head -n 1 || true)"
  if [ -z "$selected" ]; then
    # No interpreter is downloaded or installed: the runner image
    # provides the requested Python or the job fails closed (LLMA-368).
    printf '%s\n' \
      "state=FAIL_CLOSED" \
      "failure_code=REQUESTED_PYTHON_NOT_PROVIDED_BY_RUNNER" \
      "failed_predicate=runner_provides_python_${PYTHON_VERSION}" \
      "required_evidence_or_repair=select a runner image whose PATH, py launcher or tool cache provides Python ${PYTHON_VERSION}" \
      "retry_entrypoint=tools/tasks/folded/capability-runtime.yml (workflow_dispatch)" \
      "owning_existing_goal=LLMA-DECLARED-PATH-CONFORMANCE-368" \
      "next_attempt=rerun the matrix entry on a runner image that provides Python ${PYTHON_VERSION}"
    exit 1
  fi
fi
if [ ! -s "$wrapper" ]; then
  printf '#!/usr/bin/env bash\nexec %q "$@"\n' "$selected" > "$wrapper"
fi
chmod +x "$wrapper"
echo "PYTHON_BIN=$wrapper" >> "$GITHUB_ENV"
"$wrapper" --version
"$wrapper" - <<'PY'
import sys
expected = tuple(map(int, "${{ matrix.python }}".split('.')))
assert sys.version_info[:2] == expected, (sys.version, expected)
print("CAPABILITY_RUNTIME_PYTHON=PASS")
PY
