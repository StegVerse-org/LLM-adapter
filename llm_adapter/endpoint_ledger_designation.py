"""Per-endpoint ledger designation and the store-reader seam (ENDPOINT-LEDGER-DESIGNATION-001).

Ruling (Rigel, StegVerse-org/.github#160 comments 6371986288 and 6372216673): KV is independent of the Orgs. It
runs its own ledger behind its own InTr ingress/egress endpoint and that ledger is never stored on an org's
refs/stegverse/organization-ledger. KV's ledger is a set of encrypted, content-addressed objects in user-owned
storage (for example Google Drive) behind a GATEWAY node: each receipt is an opaque encrypted blob keyed by sha256,
with an append-only head pointer under a ``##_<name>`` location (01_KV_Ledger, 02_SKAP_Vault_Ledger). KV verifies
and decrypts on its own side; the storage's own records never cross.

A designation names, per endpoint, where its ledger is and what authenticates it. It is read from the endpoint's
own contract, never from a caller::

    {"schema": "stegverse.endpoint-ledger-designation/v1", "endpoint_id": str,
     "endpoint_kind": "ORG" | "PERMANENT" | "KV" | "SKAP_VAULT",
     "stores": [<exactly one store entry>], "provider_selection": "SINGLE_PROVIDER_V1",
     "genesis_class": str, "expected_genesis_receipt_sha256": null | "sha256:<hex>",
     "head_signer_source": "ORG_LEDGER_HEAD_SIGNER" | "KV_LEDGER_HEAD_SIGNER",
     "rollback_watermark_source": null | {"source": "ORG_LEDGER_LINKED_RECEIPTS_ENDPOINT_HEAD",
                                          "path_ids": [str, ...]}}

store_type (an enum):

* ``GIT_REF``: {store_type, provider "git", repository, ref, namespace}. Read by the existing git reader,
  llm_adapter.org_ledger_location.designated_org_ledger, unchanged (it pins the genesis and authenticates the head
  with the org-ledger head signers). Used for ORG and PERMANENT.
* ``GATEWAY_ENCRYPTED_BLOB`` (reserved): {store_type, provider, gateway_node_id, location "##_<name>"}. Required
  for KV and SKAP_VAULT; GIT_REF is refused for them. No reader is installed: the reader is Lane D's
  (KV-LEDGER-STORE-READER-001 under ECOSYSTEM-OWN-KV-001), consuming their gateway storage adapter contract
  (put/get/list of opaque blobs by location, stdlib only). Until it is admitted every such read is six-field
  FAIL_CLOSED ENDPOINT_LEDGER_STORE_READER_NOT_INSTALLED.

Several storage providers per endpoint (designed for, not supported): ``stores`` is an ordered list. The selection
rule is deterministic: list order is the only selector, never health, latency, a clock or the caller.
SINGLE_PROVIDER_V1 (the only rule now) selects ``stores[0]`` and requires exactly one entry; more than one is
six-field ENDPOINT_LEDGER_MULTI_PROVIDER_NOT_SUPPORTED. A multi-provider rule is its own admitted change.

The reader seam: ``READERS`` maps store_type to a reader. A reader is a context manager factory
``reader(designation, store, source, head_attestation)`` that yields ``(chain, None)`` (receipts newest first,
as the endpoint sees them after its own decryption) or ``(None, (reason, detail))``. Whatever a reader yields is
checked again here by the pure ``chain_admission_failure``, for every store type:

1. an empty or missing ledger is never taken as a genesis (ENDPOINT_LEDGER_EMPTY_NOT_A_GENESIS);
2. every receipt is sealed and linked, and the chain ends at the designated genesis class;
3. the genesis equals the designation's pin (null: ENDPOINT_LEDGER_GENESIS_NOT_PINNED; the pre-pin receiver
   pattern of #431 sets it);
4. KV and SKAP_VAULT: the head is signed by kv_ledger_head_signer (TVC#542), a key published in
   .stegverse/node-ledger/kv-ledger-head-signers.v1.json (none published yet:
   KV_LEDGER_HEAD_SIGNER_NOT_PUBLISHED). GIT_REF heads were authenticated by the git reader;
5. the rollback watermark: the newest endpoint_head_sha256 the Org recorded on its linked receipts for this
   endpoint's path_ids must be on the presented chain; an older head is DENY KV_LEDGER_HEAD_ROLLBACK_DETECTED.

Pure apart from the reader it hands off to. No clock, no network, no randomness, stdlib only. Tests use fixture
keys only; bots never hold keys.
"""
from __future__ import annotations

