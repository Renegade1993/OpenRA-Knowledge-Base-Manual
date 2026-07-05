# OpenRA Knowledge Base Manual — Export Pipeline

This document describes the repeatable, sustainable workflow for producing the final publishable manual from the Markdown source files.

## Philosophy

The pipeline is split into two layers:

1. **Mechanical layer (scripted, deterministic)** — assembly, verification, and first-pass export. This must be 100% repeatable by anyone, including CI/CD, so the manual can be regenerated for every future OpenRA update.
2. **Design layer (human/AI creative)** — template styling, layout polish, diagram refinement, and final formatting. This is done once (or per major edition) and produces a reference template for the mechanical layer to reuse.

## File layout

```
Manual/
  OpenRA_Knowledge_Base_Manual.md          # combined manual (generated)
  OpenRA_Knowledge_Base_Manual.docx      # exported DOCX (optional, generated)
  OpenRA_Knowledge_Base_Manual.pdf       # exported PDF (optional, generated)
  build files/
    assemble_manual.py                     # source -> combined manual
    verify_paths.py                        # validate OpenRA source paths
    verify_internal_links.py               # validate internal Markdown links
    build_manual.ps1                       # orchestration script
    reference.docx                           # optional Pandoc reference template
    EXPORT_PIPELINE.md                     # this file
  images/                                  # SVG diagrams + actor sprites
  images/actors/                           # cameo/unit sprites per mod
```

## Verification step (always run first)

For Windows users who prefer not to run `.ps1` files directly, a batch wrapper is provided:

```batch
build files\build_manual.bat -Export all
```

The wrapper automatically requests Administrator privileges if they are needed and bypasses the PowerShell execution-policy restriction.

```powershell
cd "Manual\build files"
py assemble_manual.py
py verify_paths.py
py verify_internal_links.py
```

Or use the orchestration script:

```powershell
powershell -ExecutionPolicy Bypass -File "build files\build_manual.ps1"
```

## Export options

### Option A: Pandoc (recommended for the mechanical layer)

Pandoc is free, open-source, and excellent at Markdown → DOCX/PDF conversion. It preserves headings, tables, images, and internal links reasonably well. It is the right tool for the repeatable, unsupervised export.

Requirements:
- Pandoc: https://pandoc.org/installing.html
- For PDF only: a LaTeX engine such as TeX Live or MiKTeX.

Commands:

```powershell
# DOCX
pandoc "OpenRA_Knowledge_Base_Manual.md" -o "OpenRA_Knowledge_Base_Manual.docx"

# PDF with table of contents
pandoc "OpenRA_Knowledge_Base_Manual.md" -o "OpenRA_Knowledge_Base_Manual.pdf" --pdf-engine=xelatex --toc
```

For consistent styling, create a `reference.docx` in `build files/` and use:

```powershell
pandoc "OpenRA_Knowledge_Base_Manual.md" -o "OpenRA_Knowledge_Base_Manual.docx" --reference-doc="build files\reference.docx"
```

The `build_manual.ps1` script encapsulates these commands.

### Option B: Claude / other design tooling (recommended for the design layer)

