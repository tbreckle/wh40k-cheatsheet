# Phase 0 Research: Subphase Heading

Feature: [spec.md](./spec.md) · Plan: [plan.md](./plan.md)

Unlike `005-page-breaks`/`006-column-reset` (which required verifying non-obvious WeasyPrint layout
behavior) or `007-spanning-headline` (which required verifying `column-span: all` support), this
feature reuses only mechanisms already verified and shipped in this codebase: the `render_block`
dispatch pattern, the `:root` custom-property palette, and the light-mode/grayscale pairing from
`011-print-friendly-pdf`. No new WeasyPrint capability is exercised.

---

## 1. Reusing the `phase` markup shape with a modifier class

**Decision**: Render `subphase` as `<h2 class="phase phase--sub">{{ title }}</h2>`, exactly mirroring
how `spanning_headline` renders as `<h2 class="phase phase--spanning">{{ title }}</h2>` (§1 of
`007-spanning-headline`'s research). `.phase--sub` overrides only `background-color`.

**Rationale**: `h2.phase` and `h2.phase--sub` share equal CSS specificity (element + one class each);
source order alone decides which wins where both apply to the same property. Since `.phase--sub` is
declared after `.phase` in the stylesheet, its `background` declaration wins for elements carrying
both classes, while every other `.phase` property (padding, font-size, uppercase, letter-spacing,
`break-inside`/`break-after`) is inherited unchanged. This is the same technique already proven
correct for `.phase--spanning` (which overrides `column-span`/`margin-top` instead).

**Alternatives considered**:
- *A wholly separate `h2.subphase` rule, duplicating every `phase` property*: would work identically
  but duplicates five declarations for no benefit, and risks drifting out of sync with `phase` if its
  typography changes later. Rejected in favor of the modifier-class approach already established by
  `spanning_headline`.

---

## 2. Distinguishing `subphase` from the existing `subsection` heading

**Decision**: `subphase` is a new, third heading level, visually related to `phase` (same width,
typography, and color family — just brighter), and deliberately distinct from the existing
`subsection` heading (`h3`, its own `--green-sub` custom property, smaller font-size, different
padding).

**Rationale**: `subsection` already exists as a lighter-green heading one level below `phase`, but
it's a different HTML element (`h3` vs `h2`) with its own distinct typography — it was not designed to
be "phase, but brighter," it's a separate heading style entirely. The user's ask is specifically for a
`phase`-shaped heading with only its color changed. Reusing `subsection`'s existing
`--green-sub` (`#5f8a6e`) value for the new block would conflate two conceptually different things
(a differently-styled heading level, vs. a same-styled-but-brighter variant of `phase`) under one
color; a new, distinct custom property (`--green-subphase`) keeps the two independent, so a future
change to either doesn't silently affect the other.

**Alternatives considered**:
- *Reuse `--green-sub` (`subsection`'s existing color) for `subphase` too*: rejected — couples two
  independently-motivated heading styles through a shared color variable, and `#5f8a6e` was tuned for
  `subsection`'s smaller, `h3`-based presentation, not validated against `phase`'s `h2` bar.

---

## 3. Grayscale pairing in print-friendly mode

**Decision**: Add `--green-subphase` following the exact pattern already established for every other
color-bearing custom property in `011-print-friendly-pdf`'s `:root` block: a light-mode value and a
print-friendly grayscale value, chosen via the same Jinja ternary (`{{ 'grayscale' if print_friendly
else 'color' }}`), with the grayscale value distinct from `--green-dark`'s grayscale value
(`#262626`) so `phase` and `subphase` remain distinguishable in print-friendly mode (FR-004), exactly
as `011` already keeps callout and stratagem-timing variants distinguishable via distinct grey shades
rather than relying on color alone.

**Rationale**: This is a direct, mechanical application of an already-shipped, tested pattern — no
new research needed. `011`'s own test suite (`test_print_friendly_pdf.py`) already asserts every
rendered color resolves to grayscale when the flag is set, and that same suite is extended (not
replaced) to cover the new `--green-subphase` property and its distinguishability from
`--green-dark`.

**Alternatives considered**: None — this is the established, only pattern used for every existing
custom property in this stylesheet.

---

## Resolved unknowns summary

| Unknown | Resolution |
|---------|------------|
| Can `subphase` reuse `phase`'s markup/CSS shape? | Yes — modifier class overriding only `background-color`, same technique as `.phase--spanning` |
| Does this conflict with the existing `subsection` heading? | No — `subphase` is a distinct heading level with its own custom property; `subsection` is untouched |
| Print-friendly grayscale handling | Direct application of the existing `011-print-friendly-pdf` pattern; no new mechanism |
| Python code changes needed | None — template/CSS only |

No open NEEDS CLARIFICATION items remain.
