# Contract: `package` CLI Command

Feature: [spec.md](../spec.md) · Plan: [plan.md](../plan.md) · Data model: [data-model.md](../data-model.md)

---

## CLI contract

| # | Guarantee | Basis |
|---|-----------|-------|
| G1 | `wh40k-cheatsheet package` builds every edition and every language declared in `project.yaml` — never a hardcoded or partial subset | FR-002; SC-005; data-model.md §2 |
| G2 | Each built PDF is staged at `<dist-dir>/<edition_id>-<language>.pdf` (default `dist-dir`: `dist/`, resolved relative to `--project-root` unless given as an absolute path — matching how `out/` is already resolved), flat, no subdirectories | FR-008; data-model.md §2 |
| G3 | If generation fails for any single edition/language, the command exits non-zero and no partial/complete `dist/` is presented as successful — the CI step that ran it fails, so nothing downstream (artifact upload, release publish) ever sees a partial build | Edge case: "the whole build step fails... a release is all-editions-and-languages or nothing" |
| G4 | Adding a new edition or language to `project.yaml` is picked up automatically on the next run — no code or CI change required | FR-002; SC-005 |
| G5 | `--project-root` behaves identically to `generate`/`list`'s existing flag (defaults to `.`) | Consistency with existing CLI conventions |

## Example

```bash
uv run wh40k-cheatsheet package
# dist/11e-en.pdf
# dist/11e-de.pdf

uv run wh40k-cheatsheet package --dist-dir out/dist --project-root ./repo-checkout
```

## Failure-mode contract

| # | Guarantee | Basis |
|---|-----------|-------|
| F1 | A `ContentError`/`RenderError`/`PdfError` from any single edition/language propagates as-is (same `KNOWN_ERRORS` handling as `generate`) — exit code `1`, clear message identifying which edition/language/language failed | Reuses `generate()`'s existing error messages unchanged |
