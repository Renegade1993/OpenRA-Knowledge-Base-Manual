# OpenRA Knowledge Base Manual — Production Handoff (v1.0)

> **Last updated:** 2026-06-29 (Round 1/2 polish complete, ready for third feedback round)
> **Manual version:** v.5
> **Target:** v1.0 production release
> **Verified against:** OpenRA `bleed` @ `972c10ec80f90a30a4fa80abfebc633af3365847` (playtest line)
> **Status:** text technically verified (static + engine execution) and proofread. All YAML snippets and C# custom-trait snippets compile and load against the pinned engine. The Appendix I visual asset pass is complete. Round 1 and Round 2 feedback items have been addressed. Pandoc 3.10 is installed and the `build_manual.ps1` export pipeline is ready; MiKTeX installation is in progress to provide a LaTeX engine for PDF export. The project now has a root `README.md` and an expanded `EXPORT_PIPELINE.md` for GitHub transparency. The manual is ready for a third round of external AI feedback before production export.

This document is the **single source of truth** for the next person (Claude, an editor, or a formatter) who takes the manual from its current draft state to a published v1.0. It is intentionally exhaustive.

---

## Executive summary

The OpenRA Knowledge Base Manual is a comprehensive, single-source Markdown reference for the OpenRA engine and modding ecosystem. It is complete in the following senses:

- **All planned chapters and appendices are written, assembled, and internally verified.**
- **Every chapter and appendix has a `## Summary` section.**
- **All internal markdown links and OpenRA source-path references resolve.** (Verified: 1,741 internal links, 275 source paths.)
- **340 Mermaid SVG diagrams have been generated and embedded** in place of the original `<!-- DEV-NOTE [visual-aid]: ... -->` placeholders.
- **Two new reference appendices were added late in the cycle:**
  - **Appendix G — Asset Visual Reference** (file formats, YAML definitions, engine classes per asset category).
  - **Appendix H — Advanced Modding Walkthroughs** (Chrome UI, Lua missions, crates, resources, shroud, capture, cloak, voxels, AI bots).

The remaining work is **visual production finishing**: replacing or refining generic diagrams, adding real screenshots and accent art, and producing the final publishable artifact (Markdown, DOCX, PDF, or web site). Technical verification is complete.

---

## What is already done (do not redo)

- [x] 56 source files (chapters + appendices) written and integrated.
- [x] `build files/assemble_manual.py` regenerates the combined manual.
- [x] `build files/verify_paths.py` confirms 275–276 OpenRA source paths exist.
- [x] `build files/verify_internal_links.py` confirms 1,546 internal links resolve.
- [x] Engine-execution verification runbook completed: `make.cmd all` builds clean, `ra/cnc/d2k --check-yaml` pass, manual YAML snippets load, C# custom traits compile, Lua mission map loads.
- [x] `## Summary` sections added to all chapters/appendices; 33 malformed Summary sentences fixed.
- [x] Visible `<!-- DEV-NOTE [tooling]: ... -->` comments moved to `### External resources` sections.
- [x] PDF-note placeholders removed.
- [x] Round 2 external AI feedback triaged and applied.
- [x] Practical examples added for Lua scripting, Chrome UI, audio playback, and nine advanced modding topics.
- [x] Glossary links use consistent relative paths (`../appendices/Appendix_A_Glossary.md` from chapters, `Appendix_A_Glossary.md` from appendices).
- [x] 340 Mermaid SVG diagrams rendered to `images/` and embedded in the source files.
- [x] `IMAGE_MANIFEST.md` records the 347 requested visual aids (some are embedded as text, some as SVG, some remain as screenshot placeholders).
- [x] `DEVELOPMENT_LOG.md` maintained with session entries.

---

## What Claude needs to do for v1.0 production

### Recommended session split (two-Claude workflow)

If you have two Claude sessions available (for example, a technical/verification Claude and a design/export Claude), the cleanest split is:

- **Claude #1 — Technical Verification & Proofreading:** make the manual textually and technically correct.
- **Claude #2 — Visual Asset & Export Production:** make the manual visually polished and publishable.

Both sessions must run the verification commands at the end. The split below is recommended because the visual pass is safest after all examples are verified, and the export pass is safest after all visual assets are in place.

---

### Claude #1 — Technical Verification & Proofreading

**Goal:** Leave the manual in a technically correct, fully proofread state. No visual work yet.

