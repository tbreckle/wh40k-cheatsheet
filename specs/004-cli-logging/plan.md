# Implementation Plan: CLI Progress Logging & Verbose Mode

**Branch**: `004-cli-logging` | **Date**: 2026-08-14 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/004-cli-logging/spec.md`

## Summary

Add operator-facing progress visibility to the existing `generate`/`list` CLI (features
`002-pdf-generation`, `003-edition-revisions`) using Python's standard-library **`logging`**
framework. A per-module logger hierarchy under `wh40k_cheatsheet` emits **INFO**-level stage
messages (config loaded, edition/revision resolved, content resolved, template rendered, PDF
converted) by default, and **DEBUG**-level diagnostic detail (resolved paths, chosen
template/revision/language) when a new `-v`/`--verbose` flag is passed. Run-terminating failures —
currently a bare `print(..., file=sys.stderr)` in `cli.main` — become **CRITICAL**-level log records,
which the logging module's built-in level ordering guarantees are emitted regardless of the chosen
threshold. **WARNING** (the level the user calls "WARN" — `logging.WARN` is a legacy alias constant
for the same value) is wired in architecturally for future non-fatal anomalies. All log output goes
to **stderr** via a single `StreamHandler`; the CLI's existing result output (success lines, `list`
output) stays on **stdout** via plain `print()`, unchanged — cleanly separating "data output" from
"operational logging" per Unix convention and directly satisfying the spec's requirement that
existing output is preserved and that verbosity never changes generated files.

## Technical Context

**Language/Version**: Python 3.12+ (shared with features 001–003)

**Primary Dependencies**: None new — Python's standard-library `logging` module only, per explicit
user instruction. No third-party logging library.

**Storage**: N/A — console output only; no log files are written (per spec Assumptions, out of
scope).

**Testing**: pytest (from feature 001). Log-level threshold tests (default vs. `--verbose`), stage-
message-presence tests, CRITICAL-always-visible tests, and a byte-identical-output test (verbose vs.
non-verbose) map directly to the spec's success criteria.

**Target Platform**: Same as features 001–003 — local dev + CI (Linux), CLI invocation.

**Project Type**: Single project — extends the existing `src/wh40k_cheatsheet/` package; no new
modules beyond a small `logging_setup` helper.

**Performance Goals**: Logging overhead is negligible; no measurable change to the existing <10s
per-PDF generation budget (feature 002 SC-006).

**Constraints**: Log output MUST NOT alter generated HTML/PDF bytes (FR-006/SC-003) — enforced by
routing logs exclusively to stderr, never touching the render/PDF code paths' return values. Log
messages MUST NOT include cheat-sheet rule text (FR-010) — only stage names, identifiers, and paths.

**Scale/Scope**: Adds logging calls to existing pipeline stages (`config/loader.py`, `pipeline.py`,
`content/resolver.py`, `render/html_renderer.py`, `pdf/weasyprint_pdf.py`) and a `-v`/`--verbose` flag
plus a small setup helper in `cli.py`. No new pipeline behavior.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Assessment |
|-----------|------------|
| I. Code Quality | **Satisfied.** Small, focused addition (one setup helper + logger-per-module calls); ships under the existing feature-001 gates. |
| II. Testing Standards (NON-NEGOTIABLE) | **Satisfied by design.** Level-threshold behavior, stage-message presence, and output-parity (verbose vs. non-verbose) are all directly testable and map to SC-001–SC-005. |
| III. User Experience Consistency | **Directly served.** This feature *is* a UX-consistency improvement — predictable, ordered, per-stage feedback instead of a silent wait, with errors always visible regardless of verbosity. |
| IV. Performance Requirements | **Satisfied.** Logging calls are cheap; no impact on the existing generation-time budgets. |
| Additional Constraints & Standards | **Satisfied.** No new dependencies; no secrets or content ever logged (FR-010). |
| Development Workflow & Quality Gates | **Satisfied.** Ships through the same PR-gated workflow as prior features. |

**Verdict**: PASS. No violations; Complexity Tracking not required.

## Project Structure

### Documentation (this feature)

```text
specs/004-cli-logging/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/            # Phase 1 output
│   └── logging-contract.md      # Levels, streams, flag, message-shape contract
└── tasks.md              # Phase 2 (/speckit-tasks — NOT created here)
```

### Source Code (repository root) — changes to the existing package

```text
src/wh40k_cheatsheet/
├── logging_setup.py     # NEW: configure_logging(verbose: bool) -> None
├── cli.py                # CHANGED: -v/--verbose flag; configure_logging() in main(); CRITICAL on failure
├── pipeline.py            # CHANGED: module logger; INFO stage messages per (edition, revision, language); DEBUG diagnostic detail
├── config/loader.py       # CHANGED: module logger; INFO "configuration loaded" / DEBUG resolved path
├── content/resolver.py    # CHANGED: module logger; INFO "content resolved" / DEBUG resolved path
├── render/html_renderer.py# CHANGED: module logger; INFO "template rendered" / DEBUG template name
└── pdf/weasyprint_pdf.py  # CHANGED: module logger; INFO "PDF converted" / DEBUG output path

tests/
├── unit/test_logging_setup.py       # threshold selection (INFO vs DEBUG), stderr handler
└── integration/test_generate_logging.py  # stage messages present & ordered; verbose adds detail;
                                            # output bytes identical verbose vs non-verbose; CRITICAL
                                            # visible at both levels
```

**Structure Decision**: Single new module, `logging_setup.py`, centralizes handler/formatter/level
configuration; every existing pipeline module gets a `logging.getLogger(__name__)` logger and a
handful of `logger.info(...)`/`logger.debug(...)` calls at existing stage boundaries — no new
architectural layers, no new dependencies, minimal surface area on top of features 001–003.

## Complexity Tracking

> No constitution violations. Section intentionally left empty.
