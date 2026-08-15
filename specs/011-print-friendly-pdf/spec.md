# Feature Specification: Print-Friendly PDF Flag

**Feature Branch**: `011-print-friendly-pdf`

**Created**: 2026-08-15

**Status**: Draft

**Input**: User description: "Command line flag for a printer friendly version of the pdf's that are black/white/grey and no background image."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate a printer-friendly PDF via a CLI flag (Priority: P1)

A user running the `generate` command wants a version of the cheat sheet suited to black-and-white
printing — one that doesn't waste ink on colored highlights or the faint background logo watermark,
and prints cleanly on a black-and-white/greyscale printer. They pass a new flag to `generate` and
receive a PDF where every color has been replaced with black, white, or grey, and the background
watermark image is absent, while the text, layout, and page structure are otherwise unchanged from
the standard version.

**Why this priority**: This is the entire feature — a single opt-in flag that produces a
print-optimized rendering. There is no smaller meaningful slice.

**Independent Test**: Run `generate` with the new flag for an edition/revision/language and inspect
the resulting PDF: no non-grayscale colors appear anywhere (headers, callout boxes, borders, table
rows), no watermark image is visible on any page, and all text/content matches the standard version.

**Acceptance Scenarios**:

1. **Given** a valid edition, **When** the user runs `generate` with the print-friendly flag,
   **Then** a PDF is produced in which every element that would otherwise be colored (green
   headers, blue "info" callouts, green/red/yellow "Your Turn"/"Opponent Turn"/"Either" callouts,
   cream section backgrounds) instead renders using only black, white, and shades of grey.
2. **Given** the print-friendly flag is set, **When** the PDF is generated, **Then** the faint
   diagonal background logo watermark does not appear on any page.
3. **Given** the print-friendly flag is set, **When** the PDF is generated, **Then** the document's
   text content, section structure, and page/column breaks are identical to the standard version —
   only color and the background image differ.
4. **Given** the print-friendly flag is set, **When** the PDF is generated, **Then** the standard
   (color, watermarked) PDF is still produced as usual — the print-friendly PDF is an additional
   output, not a replacement, and neither overwrites the other.
5. **Given** the print-friendly flag is omitted, **When** `generate` is run, **Then** output is
   byte-for-byte unaffected by this feature — only the standard colored PDF is produced, exactly as
   before.
6. **Given** callout boxes that are normally distinguished only by color ("Your Turn" vs "Opponent
   Turn" vs "Either" vs "Info"), **When** the print-friendly PDF is generated, **Then** those boxes
   remain visually distinguishable from one another (e.g., via different grey shades and/or border
   styles), not collapsed into indistinguishable identical grey boxes.

---

### Edge Cases

- What happens when the print-friendly flag is combined with `--revision` and `--language`? It
  applies the same way as the standard PDF generation — the print-friendly PDF is produced for
  whichever (edition, revision, language) combination(s) are resolved, alongside the standard PDF
  for each.
- What happens to the header/footer running title, page numbers, and edition/revision text? They
  remain present and legible, rendered in black/grey instead of the standard palette.
- What happens if the logo image asset is missing? Generation still fails per existing behavior
  (FR-005 of feature 010) for the standard PDF; the print-friendly PDF does not reference the
  watermark image at all, so its generation is unaffected by the logo asset's presence.
- What happens with the intermediate HTML file that is normally retained alongside the PDF? A
  print-friendly HTML file is retained alongside the print-friendly PDF, following the same naming
  convention used to distinguish print-friendly output from standard output.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The `generate` command MUST accept a new opt-in flag (e.g. `--print-friendly`) that
  requests a printer-friendly rendering of the PDF, usable in combination with the existing
  `--edition`, `--revision`, and `--language` flags.
- **FR-002**: When the flag is set, every color used in the standard rendering (section headers,
  "Your Turn"/"Opponent Turn"/"Either"/"Info" callout backgrounds and text, cream section
  backgrounds, colored borders/rules) MUST instead render using only black, white, and shades of
  grey.
- **FR-003**: When the flag is set, the generated document MUST NOT include the background logo
  watermark image on any page.
- **FR-004**: The print-friendly rendering MUST preserve the same text content, section structure,
  and page/column breaks as the standard rendering for the same (edition, revision, language) —
  only color treatment and the background image differ.
- **FR-005**: The print-friendly rendering MUST preserve visual distinction between the different
  callout box types ("Your Turn", "Opponent Turn", "Either", "Info") using non-color means (e.g.,
  distinct grey shades and/or border styles), so their meaning is not lost when color is removed.
- **FR-006**: The print-friendly PDF (and its retained intermediate HTML) MUST be written to output
  file(s) distinct from the standard PDF/HTML for the same (edition, revision, language), so
  generating one never overwrites the other.
- **FR-007**: When the flag is set, `generate` MUST still produce the standard colored,
  watermarked PDF as usual for each resolved (edition, revision, language) — the print-friendly
  output is additional, not a replacement.
- **FR-008**: Omitting the flag MUST leave `generate`'s existing behavior and output completely
  unchanged from before this feature.
- **FR-009**: `generate`'s per-document result output (one line per generated file) MUST include
  the print-friendly PDF's path when the flag is set, consistent with how the standard PDF's path
  is already reported.

### Key Entities

- **Print-Friendly Rendering**: An alternate rendering mode for a generated document that replaces
  the standard color palette with black/white/grey equivalents and omits the background watermark
  image, while preserving all text content, structure, and page layout. Produced only when
  explicitly requested via the new flag, as an additional output alongside the standard rendering.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of colored elements in the standard rendering (headers, callout boxes,
  backgrounds, borders) render using only black, white, or grey in the print-friendly rendering.
- **SC-002**: 0% of pages in a print-friendly rendering show the background logo watermark.
- **SC-003**: 100% of text content and page/column break placement in a print-friendly rendering
  matches the corresponding standard rendering for the same (edition, revision, language).
- **SC-004**: Generating with the print-friendly flag always yields two distinct, non-overwriting
  output files (standard and print-friendly) per (edition, revision, language); generating without
  the flag yields exactly the same single output as before this feature.
- **SC-005**: A reader can distinguish "Your Turn", "Opponent Turn", "Either", and "Info" callout
  boxes from one another in a print-friendly rendering without relying on color.

## Assumptions

- The flag is boolean/opt-in (e.g. `--print-friendly`); its exact name is a planning-phase detail.
- "No background image" refers to the existing diagonal logo watermark (feature 010) — the only
  background image currently present in the document; no other embedded images exist in content
  today.
- The print-friendly PDF is written as an additional file (not a replacement), using a naming
  convention that distinguishes it from the standard file (e.g. a `-print` suffix on the output
  filename), consistent with the project's existing per-(edition, revision, language) output
  layout.
- "Black/white/grey" permits multiple shades of grey (not strictly two-tone), which is necessary to
  preserve the existing visual distinction between the four callout box types without color.
- Only the currently-supported page size/orientation (A4 portrait) and existing content/layout are
  in scope; no new content or layout changes are introduced by this feature.
- The print-friendly flag applies uniformly to every language generated in the same invocation
  (when `--language` is omitted), not selectively.