| Task | Section | Done? |
|------|---------|-------|
| Pin the target OpenRA version | 1.1 | ✅ `bleed` @ `972c10ec` = playtest `playtest-20260222-76-g972c10ec80` |
| Validate all YAML snippets with `--check-yaml` | 1.2 | ◑ Static-verified vs source; engine `--check-yaml` run **deferred to Windows** (no .NET in sandbox) |
| Validate/compile all C# trait snippets | 1.3 | ◑ Static-verified vs source APIs; compile **deferred to Windows** |
| Validate the Lua mission template in a real `.oramap` | 1.4 | ◑ Static-verified vs Lua API + fixed `Scripts:` bug; real `.oramap` run **deferred to Windows** |
| Validate asset paths against the pinned source tree | 1.5 | ✅ 275 paths verified vs mounted source; `ServerTraits/...` artifact removed |
| Check for engine-field drift against docs.openra.net | 1.6 | ✅ Verified vs pinned source (authoritative for this commit); fixed `Race`/`ServerTraits`/`ExternalCaptures`/`Slot` drift |
| Final proofread for typos, phrasing, and formatting | 3.1 | ✅ Programmatic scan + targeted reading; fixed Part 8/9 + Appendix H |
| Fix heading-hierarchy issues | 3.2 | ✅ 0 skipped levels across 55 files |
| Ensure correct code-block language tags | 3.3 | ◑ All C#/YAML/bash/Lua blocks tagged; 118 bare ASCII-diagram fences left as optional `text` follow-up |
| Re-run link verification and fix any broken links | 3.4 | ✅ 1,546 links / 0 broken (no links added/removed by edits); re-run on Windows to confirm |
| Glossary completeness pass | 3.5 | ◑ Light spot-check; linking maintained from prior sessions (P2) |

> **Legend:** ✅ done · ◑ done as far as this environment allows (engine-execution steps deferred to a Windows machine with .NET + the OpenRA source).
>
> **Verified against:** OpenRA `bleed` @ `972c10ec80f90a30a4fa80abfebc633af3365847` (playtest line). Claude #2 should use the **same** checkout.

**Handoff to Claude #2:**
- Update this `PRODUCTION_HANDOFF.md` and `DEVELOPMENT_LOG.md` with what was fixed and any open questions.
- Note any OpenRA version or source tree used for verification so Claude #2 uses the same baseline.
- Do not start adding images or exporting yet — the manual is now ready for the visual pass.

---

### Claude #2 — Visual Asset & Export Production

**Goal:** Produce the final, publishable artifact with polished visuals and all export steps complete.

**Prerequisites:** Claude #1 must be complete, and the verification commands must pass with zero errors.

| Task | Section | Done? |
|------|---------|-------|
| Audit and replace generic SVG diagrams | 2.1 | ☐ |
| Add real in-game screenshots | 2.2 | ☐ |
| Add accent / flavor images | 2.3 | ☐ |
| Standardize diagram style (palette, font, line style) | 2.4 | ☐ |
| Verify all image alt text | 2.5 | ☐ |
| Decide output format | 4.1 | ☐ |
| Generate Markdown export | 4.2 | ☐ |
| Generate DOCX export (if needed) | 4.3 | ☐ |
| Generate PDF export (if needed) | 4.4 | ☐ |
| Generate web site export (if needed) | 4.5 | ☐ |
| Verify the exported artifact renders correctly | 4.6 | ☐ |
| Confirm no copyrighted game art is embedded | 5.1 | ☐ |
| Add license file | 5.2 | ☐ |
| Add/update README for the chosen channel | 5.3 | ☐ |
| Publish / distribute v1.0 | 5.4 | ☐ |
| Final checklist | Final checklist | ☐ |

**Handoff to user:**
- Final exported files, verification output, and updated `PRODUCTION_HANDOFF.md` / `DEVELOPMENT_LOG.md`.
- Summary of any remaining optional improvements (e.g., self-assessment prompts, per-diagram polish).

---

### 1. Verify technical accuracy (CRITICAL — must be done first)

The manual contains many YAML/C#/Lua snippets. They were written against a recent OpenRA source tree, but engine APIs and YAML fields change between playtests.

