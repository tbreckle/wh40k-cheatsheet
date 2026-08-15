# Phase 0 Research: CLI Progress Logging & Verbose Mode

Feature: [spec.md](./spec.md) · Plan: [plan.md](./plan.md)

The user specified the technology (Python's stdlib `logging` framework) and named four levels —
DEBUG, INFO, WARN, CRITICAL. Research below resolves how those levels map onto the spec's
requirements, and the remaining integration questions (streams, flag, message shape).

---

## 1. Level mapping: default vs. verbose, and why CRITICAL (not ERROR) for failures

**Decision**: Two operator-selectable thresholds — **INFO** (default) and **DEBUG** (`--verbose`).
Stage messages (FR-001) are logged at **INFO**; extra diagnostic detail (FR-005 — resolved paths,
chosen template/revision/language) is logged at **DEBUG**. Run-terminating failures (today's
`print(f"Error: {exc}", file=sys.stderr)` in `cli.main`) become **CRITICAL** log records.

**Rationale**: The user asked for exactly DEBUG/INFO/WARN/CRITICAL — notably omitting the more
conventional `ERROR`. Since every failure this CLI currently raises is command-terminating (the
process exits 1), treating it as **CRITICAL** ("this run cannot continue/complete") is a defensible,
intentional reading of that omission rather than an oversight to silently correct. Python's logging
level ordering (`DEBUG=10 < INFO=20 < WARNING=30 < ERROR=40 < CRITICAL=50`) guarantees a `CRITICAL`
record is emitted at *any* threshold at or below `CRITICAL` — so with only two thresholds in use
(`INFO`/`DEBUG`), failures are always visible, directly satisfying FR-007/SC-004 with zero special-
case logic.

**Alternatives considered**:
- *Use `ERROR` for failures (standard practice)*: more conventional, but explicitly not what was
  asked; would silently diverge from the user's four named levels without a stated reason.
- *Introduce a fifth, custom level*: unnecessary — stdlib's five built-in levels already cover every
  case the spec needs.

---

## 2. "WARN" vs. "WARNING"

**Decision**: Use the standard level **`WARNING`** (value 30) and its default display name
`"WARNING"`. `logging.WARN` is not a distinct level — it is a legacy alias constant equal to
`logging.WARNING`. No custom `logging.addLevelName(30, "WARN")` remapping is applied.

**Rationale**: The four levels the user asked for *are* fully available and used as named — `WARN`
is simply the pre-3.4-style spelling of the same level object. Renaming the display text would be
pure cosmetic churn with no functional benefit and would diverge from how every other Python tool
and log-reading habit expects `WARNING` to look. The level is wired in architecturally (module
loggers may call `logger.warning(...)`) even though the current spec identifies no concrete
WARNING-worthy condition yet — it is reserved for future non-fatal anomalies (e.g., a future
"falling back to a default template" case).

**Alternatives considered**:
- *Remap the level name to "WARN"*: rejected — nonstandard, purely cosmetic, adds a global
  `addLevelName` side effect for no behavioral gain.

---

## 3. Log stream vs. result stream

**Decision**: All logging (`INFO`/`DEBUG`/`WARNING`/`CRITICAL`) is written to **stderr** via a single
`logging.StreamHandler(sys.stderr)`. The CLI's existing result output — the `generate` success lines
(`edition / revision / language -> path`) and the entire `list` output — remains **plain `print()` to
stdout**, completely unchanged.

**Rationale**: This is the standard Unix separation of "diagnostic/operational text" (stderr) from
"data a script might pipe or capture" (stdout). It directly satisfies FR-009 ("existing final result
output... MUST continue to appear... this feature adds visibility, it does not remove existing
output") and FR-006/SC-003 (verbose mode must never alter *generated output* — here read as: it does
not even touch the CLI's own stdout result stream, only stderr).

**Alternatives considered**:
- *Interleave logs and results on stdout*: rejected — breaks piping/capturing of `generate`/`list`
  output and risks a maintainer misreading a log line as a result line.
- *Send logs to stdout, results to stderr*: rejected — inverts the Unix convention for no benefit.

---

## 4. Flag design

**Decision**: A single boolean flag, `-v` / `--verbose`, added to the **top-level** parser (applies
to both `generate` and `list`), defaulting to `False`. `configure_logging(verbose=args.verbose)` runs
once in `cli.main()` before dispatching to the subcommand handler.

**Rationale**: A top-level flag (rather than per-subcommand) means `--verbose` works identically
regardless of which command follows, matching the spec's framing of "verbose mode" as a general
property of a run (US2), and avoids duplicating the flag definition on every subparser.

**Alternatives considered**:
- *Per-subcommand `--verbose`*: more argparse boilerplate for no behavioral difference; rejected.
- *Repeatable `-v`/`-vv` for multiple verbosity tiers*: the spec defines exactly two tiers (default,
  verbose) — no need for finer granularity now; can be added later without breaking this design.

---

## 5. Per-language / per-stage attribution (FR-003, SC-005)

**Decision**: Since `generate` processes languages **sequentially** within a single thread/process
(no concurrency), true log-line interleaving cannot occur. Attribution is achieved by prefixing every
stage message emitted from `_generate_one` with its `(edition_id, revision_id, language)` context,
e.g. `logger.info("[%s/%s/%s] rendering template", edition_id, revision_id, language)`.

**Rationale**: Satisfies FR-003/SC-005 (a maintainer can correctly attribute each message) without
needing structured logging, correlation IDs, or thread-local context — the existing sequential
execution model already guarantees ordering; the prefix just makes that ordering legible.

**Alternatives considered**:
- *`logging.LoggerAdapter` / `contextvars`-based context injection*: more machinery than needed for a
  single-threaded, sequential pipeline; deferred unless concurrency is introduced later.

---

## 6. Logger hierarchy & configuration entry point

**Decision**: Each module obtains `logging.getLogger(__name__)` (e.g.
`wh40k_cheatsheet.pipeline`, `wh40k_cheatsheet.config.loader`, …), giving a natural hierarchy under
the `wh40k_cheatsheet` package logger. A new `logging_setup.py` exposes
`configure_logging(verbose: bool) -> None`, which sets the `wh40k_cheatsheet` package logger's level
(`DEBUG` or `INFO`) and attaches one `StreamHandler(sys.stderr)` with a formatter
`"%(levelname)s %(name)s: %(message)s"` — the level name prefix keeps `CRITICAL` visually
distinguishable from routine `INFO`/`DEBUG` lines even under high verbose volume (FR-008).

**Rationale**: A single configuration entry point avoids scattered `basicConfig` calls and keeps
`cli.main()` as the one place that decides verbosity, matching how the CLI already centralizes error
handling.

**Alternatives considered**:
- *`logging.basicConfig()` at import time*: configures the *root* logger, which is less composable
  (harder to test, affects any dependency's logging) — rejected in favor of an explicit, scoped
  setup function.

---

## 7. Output-parity guarantee (SC-003)

**Decision**: No test or verification code inspects log output when comparing generated files;
byte-identical output across verbosity levels is guaranteed structurally because logging calls never
participate in constructing the HTML/PDF — they only read already-computed values (paths, ids) for
display. This is confirmed by re-running the existing manual verification (feature 002/003) once with
and once without `--verbose` and diffing outputs.

**Rationale**: Keeps the guarantee simple and structural rather than relying on incidental test
coverage; also is how the spec itself frames SC-003 as verifiable.

---

## Resolved unknowns summary

| Unknown | Resolution |
|---------|------------|
| Default vs. verbose threshold | `INFO` (default), `DEBUG` (`--verbose`) |
| Failure level | `CRITICAL` (per explicit user level set; always emitted regardless of threshold) |
| "WARN" handling | Standard `WARNING` (30) — `WARN` is just its legacy alias, no remapping needed |
| Log stream | stderr for all logging; stdout stays reserved for existing result output |
| Flag | Top-level `-v`/`--verbose`, boolean, default off |
| Per-language attribution | `[edition/revision/language]` prefix in stage messages; sequential execution already ensures ordering |
| Config entry point | `logging_setup.configure_logging(verbose)`, scoped to the `wh40k_cheatsheet` logger, not root |
| Output parity | Structural — logging never feeds into rendered content |

No open NEEDS CLARIFICATION items remain.
