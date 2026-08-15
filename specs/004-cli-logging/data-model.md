# Phase 1 Data Model: CLI Progress Logging & Verbose Mode

Feature: [spec.md](./spec.md) · Plan: [plan.md](./plan.md)

This feature is operator-facing console output, not application data. The one conceptual entity from
the spec — **Status Message** — maps directly onto a standard-library `logging.LogRecord`; no new
persisted or in-memory data structures are introduced.

---

## Entity: Status Message → `logging.LogRecord`

| Spec attribute | Realization |
|-----------------|-------------|
| severity/level | `LogRecord.levelname` — one of `DEBUG`, `INFO`, `WARNING`, `CRITICAL` (see research.md §1–2) |
| stage/operation | Encoded in the message text, e.g. `"[11e/2026-08-01-00/en] rendering template"` |
| human-readable text | `LogRecord.getMessage()` |
| origin | `LogRecord.name` — the emitting module's logger name (e.g. `wh40k_cheatsheet.pipeline`) |

**Validation rules**
- MUST NOT contain cheat-sheet rule text — only identifiers (edition/revision/language), stage
  names, and filesystem paths (FR-010).
- A message describing work on a specific (edition, revision, language) MUST include that triple in
  its text so it is attributable (FR-003).
- A message signaling a run-terminating failure MUST be emitted at `CRITICAL` (research.md §1).

---

## Configuration state: `LoggingConfig` (conceptual, not a persisted entity)

| Field | Type | Notes |
|-------|------|-------|
| `verbose` | `bool` | From the `-v`/`--verbose` CLI flag; default `False` |
| `threshold` | `DEBUG \| INFO` | `DEBUG` if `verbose` else `INFO` — the `wh40k_cheatsheet` logger's effective level |
| `stream` | `stderr` | Fixed; not configurable via CLI in this feature |

**Derived behavior**
- `threshold` determines which of `DEBUG`/`INFO` records are emitted; `WARNING` and `CRITICAL` are
  always emitted at either threshold (level ordering: `DEBUG < INFO < WARNING < CRITICAL`).
- Realized by `logging_setup.configure_logging(verbose: bool) -> None`, called once in `cli.main()`.

---

## Relationships

```text
CLI flag (-v/--verbose)
        │
        ▼
LoggingConfig.threshold ──configures──► wh40k_cheatsheet logger + stderr StreamHandler
                                                  │
                       ┌──────────────────────────┼──────────────────────────┐
                       ▼                          ▼                          ▼
        config.loader logger        pipeline logger (per lang)      render/pdf loggers
        INFO: "configuration        INFO: "[ed/rev/lang] resolving  INFO: "[ed/rev/lang]
        loaded" / DEBUG: path       revision" / DEBUG: chosen id    template rendered" / etc.
                       │                          │                          │
                       └──────────────────────────┴──────────────────────────┘
                                                  │
                                       cli.main() failure path
                                       CRITICAL: "Error: ..." (always emitted)
```

No state machine or persistence is required — each log record is emitted once, synchronously, in the
order its corresponding pipeline step executes.
