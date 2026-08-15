# Phase 1 Data Model: PDF Generation

Feature: [spec.md](./spec.md) · Plan: [plan.md](./plan.md)

Entities map the spec's Key Entities to concrete Pydantic models and runtime structures. Field types
use Python/Pydantic notation.

---

## Config models (Pydantic v2, `extra="forbid"`)

### `LanguageEntry`

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `template` | `str \| None` | optional | Per-language template file name; overrides the edition template (FR-017). `None` → inherit edition template. |

### `Edition`

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `template` | `str` | **mandatory** | Default template file name for the edition (FR-016). |
| `languages` | `dict[str, LanguageEntry]` | **mandatory** | Keyed by simple language code (`en`, `de`, `it`, …) (FR-016, FR-018). |

**Validation rules**
- `languages` MUST be non-empty (validator).
- Language keys SHOULD match a simple language-code pattern (e.g., `^[a-z]{2}(-[A-Za-z0-9]+)?$`).
- Unknown keys anywhere → validation error (`extra="forbid"`) → reported per FR-008.

### `ProjectConfig`

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `editions` | `dict[str, Edition]` | **mandatory** | Keyed by edition id; the authoritative set of buildable editions (FR-015). |

**Derived helpers** (not stored): `list_editions()`, `list_languages(edition_id)`,
`resolve_template(edition_id, lang) -> str` (returns language override else edition template).

Example (`project.yaml`):

```yaml
editions:
  10e:
    template: base.html.j2
    languages:
      en: {}
      de:
        template: base.de.html.j2
      it: {}
```

---

## Content structures (resolved by convention)

### `StringCatalog`

| Field | Type | Notes |
|-------|------|-------|
| `language` | `str` | Language code. |
| `entries` | `dict[str, str]` | key → translated text; referenced by templates. One catalog per language. |

Loaded from `editions/<edition-id>/<lang-code>/` (FR-019). A referenced key absent here surfaces via
Jinja2 `StrictUndefined` → reported (FR-009).

### `HtmlFragment`

| Field | Type | Notes |
|-------|------|-------|
| `name` | `str` | Fragment identifier / filename stem. |
| `markup` | `str` | Pre-authored trusted HTML, injected at explicit reviewed points. |

Located in the same per-(edition, language) directory. Broken/missing fragment → reported (Edge
Cases), not silently embedded.

### `RenderContext`

The assembled input to Jinja2 for one (edition, language): the resolved `StringCatalog`, the set of
`HtmlFragment`s, and edition/language identifiers. Produced by the content resolver + config.

---

## Pipeline artifacts

### `GenerationRequest`

| Field | Type | Notes |
|-------|------|-------|
| `edition_id` | `str` | Must exist in `ProjectConfig.editions` (else clear error listing available). |
| `language` | `str \| None` | A specific language, or `None` = all languages of the edition (FR-005). |

### `GeneratedDocument`

| Field | Type | Notes |
|-------|------|-------|
| `edition_id` | `str` | Identifies the edition (FR-012). |
| `language` | `str` | Identifies the language (FR-012). |
| `html_path` | `Path` | Retained intermediate HTML artifact (stage 1). |
| `pdf_path` | `Path` | Output PDF (stage 2), valid & openable (FR-003). |

**Validation rules**
- Exactly one `GeneratedDocument` per (edition, language) combination (spec Assumptions, FR-007).
- Content reproducible across runs (FR-010/FR-011) via normalized PDF metadata (research §7).

---

## Relationships

```text
ProjectConfig (project.yaml, Pydantic-validated)
   └── editions: dict[edition_id → Edition]
                          ├── template: str (mandatory)
                          └── languages: dict[lang → LanguageEntry(template?)]

GenerationRequest(edition_id, language?)
   │ resolve_template()  +  content resolver (convention editions/<edition>/<lang>/)
   ▼
RenderContext(StringCatalog, [HtmlFragment], ids)
   │ Jinja2 (StrictUndefined, autoescape)
   ▼
HTML document ──WeasyPrint (pinned metadata)──► GeneratedDocument(html_path, pdf_path)
```

## State / flow

Generation is a stateless transform per (edition, language): validate config → resolve template &
content → render HTML → convert PDF. No persistent state or transitions; same inputs → equivalent
outputs.
