# Quickstart: Skip Cheat Sheet Sections on Generation

Feature: [spec.md](./spec.md) · Plan: [plan.md](./plan.md) · Data model: [data-model.md](./data-model.md) ·
Contracts: [contracts/cli-skip-flags.md](./contracts/cli-skip-flags.md),
[contracts/section-marker-block.md](./contracts/section-marker-block.md)

Validates the feature end-to-end once implemented. Each scenario names the guarantee it checks.

## Prerequisites

```bash
cd /path/to/wh40k-cheatsheet
uv sync
```

WeasyPrint native libraries installed, same as every prior feature.

## 1. Quality gates

```bash
uv run poe check
```

**Expected**: all gates pass, including the new `tests/unit/test_sections.py`,
`tests/integration/test_skip_sections_pdf.py`, `test_skip_sections_cli.py`, and
`test_section_markers_shipped_content.py`.

## 2. Regression: no flags → identical output (FR-006, SC-003)

On the commit **before** this feature, generate a baseline and keep a copy:

```bash
uv run wh40k-cheatsheet generate --edition 11e
cp -r out/11e /tmp/baseline-11e
```

On the feature commit (content now has `section` markers):

```bash
uv run wh40k-cheatsheet generate --edition 11e
diff /tmp/baseline-11e/2026-06-01-00/en.html out/11e/2026-06-01-00/en.html && echo "en unchanged ✓"
diff /tmp/baseline-11e/2026-06-01-00/de.html out/11e/2026-06-01-00/de.html && echo "de unchanged ✓"
```

**Expected**: no diff (contract M2 in section-marker-block.md). The printed result lines are
identical to before.

## 3. Skip one section (US1, FR-003/004/005)

```bash
uv run wh40k-cheatsheet generate --edition 11e --language en --skip-core-stratagems
```

**Expected**: prints `11e / 2026-06-01-00 / en -> out/11e/2026-06-01-00/en-no-core-stratagems.pdf`.
Open it: no STRATAGEMS heading, no stratagem cards, no USING STRATAGEMS; every other page matches
the full sheet; no blank page at the end. `out/11e/2026-06-01-00/en.pdf` from step 2 is unchanged
(SC-007).

```bash
uv run wh40k-cheatsheet generate --edition 11e --language en --skip-core-rules
```

**Expected**: `en-no-core-rules.pdf` starts directly with CORE ABILITIES; no leading blank page.

## 4. Skip several sections; order doesn't matter (US2, FR-012)

```bash
uv run wh40k-cheatsheet generate --edition 11e --language en --skip-core-stratagems --skip-core-rules
uv run wh40k-cheatsheet generate --edition 11e --language en --skip-core-rules --skip-core-stratagems
```

**Expected**: both runs write the same file, `en-no-core-rules-core-stratagems.pdf`, containing only
CORE ABILITIES and DATASHEET CHARACTERISTICS (SC-005).

## 5. Nothing would remain → fail, nothing written (FR-011)

```bash
uv run wh40k-cheatsheet generate --edition 11e --skip-core-rules --skip-core-abilities \
  --skip-datasheet-characteristics --skip-core-stratagems; echo "exit: $?"
uv run wh40k-cheatsheet generate --edition 10e --skip-core-rules --skip-core-abilities \
  --skip-core-stratagems; echo "exit: $?"
```

**Expected**: both exit `1` with a CRITICAL error naming what would be empty; no new or changed files
under `out/` (check with `ls -la --time-style=full-iso out/11e/*/ out/10e/*/` before and after).

## 6. Section absent from the edition → no-op (US3, FR-009)

```bash
uv run wh40k-cheatsheet generate --edition 10e --skip-datasheet-characteristics
```

**Expected**: succeeds and writes `out/10e/2026-06-16-00/de.pdf` (standard name, research.md §7),
identical to generating without the flag.

## 7. Print-friendly and multi-language (US3, FR-008)

```bash
uv run wh40k-cheatsheet generate --edition 11e --print-friendly --skip-datasheet-characteristics
ls out/11e/2026-06-01-00/
```

**Expected**: `en-no-datasheet-characteristics.pdf`, `en-no-datasheet-characteristics-print.pdf`,
`de-no-datasheet-characteristics.pdf`, `de-no-datasheet-characteristics-print.pdf` alongside the
untouched full `en.pdf`, `en-print.pdf`, `de.pdf`, `de-print.pdf`. None of the four new PDFs
contains DATASHEET CHARACTERISTICS / DATENBLATT-KENNWERTE.

## 8. Unknown flag rejected before generation (FR-010)

```bash
uv run wh40k-cheatsheet generate --edition 11e --skip-stratagems; echo "exit: $?"
```

**Expected**: exit `2`, argparse "unrecognized arguments: --skip-stratagems"; `--help` lists all four
`--skip-*` flags (FR-015). Nothing written.

## 9. Releases unaffected (FR-014)

```bash
uv run wh40k-cheatsheet package
ls dist/
```

**Expected**: the same full-sheet assets as before (`11e-en.pdf`, `11e-de.pdf`, `10e-de.pdf`); no
`-no-` file anywhere in `dist/`.

## 10. Broken markers fail loudly (contract V1–V3)

Temporarily add a second `{type: section, id: core-rules}` marker to
`editions/11e/2026-06-01-00/en/content.yaml` and run `generate --edition 11e --language en`.

**Expected**: exit `1`, a `ContentError` naming the file and the duplicated id. Revert the change.