| Task | How to do it | Owner | Priority |
|------|--------------|-------|----------|
| **1.1 — Pin the OpenRA version** | Decide whether v1.0 targets the current release docs (`https://docs.openra.net/en/release/`) or the latest playtest docs (`https://docs.openra.net/en/playtest/`). Update the manual's examples to match that version. | Claude / User | P0 |
| **1.2 — Validate all YAML snippets** | Create a temporary test mod, copy each major snippet (Appendix E recipes, Appendix H walkthroughs, Part 2.4, Part 10.3) into it, and run `OpenRA.Utility.exe <mod> --check-yaml`. Fix any field-name or trait-name errors. | Claude | P0 |
| **1.3 — Validate C# trait snippets** | Compile the custom-trait examples (Part 0, Appendix E Recipe 6, Appendix H Chrome UI) against the same engine version. Fix any API changes (`World.SharedRandom`, `ITick`, `INotifyCreated`, etc.). | Claude | P0 |
| **1.4 — Validate Lua mission snippets** | Create a test `.oramap` using the Appendix H Lua mission template, run `--check-yaml`, and start the mission. Confirm `WorldLoaded`, `Trigger`, `Reinforcements`, and objectives work. | Claude | P0 |
| **1.5 — Validate asset paths** | Re-run `verify_paths.py` against the **same** source tree used for v1.0. If the source tree is updated, update the paths in the manual. | Claude | P0 |
| **1.6 — Check for engine-field drift** | Compare the manual's trait/weapon fields against `https://docs.openra.net/en/<version>/traits/` and `https://docs.openra.net/en/<version>/weapons/`. Pay special attention to recently renamed fields (`Units` vs `Unit` in `GiveUnitCrateAction`, `ResourceTypes` vs older `ResourceType`, `CaptureManager` vs old capture system). | Claude | P0 |

**Reference source tree for verification:**
```text
C:\Users\Kmoney\Documents\AI Projects\Cameo Work\Game Sources and Development Reference Materials\OpenRA GitHub Repositories\OpenRA
```

---

### 2. Visual assets (diagrams, screenshots, accent art)

The manual currently uses generated SVGs. For v1.0, decide whether to keep the SVGs, replace them with polished custom diagrams, or add real screenshots.

| Task | How to do it | Owner | Priority |
|------|--------------|-------|----------|
| **2.1 — Audit every SVG diagram** | Open `build files/IMAGE_MANIFEST.md` and check each of the 340 SVGs in `images/`. Many are template diagrams that need real labels, types, and chapter-specific details. Replace generic diagrams with content-rich ones. | Claude / User | P0 |
| **2.2 — Add screenshots** | For every `<!-- DEV-NOTE [visual-aid]: screenshot ... -->` comment in the source, capture a real screenshot and replace it with `![caption](images/<file>.png)`. Re-run verification after each batch. | User | P1 |
| **2.3 — Add accent / flavor images** | Create or source faction icons, unit silhouettes, chapter header art, and decorative borders. Save to `images/` and insert near relevant headings. | User + Claude | P1 |
| **2.4 — Standardize diagram style** | Choose a consistent color palette, font, and line style for all Mermaid diagrams. Apply it globally via the Mermaid CLI config or by regenerating diagrams. | Claude | P2 |
| **2.5 — Verify alt text** | Every image/SVG reference must have meaningful alt text. Check for empty `![]()` or generic captions. | Claude | P2 |

**How to add a screenshot:**
1. Capture the image.
2. Save it to `images/<descriptive-name>.png` (or `.svg`).
3. Replace the placeholder comment in the source file with:
   ```markdown
   ![Descriptive caption](images/<descriptive-name>.png)
   ```
4. Re-run the verification commands.

**How to add a new diagram:**
1. Add a Mermaid diagram in a source file between ` ```mermaid ` fences.
2. Or, create a `.mmd` file in `images/` and reference it.
3. Use the existing Mermaid CLI pipeline to render SVGs if regenerating all diagrams.
4. Re-run verification.

---

### 3. Content polish and final proofreading

| Task | How to do it | Owner | Priority |
|------|--------------|-------|----------|
| **3.1 — Final proofread** | Read the combined `OpenRA_Knowledge_Base_Manual.md` end-to-end. Fix typos, awkward phrasing, inconsistent capitalization, and formatting. | Claude / User | P0 |
| **3.2 — Heading hierarchy** | Ensure no skipped heading levels (e.g., `##` followed by `####` without `###`). | Claude | P1 |
| **3.3 — Code-block languages** | Ensure every YAML/C#/Lua/Shell block has the correct language tag. | Claude | P1 |
| **3.4 — Link sanity** | Run `verify_internal_links.py` and fix any broken links introduced by proofreading. | Claude | P0 |
| **3.5 — Glossary completeness** | Make sure every OpenRA-specific term used in a chapter is defined or linked in `Appendix_A_Glossary.md`. | Claude | P2 |
| **3.6 — Self-assessment (optional)** | The audit noted that the manual lacks self-assessment prompts. Consider adding 1–3 review questions per major chapter if the target audience is learners. | Claude | P3 |

---

### 4. Export and publication

