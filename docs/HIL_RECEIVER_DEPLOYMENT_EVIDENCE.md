# HIL Receiver Deployment Evidence

This gate converts a managed-host deployment into reviewable activation evidence without treating configuration or health as completion.

## Evidence path

1. Copy `evidence/hil-receiver-deployment.example.json` to a new immutable evidence file.
2. Replace placeholders only with directly observed values.
3. Do not mark readiness, submission, restart durability, Site enablement, custody, or reconstruction as complete until each event has actually occurred.
4. Validate with:

```bash
python scripts/verify_hil_receiver_deployment_evidence.py evidence/<observed-file>.json
```

A passing record proves that the required observations are present and internally consistent. It does not grant publication, review, scientific-validation, or Master-Records append authority.

## Current blocker

Until `receiver.stegverse.com` is deployed through an authorized managed-host account and its DNS/TLS configuration is active, the example remains intentionally failing. Repository configuration is not deployment evidence.

## Required completion chain

```text
public DNS
→ verified TLS without readiness redirects
→ exact HIL v1.1 READY response
→ controlled PDF submission and valid receipt
→ managed restart or redeploy
→ byte-identical reconstruction
→ public Site upload control enabled
→ Master-Records custody RECORDED
→ Master-Records reconstruction PASS
```

No secret, token, participant PDF, private response, or unredacted participant metadata belongs in a public evidence record.
