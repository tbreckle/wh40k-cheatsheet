# Quickstart: PDF Generation

Feature: [spec.md](./spec.md) · Plan: [plan.md](./plan.md) ·
Contracts: [config-schema.md](./contracts/config-schema.md), [generate-command.md](./contracts/generate-command.md)

Validates the generator end-to-end. Assumes the implementation tasks have produced the pipeline
modules, a sample `project.yaml`, a `templates/` template, and a fixture edition under `editions/`.

## Prerequisites

- Python 3.12+ and **uv** (from feature 001).
- **WeasyPrint native libraries** installed on the host: Pango, cairo, GDK-PixBuf, HarfBuzz.
  (Install via the OS package manager per WeasyPrint's platform docs before running PDF steps.)

## Setup

```bash
uv sync         # installs pydantic, pyyaml, jinja2, weasyprint (+ dev tools)
```

## Validation scenarios

### Scenario 1 — List available editions and languages (SC-007, FR-013)

```bash
uv run wh40k-cheatsheet list      # or: uv run poe generate-list
```

**Expected**: prints each edition id and its supported language codes, read from `project.yaml`.
No files are generated.

### Scenario 2 — Generate one (edition, language) PDF (US1, SC-001)

```bash
uv run wh40k-cheatsheet generate --edition 10e --language en
```

**Expected**: an intermediate `out/10e/en.html` and a valid, openable `out/10e/en.pdf` whose content
matches the source strings/HTML laid out by the resolved template.

### Scenario 3 — All languages of an edition in one run (US2, SC-003)

```bash
uv run wh40k-cheatsheet generate --edition 10e
```

**Expected**: exactly one PDF per language declared under `10e`, same layout, language-specific text.

### Scenario 4 — Language template override (FR-017)

Give `de` a `template:` override in `project.yaml`, then generate `--edition 10e --language de`.

**Expected**: the `de` PDF uses the override template; other languages use the edition default.

### Scenario 5 — Missing string is reported, not blanked (US2-3, FR-009)

Remove a referenced string key from the `de` catalog and generate `--edition 10e --language de`.

**Expected**: generation fails with a message naming the missing key, edition, and language; no
partial/corrupt PDF is written (StrictUndefined behavior).

### Scenario 6 — Invalid config is rejected with a located message (FR-008)

Introduce an edition without a `template` (violates C2), then run any generate.

**Expected**: a clear config error naming `editions.<id>.template` and `project.yaml`; nothing is
rendered.

### Scenario 7 — Unknown edition/language fails clearly (Edge Cases)

```bash
uv run wh40k-cheatsheet generate --edition does-not-exist
```

**Expected**: error stating the edition was not found and listing available editions.

### Scenario 8 — Reproducible content (US3, SC-004)

Generate the same (edition, language) twice into two locations and compare.

**Expected**: the two PDFs are content-equivalent (normalized metadata; no wall-clock drift).

## Success signals

- One command produces HTML then a valid PDF per (edition, language) (SC-001).
- All-languages run yields one PDF per language (SC-003).
- Every malformed/missing input yields a clear error and zero corrupt PDFs (SC-005).
- A single PDF generates in under ~10s for a typical cheatsheet (SC-006).
- Past editions regenerate to identical content (SC-004).
