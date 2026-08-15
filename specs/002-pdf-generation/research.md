# Phase 0 Research: PDF Generation from Templated Source Files

Feature: [spec.md](./spec.md) · Plan: [plan.md](./plan.md)

The technology choices were specified by the user (Pydantic, PyYAML, Jinja2, WeasyPrint, two-stage
HTML→PDF). Research below confirms fit, records rationale, and resolves the integration unknowns each
choice introduces.

---

## 1. Pipeline shape: templates → HTML → PDF (two stages)

**Decision**: A two-stage pipeline. Stage 1 renders a Jinja2 template to a complete HTML document;
stage 2 converts that HTML to PDF with WeasyPrint. The HTML is a **retained, inspectable
intermediate** artifact.

**Rationale**: Separating rendering from PDF conversion makes each stage independently testable
(golden-HTML snapshots for stage 1; PDF-validity checks for stage 2), speeds authoring iteration
(inspect HTML without rendering PDF), and matches the user's explicit "first HTML then PDF"
directive. It also aids debuggability (constitution observability intent).

**Alternatives considered**:
- *Direct-to-PDF (ReportLab-style)*: rejected — loses HTML/CSS layout power and the inspectable
  intermediate; not what was requested.
- *Discard HTML after conversion*: rejected — keeping it is nearly free and greatly aids debugging.

---

## 2. Configuration modeling & validation: Pydantic v2

**Decision**: Model the project configuration with **Pydantic v2** models — `ProjectConfig`,
`Edition`, `LanguageEntry` — with strict validation (no extra keys, required fields enforced).

**Rationale**: Pydantic turns the spec's mandatory/optional-key rules (FR-015–FR-018) into
declarative, self-validating types and produces precise, field-located error messages that satisfy
FR-008 ("clear message naming the file and problem"). Language codes as dict keys map naturally to
`dict[str, LanguageEntry]`.

**Key settings**:
- `model_config = ConfigDict(extra="forbid")` so unknown keys are reported, not ignored.
- `LanguageEntry.template: str | None = None` (optional override); `Edition.template: str` (required).
- A field/model validator asserting each edition has at least one language.

**Alternatives considered**:
- *dataclasses + manual checks*: more boilerplate, weaker error messages.
- *jsonschema*: validates shape but doesn't give typed Python objects the pipeline can consume.

---

## 3. YAML parsing: PyYAML

**Decision**: Parse the YAML config with **PyYAML** using `yaml.safe_load`, then hand the resulting
dict to Pydantic for validation.

**Rationale**: `safe_load` avoids arbitrary-object construction (bandit-clean; no `B506`). PyYAML is
the standard, and separating parse (PyYAML) from validate (Pydantic) keeps a clean seam and lets a
YAML syntax error and a schema error produce distinct, clear messages (FR-008).

**Alternatives considered**:
- *ruamel.yaml*: round-trip/comment preservation not needed for read-only config loading.
- *`yaml.load` (unsafe)*: rejected — security risk, flagged by bandit.

---

## 4. Templating: Jinja2 → HTML