Claude is useful for:
- Designing the DOCX reference template (fonts, heading styles, page layout, table formatting).
- Deciding which diagrams need polish or replacement.
- Producing a final PDF with custom page design (if Pandoc's output is insufficient).

Recommended workflow:
1. Run Pandoc to produce a first-pass DOCX.
2. Use Claude to design a `reference.docx` template and refine the DOCX manually.
3. Save the final `reference.docx` back into `build files/` so future Pandoc runs reuse it.

This gives the best of both worlds: Pandoc for repeatability, Claude for creative design.

## Designing the reference DOCX (Claude-assisted)

The reference DOCX is a one-time design investment. After it is styled, every future run of `build_manual.ps1` or `build_manual.bat` will apply those styles automatically.

1. Read `DESIGN_BRIEF.md` for the agreed design goals, typography, and page layout.
2. Open `build files/sample_styles.docx` in Microsoft Word. It contains one example of every Markdown element the manual uses.
3. Apply styles in Word: Normal, Heading 1, Heading 2, Heading 3, Code, Source Code, Table, Caption, etc.
4. Add headers, footers, page margins, and a cover page if desired.
5. Save the styled document as `build files/reference.docx`.
6. Run `build_manual.bat -Export docx` and review the generated DOCX.
7. Refine `reference.docx` and repeat until the output is production-ready.

Claude helps by drafting the design brief, proposing typography and color choices, and debugging Pandoc behavior. The actual styling must be done inside Word because the reference template is a binary Office document.

## Generated artifacts

After running `build_manual.ps1 -Export all`, the following files are produced in `Manual/`:

- `OpenRA_Knowledge_Base_Manual.md` � the assembled Markdown manual (always regenerated).
- `OpenRA_Knowledge_Base_Manual.docx` � Word export for editing/template design.
- `OpenRA_Knowledge_Base_Manual.pdf` � PDF export for distribution.

The first production run produced a 5.8 MB DOCX and a 4.7 MB PDF with all 681 SVG diagrams and 380 actor sprites embedded. Some older `rsvg-convert` versions emit CSS parsing warnings for Mermaid-generated SVGs, but the output is still usable; upgrading to a newer `rsvg-convert` will reduce warning noise.

## Re-generating after future OpenRA updates

1. Update the pinned engine tag in `Part_00_Foundations.md` and `assemble_manual.py` if necessary.
2. Edit the relevant source files.
3. Run `build_manual.ps1`.
4. Re-apply the reference template (Pandoc will use `reference.docx` automatically if present).

## Pandoc vs Claude: detailed breakdown

The pipeline intentionally separates two distinct jobs:

- **Pandoc** is the mechanical converter.
- **Claude** is the design assistant.
- **Pandoc** runs every time the manual changes.
- **Claude** refines the template once, then Pandoc reuses it forever.

### Pandoc in detail

Pandoc is a free, open-source universal document converter. It reads Markdown and writes DOCX, PDF, EPUB, HTML, and many other formats. For this manual it is the right tool because:

- **It preserves structure:** headings, tables, fenced code blocks, images, footnotes, and internal links all survive the conversion.
- **It is deterministic:** the same Markdown input produces the same output every time.
- **It is scriptable:** `build_manual.ps1` can call Pandoc automatically after verification.
- **It is free and portable:** Pandoc is available on Windows, macOS, and Linux under the GPL license, so contributors can reproduce the build on any platform.
- **It supports custom templates:** DOCX styling can be controlled with a `reference.docx` template; PDF output can use a LaTeX template or variables.

For PDF output Pandoc needs a LaTeX engine (we recommend `xelatex` for Unicode support). On Windows the easiest engine to install is **MiKTeX**; on Linux/macOS **TeX Live** is common.

For SVG image conversion Pandoc also needs `rsvg-convert`. This repository bundles a Windows copy of `rsvg-convert` in `build files/tools/rsvg-convert/`, so `build_manual.ps1` works out-of-the-box on Windows. On other platforms, install `rsvg-convert` via your package manager (e.g., `brew install librsvg` on macOS, `apt-get install librsvg2-bin` on Debian/Ubuntu).

### Claude in detail

Claude is a large language model. It is not a document converter, but it is an excellent partner for the design layer because it can reason about readability, layout, and pedagogy. In this workflow Claude is useful for:

- **Reference-template design:** "Create a Word reference template with serif body text, sans-serif headings, shaded code blocks, and a page size/layout suitable for a 1.4 MB technical manual."
- **Layout judgment:** "This table breaks awkwardly across pages. Should we rotate it, shrink the font, or split it into two tables?"
- **Diagram polish:** "Redesign this Mermaid SVG so the labels are readable at print size."
- **Export troubleshooting:** "Pandoc is floating all images away from their sections. How do we fix that with a LaTeX preamble or reference template?"
- **One-time cleanup:** after the first Pandoc export, Claude can fix the remaining visual issues and save the result as the reusable template.

Claude is not a replacement for Pandoc because it cannot reliably run the same mechanical conversion 100 times in a CI/CD pipeline. It is a complement: Pandoc handles repetition, Claude handles the creative decisions that require judgment.

### Why this split matters for sustainability

If every manual update required a human/AI design pass, the project would become fragile. By separating the two layers:

- A future contributor can edit a Markdown source file, run `build_manual.ps1`, and get a new DOCX/PDF without needing design expertise.
- A maintainer can regenerate the manual for a new OpenRA release without redoing the layout from scratch.
- The design investment is preserved in the `reference.docx` template, not lost in a one-off manual edit.

## Installing dependencies

### Pandoc (required for DOCX and PDF)

Download and install from https://pandoc.org/installing.html. The default installer adds Pandoc to the system PATH. If you installed it to a custom location, `build_manual.ps1` also checks the common Windows paths `C:\Program Files\Pandoc\pandoc.exe` and the Chocolatey bin directory.

### LaTeX engine (required for PDF only)

On Windows, install **MiKTeX** from https://miktex.org/download. The basic installer is sufficient; Pandoc will prompt MiKTeX to download any missing LaTeX packages on the first PDF run. Alternatively, install **TeX Live** for a complete offline system.

After installation, verify that `xelatex` or `lualatex` is on your PATH:

```powershell
xelatex --version
```

## Licensing note

The manual text, scripts, and original diagrams are released under the UNLICENSE in the project root. Game assets referenced or rendered in the manual belong to their respective owners and are not licensed here.
