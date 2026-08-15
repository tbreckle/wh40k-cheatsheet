# Contract: CLI Logging Behavior

Feature: [spec.md](../spec.md) · Plan: [plan.md](../plan.md) · Data model: [data-model.md](../data-model.md)

The interface contributors and future features depend on: what levels exist, what stream they go to,
what the flag does, and what is guaranteed regardless of verbosity.

---

## Flag

| Flag | Scope | Default | Effect |
|------|-------|---------|--------|
| `-v`, `--verbose` | Applies to `generate` and `list`; accepted either before or after the subcommand (e.g. both `wh40k-cheatsheet -v generate ...` and `wh40k-cheatsheet generate ... -v` work) | off | Sets the `wh40k_cheatsheet` logger threshold to `DEBUG` instead of `INFO` |

---

## Levels (research.md §1–2)

| Level | Used for | Emitted at default? | Emitted with `--verbose`? |
|-------|----------|:---:|:---:|
| `DEBUG` | Diagnostic detail: resolved paths, chosen template/revision/language | No | Yes |
| `INFO` | Per-stage status: config loaded, edition/revision resolved, content resolved, template rendered, PDF converted | Yes | Yes |
| `WARNING` (`WARN`) | Reserved for future non-fatal anomalies; no current emitter | Yes, if emitted | Yes, if emitted |
| `CRITICAL` | Run-terminating failures (replaces the old bare `print(..., file=sys.stderr)`) | **Always** | **Always** |

`ERROR` is deliberately not used in this feature (research.md §1).

---

## Streams

- **stderr**: every log record, at every level, via one `logging.StreamHandler(sys.stderr)`.
- **stdout**: unchanged from features 002/003 — `generate`'s success lines and all of `list`'s output,
  via plain `print()`. Logging code never writes to stdout.

---

## Behavioral contract

1. **Default visibility** (FR-001/SC-001): running `generate` with no flag prints one `INFO` line per
   major stage, in execution order, to stderr, in addition to the existing stdout result lines.
2. **Verbose adds, doesn't replace** (FR-005/US2-2): `--verbose` adds `DEBUG` lines; it does not
   suppress or alter the `INFO` lines that appear by default.
3. **Output parity** (FR-006/SC-003): the generated `.html`/`.pdf` files are byte-identical whether or
   not `--verbose` is passed. Verified by diffing outputs of two runs (one plain, one `--verbose`)
   against the same inputs.
4. **Failures always visible** (FR-007/SC-004): any exception in `cli.KNOWN_ERRORS` is logged at
   `CRITICAL` before `main()` returns `1` — this happens identically at default and verbose
   thresholds, because `CRITICAL` (50) is always ≥ both `INFO` (20) and `DEBUG` (10).
5. **Distinguishable failures** (FR-008): the formatter prefixes every line with its level name
   (`"%(levelname)s %(name)s: %(message)s"`), so a `CRITICAL` line is visually distinct from `INFO`/
   `DEBUG` lines even in a long verbose run.
6. **Per-language attribution** (FR-003/SC-005): every stage message emitted while processing a
   specific (edition, revision, language) is prefixed with that triple, e.g.
   `INFO wh40k_cheatsheet.pipeline: [11e/2026-08-01-00/de] rendering template`.
7. **No content leakage** (FR-010): no log message ever contains cheat-sheet rule text — only
   identifiers, stage names, and paths.
8. **`list` stays concise** (US1-3): `list` is not required to add step-by-step `INFO` logging since
   it does no multi-stage work; its existing stdout output is unaffected.

---

## Example output (illustrative)

```text
$ wh40k-cheatsheet generate --edition 11e --language en
INFO wh40k_cheatsheet.config.loader: configuration loaded
INFO wh40k_cheatsheet.pipeline: [11e/2026-08-01-00/en] resolving revision
INFO wh40k_cheatsheet.pipeline: [11e/2026-08-01-00/en] resolving content
INFO wh40k_cheatsheet.render.html_renderer: [11e/2026-08-01-00/en] template rendered
INFO wh40k_cheatsheet.pdf.weasyprint_pdf: [11e/2026-08-01-00/en] PDF converted
11e / 2026-08-01-00 / en -> out/11e/2026-08-01-00/en.pdf
```

```text
$ wh40k-cheatsheet generate --edition does-not-exist -v
DEBUG wh40k_cheatsheet.config.loader: resolved project.yaml at /repo/project.yaml
INFO wh40k_cheatsheet.config.loader: configuration loaded
CRITICAL wh40k_cheatsheet.cli: Error: edition 'does-not-exist' not found. Available: 11e
```
