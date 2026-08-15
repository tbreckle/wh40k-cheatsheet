# Implementation Plan: PDF Generation from Templated Source Files

**Branch**: `002-pdf-generation` | **Date**: 2026-08-13 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/002-pdf-generation/spec.md`

## Summary

Build a command-driven generator that renders the WH40K cheatsheet to PDF via a two-stage pipeline:
**(1)** load and validate a single YAML **project configuration file** (editions → template +
languages, with optional per-language template overrides), resolve the per-(edition, language)
strings and HTML fragments by directory convention, and render a **Jinja2** template to an HTML
document; **(2)** convert that HTML to **PDF** with **WeasyPrint**. Configuration is modeled and
validated with **Pydantic**; YAML is parsed with **PyYAML**. The intermediate HTML is a retained,
inspectable artifact. The generator runs on the Python 3.12+ / uv toolchain established by feature
`001-python-quality-gates`.

## Technical Context

**Language/Version**: Python 3.12+ (`requires-python = ">=3.12"`, shared with feature 001)

**Primary Dependencies**:
- **pydantic** (v2) — typed models + validation for the project configuration structure
- **PyYAML** — parse the YAML project configuration file
- **Jinja2** — render templates into an HTML document (stage 1)
- **WeasyPrint** — convert HTML → PDF (stage 2)

**Storage**: Filesystem only. Inputs: YAML config, per-edition/per-language string catalogs and HTML
fragments (by directory convention), Jinja2 templates. Outputs: HTML (intermediate) and PDF.

**Testing**: pytest (from feature 001). Config-validation tests, template-render (golden HTML)
tests, content-resolution tests, and a PDF smoke test (valid, openable, non-empty PDF).

**Target Platform**: Local developer machines and CI (Linux). WeasyPrint requires native libraries
(Pango, cairo, GDK-PixBuf, HarfBuzz) present on the host — a documented environment prerequisite.

**Project Type**: Single project — a CLI/library application under `src/wh40k_cheatsheet/`.

**Performance Goals**: Under 10 seconds per (language, edition) PDF for a typical cheatsheet on a
standard developer machine (SC-006).

**Constraints**: Fully offline (no network at generation time), consistent with the constitution's
offline-capable goal. Output must be reproducible in content (SC-004) — WeasyPrint document metadata
(e.g., creation timestamp) MUST be pinned/normalized so repeated runs are content-equivalent. The
project configuration file is structure-only; content is located by convention (FR-019).

**Scale/Scope**: A handful of editions × several languages; documents of tens of pages. Content set
grows with the game; the pipeline is per-(edition, language) and embarrassingly parallel across
combinations.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Assessment |
|-----------|------------|
| I. Code Quality | **Satisfied.** Code lives under the feature-001 gates (ruff/pylint/bandit/ty); Pydantic models give typed, self-documenting config boundaries. |
| II. Testing Standards (NON-NEGOTIABLE) | **Satisfied by design.** Golden-HTML render tests, config-validation tests, content-resolution tests, and a PDF validity test. Each maps to acceptance scenarios. New rules/data validated by schema (Pydantic) → constitution's data-validation clause. |
| III. User Experience Consistency | **Directly served.** One shared template per edition (with optional per-language override) enforces identical layout across languages; strings carry exact game vocabulary unchanged (constitution: no reworded rules). Missing strings are reported, never silently blanked (FR-009). |
| IV. Performance Requirements | **Satisfied.** <10s/PDF budget (SC-006); generation is fully local/offline. HTML intermediate aids fast iteration. |
| Additional Constraints & Standards | **Satisfied.** YAML config is structured, version-controlled, human-reviewable; editions provide the traceable, edition-attributable sourcing the constitution requires; no secrets. |
| Development Workflow & Quality Gates | **Satisfied.** Ships under the same PR-gated workflow; WeasyPrint native deps documented so CI stays green. |

**Verdict**: PASS. No violations; Complexity Tracking not required.

## Project Structure

### Documentation (this feature)

```text
specs/002-pdf-generation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── config-schema.md         # YAML project-config schema contract
│   └── generate-command.md      # CLI command contract
└── tasks.md             # Phase 2 (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

```text
src/wh40k_cheatsheet/
├── __init__.py
├── cli.py                  # Command entrypoint: generate / list
├── config/
│   ├── __init__.py
│   ├── models.py           # Pydantic models: ProjectConfig, Edition, LanguageEntry
│   └── loader.py           # PyYAML load + Pydantic validation → ProjectConfig
├── content/
│   ├── __init__.py
│   └── resolver.py         # Convention-based resolution of strings + HTML per (edition, lang)
├── render/
│   ├── __init__.py
│   └── html_renderer.py    # Jinja2 environment; render template → HTML (stage 1)
├── pdf/
│   ├── __init__.py
│   └── weasyprint_pdf.py   # HTML → PDF via WeasyPrint, with pinned metadata (stage 2)
└── pipeline.py             # Orchestrates: config → resolve → render HTML → convert PDF

editions/                   # Content root (convention-based; sample fixture data)
└── <edition-id>/
    ├── <lang-code>/        # strings + HTML fragments for that edition+language
    └── ...
templates/                  # Jinja2 templates referenced by config `template` keys
project.yaml                # The single YAML project configuration file (editions/languages/templates)

tests/
├── unit/                   # config models/loader, content resolver, renderer units
├── integration/            # end-to-end generate (fixture edition) → HTML + PDF
├── golden/                 # expected HTML snapshots for render tests
└── fixtures/               # sample project.yaml, editions/, templates/
```

**Structure Decision**: Single-project src layout, extending the package seeded by feature 001. The
pipeline is split into four cohesive modules — `config`, `content`, `render`, `pdf` — orchestrated by
`pipeline.py`, mirroring the two-stage "templates → HTML → PDF" flow and keeping each external
dependency (PyYAML+Pydantic, Jinja2, WeasyPrint) behind a single module boundary for testability and
future swap-ability.

## Complexity Tracking

> No constitution violations. Section intentionally left empty.
