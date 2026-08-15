# Phase 0 Research: Edition Revisions

Feature: [spec.md](./spec.md) · Plan: [plan.md](./plan.md)

This feature extends `002-pdf-generation`. Research resolves the deferred design questions:
identifier modeling/ordering, where revisions live, how they interact with templates, and how
selection and discovery integrate with the existing pipeline.

---

## 1. Revision identifier modeling & ordering

**Decision**: A typed, immutable `RevisionId` value object parsed from `YYYY-MM-DD-NN`. Parsing
validates the date with `datetime.date(...)` (rejects impossible dates like `2026-13-40`) and the
sequence with a regex/range check (`NN` = `00`–`99`). Ordering is total, by `(date, sequence)`;
"latest" is the maximum.

**Rationale**: A dedicated value object localizes all format rules (FR-002/FR-003/FR-009) and gives
clear, testable parse errors. Validating the date via the standard library catches non-calendar
dates for free. Although fixed-width, zero-padded, most-significant-first identifiers already sort
correctly as plain strings, parsing to `(date, seq)` makes validation and comparison explicit and
guards against malformed input sneaking through a naive string compare.

**Implementation notes**:
- Grammar: `^\d{4}-\d{2}-\d{2}-\d{2}$`, then `date.fromisoformat(YYYY-MM-DD)` + `0 <= NN <= 99`.
- Represent as frozen dataclass (or Pydantic model) with `date: datetime.date` and `sequence: int`;
  implement ordering via `(date, sequence)`; `__str__` re-emits the canonical zero-padded form.

**Alternatives considered**:
- *Plain string compare only*: works for well-formed input but silently mis-handles malformed values;
  rejected for weaker validation and error messages.
- *Full datetime with time*: unnecessary; the spec treats dates as opaque calendar dates, no timezone.

---

## 2. Where revisions live: filesystem discovery, not config

**Decision**: Revisions are **discovered from the source layout** at
`editions/<edition-id>/<revision-id>/<lang-code>/`. They are NOT listed in `project.yaml`.

**Rationale**: Feature 002 fixed `project.yaml` as structure-only (editions/languages/templates;
FR-019). Adding revisions there would reintroduce content bookkeeping into config and require an edit
for every correction. Discovering revisions as directories named `YYYY-MM-DD-NN` lets "latest" be
computed from what actually exists, and new corrections are added by dropping in a directory.

**Rationale for discovery robustness**: A directory under an edition whose name is not a valid
`RevisionId` is reported (FR-009), not silently skipped or mis-ordered (spec US3/Edge Cases).

**Alternatives considered**:
- *Declare revisions in `project.yaml`*: rejected — breaks 002's structure-only config and duplicates
  filesystem truth.
- *A per-edition manifest file listing revisions*: extra bookkeeping with no benefit over directory
  discovery for this scale.

---

## 3. Templates across revisions

**Decision**: Revisions do **not** change templates. Template resolution continues from feature 002
— the edition template, optionally overridden per language. A revision corrects *content* only.

**Rationale**: The spec defines a revision as a "corrected edition" — a content fix within the same
edition identity, not a layout change. Keeping templates edition/language-scoped avoids duplicating
template config per revision and matches the UX-consistency principle (same layout across
corrections).

**Alternatives considered**:
- *Per-revision template overrides*: no requirement calls for it; adds config surface. Deferred until
  a real need appears.

---

## 4. Selection semantics (default latest + explicit override)

**Decision**: The pipeline resolves the revision **before** content resolution. If no `--revision`
is given, select the latest discovered `RevisionId` (FR-006). If given, it must parse as a valid
identifier (else format error, FR-009) and exist for the edition (else a not-found error listing
available revisions, FR-008). Selection is scoped per edition (FR-013).

**Rationale**: Centralizing selection in one step keeps the content resolver simple (it just receives
a concrete revision) and makes the default/override behavior a single, well-tested decision point.

**Alternatives considered**:
- *Resolve revision lazily inside the content resolver*: scatters selection logic and complicates
  error reporting; rejected.

---

## 5. Discovery & validation behavior

**Decision**: `discovery.py` lists directory entries under `editions/<edition-id>/`, parses each as
a `RevisionId`, and returns them sorted. Malformed entries are surfaced as errors (FR-009); an
edition with zero valid revisions yields a clear "no revisions" report (FR-011). Duplicate
identifiers cannot occur as sibling directory names, but any ambiguity is treated as an error
(FR-004).

**Rationale**: One directory listing per edition is cheap and deterministic. Reporting malformed
entries (rather than ignoring them) prevents a mistyped directory from silently changing which
revision is "latest".

**Alternatives considered**:
- *Silently ignore non-matching directories*: rejected — could hide a mistyped intended revision and
  mislead "latest".

---

## 6. Integration seam with feature 002

**Decision**: Minimal, additive changes: (a) new `revision` module; (b) `content/resolver.py` takes a
revision and resolves `editions/<edition>/<revision>/<lang>/`; (c) `pipeline.py` inserts revision
resolution ahead of content; (d) `cli.py` adds `--revision` to `generate` and revision listing to
`list`; (e) `GeneratedDocument` and the output path gain a revision segment
(`out/<edition>/<revision>/<lang>.{html,pdf}`, FR-012).

**Rationale**: Keeps feature 002's module boundaries intact and confines new logic to one module plus
thin threading, minimizing regression risk and keeping each change reviewable.

**Alternatives considered**:
- *Rewrite the content resolver around revisions*: unnecessary churn; the additive segment suffices.

---

## 7. Reproducibility & performance

**Decision**: No change to feature 002's reproducibility approach — output remains content-equivalent
per `(edition, revision, language)` via normalized PDF metadata. Discovery/selection cost is a single
listing plus an in-memory sort, well within the <10s budget.

**Rationale**: Revisions only pin *which* content is rendered; they do not alter rendering
determinism. Past revisions are naturally reproducible because their content directory is immutable
once published.

---

## Resolved unknowns summary

| Unknown | Resolution |
|---------|------------|
| Identifier model & ordering | `RevisionId` value object; validate date via stdlib + `NN` range; order by `(date, seq)`; latest = max |
| Where revisions live | Filesystem: `editions/<edition>/<revision>/<lang>/`; NOT in `project.yaml` |
| Templates per revision | Unchanged — edition/language template reused; revisions correct content only |
| Selection | Resolve before content; default latest, explicit `--revision`; per-edition scope |
| Discovery/validation | List + parse dirs; malformed reported; zero-revisions reported |
| 002 integration | Additive: new `revision` module + revision threaded through resolver/pipeline/cli |
| Reproducibility/perf | Unchanged; content-equivalent per (edition, revision, language); negligible overhead |

No open NEEDS CLARIFICATION items remain.
