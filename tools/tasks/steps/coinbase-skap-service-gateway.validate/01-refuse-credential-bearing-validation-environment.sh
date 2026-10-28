for key in GITHUB_TOKEN GH_TOKEN GITHUB_PAT OPENAI_API_KEY ANTHROPIC_API_KEY COINBASE_API_KEY COINBASE_API_SECRET COINBASE_API_PRIVATE_KEY; do
  if [ -n "${!key:-}" ]; then
    echo "credential_exposed:$key"
    exit 1
  fi
done
