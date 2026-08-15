# Contract: Revision Selection (generate / list)

Feature: [spec.md](../spec.md) · Plan: [plan.md](../plan.md)

Extends feature 002's `generate` / `list` commands with revisions. Only the revision-related behavior
is specified here; all other generate/list guarantees from feature 002 still apply.

## Commands

| Command | Purpose | Revision behavior |
|---------|---------|-------------------|
| `generate --edition <id> [--language <code>]` | Generate using the **latest** revision | Selects `RevisionSet.latest()` for the edition (FR-006) |
| `generate --edition <id> --revision <YYYY-MM-DD-NN> [--language <code>]` | Generate a **specific** revision | Uses exactly that revision (FR-007) |
| `list` | Show inventory | For each edition, list its revisions in chronological order with the latest marked (FR-010) |

## Behavioral contract

1. **Default latest** (FR-006): omitting `--revision` selects the maximum `RevisionId` for the edition,
   including correct handling of multiple revisions on the same day (highest `NN`).
2. **Explicit selection** (FR-007): a valid, existing `--revision` is used exactly; the latest is not
   substituted.
3. **Unknown revision** (FR-008): a well-formed but non-existent `--revision` fails with a message
   listing the edition's available revisions; no output is produced.
4. **Malformed revision** (FR-009): a `--revision` that violates the identifier contract fails with a
   message describing the required `YYYY-MM-DD-NN` format.
5. **No revisions** (FR-011): an edition with zero valid revisions fails clearly on generate and on
   list; no empty/default output.
6. **Per-edition scope** (FR-013): revision selection for one edition never affects another.
7. **Traceable output** (FR-012): output is written under and identified by edition + revision, e.g.
   `out/<edition-id>/<revision-id>/<lang-code>.{html,pdf}`.
8. **Content checks still apply**: selecting a revision does not bypass feature 002's content
   validation (missing string/HTML still reported for the chosen revision).

## Failure message examples

- `Revision error: '2026-13-40-00' is not a valid revision id (expected YYYY-MM-DD-NN)`  → R2/FR-009
- `Revision error: '2026-07-01-00' not found for edition '10e'. Available: 2026-08-01-00, 2026-08-01-01`  → FR-008
- `Revision error: edition '10e' has no revisions`  → FR-011