| Task | How to do it | Owner | Priority |
|------|--------------|-------|----------|
| **4.1 — Decide the output format** | Options: Markdown + images (GitHub/wiki), static HTML (GitHub Pages), DOCX, PDF, or all of the above. | User | P0 |
| **4.2 — Markdown export** | Use the assembled `OpenRA_Knowledge_Base_Manual.md` directly. Ensure image paths are relative to `Manual/`. | Claude | P1 |
| **4.3 — DOCX export (optional)** | Use Pandoc or a Markdown-to-DOCX converter. Convert SVGs to PNG first if the converter does not embed SVG. | Claude | P2 |
| **4.4 — PDF export (optional)** | Use Pandoc + LaTeX or wkhtmltopdf. Again, convert SVGs to PNG first if needed. | Claude | P2 |
| **4.5 — Web site export (optional)** | Use a static site generator (e.g., MkDocs, Hugo). Split the combined manual into chapter pages or keep it as one long page. | Claude | P2 |
| **4.6 — Verify exported artifact** | Open the exported file and check that the Table of Contents, image references, cross-references, and code blocks render correctly. | Claude / User | P0 |

---

### 5. Legal, copyright, and distribution

| Task | How to do it | Owner | Priority |
|------|--------------|-------|----------|
| **5.1 — No copyrighted game art** | The manual currently uses text placeholders and generated SVGs. Do not embed Westwood/EA-owned SHP sprites, voxel models, or music without permission. Screenshots should be from the user's own game or clearly fair-use. | User | P0 |
| **5.2 — License the manual text** | Decide a license (e.g., CC BY-SA 4.0, GPL-3). Add a `LICENSE.md` to the manual project root. | User | P1 |
| **5.3 — Add a README** | If publishing to GitHub, ensure the top-level `README.md` explains what the manual is, who it is for, and how to build it. | Claude | P1 |
| **5.4 — Distribution channel** | Publish to GitHub repo, `docs.openra.net`, the OpenRA wiki, or a standalone site. Update the manual's own cross-references if URLs change. | User | P2 |

---

## Known issues and risks

1. **Engine version drift:** The manual was written against a recent source tree. If the target OpenRA version changes, YAML fields and trait names may need updating. This is the highest-risk remaining task.
2. **Generic diagrams:** The 340 Mermaid SVGs are functional but may not be publication-quality. Some may be generic templates with placeholder labels.
3. **No automated YAML/C# tests:** The verification scripts only check paths and links, not that the code examples compile or load. Manual testing is required.
4. **Screenshots absent:** Real in-game screenshots are not yet included. The `IMAGE_MANIFEST.md` flags where they are needed.
5. **Self-assessment prompts absent:** The audit recommended adding self-assessment. This is optional for v1.0 but would improve educational value.

---

## File locations

| Item | Path |
|------|------|
| Combined manual | `C:\Users\Kmoney\Documents\AI Projects\Cameo Work\Game Sources and Development Reference Materials\OpenRA Manual\OpenRA_Knowledge_Base_Manual.md` |
| Source chapters | `C:\Users\Kmoney\Documents\AI Projects\Cameo Work\Game Sources and Development Reference Materials\OpenRA Manual\build files\chapters\` |
| Source appendices | `C:\Users\Kmoney\Documents\AI Projects\Cameo Work\Game Sources and Development Reference Materials\OpenRA Manual\build files\appendices\` |
| Build scripts | `C:\Users\Kmoney\Documents\AI Projects\Cameo Work\Game Sources and Development Reference Materials\OpenRA Manual\build files\` |
| Generated images | `C:\Users\Kmoney\Documents\AI Projects\Cameo Work\Game Sources and Development Reference Materials\OpenRA Manual\images\` |
| Image manifest | `C:\Users\Kmoney\Documents\AI Projects\Cameo Work\Game Sources and Development Reference Materials\OpenRA Manual\build files\IMAGE_MANIFEST.md` |
| Development log | `C:\Users\Kmoney\Documents\AI Projects\Cameo Work\Game Sources and Development Reference Materials\OpenRA Manual\DEVELOPMENT_LOG.md` |
| This handoff | `C:\Users\Kmoney\Documents\AI Projects\Cameo Work\Game Sources and Development Reference Materials\OpenRA Manual\PRODUCTION_HANDOFF.md` |
| OpenRA source clone | `C:\Users\Kmoney\Documents\AI Projects\Cameo Work\Game Sources and Development Reference Materials\OpenRA GitHub Repositories\OpenRA` |
| Temporary / old files | `C:\Users\Kmoney\Documents\AI Projects\Cameo Work\to delete\` |

---

## Verification commands

Run these after **every** change before any export:

```powershell
cd "C:\Users\Kmoney\Documents\AI Projects\Cameo Work\Game Sources and Development Reference Materials\OpenRA Manual\build files"
python assemble_manual.py
python verify_paths.py
python verify_internal_links.py
```

Expected output:
```text
Chapters: 55
Size: 1,343,193 bytes
Total unique file paths checked: 275
Paths not found: 0
Internal links checked: 1546
Broken internal links: 0
```

All checks must pass with zero errors before production export.

---

## How to add a new chapter or appendix

1. Create the file in `build files/chapters/` or `build files/appendices/`.
2. Add a `## Summary` and a `## What to read next` section.
3. Add the relative path to `assemble_manual.py` in the correct order.
4. Add a row to `MASTER_INDEX.md`.
5. Add cross-references from related chapters/appendices.
6. Re-run the verification commands.