import base64
import binascii
import contextlib
import json
import re
from pathlib import Path
from types import MappingProxyType
from typing import Any, Iterator, Mapping

from llm_adapter import ed25519_verify
from llm_adapter import healthy_node_evaluator as hne
from llm_adapter import org_ledger_location

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "stegverse.endpoint-ledger-designation/v1"
RESULT_SCHEMA = "stegverse.endpoint-ledger-read/v1"
ALLOW, FAIL_CLOSED, DENY = "ALLOW", "FAIL_CLOSED", "DENY"

GIT_REF, GATEWAY_ENCRYPTED_BLOB = "GIT_REF", "GATEWAY_ENCRYPTED_BLOB"
STORE_TYPES = (GIT_REF, GATEWAY_ENCRYPTED_BLOB)
ORG, PERMANENT, KV, SKAP_VAULT = "ORG", "PERMANENT", "KV", "SKAP_VAULT"
STORE_TYPE_OF = {ORG: GIT_REF, PERMANENT: GIT_REF, KV: GATEWAY_ENCRYPTED_BLOB, SKAP_VAULT: GATEWAY_ENCRYPTED_BLOB}
INDEPENDENT_KINDS = (KV, SKAP_VAULT)
STORE_KEYS = {GIT_REF: ("namespace", "provider", "ref", "repository", "store_type"),
              GATEWAY_ENCRYPTED_BLOB: ("gateway_node_id", "location", "provider", "store_type")}
BLOB_LOCATION = re.compile(r"^[0-9]{2}_[A-Za-z0-9][A-Za-z0-9_]*$")
SINGLE_PROVIDER_V1 = "SINGLE_PROVIDER_V1"
SELECTION_RULES = (SINGLE_PROVIDER_V1,)
DESIGNATION_KEYS = ("endpoint_id", "endpoint_kind", "expected_genesis_receipt_sha256", "genesis_class",
                    "head_signer_source", "provider_selection", "rollback_watermark_source", "schema", "stores")

ORG_LEDGER_HEAD_SIGNER, KV_LEDGER_HEAD_SIGNER = "ORG_LEDGER_HEAD_SIGNER", "KV_LEDGER_HEAD_SIGNER"
HEAD_SIGNER_OF = {ORG: ORG_LEDGER_HEAD_SIGNER, PERMANENT: ORG_LEDGER_HEAD_SIGNER,
                  KV: KV_LEDGER_HEAD_SIGNER, SKAP_VAULT: KV_LEDGER_HEAD_SIGNER}
#: head-signer set sources: public-key reference files, TV/TVC custody, empty until published
HEAD_SIGNER_FILES = MappingProxyType({
    ORG_LEDGER_HEAD_SIGNER: (ROOT / ".stegverse/node-ledger/org-ledger-head-signers.v1.json", "ORG_LEDGER_HEAD"),
    KV_LEDGER_HEAD_SIGNER: (ROOT / ".stegverse/node-ledger/kv-ledger-head-signers.v1.json", "KV_LEDGER_HEAD"),
})
SIGNERS_SCHEMA = "stegverse.published-public-key-references/v1"
KV_HEAD_ATTESTATION_SCHEMA = "stegverse.kv-ledger-head-attestation/v1"
KV_HEAD_ATTESTATION_FIELDS = ("schema", "endpoint_id", "store_location", "genesis_receipt_sha256",
                              "head_receipt_sha256", "signer_role")
KV_SIGNER_ROLE = "kv_ledger_head_signer"
WATERMARK_SOURCE = "ORG_LEDGER_LINKED_RECEIPTS_ENDPOINT_HEAD"
ENDPOINT_HEAD_KEY = "endpoint_head_sha256"

ENTRYPOINT = "llm_adapter.endpoint_ledger_designation.read_designated(designation, source=..., ...)"
GOAL = "StegVerse-org/.github#162 (ENDPOINT-LEDGER-DESIGNATION-001; KV independence, .github#160 comment 6372216673)"
READER_GOAL = "KV-LEDGER-STORE-READER-001 under ECOSYSTEM-OWN-KV-001 (Lane D)"
SIGNER_GOAL = "StegVerse-Labs/TVC#542 (kv_ledger_head_signer; ORG-LEDGER-HEAD-SIGNER-001 pattern)"
ON_CHANGE = "on the admission of a corrected designation in the endpoint's own contract (event-triggered)"

