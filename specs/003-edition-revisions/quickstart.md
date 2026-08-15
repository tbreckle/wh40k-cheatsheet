# Quickstart: Edition Revisions

Feature: [spec.md](./spec.md) · Plan: [plan.md](./plan.md) ·
Contracts: [revision-identifier.md](./contracts/revision-identifier.md), [revision-selection.md](./contracts/revision-selection.md)

Validates revision selection end-to-end. Builds on feature 002's generator; assumes implementation
tasks have added the `revision` module and threaded revisions through the pipeline and CLI, plus
fixture editions containing revision directories.

## Prerequisites

- Feature 002 working (Python 3.12+, uv, WeasyPrint native libraries installed).
- Fixture layout with revisions, e.g.:
  ```text
  editions/10e/2026-08-01-00/en/ ...
  editions/10e/2026-08-01-01/en/ ...   # a later same-day correction
  ```

## Setup

```bash
uv sync
```

## Validation scenarios

### Scenario 1 — Latest revision by default (US1, SC-001)

```bash
uv run wh40k-cheatsheet generate --edition 10e --language en
```

**Expected**: output produced from `2026-08-01-01` (the highest revision), written under
`out/10e/2026-08-01-01/en.{html,pdf}`.

### Scenario 2 — Latest picks highest same-day sequence (US1-2)

With `2026-08-01-00` and `2026-08-01-01` present, generate without `--revision`.

**Expected**: `2026-08-01-01` is chosen (highest `NN` that day).

### Scenario 3 — Explicit older revision (US2, SC-002)

```bash
uv run wh40k-cheatsheet generate --edition 10e --revision 2026-08-01-00 --language en
```

**Expected**: output produced from `2026-08-01-00`, not the latest; written under
`out/10e/2026-08-01-00/en.{html,pdf}`.

### Scenario 4 — Unknown revision lists available (US2-2, SC-004)

```bash
uv run wh40k-cheatsheet generate --edition 10e --revision 2026-07-01-00
```

**Expected**: failure naming the missing revision and listing the edition's available revisions; no
output written.

### Scenario 5 — Malformed revision rejected (US2-3, SC-003)

```bash
uv run wh40k-cheatsheet generate --edition 10e --revision 2026-13-40-00
```

**Expected**: failure describing the required `YYYY-MM-DD-NN` format (invalid calendar date).

### Scenario 6 — List revisions in order (US3, SC-005)

```bash
uv run wh40k-cheatsheet list
```

**Expected**: for edition `10e`, revisions shown oldest → newest with the latest marked; no
generation.

### Scenario 7 — Malformed revision directory reported (US3-2, SC-003)

Add a bad directory `editions/10e/2026-8-1/` and run `list` or `generate`.

**Expected**: the malformed identifier is reported rather than silently ignored or mis-ordered.

### Scenario 8 — Edition with no revisions (US3-3, FR-011)

Point at an edition directory containing no valid revision subdirectories.

**Expected**: a clear "edition has no revisions" report on generate and on list; no empty output.

## Success signals

- Default generation always uses the newest revision, including same-day (SC-001).
- Explicit `--revision` reproduces exactly that revision (SC-002).
- Malformed/unknown/absent revisions all fail clearly with actionable messages (SC-003/SC-004).
- Every output path encodes its edition and revision for traceability (SC-006).
