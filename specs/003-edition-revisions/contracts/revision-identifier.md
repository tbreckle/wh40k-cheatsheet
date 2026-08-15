# Contract: Revision Identifier (`YYYY-MM-DD-NN`)

Feature: [spec.md](../spec.md) · Plan: [plan.md](../plan.md) · Data model: [data-model.md](../data-model.md)

The grammar, validation, and ordering rules the `RevisionId` value object must honor.

## Grammar

```text
revision-id = YYYY "-" MM "-" DD "-" NN
YYYY = 4 digits    MM = 2 digits    DD = 2 digits    NN = 2 digits (00–99)
regex: ^\d{4}-\d{2}-\d{2}-\d{2}$
```

## Rules

| # | Rule | Source |
|---|------|--------|
| R1 | Must match the regex exactly (fixed width, zero-padded) | FR-002 |
| R2 | `YYYY-MM-DD` must be a real calendar date | FR-002, FR-009 |
| R3 | `NN` is `00`–`99` (max 100 revisions/day) | FR-003 |
| R4 | Ordering is total, by `(date, sequence)`; latest = maximum | FR-005 |
| R5 | Canonical string form re-emits zero-padded `YYYY-MM-DD-NN` | — |
| R6 | Identifiers are unique within an edition | FR-004 |

## Valid

```text
2026-08-01-00      # first revision on that day
2026-08-01-01      # second revision same day → later than -00
2026-12-31-99      # max daily sequence
```

Ordering example (ascending): `2026-07-01-00` < `2026-08-01-00` < `2026-08-01-01`.

## Invalid (must be rejected with a format-describing message)

```text
2026-8-1-0         # R1: not zero-padded / wrong widths
2026-13-40-00      # R2: not a real calendar date
2026-08-01-100     # R1/R3: sequence not two digits / > 99
2026-08-01         # R1: missing NN
20260801-00        # R1: missing date separators
latest             # R1: not an identifier
```
