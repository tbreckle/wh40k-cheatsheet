# Quickstart: Print-Friendly PDF Flag

Validates the feature end-to-end once implemented. See [contracts/print-friendly-flag.md](./contracts/print-friendly-flag.md)
for the exact guarantees being checked and [data-model.md](./data-model.md) for the grayscale
palette and output-file layout referenced below.

## Prerequisites

```bash
cd /home/tobi/code/wh40k-cheatsheet
uv sync
```

## 1. Generate with the flag

```bash
uv run wh40k-cheatsheet generate --edition 11e --language en --print-friendly
```

**Expected**: two result lines for the `en` document — the existing standard-PDF line, plus a new
line naming the print-friendly PDF's path (contract C4). Exit code `0`.

## 2. Confirm both output files exist and neither overwrote the other

```bash
ls out/11e/*/en.pdf out/11e/*/en-print.pdf out/11e/*/en.html out/11e/*/en-print.html
```

**Expected**: all four files present, distinct paths (contract O1/O2).

## 3. Confirm the flag-omitted path is unaffected

```bash
uv run wh40k-cheatsheet generate --edition 11e --language en
ls out/11e/*/en-print.pdf 2>&1   # should still exist from step 1 — not deleted
```

Re-running without `--print-friendly` must not touch `en-print.*`, and `en.pdf`/`en.html` bytes
must be identical to what a pre-feature `generate` (no flag) would have produced (contract C3).

## 4. Visual check

Open `out/11e/<latest-revision>/en-print.pdf` in a PDF viewer alongside `en.pdf`:

- No color anywhere in `en-print.pdf` — headers, callouts, and stratagem cards render in
  black/white/grey only (guarantee G1).
- No faint diagonal logo visible on any page of `en-print.pdf` (guarantee G2), present as usual in
  `en.pdf`.
- Same text, same page count, same section order in both files (guarantee G3).
- The three stratagem-timing bars ("YOUR TURN" / "OPPONENT'S TURN" / "EITHER PLAYER'S TURN") are
  still visually distinguishable from each other by their icon, text, and grey shade (guarantee G4).

## 5. Run the automated checks

```bash
uv run pytest tests/integration/test_print_friendly_pdf.py -v
uv run pytest   # full suite — confirms no regression to existing output
```

**Expected**: all tests pass, including the grayscale computed-style assertions, the
watermark-box-absence assertion, and the content/page-count parity assertion described in
plan.md's Testing section.
