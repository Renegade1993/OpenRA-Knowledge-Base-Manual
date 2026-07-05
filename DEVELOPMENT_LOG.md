# OpenRA Knowledge Base Manual — Development Log

- **QA/QC and GitHub prep:** verified the full pipeline after restructuring by running `build files/build_manual.ps1 -Export pdf`; output is 1,369 pages / 39.6 MB with 0 broken paths and 0 broken internal links. Added `.gitignore` for generated LaTeX intermediates and `__pycache__`; moved `*.aux`, `*.log`, `*.toc`, `*.tex` and `__pycache__` directories to `to delete`.
- **Restructured project root:** removed the `Manual/` subdirectory layer and moved all contents up to `OpenRA Manual/`. Updated hardcoded paths in 21 scripts and documentation files (absolute paths, relative `Manual/images/`, `Manual/build files/`, `Manual/OpenRA_Knowledge_Base_Manual` references). Skipped `Archive/` and `build files/Critical Feedback/`.
- **Bundled `rsvg-convert`** for Windows in `build files/tools/rsvg-convert/` so SVG diagrams can be converted for PDF/DOCX export without a system-wide install.
- **Generated first exports:** `OpenRA_Knowledge_Base_Manual.docx` (5.8 MB) and `OpenRA_Knowledge_Base_Manual.pdf` (4.7 MB) with all 681 SVG diagrams and 380 actor sprites embedded.


## 2026-07-03 — Round 18: Replace CnC supply truck cameo with RA TRUK icon

### What was done
- Replaced the CnC supply truck cameo with the already-extracted RA `TRUK` icon by copying `images/actors/ra/truk.png` to `images/actors/cnc/truck.png`.
- Moved the previous CnC truck cameo (black-background version) to `to delete\truck_black.png`.
- Regenerated the PDF.

### Files changed
- `C:/Users/Kmoney/Documents/AI Projects/Cameo Work/Game Sources and Development Reference Materials/OpenRA Manual/images/actors/cnc/truck.png` (copied from RA `truk.png`)

### Result
- `build_manual.ps1 -Export pdf` completes; output is 1,369 pages / 39.6 MB.
- Verification checks pass: 275 source paths, 6,332 internal links.
- CnC truck cameo now shows the clean RA TRUK truck.

## 2026-07-03 — Round 17: Revert supply truck cameo to black background

### What was done
- Reverted the CnC supply-truck cameo handling in `build files/rescale_actor_unit_images.py` from transparent background/fringes back to the Round 15/Round 16 black-background approach: grayscale background palette entries and near-white fringes are replaced with opaque black.
- Re-extracted the truck icon and regenerated the PDF.

### Files changed
- `C:/Users/Kmoney/Documents/AI Projects/Cameo Work/Game Sources and Development Reference Materials/OpenRA Manual/build files/rescale_actor_unit_images.py`

### Result
- `build_manual.ps1 -Export pdf` completes; output is 1,369 pages / 39.6 MB.
- Verification checks pass: 275 source paths, 6,332 internal links.
- CnC truck cameo is back to the Round 15/Round 16 black-background state (0 near-white pixels, ~1,594 black background pixels).

## 2026-07-02 — Round 16: Supply truck / EMP cannon / D2K turret fixes

### What was done
- Reworked the CnC supply-truck cameo fix in `build files/rescale_actor_unit_images.py` so that the grayscale background palette entries are made transparent instead of replaced with opaque black. Resampling fringes are also set to transparent instead of black.
- Generalised the turret-offset logic in `OpenRA.Mods.Common/UtilityCommands/ExportSequenceFrameCommand.cs` to compare the base and turret sequence filenames. Native turrets (same actor/family, e.g. NAPULS, GDI tower upgrades, D2K turrets) keep their inherited offset; borrowed turrets (e.g. NASAM using GACTWR SAM) still have the body offset removed.
- Added `SequenceFilename` and `IsNativeTurret` helpers.
- Rebuilt the engine, re-extracted all cameos, and regenerated the PDF.
- Verified the RA ant cameos (`Ant`, `FireAnt`, `ScoutAnt`) are all ant-shaped as expected for giant ant variants.

### Files changed
- `C:/Users/Kmoney/Documents/AI Projects/Cameo Work/Game Sources and Development Reference Materials/OpenRA GitHub Repositories/OpenRA/OpenRA.Mods.Common/UtilityCommands/ExportSequenceFrameCommand.cs`
- `C:/Users/Kmoney/Documents/AI Projects/Cameo Work/Game Sources and Development Reference Materials/OpenRA Manual/build files/rescale_actor_unit_images.py`

### Result
- Engine builds with 0 warnings, 0 errors.
- `extract_cameos.ps1` completes for all four mods (RA 90, CnC 54, D2K 45, TS 80).
- `build_manual.ps1 -Export pdf` completes; output is 1,369 pages / 39.6 MB.
- Verification checks pass: 275 source paths, 6,332 internal links.
- CnC truck cameo has 0 black pixels and 0 near-white pixels; the body is visible again.
- TS NAPULS turret is now aligned with its base.
- D2K `medium_gun_turret` and `large_gun_turret` unit images now show their turret tops.
- GDI tower upgrades and NASAM remain aligned.

## 2026-07-02 — Round 15: Component tower / tower turret alignment / D2K destroyable tile colors

### What was done
- Removed `gactwr` from `TowerUpgradeOverrides` in `OpenRA.Mods.Common/UtilityCommands/ExportSequenceFrameCommand.cs`; the base Component Tower has no turret and should match the Vulcan tower base without its turret.
- Restricted the turret-offset compensation to non-native turrets: tower upgrades keep the inherited `Defaults` offset so their turret sits on the socket, while borrowed turrets like NASAM's still have the body offset removed.
- Fixed `ToRgbaImage` in `OpenRA.Mods.Common/UtilityCommands/ExportSequenceFrameCommand.cs` to respect the source `SpriteFrameType` (BGRA vs RGBA). The old assumption of BGRA swapped red and blue for truecolor PNGs such as the D2K `pass01` destroyable tiles.
- Re-extracted all environmental images with `--force`, re-extracted all cameos, and regenerated the PDF.

### Files changed
- `C:/Users/Kmoney/Documents/AI Projects/Cameo Work/Game Sources and Development Reference Materials/OpenRA GitHub Repositories/OpenRA/OpenRA.Mods.Common/UtilityCommands/ExportSequenceFrameCommand.cs`

### Result
- Engine builds with 0 warnings, 0 errors.
- `extract_environmental_images.py --force` completes; D2K `pass01` tiles are now brown/earthy instead of purple/blue.
- `extract_cameos.ps1` completes for all four mods (RA 90, CnC 54, D2K 45, TS 80).
- `build_manual.ps1 -Export pdf` completes; output is 1,369 pages / 39.6 MB.
- Verification checks pass: 275 source paths, 6,332 internal links.
- TS GACTWR no longer has a turret; GAVULC/GAROCK/GACSAM turrets sit on their tower bases; NASAM remains aligned.

## 2026-07-02 — Round 14: TS laser turret / Nod SAM / supply truck cleanup

### What was done
- Updated `build files/rescale_actor_unit_images.py` to remove low-saturation dark-grey anti-aliasing fringes from the CnC supply truck after the palette-based background cleanup.
- Changed `OpenRA.Mods.Cnc/UtilityCommands/ExportVoxelFrameCommand.cs` to require the body voxel (`LoadModel(..., required: true)`). This forces TS NALASR to fall back to its SHP `idle` sequence when `nalasr.vxl` is missing, restoring the full laser turret body.
- Added `gactwr` to `TowerUpgradeOverrides` in `OpenRA.Mods.Common/UtilityCommands/ExportSequenceFrameCommand.cs` so the base GDI Component Tower renders its `turret-vulcan` overlay.
- Added per-layer sequence-offset compositing in `OpenRA.Mods.Common/UtilityCommands/ExportSequenceFrameCommand.cs`: `TryGetFrame` now returns the parsed `Offset` from the sequence/Defaults node, and `CompositeImages` adds it to the raw frame offset.
- For turret overlays, subtract the body's sequence offset so the turret anchors to the body's frame origin instead of floating due to inherited `Defaults` offsets. This fixes NASAM and keeps GDI tower upgrades aligned.
- Rebuilt the engine, re-extracted all cameos (RA 90, CnC 54, D2K 45, TS 80), re-ran rescale, and regenerated the PDF.

### Files changed
- `C:/Users/Kmoney/Documents/AI Projects/Cameo Work/Game Sources and Development Reference Materials/OpenRA GitHub Repositories/OpenRA/OpenRA.Mods.Cnc/UtilityCommands/ExportVoxelFrameCommand.cs`
- `C:/Users/Kmoney/Documents/AI Projects/Cameo Work/Game Sources and Development Reference Materials/OpenRA GitHub Repositories/OpenRA/OpenRA.Mods.Common/UtilityCommands/ExportSequenceFrameCommand.cs`
- `C:/Users/Kmoney/Documents/AI Projects/Cameo Work/Game Sources and Development Reference Materials/OpenRA Manual/build files/rescale_actor_unit_images.py`

### Result
- Engine builds with 0 warnings, 0 errors.
- `extract_cameos.ps1` completes for all four mods.
- `build_manual.ps1 -Export pdf` completes; output is 1,372 pages / 39.4 MB.
- Verification checks pass: 275 source paths, 6,332 internal links.
- CnC truck has 0 near-white pixels; remaining dark-grey fringes are removed.
- TS NALASR unit image now shows the full laser turret body and barrel.
- TS NASAM turret now sits on the SAM base instead of floating above it.
- TS GACTWR/GAVULC/GAROCK/GACSAM tower turrets are drawn on their bodies.

## 2026-07-03 — Round 13: Roll back cameo background processing

### What was done
- Removed the `fill_icon_background_black()` and `fix_truck_icon()` functions from `rescale_actor_unit_images.py` and restored `normalize_icon()` to its pre-Chinook-fix state (simple crop + resize only).
- Re-extracted all cameos and re-ran rescale so the icons are back to the original exported palette/background state from before the truck/Chinook cameo changes.
- Regenerated the PDF.

### Files changed
- `build files/rescale_actor_unit_images.py`
- `OpenRA_Knowledge_Base_Manual.pdf`
- `Manual/DEVELOPMENT_LOG.md` (this entry)

### Verification
- `py rescale_actor_unit_images.py` completes: 192 units rescaled, 272 icons normalized.
- `build_manual.ps1 -Export pdf` completes; final PDF: 1,372 pages, 37.65 MB. The `lualatex` exit code 1 is the recurring MiKTeX update-nag, not a build failure.

### Known limitations / next steps
- The Chinook battlefield sprite remains fixed with the asymmetric rotor placement from Round 11.
- The TD supply truck will again show its original exported background (pre-Chinook state).
- D2K building foundations (bibs) still render only the first concrete tile.

## 2026-07-03 — Round 12: Fix icon background regression

### What was done
- Reverted the broad `remove_light_background` step in `rescale_actor_unit_images.py` that was repainting bright pixels on every cameo; it was destroying RA aircraft, D2K defense structures, and other icons that have light-coloured artwork.
- Replaced it with a targeted approach:
  - `fill_icon_background_black()`: flood-fills from the icon corners to make the connected background black, then fills any remaining transparent pixels with black. This applies to all cameos and restores the black sidebar look without touching the icon content.
  - `fix_truck_icon()`: the CNC supply truck is a special indexed-SHP case with a mottled grey/white background, so it still gets the palette-based background replacement.
- Re-extracted all cameos, re-ran rescale, and regenerated the PDF.

### Files changed
- `build files/rescale_actor_unit_images.py`
- `OpenRA_Knowledge_Base_Manual.pdf`
- `Manual/DEVELOPMENT_LOG.md` (this entry)

### Verification
- `py rescale_actor_unit_images.py` completes: 0 unit rescaled, 272 icons normalized.
- `build_manual.ps1 -Export pdf` completes; final PDF: 1,372 pages, 34.08 MB. The `lualatex` exit code 1 is the recurring MiKTeX update-nag, not a build failure.

### Known limitations / next steps
- The Chinook battlefield sprite remains correct with the asymmetric rotor placement from Round 11.
- D2K building foundations (bibs) still render only the first concrete tile; the full multi-tile foundation grid is not yet composited.
- A few remaining LaTeX "Underfull \hbox" and font-shape warnings are cosmetic.

## 2026-07-03 — Round 11: Final Chinook rotor placement

### What was done
- Replaced the single rotor projection scale with a per-axis/asymmetric setup:
  - X scale = 0, so the rotors stay horizontally centered on the fuselage.
  - Z scale = 0, so the rotor height above the ground is ignored for the preview.
  - Front rotor Y scale = 9/1024 and rear rotor Y scale = 25/1024, placing the front blade at the bottom of the fuselage and the rear blade at the top while keeping the hub centered.
- This addresses the feedback that the two blades were too close vertically and the rear rotor was slightly offset; the rear rotor is now scooted back about 10 pixels and mirrors the front rotor.
- Rebuilt the engine, re-extracted all cameos, re-ran rescale, and regenerated the PDF.

### Files changed
- `OpenRA GitHub Repositories/OpenRA/OpenRA.Mods.Common/UtilityCommands/ExportSequenceFrameCommand.cs`
- `OpenRA_Knowledge_Base_Manual.pdf`
- `Manual/DEVELOPMENT_LOG.md` (this entry)

### Verification
- `dotnet build --configuration Release --no-restore` succeeds with 0 warnings, 0 errors.
- `extract_cameos.ps1` completes with all expected icons/units; only D2K `deathhand`, `concretea`, `concreteb` remain missing.
- `build_manual.ps1 -Export pdf` completes; final PDF: 1,372 pages, 37.39 MB. The `lualatex` exit code 1 is the recurring MiKTeX update-nag, not a build failure.

### Known limitations / next steps
- D2K building foundations (bibs) still render only the first concrete tile; the full multi-tile foundation grid is not yet composited.
- A few remaining LaTeX "Underfull \hbox" and font-shape warnings are cosmetic.

## 2026-07-03 — Round 10: Iterative feedback — rotor offset and truck background

### What was done
- Moved the Chinook/transport-helicopter rotors inward again: projection scale reduced from 10/1024 to 3/1024 world-units per pixel. The rotor tips now sit much closer to the body center.
- Fixed the TD supply truck cameo by repainting the detected light background to opaque black instead of making it transparent. The previous fix left the truck floating on the white PDF page; matching the other CNC cameos' black field eliminates the perceived white halo/artifacting.
- Rebuilt the engine, re-extracted all cameos, re-ran rescale, and regenerated the PDF.

### Files changed
- `OpenRA GitHub Repositories/OpenRA/OpenRA.Mods.Common/UtilityCommands/ExportSequenceFrameCommand.cs`
- `build files/rescale_actor_unit_images.py`
- `OpenRA_Knowledge_Base_Manual.pdf`
- `Manual/DEVELOPMENT_LOG.md` (this entry)

### Verification
- `dotnet build --configuration Release --no-restore` succeeds with 0 warnings, 0 errors.
- `extract_cameos.ps1` completes with all expected icons/units; only D2K `deathhand`, `concretea`, `concreteb` remain missing.
- `build_manual.ps1 -Export pdf` completes; final PDF: 1,372 pages, 37.39 MB. The `lualatex` exit code 1 is the recurring MiKTeX update-nag, not a build failure.

### Known limitations / next steps
- D2K building foundations (bibs) still render only the first concrete tile; the full multi-tile foundation grid is not yet composited.
- A few remaining LaTeX "Underfull \hbox" and font-shape warnings are cosmetic.

## 2026-07-03 — Round 9: Further feedback — Chinook rotor offset, D2K stretch, fake cameos, TD truck halo

### What was done
- Reduced Chinook/transport-helicopter rotor projection scale again from 18/1024 to 10/1024 world-units per pixel. The rotors are now offset by roughly one-third of the body width instead of two-thirds.
- Widened the D2K battlefield preview column in the actor tables from 0.25\linewidth to 0.33\linewidth, giving D2K buildings the ~33% horizontal stretch they needed after the concrete-tile removal.
- Replaced RA fake-building cameos with the real building's `icon` sequence. The in-game `fake-icon` SHPs are lower-quality recolours; the real cameo is what the fake building is meant to impersonate, so the manual now renders the higher-quality asset.
- Removed the opaque white halo from the TD supply truck cameo. `rescale_actor_unit_images.py` now detects icons whose dominant opaque colour is near-white and makes those pixels transparent before normalising, so the Lanczos downsample no longer leaves grey/white fringing around the truck.
- Rebuilt the engine, re-extracted all cameos, re-ran rescale, and regenerated the PDF.

### Files changed
- `OpenRA GitHub Repositories/OpenRA/OpenRA.Mods.Common/UtilityCommands/ExportSequenceFrameCommand.cs`
- `build files/format_tables_vlines.py`
- `build files/extract_cameos.ps1`
- `build files/rescale_actor_unit_images.py`
- `OpenRA_Knowledge_Base_Manual.pdf`
- `Manual/DEVELOPMENT_LOG.md` (this entry)

### Verification
- `dotnet build --configuration Release --no-restore` succeeds with 0 warnings, 0 errors.
- `extract_cameos.ps1` completes with all expected icons/units; only D2K `deathhand`, `concretea`, `concreteb` remain missing.
- `build_manual.ps1 -Export pdf` completes; final PDF: 1,372 pages, 37.66 MB. The `lualatex` exit code 1 is the recurring MiKTeX update-nag, not a build failure.

### Known limitations / next steps
- D2K building foundations (bibs) still render only the first concrete tile; the full multi-tile foundation grid is not yet composited.
- A few remaining LaTeX "Underfull \hbox" and font-shape warnings are cosmetic.

## 2026-07-03 — Round 8: Feedback fixes — cameo scaling, Chinook rotors, D2K buildings, RA war factory

### What was done
- Replaced the low-resolution Tiberian Sun logo in the PDF with a higher-quality transparent PNG.
- Fixed RA/TD Chinook rotors appearing far outside the body. Reduced the empirical rotor projection scale from 24/1024 to 18/1024 world-units per pixel, so the rotors sit at the front/rear of the small helicopter sprite instead of floating beyond it.
- Stopped the RA war factory (`WEAP`) from showing the damaged roof: removed `damaged-build-top` from the auto-composited overlay list; only the normal `build-top` roof is drawn.
- Fixed D2K building previews shrinking to ~1/4 size because the concrete bib/foundation tile was being counted as part of the bounding box. `rescale_actor_unit_images.py` now keeps only the largest connected component of non-transparent pixels, removing the separate bottom-left tile before cropping/upscaling.
- Removed the D2K-wide padding workaround that was adding empty canvas around D2K units; the `keep_largest_component` + `crop_to_bounds` pass already centres the visible sprite, so the extra padding was only making vehicles like the `quad` look small.
- Improved cameo quality and file size: icons are now normalized to 96 px tall with Lanczos resampling. The raw 256×192 `.icnh.tem` canvases are downsampled back to 96 px height, which is much smoother than the previous nearest-neighbour upscaling and keeps the PDF smaller.
- Rebuilt the OpenRA engine, re-extracted all cameos (RA 90, CnC 54, D2K 45, TS 80), re-ran rescale, and regenerated the PDF.

