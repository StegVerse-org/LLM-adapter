for key in GITHUB_TOKEN GH_TOKEN OPENAI_API_KEY ANTHROPIC_API_KEY; do
  if [ -n "${!key:-}" ]; then echo "credential_exposed:$key"; exit 1; fi
done
