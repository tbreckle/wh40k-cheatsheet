# Contract: Project Configuration Schema (`project.yaml`)

Feature: [spec.md](../spec.md) · Plan: [plan.md](../plan.md) · Data model: [data-model.md](../data-model.md)

The single YAML project configuration file. This contract is what config authors and the loader
(`config/loader.py` + Pydantic models) must honor. Validated with `extra="forbid"` — unknown keys
are errors.

## Shape

```yaml
editions:                       # mandatory — map of edition id → edition
  <edition-id>:                 # e.g. "10e", "9e"
    template: <file-name>       # mandatory — default template for this edition
    languages:                  # mandatory — non-empty map of language code → entry
      <lang-code>:              # e.g. en, de, it (simple language codes)
        template: <file-name>   # optional — overrides the edition template for this language
```

## Rules

| # | Rule | Source |
|---|------|--------|
| C1 | `editions` is required and is a non-empty map | FR-015 |
| C2 | Each edition MUST have a `template` (string) | FR-016 |
| C3 | Each edition MUST have a non-empty `languages` map | FR-016 |
| C4 | Language keys are simple language codes (`^[a-z]{2}(-[A-Za-z0-9]+)?$`) | FR-018 |
| C5 | A language entry MAY have `template`; if absent, the edition `template` is used | FR-017 |
| C6 | Unknown/misspelled keys anywhere fail validation with the offending path | FR-008 |
| C7 | The file is structure-only — no content/string/HTML paths appear here | FR-019 |

## Valid example

```yaml
editions:
  10e:
    template: base.html.j2
    languages:
      en: {}
      de:
        template: base.de.html.j2
      it: {}
  9e:
    template: legacy.html.j2
    languages:
      en: {}
```

## Invalid examples (must be rejected with a clear, located message)

```yaml
# Missing mandatory edition template
editions:
  10e:
    languages: { en: {} }        # ERROR C2: 'template' required for edition '10e'
```

```yaml
# Empty languages
editions:
  10e:
    template: base.html.j2
    languages: {}                # ERROR C3: edition '10e' has no languages
```

```yaml
# Unknown key
editions:
  10e:
    template: base.html.j2
    langauges: { en: {} }        # ERROR C6: unknown key 'langauges' (did you mean 'languages'?)
```
