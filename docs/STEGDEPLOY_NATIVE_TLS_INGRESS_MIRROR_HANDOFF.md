# StegDeploy Native TLS Ingress Mirror Handoff

Updated: 2026-08-27
Repository: `StegVerse-org/LLM-adapter`
Canonical owner: `StegVerse-org/LLM-adapter#72`
Coinbase downstream owner: `StegVerse-Labs/TVC#119`

## Goal

Add a sovereign HTTPS transport mode to the existing StegDeploy Service Gateway without creating a second gateway, reverse proxy, tunnel, hosted ingress service, or non-TV/TVC credential authority.

The implementation must reuse:

```text
same image
same deployed_gateway app
same StegDeploy bootstrap
same health-bound node advertisement
same durable storage
same Service Gateway authority model
```

## Authority

```text
credential_authority: TV/TVC
tls_private_key_authority: TV/TVC
gateway_execution_authority: NONE
github_token_runtime_authority: NONE
render_required: false
cloudflare_required: false
reverse_proxy_required: false
second_service_plane: false
```

Certificate/private-key bytes must never be committed, written into `.stegdeploy/runtime.env`, placed in a receipt, passed as command-line values, or stored in GitHub Actions.

## Runtime contract

Native TLS uses Uvicorn in the existing container.

```text
compose.stegdeploy.yaml
+ compose.stegdeploy.tls.yaml
+ TV/TVC-materialized certificate file
+ TV/TVC-materialized private-key file
-> Docker Compose runtime secrets
-> /run/secrets/stegverse_tls_cert
-> /run/secrets/stegverse_tls_key
-> existing llm_adapter.deployed_gateway:app
-> HTTPS on container port 8000
```

The TLS deploy mode must require:

- certificate and key files exist and are regular files;
- certificate is parseable as X.509 PEM;
- private key content is never read into the deployment receipt;
- public bind address is explicit and not loopback;
- external port is explicit;
- health URL is HTTPS;
- local image build remains mandatory with `pull_policy: never`;
- no third-party registry or ingress is required.

## Receipt boundary

The deployment receipt may record:

- TLS enabled = true;
- certificate SHA-256 fingerprint;
- public bind address;
- public port;
- HTTPS health URL;
- certificate/key material present = true;
- private-key material recorded = false.

It must not record:

- private key bytes;
- certificate private key;
- provider credentials;
- bearer tokens;
- GitHub tokens.

## State distinctions

```text
TLS source implemented != sovereign runtime executed
TLS runtime executed != public internet reachability
public HTTPS observed != TVC READY_FOR_OWNER_INGRESS
READY_FOR_OWNER_INGRESS != Coinbase credential ingress
credential ingress != provider capability
provider capability != StegFin approval
approval != order
order != fill
fill != reconciliation
```

## Runtime completion boundary

This source lane becomes complete when native TLS compose/bootstrap/tests are merged and hosted validation passes.

Production route remains NOT OBSERVED until a real StegVerse-owned/federated runtime executes this mode and TVC independently observes the HTTPS node/readiness surface.

No current iPhone action is due.


## Merge / validation evidence

```text
PR: StegVerse-org/LLM-adapter#209
merge: 10a6f6247771b2a85b07f5f19810403c3acde513
Coinbase SKAP Service Gateway Validation: 33121152939 SUCCESS
global validate: 33121152794 SUCCESS
source state: MERGED / VALIDATED
```

Downstream carrier/propagation:

```text
StegVerse-Labs/StegVerse-Healer#43
merge: 7aa88c39d5e46402e3368b5ebd81d27a773ce93d
Test Readiness: 33121314608 SUCCESS

StegVerse-Labs/.github#328
merge: 583f3277c7eee9f0d12ab63280d31fbbc278aa85
Heartbeat Worker Project: 33121525095 SUCCESS
Organization control plane: 33121525130 SUCCESS
```

The complete source path from resident worker -> Healer -> StegDeploy native TLS is therefore merged and validation-green. No real TLS runtime receipt or public-route observation is claimed.


## Host-native sovereign primary runtime — 2026-08-29

The original native-TLS lane used native Uvicorn TLS *inside* Docker. That remains valid as a compatibility path but is no longer sufficient as the sovereign primary topology for same-host loopback services such as evaluator InTr.

Issue #224 adds:

```text
scripts/stegdeploy_native_gateway.py
```

This launcher runs the existing `llm_adapter.deployed_gateway:app` directly in the deployment-local Python runtime and can consume TV/TVC-materialized certificate/key files without serializing their path or bytes into its deployment receipt.

The runtime distinction is now:

```text
HOST_NATIVE_PYTHON_UVICORN
  sovereign primary / same-host loopback composition / docker_required=false

DOCKER_COMPOSE + native Uvicorn TLS
  optional compatibility/fallback method
  may not become a requirement for StegVerse authority or runtime semantics
```

The host-native receipt remains local-only:

```text
state=LOCAL_NATIVE_GATEWAY_READY
production_public_route_observed=false
public_certificate_hostname_verified=false
credential_authority=TV/TVC
github_token_runtime_authority=NONE
```

Public reachability and hostname verification remain separately observed runtime predicates.
