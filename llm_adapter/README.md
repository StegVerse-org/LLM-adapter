# LLM Adapter package

## Coinbase SKAP Device → KV canonical transport

The Coinbase SKAP Service Gateway is the receiver that accepts the current-iPhone encrypted browser ingress. In addition to the preserved legacy TVC double-Interlock stage receipt, it emits a separate canonical Universal-InTr first-hop projection for the end-to-end `STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001` lineage.

```text
CURRENT_USER_IPHONE
-> Service Gateway
-> canonical DEVICE_SYSTEM -> KV intent + hop receipt
-> durable canonical sidecar
-> TVC custody continuation
```

Implementation surfaces:

- `canonical_device_kv_stage.py` builds a non-secret `kv.interlock.request.v1` reference payload, canonical Universal-InTr intent, and `stegverse.intr.hop_receipt/v1` receipt.
- `service_gateway_composed.py` persists that projection at `<gateway-storage-root>/coinbase-skap-stage-canonical/<ingress_id>.json` with exact readback and collision failure.
- `service_gateway_coinbase_skap.py` continues to own the existing legacy stage receipt and exact encrypted browser-packet staging; its TVC compatibility contract is not replaced by the canonical sidecar.

The canonical first-hop projection contains references and hashes, not browser ciphertext or credential values. It grants no execution, credential, provider, custody, governance, or transition authority. TV/TVC remains credential/custody authority and Interlock/InTr governs transitions.

Downstream code must not manufacture this first-hop evidence after custody. It must consume the sidecar emitted by the Gateway and preserve its receipt hash as the prior lineage for the canonical KV → SKAP transition. Source or CI validation is not current-device runtime proof.
