# Feature Specification: Page Header Logo

**Feature Branch**: `010-page-header-logo`

**Created**: 2026-08-14

**Status**: Draft

**Input**: User description: "Use the Warhammer 40k logo provided in images/logo_40k.png on each page on the top right. The logo shall be resized to a height of 50 pixel keeping the aspect ratio." — later amended: "Change the logo so that it is in the background instead of top right and is full page in a 45° angle with an alpha value of 0.3 to only be shown very light."

## Clarifications

### Session 2026-08-14

- Q: When the logo is scaled up to "full page" size and rotated 45°, should it be sized to fit
  entirely within the page (whole logo visible, some margin near the corners), or sized to cover the
  page edge-to-edge (fills the whole page, but the rotated image's corners get cropped off)? → A: Fit
  within the page — the whole logo stays visible after rotation, with empty margin near the page
  corners; nothing is cropped.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See a faint, consistent brand watermark on every page (Priority: P1)

A reader viewing any page of the generated cheat sheet — the first page or any later page, in any
supported language — sees the Warhammer 40,000 logo as a large, faint, diagonal watermark behind the
page's content, reinforcing the document's identity without competing with or reducing the
readability of the reference text printed over it.

**Why this priority**: This is the entire feature — a single, consistently-placed, correctly-styled
background brand mark across the whole document. There is no smaller meaningful slice.

**Independent Test**: Generate a cheat sheet and visually inspect every page: each one shows the
logo as a large, rotated, faint watermark filling the page behind the content, with all reference
text still fully readable on top of it.

**Acceptance Scenarios**:

1. **Given** a generated cheat sheet with multiple pages, **When** a reader looks at any page,
   **Then** the logo appears as a background watermark on that page, not in a corner.
2. **Given** the logo's source image, **When** it is placed on the page, **Then** it is rotated 45°
   and scaled as large as possible while remaining fully visible within the page bounds (no
   cropping), with its aspect ratio preserved (not stretched or squashed).
3. **Given** the watermark's rendered opacity, **When** it is placed behind the page's content,
   **Then** it renders at approximately 5% opacity (alpha 0.05) — faint enough that it never
   competes with or reduces the readability of the text and reference content printed over it.
4. **Given** a multi-language document (e.g., English and German editions), **When** either language
   is generated, **Then** the watermark appears identically (position, size, rotation, opacity) on
   every page of both.
5. **Given** the page's existing header/footer content (running title, edition/revision, page
   number) and body content, **When** the watermark is added, **Then** all of that existing content
   remains fully legible — the watermark sits strictly behind it, never in front, and never darkens
   text enough to impair reading.

---

### Edge Cases

- What happens if the logo image file is missing or unreadable when the document is generated? The
  system MUST fail generation with a clear message identifying the missing/unreadable asset, rather
  than silently omitting the watermark or producing a broken image placeholder in the output.
- What happens where body content is visually dense (e.g., a stratagem card or data table sits
  directly over the watermark)? The watermark's low opacity (≈0.05) MUST keep all such content fully
  readable — the watermark is a subtle background effect, never a readability hazard.
- What happens across the very first page versus later pages? The watermark appears identically on
  every page — there is no distinct "cover page" behavior in this feature.
- What happens at the page edges after rotation? Because the watermark is sized to fit entirely
  within the page after rotation (per Clarifications), no part of the logo is ever cropped or
  extends past the page boundary.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST display the Warhammer 40,000 logo as a background watermark behind the
  page's content on every generated page — not in a page corner or margin.
- **FR-002**: The watermark MUST be rotated 45° from horizontal.
- **FR-003**: The watermark MUST be scaled as large as possible while remaining fully visible within
  the page bounds after rotation — no part of the image may be cropped or extend past the page edge
  — and MUST preserve the source image's original aspect ratio (no stretching or squashing).
- **FR-004**: The watermark MUST render at approximately 5% opacity (alpha 0.05), faint enough that
  it never reduces the readability of any text or reference content printed over it.
- **FR-005**: The watermark MUST render strictly behind all other page content — running
  header/footer and body content — never in front of or interrupting it.
- **FR-006**: The watermark MUST appear consistently (same position, size, rotation, and opacity) on
  every page of a generated document, regardless of language or page content.
- **FR-007**: If the logo image asset is missing or cannot be read at generation time, the system
  MUST fail generation with a clear, actionable message rather than silently omitting the watermark
  or emitting a document with a broken image.
- **FR-008**: The logo image asset MUST be sourced from the project's version-controlled files
  (`images/logo_40k.png`), consistent with how the project already manages its other source assets.

### Key Entities

- **Logo Watermark**: The Warhammer 40,000 brand image, rendered as a large, faint (≈5% opacity),
  45°-rotated background element behind every generated page's content. Has a fixed source aspect
  ratio, preserved when scaled. Does not vary by language or content; always sits behind, never in
  front of, other page content.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of pages in every generated document show the logo as a background watermark,
  not in a page corner.
- **SC-002**: The watermark's rotation is 45° and its opacity is approximately 5% on every page of
  every generated document.
- **SC-003**: 100% of generated pages show the watermark at its correct source aspect ratio, fully
  visible with no cropping, scaled as large as the page allows.
- **SC-004**: 100% of existing header, footer, and body content remains fully readable — the
  watermark never sits in front of or visually obscures it.
- **SC-005**: Regenerating existing real content after this feature ships shows only the change from
  a corner logo to a background watermark — no other change to page count or layout.

## Assumptions

- "Full page" (per Clarifications) means scaled to the largest size that fits entirely within the
  page bounds after the 45° rotation — not stretched to the page's unrotated width/height, and not
  cropped at the edges.
- The watermark is centered on the page; the exact rotation direction (clockwise vs.
  counter-clockwise) is a planning-phase detail with no material visual or functional difference for
  a diagonal watermark.
- "Alpha value of 0.05" is interpreted as standard CSS/PDF opacity semantics — 5% opaque, 95%
  transparent to whatever is behind it (the page background). This value was tuned down from the
  originally-clarified 0.3 after visual review, per explicit follow-up instruction.
- The watermark is language-independent — the same image, position, rotation, and opacity are used
  regardless of which language edition is generated.
- Only the currently-supported page size/orientation (A4 portrait) is in scope; no other page format
  is introduced by this feature.
- `images/logo_40k.png` is the authoritative, version-controlled source of the logo image, already
  present in the repository.
- This replaces the prior top-right corner placement entirely — there is one logo element per page,
  not two.