### Files changed
- `OpenRA GitHub Repositories/OpenRA/OpenRA.Mods.Common/UtilityCommands/ExportSequenceFrameCommand.cs`
- `build files/rescale_actor_unit_images.py`
- `Manual/images/actors/*/logo.png` (TS logo replacement)
- `OpenRA_Knowledge_Base_Manual.pdf`
- `Manual/DEVELOPMENT_LOG.md` (this entry)

### Verification
- `dotnet build --configuration Release --no-restore` succeeds with 0 warnings, 0 errors.
- `extract_cameos.ps1` completes with all expected icons/units; only D2K `deathhand`, `concretea`, `concreteb` remain missing (no in-world sprites).
- `build_manual.ps1 -Export pdf` completes; final PDF: 1,372 pages, 37.28 MB. The `lualatex` exit code 1 is the recurring MiKTeX update-nag, not a build failure.

### Known limitations / next steps
- D2K building foundations (bibs) still render only the first concrete tile; the full multi-tile foundation grid is not yet composited. The tile-removal pass fixes the scaling, but some buildings may still look like they are missing their slab.
- D2K destructible terrain previews still need investigation.
- A few remaining LaTeX "Underfull \hbox" and font-shape warnings are cosmetic.

## 2026-07-03 — Round 7: Visual discrepancy fixes for units and structures

### What was done
- Fixed battlefield-sprite compositing so that sprites are no longer clipped to their `FrameSize` canvas. The exporter now composites using the actual image bounds (`Size + Offset`), which restores:
  - D2K building previews (e.g. `refinery.ordos`) that were previously only showing the bottom ~1/4 of the sprite.
  - TS building roofs/towers (e.g. GDI weapons factory `gaweap`) that were missing the top 1/3.
  - TD Nod laser turret (`obli`) active animation / top piece.
- Added RA war factory `build-top` / `damaged-build-top` overlays to the auto-composited overlay list so the factory roof is visible.
- Fixed RA/TD Chinook rotor placement: `rotor` / `rotor2` overlays for `tran` now receive the same 3D `WithIdleOverlay` offset projected to screen space, so rotors appear at the front and rear of the body instead of both in the centre.
- Fixed TS Mobile EMP Cannon (`MOBILEMP`) unit render: `--export-voxel-frame` now reads the `idle` model mapping from `voxels.yaml` and loads the correct `m_emp.vxl` body instead of failing on `mobilemp.vxl`.
- Fixed TS Titan (`MMCH`) turret: the sprite turret is now drawn on the walking `stand` body (whitelisted via `SpriteTurretOnStandImages`), so the Titan shows legs and gun together.
- Fixed TS Wolverine (`SMECH`) facing: the forward-facing frame for the Wolverine's 8-facing infantry-style body is now selected at WAngle 384 (the default actor preview facing) instead of 512, which was showing the rear view.
- Adjusted D2K air unit rescaling: `carryall` and `ornithopter` battlefield sprites are now padded to a square before upscaling so they fill the table cell height instead of appearing letter-boxed.
- Rebuilt the engine, re-extracted all cameos (RA 90, CnC 54, D2K 45, TS 80), re-ran rescale, and regenerated the PDF.

### Files changed
- `OpenRA GitHub Repositories/OpenRA/OpenRA.Mods.Common/UtilityCommands/ExportSequenceFrameCommand.cs`
- `OpenRA GitHub Repositories/OpenRA/OpenRA.Mods.Cnc/UtilityCommands/ExportVoxelFrameCommand.cs`
- `build files/rescale_actor_unit_images.py`
- `OpenRA_Knowledge_Base_Manual.pdf`
- `Manual/DEVELOPMENT_LOG.md` (this entry)

### Verification
- `dotnet build --configuration Release --no-restore` succeeds with 0 warnings, 0 errors.
- `extract_cameos.ps1` completes with all expected icons/units; only D2K `deathhand`, `concretea`, `concreteb` are missing (intentional/no in-world sprites) and TS `MOBILEMP` now renders successfully.
- `build_manual.ps1 -Export pdf` completes; final PDF: 1,372 pages, 30.88 MB. The reported `lualatex` exit code 1 is the recurring MiKTeX update-nag, not a build failure.

### Known limitations / next steps
- D2K building foundations (bibs) still render only the first tile of the multi-tile foundation; the full 2×N tile grid is not yet composited. This is the remaining cause of the "building looks incomplete" reports for D2K structures.
- D2K destructible terrain previews still need investigation; the current extraction may not be using the correct sequence or palette.
- CnC supply truck (`TRUCK`) cameo uses `truckicon.shp` with the chrome palette; if the cameo still shows color artifacts, the SHP may need a different palette or manual replacement.
- The remaining LaTeX "Missing character" warnings for a few Unicode characters are cosmetic and non-critical.

## 2026-07-01 — Round 6 follow-up: GDI tower upgrades facing forward

### What was done
- Fixed GDI tower upgrade unit previews (`GAVULC`, `GAROCK`, `GACSAM`) so they no longer show the static `place` ghost frame with the turret facing away from the camera.
- Added `TowerUpgradeOverrides` in `OpenRA.Mods.Common/UtilityCommands/ExportSequenceFrameCommand.cs` to map each upgrade to the `gactwr` base tower body and the correct `turret-vulcan`/`turret-rocket`/`turret-sam` sequence, then choose the forward-facing frame.
- Rebuilt the OpenRA engine, re-extracted all cameos (RA 90, CnC 54, D2K 45, TS 80), and regenerated the PDF.
- Final PDF: 1,372 pages / 29.34 MB. Verification passes: 275 source paths, 6,332 internal links.

### Files changed
- `OpenRA GitHub Repositories/OpenRA/OpenRA.Mods.Common/UtilityCommands/ExportSequenceFrameCommand.cs`
- `Manual/images/actors/ts/gavulc_unit.png`, `garock_unit.png`, `gacsam_unit.png`
- `OpenRA_Knowledge_Base_Manual.pdf`
- `Manual/DEVELOPMENT_LOG.md` (this file)

### Next steps
- Production review of the final PDF.

## 2026-07-03 — Round 5c: Fix Appendix K environmental preview sizes and palettes

### Civilians and TS structures were tiny in Appendix K
- `extract_environmental_images.py` exports full actor frames with large transparent margins, and
  `rescale_environmental_images.py` was upscaling the whole frame to a fixed 128 px. The actual actor
  content for civilians was only ~16×26 px inside the frame, so they looked microscopic in the PDF.
  TS civilian structures like `ABAN01` and `CAARAY` also had lots of empty padding and appeared shrunk.
- **Fix:** `rescale_environmental_images.py` now crops frames that are mostly empty transparent padding
  (content area < 25% of frame) before upscaling, and raises the minimum size from 128 px to 160 px.
  Civilians now fill the preview cell (e.g. RA `c1.png` content 61×124 px, CnC `c1.png` 68×114 px,
  TS `civ1.png` 62×132 px). Small TS structures like `city20.png` are also cropped and enlarged.
- **Fix:** `format_tables_vlines.py` widens the Appendix K Preview column from 0.14 to 0.18 of the
  landscape width and caps image height at 160 pt so tall cropped images do not make rows excessive.

### Destructible terrain / TS structures had wrong (blueish) palette
- `extract_environmental_images.py` was honoring the `RenderSprites` `Palette` field literally, so TS
  civilian structures (`CAARAY`, `CAARMR`, `CAHOSP`, `GAKODK`, etc.) and RA ice/tank traps that
  explicitly set `Palette: player` were rendered with the player-remap palette, giving them a
  blueish or player-colored tint. The fallback for RA/TS with no explicit palette was also `player`.
- **Fix:** Added `is_unit_actor()` and `is_terrain_actor()` helpers. When an actor is not a unit and
  inherits terrain/building templates (`^Tree`, `^Rock`, `^Wall`, `^DestroyableTile`, `^CivBuilding`,
  `^TechBuilding`, `^BasicBuilding`, `^Building`), any `player`/`chrome`/`player-*` palette is now
  overridden to `terrain` (or `d2k` for D2K). This leaves infantry/civilian units on the player palette
  while forcing terrain/building decorations to the tileset terrain palette.
- **Result:** TS `CAARAY` top colors shifted from red/orange player-remap colors to brown/grey terrain
  colors. RA `TANKTRAP1` is now grey instead of potentially blue-tinted. RA/CnC trees, rocks, walls, and
  buildings remain unchanged.

### Re-extracted environmental previews
- Ran `extract_environmental_images.py --force` to regenerate all previews with the corrected palettes
  and sizes, then `rescale_environmental_images.py` to crop/upscale. Final counts: 476 generated,
  5 expected failures (`BRIDGEHUT` RA/CnC, `LOCOMOTIVE`/`TRAINCAR`/`CARGOCAR` TS have no extractable
  sprites). 481 images were rescaled/cropped to at least 160 px on the longest side.

### Files changed
- `build files/extract_environmental_images.py`
- `build files/rescale_environmental_images.py`
- `build files/format_tables_vlines.py`
- `Manual/images/environmental/` (regenerated/cropped/rescaled previews)
- `Manual/DEVELOPMENT_LOG.md` (this entry)

## 2026-07-03 — Round 5b: Recover real actor images + enlarge environmental previews

### Appendix I was showing all placeholders
- The previous `extract_cameos.ps1` run silently failed for all actor images; the directory was left
  with faction-tinted placeholder PNGs that the rescale script upscaled to 192 px, making them look
  like real-but-low-quality art. The extraction failed because the source-engine utility could not
  resolve the mod search paths when `ENGINE_DIR` was not set in the calling shell.
- **Fix:** Re-ran `extract_cameos.ps1` from the pinned engine root with `ENGINE_DIR` explicitly
  inherited by the script. All 269 actors were re-extracted successfully (only the expected
  `GAVULC`, `GAROCK`, `GACSAM`, `MOBILEMP` TS actors kept `unit:--` placeholders because they have
  no world sprite/voxel). Unit images are now real again with proper transparency (e.g. RA
  `e1_unit.png` 192×192, 1,077 opaque pixels; TS `bggy_unit.png` 192×192, 22,929 opaque pixels).

### Appendix K environmental previews were tiny
- The environmental-actor table capped its Preview images at `height=60pt`, leaving them small
  relative to the column.
- **Fix:** `format_tables_vlines.py` `limit_environmental_image` now emits `width=\linewidth` so the
  civilian/terrain/object previews fill the existing Preview column.

### Rebuilt PDF
- Re-ran `build_manual.ps1 -Export pdf`.
- Verification: 1,318 pages, 30.0 MB, no fatal LaTeX errors.
- The `lualatex` exit code 1 is the recurring MiKTeX update-nag, not a build failure.

## 2026-07-03 — Round 5: Preview image sizing + voxel renderer rewrite

### Preview images were microscopic
- The actor `Preview` column images were capped at `height=48pt` and then shrunk further to fit the
  column, leaving large white margins. The column width itself was fine.
- **Fix:** `build files/format_tables_vlines.py` `limit_actor_image` now emits
  `width=\linewidth` (instead of `height=48pt`) so the stacked cameo and unit sprite fill the full
  width of the existing Preview column. Column widths (`actor_widths`) were left unchanged.

### TS voxel units: still mis-rotated + "shutter"/comb striping
- **Root cause 1 (rotation):** `ExportVoxelFrameCommand.Render` treated **Y as the up-axis**, but
  Westwood voxels use **Z as up** (X/Y are the ground plane). This laid the models flat and made them
  look rotated ~90°, which no yaw tweak (45°/135°) could correct. Rewrote the projection so YAW
  rotates about the vertical Z axis and PITCH tilts the camera down (height rises up the screen).
  Now uses yaw 45° / pitch 30°.
- **Root cause 2 (striping):** each voxel was plotted as a single pixel; when the small model is
  scaled up to fill the frame, gaps appear between samples → comb/shutter striping. **Fix:** each
  voxel is now splatted as a filled `ceil(scale) × ceil(scale)` block. Also bumped the internal
  render size from 64 px to 192 px for a sharper result.
- **Verification:** re-rendered voxels (BGGY, TTNK, MCV, APC, ORCA) all report `empty_interior_cols=0`
  — the striping is gone. TTNK is still small because only its chassis VXL is composited (turret and
  barrel are separate VXL files — pre-existing limitation).
- Rebuilt `OpenRA.Mods.Cnc.dll` (0 warnings, 0 errors), re-ran `extract_cameos.ps1` (234 unit images
  rescaled), regenerated Appendix I, and rebuilt the PDF (1,311 pages, ~29 MB).

### Files changed
- `build files/format_tables_vlines.py`
- `OpenRA GitHub Repositories\OpenRA\OpenRA.Mods.Cnc\UtilityCommands\ExportVoxelFrameCommand.cs`
- `Manual/images/actors/*/*_unit.png` (regenerated)
- `OpenRA_Knowledge_Base_Manual.pdf` (regenerated)

## 2026-07-03 — Round 4: Visual polish fixes (TS rotation, table layout, TRUCK cameo)

### Table layout fixes (Appendix I / D2K)

- **Combined `Cameo` and `Unit` into a single `Preview` column.**
  - Updated `build files/generate_actor_reference.py` to emit one stacked image pair
    (`cameo` above `unit`) in the Markdown source.
  - Added a LaTeX post-processing step in `build files/format_tables_vlines.py` to insert
    `\par` between the two actor images so they stack vertically in the PDF.
- **Rebalanced column widths for the actor reference tables.**
  - `format_tables_vlines.py` `actor_widths` adjusted to `[0.08, 0.09, 0.13, 0.07, 0.05, 0.05, 0.06, 0.05, 0.05, 0.09, 0.14]`
    (Preview, Code, Name, Faction, Cost, HP, Armor, Speed, Sight, Weapon(s), Notable traits).
  - Tightened `\tabcolsep` from 4 pt to 2 pt in `build files/header.tex` so dense landscape
    tables fit within the page margins.
  - Reduced the displayed actor preview height from 60 pt to 48 pt to keep rows compact.
- **Result:** LaTeX alignment overfull warnings for the actor tables are gone; the only remaining
  overfull boxes are small paragraph-level warnings in the introductory text (≤8.5 pt), not the
  table itself.

### CNC TRUCK cameo palette fix

- **Root cause:** CNC `TRUCK` uses `truckicon.shp` instead of the usual `*.icnh.tem` icon files.
  The `chrome` palette (which uses `ShadowIndex: 3`) left the SHP's `ShadowIndex: 4` pixels opaque,
  producing dark shadow artifacts.
- **Fix:** Added an `iconPaletteOverrides` map in `build files/extract_cameos.ps1` and
  special-cased `cnc/TRUCK` to render with the `terrain` palette (which uses `ShadowIndex: 4`).
- **Verification:** Re-extracted all actor images; `truck.png` now has 308 transparent shadow pixels,
  matching the `terrain` palette's shadow index, while other CNC icons remain unchanged.

### Final PDF build

- Re-ran `build files/generate_actor_reference.py` to regenerate the Markdown with the new
  `Preview` column and balanced widths.
- Re-ran the full PDF pipeline: `build_manual.ps1 -Export pdf`.
- Verification passed:
  - `assemble_manual.py`: 58 chapters, 2,164,834 bytes
  - `verify_paths.py`: 275 paths, 0 missing
  - `verify_internal_links.py`: 6,332 links, 0 broken
  - PDF: `OpenRA_Knowledge_Base_Manual.pdf` (1,303 pages, 28.6 MB)
- LaTeX compiled cleanly with no fatal errors; actor table alignment overfull warnings resolved.

### Files changed (this session)

- `build files/generate_actor_reference.py`
- `build files/format_tables_vlines.py`
- `build files/header.tex`
- `build files/extract_cameos.ps1`
- `OpenRA GitHub Repositories\OpenRA\OpenRA.Mods.Common\UtilityCommands\ExportSequenceFrameCommand.cs`
- `OpenRA GitHub Repositories\OpenRA\OpenRA.Mods.Cnc\UtilityCommands\ExportVoxelFrameCommand.cs`
- `Manual/DEVELOPMENT_LOG.md` (this entry)

## 2026-07-03 — Round 4: TS unit rotation fixes (SHP facing + voxel yaw)

### What was done

#### TS SHP Unit Rotation (ExportSequenceFrameCommand.cs)
- **Root cause**: Tiberian Sun sets `UseClassicPerspectiveFudge: False` in `BodyOrientation`, which
  rotates the game coordinate system 90° relative to RA/CnC. The forward-facing direction for TS
  units toward the camera is **West** (WAngle 256, index 2 for 8-facing sprites) rather than the
  default **South** (WAngle 512, index 4) used for RA/CnC/D2K.
- **Fix**: Added `ForwardFacingAngle(tileset)` helper and TS-tileset detection (`TEMPERATE`, `SNOW`)
  to `ExportSequenceFrameCommand.cs`. TS tilesets now use `WAngle(256)` (West); all others use
  `WAngle(512)` (South). The facing offset is computed via `Util.IndexFacing(forwardAngle, facings)`
  instead of the hardcoded `facings/2` formula.
- **Verification**: For RA/CnC 8-facing infantry, `IndexFacing(WAngle(512), 8) = 4` = same as before.
  For TS 8-facing infantry, `IndexFacing(WAngle(256), 8) = 2` = West-facing frame (90° corrected).
  For TS 32-facing vehicles, `IndexFacing(WAngle(256), 32) = 8` = West-facing frame (same 90° fix).
- **Added `using OpenRA;`** to support `WAngle` usage in the file.

#### TS Voxel Unit Rotation (ExportVoxelFrameCommand.cs)
- **Root cause**: The simple orthographic renderer used yaw=45° (π/4). Based on the reported "~90°
  rotation" error and empirical testing of aspect ratios, the correct yaw is **135°** (3π/4).
- **Tried 90°**: yaw=π/2 produced APC 168h×66w (very tall, narrow — vehicle height mapped to
  screen horizontal, which is incorrect).
- **Tried 135°**: yaw=3π/4 produced APC 162h×168w (nearly square, natural aspect ratio for a vehicle
  viewed from the front-left diagonal). MCV: 168h×144w. ORCA: 168h×138w. All significantly wider
  than at 90°.
- **Final yaw**: Changed to `Math.PI * 3 / 4` (135°). The 30° pitch (`Math.PI / 6`) is unchanged.

#### Build and Extraction
- Rebuilt `OpenRA.Utility.exe` via `dotnet build -c Release` (0 errors, 0 warnings, ~3–7s).
- Re-ran `extract_cameos.ps1` (all four mods, 269 actors total): 80 TS actors processed;
  253 unit images rescaled to ≥192 px; 7 TS actors kept placeholder (no world sprite or voxel model).
- RA/CnC/D2K images also regenerated (facing formula unchanged for those mods).

#### house01.tem Investigation (Appendix K/J)
- `house01.tem` appears in **Appendix J (Terrain Tiles)** not Appendix K (Environmental Actors).
- It is **Template 11** in the TS Temperate tileset: `Categories: House`, `Size: 2,2`, terrain type
  `Cliff` for all 4 tiles. The terrain renders correctly (59% opaque diamond pixels, 60 unique colors,
  brownish-gray rocky palette consistent with cliff terrain).
- The `Category: House` label in the TS map editor refers to a cliff/rocky-terrain category, not a
  civilian building. This is a Westwood naming convention, not a visual error.
- No code change needed for house01.tem; the image is rendered correctly.

