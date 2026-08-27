# Coinbase SKAP Service Gateway Mirror Handoff

Updated: 2026-08-26T14:35:00-05:00
Repository: `StegVerse-org/LLM-adapter`
Upstream architecture owner: `StegVerse-org/LLM-adapter#72`
Downstream credential/custody owner: `StegVerse-Labs/TVC#119`
Status: SOURCE_VALIDATED_FIRST_INTERLOCK / STEGDEPLOY_PRIMARY_RUNTIME_BINDING_MERGED_HOSTED_PASS / RENDER_FALLBACK_ONLY / PRODUCTION_ROUTE_NOT_OBSERVED

## Goal

Reuse the existing shared StegVerse Service Gateway for the public HTTPS transport/staging hop of current-iPhone SKAP ingress without granting the Gateway credential, private-key, decryption, custody, provider-operation, trading, or execution authority.

## Canonical topology and authority

```text
CURRENT_USER_IPHONE
-> browser-local P-256 sealed ciphertext
-> Service Gateway
-> DEVICE -> KV InTr receipt
-> STAGED_FOR_TVC
-> event-driven TVC stage drain
-> KV -> SKAP_VAULT InTr receipt chained to first receipt
-> ADMITTED_TO_SKAP_VAULT
-> endpoint/session verification
-> transient credential resolution inside SKAP authority
```

The Service Gateway is transport + bounded durable staging only. `STAGED_FOR_TVC` proves only the first `DEVICE -> KV` boundary. It MUST NOT be interpreted as SKAP Vault custody or provider authorization.

Hard invariants:

```text
credential_authority: TV/TVC
gateway_credential_value_access: false
gateway_decryption_authority: false
gateway_execution_authority: NONE
authority_transfer: false
secret_plaintext_present: false
blind_retry_allowed: false
```

## Current source implementation

- `llm_adapter/service_gateway_coinbase_skap.py`
- `llm_adapter/service_gateway_composed.py`
- `llm_adapter/runtime_gateway.py`
- `tests/test_service_gateway_coinbase_skap.py`
- `tests/test_service_gateway_coinbase_skap_api.py`
- `.github/workflows/coinbase-skap-service-gateway.yml`

The adapter remains mounted on the shared `stegverse-service-gateway` runtime entrypoint; no second service plane is required.

Current source emits:

```text
schema: stegverse.service_gateway.coinbase_skap_stage_receipt/v1
decision: STAGED_FOR_TVC
device_kv_interlock_receipt.connector: InTr
device_kv_interlock_receipt.from_boundary: DEVICE
device_kv_interlock_receipt.to_boundary: KV
tvc_admission_completed: false
next_required_transition: KV_SKAP_VAULT_INTERLOCK_ADMISSION
```

The previous handoff text naming `TVC_SKAP_CIPHERTEXT_CUSTODY_ADMISSION` is superseded by the current source and canonical double-Interlock transition name `KV_SKAP_VAULT_INTERLOCK_ADMISSION`.

## Validation evidence

Earlier repair/validation evidence remains valid:

```text
Coinbase SKAP Service Gateway Validation: run 32879101025 SUCCESS
Global repository validate: run 32879100937 SUCCESS
TVC downstream stage-consumer validation: run 32879237493 SUCCESS
```

Later aligned first-Interlock/readiness validation recorded by the Site/TVC lane:

```text
LLM-adapter primary Gateway first-interlock/readiness: run 32885966113 SUCCESS
```

Current workflow explicitly asserts the no-value TVC boundary, `DEVICE -> KV` InTr receipt, no authority transfer, and `KV_SKAP_VAULT_INTERLOCK_ADMISSION` as the next transition.

## Current production state