#: (failed_predicate, required_evidence_or_repair, owning_existing_goal, next_attempt, disposition)
CODES: Mapping[str, tuple[str, str, str, str, str]] = MappingProxyType({
    "ENDPOINT_LEDGER_DESIGNATION_INVALID": (
        "ENDPOINT_LEDGER_DESIGNATION_WELL_FORMED",
        "a stegverse.endpoint-ledger-designation/v1 with exactly the designation keys, a designated endpoint_kind "
        "(ORG, PERMANENT, KV, SKAP_VAULT), its store_type, head_signer_source and genesis_class", GOAL, ON_CHANGE,
        FAIL_CLOSED),
    "ENDPOINT_LEDGER_STORE_TYPE_UNDECLARED": (
        "STORE_TYPE_IS_A_DECLARED_STORE_TYPE", "store_type GIT_REF or GATEWAY_ENCRYPTED_BLOB", GOAL, ON_CHANGE,
        FAIL_CLOSED),
    "KV_LEDGER_DESIGNATED_ON_GIT_REF": (
        "INDEPENDENT_ENDPOINT_LEDGER_NOT_ORG_HOSTED",
        "KV and SKAP_VAULT designate store_type GATEWAY_ENCRYPTED_BLOB (their own encrypted ledger behind their "
        "gateway node); their ledger is never a git ref and never on refs/stegverse/organization-ledger", GOAL,
        ON_CHANGE, FAIL_CLOSED),
    "ENDPOINT_LEDGER_MULTI_PROVIDER_NOT_SUPPORTED": (
        "ONE_STORE_PROVIDER_UNDER_SINGLE_PROVIDER_V1",
        "designate exactly one store; more than one provider needs its own admitted selection rule (list order "
        "only), which is not built", GOAL, "on the admission of a multi-provider selection rule", FAIL_CLOSED),
    "ENDPOINT_LEDGER_STORE_READER_NOT_INSTALLED": (
        "ENDPOINT_LEDGER_STORE_HAS_AN_INSTALLED_READER",
        "an admitted GATEWAY_ENCRYPTED_BLOB reader registered in READERS, consuming Lane D's gateway storage "
        "adapter contract (put/get/list of opaque blobs by location), yielding the chain as KV decrypts it; no "
        "storage-side record is admitted", READER_GOAL, "on the admission of Lane D's reader (event-triggered)",
        FAIL_CLOSED),
    "ENDPOINT_LEDGER_EMPTY_NOT_A_GENESIS": (
        "ENDPOINT_LEDGER_HAS_A_SEALED_GENESIS",
        "an endpoint ledger whose head walks back to a sealed genesis of the designated genesis_class; an empty or "
        "missing ledger is never taken as a genesis", GOAL,
        "on the endpoint's genesis append and its read-back (event-triggered)", FAIL_CLOSED),
    "ENDPOINT_LEDGER_UNREADABLE": (
        "ENDPOINT_LEDGER_CHAIN_SEALED_AND_LINKED", "every receipt sealed (receipt_sha256 is the digest of the rest) "
        "and linked to its predecessor, ending at a genesis of the designated genesis_class", GOAL,
        "on the next read-back of the designated store", FAIL_CLOSED),
    "ENDPOINT_LEDGER_GENESIS_NOT_PINNED": (
        "ENDPOINT_LEDGER_GENESIS_PINNED_BY_DESIGNATION",
        "expected_genesis_receipt_sha256 set from the receipted genesis by the endpoint's own genesis-pin "
        "transition (the #431 pre-pin receiver pattern)", GOAL,
        "after the endpoint's genesis pin transition is admitted (event-triggered)", FAIL_CLOSED),
    "ENDPOINT_LEDGER_GENESIS_MISMATCH": (
        "ENDPOINT_LEDGER_GENESIS_PINNED_BY_DESIGNATION", "the store's genesis equal to the designation's pin", GOAL,
        "on the next read-back of the designated store", FAIL_CLOSED),
    "KV_LEDGER_HEAD_SIGNER_NOT_PUBLISHED": (
        "KV_LEDGER_HEAD_SIGNED_BY_KV_LEDGER_HEAD_SIGNER",
        "a kv_ledger_head_signer public-key reference published in .stegverse/node-ledger/"
        "kv-ledger-head-signers.v1.json by an admitted change carrying TV/TVC's publication receipt", SIGNER_GOAL,
        "on the kv_ledger_head_signer publication event", FAIL_CLOSED),
    "KV_LEDGER_HEAD_NOT_AUTHENTICATED": (
        "KV_LEDGER_HEAD_SIGNED_BY_KV_LEDGER_HEAD_SIGNER",
        "a stegverse.kv-ledger-head-attestation/v1 over exactly this endpoint, store location, genesis and head, "
        "Ed25519-signed by a published kv_ledger_head_signer key", SIGNER_GOAL,
        "on the next signed head (event-triggered)", FAIL_CLOSED),
    "KV_LEDGER_ROLLBACK_WATERMARK_UNREAD": (
        "ROLLBACK_WATERMARK_READ_FROM_THE_AUTHENTICATED_ORG_LEDGER",
        "the authenticated org-ledger chain whose linked receipts carry endpoint_head_sha256 for this endpoint's "
        "path_ids", GOAL, "on the next authenticated org-ledger read-back", FAIL_CLOSED),
    "KV_LEDGER_HEAD_ROLLBACK_DETECTED": (
        "ENDPOINT_HEAD_NOT_OLDER_THAN_THE_NEWEST_ORG_RECORDED_HEAD",
        "present a ledger whose chain contains the newest endpoint_head_sha256 the Org recorded for this endpoint; "
        "an older or forked head is refused", GOAL, "on a read-back at or after the recorded head (event-triggered)",
        DENY),
})


