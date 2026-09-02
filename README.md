# Warhammer 40,000 Cheat Sheets

[![quality](https://github.com/tbreckle/wh40k-cheatsheet/actions/workflows/quality.yml/badge.svg?branch=develop)](https://github.com/tbreckle/wh40k-cheatsheet/actions/workflows/quality.yml)

A free, print-ready quick-reference cheat sheet for **Warhammer 40,000**. It gathers the phases,
core rules, stratagems, and other need-to-know info for an edition of the game onto a compact,
well-organized PDF you can print and keep on the table during a game — no more flipping through
rulebooks mid-turn.

Available in multiple languages, and kept up to date as rules get corrected or clarified between
official releases.

## Download

Head to the **[Releases page](https://github.com/tbreckle/wh40k-cheatsheet/releases)** to grab the
latest PDF for your edition and language.

## Run it yourself

Prefer to generate the PDFs locally instead of grabbing a release? You'll need Python 3.12+ and
[uv](https://docs.astral.sh/uv/):

```bash
git clone https://github.com/tbreckle/wh40k-cheatsheet.git
cd wh40k-cheatsheet
uv sync
```

WeasyPrint (the PDF renderer) needs native libraries on your machine — Pango, cairo, GDK-PixBuf,
HarfBuzz — install them via your OS package manager first.

<details>
<summary><strong>Debian / Ubuntu</strong></summary>

```bash
sudo apt-get update
sudo apt-get install libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libharfbuzz0b libcairo2
```

</details>

<details>
<summary><strong>Fedora</strong></summary>

```bash
sudo dnf install pango cairo-gobject gdk-pixbuf2 harfbuzz
```

</details>

<details>
<summary><strong>macOS</strong></summary>

Via [Homebrew](https://brew.sh/):

```bash
brew install pango
```

(Homebrew's `pango` formula pulls in cairo, HarfBuzz, and GDK-PixBuf as dependencies.)

</details>

<details>
<summary><strong>Windows</strong></summary>

WeasyPrint needs the GTK3 runtime, which bundles Pango, cairo, GDK-PixBuf, and HarfBuzz. Download
and run the latest installer from the
[GTK3 Windows Runtime Environment Installer](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases)
project, then make sure the option to add GTK3 to your `PATH` is checked (or add its `bin`
directory to `PATH` yourself) before opening a new terminal.

See WeasyPrint's own
[install guide](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#installation) for
more detail or troubleshooting.

</details>

List what's available, then generate a PDF:

```bash
uv run wh40k-cheatsheet list
uv run wh40k-cheatsheet generate --edition 11e --language en
```

`--edition` is required; `--revision` and `--language` default to the latest revision and all
languages if omitted. Add `--print-friendly` for an extra black/white/grey PDF with no background
watermark. Output lands in `out/`. Run `uv run wh40k-cheatsheet --help` (or `<subcommand> --help`)
for the full option list.

## More information

- Contributing content or code: see [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)
- Authoring or editing cheat sheet content: see [docs/CONTENT_AUTHORING.md](docs/CONTENT_AUTHORING.md)

## Acknowledgements

The 11th edition content in `editions/11e/2026-08-01-00/en/content.yaml` is transcribed from a
community-made cheat sheet shared on Reddit — thank you to its original creator [Kaysette](https://www.reddit.com/user/Kaysette/):
[11th edition cheat sheet thread](https://www.reddit.com/r/Warhammer40k/comments/1tv312v/11th_edition_cheat_sheet/). The
translations are a derivative work of that content.

## Legal

*Warhammer 40,000*, the Warhammer 40,000 logo, and all associated names, races, race insignia,
characters, vehicles, locations, weapons, and units are either ®, TM, and/or © Games Workshop
Limited, variably registered around the world, and used without permission. This is an unofficial,
fan-made project, not affiliated with, endorsed by, or sponsored by Games Workshop. No copyright or
trademark infringement is intended; content is provided for free, personal use only.
