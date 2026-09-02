# Quickstart: Alphabetical Core Abilities Glossary

Validates the feature end-to-end once implemented. See
[contracts/glossary-term-ordering.md](./contracts/glossary-term-ordering.md) for the exact
guarantees being checked and [data-model.md](./data-model.md) for the sort key referenced below.

## Prerequisites

```bash
cd /home/tobi/code/wh40k-cheatsheet
uv sync
```

## 1. Run the quality gates

```bash
uv run poe check
```

**Expected**: format, lint, bandit, `ty`, and the full pytest suite all pass — including the new
`tests/unit/test_glossary_order.py` and `tests/integration/test_glossary_order_cross_language.py`,
and the pre-existing `tests/integration/test_reproducible.py` (an unstable sort would break its
byte-identical guarantee — contract G5).

## 2. Generate both languages of the current edition

```bash
uv run wh40k-cheatsheet generate --edition 11e
```

**Expected**: exit code `0`, one result line per language, no warnings about content.

## 3. Confirm the German glossary is now in German alphabetical order

```bash
python3 - <<'PY'
import re, pathlib
html = sorted(pathlib.Path("out/11e").rglob("de.html"))[-1].read_text(encoding="utf-8")
block = re.search(r'<div class="glossary[^"]*">(.*?)</div>', html, re.S).group(1)
terms = re.findall(r'<span class="term__name">(.*?):</span>', block)
print(len(terms), "terms")
print("\n".join(terms))
PY
```

**Expected** — 33 terms, beginning `ANFÜHRER / UNTERSTÜTZUNG`, `ANHALTENDE TREFFER X`, `ANTI-X Y+`,
`EINMALIG`, `EINZELGÄNGER`, … and containing `ÜBERSCHWERER LÄUFER` between `TÖDLICHE TREFFER` and
`VERHEERENDE WUNDEN` (contract G1/G3). Before this feature the list started `ANTI-X Y+`, `STURM`,
`EXPLOSIV X`, `SPALTEN X` — English source order.

Repeat for `10e`, which has its own German glossary of 31 terms whose entries carry bracketed
English glosses (`STURM (Assault)`) — those must act only as tie-breakers, never as the primary key:

```bash
uv run wh40k-cheatsheet generate --edition 10e
```

## 4. Confirm the English output is unchanged

The English 11e glossary is already authored alphabetically, so this feature must be a no-op for it
(contract G6, SC-005). Against a checkout of the pre-feature commit:

```bash
git stash                                   # or check out the parent commit in a worktree
uv run wh40k-cheatsheet generate --edition 11e --language en
cp out/11e/*/en.html /tmp/en-before.html
git stash pop
uv run wh40k-cheatsheet generate --edition 11e --language en
diff /tmp/en-before.html out/11e/*/en.html && echo "unchanged ✓"
```

**Expected**: no diff.

## 5. Confirm authored order does not matter

Temporarily reverse the `terms` list of a glossary block in
`editions/11e/2026-08-01-00/en/content.yaml`, regenerate, and diff against the output from step 4.

**Expected**: identical output — authored order has no effect (contract G7). Revert the content file
afterwards; this feature never requires a content change.

## 6. Confirm layout and the spanning flag are untouched

```bash
uv run wh40k-cheatsheet generate --edition 11e --language en --print-friendly
```

Open `out/11e/<latest-revision>/en.pdf` and `en-print.pdf`:

- The CORE ABILITIES glossary still spans the full page width as one cleanly 2-column unit — not
  fragmented into four narrow columns (feature 007's G2 still holds; contract G9).
- The print-friendly variant is alphabetical too, with no extra wiring (contract G8).
- Term text, punctuation, and any inline markup (`→`, `&gt;`, bold) render exactly as before —
  only positions moved (contract G6).
