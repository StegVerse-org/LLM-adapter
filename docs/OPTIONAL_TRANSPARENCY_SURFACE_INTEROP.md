# Optional Transparency Surface Interop

## Canonical contract

Canonical product semantics are defined by:

```text
StegVerse-org/StegVerse-SDK/docs/OPTIONAL_TRANSPARENCY_SURFACES.md
```

The LLM-adapter must preserve that separation.

## Direct machine use

An external LLM/framework that can produce a conforming `stegverse.ingress-manifest.v1` manifest does not need Option `000` or Option `00` before governed submission.

```text
LLM/framework
  -> canonical manifest
  -> LLM-adapter ingress
  -> canonical StegVerse governance
  -> governed result
```

`000` and `00` are not hidden prerequisites and do not provide stronger authority.

## Optional assisted-user use

An LLM/agent may use the same `000` and `00` transparency surfaces available to a human when helping its user understand or configure StegVerse.

Use `000` when the user wants a worked explanation of:

```text
submitted data
manifest shape
governance outcome vocabulary
state-transition classes
receipt classes
editability boundaries
authority boundaries
caller-return projection
Master Records custody
exact-run locator semantics
```

Use `00` when the user wants help selecting permitted manifest parameters such as:

```text
return_projection
manifest_labels
```

The assisting LLM may translate those canonical surfaces into natural-language explanation or use them to construct a new ordinary manifest reflecting the user's choices.

## Same-semantics rule

There must be no AI-only explanation schema and no alternate AI governance path.

```text
human invoking 000/00
LLM invoking 000/00 for a human
LLM constructing a manifest directly
```

must converge on the same canonical manifest semantics and the same governed runtime path.

The educational/configuration surfaces grant no authority. Demo outcomes, generated receipts, labels, discovery, and receipt locators must not be promoted into authorization.

## Adapter boundary

The LLM-adapter remains transport/ingress/egress, not StegGate authority. Optional transparency use must not create a parallel evaluator, receipt authority, custody store, or consequence path.