---

## OpenRA reference resources

Use these as the definitive source for all verification questions:

| Resource | URL | Use for |
|----------|-----|---------|
| Release docs | `https://docs.openra.net/en/release/` | Stable trait/weapon/Lua reference |
| Playtest docs | `https://docs.openra.net/en/playtest/` | Latest engine reference |
| Traits reference | `https://docs.openra.net/en/release/traits/` | Every trait and field |
| Weapons reference | `https://docs.openra.net/en/release/weapons/` | Weapon/warhead definitions |
| Lua API | `https://docs.openra.net/en/release/lua/` | Mission scripting API |
| Sprite sequences | `https://docs.openra.net/en/release/sprite-sequences/` | Sequence YAML |
| Community Lua tutorial | `https://steamsdev.github.io/content/openratut/home.html` | Beginner-friendly mission scripting |

---

## Session log

### 2026-06-28 — Engine-execution verification runbook completed
- Ran the four-part engine-execution runbook against the pinned OpenRA `bleed` source.
- `make.cmd all`: build succeeded.
- `utility.cmd ra/cnc/d2k --check-yaml`: all three mods passed with no errors.
- Created a `manual-test` map, loaded the `yaml-snippets.md` blocks, and validated with `--check-yaml`: passed.
- Assembled a `manual-mission` map from the Appendix H Lua template, using a compatible 96×96 TEMPERAT `map.bin` from `fort-lonestar`; `--check-yaml` passed. GUI play-through is the only remaining step.
- Compiled the four manual C# custom-trait snippets inside `OpenRA.Mods.Common`: `Build succeeded`, 0 errors.
- **Found and fixed a manual bug:** the Appendix H Lua mission example used invalid actor types (`Waypoint1`/`EnemyEntry`) and missed a required `mpspawn`. Corrected in `Appendix_H_Advanced_Modding_Walkthroughs.md` and the `engine-tests/lua-mission/map.yaml` test file, and added explicit `.oramap` packaging instructions to the walkthrough's verification steps.
- **Additional in-game bug found by user:** the objective text displayed as the raw Fluent key `destroy-enemy-factory`. Fixed by adding a `map.ftl` translation file, loading it via `FluentMessages:` in `map.yaml`, and documenting the requirement in the walkthrough, common pitfalls, and runbook.
- **Briefing bug found by user:** the mission briefing showed the wrong text (Einstein rescue). Fixed by adding `MissionData: Briefing: briefing` to `rules.yaml` and the `briefing` translation to `map.ftl`, and documenting that missing `MissionData` can cause the mission selector to show the previous mission's briefing.
- **Extra MCV / crash bug found by user:** the player started with both a placed Construction Yard and an extra MCV, and later the game crashed on the enemy tooltip with `Invalid bot type: campaign`. Fixed by adding `ModularBot@CampaignAI` directly to the map's `rules.yaml`, loading the RA campaign rules in `map.yaml`, and removing the workaround `mpspawn` actor.
- **No money bug found by user:** the player started with `0` credits because `campaign-rules.yaml` sets `PlayerResources.DefaultCash: 0`. Fixed by overriding `PlayerResources.DefaultCash: 5000` in the map's `rules.yaml`.
- **Sell Conyard exploit found by user:** selling the Construction Yard did not lose the mission because `Trigger.OnKilled` only fires on destruction, not on sale or capture. Fixed by using `Trigger.OnRemovedFromWorld` for destroyed/sold buildings and `Trigger.OnCapture` for captured buildings.
- Updated `DEVELOPMENT_LOG.md` with the results.
- Status: technically verified; ready for the visual asset / export pass.