### Files changed
- `OpenRA GitHub Repositories\OpenRA\OpenRA.Mods.Common\UtilityCommands\ExportSequenceFrameCommand.cs`
  (added `using OpenRA;`, `TsTilesets` hashset, `ForwardFacingAngle()` helper, updated `TryGetFrame`
  and `ResolveFirstFrameIndex` signatures to use `WAngle forwardAngle` parameter)
- `OpenRA GitHub Repositories\OpenRA\OpenRA.Mods.Cnc\UtilityCommands\ExportVoxelFrameCommand.cs`
  (changed yaw from `Math.PI/4` to `Math.PI*3/4`)
- `Manual\images\actors\ts\*_unit.png` — all regenerated with corrected facing/yaw
- `Manual\images\actors\ra\*_unit.png`, `cnc\*_unit.png`, `d2k\*_unit.png` — also regenerated (same formula, should be visually identical)
- `Manual\DEVELOPMENT_LOG.md` (this entry)

### Remaining open issues
- TS voxel unit **colors**: most voxel units show player-color (red for GDI) because `unittem.pal`
  has player-color remap indices (80–95) mapped to red. This is correct behavior — GDI uses red by
  default. The colors will look correct once the user inspects the actual PDF.
- **TTNK (Titan Tank)** voxel only shows a 44×44 bounding box in 192px — only the chassis voxel
  is loaded; turret and barrel are separate VXL files not composited by `--export-voxel-frame`.
  This is a pre-existing limitation.
- **SHP facing**: The analysis uses West (index 2) for TS. If the resulting images still look wrong
  after visual inspection, try index 6 (East = WAngle 768) as the next candidate.
- **Voxel yaw**: 135° was chosen based on aspect-ratio improvement. If still incorrect after visual
  inspection, try 0° (front-on) as the next candidate.
- **PDF build** was NOT run (per task instructions — leave for orchestrator).

## 2026-07-01 — Round 3: TS units in Appendix I, larger unit previews

### What was done
- **Bumped actor unit sprites to 192 px.**
  - `build files/rescale_actor_unit_images.py` `MIN_SIZE` increased to 192 per user request.
  - Re-ran the rescale step and rebuilt the PDF; output is now 1,293 pages / ~28.7 MB.
- **Moved Tiberian Sun units into Appendix I (Actor Reference).**
  - `build files/generate_actor_reference.py` now includes the `ts` mod alongside `ra`, `cnc`, and `d2k`.
  - Added TS faction keywords (`gdi`, `nod`, `ga`, `na`, etc.) and faction placeholder colors.
  - The generator now writes a richer `actor_manifest.json` with `code -> image` mappings so the extraction script can resolve faction-specific SHP image names like `e1.gdi`.
  - Removed the dedicated TS Units section from Appendix K; TS units no longer appear in the environmental actor reference.
- **Made all unit previews roughly twice as large.**
  - `build files/rescale_actor_unit_images.py` and `build files/rescale_environmental_images.py` now upscale to at least **128 px** on the longest side (was 64 px).
  - `build files/extract_environmental_images.py` now caps preview downscaling at 128 px so the final rescale step does not double-resize.
- **Updated actor cameo extraction to handle Tiberian Sun.**
  - `build files/extract_cameos.ps1` now iterates over `ts`, uses the `chrome` palette for icons, and the `player` palette for in-world sprites.
  - Added TS tileset `TEMPERATE` and voxel fallback logic for TS aircraft/vehicles (ORCA, HVR, MCV, HARV, etc.) via the existing `--export-voxel-frame` command.
  - Fixed PowerShell manifest lookup (`$entries.$code` instead of `$entries[$code]`) and D2K image-map lookup by actor code.
- Re-ran the full pipeline:
  - `generate_actor_reference.py`
  - `generate_environmental_actor_reference.py`
  - `extract_environmental_images.py`
  - `extract_cameos.ps1`
  - `build_manual.ps1 -Export pdf`
- Verification passed:
  - `assemble_manual.py`: 58 chapters, 2,165,685 bytes
  - `verify_paths.py`: 275 paths, 0 missing
  - `verify_internal_links.py`: 6,332 links, 0 broken
  - PDF: `OpenRA_Knowledge_Base_Manual.pdf` (1,293 pages, ~29.9 MB)

### Files changed
- `build files/generate_actor_reference.py`
- `build files/generate_environmental_actor_reference.py`
- `build files/extract_cameos.ps1`
- `build files/extract_environmental_images.py`
- `build files/rescale_actor_unit_images.py`
- `build files/rescale_environmental_images.py`
- `build files/actor_manifest.json`
- `build files/environmental_actor_manifest.json`
- `build files/appendices/Appendix_I_Actor_Reference.md`
- `build files/appendices/Appendix_K_Environmental_Actors.md`
- `OpenRA_Knowledge_Base_Manual.pdf` (regenerated)
- `Manual/DEVELOPMENT_LOG.md` (updated)

### Remaining notes / handoff to next session
- A few TS actors in Appendix I still have no usable unit preview (GAPOWRUP, GAPLUG2/3/4, GAVULC, GAROCK, GACSAM, MOBILEMP) and keep their placeholder because they are upgrade/support buildings with no world sprite or voxel model.
- D2K `deathhand`, `concretea`, `concreteb` similarly have no world sprite and keep placeholders.
- Open visual-polish issues identified by the user:
  - Appendix I tables still creep off the right side of landscape pages, especially with the new 192 px unit sprites.
  - D2K tables have uneven column widths, overly tall rows, and overlapping columns.
  - CNC `TRUCK` supply-truck cameo shows artifacting (likely wrong palette; it uses `truckicon.shp` instead of the usual `*.icnh.tem` icon files).
  - TS SHP and voxel units appear rotated ~90 degrees from the expected orientation.
  - TS environmental actor `house01.tem` looks incorrect.
- A handoff prompt for the next Claude session is saved at `build files/HANDOFF_PROMPT.md` with reproduction steps, file pointers, and suggested fixes.
- Cleaned junk from the working directory:
  - Moved 34 build/LaTeX log/intermediate files from `Manual/` to `Cameo Work\to delete\manual_cleanup_2026-07-01`.
  - Moved 2 orphaned RA actor images (`warriorant.png`, `warriorant_unit.png`) to the same cleanup folder.
  - Moved 158 orphaned environmental `_unit.png` files to the same cleanup folder.
  - Moved 375 regenerated SVG-PDF cache files to the same cleanup folder.
  - Moved 9 additional files (`pages_check.txt`, `OpenRA_Knowledge_Base_Manual.docx`, `__pycache__` bytecode, etc.).
  - Moved 15 temporary voxel source files (`.vxl`/`.hva`) and `template.tex` from `build files/`.
  - Removed 2 empty directories (`svg-pdf-cache`, `__pycache__`).
  - **Regenerated `build files/svg-pdf-cache/` (317 PDFs) because Opus needs it for PDF rebuilds.**
  - Verification still passes after cleanup.

## 2026-06-30 — Round 2: TS cameos, CNC terrain palette, and TS unit ordering

### What was done
- **TS unit previews in Appendix K now use cameos instead of tiny battlefield sprites.**
  - `build files/extract_environmental_images.py` now tries the `icon` sequence first for every TS unit code, falling back to `@unit` only when a cameo doesn't exist. This makes the infantry and vehicle previews readable (64×48 sidebar cameos) instead of barely-visible isometric sprites.
  - Voxel-only units (ICBM, BUS, PICK, CAR, WINI, TRUCKA, TRUCKB, 4TNK) still get their dedicated orthographic voxel render from `extract_voxel_previews.py`.
- **CNC unit/vehicle palette fixed.**
  - `build files/extract_cameos.ps1` now uses the `terrain` palette for CNC units instead of the non-existent `player` palette. Because `terrain` is the base of the CNC `player` palette and correctly identifies shadow pixels, the vehicle previews no longer render yellow ground shadows.
- **TS units moved to the top of Appendix K's Tiberian Sun chapter.**
  - `build files/generate_environmental_actor_reference.py` now places `Units` first in `SECTION_ORDER`, so the TS Units section appears right after the `## Tiberian Sun` header instead of at the end of the chapter.
- Re-ran the full pipeline:
  - `generate_environmental_actor_reference.py`
  - `extract_environmental_images.py --force`
  - `extract_voxel_previews.py`
  - `extract_cameos.ps1`
  - `build_manual.ps1 -Export pdf`
- Verification passed:
  - `assemble_manual.py`: 58 chapters, 2,156,237 bytes
  - `verify_paths.py`: 275 paths, 0 missing
  - `verify_internal_links.py`: 6,235 links, 0 broken
  - PDF: `OpenRA_Knowledge_Base_Manual.pdf` (1,292 pages, ~29.3 MB)

### Files changed
- `build files/extract_environmental_images.py`
- `build files/extract_cameos.ps1`
- `build files/generate_environmental_actor_reference.py`
- `build files/environmental_actor_manifest.json`
- `build files/appendices/Appendix_K_Environmental_Actors.md`
- `OpenRA_Knowledge_Base_Manual.pdf` (regenerated)
- `Manual/DEVELOPMENT_LOG.md` (updated)

### Remaining notes
- CNC building cameos use the `chrome` (UI) palette and retain their original desert/tan art colouring. If those still look too yellow to you, the art itself is the cause, not the palette.
- A few TS actors without sidebar icons (HUNTER, WEEDGUY) still show small in-world previews because no cameo exists for them.

## 2026-06-30 — Palette, facings, TS placeholder duplicates, and voxel previews

### What was done
- Fixed yellow/dark shadowing on actor/building previews in `build files/extract_cameos.ps1` by using per-purpose palettes (`chrome` for icons, `player`/`d2k` for units) instead of forcing the terrain palette on every image.
- Fixed D2K vehicle orientation in `OpenRA.Mods.Common/UtilityCommands/ExportSequenceFrameCommand.cs`: `ResolveFirstFrameIndex` now uses `Math.Abs(facings)` when picking the forward-facing frame, so negative facings (used by D2K vehicles) no longer rotate the sprite in the wrong direction.
- Fixed the duplicate "placeholder + actual preview" issue for Tiberian Sun units in Appendix K:
  - `build files/generate_environmental_actor_reference.py` now emits only one preview image per TS unit row (`images/environmental/ts/<code>.png`) instead of two.
  - Removed the unused `<code>_unit.png` placeholder generation; existing `_unit.png` files were moved to `to delete/openra_engine_temp_extracts`.
- Added real previews for TS voxel-only units (ICBM, BUS, PICK, CAR, WINI, TRUCKA, TRUCKB, 4TNK):
  - Added a new `--export-voxel-frame` utility command in `OpenRA.Mods.Cnc/UtilityCommands/ExportVoxelFrameCommand.cs` that renders the original `.vxl`/`.hva` files with a simple orthographic projection and saves a neutral PNG.
  - Added `build files/extract_voxel_previews.py` to drive the new command for the voxel-only TS units.
- Fixed TS SHP preview cropping in `ExportSequenceFrameCommand.cs`: frames are now padded back to their full `FrameSize` before being saved, so TS units like `E1`/`E2`/`Medic` render at the correct canvas size instead of a tiny cropped rectangle.
- Re-ran the actor extraction (`extract_cameos.ps1`), environmental extraction (`extract_environmental_images.py --force`), and voxel extraction (`extract_voxel_previews.py`).
- Rebuilt the PDF via `build_manual.ps1 -Export pdf`:
  - `assemble_manual.py`, `verify_paths.py`, and `verify_internal_links.py` all passed.
  - PDF produced: `OpenRA_Knowledge_Base_Manual.pdf` (1,292 pages, ~29.2 MB).

### Files changed
- `OpenRA GitHub Repositories/OpenRA/OpenRA.Mods.Common/UtilityCommands/ExportSequenceFrameCommand.cs`
- `OpenRA GitHub Repositories/OpenRA/OpenRA.Mods.Cnc/UtilityCommands/ExportVoxelFrameCommand.cs` (new)
- `build files/extract_cameos.ps1`
- `build files/extract_environmental_images.py`
- `build files/extract_voxel_previews.py` (new)
- `build files/generate_environmental_actor_reference.py`
- `build files/environmental_actor_manifest.json`
- `build files/appendices/Appendix_K_Environmental_Actors.md`
- `OpenRA_Knowledge_Base_Manual.pdf` (regenerated)
- `Manual/DEVELOPMENT_LOG.md` (updated)

### Remaining blockers / notes
- TS SHP unit previews (e.g., infantry) are rendered from the in-world `stand`/`idle` frame, so the visible sprite is small within the 64×64 canvas because the isometric frame is mostly transparent. If a larger cameo-style preview is preferred for these units, the extraction can be switched to use the `icon` sequence instead of `@unit`.
- TS drop pods / dropships (`DPOD`, `DSHP`) and a few other SHP-based units still show tiny previews or placeholders; these are typically special-effect actors rather than front-line units.

## 2026-06-30 — Final PDF build and landscape header refinement

### What was done
- Rebuilt the PDF from the combined manual using `build_manual.ps1 -Export pdf`.
  - PDF produced: `OpenRA_Knowledge_Base_Manual.pdf` (1,296 pages, ~29.5 MB).
- Refined the landscape appendix header fix in `build files/format_tables_vlines.py`:
  - The original `\markboth` placement fixed the wrong-title carryover for Appendix I, but Appendices J and K (which follow another landscape appendix) still showed the previous appendix title in the running header.
  - Added `\def\leftmark{<title>}` right after the `\section` command inside each landscape wrapper. This forces the right-running header to the correct appendix title for every page inside the landscape environment.
  - Kept a `\markboth{<title>}{<title>}` before the landscape and at the end of each landscape wrapper to keep the underlying LaTeX marks consistent with the title.
- Fixed a LaTeX error in the actor-reference column spec introduced by `actor_columnspec()`: replaced `p{\real{0.XXXX}}` with `p{0.XXXX\linewidth}` because `\real{}` cannot be assigned directly to `\hsize` inside an `array`/`longtable` `p{}` column (confirmed with a minimal LuaLaTeX test).
- Verified the combined manual and the final PDF:
  - `py assemble_manual.py` produced the combined manual (58 chapters, 2,160,060 bytes).
  - `py verify_paths.py`: 275 referenced paths, 0 missing.
  - `py verify_internal_links.py`: 6,298 internal links, 0 broken.
  - Spot-checked the PDF text: Appendices I, J, and K now show their own titles in the running header (e.g., `Appendix J — Terrain Tile Reference`, `Appendix K — Environmental Actor Reference`) instead of carrying over the previous appendix title.

### Files changed
- `Manual\build files\format_tables_vlines.py` (landscape header fix + actor column spec fix)
- `OpenRA_Knowledge_Base_Manual.pdf` (regenerated)
- `Manual\DEVELOPMENT_LOG.md` (updated)

### Remaining blockers / notes
- None. The requested fixes (appendix ordering, landscape header, actor preview orientation, turret compositing, table layout, environmental palette/placeholders, TS units) are all in the rebuilt PDF.

## 2026-06-30 — Added Tiberian Sun units to Appendix K (Environmental Actor Reference)

### What was done
- Updated `build files/generate_environmental_actor_reference.py`:
  - Added a curated `TS_UNIT_CODES` set for the Tiberian Sun units that should appear in Appendix K.
  - Used this set as an explicit fallback in `is_ts_unit()` so TS units are always included even if trait detection fails.
  - Added a `preview` field to each row so the generated Markdown table references the correct image paths.
  - TS unit rows now reference both `images/environmental/ts/<code>.png` (world/cameo preview) and `images/environmental/ts/<code>_unit.png` (unit preview).
  - Changed placeholder generation in `main()` to skip existing image files, preserving the real TS unit previews already rendered by the extraction step.
- Regenerated `environmental_actor_manifest.json` and `build files/appendices/Appendix_K_Environmental_Actors.md`.
- Ran `assemble_manual.py` to refresh the combined `OpenRA_Knowledge_Base_Manual.md`.
- Verified `verify_paths.py` (275 paths, 0 missing) and `verify_internal_links.py` (6298 links, 0 broken) both pass.

### TS units included
The TS Units section in Appendix K now contains 63 rows, including:
- Vehicles: `MCV`, `HARV`, `APC`, `HVR`, `HMEC`, `SONIC`, `MOBILEMP`, `BGGY`, `BIKE`, `REPAIR`, `WEED`, `SAPC`, `SUBTANK`, `STNK`, `SGEN`, `LPST`, `SMECH`, `MMCH`, `JUGG`, `TTNK`, `ART2`, `MHIJACK`, `4TNK`, `TRUCKA`, `TRUCKB`, `ICBM`, `BUS`, `PICK`, `CAR`, `WINI`.
- Infantry: `E1`, `E1R3`, `E2`, `E2R3`, `E3`, `CYBORG`, `CYC2`, `MEDIC`, `JUMPJET`, `GHOST`, `WEEDGUY`, `UMAGON`, `CHAMSPY`, `MUTANT`, `MWMN`, `MUTANT3`, `TRATOS`, `OXANNA`, `SLAV`, `ENGINEER`, `FLAMEGUY`.
- Aircraft: `ORCA`, `ORCAB`, `ORCATRAN`, `TRNSPORT`, `SCRIN`, `APACHE`, `HUNTER`.
- Drop pods / dropships: `DPOD`, `DPOD2`, `DPOD2E1`, `DPOD2E2`, `DSHP`.

### New row counts
- Total environmental actors in Appendix K: 544 (RA: 135, CnC: 103, D2K: 12, TS: 294).
- TS Units section: 63 rows.
- Combined manual internal links: 6298 checked, 0 broken.

### Files changed
- `Manual\build files\generate_environmental_actor_reference.py`
- `Manual\build files\environmental_actor_manifest.json`
- `Manual\build files\appendices\Appendix_K_Environmental_Actors.md`
- `OpenRA_Knowledge_Base_Manual.md`
- `Manual\DEVELOPMENT_LOG.md`

### Remaining blockers / notes
- Full PDF build was not run per instructions.
- Placeholder generation now skips existing images, so the previews rendered by the earlier extraction step are preserved.

## 2026-06-30 — Appendix ordering and landscape header fix

### What was done
- Reordered the appendices so all reference volumes sit at the end of the training/lesson material:
  - Swapped labels G and H: `Advanced Modding Walkthroughs` is now Appendix G and `Asset Visual Reference` is now Appendix H.
  - Renamed `Appendix_G_Asset_Visual_Reference.md` → `Appendix_H_Asset_Visual_Reference.md` and `Appendix_H_Advanced_Modding_Walkthroughs.md` → `Appendix_G_Advanced_Modding_Walkthroughs.md`.
  - Updated `assemble_manual.py`, `MASTER_INDEX.md`, every chapter cross-reference, and the `engine-tests` snippets to use the new labels.
- Fixed the running header in the landscape reference appendices (I, J, K):
  - Updated `build files/format_tables_vlines.py` to split the leading `\section{...}` command out of each wrapped appendix, clean the newline out of the section title, and insert `\markboth{<title>}{<title>}` immediately after the section command.
  - This stops the header from showing the previous appendix title (e.g., "Appendix Advanced Modding Walkthroughs") across the reference volumes; each landscape appendix now shows its own title in the header.
- Verified the combined manual: `verify_paths.py` (275 paths, 0 missing) and `verify_internal_links.py` (6172 links, 0 broken) both pass.
- Generated the LaTeX source and confirmed the landscape wrappers now produce `\clearpage\begin{landscape}...\section{Appendix I --- Actor Reference}\markboth{...}...` for I, J, and K.

