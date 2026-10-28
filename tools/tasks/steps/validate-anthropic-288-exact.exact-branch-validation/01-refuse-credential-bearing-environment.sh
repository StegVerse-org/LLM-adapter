for key in GITHUB_TOKEN GH_TOKEN ANTHROPIC_API_KEY OPENAI_API_KEY; do
  if [ -n "${!key:-}" ]; then echo "credential_exposed:$key"; exit 1; fi
done