**Decision**: Render HTML with **Jinja2**. A configured `Environment` loads templates from
`templates/` (referenced by the config's `template` keys), with autoescaping on for HTML.

**Rationale**: Jinja2 is the standard Python templating engine; autoescape mitigates injection from
string content. Template selection uses the resolved template name (language override → edition
default, FR-017). Strings and HTML fragments are passed in as the render context.

**Key settings**:
- `autoescape=select_autoescape(["html"])` — but **pre-authored HTML fragments** (FR-001) are
  trusted content authored in-repo and are injected via `| safe` / `Markup` at explicit, reviewed
  points only. This trust boundary is documented so it is a deliberate, auditable choice.
- `undefined=StrictUndefined` so a referenced-but-missing string raises rather than renders empty —
  directly implementing FR-009 (report unresolved references).

**Alternatives considered**:
- *string.Template / f-strings*: too weak for structured layout.
- *Mako/Chameleon*: viable but Jinja2 is the ecosystem default and was requested.

---

## 5. HTML → PDF: WeasyPrint

**Decision**: Convert the rendered HTML to PDF with **WeasyPrint**, driving layout via CSS (print
stylesheets, `@page` rules).

**Rationale**: WeasyPrint renders HTML/CSS to PDF entirely locally (offline — constitution
requirement) with strong CSS paged-media support, fitting a layout-driven cheatsheet. It was
explicitly requested.

**Native dependency note**: WeasyPrint needs system libraries (Pango, cairo, GDK-PixBuf, HarfBuzz).
This is a documented environment prerequisite for both local dev and CI (the CI workflow from
feature 001 must install them before the tests/gates that exercise PDF generation).

**Alternatives considered**:
- *wkhtmltopdf*: unmaintained; heavier/less accurate CSS.
- *Headless Chromium (Playwright)*: heavier, network/binary footprint, overkill for offline docs.

---

## 6. Content resolution convention (strings + HTML)

**Decision**: Resolve per-(edition, language) strings and HTML fragments from a fixed directory
convention rooted at `editions/<edition-id>/<lang-code>/` (per spec Clarification 2026-08-13 /
FR-019). Strings load as a mapping (keyed like the config's language codes); HTML fragments load by
known filenames within that directory.

**Rationale**: Keeps the YAML config structure-only (FR-019) and lets new languages/editions be added
by dropping in directories, no config-path edits. A missing expected file/key is reported per
FR-008/FR-009.

**Open detail deferred to implementation**: exact string-file format inside the language directory
(e.g., a per-language YAML/JSON of key→text). Default assumption: a per-language YAML strings file
loaded with the same PyYAML+validation approach; finalized in data-model/tasks.

**Alternatives considered**:
- *Paths declared in config*: explicitly rejected by the clarification (config stays structure-only).

---

## 7. Reproducible output (SC-004 / FR-010 / FR-011)

**Decision**: Normalize non-deterministic PDF metadata so repeated runs are **content-equivalent**.
Set WeasyPrint document metadata explicitly and avoid embedding a wall-clock creation timestamp
(pin/normalize it); keep dict iteration deterministic (Python dict insertion order + sorted where
needed).

**Rationale**: The spec defines reproducibility as equivalent *content*, not byte-identical (spec
Assumptions). Pinning metadata removes the main source of run-to-run drift while leaving room for a
stricter byte-level mode later if requested.

**Alternatives considered**:
- *Byte-identical guarantee*: not required now; would need deeper control over PDF object ordering —
  deferred unless the reproducibility definition tightens.

---

## 8. Invocation mechanism (CLI)

**Decision**: Expose a **command** (a console entrypoint, also wired as a poe task consistent with
feature 001) with two operations: `generate` (by edition, language, or all) and `list` (available
editions/languages) — satisfying SC-001/SC-003/SC-007 and FR-013.

**Rationale**: A CLI matches the "maintainer runs generation as a build step" assumption in the spec.
Reusing the poe runner keeps one consistent developer entrypoint across features.

**Alternatives considered**:
- *Web service / GUI*: out of scope per spec Assumptions (maintainer build step, not end-user app).

---

## Resolved unknowns summary

| Unknown | Resolution |
|---------|------------|
| Pipeline shape | Two-stage: Jinja2 → HTML (retained) → WeasyPrint → PDF |
| Config validation | Pydantic v2 models, `extra="forbid"`, precise field errors |
| YAML parsing | PyYAML `safe_load`, then Pydantic validation |
| Missing-string behavior | Jinja2 `StrictUndefined` → raises → reported (FR-009) |
| HTML trust boundary | Autoescape on; pre-authored fragments injected via explicit reviewed `safe` |
| PDF engine & native deps | WeasyPrint; Pango/cairo/GDK-PixBuf/HarfBuzz documented for local+CI |
| Content resolution | Convention `editions/<edition-id>/<lang-code>/`; config stays structure-only |
| Reproducibility | Normalize PDF metadata → content-equivalent output |
| Invocation | CLI `generate` / `list`, wired as a poe task |

No open NEEDS CLARIFICATION items remain.