```text
shared Gateway source integration: HOSTED/SOURCE PASS
Gateway no-value TVC boundary: HOSTED/SOURCE PASS
exact ciphertext staging/readback: HOSTED/SOURCE PASS
DEVICE -> KV first-interlock receipt semantics: HOSTED/SOURCE PASS
TVC downstream stage-drain source: HOSTED PASS
TVC one-command resident shared-KV stage-drain integration: MERGED in StegVerse-Labs/TVC PR #128 / commit 0e2a5986773243efafa835f9c214e963b8d08c96
public production Service Gateway Coinbase route: NOT OBSERVED
production recipient public-key lease: NOT OBSERVED
real current-iPhone owner credential ingress: NOT OBSERVED
real DEVICE -> KV receipt from production iPhone ingress: NOT OBSERVED
real KV -> SKAP_VAULT chained receipt: NOT OBSERVED
real provider credential ciphertext in SKAP Vault: NOT OBSERVED
authentic provider permission/fee observation: NOT OBSERVED
live bounded order: NOT EXECUTED
```

## Dependencies

Upstream/boundary contract owner:
- `StegVerse-Labs/continuity-vault-kit/SKAP_INTR_REVIEW_CANDIDATE_MIRROR_HANDOFF.md`
- RC-01 through RC-05 baseline are complete, including connected-KV non-secret runtime proof.

Downstream resident/custody owner:
- `StegVerse-Labs/TVC/docs/TVC_COINBASE_IPHONE_SKAP_ACTIVATION_MIRROR_HANDOFF.md`
- `StegVerse-Labs/TVC/tasks/TVC-COINBASE-RESIDENT-ACTIVATION-091.json`

Browser consumer:
- `StegVerse-Labs/Site/docs/STEGFIN_PHONE_SKAP_INTR_ROUTE_MIRROR_HANDOFF.md`

## Next executable boundary

1. Observe/deploy the actual shared Service Gateway runtime serving the Coinbase readiness/ingress routes under the no-value TVC decision boundary.
2. Obtain live TVC recipient-key activation/liveness and current public-only projection.
3. Propagate only the live public recipient config + proven Gateway route to Site.
4. Current user performs owner-authorized iPhone WebAuthn/browser sealing.
5. Retain the real `DEVICE -> KV` receipt, then allow TVC to produce the chained `KV -> SKAP_VAULT` receipt and exact ciphertext readback.
6. Only after custody admission proceed to endpoint/session-bound provider permission/fee observation.

## Non-claims

Source/hosted validation is not a production route observation. No production recipient private key is claimed here. No real provider credential is stored by this handoff. No SKAP Vault custody is implied by `STAGED_FOR_TVC`. No provider-operation or trading authority is granted to the Gateway.


## 2026-08-27 deployed-entrypoint 404 diagnosis

A live TVC/Site compatibility probe reached:

`https://stegverse-ecosystem-chat-gateway.onrender.com/api/coinbase/skap/readiness`

and received HTTP 404 even though `service_gateway_composed.py` and `runtime_gateway.py` already contained the validated Coinbase SKAP route.

Live service inspection established the cause:

```text
service: stegverse-ecosystem-chat-gateway
repository: StegVerse-org/LLM-adapter
branch: main
auto deploy: enabled
deployed start command:
  python -m llm_adapter.custody_worker &&
  uvicorn llm_adapter.deployed_gateway:app --host 0.0.0.0 --port $PORT
```

`llm_adapter.deployed_gateway:app` did not mount the Coinbase SKAP readiness/ingress handlers. The 404 was therefore deployed-entrypoint drift, not absence of the canonical SKAP/InTr staging implementation.

Bounded repair on branch `repair/deployed-gateway-coinbase-skap-routes`:

- mounts only the existing validated `coinbase_skap_readiness` and `coinbase_skap_ingress` handlers on the actual deployed app;
- adds `tests/test_deployed_gateway_coinbase_skap.py`;
- extends the existing Coinbase SKAP validation workflow to compile/test the deployed entrypoint;
- grants no new credential, decryption, custody, provider-operation or execution authority;
- does not create a second public service plane.

This repair must not be called production-observed until:
1. hosted validation passes;
2. the repair merges to `main`;
3. the existing auto-deploy completes;
4. the live readiness URL returns the canonical readiness contract rather than 404.

