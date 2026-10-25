set -euo pipefail
for name in OPENAI_API_KEY ANTHROPIC_API_KEY GITHUB_TOKEN GH_TOKEN; do
  value="${!name-}"
  if [ -n "$value" ]; then
    echo "Unexpected credential-bearing environment: $name" >&2
    exit 1
  fi
done
