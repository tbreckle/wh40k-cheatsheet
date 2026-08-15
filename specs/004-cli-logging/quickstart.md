# Quickstart: CLI Progress Logging & Verbose Mode

Feature: [spec.md](./spec.md) · Plan: [plan.md](./plan.md) ·
Contract: [contracts/logging-contract.md](./contracts/logging-contract.md)

Validates logging/verbosity end-to-end on top of the existing `002`/`003` generator. Assumes the
implementation tasks have added `logging_setup.py`, the `-v`/`--verbose` flag, and per-stage log
calls.

## Prerequisites

Same as feature 002/003: `uv sync`, WeasyPrint native libraries installed, `project.yaml` and
`editions/11e/2026-08-01-00/{en,de}/content.yaml` present.

## Validation scenarios

### Scenario 1 — Default run shows per-stage status (US1, SC-001)

```bash
uv run wh40k-cheatsheet generate --edition 11e --language en
```

**Expected**: stderr shows one `INFO` line per stage (config loaded, revision resolved, content
resolved, template rendered, PDF converted), in order; stdout still shows the existing
`11e / 2026-08-01-00 / en -> out/...` result line, unchanged from before this feature.

### Scenario 2 — Verbose adds diagnostic detail without changing output (US2, SC-002/SC-003)

```bash
uv run wh40k-cheatsheet generate --edition 11e --language en -v
diff <(uv run wh40k-cheatsheet generate --edition 11e --language en) \
     <(uv run wh40k-cheatsheet generate --edition 11e --language en -v) 2>/dev/null
```

**Expected**: the `-v` run additionally prints `DEBUG` lines (resolved paths, chosen
template/revision). The generated `out/11e/2026-08-01-00/en.{html,pdf}` files are byte-identical
between the two runs (`diff`/`cmp` on the files themselves, not the console output).

### Scenario 3 — Multi-language run stays attributable (US1-2/US2, SC-005)

```bash
uv run wh40k-cheatsheet generate --edition 11e
```

**Expected**: stage messages for `en` and `de` are grouped and each line is prefixed with its own
`[11e/2026-08-01-00/<lang>]` context — no message is ambiguous about which language it belongs to.

### Scenario 4 — Errors always visible, at any verbosity (US3, SC-004)

```bash
uv run wh40k-cheatsheet generate --edition does-not-exist
uv run wh40k-cheatsheet generate --edition does-not-exist -v
```

**Expected**: both invocations print a clearly visible `CRITICAL` line naming the problem and exit
non-zero; the verbose run's extra `DEBUG` output does not bury or hide the failure.

### Scenario 5 — `list` remains concise (US1-3)

```bash
uv run wh40k-cheatsheet list
```

**Expected**: output is unchanged from before this feature — no new step-by-step logging is required
for a command with no multi-stage work.

## Success signals

- A maintainer can tell what stage a `generate` run is in without any extra flag (SC-001).
- One flag (`-v`/`--verbose`) yields materially more diagnostic detail (SC-002).
- Generated files are byte-identical regardless of verbosity (SC-003).
- 100% of failures are clearly visible at any verbosity (SC-004).
- Multi-language runs remain correctly attributable from console output alone (SC-005).