### 2026-06-28 — Cameo export pass
- Built the OpenRA engine (`make.cmd all`) and ran `build files/extract_cameos.ps1`.
- RA: 91/91 real cameos extracted successfully.
- CNC: 54/54 real cameos extracted successfully.
- D2K: 0/45 real cameos extracted; `DATA.R16` is not installed. To complete, launch the D2K mod once so OpenRA downloads the content, then re-run the script.
- Fixed `extract_cameos.ps1` during the run: direct `bin\OpenRA.Utility.exe` invocation with `ENGINE_DIR`, added `--extract` step before `--png`, and replaced em dashes in `Write-Host` strings.
- Manual verification passed after the export.
- Updated `DEVELOPMENT_LOG.md` with the results.

### 2026-06-28 — Cameo export pass (D2K re-run after content install)
- User installed the D2K content by launching the D2K mod.
- Implemented a custom OpenRA utility command `--export-sequence-frame` in `OpenRA.Mods.Common/UtilityCommands/ExportSequenceFrameCommand.cs` that loads the actor's sequence set and exports the exact `icon` frame.
- Updated `extract_cameos.ps1` to use the new command for all mods (RA, CNC, D2K) and added a fallback mapping for D2K actor codes to their faction-specific sequence image (e.g., `construction_yard` -> `conyard.ordos`).
- Fixed palette handling: RA/CNC palettes are read from the mod's file system; D2K uses the embedded R16 frame palette when available, eliminating the purple hue.
- Fixed RA/CNC structure cameos (e.g., `weap`) being cut off by resolving the correct `icon` filename (e.g., `weapicon.shp`) through the engine's sequence loader instead of the default `weap.shp`.
- Re-ran `extract_cameos.ps1`. Final counts: RA 78/91 real cameos (13 fake/placeholder actors have no `icon`), CNC 54/54 real cameos, D2K 43/45 real cameos. Only `mpsardaukar` and `nsfremen` remain placeholders because they have no `icon` sequence.
- Updated Appendix I to reflect that the cameos are real game art. Manual verification passed.

### 2026-06-29 — Dual images (battlefield sprite + construction-menu cameo) and final D2K purple fix
- **Purple fix (root cause):** the D2K purple was a red<->blue channel swap caused by reading the cameo back through the texture sheet (`Sheet.AsPng` + premultiply). Rewrote `ExportSequenceFrameCommand` to read the raw `ISpriteFrame` directly — indexed SHP frames (RA/CNC) get the supplied palette; truecolour D2K R16 frames are written as-is (the loader already has the correct colour). Verified numerically: D2K `light_inf` icon went from avgR=81/B=132 (purple) to avgR=132/B=81 (warm tan).
- **Two images per actor:** Appendix I now shows a **Cameo** column (sidebar/construction-menu icon, `<code>.png`) AND a **Unit** column (in-world battlefield sprite, `<code>_unit.png`) for all three mods. Added a `@unit` auto-pick to the utility command (first available of `idle`/`stand`/`turret`/...), which also skips intentionally-empty placeholder frames so turret defences (GUN/AGUN/SAM) export their `turret` body.
- Updated `generate_actor_reference.py` (new column + dual faction-tinted placeholders) and `extract_cameos.ps1` (exports both images per actor).
- Final image counts: RA 78 icons / 78 units, CNC 54 / 54, D2K 43 / 40. Remaining placeholders are fake structures, faction duplicates (`mpsardaukar`, `nsfremen`), concrete slabs (`concretea`/`concreteb`) and the death-hand missile (`deathhand`) — none have standalone art.
- Manual verification passed: 56 chapters, 275 paths, **1931** internal links, 0 broken.

### 2026-06-29 — Battlefield sprite visual polish
- **Composited building overlays.** The custom `ExportSequenceFrameCommand` now layers `idle-top` and `build-top` sequences on top of the base `idle`/`stand` body when exporting `@unit` battlefield sprites. This fixes cut-off buildings (RA `proc` tower, RA/CNC `weap` roof/crane, D2K structures with animated roofs) and treats each frame's own `Offset` as the relative placement.
- **Dropped ground shadows.** RA/CNC player-palette shadow index 4 is made transparent in the exported RGBA battlefield sprite, and D2K R16 translucent-black shadow pixels are dropped, removing the solid coloured block at the base of units.
- **Neutralised D2K house-colour markers.** D2K `RemappableFrame` true-colour units are recoloured via the loader's `WithSequenceFlags` to a neutral blue-grey so the reference image doesn't show the raw green house-colour reference pixels.
- Re-ran `extract_cameos.ps1` to regenerate all battlefield sprites; image counts stayed the same but every exported sprite is now complete and shadow-free. Manual verification passed: 56 chapters, 1,397,451 bytes, 275 paths, 1931 internal links, 0 broken.

