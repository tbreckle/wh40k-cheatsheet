# Contract: Generate Command Interface

Feature: [spec.md](../spec.md) · Plan: [plan.md](../plan.md)

The CLI is the interface the maintainer depends on. Exposed as a console entrypoint and wired as a
poe task (consistent with feature 001). Two operations: `generate` and `list`.

## Commands

| Command | Purpose | Exit code contract |
|---------|---------|--------------------|
| `generate --edition <id> [--language <code>]` | Render HTML then PDF for one edition; one language or all its languages if `--language` omitted | `0` on success for every requested (edition, language); non-zero on any failure |
| `generate --edition <id> --all-languages` | Explicitly generate every language of the edition | `0` iff all succeed |
| `list` | List available editions and, per edition, supported languages | `0`; prints discoverable inventory (FR-013, SC-007) |

(Exact flag spelling is an implementation detail; the operations and their guarantees are the
contract.)

## Behavioral contract

1. **Valid PDF output** (FR-003): each success produces an openable, non-empty PDF plus its retained
   intermediate HTML.
2. **Two-stage, inspectable** (research §1): stage 1 writes HTML; stage 2 writes PDF from that HTML.
3. **Template resolution** (FR-017): language-level `template` wins, else edition `template`.
4. **Fail loud, no partial output** (FR-008): a missing/malformed config, missing template, missing
   language directory, or unresolved string reference stops that unit with a clear message naming the
   file/key/context; no corrupt or partial PDF is emitted.
5. **Unknown selectors** (Edge Cases): unknown `--edition` or `--language` fails clearly and lists
   what is available.
6. **All-languages run** (FR-005/SC-003): produces exactly one PDF per supported language in a single
   invocation.
7. **Identifiable output** (FR-012): each output is associated with its edition and language (e.g., in
   the output path/filename).
8. **Reproducible content** (FR-010/FR-011/SC-004): same inputs → content-equivalent PDFs across runs
   (normalized PDF metadata).
9. **Performance** (SC-006): a single (edition, language) PDF completes under ~10s for a typical
   cheatsheet.

## Output layout (illustrative)

```text
out/
└── <edition-id>/
    ├── <lang-code>.html     # retained intermediate
    └── <lang-code>.pdf      # final artifact
```

## Failure message examples

- `Config error: editions.10e.template is required (project.yaml)`  → C2
- `Content error: missing string 'weapon.range' for edition '10e' language 'de'`  → FR-009
- `Selection error: edition 'X' not found. Available: 10e, 9e`  → Edge Cases