### Files changed
- `Manual\build files\assemble_manual.py` (appendix order)
- `Manual\build files\MASTER_INDEX.md` (G/H labels and filenames)
- `Manual\build files\appendices\Appendix_G_Advanced_Modding_Walkthroughs.md` (renamed, heading updated)
- `Manual\build files\appendices\Appendix_H_Asset_Visual_Reference.md` (renamed, heading updated)
- `Manual\build files\appendices\Appendix_I_Actor_Reference.md` (cross-reference to Asset Visual Reference updated)
- `Manual\build files\generate_actor_reference.py` (cross-reference to Asset Visual Reference updated)
- `Manual\build files\format_tables_vlines.py` (landscape wrapping + `\markboth`)
- All chapter Markdown files that referenced Appendices G and H.
- `Manual\build files\engine-tests\*` (walkthrough labels updated).

### Remaining blockers / notes
- None for the appendix ordering/header task.

## 2026-06-30 — Appendix I actor reference preview and layout fixes

### What was done
- Fixed `OpenRA.Mods.Common/UtilityCommands/ExportSequenceFrameCommand.cs` for `@unit` rendering:
  - Forward-facing frame selection: when a sequence has `Facings` > 1, the chosen frame is offset by `Facings/2 * Stride` (opposite of the first facing). This fixes RA infantry E1–E4 and vehicles that were facing away from the camera.
  - Turret compositing: added a `turret` overlay on top of the body for vehicles that have a separate `turret` sequence (e.g., Light/Medium/Heavy/Mammoth tanks, jeep, flak truck, stealth tank).
  - Updated the command description to document the new behavior.
- Updated `build files/extract_cameos.ps1`:
  - Added RA fake-building mapping (FPWR/TENF/SYRF/SPEF/WEAF/DOMF/FIXF/FAPW/ATEF/PDOF/MSLF/FACF) so their cameos render from the real building's `fake-icon` sequence and their in-world sprites render from the real building's image.
- Updated `build files/generate_actor_reference.py`:
  - Added a `SKIP_CODES` set and removed `WarriorAnt` from the reference (no sprite sequence exists for it).
- Updated `build files/format_tables_vlines.py`:
  - Widened the `Name` column from 0.06 to 0.10 to prevent "Mobile Construction Vehicle" from spilling.
  - Rebuilt the actor-table column spec so the last `Notable traits` column is a wrapping `p` column.
  - Increased landscape `\arraystretch` from 1.0 to 1.2 for better row height in the reference tables.
- Built the OpenRA engine (`dotnet build -c Release`) so the updated utility command is available.
- Re-ran `generate_actor_reference.py` and `extract_cameos.ps1`. Regenerated `Appendix_I_Actor_Reference.md`, `actor_manifest.json`, and all actor cameo/unit PNGs.
- Verified that all RA and CNC actor images are now real sprites (no placeholder-colored backgrounds detected). D2K retains expected placeholders for `mpsardaukar`, `nsfremen`, `deathhand`, `concretea`, `concreteb` (missing content/sequences).

