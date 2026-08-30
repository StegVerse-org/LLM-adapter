# StegVerse.me Personal Origin Service Gateway Mirror Handoff

Updated: 2026-08-30
Repository: `StegVerse-org/LLM-adapter`
Issue: `#233`
Branch: `feature/stegverse-me-personal-origin-233`
Goal: `LLMA-STEGVERSE-ME-PERSONAL-ORIGIN-233`
State: SOURCE_COMPLETE_MERGED_VALIDATED
Credential authority: TV/TVC
Gateway authority effect: NONE
Activation effect: false

## Source of truth

This handoff governs the bounded addition of a dedicated `stegverse.me` virtual-origin adapter to the existing shared StegVerse Service Gateway.

Canonical upstream Site sources:

- `StegVerse-Labs/Site/docs/STEGVERSE_ME_SITE_ORIGIN_MIRROR_HANDOFF.md`
- `StegVerse-Labs/Site/docs/STEGVERSE_ME_OPAQUE_NODE_RESOLVER_MIRROR_HANDOFF.md`
- Site issue #581 / released origin source
- Site issue #680 / released opaque resolver source

Canonical runtime/TLS owners remain external to this implementation:

- shared Service Gateway: this repository
- resident execution: `StegVerse-Labs/.github`
- TV/TVC TLS/WebPKI authority: `StegVerse-Labs/TVC`

## Goal

Serve the already-governed public personal-origin bundle on the existing shared Gateway without creating a second gateway, server-side identity registry, KV custody surface, DNS authority, certificate authority, or activation authority.

## Required adapter boundary

The adapter must:

1. reuse `llm_adapter.deployed_gateway:app`;
2. admit only configured personal-origin Host values, defaulting to `stegverse.me` and `www.stegverse.me`;
3. serve only files beneath a deployment-local public bundle root;
4. reject symlinks and traversal;
5. optionally verify files against a deployment-local SHA-256 manifest before serving;
6. expose only the bounded public routes needed by the Site personal projection;
7. treat the opaque node segment as routing input only;
8. never read private KV, derive identity, mint an opaque node, or create server-side continuity;
9. never mutate DNS or perform certificate issuance;
10. preserve TV/TVC as credential authority and Gateway authority as NONE.

## Source completion boundary

Machine-executable here:

- adapter implementation;
- deterministic host/path/traversal/hash negative tests;
- deployed-gateway integration;
- source validation;
- PR merge;
- handoff update.

Not established by source completion:

- dedicated public origin selected at runtime;
- TVC certificate material present;
- live resident Gateway;
- public HTTPS;
- DNS cutover;
- local continuity admission;
- authentic Interlock/InTr admission;
- private-KV readback;
- activation.

## Remaining destinations

`StegVerse-Labs/Site`
- materialize the exact public bundle contract and observer/projector for this Gateway origin;
- preserve local resolver authority boundaries.

`StegVerse-Labs/TVC`
- materialize/adopt authentic WebPKI material for the admitted hostname under TV/TVC custody.

`StegVerse-Labs/.github`
- execute the host-native Gateway on an eligible sovereign resident runtime.

Runtime/DNS owner
- independently observe public HTTPS before any controlled DNS cutover.


## Merge and validation evidence

- Source PR: #234
- Source merge: `f23638072f950691a1cee26cbfcd6e1e1ed99ae3`
- Exact source head: `7380f1b1c33b7eb51413887233ddc7e22d9fffe2`
- `validate` run: 33322456494 SUCCESS
- `Coinbase SKAP Service Gateway Validation` run: 33322456282 SUCCESS
- changed files: 4
- shared Gateway reused: true
- second Gateway created: false
- private-KV readback: false
- DNS mutation: false
- certificate issuance: false
- authority effect: NONE
- activation effect: false

This source completion does not establish a live resident Gateway, public HTTPS, TV/TVC certificate materialization, DNS cutover, local continuity admission, authentic Interlock/InTr admission, private-KV readback, or production activation.
