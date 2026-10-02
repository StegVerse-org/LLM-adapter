# Canonical Node Standing Ingress Mirror Handoff

Updated: 2026-10-02
Parent Goal: StegVerse-org/.github `SVORG-STEGOS-PORTABILITY-001`
Parent contract head reviewed: `320aab81a5c386324ae41c0dc5e05152bf5b137d`
Authority effect: NONE

## Existing surfaces mapped

No endpoint was added. The existing `/api/stegverse-node` advertisement now maps existing surfaces for bounded chat, resident-node rendezvous request/ack, organization InTr frame/ack, evaluator InTr, HIL intake and attachment intake.

The mapping is discovery only and grants no authority.

## Canonical standing seam

`governed_manifest_ingress.validate_ingress_manifest` now requires a declared predecessor key and generation. A present `null` predecessor is accepted only for generation 1 and is labeled `ESTABLISH_GENESIS`. Later generations require the canonical predecessor shape `generation, manifest_sha256, result_sha256, heartbeat_epoch` and are labeled `VERIFY_EXISTING`. Missing or malformed continuity fails closed before the SDK endpoint is called. Failed existing-node verification never falls back to genesis.

The predecessor shape and oscillator ordering reuse the StegVerse-SDK contract at `50d6ed8c1e9058092ce5056fa09157804b2c70d3`; this adapter does not define a second receipt-chain predecessor semantics.

## Processing selection repair

The bounded AI-entry backend accepts an already-declared route as authoritative for its local response classification and uses message keyword classification only when no declared route exists. This prevents message content from substituting a governed manifest-selected processing declaration on a governed caller path.

The production `/api/ecosystem-chat` request model still accepts caller-supplied transition identity. It is not promoted to canonical standing by this repair. Direct public-chat binding into the canonical standing validator remains a separate source gap and must fail closed wherever canonical standing is required.

## Regressions added

- missing predecessor key fails closed
- explicit generation-1 null predecessor is carried as ESTABLISH_GENESIS
- generation >1 canonical predecessor is carried as VERIFY_EXISTING
- failed existing-node verification does not re-enroll
- node advertisement exposes standing semantics and maps existing continuations

## Proof boundary

Source changes and regression definitions do not prove deployed propagation, authentic node standing, attestation, external transport, custody, KV-as-node, or StegBrowser-as-KV-surface. Those remain NOT_PROVEN unless their canonical owners provide evidence.
