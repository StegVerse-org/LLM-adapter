set -euo pipefail
selected="$(command -v python3 || command -v python)"
echo "PYTHON_BIN=$selected" >> "$GITHUB_ENV"
"$selected" --version
