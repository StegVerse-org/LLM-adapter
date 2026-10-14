# HIL Receiver Runtime Quickstart

This path starts the governed HIL v1.1 receiver on the host-native launcher (`scripts/stegdeploy_native_gateway.py`). No container framework, image build or hosting provider is involved.

## Start locally

```sh
git clone https://github.com/StegVerse-org/LLM-adapter.git
cd LLM-adapter
sh scripts/start-hil-runtime.sh
```

The bootstrap command:

- creates `.env.hil.local` with distinct review and publication secrets;
- starts the gateway with `scripts/stegdeploy_native_gateway.py start`, which closes when the process is spawned and keeps durable state under the launcher's durable root;
- observes `/api/hil/readiness` once afterwards and reports whether the v1.1 Primary and prompt hashes match. That observation never gates the start; an unanswered probe is reported as `NOT_AUTHENTICALLY_OBSERVED` with the readiness URL as its reconciliation entrypoint.

The generated environment file is ignored by Git and must not be committed.

## Verify the runtime

```sh
curl -fsS http://127.0.0.1:8000/health
curl -fsS http://127.0.0.1:8000/api/hil/readiness
curl -fsS http://127.0.0.1:8000/api/hil/publication-readiness
```

Readiness must report:

```text
state = READY
primary_sha256 = a7b1c62e336b4e244ecf7fdcd10af195401f6c44328de32615b073d2a5c3c462
prompt_sha256 = cdff8d2266bb3eefbb6e5d28d9adc548e6c8dfc039debd72fe404f1d0249912c
provenance_manifest_required = true
```

## Make the receiver reachable from the public Site

A browser loaded from the HTTPS Site requires an HTTPS receiver endpoint. Supply HTTPS through any standards-compatible reverse proxy, ingress controller, load balancer, or tunnel. The application itself does not depend on which implementation provides TLS.

The public endpoint must forward these paths unchanged:

```text
/health
/api/hil/readiness
/api/hil/submissions
/api/hil/publication-readiness
```

Set `STEGVERSE_ALLOWED_ORIGINS` to include the exact Site origin. Do not use `*` for a public governed receiver.

After HTTPS readiness succeeds, update `StegVerse-Labs/Site/data/hil-receiver-config.json` with the receiver base URL. The Site configuration must remain unconfigured until the receiver proves the exact v1.1 readiness contract.

## Prove persistence

A durable-storage declaration is not proof. After the first controlled upload:

```sh
python scripts/stegdeploy_native_gateway.py stop
sh scripts/start-hil-runtime.sh
```

Then verify that the submission database, exact PDF bytes, provenance manifest, and receipt-linked hashes remain available from the same durable root.

## Stop without deleting custody state

```sh
python scripts/stegdeploy_native_gateway.py stop
```

Stopping leaves the durable root in place. Deleting it destroys the local custody copy.

## Authority boundary

Runtime readiness authorizes no publication, review outcome, ecosystem execution, or Master Record mutation. Intake, private review, publication, and Master Record operations remain separate governed steps with separate credentials and evidence.