def refusal(code: str, detail: str, **extra: Any) -> dict[str, Any]:
    predicate, repair, goal, next_attempt, disposition = CODES[code]
    return {"schema": RESULT_SCHEMA, "disposition": disposition, "failure_code": code,
            "failed_predicate": predicate, "required_evidence_or_repair": f"{repair} ({detail})",
            "retry_entrypoint": ENTRYPOINT, "owning_existing_goal": goal, "next_attempt": next_attempt, **extra,
            "ledger_written": False, "authority_effect": "NONE_READ_ONLY"}


def _is_digest(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 71 and value.startswith("sha256:") \
        and all(c in "0123456789abcdef" for c in value[7:])


def designation_failure(designation: Any) -> dict[str, Any] | None:
    """Six-field refusal unless `designation` is well formed for its endpoint kind. Pure."""
    d = designation
    if not isinstance(d, Mapping) or tuple(sorted(d)) != DESIGNATION_KEYS or d.get("schema") != SCHEMA \
            or not isinstance(d.get("endpoint_id"), str) or not d["endpoint_id"] \
            or d.get("endpoint_kind") not in STORE_TYPE_OF or not isinstance(d.get("genesis_class"), str) \
            or not d["genesis_class"] or d.get("provider_selection") not in SELECTION_RULES \
            or not isinstance(d.get("stores"), list) or not d["stores"] \
            or not all(isinstance(s, Mapping) for s in d["stores"]):
        return refusal("ENDPOINT_LEDGER_DESIGNATION_INVALID", f"got {d!r}"[:400])
    kind = d["endpoint_kind"]
    for store in d["stores"]:
        st = store.get("store_type")
        if st not in STORE_TYPES:
            return refusal("ENDPOINT_LEDGER_STORE_TYPE_UNDECLARED", f"store_type {st!r}")
        if kind in INDEPENDENT_KINDS and st == GIT_REF:
            return refusal("KV_LEDGER_DESIGNATED_ON_GIT_REF", f"{kind} {d['endpoint_id']} designates {store!r}")
        if st != STORE_TYPE_OF[kind]:
            return refusal("ENDPOINT_LEDGER_DESIGNATION_INVALID", f"{kind} uses {STORE_TYPE_OF[kind]}, not {st}")
        if tuple(sorted(store)) != STORE_KEYS[st] or not all(isinstance(store[k], str) and store[k] for k in store):
            return refusal("ENDPOINT_LEDGER_DESIGNATION_INVALID", f"a {st} store has exactly {list(STORE_KEYS[st])}"
                           " as non-empty strings (no storage-side record or external ledger ref)")
        if st == GATEWAY_ENCRYPTED_BLOB and not BLOB_LOCATION.match(store["location"]):
            return refusal("ENDPOINT_LEDGER_DESIGNATION_INVALID", f"location {store['location']!r} is not ##_<name>")
    if d["head_signer_source"] != HEAD_SIGNER_OF[kind]:
        return refusal("ENDPOINT_LEDGER_DESIGNATION_INVALID", f"{kind} heads are signed by "
                       f"{HEAD_SIGNER_OF[kind]}, not {d['head_signer_source']!r}")
    w = d["rollback_watermark_source"]
    if kind in INDEPENDENT_KINDS or w is not None:
        if not isinstance(w, Mapping) or tuple(sorted(w)) != ("path_ids", "source") or w["source"] != WATERMARK_SOURCE \
                or not isinstance(w["path_ids"], list) or not w["path_ids"] \
                or not all(isinstance(p, str) and p for p in w["path_ids"]):
            return refusal("ENDPOINT_LEDGER_DESIGNATION_INVALID", f"rollback_watermark_source must be "
                           f"{{source: {WATERMARK_SOURCE}, path_ids: [..]}} (required for KV and SKAP_VAULT)")
    g = d["expected_genesis_receipt_sha256"]
    if g is not None and not _is_digest(g):
        return refusal("ENDPOINT_LEDGER_DESIGNATION_INVALID", f"expected_genesis_receipt_sha256 {g!r}")
    return None


def select_store(designation: Mapping[str, Any]) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """SINGLE_PROVIDER_V1: exactly one store, selected by list order (stores[0]). Pure."""
    failed = designation_failure(designation)
    if failed:
        return None, failed
    stores = designation["stores"]
    if len(stores) != 1:
        return None, refusal("ENDPOINT_LEDGER_MULTI_PROVIDER_NOT_SUPPORTED", f"{len(stores)} stores designated "
                             f"({[s.get('provider') for s in stores]}); {SINGLE_PROVIDER_V1} accepts one")
    return dict(stores[0]), None


def store_location(store: Mapping[str, Any]) -> str:
    if store["store_type"] == GIT_REF:
        return f"{store['ref']}:{store['namespace']}"
    return f"gateway:{store['gateway_node_id']}/{store['location']}"


# -- head signers and the KV head attestation ---------------------------------------------------------------

def load_head_signers(source: str) -> list[dict[str, Any]]:
    """Published head-signer references for a designated source (empty until published)."""
    path, signs = HEAD_SIGNER_FILES[source]
    try:
        published = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    if not isinstance(published, Mapping) or published.get("schema") != SIGNERS_SCHEMA:
        return []
    return [dict(k) for k in published.get("signers") or [] if isinstance(k, Mapping) and k.get("signs") == signs]


def kv_head_attestation_body(designation: Mapping[str, Any], store: Mapping[str, Any], genesis_sha: str,
                             head_sha: str) -> dict[str, Any]:
    return {"schema": KV_HEAD_ATTESTATION_SCHEMA, "endpoint_id": designation["endpoint_id"],
            "store_location": store_location(store), "genesis_receipt_sha256": genesis_sha,
            "head_receipt_sha256": head_sha, "signer_role": KV_SIGNER_ROLE}


def kv_head_attestation_message(body: Mapping[str, Any]) -> bytes:
    return KV_HEAD_ATTESTATION_SCHEMA.encode("utf-8") + b"\n" + hne.canon(dict(body))


def _b64(value: Any) -> bytes | None:
    try:
        return base64.b64decode(value, validate=True) if isinstance(value, str) else None
    except (binascii.Error, ValueError):
        return None


def kv_head_failure(designation: Mapping[str, Any], store: Mapping[str, Any], genesis_sha: str, head_sha: str,
                    attestation: Any, signers: list[Mapping[str, Any]]) -> dict[str, Any] | None:
    """Six-field refusal unless a published kv_ledger_head_signer signed exactly this head. Pure."""
    if not signers:
        return refusal("KV_LEDGER_HEAD_SIGNER_NOT_PUBLISHED", "kv-ledger-head-signers.v1.json is NONE_PUBLISHED")
    if not isinstance(attestation, Mapping):
        return refusal("KV_LEDGER_HEAD_NOT_AUTHENTICATED", f"no {KV_HEAD_ATTESTATION_SCHEMA} for head {head_sha}")
    body = {k: attestation.get(k) for k in KV_HEAD_ATTESTATION_FIELDS}
    if body != kv_head_attestation_body(designation, store, genesis_sha, head_sha):
        return refusal("KV_LEDGER_HEAD_NOT_AUTHENTICATED", "the attestation names another endpoint, location, "
                       f"genesis or head than the store holds (head {head_sha})")
    key = next((k for k in signers if k.get("key_id") == attestation.get("key_id")), None)
    public, signature = _b64((key or {}).get("public_key_b64")), _b64(attestation.get("signature_b64"))
    if key is None or public is None or len(public) != 32 or signature is None or len(signature) != 64 \
            or not ed25519_verify.verify(public, kv_head_attestation_message(body), signature):
        return refusal("KV_LEDGER_HEAD_NOT_AUTHENTICATED", "not by a published key, or the signature does not verify")
    return None


# -- the rollback watermark ---------------------------------------------------------------------------------

def org_recorded_endpoint_heads(org_chain: list[Mapping[str, Any]], designation: Mapping[str, Any]) -> list[str]:
    """endpoint_head_sha256 values the Org recorded on its linked receipts for this endpoint's path_ids, newest
    first (org-chain order is the only order). Pure."""
    path_ids = set((designation.get("rollback_watermark_source") or {}).get("path_ids") or ())
    heads = []
    for receipt in org_chain:
        ev = receipt.get("evidence") if isinstance(receipt, Mapping) else None
        if isinstance(ev, Mapping) and ev.get("path_id") in path_ids and _is_digest(ev.get(ENDPOINT_HEAD_KEY)):
            heads.append(ev[ENDPOINT_HEAD_KEY])
    return heads


def rollback_failure(chain: list[Mapping[str, Any]], recorded_heads: list[str]) -> dict[str, Any] | None:
    """DENY KV_LEDGER_HEAD_ROLLBACK_DETECTED when the newest Org-recorded head is not on the presented chain (the
    presented head is older, or a fork). No recorded head yet: no watermark. Pure."""
    if not recorded_heads:
        return None
    newest = recorded_heads[0]
    if newest in {r.get("receipt_sha256") for r in chain}:
        return None
    return refusal("KV_LEDGER_HEAD_ROLLBACK_DETECTED", f"the Org recorded head {newest}; the presented head is "
                   f"{chain[0].get('receipt_sha256') if chain else None}", recorded_head_sha256=newest)


# -- what every reader's output must satisfy ----------------------------------------------------------------

def chain_failure(designation: Mapping[str, Any], chain: Any) -> dict[str, Any] | None:
    """Empty, unsealed, unlinked or wrong-genesis chains are refused, for every store type. Pure."""
    if not isinstance(chain, list) or not chain:
        return refusal("ENDPOINT_LEDGER_EMPTY_NOT_A_GENESIS", "the store holds no receipts")
    for i, r in enumerate(chain):
        body = {k: v for k, v in r.items() if k != "receipt_sha256"} if isinstance(r, Mapping) else None
        if body is None or not _is_digest(r.get("receipt_sha256")) or hne.sha(body) != r["receipt_sha256"]:
            return refusal("ENDPOINT_LEDGER_UNREADABLE", f"receipt {i} is not sealed")
        expected_previous = chain[i + 1]["receipt_sha256"] if i + 1 < len(chain) else None
        if r.get("previous_receipt_sha256") != expected_previous:
            return refusal("ENDPOINT_LEDGER_UNREADABLE", f"receipt {i} does not link to its predecessor")
    if chain[-1].get("transition_class") != designation["genesis_class"]:
        return refusal("ENDPOINT_LEDGER_EMPTY_NOT_A_GENESIS", f"the chain ends at "
                       f"{chain[-1].get('transition_class')!r}, not a {designation['genesis_class']} genesis")
    pin = designation["expected_genesis_receipt_sha256"]
    if pin is None:
        return refusal("ENDPOINT_LEDGER_GENESIS_NOT_PINNED", "expected_genesis_receipt_sha256 is null")
    if chain[-1]["receipt_sha256"] != pin:
        return refusal("ENDPOINT_LEDGER_GENESIS_MISMATCH", f"the store's genesis is {chain[-1]['receipt_sha256']}, "
                       f"the designation pins {pin}")
    return None


def chain_admission_failure(designation: Mapping[str, Any], store: Mapping[str, Any], chain: Any, *,
                            head_attestation: Any, signers: list[Mapping[str, Any]],
                            org_chain: list[Mapping[str, Any]] | None) -> dict[str, Any] | None:
    """The checks every store type's reader output passes before anything reads it. Pure."""
    failed = chain_failure(designation, chain)
    if failed:
        return failed
    if designation["endpoint_kind"] in INDEPENDENT_KINDS:
        failed = kv_head_failure(designation, store, chain[-1]["receipt_sha256"], chain[0]["receipt_sha256"],
                                 head_attestation, signers)
        if failed:
            return failed
    if designation["rollback_watermark_source"] is not None:
        if not isinstance(org_chain, list):
            return refusal("KV_LEDGER_ROLLBACK_WATERMARK_UNREAD", "no authenticated org-ledger chain supplied")
        return rollback_failure(chain, org_recorded_endpoint_heads(org_chain, designation))
    return None


# -- the reader seam ----------------------------------------------------------------------------------------

@contextlib.contextmanager
def _git_ref_reader(designation: Mapping[str, Any], store: Mapping[str, Any], source: Any,
                    head_attestation: Any) -> Iterator[tuple[list[dict[str, Any]] | None, tuple[str, str] | None]]:
    """GIT_REF: the existing git reader, unchanged, for the location the repository contract designates."""
    designated = org_ledger_location.org_ledger_location()
    if designated is None or (store["repository"], store["ref"], store["namespace"]) != \
            (designated["repository"], designated["ref"], designated["namespace"]):
        yield None, ("ORG_LEDGER_LOCATION_NOT_DESIGNATED", f"{store_location(store)} is not the location the "
                     "repository contract designates")
        return
    with org_ledger_location.designated_org_ledger(source, head_attestation) as (root, failed):
        if failed:
            yield None, failed
            return
        chain, failure, detail = hne.read_chain(root)
        yield (None, ("ENDPOINT_LEDGER_UNREADABLE", f"{failure}: {detail}")) if failure else (chain, None)


#: store_type -> reader. GATEWAY_ENCRYPTED_BLOB has none until Lane D's reader is admitted by its own change.
_READERS: dict[str, Any] = {GIT_REF: _git_ref_reader}
READERS = MappingProxyType(_READERS)


@contextlib.contextmanager
def read_designated(designation: Any, *, source: Any, head_attestation: Any = None,
                    org_chain: list[Mapping[str, Any]] | None = None) -> Iterator[tuple[Any, Any]]:
    """Yield (chain, None) for an admitted read of the designated ledger, or (None, six-field refusal)."""
    store, failed = select_store(designation)
    if failed:
        yield None, failed
        return
    reader = READERS.get(store["store_type"])
    if reader is None:
        yield None, refusal("ENDPOINT_LEDGER_STORE_READER_NOT_INSTALLED", f"no {store['store_type']} reader for "
                            f"{store_location(store)} ({store['provider']})", store_type=store["store_type"])
        return
    with reader(designation, store, source, head_attestation) as (chain, reason):
        if reason:
            code, detail = reason
            if code in CODES:
                yield None, refusal(code, detail)
            else:   # the git reader's own six-field codes (ORG_LEDGER_*, MERGE_APPEND_PATH_NOT_ADMITTED)
                yield None, {**refusal("ENDPOINT_LEDGER_UNREADABLE", f"{code}: {detail}"), "failure_code": code,
                             "reader_failure_code": code}
            return
        if not chain:
            yield None, refusal("ENDPOINT_LEDGER_EMPTY_NOT_A_GENESIS", "the reader yielded no receipts")
            return
        signers = load_head_signers(designation["head_signer_source"])
        failed = chain_admission_failure(designation, store, chain, head_attestation=head_attestation,
                                         signers=signers, org_chain=org_chain)
        yield (None, failed) if failed else (chain, None)


__all__ = ["CODES", "GATEWAY_ENCRYPTED_BLOB", "GIT_REF", "READERS", "SCHEMA", "SINGLE_PROVIDER_V1", "STORE_TYPES",
           "chain_admission_failure", "chain_failure", "designation_failure", "kv_head_attestation_body",
           "kv_head_attestation_message", "kv_head_failure", "load_head_signers", "org_recorded_endpoint_heads",
           "read_designated", "refusal", "rollback_failure", "select_store", "store_location"]
