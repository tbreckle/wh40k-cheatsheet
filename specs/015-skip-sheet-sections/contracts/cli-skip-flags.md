# Contract: `generate --skip-*` Flags

Feature: [spec.md](../spec.md) · Plan: [plan.md](../plan.md) · Data model: [data-model.md](../data-model.md) ·
Related: [section-marker-block.md](./section-marker-block.md)

---

## CLI contract

| # | Guarantee | Basis |
|---|-----------|-------|
| C1 | `generate` accepts four boolean flags (`action="store_true"`, default `False`): `--skip-core-rules`, `--skip-core-abilities`, `--skip-datasheet-characteristics`, `--skip-core-stratagems` | FR-001; planning input |
| C2 | Each flag maps to the section id equal to its suffix (`core-rules`, `core-abilities`, `datasheet-characteristics`, `core-stratagems`); the CLI passes the set of passed flags' ids to `generate(..., skip_sections=frozenset(...))` | FR-001; FR-007; data-model.md §1, §4 |
| C3 | The flags compose freely with each other and with `--edition`, `--revision`, `--language`, `--print-friendly`, and `-v`/`--verbose`; order is irrelevant; repeating a flag is harmless | FR-002; spec edge cases |
| C4 | Passing none of the flags leaves `generate`'s behavior, written files, and printed result lines byte-for-byte identical to before this feature | FR-006; SC-003 |
| C5 | `generate --help` lists all four flags, each naming the section it omits | FR-015 |
| C6 | Result lines keep their existing format (`<edition> / <revision> / <lang> -> <pdf path>`, plus the `(print-friendly)` line when requested); the paths are simply the partial files' paths | FR-006; research.md §8 |
| C7 | `package` gains no `--skip-*` flag and always builds full sheets | FR-014 |

## Output-file contract

| # | Guarantee | Basis |
|---|-----------|-------|
| O1 | A sheet from which at least one section was actually omitted is written alongside the full sheet in `out/<edition>/<revision>/`; it never overwrites, modifies, or deletes the full sheet's `<lang>.{html,pdf}` or `<lang>-print.{html,pdf}` | FR-012; SC-007 |
| O2 | File stem = `<lang>` + (`-no-` + actually-omitted ids joined by `-`, in canonical order `core-rules`, `core-abilities`, `datasheet-characteristics`, `core-stratagems`) + (`-print` for the print-friendly variant). HTML and PDF share the stem | FR-012; data-model.md §6; research.md §7 |
| O3 | Examples: `--skip-core-stratagems` → `en-no-core-stratagems.pdf` / `en-no-core-stratagems-print.pdf`; `--skip-core-stratagems --skip-core-rules` → `en-no-core-rules-core-stratagems.pdf` (same name for either flag order) | FR-012; spec edge cases |
| O4 | If none of the selected sections are present in a given sheet (e.g. `--skip-datasheet-characteristics` for 10e), that sheet is written under its standard stem (`de.pdf`), with content identical to generating it without the flag | FR-009; FR-012 |
| O5 | The omission applies to every language generated in the run and to both the standard and print-friendly variant of each | FR-008 |
| O6 | `GeneratedDocument.omitted_sections` is a `tuple[str, ...]` of actually-omitted ids in canonical order, `()` when nothing was omitted | data-model.md §7 |

## Failure-mode contract

| # | Guarantee | Basis |
|---|-----------|-------|
| F1 | An unrecognized flag (e.g. `--skip-stratagems`) is rejected with exit code `2` and an "unrecognized arguments" message that itself lists the four valid `--skip-*` flags, before any content is resolved or output written. `cli.main` adds that listing (via `parse_known_args` + `parser.error`), because argparse reports unknown subcommand arguments through the top-level parser, whose usage line doesn't show `generate`'s flags (verified 2026-09-15). Unknown non-`--skip-` flags keep argparse's plain message | FR-010 |
| F2 | `generate(..., skip_sections=...)` called programmatically with an id outside the four section ids raises `PipelineError` naming the invalid id(s) and listing the valid ones, before resolving any content | FR-010 |
| F3 | If, after omission, **any** sheet in the run would contain no content blocks (all four flags passed, or e.g. 10e with `--skip-core-rules --skip-core-abilities --skip-core-stratagems`), `generate` raises `PipelineError` naming the edition, revision, language, and skipped sections - before rendering or writing **any** file for **any** language in the run; CLI exit code `1` | FR-011; SC-004; research.md §6 |
| F4 | Requesting any skip against content with no `section` markers raises `ContentError` naming the content file; CLI exit code `1` | research.md §5; contracts/section-marker-block.md V4 |
| F5 | F2–F4 errors are reported through `cli.py`'s existing `KNOWN_ERRORS` path (`logger.critical`, exit `1`), never as an uncaught traceback | Consistency with existing CLI error handling |

---

## Mechanism (implementation detail, documented for traceability)

```python
# cli.py - generate subparser
for section_id in SECTION_IDS:
    generate_parser.add_argument(
        f"--skip-{section_id}",
        action="store_true",
        help=f"Omit the '{section_id}' section from the generated sheet(s)",
    )

# _cmd_generate
skip_sections = frozenset(
    section_id for section_id in SECTION_IDS if getattr(args, f"skip_{section_id.replace('-', '_')}")
)
documents = generate(
    config, paths, args.edition, revision=..., language=..., print_friendly=..., skip_sections=skip_sections
)
```

```python
# pipeline.py - generate (sketch)
_validate_selection(skip_sections)                        # F2
prepared = []
for lang in languages:                                    # resolve + omit ALL first
    context = resolve_content(...)                        # validates markers (V1–V3)
    result = omit_sections(context["document"]["blocks"], skip_sections)   # F4
    if not _has_content(result.blocks):
        raise PipelineError(...)                          # F3 - nothing written yet
    prepared.append((lang, context_with(result.blocks), result.omitted))
return [_render_one(..., filename_stem=output_stem(lang, omitted, print_friendly=False), ...)
        for lang, context, omitted in prepared]           # O1–O6
```