The hosting substrate is compatibility execution only and remains replaceable; it is not StegVerse credential or governance authority.


## 2026-08-27 deployed-entrypoint repair merge and runtime blocker

The deployed-entrypoint repair is now source/hosted complete:

```text
PR: #204
head: 90cfe8cd6f4d49aad5d69ea9621bf91857664d92
merge: 244902d475c12ee6bff7dd67e4dfacb4e2357ca7

Coinbase SKAP Service Gateway Validation:
  push run 33070210104 SUCCESS
  PR run 33070270802 SUCCESS

global validate:
  push run 33070210184 SUCCESS
```

The repair mounts the existing validated Coinbase SKAP readiness and ingress handlers onto the actual deployed `llm_adapter.deployed_gateway:app` entrypoint and adds a deployed-entrypoint regression test. This closes the source seam that produced the earlier 404.

The existing compatibility service auto-deploy did trigger on the exact merge commit:

```text
Render service id: srv-d9epkh3rjlhs73csc3qg
service: stegverse-ecosystem-chat-gateway
deploy: dep-da82gv4s728c73akg010
commit: 244902d475c12ee6bff7dd67e4dfacb4e2357ca7
status: BUILD_FAILED
```

Render build logs establish the failure class:

```text
Build canceled: your workspace has run out of build pipeline minutes for the current billing period.
```

This is an external hosting quota/billing limitation, not a repository build/test failure and not a Coinbase/SKAP contract failure.

Current distinctions:

```text
deployed-entrypoint source repair: MERGED
dedicated hosted validation: PASS
global hosted validation: PASS
compatibility service auto-deploy: TRIGGERED / BUILD_BLOCKED_BY_RENDER_QUOTA
live compatibility Coinbase readiness route after repair: NOT OBSERVED
StegVerse-owned production primary route: NOT OBSERVED
authority_effect: NONE
```

The compatibility Render service remains replaceable and non-authoritative. Restoring its build quota may allow the compatibility route to deploy, but that does not satisfy the separate requirement for a StegVerse-owned/substrate-admissible production primary route.


## Primary runtime migration away from Render

Render is explicitly classified as fallback compatibility only and is no longer a production-continuity dependency for this lane.

The canonical primary carrier is the existing StegDeploy sovereign runtime:

```text
source -> local OCI build -> compose.stegdeploy.yaml
-> llm_adapter.deployed_gateway:app
-> durable /var/lib/stegverse state
-> Coinbase SKAP readiness/ingress
-> no-value DEVICE -> KV InTr staging
```

Primary-runtime configuration now carries:

```text
STEGVERSE_SERVICE_GATEWAY_STORAGE_ROOT=/var/lib/stegverse
STEGVERSE_COINBASE_SKAP_TVC_DECISION_RECEIPT=<no-value TVC receipt, injected at runtime>
```

The TVC decision receipt contains no provider credential values. If it is absent or invalid, the Coinbase SKAP readiness route fails closed.

Current policy:

```text
StegDeploy / StegVerse-owned substrate: PRIMARY
Render: FALLBACK_ONLY
Render billing/build minutes required: false
Render hostname required: false
Render authority: NONE
TV/TVC credential authority: unchanged
```

The next production gate is therefore to instantiate this StegDeploy image on an authorized StegVerse-owned/sovereign runtime and observe the HTTPS readiness route there. Restoring Render is optional compatibility work, not a prerequisite.


## StegDeploy primary-runtime merge evidence

```text
PR: #205
head: 078cbe43a2c4168a4facc41b0d2d963257fb6613
merge: 0ec44419ada49147feb1866abfa6fe4fb4d0bbb2
Coinbase SKAP Service Gateway Validation:
  push 33070875928 SUCCESS
  PR   33070931930 SUCCESS
global validate:
  push 33070875926 SUCCESS
```

Primary runtime is now source-merged and hosted-validated. Render remains optional fallback compatibility only. The remaining production predicate is a real StegVerse-owned/sovereign runtime execution and public HTTPS observation of the readiness route.
