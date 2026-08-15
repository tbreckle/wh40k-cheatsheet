# Phase 1 Data Model: Edition Revisions

Feature: [spec.md](./spec.md) · Plan: [plan.md](./plan.md)

Extends the feature-002 data model with a revision level. New/changed entities below.

---

## Entity: `RevisionId` (value object)

Immutable, validated identifier parsed from `YYYY-MM-DD-NN`.

| Field | Type | Notes |
|-------|------|-------|
| `date` | `datetime.date` | Parsed from the `YYYY-MM-DD` part; must be a real calendar date. |
| `sequence` | `int` | The `NN` part, `0`–`99`. |

**Derived**: `__str__` → canonical zero-padded `YYYY-MM-DD-NN`; ordering by `(date, sequence)`.

**Validation rules**
- Must match `^\d{4}-\d{2}-\d{2}-\d{2}$` (FR-002).
- `YYYY-MM-DD` must be a valid calendar date (FR-009); invalid → parse error.
- `0 <= sequence <= 99` (FR-003); out of range → parse error.
- Total order: `a < b` iff `(a.date, a.sequence) < (b.date, b.sequence)` (FR-005).

---

## Entity: `Revision`

A corrected content set for an edition.

| Field | Type | Notes |
|-------|------|-------|
| `id` | `RevisionId` | Unique within its edition (FR-004). |
| `edition_id` | `str` | Owning edition (selection is per-edition, FR-013). |
| `path` | `Path` | `editions/<edition-id>/<revision-id>/` — root for its per-language content. |

**Validation rules**
- Belongs to exactly one edition.
- Its per-language content is resolved under `path/<lang-code>/` (feature 002 convention, now nested
  under the revision).

---

## Entity: `RevisionSet` (per edition)

The discovered, ordered collection of an edition's revisions.

| Field | Type | Notes |
|-------|------|-------|
| `edition_id` | `str` | Owning edition. |
| `revisions` | `list[Revision]` | Sorted ascending by `RevisionId`. |

**Derived helpers**: `latest() -> Revision` (max; error if empty, FR-011);
`get(id: RevisionId) -> Revision` (error listing available if absent, FR-008);
`ids() -> list[RevisionId]` (chronological, for `list`, FR-010).

**Validation rules**
- Built by discovery: list directories under `editions/<edition-id>/`, parse each name as a
  `RevisionId`. A non-matching/malformed directory name is reported, not skipped (FR-009).
- Empty set → clear "no revisions for edition" error on generate/list (FR-011).

---

## Changed entities (from feature 002)

### `GenerationRequest` (changed)

| Field | Type | Notes |
|-------|------|-------|
| `edition_id` | `str` | Unchanged. |
| `revision` | `RevisionId \| None` | **NEW**: specific revision, or `None` = latest (FR-006/FR-007). |
| `language` | `str \| None` | Unchanged (`None` = all languages). |

### `GeneratedDocument` (changed)

| Field | Type | Notes |
|-------|------|-------|
| `edition_id` | `str` | Identifies the edition. |
| `revision` | `RevisionId` | **NEW**: the concrete revision used (FR-012). |
| `language` | `str` | Identifies the language. |
| `html_path` / `pdf_path` | `Path` | Output under `out/<edition-id>/<revision-id>/<lang-code>.{html,pdf}`. |

---

## Relationships

```text
Edition (feature 002)
  └── RevisionSet (discovered from editions/<edition-id>/*)
          └── Revision (id: RevisionId, path)
                  └── <lang-code>/  → StringCatalog + HtmlFragments (feature 002 resolver)

GenerationRequest(edition_id, revision?, language?)
   │ revision resolution:  revision ?? RevisionSet.latest()   (per edition)
   ▼
(edition, revision, language) → feature-002 pipeline (template from edition/language, unchanged)
   ▼
GeneratedDocument(edition_id, revision, language, html_path, pdf_path)
```

## State / flow

Revision selection is a pure function of the request and the discovered `RevisionSet`: parse/validate
request → discover set → pick latest or requested → hand a concrete `(edition, revision, language)` to
the existing pipeline. No persistent state; a published revision directory is immutable, making past
revisions reproducible (FR from spec, SC-002/US3).