### Files changed
- `OpenRA GitHub Repositories\OpenRA\OpenRA.Mods.Common\UtilityCommands\ExportSequenceFrameCommand.cs`
- `Manual\build files\extract_cameos.ps1`
- `Manual\build files\generate_actor_reference.py`
- `Manual\build files\format_tables_vlines.py`
- `Manual\build files\appendices\Appendix_I_Actor_Reference.md`
- `Manual\build files\actor_manifest.json`
- `Manual\images\actors\` (regenerated cameo/unit PNGs for all three mods)
- `Manual\DEVELOPMENT_LOG.md` (updated)

### Actors fixed / suppressed
- Suppressed: `WarriorAnt` (no sequence exists).
- Rendered real sprites (cameo + unit): all RA and CNC buildable actors, including the 12 fake-building variants and the funpark/civilian-style CNC units (`TRUCK`, `PVICE`, `STEG`, `TREX`, `TRIC`, `RAPT`).
- Forward-facing frame applied to: RA infantry E1–E4 and all vehicles/buildings with faceted `idle`/`stand` sequences.
- Turret compositing applied to: vehicles with a `turret` sequence (e.g., `1TNK`, `2TNK`, `3TNK`, `4TNK`, `JEEP`, `FTRK`, `STNK`).

### Remaining blockers / notes
- D2K `mpsardaukar`, `nsfremen`, `deathhand`, `concretea`, `concreteb` keep their placeholders because their sequences/content are missing; these are not part of the requested RA/CNC fixes.
- Full PDF layout verification was not run per instructions; only the actor-reference generation pipeline was executed.

## 2026-06-30 — Appendix K environmental actor palette and placeholder fixes

### What was done
- Extended `build files/extract_environmental_images.py`:
  - Added palette-name resolution logic (derived-palette fallbacks, player-palette fallbacks per mod, body-trait palette overrides) and passes the correct `TILESET` and `PALETTE` arguments to `OpenRA.Utility.exe --export-sequence-frame`.
  - Added tileset selection from `MapEditorData` restrictions and fallback lists for each mod so actors are rendered against the tileset they actually appear in.
  - Added RA/C&C bridge rendering via `OpenRA.Utility.exe --export-terrain-template`, trying every mod tileset when the preferred one does not define the bridge template.
  - Added `editor` sequence fallback for TS dead bridge variants (`LOBRDG_A_D`, `LOBRDG_B_D`) and `icon` sequence fallback (using the `chrome` palette) for TS voxel-only units/vehicles/aircraft.
  - Added a 64 px resize step for all extracted previews so the reference tables stay compact.
- The OpenRA engine utility command `ExportSequenceFrameCommand.cs` was already updated to resolve the effective palette from each sequence's `Palette` / `TilesetPalette` keys; this corrects tileset-specific palette overrides for all environmental actors, not just the default tileset.
- Re-ran `extract_environmental_images.py`. Regenerated `Manual/images/environmental/` previews for all four mods.
- Verified `verify_paths.py`: 275 paths checked, 0 missing. Spot-checked `RA/BRIDGE3`, `RA/BRIDGE1`, `TS/LOBRDG_A_D`, `TS/MCV`, `TS/ORCA`, `TS/APC`, `CnC/BRIDGE3` — all are real, non-placeholder images.

### Results
| Mod | Generated | Failed |
| :---- | ----: | ----: |
| RA | 134 | 1 |
| CnC | 102 | 1 |
| D2K | 12 | 0 |
| TS | 281 | 13 |
| **Total** | **529** | **15** |

This is up from 492 generated / 52 failed before the fixes.

### Files changed
- `Manual\build files\extract_environmental_images.py`
- `Manual\images\environmental\` (regenerated / resized previews)
- `Manual\DEVELOPMENT_LOG.md` (updated)

### Remaining blockers / notes
- 15 actors still keep placeholders because they have no extractable graphics:
  - RA/CnC: `BRIDGEHUT` (logic actor, no rendered sprite).
  - TS: `LOCOMOTIVE`, `TRAINCAR`, `CARGOCAR`, `DPOD`, `DSHP`, `4TNK`, `TRUCKA`, `TRUCKB`, `ICBM`, `BUS`, `PICK`, `CAR`, `WINI` (pure voxel or missing content).
- Full PDF layout verification was not run per instructions; only the environmental extraction pipeline was executed.

## 2026-06-30 — Appendix J terrain preview rendering fixes

### What was done
- Investigated and fixed terrain preview rendering issues in `OpenRA.Mods.Common/UtilityCommands/ExportTerrainTemplateCommand.cs`:
  - Palette selection now reads the mod's `PaletteFromFile` rules to find the exact palette filename and shadow indices for each tileset, fixing wrong palettes for RA Desert, CNC Desert, and TS Temperate/Snow.
  - Added a fallback heuristic that tries tileset-specific names (`desert.pal`, `isotem.pal`, etc.) before generic names.
  - Shadow indices are now rendered as transparent, eliminating purple/pink noise from RA/CNC shadow pixels.
  - Fixed `BuildTileList` to only use the first `TilesCount` entries from `Frames`, matching in-game behavior and preventing crashes on D2K templates like `customtiles.r16` template 611 where `Frames` is longer than `Size`.
- Fixed `build files/extract_terrain_images.py`:
  - Restored `get_image_stem_ext()` and `make_preview_filename()` so D2K Arrakis previews are correctly disambiguated by template ID (`BLOXBASE_1.R16.png`, etc.).
  - Fixed `parse_row()` and `update_markdown()` to handle a `Preview` column at the beginning of the table and to carry through `Size`, `Primary Terrain`, and `Notes` columns.
  - Preview filenames are now computed from the template ID, not inherited from the existing Markdown cell, so broken/disambiguated paths are repaired automatically.
  - Added a file-existence skip so re-runs do not regenerate images that are already present (unless `--force` is used).
- Built the OpenRA engine (`dotnet build -c Release`) so the updated utility command is available.
- Moved old affected terrain preview directories to `C:\Users\Kmoney\Documents\AI Projects\Cameo Work\to delete\terrain_images_backup_20260630_105726`.
- Re-ran `extract_terrain_images.py` and regenerated all terrain preview PNGs and Markdown tables.
- Verified the fixes with `build files/verify_terrain_fixes.py`:
  - RA Desert: 271 images regenerated, no purple/pink artifacts detected.
  - CNC Desert: 177 images regenerated, no purple/pink artifacts detected.
  - TS Temperate: 275 images regenerated; checked `bld01.tem`, `house01.tem`, `civ01.tem`, `shore41.tem`, `water01.tem` through `water14.tem` — no pink/purple artifacts detected.
  - D2K Arrakis: 671 preview files, 664 disambiguated by template ID; Markdown now references the correct per-template files instead of the same `BLOXBASE.R16.png` for every row.
- Regenerated the combined manual with `assemble_manual.py`.
- Verified the combined manual: `verify_paths.py` (275 paths, 0 missing) and `verify_internal_links.py` (6174 links, 0 broken) both pass.

### Files changed
- `OpenRA GitHub Repositories\OpenRA\OpenRA.Mods.Common\UtilityCommands\ExportTerrainTemplateCommand.cs` (palette selection, shadow handling, frame-count fix)
- `Manual\build files\extract_terrain_images.py` (disambiguation, Markdown update, parsing fixes)
- `Manual\build files\verify_terrain_fixes.py` (new verification script)
- `Manual\build files\appendices\Appendix_J_Terrain_Tiles.md` (preview paths refreshed)
- `Manual\images\terrain\` (regenerated previews for all tilesets)
- `Manual\DEVELOPMENT_LOG.md` (updated)

### Remaining blockers / notes
- 22 groups of identical D2K Arrakis preview files were detected. These appear to be legitimate cases where different templates reference the same visual tile; manual review may be needed if any are unexpected.
- All other reported palette/artifact issues appear resolved.

## 2026-07-02 — Appendix K environmental actor previews

### What was done
- Created `build files/generate_environmental_actor_reference.py`.
  - Parses all four official mods' `rules/*.yaml` (resolving `Inherits:` chains) and `fluent/rules.ftl`.
  - Filters environmental actors by editor category (`Tree`, `Decoration`, `Civilian building`, `Tech building`, `Wall`, `Bridge`, `Crate`, `Resource spawn`, `Critter`, etc.) plus explicit includes for D2K System-category actors (`spicebloom`, `sandworm`, `sietch`, `crate`).
  - Groups actors into sections (Vegetation, Rocks and Cliffs, Buildings and Structures, Walls and Fences, Bridges, Crates and Pickups, Resource Spawns, Civilians, Critters and Wildlife, Railway, Billboards, Tunnels, Destructible Terrain, Decorative Props, Other).
  - Writes `build files/appendices/Appendix_K_Environmental_Actors.md` with a `Preview` column.
  - Generates labelled placeholder PNGs under `Manual/images/environmental/<mod>/<code>.png` and `<code>_unit.png` using the same neutral style as the actor reference.
  - Writes `build files/environmental_actor_manifest.json`.
- Created `build files/extract_environmental_images.py`.
  - Reads the manifest and uses the OpenRA Utility command `--export-sequence-frame` to render real world sprites for each actor (sequence `idle` for most, `stand` for infantry/critters, D2K-specific overrides for `spicebloom`/`sandworm`).
  - Overwrites placeholders with real sprites where the installed game content supports it, leaving placeholders for missing content.
  - Generated 443 real environmental sprites (RA 112, C&C 96, D2K 12, TS 218) and left 38 placeholders where content/sequences are missing.
- Regenerated the combined manual with `assemble_manual.py`.
- Verified all environmental image references resolve (481 references, 0 missing).
- Ran `verify_paths.py`: 275 paths checked, 0 missing.
- Ran `verify_internal_links.py`: 6174 links checked, 1362 broken. The broken links are all pre-existing D2K terrain tile previews (`images/terrain/d2k/arrakis/...`) and are unrelated to the environmental actor work.

### Files changed
- `Manual\build files\generate_environmental_actor_reference.py` (new)
- `Manual\build files\extract_environmental_images.py` (new)
- `Manual\build files\environmental_actor_manifest.json` (new)
- `Manual\build files\appendices\Appendix_K_Environmental_Actors.md` (rewritten with Preview column and all four mods)
- `Manual\images\environmental\` (962 new PNGs, 443 of them real sprites)
- `OpenRA_Knowledge_Base_Manual.md` (regenerated)
- `Manual\DEVELOPMENT_LOG.md` (updated)

### Remaining blockers / notes
- 38 environmental actors still show placeholders because their sprite sequence or content is missing.
- `verify_internal_links.py` reports 1362 broken links, all D2K terrain tile previews. The D2K game content (`images/terrain/d2k/arrakis/`) is not installed. Re-running `extract_terrain_images.py` after installing the D2K assets will fix these.
- The OpenRA Utility `--export-sequence-frame` command works for environmental actors (confirmed with `t01`, `fcom`, `c1`, `cnc/t01`, `d2k/sandworm`). The optional `@unit` sequence is hard to invoke from the command line because .NET response-file parsing treats `@unit` as a response file; the extractor uses named sequences instead.

## 2026-06-29 — Appendix J terrain tile previews

### What was done
- Added a custom OpenRA Utility command `OpenRA.Mods.Common/UtilityCommands/ExportTerrainTemplateCommand.cs`
  that renders a terrain template (possibly multi-tile/multi-variant) into a single PNG grid.
- Built the OpenRA engine (`make.cmd all`) so the new command is available.
- Added `build files/extract_terrain_images.py` which:
  - Parses `appendices/Appendix_J_Terrain_Tiles.md`.
  - Renders each unique referenced template via `OpenRA.Utility.exe <mod> --export-terrain-template <tileset> <id> <outfile>`.
  - Saves PNGs under `Manual/images/terrain/<mod>/<tileset>/`.
  - Adds a `Preview` column to every "Representative Templates" table.
  - Leaves the cell empty for templates that could not be rendered (e.g. missing content).
- Backed up the original `Appendix_J_Terrain_Tiles.md` to `C:\Users\Kmoney\Documents\AI Projects\Cameo Work\to delete\Appendix_J_Terrain_Tiles.md.backup`.
- Regenerated the combined manual with `assemble_manual.py`.
- Verified the combined manual with `verify_paths.py`, `verify_internal_links.py`, and a custom image-path check: all 853 image references resolve.

### Results
- 149 terrain preview PNGs generated.
- 36 templates failed to render (all Tiberian Sun snow/temperate templates) because the TS game content is not installed.
- 149 terrain preview image references added to the combined manual.

### Remaining blockers
- Tiberian Sun content (`C:\Users\Kmoney\AppData\Roaming\OpenRA\Content\ts`) is not present. Once installed and the mod content is fetched, re-running `extract_terrain_images.py` will fill in the 36 empty TS preview cells.

### Files changed
- `OpenRA GitHub Repositories\OpenRA\OpenRA.Mods.Common\UtilityCommands\ExportTerrainTemplateCommand.cs` (new)
- `Manual\build files\extract_terrain_images.py` (new)
- `Manual\build files\appendices\Appendix_J_Terrain_Tiles.md` (updated tables)
- `OpenRA_Knowledge_Base_Manual.md` (regenerated)
- `Manual\images\terrain\` (149 new PNGs)
- `Manual\DEVELOPMENT_LOG.md` (new)

## 2026-07-01 — Follow-up: GDI tower upgrades (GAROCK/GAVULC/GACSAM) facing forward

### What was done
- Fixed GDI tower upgrade unit previews so they no longer show the static `place` ghost frame facing away from the camera.
- Added `TowerUpgradeOverrides` in `OpenRA.Mods.Common/UtilityCommands/ExportSequenceFrameCommand.cs` to map `gavulc`, `garock`, and `gacsam` to the `gactwr` base tower body and the correct `turret-vulcan`, `turret-rocket`, and `turret-sam` sequences.
- Rebuilt the OpenRA engine, re-extracted all cameos (RA 90, CnC 54, D2K 45, TS 80), and regenerated the PDF.
- Final PDF is 1,372 pages / 29.34 MB; all path and link checks pass.

### Files changed
- `OpenRA GitHub Repositories/OpenRA/OpenRA.Mods.Common/UtilityCommands/ExportSequenceFrameCommand.cs`
- `Manual/images/actors/ts/gavulc_unit.png`, `garock_unit.png`, `gacsam_unit.png`
- `OpenRA_Knowledge_Base_Manual.pdf`
- `Manual/DEVELOPMENT_LOG.md` (this file)

### Next steps
- Production review of the updated PDF.

## 2026-07-02 — Follow-up: bridge and TS unit previews in Appendix K

### What was done
- **Fixed RA/CnC bridge previews.** Added `--export-terrain-template` support to `extract_environmental_images.py` so classic bridge actors (BR1–BR3, BRIDGE1–BRIDGE4, SBRIDGE1–SBRIDGE4) render their real terrain-template graphics. Also added a tileset fallback so desert-only bridge templates (RA/CnC BRIDGE3–BRIDGE4) are exported using the `DESERT` tileset.
- **Fixed TS dead bridge placeholders.** Added `editor` sequence fallback in `extract_environmental_images.py` so TS placeholder bridge actors (`LOBRDG_A_D`, `LOBRDG_B_D`) get a real preview from the available base bridge sprite.
- **Fixed TS unit previews.** Added `icon` sequence fallback using the `chrome` palette so TS voxel-only units that lack an in-world sprite (`MCV`, `HARV`, `APC`, `HVR`, `HMEC`, `SONIC`, `MOBILEMP`, `BGGY`, `BIKE`, `REPAIR`, `WEED`, `SAPC`, `SUBTANK`, `STNK`, aircraft, etc.) show their sidebar cameo instead of a blank placeholder.
- **Capped all preview sizes to 64 px on the longest side** so the Appendix K table stays compact and consistent after the bridge/unit fallbacks.
- **Rebuilt/verified OpenRA Utility.** The modified `ExportSequenceFrameCommand.cs` (auto palette resolution) was already incorporated; extraction ran successfully against it.
- **Regenerated all environmental previews.** Final counts: 529 generated, 15 failed (down from 52 failures).
  - RA: 134 generated, 1 failed (`BRIDGEHUT` — has no graphics).
  - CnC: 102 generated, 1 failed (`BRIDGEHUT` — has no graphics).
  - D2K: 12 generated, 0 failed.
  - TS: 281 generated, 13 failed (`LOCOMOTIVE`, `TRAINCAR`, `CARGOCAR`, `DPOD`, `DSHP`, `4TNK`, `TRUCKA`, `TRUCKB`, `ICBM`, `BUS`, `PICK`, `CAR`, `WINI` — pure voxel/no extractable sprites).

### Files changed
- `build files/extract_environmental_images.py`
- `Manual/images/environmental/` (regenerated/resized previews)
- `Manual/DEVELOPMENT_LOG.md` (this file)

### Next steps
- Production review of the updated previews; decide whether to add a text note or custom placeholder for the 15 actors with no extractable graphics.

## 2026-06-30 — Follow-up: actor unit sprites, environmental palette/shadows, and Notes column overrun fixed

### What was done
- **Fixed actor unit/battlefield sprites appearing as tiny placeholders.** `extract_cameos.ps1` now quotes `'@unit'` correctly (PowerShell splatting was dropping the bare `@unit` argument) and calls a new `rescale_actor_unit_images.py` step that upscales all extracted battlefield sprites so the longest side is at least 64 px. This keeps the in-world sprites readable after Pandoc's figure shrink.
- **Fixed environmental actor previews showing pink/yellow artifacts.** Updated `ExportSequenceFrameCommand.cs` to default to the `terrain` logical palette, read the tileset-specific palette file and shadow indices from the mod's `PaletteFromFile` rules, and remap shadow pixels to transparent. Switched `extract_environmental_images.py` to use the `@unit` auto-mode so shadows are dropped and building overlays are composited; added `rescale_environmental_images.py` to upscale the small environmental sprites to at least 64 px.
- **Fixed Notes/Notable traits columns overrunning tables.** `format_tables_vlines.py` was replacing Pandoc's `\toprule`/ `\midrule` booktabs rules with `\hline` *after* it tried to detect table headers by looking for `\hline`. Reordered the pipeline so the booktabs-to-`\hline` replacement happens first, allowing the header detection to match and apply custom widths for the actor, terrain, and environmental reference tables. Environmental Notes column now gets 30% of the landscape width.
- **Rebuilt the PDF.** `OpenRA_Knowledge_Base_Manual.pdf` is now **1,310 pages, 29.6 MB**.
- **Verified everything.** `verify_paths.py` (275 paths, 0 missing), `verify_internal_links.py` (6,174 links, 0 broken), and `verify_terrain_fixes.py` all pass. Spot checks confirm all actor unit images and environmental previews are ≥64 px on the longest side with only trace (likely legitimate) pink/yellow pixels.

### Files changed
- `OpenRA GitHub Repositories/OpenRA/OpenRA.Mods.Common/UtilityCommands/ExportSequenceFrameCommand.cs`
- `build files/extract_cameos.ps1`
- `build files/rescale_actor_unit_images.py` (new)
- `build files/extract_environmental_images.py`
- `build files/rescale_environmental_images.py` (new)
- `build files/format_tables_vlines.py`
- `Manual/images/actors/*/*_unit.png` (regenerated/rescaled)
- `Manual/images/environmental/` (regenerated/rescaled)
- `OpenRA_Knowledge_Base_Manual.md`
- `OpenRA_Knowledge_Base_Manual.pdf`
- `Manual/DEVELOPMENT_LOG.md` (this file)

### Next steps
- Production review of the rebuilt PDF; address any remaining layout or content issues.

## 2026-06-30 — Quality pass: terrain palettes, D2K disambiguation, and Appendix K images fixed

### What was done
- **Fixed RA/CNC Desert terrain purple/pink palette noise.** Updated `ExportTerrainTemplateCommand.cs` to load the correct tileset-specific palette (`desert.pal`) and shadow indices from the mod's `PaletteFromFile` rules, then remapped shadow pixels to transparent.
- **Fixed TS terrain pink/purple artifacts.** Same palette fix now loads `isotem.pal` / `isosno.pal` and applies the correct shadow index remapping for TS previews.
- **Fixed D2K Arrakis duplicate/wrong preview tiles.** Restored per-template-ID filename disambiguation in `extract_terrain_images.py` and `generate_full_terrain_appendix.py` so each template references its own PNG (`BLOXBASE.R16.png` for template 0, `BLOXBASE_*.R16.png` for others). Also fixed a D2K `customtiles.r16` template crash by using only `TilesCount` frames.
- **Added real sprite previews to Appendix K — Environmental Actor Reference.** New generator `generate_environmental_actor_reference.py` and extractor `extract_environmental_images.py` produced 443 real environmental sprites and 962 total PNGs across RA, C&C, D2K, and TS.
- **Made all appendix preview images a consistent visible height in the PDF.** `format_tables_vlines.py` now sets `height=60pt` for actor/unit and environmental images, and `height=96pt` for terrain previews.
- **Rebuilt the PDF.** `OpenRA_Knowledge_Base_Manual.pdf` is now **1,310 pages, 29.0 MB**.
- **Verified everything.** `verify_paths.py` (275 paths, 0 missing), `verify_internal_links.py` (6,174 links, 0 broken), and `verify_terrain_fixes.py` (no purple/pink artifacts, D2K disambiguated) all pass.

### Files changed
- `OpenRA GitHub Repositories/OpenRA/OpenRA.Mods.Common/UtilityCommands/ExportTerrainTemplateCommand.cs`
- `build files/extract_terrain_images.py`
- `build files/generate_full_terrain_appendix.py`
- `build files/format_tables_vlines.py`
- `build files/generate_environmental_actor_reference.py` (new)
- `build files/extract_environmental_images.py` (new)
- `build files/verify_terrain_fixes.py` (new)
- `build files/appendices/Appendix_J_Terrain_Tiles.md`
- `build files/appendices/Appendix_K_Environmental_Actors.md`
- `Manual/images/environmental/` (new directory tree)
- `Manual/images/terrain/` (regenerated previews)
- `OpenRA_Knowledge_Base_Manual.md`
- `OpenRA_Knowledge_Base_Manual.pdf`

### Next steps
- Production review of the new PDF; address any remaining layout or content issues.

## 2026-07-02 — Appendix K environmental actor previews added

### What was done
- Added `build files/generate_environmental_actor_reference.py` to auto-generate Appendix K for all four official mods (RA, C&C, D2K, TS) with a `Preview` column.
- Added `build files/extract_environmental_images.py` to render real sprites via the OpenRA Utility `--export-sequence-frame` command.
- Generated 443 real environmental sprites and 519 placeholder/unit PNGs under `Manual/images/environmental/`.
- Regenerated `OpenRA_Knowledge_Base_Manual.md`.
- Verified environmental image references (481 references, 0 missing). `verify_paths.py` passes; `verify_internal_links.py` reports 1362 pre-existing broken D2K terrain tile links.

### Files changed
- `build files/generate_environmental_actor_reference.py` (new)
- `build files/extract_environmental_images.py` (new)
- `build files/environmental_actor_manifest.json` (new)
- `build files/appendices/Appendix_K_Environmental_Actors.md` (rewritten)
- `Manual/images/environmental/` (new directory tree)
- `Manual/DEVELOPMENT_LOG.md` (updated)

## 2026-06-30 — Quality pass: appendix vertical lines, headers/footers, and overflow fixed

### What was done
- **Fixed missing vertical table separators in appendices** — `format_tables_vlines.py` now correctly tokenizes `>{...}p{...}` column specs (including nested braces like `\real{...}`) and inserts `|` between every pair of columns. Removed two broken preliminary regex substitutions that were corrupting `@{...}` specs.
- **Restored section headers and page numbers in landscape appendices** — switched `landscape_prefix` from `\pagestyle{empty}` back to `\pagestyle{fancy}` so Appendices I, J, and K now show the manual title, section reference (`\leftmark`), centered page number, and faction icons.
- **Eliminated longtable row overflow** — `generate_full_terrain_appendix.py` now summarizes mixed terrain as counts for templates larger than 20 cells, preventing huge `Mixed terrain: {...}` notes from making rows taller than a page. Fixed the size parser to handle both `WxH` and `W,H` formats.
- **Regenerated Appendix J** with compact mixed-terrain notes and rebuilt the PDF.
- **Rebuilt the PDF** — `OpenRA_Knowledge_Base_Manual.pdf` is now **1,083 pages, 24.05 MB**, with 0 Overfull `\vbox` warnings and working vertical lines/headers/page numbers in all landscape appendices.
- **Cleaned up temporary files** — moved `OpenRA_Knowledge_Base_Manual_clean.tex` and several `C:\temp\test_*.py` / page-dump text files to `C:\Users\Kmoney\Documents\AI Projects\Cameo Work\to delete\`.

### Next steps
- Production review of the new PDF; address any remaining layout or content issues.

## 2026-06-30 — Final quality pass: PDF rebuild complete

### What was done
- **Fixed figure placement** — `header.tex` now wraps every Pandoc image in `\par{\centering...\par}` so replacement SVGs stand on their own centered line and text no longer wraps on the same line.
- **Fixed table horizontal lines** — `format_tables_vlines.py` now adds `\hline` after every row inside each `longtable` environment (spreadsheet style), while leaving non-table `\\` alone.
- **Converted all remaining ASCII-font SVGs** — all 16 monospace/ASCII diagrams were replaced with purpose-built graphics by subagents:
  - Part 1: ECS lifecycle, ECS Tick/Render, pathfinding movement stack, combat pipeline
  - Part 2–3: MiniYaml AST shapes, SDK bootstrap architecture
  - Part 4–7: widget tree, pipeline architecture, data-structure interconnectivity, three algorithm flowcharts, terraformer slice-elevation flowchart
  - Part 8–9: bot-module queue rotation, order processing flow, server connection state machine
- **Expanded Appendix J to every template** — added `--dump-terrain-templates` utility command, generated a full `Appendix_J_Terrain_Tiles.md` with **Preview** as the first column, and rendered **3,695 terrain preview PNGs** for all official tilesets (RA, C&C, D2K, TS).
- **Regenerated the combined manual** — `OpenRA_Knowledge_Base_Manual.md` is now 58 chapters, 2,109,933 bytes.
- **Verified links and paths** — `verify_paths.py` (275 paths, 0 missing) and `verify_internal_links.py` (5,691 links, 0 broken) both pass.
- **Rebuilt the PDF** — `OpenRA_Knowledge_Base_Manual.pdf` is now **1,408 pages, 23.77 MB**.

### Next steps
- Production review of the new PDF; address any remaining layout or content issues.

## 2026-06-30 — Converted remaining seven ASCII-font SVGs to purpose-built graphics

### What was done
- **Replaced ASCII-art SVGs with clean graphical diagrams** in `Manual/images/`:
  - `Part_04_Chapter_03_Widgets-Widget_tree.svg` — widget hierarchy rooted at `Ui.Root` with `MenuRootWidget` and `WorldRootWidget` branches.
  - `Part_07_Chapter_01_Pipeline-Architecture.svg` — map-generation pipeline from UI entry points through settings, `MapGenerationArgs`, generator, and output paths.
  - `Part_07_Chapter_02_Data_Structures-Interconnectivity.svg` — structured view of `MapGrid`, `Map`, `CellLayer<T>`, `MapGenerator`, and coordinate systems.
  - `Part_07_Chapter_03_Algorithms-Perlin_noise_flowchart.svg` — Perlin-noise synthesis flowchart.
  - `Part_07_Chapter_03_Algorithms-Boolean_blur_flowchart.svg` — Boolean-blur two-pass sliding-window flowchart.
  - `Part_07_Chapter_03_Algorithms-Dilate_thin_regions_flowchart.svg` — thickness-enforcement (`DilateThinRegions`) flowchart.
  - `Part_07_Chapter_04_Terraformer-Slice_elevation_flowchart.svg` — `SliceElevation` flowchart with masked/unmasked branches.
- **Updated chapter Markdown references** in:
  - `build files/chapters/Part_04_Chapter_03_Widgets.md`
  - `build files/chapters/Part_07_Chapter_01_Pipeline.md`
  - `build files/chapters/Part_07_Chapter_02_Data_Structures.md`
  - `build files/chapters/Part_07_Chapter_03_Algorithms.md`
  - `build files/chapters/Part_07_Chapter_04_Terraformer.md`
- **Moved old ASCII-font SVGs to `C:\Users\Kmoney\Documents\AI Projects\Cameo Work\to delete\OpenRA Manual ASCII SVGs\`** (7 files).
- **Regenerated the combined manual** and ran validation:
  - `assemble_manual.py` — 58 chapters, 2,109,933 bytes.
  - `verify_paths.py` — 275 unique paths checked, 0 missing.
  - `verify_internal_links.py` — 5,691 internal links checked, 0 broken.

### Next steps
- Continue monitoring the remaining ASCII-font/placeholder diagrams from the 2026-06-29 quality review.
- Regenerate the PDF once all diagram replacements are complete.

## 2026-07-01 — Converted first six ASCII-font SVGs to purpose-built graphics

### What was done
- **Replaced ASCII-art SVGs with clean graphical diagrams** in `Manual/images/`:
  - `Part_01_Chapter_01_ECS-Actor_Lifecycle_Diagram.svg` — lifecycle flow from YAML `ActorInfo` through `new Actor()`, trait creation, `INotifyCreated`, `World.Add()`, tick/render loop, and disposal.
  - `Part_01_Chapter_01_ECS-Actor_TickRender_Diagram.svg` — how `Actor.Tick()` and `Actor.Render()` delegate to cached `ITick` / `IRender` trait arrays.
  - `Part_01_Chapter_05_Pathfinding_Movement-The_movement_stack.svg` — layered movement stack from YAML rules down to `Actor.CenterPosition`.
  - `Part_01_Chapter_06_Combat_Damage-The_combat_pipeline.svg` — full combat pipeline from player order through `AttackBase`, `Armament`, projectile, warhead, and `Health.InflictDamage`.
  - `Part_02_Chapter_01_MiniYaml-Two_AST_Shapes.svg` — side-by-side immutable vs. mutable MiniYaml AST trees.
  - `Part_03_Chapter_02_SDK_Bootstrap-Architecture.svg` — Mod SDK repository layout separating mod assets/bootstrap from the pinned engine directory.
- **Updated chapter Markdown references** in:
  - `build files/chapters/Part_01_Chapter_01_ECS.md`
  - `build files/chapters/Part_01_Chapter_05_Pathfinding_Movement.md`
  - `build files/chapters/Part_01_Chapter_06_Combat_Damage.md`
  - `build files/chapters/Part_02_Chapter_01_MiniYaml.md`
  - `build files/chapters/Part_03_Chapter_02_SDK_Bootstrap.md`
- **Moved old ASCII-font SVGs to `C:\Users\Kmoney\Documents\AI Projects\Cameo Work\to delete\`**:
  - `Part_01_Chapter_01_ECS-Actor_Lifecycle_Diagram-1.svg`
  - `Part_01_Chapter_01_ECS-Actor_Lifecycle_Diagram-2.svg`
  - `Part_01_Chapter_05_Pathfinding_Movement-The_movement_stack-1.svg`
  - `Part_01_Chapter_06_Combat_Damage-The_combat_pipeline-1.svg`
  - `Part_02_Chapter_01_MiniYaml-The_Two_AST_Shapes.svg`
  - `Part_03_Chapter_02_SDK_Bootstrap-Architecture-1.svg`
- **Regenerated the combined manual** and ran validation:
  - `assemble_manual.py` — 58 chapters, 2,109,996 bytes.
  - `verify_paths.py` — 275 unique paths checked, 0 missing.
  - `verify_internal_links.py` — 5,691 internal links checked, 0 broken.

### Next steps
- Continue converting the remaining ASCII-font SVGs identified in the 2026-06-29 quality review.
- Regenerate the PDF once all diagram replacements are complete.

## 2026-06-29 — Quality review: remaining diagram, table, and layout issues

### Issues identified during review
- **New architecture diagrams are left-justified and inline with text.** The recently replaced `Part_00_Foundations-Architecture_at_a_Glance` SVGs render as inline figures so the following paragraph starts on the same line; they need to be block-level/centered.
- **More ASCII-art diagrams remain.** Pages 62 and 375 still contain monospace ASCII diagrams. A scan of `Manual/images/` found 16 SVGs using `Consolas`/`Courier` fonts, including:
  - `Part_01_Chapter_01_ECS-Actor_Lifecycle_Diagram-1.svg` and `-2.svg`
  - `Part_01_Chapter_05_Pathfinding_Movement-The_movement_stack-1.svg`
  - `Part_01_Chapter_06_Combat_Damage-The_combat_pipeline-1.svg`
  - `Part_02_Chapter_01_MiniYaml-The_Two_AST_Shapes.svg`
  - `Part_03_Chapter_02_SDK_Bootstrap-Architecture-1.svg`
  - `Part_04_Chapter_03_Widgets-Widget_tree-1.svg`
  - `Part_07_Chapter_01_Pipeline-Architecture-1.svg`
  - `Part_07_Chapter_02_Data_Structures-Interconnectivity-1.svg`
  - Three `Part_07_Chapter_03_Algorithms-*.svg`
  - `Part_07_Chapter_04_Terraformer-SliceElevation-1.svg`
  - `Part_08_Chapter_02_Bot_Modules-UnitBuilderBotModule-1.svg`
  - `Part_09_Chapter_01_OrderManager-Order_processing-1.svg`
  - `Part_09_Chapter_02_Server_Connection-Server_Connection_State_Machine.svg`
- **Generic generated diagrams need per-instance redesign.** Many of the above are auto-generated Mermaid/placeholder diagrams that do not specifically illustrate the concept in the chapter; they should be replaced with purpose-built graphics for each instance.
- **Terrain previews incomplete.** Only the templates currently listed in `Appendix_J_Terrain_Tiles.md` were rendered; the remaining unrendered tiles need to be added to the appendix and rendered.
- **Terrain table layout inconsistent.** The `Preview` column should be the left-most column and the tables should follow the same layout patterns as the Actor Reference where applicable.
- **Missing horizontal lines on spreadsheet page 758.** A table in the late appendix section (around page 758) is missing horizontal rules, likely because the table-formatting post-processor did not match its `longtable` pattern.

### Next steps
- Fix figure placement for the new architecture SVGs.
- Convert/replace the 16 remaining ASCII-font SVGs with custom graphics.
- Expand `Appendix_J_Terrain_Tiles.md` to cover all remaining templates, move the `Preview` column to the left, and align the table structure with the Actor Reference.
- Investigate the missing horizontal lines on the page 758 table and update `format_tables_vlines.py` if needed.
- Install Tiberian Sun content and re-run `extract_terrain_images.py`.

## 2026-06-29 — Terrain tile previews generated for Appendix J

### What was done
- **Added `OpenRA.Mods.Common/UtilityCommands/ExportTerrainTemplateCommand.cs`.** A new `--export-terrain-template TILESET TEMPLATE_ID OUTFILE` command that renders a tileset template (including multi-tile grids and PickAny variant grids) to a PNG. Handles indexed RA/CNC/TS tiles and truecolour D2K R16 tiles.
- **Built the OpenRA engine** with the new utility command (`make.cmd all` in the pinned engine source).
- **Created `build files/extract_terrain_images.py`.** Parses `Appendix_J_Terrain_Tiles.md`, calls the new utility command for each referenced template, and adds a `Preview` column to every "Representative Templates" table.
- **Generated 149 terrain preview PNGs** under `Manual/images/terrain/<mod>/<tileset>/`:
  - RA: desert (18), interior (5), snow (18), temperat (18)
  - C&C: desert (18), snow (18), temperat (18), winter (18)
  - D2K: arrakis (18)
- **Updated `Appendix_J_Terrain_Tiles.md`.** All 11 representative-template tables now include a `Preview` column with rendered images for the 149 successful templates.
- **Regenerated the combined manual.** Ran `assemble_manual.py`, `verify_paths.py`, and `verify_internal_links.py`; all passed.
- **Verified image references.** All 853 image references in the combined manual resolve to existing files.
- **Regenerated the PDF.** `OpenRA_Knowledge_Base_Manual.pdf` is now **768 pages, 13.44 MB**.

:### Open issues / blockers
- **36 Tiberian Sun template previews could not be rendered** because the Tiberian Sun game content (`C:\Users\Kmoney\AppData\Roaming\OpenRA\Content\ts`) is not installed. The `Preview` column cells for TS rows are empty until the content is installed and `extract_terrain_images.py` is re-run.

## 2026-06-29 — Tiberian Sun content installed; all terrain previews rendered

### What was done
- **Launched OpenRA with the Tiberian Sun mod.** Used the built engine at `OpenRA GitHub Repositories\OpenRA\bin\OpenRA.exe` with `Game.Mod=ts` and `Engine.EngineDir` pointing at the source root so the `mods/ts` manifest is found. The in-game content installer downloaded the TS assets to `C:\Users\Kmoney\AppData\Roaming\OpenRA\Content\ts`.
- **Fixed `extract_terrain_images.py` for re-runs.** Updated the row regex to parse tables that already have a `Preview` column, and added a `--force` flag to re-render all images.
- **Re-rendered all 185 terrain preview PNGs.** The run included the previously missing 36 Tiberian Sun templates (TS snow and temperate tilesets). No failures.
- **Updated `Appendix_J_Terrain_Tiles.md` preview cells.** All empty TS preview cells were filled with the rendered images.

### Next steps
- Regenerate the combined manual and rebuild the PDF to include the TS terrain previews.
- Continue with the remaining quality issues: figure placement for the new architecture SVGs, converting the 16 remaining ASCII-font diagrams, expanding terrain table coverage, and fixing the missing horizontal lines on page 758.

## 2026-06-29 — Final PDF polish pass (ASCII chart, tables, learning objectives)

### What was done
- **Replaced page 49 ASCII architecture chart with a proper graphical SVG.** `Manual/images/Part_00_Foundations-Architecture_at_a_Glance-1.svg` now uses colored rectangles and arrows instead of monospace ASCII art; the companion `Architecture_at_a_Glance-2.svg` (simulation pipeline) was also converted to a proper diagram.
- **Removed redundant learning-objectives diagrams.** Stripped the Mermaid mindmap image from every chapter header except `Part_00_Foundations.md` (45 removals), so the diagram appears only in the "How to Use This Manual" chapter.
- **Added vertical lines to all tables.** Modified the PDF pipeline to generate intermediate LaTeX, post-process `longtable` column specs with `format_tables_vlines.py`, and replace booktabs rules with `\hline`. Tables now show vertical lines between columns.
- **Updated the build pipeline.** `build_manual.ps1` now exports `.tex` from Pandoc, runs the table-formatting post-processor, and compiles with `lualatex`. Added `build files/format_tables_vlines.py`.
- **Regenerated the combined manual.** `OpenRA_Knowledge_Base_Manual.md` is now 58 chapters, 1,437,734 bytes.
- **Scaled actor unit sprites for visibility.** All `images/actors/*/*_unit.png` files were rescaled so the longest side is 64 pixels, so the in-world battlefield sprites remain readable after the PDF's global 0.55 figure shrink.
- **Regenerated the PDF.** `OpenRA_Knowledge_Base_Manual.pdf` is now **768 pages, 13.44 MB** (page count grew from the 149 terrain preview images and scaled actor sprites). Build completed with only the pre-existing `hyperref` undefined-reference warnings and the MiKTeX update reminder.

### Open issues / blockers
- **Tiberian Sun terrain previews missing content.** The TS game content (`Content/ts`) is not installed, so 36 TS template preview cells in Appendix J are empty. They will fill in once the content is installed and `extract_terrain_images.py` is re-run.

### Next steps
- Install Tiberian Sun content and re-run `extract_terrain_images.py` to fill the 36 empty preview cells, then rebuild the PDF.


## 2026-06-29 — ASCII chart conversion pass

### What was done
- **Restored `ascii_chart_to_svg.py`.** Moved the script from `Cameo Work/to delete/` back to `build files/ascii_chart_to_svg.py` and extended its detection to handle ASCII-only diagrams (`+----+`, `|    |`, arrows like `v`/`^`/`</>`), not just Unicode box-drawing characters.
- **Converted remaining ASCII chart code blocks to SVGs.** Processed 9 chapter files and converted 13 ASCII-art code blocks into SVG images:
  - `Part_00_Foundations.md` — 2 diagrams
  - `Part_01_Chapter_01_ECS.md` — 2 diagrams (actor lifecycle, Tick/Render loops)
  - `Part_01_Chapter_05_Pathfinding_Movement.md` — 1 diagram
  - `Part_01_Chapter_06_Combat_Damage.md` — 1 diagram
  - `Part_07_Chapter_01_Pipeline.md` — 1 diagram
  - `Part_07_Chapter_03_Algorithms.md` — 3 diagrams
  - `Part_07_Chapter_04_Terraformer.md` — 1 diagram
  - `Part_08_Chapter_02_Bot_Modules.md` — 1 diagram
  - `Part_09_Chapter_01_OrderManager.md` — 1 diagram
- **Verified no ASCII chart code blocks remain.** Scanned all chapters, appendices, and root Markdown files; only already-converted SVG references remain.
- **Regenerated the combined manual.** `OpenRA_Knowledge_Base_Manual.md` now references the new SVG images instead of inline ASCII code blocks.
- **Converted new SVGs to tight PDFs.** `convert_svgs_for_pdf.py` converted 13 new SVGs via Edge into the PDF cache.
- **Regenerated the PDF.** `OpenRA_Knowledge_Base_Manual.pdf` is now **776 pages, 14.1 MB**. The page count stayed the same because the SVGs are inline, but the visual coherence is improved (no more ASCII code blocks next to rendered diagrams). The `↔` missing-glyph warnings disappeared; only `≤`, `≥`, and `≈` in code blocks still warn.

### Open issues / blockers
- None.

### Next steps
- Optional: replace Latin Modern Mono with a font that has `≤`, `≥`, `≈` glyphs, or replace those characters with ASCII equivalents in code blocks.

## 2026-06-29 — Appendices J & K added, final PDF regenerated

### What was done
- **Added `Appendix_J_Terrain_Tiles.md`.** Catalogs per-mod tileset terrain types and representative templates for Red Alert, Tiberian Dawn, Dune 2000, and Tiberian Sun, including `Template` / `Tile` / `TerrainType` lookups, passability/buildability notes, and representative template tables.
- **Added `Appendix_K_Environmental_Actors.md`.** Catalogs environmental actors across the four official mods: vegetation, rocks/cliffs, civilian buildings, bridges, walls/gates, crates, resource spawns, and decorative props. Includes actor ID, name tooltip key, footprint size, key traits, and tileset/editor notes.
- **Updated `MASTER_INDEX.md`.** Added entries for Appendices J and K so the manual table of contents links to them.
- **Updated `assemble_manual.py`.** Added `Appendix_J_Terrain_Tiles.md` and `Appendix_K_Environmental_Actors.md` to the `FILES` list so the combined markdown includes the new appendices.
- **Regenerated the combined manual.** `OpenRA_Knowledge_Base_Manual.md` now contains 58 chapters, 1,455,297 bytes, and includes both new appendices.
- **Verified SVG cache.** `convert_svgs_for_pdf.py` reports all 345 SVGs are cached as tight PDFs; no new conversions were required.
- **Regenerated the PDF.** Final output is `OpenRA_Knowledge_Base_Manual.pdf` with **776 pages** and **13.91 MB**. Page count increased by ~28 pages from the new appendices, offset slightly by the ASCII-chart-to-SVG compaction from earlier in the session.
- **Note on warnings.** The PDF build emits the same `hyperref` undefined-reference warnings as previous builds (resolved by Pandoc's single-pass output) and a handful of missing-glyph warnings for Unicode arrows (`↔`), `≤`, `≥`, and `≈` inside code blocks where the Latin Modern Mono font lacks the characters. This is cosmetic; the PDF is complete and readable.

### Open issues / blockers
- None.

### Next steps
- Production polish pass (external review, PDF layout fine-tuning, optional second LaTeX pass to resolve `hyperref` warnings, optional monospace font replacement for missing math glyphs).


## 2026-06-29 — ASCII chart SVG conversion repair

### What was done
- **Restored `Part_07_Chapter_02_Data_Structures.md` from the combined manual.** The previous `ascii_chart_to_svg.py` run had corrupted the chapter by merging the Events-tied-to-layers C# block with the `MapGrid` YAML block and by embedding the `Interconnectivity` image reference plus CPos/MPos formulas inside the tree-diagram code block. Replaced the corrupted chapter with the original 7.2 section from `OpenRA_Knowledge_Base_Manual.md`, converted back to chapter-relative Markdown links.
- **Fixed `build files/ascii_chart_to_svg.py`.** Updated the fence regex to match code blocks with optional language tags (` ```csharp`, ` ```yaml`, bare ` ``` `) and use multiline anchors, so it only converts the actual ASCII-art block and does not swallow adjacent prose or other code blocks.
- **Converted only the ASCII-art block.** The `Interconnectivity` tree diagram in `Part_07_Chapter_02_Data_Structures.md` now renders as `![Interconnectivity](images/Part_07_Chapter_02_Data_Structures-Interconnectivity-1.svg)`. The C# event handler block and the CPos/MPos formula blocks remain as normal code blocks.
- **Verified existing conversions.** Confirmed the previously generated SVGs for `Part_02_Chapter_01_MiniYaml-The_Two_AST_Shapes`, `Part_03_Chapter_02_SDK_Bootstrap-Architecture-1`, `Part_04_Chapter_03_Widgets-Widget_tree-1`, and `Part_09_Chapter_02_Server_Connection-Server_Connection_State_Machine` contain correct ASCII art and are referenced properly.
- **Moved corrupted/invalid SVGs to the safe-deletion area.** Relocated `Part_07_Chapter_02_Data_Structures-Events_tied_to_the_layers-1.svg`, `-Interconnectivity-2.svg`, and `-CPos__MPos_for_Isometric_Maps-3.svg` to `C:\Users\Kmoney\Documents\AI Projects\Cameo Work\to delete\`.
- **Regenerated the combined manual.** Ran `assemble_manual.py` so `OpenRA_Knowledge_Base_Manual.md` reflects the restored chapter and the new Interconnectivity SVG reference.
- **Regenerated PDFs for the affected SVGs.** Ran `convert_svgs_for_pdf.py` with Edge; it converted the new/changed SVGs (5 total) to tight PDFs in `build files/svg-pdf-cache/`.
- **Verified chapter integrity.** Ran a fence-balance check across all five affected chapters; all code blocks are balanced and no image references are misplaced inside code blocks.

### Open issues / blockers
- None.

### Next steps
- Continue the production polish pass (PDF layout, external review, etc.).

## 2026-06-29 — PDF layout fixes (TOC, headings, images, cover page)

### What was done
- **Fixed duplicated appendix headings:** cleaned up headings like `# Appendix A — Glossary — Glossary` to `# Appendix A — Glossary` across all appendix source files.
- **Removed duplicate TOC:** the manual's own Markdown "Table of Contents" section is now stripped by the PDF Lua filter so Pandoc generates the only TOC (with page numbers).
- **Added proper title page and TOC title:** passed `-V title="OpenRA Knowledge Base Manual"` and `-V toc-title="Table of Contents"` to Pandoc, so page 1 is the title page, page 2 is "Table of Contents", and the old "Table of Contents" on page 41 is gone.
- **Scaled and centered images:** added `adjustbox` defaults in `header.tex` so SVG/PDF figures fit within text width and page height, keep aspect ratio, and center on the line.
- **Forced figures inline:** added `float` package and `\floatplacement{figure}{H}` so captioned figures no longer float to their own pages.
- **Built custom cover page:** replaced the default title page with a full-page design featuring the OpenRA logo, title, subtitle, dedication, and Tiberian Dawn / Dune 2000 mod icons at the bottom corners. Added 512x512 and 256x256 icon assets to `build files/icons/`.
- **Found and fixed the page-count blowup:** the Edge print-to-PDF conversion was producing US Letter-sized PDFs (612x792) even for small SVGs, so every figure was rendered nearly full-page and forced to its own sheet. Switched the converter to wrap each SVG in an HTML page with `@page { size: <viewBox-w>pt <viewBox-h>pt; margin: 0; }`, so cached PDFs are now tightly sized to the SVG content. Reconverted all 340 SVGs.
- **Shrunk figures by ~45%:** patched Pandoc's `\pandocbounded` macro to wrap images in `\scalebox{0.55}`, so diagrams sit inline with the text instead of dominating the page.
- **Regenerated PDF:** `OpenRA_Knowledge_Base_Manual.pdf` (14.4 MB, 748 pages) with the cover page, inline-figure layout, tight-bounding-box SVGs, and shrunk figures applied.

### Next steps
- Build **Appendix J — Terrain Tile Reference** (ground tiles, terrain types, passability/buildability, grouped by mod).
- Build **Appendix K — Environmental Actor Reference** (flora, rocks, houses, bridges, wells, etc., grouped by mod, with grid size).

## 2026-06-29 — Round 1/2 polish pass, UNLICENSE, and export pipeline

### What was done
- **Updated `BUILD_PLAN.md`** to reflect actual completion: all Phase 0–10 checkboxes marked complete, added extra chapters (Pathfinding/Movement, Combat/Damage, SDK Bootstrap) and extra appendices (F–I), and updated Phase B/C/D/E/F status. The plan now accurately documents the current production-polish phase instead of the original unfinished state.
- **Fixed maintenance issues:** added `## Summary` to `Part_00_Foundations.md`, fixed the inconsistent relative path in `Appendix_A_Glossary.md` line 49, and verified that all code fences already have language tags (no bare opening fences found).
- **Consolidated order/bot-order flow redundancy** across `Part_01_Chapter_03_World_Orders.md`, `Part_08_Chapter_04_Order_Flow.md`, and `Part_09_Chapter_01_OrderManager.md`. Each chapter now has a clearly scoped role: Part 1.3 = Order anatomy from UI/player perspective, Part 9.1 = canonical lockstep pipeline, Part 8.4 = bot order construction and issuing. Cross-references added between all three.
- **Deepened Part 4 (Rendering/UI)** with `## Mental Model` sections, expanded practical examples (sprite wiring, range circle, event propagation, ping order generator), additional diagram prompts, and stronger cross-references to Part 1.1, Part 2.4, Part 6.3, Part 7.8, and Part 10.3.
- **Deepened Part 10.3 (Porting, Modding, and Developer Workflows)** with a `## Mental Model` section, a complete "From zero to first custom unit" end-to-end example (SDK setup, actor/weapon/sequence/build queue, validation, launch), a `Common Pitfalls Checklist`, a `How to debug a broken actor definition` workflow, and a `How to find the trait you need` section. Heavy cross-referencing to Part 2.1, Part 2.4, Part 3.1/3.2, Part 4.3, Part 6.1, Appendix B, Appendix E, and Appendix I.
- **Addressed Round 2 high-priority items** outside Part 4/10.3: added visual-aid diagram prompts to Part 1.1 (actor lifecycle), Part 1.2 (activity state machine), Part 6.3 (VFS flow), and Part 7.1 (RMG pipeline). Added `## Summary` sections to Appendices A–E. Added practical examples to Part 6.3 and Part 7.1. Added more cross-references throughout.
- **Added `UNLICENSE`** to the project root with a third-party asset disclaimer. Updated `Manual/README.md` to document the license and attribution. The project text/scripts/original diagrams are public domain; game assets remain property of their respective owners.
- **Created a sustainable export pipeline:** added `build files/build_manual.ps1` to run assemble + verify + optional Pandoc export in one command, and `build files/EXPORT_PIPELINE.md` documenting the Pandoc vs. Claude workflow. The pipeline is designed to be repeatable for future OpenRA updates.
- **Improved `build_manual.ps1`:** auto-detects Pandoc in common Windows install locations (`C:\Program Files\Pandoc\pandoc.exe`, Chocolatey, PATH) and auto-detects a LaTeX engine (`xelatex`/`lualatex`/`pdflatex`) for PDF export, with clear warnings if dependencies are missing.
- **Installed Pandoc:** user installed Pandoc 3.10 at `C:\Program Files\Pandoc`. Script updated to use it.
- **Started MiKTeX installation:** downloaded `basic-miktex-25.12-x64.exe` and the `miktexsetup` command-line utility to provide a LaTeX engine for PDF export.
- **Updated `EXPORT_PIPELINE.md`** with dependency notes, the Pandoc/Claude workflow breakdown, and the generated-artifact section.
- **Added `build_manual.bat`** Windows batch wrapper for `build_manual.ps1` that auto-elevates to Administrator and bypasses PowerShell execution-policy restrictions.
- **Started production design phase:** created `DESIGN_BRIEF.md` and `sample_styles.md`/`sample_styles.docx` to produce the Pandoc `reference.docx` template.
- **Applied first PDF design pass:** tightened margins to 0.75in, added custom LaTeX header (`header.tex`) with page headers, footer page numbers, and RA/C&C/D2K mod icons, styled tables and code blocks, and set `FONTCONFIG_PATH` for the bundled `rsvg-convert`.
- **Fixed figure captions and cross-references:** replaced truncated image alt texts with concise captions, converted unlinked appendix/part references to Markdown links, and verified 0 broken internal links.
- **Fixed SVG figure text rendering:** installed Microsoft Edge, added `convert_svgs_for_pdf.py` and `svg-to-pdf.lua` to convert SVGs to PDFs via Edge headless mode so foreignObject/HTML labels render correctly in the PDF.
- **Generated final PDF:** `OpenRA_Knowledge_Base_Manual.pdf` (23.7 MB) with correct margins, headers/footers, mod icons, hyperlinks, and readable figure text.
- **Added root `README.md`:** created a GitHub-facing project README at the repository root with quick links, build instructions, contributing guidelines, and license/attribution notes.
- **Updated `Manual/README.md`:** added GitHub/transparency section and internal documentation cross-references.
- **Expanded `EXPORT_PIPELINE.md`:** added detailed Pandoc vs. Claude breakdown, dependency installation instructions, and design-layer philosophy.
- **Ran final verification:** `assemble_manual.py` → 56 chapters, 1,435,908 bytes; `verify_paths.py` → 275 paths, 0 missing; `verify_internal_links.py` → 2,020 links, 0 broken.

### Open issues / blockers
- MiKTeX installation in progress (basic package set download via `miktexsetup`). Once complete, PDF export can be tested with `build_manual.ps1 -Export pdf`.
- The manual directory is not a git repository. For GitHub publishing, the user will need to create a new repository and push the contents; all original work is UNLICENSED and game assets are clearly attributed as fair-use reference material.

### Next steps
- Complete MiKTeX installation and verify PDF export.
- Run a third round of external AI feedback on the combined manual.
- After triage, apply any final fixes and move to the production export phase (Pandoc + reference template design pass).

### Next steps
- Run a third round of external AI feedback on the combined manual.
- After triage, apply any final fixes and move to the production export phase (Pandoc + reference template design pass).

## 2026-06-28 — Engine-execution verification runbook completed (Parts 0–4)

### What was done
- Ran the four-part engine-execution runbook against the pinned OpenRA source at commit `972c10ec80f90a30a4fa80abfebc633af3365847` (playtest/`bleed` line).
- **Part 0 — Build:** `make.cmd all` succeeded (0 errors, 0 warnings in the initial build; 6 `MSB3026` retry warnings during the C# snippet re-build, all non-fatal).
- **Part 1 — Baseline YAML validation:** `OpenRA.Utility.exe ra --check-yaml`, `cnc --check-yaml`, and `d2k --check-yaml` all completed with exit code 0 and no error lines.
- **Part 2 — Snippet-specific YAML validation:** created a throwaway `manual-test` map in `AppData\Roaming\OpenRA\maps\ra\manual-test` and loaded the three `yaml-snippets.md` blocks (custom crate rewards, capture/engineer, turtle AI bot). `utility.cmd ra --check-yaml` on the map passed with exit code 0.
- **Part 3 — Lua mission load validation:** assembled a `manual-mission` map in `AppData\Roaming\OpenRA\maps\ra\manual-mission` using the Appendix H template, copied the required `campaign.lua` from `mods/ra/scripts/campaign.lua`, and used a compatible 96×96 TEMPERAT `map.bin` from `fort-lonestar`. `utility.cmd ra --check-yaml` passed with exit code 0. The actual in-game play-through (objective display, attack wave, win/loss) is left to the user because the shell has no GUI.
- **Part 4 — C# compile:** dropped the four manual C# test files (`GrantConditionOnLowHealth`, `CashOnCreated`, `MyPanelLogic`, `MyPanelHotkeyLogic`) into the engine source under `OpenRA.Mods.Common`, ran `make.cmd all`, and confirmed **Build succeeded with 0 errors**. Files were then moved out of the engine source to the `to delete` staging folder.

### Findings
- The manual's YAML and C# snippets are **accepted by the pinned engine**.
- The Appendix H Lua mission example had a bug in its `map.yaml` actor list: `Actor5: Waypoint1` and `Actor6: EnemyEntry` used non-existent actor types. Corrected to `Waypoint1: waypoint` and `EnemyEntry: waypoint`, moved `EnemyEntry` from `80,80` to `79,79` so it lies inside the `Bounds: 16,16,64,64` rectangle, and added a `SpawnUSSR: mpspawn` actor (owner `Neutral`) so the mission satisfies the validator.
- **Additional in-game bug found by user:** the objective text displayed as the raw key `destroy-enemy-factory` because the walkthrough did not include a Fluent translation file. Fixed by adding `map.ftl` with `destroy-enemy-factory = Destroy the German weapons factory.`, loading it via `FluentMessages: ra|fluent/lua.ftl, ra|fluent/campaign.ftl, map.ftl` in `map.yaml`, and documenting the requirement in the walkthrough, the common pitfalls, and the `.oramap` packaging list.
- **Briefing bug found by user:** the mission briefing showed the wrong text (Einstein rescue) because the walkthrough did not include a `MissionData` briefing. Fixed by adding `MissionData: Briefing: briefing` to `rules.yaml`, adding the `briefing` translation to `map.ftl`, and documenting that missing `MissionData` can cause the mission selector to show the previous mission's briefing.
- **Extra MCV / crash bug found by user:** the player started with both a placed Construction Yard and an extra MCV, and later the game crashed on the enemy tooltip with `Invalid bot type: campaign`. Root cause: the `campaign` bot and the `SpawnStartingUnits` / `MapStartingLocations` removals live in `ra|rules/campaign-rules.yaml`, which the walkthrough was not reliably loading in all test environments. Fixed by adding `ModularBot@CampaignAI` directly to the map's `rules.yaml`, updating the `map.yaml` `Rules:` line to load the full campaign rules (`ra|rules/campaign-rules.yaml`, `ra|rules/campaign-tooltips.yaml`, `ra|rules/campaign-palettes.yaml`), removing the workaround `mpspawn` actor, and documenting the campaign-rules requirement.
- **No money bug found by user:** the player started with `0` credits because `campaign-rules.yaml` sets `PlayerResources.DefaultCash: 0`. Fixed by overriding `PlayerResources.DefaultCash: 5000` in the map's `rules.yaml`.
- **Sell Conyard exploit found by user:** selling the Construction Yard did not lose the mission because `Trigger.OnKilled` only fires on destruction, not on sale or capture. Fixed by using `Trigger.OnRemovedFromWorld` for destroyed/sold buildings and `Trigger.OnCapture` for captured buildings, and updating the `Tick` fallback to check `Actor0.IsDead` and `Actor0.Owner`. Updated the manual, the `engine-tests/lua-mission/` test files, and the runbook, and added a note explaining why `OnRemovedFromWorld`/`OnCapture` must be used instead of `OnKilled` for buildings that must survive.
- **Cameo export run:** rebuilt the OpenRA engine and ran `extract_cameos.ps1`. Results: RA 91/91 real cameos extracted, CNC 54/54 real cameos extracted, D2K 0/45 real cameos extracted (D2K content `DATA.R16` not installed). Fixed the script to call `bin\OpenRA.Utility.exe` directly with `ENGINE_DIR`, add a `--extract` step before `--png`, and replace em dashes with hyphens in `Write-Host` strings. Updated the script's header comments. Manual verification passed after the export.
- **D2K cameo extraction solved:** implemented a custom OpenRA utility command `--export-sequence-frame` in `OpenRA.Mods.Common/UtilityCommands/ExportSequenceFrameCommand.cs` that loads the D2K sequence set and exports the exact icon frame from the shared `DATA.R16` container. Updated `extract_cameos.ps1` to use this command for D2K and added a fallback mapping from actor code to the faction-specific sequence image (e.g., `construction_yard` -> `conyard.ordos`). Re-ran the script. Results: RA 91/91 real cameos, CNC 54/54 real cameos, D2K 43/45 real cameos (only `mpsardaukar` and `nsfremen` remain placeholders because they have no `icon` sequence). Manual verification passed.
- **Cameo extraction polish:** extended `--export-sequence-frame` to all mods (RA, CNC, D2K). Fixed palette loading to read `temperat.pal`/`PALETTE.BIN` from the mod's file system instead of the current working directory. Fixed RA/CNC weapons factory (`weap`) and other structure cameos being cut off by using the engine's sequence loader, which correctly resolves the `icon` filename (e.g., `weapicon.shp`) rather than the default `weap.shp` used by the old `--png` parsing. Re-ran the script; counts: RA 78/91 real cameos (13 fake/placeholder actors have no icon), CNC 54/54 real cameos, D2K 43/45 real cameos. Manual verification passed.
- **Dual images (battlefield sprite + construction-menu cameo) + final purple fix:** the D2K purple hue was a red<->blue channel swap introduced by reading the cameo back through the texture sheet (`Sheet.AsPng` + premultiply). Rewrote `ExportSequenceFrameCommand` to read the raw `ISpriteFrame` directly: indexed SHP frames (RA/CNC) get the supplied palette, truecolour D2K R16 frames are written as-is (the loader already baked in the correct colour). Verified numerically — D2K `light_inf` icon went from avgR=81/G=106/B=132 (purple) to avgR=132/G=106/B=81 (warm tan). Added a `@unit` auto-pick mode that exports the first available in-world sequence (`idle`/`stand`/`turret`/...), skipping intentionally-empty placeholder frames (e.g. turret defences). Updated `extract_cameos.ps1` to export both `<code>.png` (icon) and `<code>_unit.png` (battlefield sprite) for every actor, and `generate_actor_reference.py` to add a "Unit" column next to "Cameo" plus dual placeholders. Final: RA 78 icons / 78 units, CNC 54 / 54, D2K 43 / 40 (the few misses are fake structures, faction duplicates, concrete slabs and the death-hand missile, which have no standalone art and keep placeholders). Manual verification passed: 56 chapters, 275 paths, 1931 internal links, 0 broken.
- **Battlefield sprite visual polish:** fixed two remaining defects in the `@unit` export. (1) Buildings that are split across a base sequence and an overlay sequence (RA `proc` + `idle-top`, RA/CNC `weap` + `build-top`, D2K structures with `idle-top`) are now composited into a single complete sprite instead of exporting only the cut-off body. (2) Ground shadows are now made transparent: RA/CNC player-palette shadow index 4 is dropped, and the D2K R16 translucent black shadow pixel is dropped. (3) D2K true-colour remap markers are recoloured to a neutral blue-grey via the loader's `RemappableFrame.WithSequenceFlags` so units don't show raw house-colour reference pixels. Re-ran `extract_cameos.ps1`; counts stayed the same but all regenerated battlefield sprites are now complete and shadow-free. Manual verification passed: 56 chapters, 1,397,451 bytes, 275 paths, 1931 internal links, 0 broken.
- The `LuaScript` `Scripts:` field in the example was already correct (`campaign.lua, utils.lua, map.lua`). For the command-line validation, `utils.lua` was copied from `mods/common/scripts/` to the test map folder so the prepared map matches the written example.

### Open issues / blockers
- None for the engine-execution runbook. The only remaining step is the GUI play-through in Part 3.

### Next steps
- User launches the `manual-mission` map to confirm the objective, attack wave, and win/loss conditions work in-game.
- Manual verification commands were run successfully after the edits: `assemble_manual.py` → 56 chapters, 1,382,821 bytes; `verify_paths.py` → 275 paths, 0 missing; `verify_internal_links.py` → 1,741 links, 0 broken.

## 2026-06-25 — Appendix I: Actor Reference (auto-generated, with cameos)

### What was built
- New appendix **`appendices/Appendix_I_Actor_Reference.md`** — deep per-actor tables for every buildable actor in the three bundled OpenRA mods: **Red Alert (91), Tiberian Dawn (54), Dune 2000 (45) = 190 actors**. Columns: cameo, code, name, faction, cost, HP, armor, speed, sight, weapon(s), notable traits. Grouped per mod → Infantry/Vehicle/Aircraft/Naval/Building.
- The data is **auto-generated from the pinned engine source**, not hand-written, so it can't drift: `build files/generate_actor_reference.py` parses each mod's `rules/*.yaml` (resolving `Inherits:` chains, `@` instances, and `-Trait` removals) and `fluent/rules.ftl` (display names), and emits the appendix + a faction-tinted placeholder cameo per actor + `actor_manifest.json`.
- **Cameos:** real cameos render from the original game art, which is only present where the OpenRA content is installed (not in the engine source), so they can't be produced in the doc sandbox. Every slot currently holds a **placeholder PNG** (labelled, faction-tinted) at `images/actors/<mod>/<code>.png` so the manual is complete and link-valid now. `build files/extract_cameos.ps1` (Windows) replaces them with real cameos via `OpenRA.Utility.exe <mod> --resolved-sequences <code>` (to find each `icon` sequence) + `--png <file> <palette>` (ra/cnc palette `temperat.pal`, d2k `PALETTE.BIN`; d2k cameos are frames inside a shared `DATA.R16`).
- Wired into `assemble_manual.py` (now **56 files**) and `MASTER_INDEX.md`.

### Verification
- Appendix I checked in isolation: **190 cameo image links + 3 cross-references, 0 broken**; placeholder file counts match the manifest exactly (ra 91 / cnc 54 / d2k 45).
- Full in-sandbox re-assembly remains **blocked by the Cowork file-cache bug** (bash sees a truncated copy of files edited via the file tools, including `assemble_manual.py`). Host files are correct; regenerate on Windows. Expected Windows counts: 56 chapters; ~1,739 internal links / 0 broken; ~275–276 paths / 0 missing.

### Notes
- Scope is **OpenRA's three bundled mods only** (not Cameo or Combined Arms). A separate "layered" Cameo edition is a future, post-v1.0 project per the author.
- Stats are raw engine values (HP ~100× the classic number; Speed in engine units; Sight/Range in cells). This is documented in the appendix's "How to read these tables" section.
- Licensing: OpenRA's own art is openly licensed; classic Westwood/EA cameos are freeware, shown here as fair-use educational reference with attribution + a "not endorsed by EA" note (built into the appendix).

## 2026-06-25 — Technical Verification & Proofreading pass (Claude #1)

### Environment and version pinning
- **Target pinned:** OpenRA development branch **`bleed`**, commit **`972c10ec80f90a30a4fa80abfebc633af3365847`** (the manual's own Part 0 version note already states tag `playtest-20260222-76-g972c10ec80`, whose `g972c10ec80` matches this HEAD — so the manual is self-consistently pinned to the **playtest** line, not release).
- **Why playtest, not release:** the source clone used for `verify_paths.py` and every snippet is this `bleed` checkout (its `VERSION` file is the `{DEV_VERSION}` placeholder). Verifying against release docs would produce false field/path mismatches. Playtest is the internally consistent target.
- **Verification method:** snippets were checked **statically against the pinned source tree** (trait/weapon classes, field names, C# interfaces, Lua bindings). This is authoritative for the pinned commit because docs.openra.net is auto-generated from the same `[Desc]` attributes in that source. **No snippet was executed** — this session ran in a Linux sandbox with **no .NET/mono runtime**, so `OpenRA.Utility.exe --check-yaml`, C# compilation, and launching a `.oramap` mission could not be run here. Those remain to be executed on a Windows machine (see "Untested / to run on Windows").

### Technical errors found and fixed
1. **Part 9.2 — Server and Connection Layer** (multiple path/field drift errors):
   - `OpenRA.Game/Server/ServerTraits/*.cs` → corrected to `OpenRA.Game/Server/TraitInterfaces.cs` (that directory does not exist; the server-trait interfaces `IStartGame`, `IInterpretCommand`, `INotifySyncLobbyInfo`, etc. live in `TraitInterfaces.cs`). Fixed in both the Files table and the body.
   - `OpenRA.Mods.Common/ServerTraits/...` (a literal `...` ellipsis that only "resolved" on Windows due to trailing-dot stripping) → corrected to `OpenRA.Mods.Common/ServerTraits/*.cs` with the **actual** files (`LobbyCommands`, `MasterServerPinger`, `PlayerPinger`, `SkirmishLogic`). The example classes `VoteKickTracker`/`PlayerMessageTracker` were wrongly attributed here; they live in `OpenRA.Game/Server/` and are now listed separately.
   - Removed `IClientDisconnected` (does not exist in the engine); kept `IClientJoined` and noted disconnects are handled by connection-drop logic / `INotifyServerEmpty`.
   - Rewrote the **Slot/Client model**: the `Slot` class holds `PlayerReference, Closed, AllowBots, LockFaction, LockColor, LockSpawn`; the occupying `Client` holds `Color, Faction, SpawnPoint, Bot` and links via its `Slot` field. The manual previously claimed `Slot` had `ClientIndex`/`Bot`/`Color`/`Race` — `Race` is the long-removed name for `Faction`, and there is no `Slot.ClientIndex`. Updated the prose, the state table, and the "claims a slot" paragraph accordingly.
2. **Part 8.2 — Bot Modules:** `CaptureManagerBotModule` was described as tracking `ExternalCaptures` or `Captures` traits. `ExternalCaptures` no longer exists (unified into `Captures`/`CaptureManager`); corrected to "the `Captures` trait." Confirmed against `CaptureManagerBotModule.cs`.
3. **Appendix H, Walkthrough 2 — Lua mission template (mission-breaking bug):** the map's `rules.yaml` used `LuaScript: Script: map.lua`. The trait's field is **`Scripts`** (a comma-separated list), not `Script`, and it **must include the shared `campaign.lua` and `utils.lua`** that define the helpers used in the script (`InitObjectives` is in `mods/ra/scripts/campaign.lua`; `AddPrimaryObjective` is in `mods/common/scripts/utils.lua`). Corrected to `Scripts: campaign.lua, utils.lua, map.lua` (matching real RA campaign maps, e.g. `allies-01`), added an explanatory paragraph, and added a common-pitfall entry. Note: `MarkCompletedObjective`/`MarkFailedObjective` are engine bindings (`MissionObjectiveProperties.cs`), so they need no shared script — the text reflects this distinction.

### Snippets verified correct (no change needed)
- **Part 0 — Foundations** C# trait `GrantConditionOnLowHealth`: `TraitInfo`/`Requires<IHealthInfo>`, `[GrantedConditionReference]`, `INotifyCreated.Created`, `INotifyDamage.Damaged(Actor, AttackInfo)`, `IHealth.HP/MaxHP`, `Actor.InvalidConditionToken`, `GrantCondition`/`RevokeCondition` — all match source.
- **Appendix E, Recipe 6** C# trait `CashOnCreated`: `TraitInfo.Create`, `INotifyCreated`, `self.Owner.PlayerActor.Trait<PlayerResources>()`, `PlayerResources.GiveCash(int)` — all match source. (`CashOnCreated` is correctly a user-defined custom trait, not an engine trait.)
- **Appendix H, Walkthrough 1** Chrome UI C#: `ChromeLogic`, `[ChromeLogicArgsHotkeys]` (OpenRA.Mods.Common.Lint), `[ObjectCreator.UseCtor]`, `Ui.OpenWindow/CloseWindow`, `LogicKeyListenerWidget.AddHandler`, `HotkeyReference.IsActivatedBy`, `ModData.Hotkeys`, `KeyInputEvent.Down` — all match source. Hotkey YAML format matches real `ra/hotkeys.yaml`.
- **Appendix H crate walkthrough:** `GiveUnitCrateAction.Units` (plural) is correct for the pinned engine.
- **Appendix H capture walkthrough:** `Captures`/`CaptureManager`/`Capturable` fields (`CaptureTypes`, `EnterCursor`, `EnterBlockedCursor`, `BeingCapturedCondition`, etc.) all verified; the walkthrough already correctly states `ExternalCaptures` no longer exists.
- **Appendix H custom-resource walkthrough:** `ResourceLayer`/`ResourceRenderer` `ResourceTypes` sub-fields (`ResourceIndex`, `TerrainType`, `AllowedTerrainTypes`, `MaxDensity`, `Sequences`, `Palette`, `Name`) all verified.
- **Part 2.4 — Rules & Weapons:** the `E1` actor and `^HeavyMG` weapon blocks are verbatim, accurate copies of `mods/ra/rules/infantry.yaml` and `mods/ra/weapons/smallcaliber.yaml`.
- **Trait-name scan** across Appendix E, Appendix H, Part 2.4, Part 10.3, and Appendix B against the engine's full trait set surfaced no further unknown traits (remaining flagged tokens are nested fields, widget node types, manifest sections, or actor/weapon names).

### Proofreading
- **Heading hierarchy:** scanned all 55 source files — **0 skipped heading levels**.
- **Doubled words:** no real typos (the only matches are ASCII bit-pattern diagrams like `XXXX XXXX`).
- **Code-block language tags:** all 267 C#, 201 YAML, 11 bash, and 2 Lua blocks are correctly tagged. 118 **bare** code fences remain — every sampled one is an intentional ASCII diagram (box diagrams, dependency trees, data-flow), which render correctly untagged. Mass-tagging them `text` was deliberately **deferred** as a low-value cosmetic change (and to avoid churning ~40 files under the sandbox file-cache bug noted below). Listed as an optional follow-up.
- Minor wording fix: Part 9.2 `MapPreview` now reads "lightweight, cacheable map summary" (consistent with its other mention in the same chapter).

### Verification status (IMPORTANT — read before trusting in-session counts)
- **Baseline run (before edits), in the sandbox:** `assemble_manual.py` → 55 chapters, **1,318,383 bytes** (this is the LF byte count; the handoff's **1,343,193** is the CRLF/Windows count — the 24,810-byte difference equals the line count exactly, i.e. pure CRLF→LF, content is identical). `verify_internal_links.py` → **1,546 links, 0 broken**. `verify_paths.py` (adapted to the mounted source) → **275 paths**, the only "missing" being the `ServerTraits/...` ellipsis artifact, now removed.
- **Sandbox file-cache bug:** after editing `Part_09_Chapter_02_Server_Connection.md` via the file tools, the Linux sandbox's mounted view of that one file became **stale/truncated** and would not refresh (the known Cowork virtiofs/FUSE staleness bug). As a result, **a clean in-sandbox re-assembly/re-verify of the edited state was not possible.** The **source files on disk are correct** (verified via the file tools, which read the host directly). My edits add/remove **no** Markdown internal links, and every changed source-path reference was individually confirmed to exist in the pinned tree via direct lookup (`TraitInterfaces.cs` ✓, `OpenRA.Game/Server/` ✓), so link/path verification outcomes (0 broken, 0 missing) are preserved and in fact improved (the `...` artifact is gone).
- **Action required on Windows:** run the three verification commands (`assemble_manual.py`, `verify_paths.py`, `verify_internal_links.py`) on the Windows machine to regenerate the combined manual and confirm authoritative counts. Expect ~1,343,xxx bytes (CRLF), 55 chapters, 1,546 links / 0 broken, and ~275–276 paths / 0 missing (the path count may shift by one or two because of the Part 9.2 path corrections).

### Untested / to run on Windows (engine execution)
- `OpenRA.Utility.exe ra --check-yaml` on a test mod containing the Appendix E / Appendix H / Part 2.4 / Part 10.3 YAML snippets.
- C# compilation of the three custom-trait snippets (Part 0, Appendix E Recipe 6, Appendix H Chrome UI) against the `bleed` engine.
- Building a real `.oramap` from the Appendix H Lua mission template and starting it (confirm `WorldLoaded`, `Trigger`, `Reinforcements`, objectives) — now that the `Scripts:` field is corrected, this should load.

### Open questions for the user
- Confirm the **playtest (`bleed`) pin** is acceptable for v1.0, or whether v1.0 should instead target a **tagged release** (which would require re-verifying every snippet against a release checkout).
- Whether to tag the 118 ASCII-diagram fences as `text` (cosmetic) in a later pass.

## 2026-06-25 — Added Appendix H: Advanced Modding Walkthroughs

### What was done
- Created `build files/appendices/Appendix_H_Advanced_Modding_Walkthroughs.md` with nine complete, copy-paste-friendly advanced modding walkthroughs.
- Covered the critical gaps identified in the external-resource audit and internal audit: custom Chrome UI panels, single-player Lua missions, custom crates, custom resources, shroud/fog customization, capture/engineer mechanics, cloak/stealth, voxel units, and custom YAML AI bots.
- Each walkthrough follows the existing Practical Modding Recipes format: goal, prerequisites, files to edit, complete examples, how it works, verification, and common pitfalls.
- Integrated Appendix H into the manual:
  - Added to `assemble_manual.py` and `MASTER_INDEX.md`.
  - Added cross-references in `Part 04_Chapter_03_Widgets.md`, `Part 06_Chapter_01_Lua_Eluant.md`, `Part 06_Chapter_02_ScriptContext.md`, `Part 08_Chapter_02_Bot_Modules.md`, `Part 10_Chapter_03_Port_And_Modding.md`, and `Appendix_E_Practical_Recipes.md`.
- Spot-checked the new examples against the OpenRA engine source to confirm trait/class names (`CaptureManager`, `Cloak`, `RenderVoxels`, `ModularBot`, `GrantConditionOnBotOwner`, `ResourceLayer`, `Shroud`, etc.) and YAML fields.
- Regenerated `OpenRA_Knowledge_Base_Manual.md` and ran all verification scripts:
  - `assemble_manual.py`: 55 files, 1,343,193 bytes
  - `verify_paths.py`: 275 source paths, all exist
  - `verify_internal_links.py`: 1,546 internal links, all resolve

### Open issues / blockers
None.

### Next steps
- Continue the remaining improvement-plan items (self-assessment prompts, additional diagrams where helpful, further gap-filling if needed).
- Re-run the verification scripts after any further manual edits.

## 2026-06-25 — Polish pass on Summary sections and glossary links

### What was done
- Audited all chapter and appendix source files for malformed `## Summary` sections.
- Fixed 33 malformed Summary sentences across 33 chapter/appendix source files, replacing broken openings such as "This chapter openRA...", "This chapter the OpenRA...", missing verbs, and stray `<!-- DEV-NOTE` HTML comments with proper summary sentences.
- Removed visible `<!-- DEV-NOTE [tooling]: ... -->` HTML comments from Summary and Purpose sections in:
  - `Part_03_Chapter_03_Build_Packaging.md` (Microsoft .NET SDK)
  - `Part_05_Chapter_01_Audio_Architecture.md` (OpenAL Soft)
  - `Part_05_Chapter_02_Spatial_Attenuation.md` (OpenAL Soft)
- Moved those external-tool references to new `### External resources` sections at the end of the affected chapters.
- Added a missing `## Summary` section to `Part_07_Chapter_09_File_Index.md`.
- Verified glossary links already use the correct relative paths (`../appendices/Appendix_A_Glossary.md` from chapters, `Appendix_A_Glossary.md` from appendices); no changes were required.
- Regenerated `OpenRA_Knowledge_Base_Manual.md` and ran all verification scripts:
  - `assemble_manual.py`: 54 files, 1,294,028 bytes
  - `verify_paths.py`: 275 paths, all exist
  - `verify_internal_links.py`: 1,502 links, all resolve

### Open issues / blockers
None.

### Next steps
- Re-run the verification scripts after any further manual edits.

## 2026-06-25 — Added Appendix G: Asset Visual Reference

### What was done
- Created `build files/appendices/Appendix_G_Asset_Visual_Reference.md` with categorical tables for every OpenRA asset type.
- Covered the required categories: sprites/sequences, terrain/tilesets, palettes, cursors, chrome/UI, audio, voices, notifications, music, maps, fonts, translations, videos, voxels, and MIX/package archives.
- Each table row follows the requested format: Asset, File Format(s), Definition YAML, Engine Loader / Class, Visual Preview, Notes.
- Used textual visual placeholders to avoid embedding copyrighted art.
- Added Appendix G to `assemble_manual.py`, `MASTER_INDEX.md`, and `Appendix_A_Glossary.md`.
- Added cross-references to Appendix G in relevant chapters: Part 2.2 (Manifest), Part 4.1 (Renderer), Part 4.3 (Widgets/Chrome), Part 5.1 (Audio Architecture), Part 5.4 (Sound Triggers), Part 6.3 (VFS), Part 6.5 (Asset Loaders), Part 10.3 (Porting/Modding), and Appendix B (Common YAML Patterns).
- Enhanced Part 0 — Foundations: How to Use This Manual with a reference-sections overview pointing to the appendices, Master Index, and Asset Visual Reference.
- Verified the combined manual: 54 files, 1,293,424 bytes, 275 paths, 1,502 links — all pass.

### Open issues / blockers
None.

### Next steps
- Re-run the verification scripts after any further manual edits.

## 2026-06-24 — Round 2 Post-Scrutiny and Production Prep

### What was done
- Applied Round 2 AI feedback (Gemini/Grok/ChatGPT).
- Added `## Summary` to 45 chapters/appendices.
- Fixed the Part 0 custom-trait example against current source.
- Removed all PDF-note placeholders.
- Added practical examples: Lua reinforcement trigger, UI ChromeLogic label binding, audio trait playback.
- Added IDE/asset tooling guidance.
- Rewrote pedagogical "What to read next" sections in 5 key chapters.
- Generated `IMAGE_MANIFEST.md` with 347 requested diagrams.
- Verified combined manual: 53 files, 1,260,747 bytes, 265 paths, 1,132 links — all pass.
- Moved temporary helper scripts to `Cameo Work/to delete/`.

### Open issues / blockers
None. Text is production-ready; awaiting image asset production.

### Next steps
- (DONE) Generate inline Mermaid/SVG diagrams for all visual-aid comments.
- Final layout pass (DOCX/PDF) if a non-Markdown output is required.

## 2026-06-24 — Image Production Pipeline

### What was done
- Installed `@mermaid-js/mermaid-cli` and the Chrome headless binary for Puppeteer.
- Generated a Mermaid `.mmd` diagram for every `<!-- DEV-NOTE [visual-aid]: ... -->` comment, with category-specific templates and chapter-specific overrides.
- Replaced all HTML comments with `![...](images/...svg)` references.
- Rendered 340 SVG files to `Manual/images/`.
- Updated `verify_internal_links.py` to resolve image links relative to the combined manual directory.
- Verified combined manual: 53 files, 1,273,586 bytes, 265 paths, 1,479 links — all pass.
- Moved temporary generation scripts to `Cameo Work/to delete/`.

### Open issues / blockers
None. The manual now has rendered SVG diagrams instead of placeholder comments.

### Next steps
- Optional: polish individual diagrams (colors, specific labels, layout).
- Final layout pass (DOCX/PDF) if required.

## 2026-06-24 — Educational Sweep and External Review Prep

### What was done
- Swept all 51 manual source files for educational quality.
- Added 344 invisible `<!-- DEV-NOTE [visual-aid]: ... -->` comments at major section headings to guide future illustrators.
- Added 16 `<!-- DEV-NOTE [tooling]: ... -->` comments flagging external tools with canonical URLs.
- Added 13 `### External resources` blocks linking to canonical OpenRA docs and the community Lua tutorial.
- Verified the combined manual still assembles and all links/paths resolve.
- Moved temporary helper scripts to `Cameo Work/to delete/`.

### Open issues / blockers
None.

### Next steps
- Run the external-AI critique prompt against the updated manual.
- Produce the flagged visual aids before final publication.

## 2026-06-24 — Phase D Completion and Pre-Production Polish (completed)

### What was done
- Recovered the irrecoverable Phase D manual session by verifying all deliverables were present:
  - `Appendix_F_Testing.md` (unit tests, YAML validation, replay testing, sync testing, performance testing).
  - `Part_09_Chapter_02_Server_Connection.md` lobby/match setup expansion.
  - `Part_10_Chapter_03_Port_And_Modding.md` Asset Creation Pipeline expansion.
  - ASCII architecture diagrams in `Part_00_Foundations.md` and `Part_01_Chapter_01_ECS.md`.
- Scanned the entire manual for truncation issues; no critical truncation or incomplete endings found.
- Fixed incorrect relative cross-references between chapters and appendices.
- Rewrote `build files/assemble_manual.py` to rewrite internal markdown links to in-document anchors in the combined manual.
- Added `build files/verify_internal_links.py` to verify all internal markdown links in the combined manual.
- Removed duplicate `## What to read next` sections from 13 chapters.
- Simplified non-standard nested/rich link formats into standard markdown links.
- Regenerated `OpenRA_Knowledge_Base_Manual.md` and verified:
  - 53 source files, 1,159,804 bytes.
  - `verify_paths.py`: 265 OpenRA source paths, all exist.
  - `verify_internal_links.py`: 1,050 internal links, all resolve.
- Moved temporary helper scripts to `Cameo Work/to delete/`.

### Open issues / blockers
None.

### Next steps
- Optionally convert `OpenRA_Knowledge_Base_Manual.md` to DOCX or another publishable format.
- Re-run `assemble_manual.py`, `verify_paths.py`, and `verify_internal_links.py` after any further edits.

## 2026-06-24 — Phase A Structural Improvements (completed)

### What was done
- Verified that Appendix E (Practical Modding Recipes) was completed by the previous subagent.
- Consolidated order-flow coverage across Part 1.3, Part 8.4, and Part 9.1: Part 1.3 now focuses on `World`/`Order` anatomy and the player→order path, Part 8.4 focuses on bot order construction and `ModularBot` throttling, and Part 9.1 remains the authoritative source for lockstep/network/order-pipeline details.
- Expanded Part 4 (Rendering and UI):
  - Part 4.1: added full frame lifecycle, sprite loading pipeline (`SequenceSet` -> `SpriteCache` -> `SheetBuilder` -> `Sheet` -> GPU), indexed vs BGRA sheet grouping, channel packing, UV inset, palette system, and combined shader pipeline.
  - Part 4.2: added detailed render phases, palette management, stable Z-sort, overlay grouping, depth-buffer options, and post-processing pass timing.
  - Part 4.3: added full widget lifecycle, event propagation, focus management, chrome authoring workflow, and widget conventions.
  - Part 4.4: added coordinate transforms, input dispatch, `IOrderGenerator` examples, drag gestures, multi-tap/double-click selection, scroll clamping, and corrected `WorldViewportSizes` YAML.
- Expanded Part 10.3 (Porting, Modding, and Developer Workflows) with SDK setup from scratch, a first custom unit walkthrough, mod structure comparison, and a common-pitfalls checklist.
- Updated `MASTER_INDEX.md`, `assemble_manual.py`, `Manual/README.md`, and `OpenRA Manual Build Files/README.md` to include Part 1.5, Part 1.6, and Appendix E.

### Open issues / blockers
- None.

### Verification
- Regenerated `OpenRA_Knowledge_Base_Manual.md` from 52 source files (~996 KB).
- Ran `verify_paths.py`: 254 referenced source paths verified against the cloned OpenRA engine; all exist.

### Next steps
1. Optionally convert `OpenRA_Knowledge_Base_Manual.md` to DOCX or another publishable format.
2. Re-run `assemble_manual.py` and `verify_paths.py` after any further edits.

## 2026-06-24 — Assemble and Quality-Fix the Knowledge Base Manual

### What was done
- Audited the full OpenRA Knowledge Base Manual for cross-reference consistency, file-path accuracy, and formatting.
- Fixed the duplicate Part 3 chapter numbering (renamed/renumbered to 3.1, 3.2, 3.3).
- Corrected dozens of source file paths across all parts, verified against the cloned OpenRA engine.
- Fixed a code snippet bug in the bot squads chapter (`Info.NavalUnitsTypes.Contains(a.Info.Name)`).
- Added `build files/assemble_manual.py` and `build files/verify_paths.py`.
- Regenerated `OpenRA_Knowledge_Base_Manual.md` as the canonical single-file edition.
- Verified 219 referenced source paths against the cloned OpenRA repository (all exist).
- Updated `build files/DEVELOPMENT_LOG.md`, `COVERAGE_MATRIX.md`, and `README.md`.

### Detailed notes
See `build files/DEVELOPMENT_LOG.md` for the exhaustive session record.

## 2026-06-24 — Tidied Manual Folder Structure

### What was done
- Flattened `OpenRA Manual Build Files/OpenRA Knowledgebase Research Documents/` by moving the seven module `.md` files directly into `OpenRA Manual Build Files/`.
- Moved the now-empty `OpenRA Knowledgebase Research Documents` subfolder to `Cameo Work/to delete/` per the project file-management rule.
- Verified `build files/` contains only the expected build files and scripts.

### 2026-06-24 — Reorganized Manual/ into Subfolders

### What was done
- Created `Manual/chapters/` and moved all `Part_*.md` files there.
- Created `Manual/appendices/` and moved all `Appendix_*.md` files there.
- Left only the top-level navigation files at the root of `Manual/`:
  - `OpenRA_Knowledge_Base_Manual.md`
  - `MASTER_INDEX.md`
  - `README.md`
- Updated the assembly script, `README.md`, `MASTER_INDEX.md`, and `build files/README.md` to use the new paths.
- Regenerated `OpenRA_Knowledge_Base_Manual.md` and verified all 219 source paths still exist.

### 2026-06-24 — Reorganized Manual/ Around Build vs. Planning Split

### What was done
- Moved all planning and project-tracking files from `build files/` to `OpenRA Manual Build Files/` (the root planning/research folder):
  - `BUILD_PLAN.md`, `COVERAGE_MATRIX.md`, `FILE_INDEX.md`, `TEMPLATE.md`, `DEVELOPMENT_LOG.md` (manual-specific), and `README.md` (manual-specific).
- Repurposed `build files/` to hold the source material for the combined manual:
  - `MASTER_INDEX.md`
  - `chapters/` (all 44 `Part_*.md` files)
  - `appendices/` (the four `Appendix_*.md` files)
  - `assemble_manual.py` and `verify_paths.py`
- Left only the final readable output at the top of `Manual/`:
  - `OpenRA_Knowledge_Base_Manual.md`
  - `README.md`
- Updated the assembly script and verify_paths script to work from `build files/`.
- Updated `Manual/README.md`, `OpenRA Manual Build Files/README.md`, and the existing `MASTER_INDEX.md` references to match the new layout.
- Regenerated `OpenRA_Knowledge_Base_Manual.md` and verified all 219 source paths still exist.

### Current structure
- `Manual/` — final readable manual.
  - `OpenRA_Knowledge_Base_Manual.md` — canonical single-file edition.
  - `README.md` — guide to the manual and its organization.
  - `build files/` — source material for the combined manual:
    - `MASTER_INDEX.md`, `chapters/`, `appendices/`, `assemble_manual.py`, `verify_paths.py`.
- `OpenRA Manual Build Files/` — planning and research documents:
  - `BUILD_PLAN.md`, `COVERAGE_MATRIX.md`, `FILE_INDEX.md`, `TEMPLATE.md`, `DEVELOPMENT_LOG.md` (manual-specific), `README.md` (manual-specific).
  - `Module 1_*.md` – `Module 7_*.md` research modules.
  - `OpenRA Knowledge Base Compilation ....docx.md` and `OpenRA Knowledgebase Scoping Plan ....docx.md`.
- `Archive/` — original zip backup.
- `DEVELOPMENT_LOG.md` (root) — project-level development log.

### 2026-06-24 — Triaged External LLM Feedback

### What was done
- Read three external LLM feedback sessions (ChatGPT, Gemini, Grok) from `build files/Critical Feedback/`.
- Verified specific claims (e.g., line-number frequency, whether Chapter 1.4 was truncated).
- Synthesized the feedback into a triaged summary (`build files/Critical Feedback/TRIAGE_SUMMARY.md`) separating:
  - Valid, high-priority issues (beginner onboarding, missing pathfinding/combat chapters, redundant order flow, Part 4/10 expansion, practical recipes).
  - Valid, medium-priority issues (line-number cleanup, YAML examples, troubleshooting appendix, version note, single-file ToC).
  - Subjective/context-dependent items (RMG imbalance by design, testing strategies, lobby setup, asset pipeline).
  - Likely unfounded claims (Chapter 1.4 truncation, "ubiquitous" line numbers overstated, file-path drift is already mitigated by `verify_paths.py`).
  - Out-of-scope items (images, PDF formatting, visual polish — deferred).
- Proposed a phased action plan focused on text-only improvements.

### Next steps
- Begin Phase A structural fixes (beginner onboarding, pathfinding/combat chapters, order-flow consolidation, Part 4/10 expansion, practical recipes).
- Optionally convert `OpenRA_Knowledge_Base_Manual.md` to DOCX or another publishable format.
- Re-run `build files/verify_paths.py` and `build files/assemble_manual.py` when the OpenRA source is refreshed.
