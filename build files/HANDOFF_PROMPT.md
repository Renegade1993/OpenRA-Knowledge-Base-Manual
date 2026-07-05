# Handoff Prompt — OpenRA Knowledge Base Manual Visual Polish

> Copy this prompt into a new Claude session. The project is the OpenRA Knowledge Base Manual under `C:\Users\Kmoney\Documents\AI Projects\Cameo Work\Game Sources and Development Reference Materials\OpenRA Manual`.

## What we already did (so you don't redo it)

- Tiberian Sun units were moved from Appendix K (Environmental Actors) into Appendix I (Actor Reference), where they sit alongside the RA/CNC/D2K tables.
- Unit/environmental previews were bumped from 64 px to 128 px, and I just applied a further bump to **192 px** for actor unit sprites (`build files/rescale_actor_unit_images.py` `MIN_SIZE = 192`).
- TS aircraft and voxel vehicles fall back to the custom `--export-voxel-frame` utility command when no `@unit` SHP sequence exists.
- The full pipeline was run and the PDF rebuilt successfully: `OpenRA_Knowledge_Base_Manual.pdf` is 1,293 pages / ~28.7 MB.
- Verification passes: `assemble_manual.py` (58 chapters, 2,165,685 bytes), `verify_paths.py` (275 paths, 0 missing), `verify_internal_links.py` (6,332 links, 0 broken).

## Remaining issues the user spotted (priority order)

1. **Appendix I tables creep off the right edge of landscape pages.**
   - The actor-reference table is very wide: `| Cameo | Unit | Code | Name | Faction | Cost | HP | Armor | Speed | Sight | Weapon(s) | Notable traits |`.
   - With 192 px images, the `Cameo` and `Unit` columns push the text columns off the page.
   - This is most prevalent in the unit and building sections.

2. **Dune 2000 unit/building tables are a layout mess.**
   - Some columns are too narrow, others too loose.
   - Rows are too tall because narrow columns force text to wrap vertically.
   - Some columns overlap visually.

3. **Tiberian Dawn supply truck cameo has artifacting.**
   - Actor code is `TRUCK` (CNC mod). Other CNC icons use `*.icnh.tem` filenames; the truck uses `truckicon.shp`.
   - Current extraction forces the `chrome` palette for all CNC icons. This is likely the wrong palette for the truck's SHP.

4. **Tiberian Sun units look twisted ~90 degrees out.**
   - Applies to both SHP-based infantry/vehicles and voxel aircraft/vehicles.
   - For SHP units, `ExportSequenceFrameCommand` picks a forward-facing frame index (`facings/2`). TS may need a different facing index or a different convention.
   - For voxel units, the custom `ExportVoxelFrameCommand` uses a fixed 45-degree yaw. The orthographic projection angle may not match TS's in-game sprite orientation.

5. **`house01.tem` (TS environmental actor) looks wrong.**
   - Likely a palette or sequence issue in the TS environmental extraction.

6. **General visual sweep needed.**
   - The user wants a full pass over the PDF to catch any other sprite/rotation/palette/table issues.

## Key files you will touch

- `build files/generate_actor_reference.py` — defines the Appendix I table columns and actor ordering.
- `build files/extract_cameos.ps1` — renders cameos and unit sprites; controls palette and tileset choices.
- `build files/rescale_actor_unit_images.py` — actor unit image upscaling.
- `build files/rescale_environmental_images.py` — environmental image upscaling.
- `OpenRA GitHub Repositories/OpenRA/OpenRA.Mods.Common/UtilityCommands/ExportSequenceFrameCommand.cs` — SHP frame extraction (facing selection, palette handling, compositing).
- `OpenRA GitHub Repositories/OpenRA/OpenRA.Mods.Cnc/UtilityCommands/ExportVoxelFrameCommand.cs` — voxel orthographic renderer.
- `build files/format_tables_vlines.py` — post-processes LaTeX longtables and landscape headers.
- `build files/header.tex` — LaTeX preamble for PDF.
- `build files/appendices/Appendix_I_Actor_Reference.md` — generated; regenerate from `generate_actor_reference.py`.
- `OpenRA_Knowledge_Base_Manual.pdf` — final output to inspect.

## Suggested approach

### Table layout (issues 1 & 2)

Consider one or more of these, then rebuild and inspect the PDF:

- Combine `Cameo` and `Unit` into a single `Preview` column with both images stacked vertically, reducing the table width by one image column.
- Drop the least-critical columns (e.g., `Sight`, `Armor`, `Weapon(s)`) or move them to sub-tables per category.
- Reduce the image display size in Markdown while keeping the rescale target at 192 px (e.g., `![name](path){width=1.2in}` or a Pandoc-compatible attribute).
- Tighten the LaTeX `longtable` column spec in the generated Markdown or via a post-processing script, especially for the D2K tables where building names with `.ordos` suffixes cause uneven wrapping.
- Ensure `format_tables_vlines.py` does not create `p{}` columns that are too narrow for the D2K actor names.

### TRUCK cameo artifacting (issue 3)

- The TRUCK icon sequence is `truckicon.shp` instead of `*.icnh.tem`. In `extract_cameos.ps1`, test whether the truck cameo renders correctly with `temperat`, `sidebar`, or `chrome` palette.
- A minimal fix is to special-case `truck` in the icon loop and use the palette that produces a clean output, or to stop forcing `chrome` and let the sequence's own `Palette` key drive the icon (this is what `ExportSequenceFrameCommand` does when no palette is passed).

### TS unit rotation (issue 4)

- For SHP units, inspect `ExportSequenceFrameCommand.ResolveFirstFrameIndex`. The forward-facing formula `(facings / 2) * length` may not align with TS's 8-facing layout. Try offsets 0, 2, 6, or 7 and compare visually.
- For voxel units, inspect `ExportVoxelFrameCommand.Render`. The yaw is `(Math.PI / 4)` (45°). Try 0, 90°, 135°, or 180° and compare to the in-game TS sprite orientation. The pitch may also need adjustment.
- Regenerate the affected TS actor unit images after any code change and run the rescale script.

### house01.tem (issue 5)

- Look at `build files/extract_environmental_images.py` and the TS environmental extraction path for `house01.tem`. Check the chosen sequence, palette, and tileset. The actor is likely a temperate-specific civilian building with a non-default palette.

### Visual sweep (issue 6)

- After fixes, run the full pipeline:
  1. `build files/generate_actor_reference.py`
  2. `build files/generate_environmental_actor_reference.py`
  3. `build files/extract_cameos.ps1` (from the OpenRA engine source root)
  4. `build files/extract_environmental_images.py`
  5. `build files/rescale_actor_unit_images.py`
  6. `build files/rescale_environmental_images.py` (if changed)
  7. `build files/build_manual.ps1 -Export pdf`
- Verify with `verify_paths.py` and `verify_internal_links.py`.
- Open the PDF and visually inspect at least one page per mod/section: RA units, CNC units, D2K units, TS units, RA buildings, CNC buildings, D2K buildings, TS buildings, TS environmental actors.

## Constraints and rules

- Never delete files directly. Move unwanted/backup files to `C:\Users\Kmoney\Documents\AI Projects\Cameo Work\to delete\`.
- Always update `Manual/DEVELOPMENT_LOG.md` with what you tried and what changed.
- Do not push to Git unless explicitly asked.
- Keep the engine build intact (`OpenRA GitHub Repositories\OpenRA\bin\OpenRA.Utility.exe` is required for extraction).

## Deliverables

- A rebuilt `OpenRA_Knowledge_Base_Manual.pdf` that the user can visually inspect.
- A summary of which issues were fixed and which remain, with any open questions.
