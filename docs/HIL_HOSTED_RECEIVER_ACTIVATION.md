# HIL Hosted Receiver Activation

## Purpose

This path resolves the public Site `NOT READY` state without participant-owned continuously live hardware.

The receiver remains provider-neutral. `render.yaml` is a managed-host blueprint for the existing OCI runtime, not an architectural dependency. Any host satisfying the same HTTPS, secret-injection, durable-storage, restart, and evidence contract may replace it.

## Required outcome

```text
managed HTTPS receiver
→ exact v1.1 readiness verified
→ hosted persistence verified across restart/redeploy
→ Site receiver configuration updated
→ public upload control becomes READY
→ one controlled browser submission returns a verified durable receipt
```

## Blueprint properties

- builds the repository Dockerfile unchanged;
- terminates public HTTPS at the managed host;
- attaches a 1 GiB persistent disk at `/var/lib/stegverse`;
- generates distinct private-review and publication secrets at the host boundary;
- restricts allowed browser origins to StegVerse public origins;
- uses `/api/hil/readiness` as the health check;
- disables automatic deployment so activation remains controlled.

## Activation evidence

Before editing `StegVerse-Labs/Site/data/hil-receiver-config.json`, preserve:

1. deployed repository revision;
2. public HTTPS base URL;
3. `/api/hil/readiness` response with exact v1.1 hashes;
4. `/api/hil/publication-readiness` response;
5. controlled PDF hash and provenance-manifest hash;
6. returned `HIL-RECEIVER-RECEIPT-v2`;
7. hosted restart or redeploy event;
8. post-restart reconstruction of the same PDF bytes and manifest;
9. proof that no participant-owned hardware supplied continuity.

## Site configuration gate

Only after the evidence above passes may the Site configuration transition to:

```json
{
  "receiver_base_url": "https://<verified-host>",
  "configuration_state": "CONFORMING_HTTPS_RECEIVER_CONFIGURED"
}
```

The actual verified hostname must be inserted. Placeholder or unverified URLs remain prohibited.

## Role boundary

The participant is not the hardware provider, installer, host operator, troubleshooter, continuity layer, or deployment authority. Managed-host account authorization and any paid-plan approval remain separate administrative acts; they do not become experiment-participant duties.