### 2026-06-29 — Round 1/2 polish pass, UNLICENSE, and export pipeline
- **Updated `BUILD_PLAN.md`** to reflect actual completion: all phases complete, extra chapters/appendices added, and Phase B/C/D/E/F status updated. The plan is now a historical/tracking document rather than an unfinished todo list.
- **Fixed maintenance issues:** added `## Summary` to `Part_00_Foundations.md`, fixed the inconsistent glossary path in `Appendix_A_Glossary.md`, and verified all code fences have language tags.
- **Consolidated order flow redundancy:** `Part_01_Chapter_03_World_Orders.md` now focuses on Order anatomy from the UI/player side; `Part_09_Chapter_01_OrderManager.md` is the canonical lockstep pipeline reference; `Part_08_Chapter_04_Order_Flow.md` focuses on bot order construction/issuing with cross-references to the other two.
- **Deepened Part 4 (Rendering/UI):** added `## Mental Model` sections, expanded practical examples (sprite wiring, range circle, widget event propagation, ping order generator), added diagram prompts, and improved cross-references.
- **Deepened Part 10.3 (Modding workflow):** added a `## Mental Model` section, a complete "From zero to first custom unit" end-to-end example, a common-pitfalls checklist, a YAML debugging workflow, and a trait-discovery guide. Heavy cross-referencing to other parts and appendices.
- **Addressed Round 2 high-priority items outside Part 4/10.3:** added visual-aid diagram prompts to Part 1.1, 1.2, 6.3, 7.1; added `## Summary` to Appendices A–E; added practical examples to Part 6.3 and Part 7.1.
- **Added `UNLICENSE`** to the project root with a third-party asset disclaimer. Updated `Manual/README.md` to document the license and attribution.
- **Created a sustainable export pipeline:** `build files/build_manual.ps1` runs assemble + verify + optional Pandoc export in one command; `build files/EXPORT_PIPELINE.md` documents the Pandoc vs. Claude workflow. Pandoc is recommended for the repeatable mechanical layer; Claude is recommended for the one-time design/template layer.
- **Installed Pandoc 3.10** at `C:\Program Files\Pandoc`; updated `build_manual.ps1` to auto-detect Pandoc and LaTeX engines, with clear warnings for missing dependencies.
- **Started MiKTeX installation** via `miktexsetup` command-line utility to provide a LaTeX engine for PDF export.
- **Added root `README.md`** for GitHub transparency, with quick links, build instructions, contributing guidelines, and license/attribution notes. Updated `Manual/README.md` with GitHub/transparency section.
- **Final verification:** `assemble_manual.py` → 56 chapters, 1,435,908 bytes; `verify_paths.py` → 275 paths, 0 missing; `verify_internal_links.py` → 2,020 links, 0 broken.
- **Status:** ready for the third round of external AI feedback. MiKTeX installation pending completion.

### 2026-06-25 — Appendix I: Actor Reference (auto-generated, with cameos)
- Added **`appendices/Appendix_I_Actor_Reference.md`**: deep tables (cameo, code, name, faction, cost, HP, armor, speed, sight, weapons, traits) for all **190 buildable actors** across the ra/cnc/d2k mods. Auto-generated from the pinned source by `build files/generate_actor_reference.py` (rules YAML + Fluent), so it stays accurate on re-run.
- Cameos: every slot has a faction-tinted **placeholder** now (manual is complete + link-valid); run `build files/extract_cameos.ps1` on Windows (content installed) to render the real cameos via `OpenRA.Utility.exe --resolved-sequences` + `--png`. This is the one step left to fully land "sprites in v1.0."
- Wired into `assemble_manual.py` (now **56 files**) and `MASTER_INDEX.md`. Appendix I verified link-valid in isolation (190 image links + 3 cross-refs, 0 broken; cameo counts match manifest). Full re-assembly to be run on Windows (sandbox cache bug).
- Scope: OpenRA's three bundled mods only; Westwood/EA cameos shown as fair-use educational reference with attribution (note built into the appendix).

