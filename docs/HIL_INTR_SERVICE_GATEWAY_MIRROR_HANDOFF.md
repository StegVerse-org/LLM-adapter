# HIL InTr Shared Service Gateway Mirror Handoff

Updated: 2026-09-09
Repository: `StegVerse-org/LLM-adapter`
Parent HIL activation: `StegVerse-Labs/.github#246`

## Goal

Use the existing shared StegVerse Service Gateway as the single public HTTPS surface for HIL and Universal InTr transport without creating a second public gateway, HIL-specific tunnel authority, participant-operated host, or GitHub-hosted production runtime.

## Corrected runtime topology

The deployed Gateway imports `llm_adapter.combined_gateway:app`, which already mounts the canonical HIL v1.1 intake router and sovereign receiver profile. Production participant HIL intake therefore does not require a second public receiver.

```text
participant browser / Site
-> https://stegverse.org/api/hil/submissions
-> shared Service Gateway
-> canonical HIL v1.1 intake
-> durable /var/lib/stegverse/hil-v1.1 state
-> HIL-RECEIVER-RECEIPT-v2
-> HIL custody Interlock receipt chain
-> durable TVC HIL-lifecycle InTr queue
```

## Universal InTr transport projections

The same shared Gateway exposes transport-only projections over the declared same-host sovereign Universal InTr receiver.

Existing surfaces:

```text
GET  /intr/profile
POST /intr/materialization
POST /intr/device-kv/result
```

The control-plane source-acquisition remediation adds:

```text
POST /intr/source-package
```

This is an extension of the existing transport adapter, not a new Gateway/runtime owner.

### Control-plane source package projection

The route is usable only when the sovereign `/intr/profile` response advertises:

```text
stegverse.control-plane
control_plane_source_package_path=/intr/source-package
```

The public request must satisfy:

```text
public HTTPS
Origin = https://stegverse.org or https://www.stegverse.org
X-StegVerse-Transport = InTr
X-StegVerse-Transport-Origin = TVC_RELAY_EGRESS
X-StegVerse-Authorization-Id = nonempty TVC authorization id
X-StegVerse-Payload-SHA256 = exact body SHA-256
no Authorization header
no Cookie header
```

The Gateway forwards the exact admitted bytes to the same configured loopback receiver host, changing only the path from `/intr/materialization` to `/intr/source-package`. The source-package request bound is 8 MiB; ordinary materialization remains bounded at 512 KiB.

The Gateway does not validate package file semantics or write source bytes itself. The sovereign receiver owns exact `stegverse.source-package/v1` validation, content-addressed retention, static-path allowlisting, and local source materialization. The resident source watcher owns subsequent refresh/dispatch. GitHub is not consulted by the runtime transport path.

## Authority invariants

```text
credential_authority: TV/TVC
github_token_runtime_authority: NONE
gateway_execution_authority: false
gateway_receipt_authority: false
gateway_custody_authority: false
gateway_source_repository_authority: false
gateway_canonical_transition_authority: false
second_user_device_required: false
third_party_runtime_required: false
```

`/intr/source-package` transports admitted bytes only. A TVC authorization ID does not transfer TVC authority to the Gateway. Package delivery does not itself prove source materialization, WorkerCoordinator execution, relay return completion, or canonical transition.

## Source

```text
llm_adapter/service_gateway_hil_intr.py
llm_adapter/combined_gateway.py
llm_adapter/deployed_gateway.py
llm_adapter/hil_intake_v1_1_api.py
llm_adapter/hil_sovereign_receiver_profile.py
tests/test_service_gateway_hil_intr.py
tests/test_service_gateway_control_plane_source_package.py
README.control-plane-source-package.md
```

## Runtime evidence still required

Source/CI/merge do not establish current deployment state. Runtime observation for this trajectory requires:

1. public `/intr/profile` from the deployed shared Gateway;
2. `stegverse.control-plane` advertised by the current sovereign receiver;
3. an admitted TVC relay request to `/intr/source-package`;
4. the sovereign source-package receipt showing content-addressed retention and local source materialization;
5. the existing resident source-refresh receipt after that local source mutation;
6. exact relay-return request consumption;
7. terminal `SOVEREIGN_RELAY_RETURN_PATH_VERIFIED` evidence.