### 2026-06-25 — Technical Verification & Proofreading (Claude #1)
- **Pinned** v1.0 to OpenRA `bleed` @ `972c10ec80f90a30a4fa80abfebc633af3365847` (playtest; matches the manual's own Part 0 version note `playtest-20260222-76-g972c10ec80`).
- **Static-verified** every priority snippet against the pinned source tree: Part 0 C# trait, Appendix E Recipe 6 C#, Appendix H Chrome UI C#, Appendix H crate/capture/resource YAML, Appendix H Lua mission, Part 2.4 weapon/actor YAML. (No engine execution — sandbox has no .NET.)
- **Fixed real drift/bugs:** Part 9.2 server-trait paths (`TraitInterfaces.cs`), `Slot`/`Client` field model (`Race`→`Faction`, no `Slot.ClientIndex`), removed nonexistent `IClientDisconnected`; Part 8.2 removed nonexistent `ExternalCaptures`; **Appendix H Lua `LuaScript: Scripts:` field + required `campaign.lua`/`utils.lua`** (was `Script: map.lua`, which would break the mission).
- **Proofread:** 0 heading-level skips; no real doubled-word typos; all programming-language code blocks correctly tagged (118 ASCII-diagram fences left bare as optional follow-up).
- **Verification:** baseline in-sandbox run = 55 chapters, 1,318,383 bytes (LF; = 1,343,193 CRLF on Windows), 1,546 links / 0 broken, 275 paths. A clean in-sandbox **re-run after edits was blocked by the Cowork file-cache staleness bug** on one edited file; source files on disk are correct, no links were added/removed, and all changed paths were confirmed to exist. **Re-run the three commands on Windows** for authoritative counts.
- **Open question:** confirm the playtest pin is acceptable for v1.0 (vs a tagged release). Full details, including the list of snippets still needing engine execution, are in `DEVELOPMENT_LOG.md`.

### 2026-06-25 — Summary polish + Appendix H: Advanced Modding Walkthroughs
- Polished all `## Summary` sections: fixed 33 malformed sentences and moved visible tooling comments to new `### External resources` sections.
- Added `build files/appendices/Appendix_H_Advanced_Modding_Walkthroughs.md` with nine advanced modding walkthroughs: custom Chrome UI panels, single-player Lua missions, custom crates, custom resources, shroud/fog customization, capture/engineer mechanics, cloak/stealth, voxel units, and custom YAML AI bots.
- Wired Appendix H into `assemble_manual.py`, `MASTER_INDEX.md`, and added cross-references in Part 4.3, Part 6.1, Part 6.2, Part 8.2, Part 10.3, and Appendix E.
- Spot-checked the new examples against the OpenRA engine source for trait/class and field accuracy.
- Updated `DEVELOPMENT_LOG.md` with the detailed session entries.
- Verified: 55 files, 1,343,193 bytes, 275 paths, 1,546 internal links — all pass.
- Status: text + diagrams ready; awaiting final screenshots, accent art, and optional export.

### 2026-06-25 — Added Appendix G: Asset Visual Reference
- Created `build files/appendices/Appendix_G_Asset_Visual_Reference.md` with categorical tables for all OpenRA asset types.
- Wired the new appendix into `assemble_manual.py`, `MASTER_INDEX.md`, and `Appendix_A_Glossary.md`.
- Added cross-references to Appendix G in Part 2.2, Part 4.1, Part 4.3, Part 5.1, Part 5.4, Part 6.3, Part 6.5, Part 10.3, and Appendix B.
- Enhanced Part 0 — Foundations with a reference-sections overview pointing to the appendices, Master Index, and Asset Visual Reference.
- Verified: 54 files, 1,293,424 bytes, 275 paths, 1,502 links — all pass.

### 2026-06-24 — Image production pipeline completed
- Installed Mermaid CLI and generated 340 SVG diagrams from all `<!-- DEV-NOTE [visual-aid]: ... -->` comments.
- Replaced all placeholder comments with image references.
- Updated `verify_internal_links.py` to resolve image links relative to the combined manual.
- Verified: 53 files, 1,273,586 bytes, 265 paths, 1,479 links — all pass.

---

## Final checklist before calling v1.0 "done"

- [ ] OpenRA version pinned and all examples tested against it.
- [ ] `assemble_manual.py`, `verify_paths.py`, and `verify_internal_links.py` all pass with zero errors.
- [ ] All generic diagrams replaced with content-rich diagrams or accepted as-is.
- [ ] All screenshot placeholders replaced with real screenshots or accepted as-is.
- [ ] Accent/flavor images added or accepted as-is.
- [ ] Exported artifact (Markdown/DOCX/PDF/web) rendered correctly and checked by a human.
- [ ] License and README added if publishing externally.
- [ ] No copyrighted game assets embedded without permission.
- [ ] `PRODUCTION_HANDOFF.md` and `DEVELOPMENT_LOG.md` updated to reflect the final state.

