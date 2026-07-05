# OpenRA Knowledge Base Manual v.5

This repository contains the OpenRA Knowledge Base Manual, version v.5.

## Main manual

- `OpenRA_Knowledge_Base_Manual.md` — the complete, combined manual in a single file. This is the version to read, print, or feed to an AI for review.
- `README.md` — this file.

## Source files

The individual source files that are assembled into the combined manual live in the `build files/` subdirectory:

- `build files/MASTER_INDEX.md` — single-page navigation for all parts and chapters.
- `build files/chapters/Part_00_Foundations.md` — how to use the manual, learning paths, and key concepts.
- `build files/chapters/Part_01_Chapter_01_ECS.md` through `build files/chapters/Part_10_Chapter_03_Port_And_Modding.md` — all 49 chapters (including the extra Pathfinding/Movement and Combat/Damage chapters in Part 1, and the SDK Bootstrap chapter in Part 3).
- `build files/appendices/Appendix_A_Glossary.md` through `build files/appendices/Appendix_I_Actor_Reference.md` — supporting reference material.
- `build files/assemble_manual.py` — script that regenerates `OpenRA_Knowledge_Base_Manual.md` from the source files.
- `build files/verify_paths.py` — script that checks every referenced file path in the combined manual against the cloned OpenRA source.

## Planning and research files

The planning, research, and project tracking documents are archived in `Archive/OpenRA Manual Build Files/`:

- `Archive/OpenRA Manual Build Files/README.md` — chapter index and project README.
- `Archive/OpenRA Manual Build Files/FILE_INDEX.md` — listing of C# source files in the OpenRA engine.
- `Archive/OpenRA Manual Build Files/COVERAGE_MATRIX.md` — source-to-chapter coverage mapping.
- `Archive/OpenRA Manual Build Files/TEMPLATE.md` — chapter template.
- `Archive/OpenRA Manual Build Files/DEVELOPMENT_LOG.md` — development history.
- `Archive/OpenRA Manual Build Files/BUILD_PLAN.md` — original build plan.
- `Archive/OpenRA Manual Build Files/Module 1_*.md` through `Module 7_*.md` — research modules.
- `Archive/OpenRA Manual Build Files/OpenRA Knowledge Base Compilation ....docx.md` — compiled research review.
- `Archive/OpenRA Manual Build Files/OpenRA Knowledgebase Scoping Plan ....docx.md` — initial scoping document.

## How to use this

- To read cover-to-cover: open `OpenRA_Knowledge_Base_Manual.md`.
- To navigate: open `build files/MASTER_INDEX.md`.
- To review the manual as an AI: read `OpenRA_Knowledge_Base_Manual.md` from top to bottom.
- To rebuild the combined manual after editing a source file: run `build files/assemble_manual.py`.
- To verify file paths after editing: run `build files/verify_paths.py`.
- To run all verification and export steps in one command: run `build files/build_manual.ps1` (PowerShell) or `build files/build_manual.bat` (Windows batch wrapper). See `build files/EXPORT_PIPELINE.md` for Pandoc / DOCX / PDF export details.

## License and attribution

The text, scripts, and original diagrams in this manual are released into the public domain under the UNLICENSE (`UNLICENSE` in the project root).

This project references and renders game assets (e.g., sprites, cameos, sounds) that belong to their respective owners (Westwood/EA for *Command & Conquer*, *Red Alert*, and *Dune 2000*). Those assets are used as fair-use educational reference material and are **not** covered by the UNLICENSE. We claim no ownership and yield all rights to their respective owners.

## GitHub and transparency

### Authors and credits

- **Renegade1993** — project author, curator, and primary researcher: https://github.com/Renegade1993
- **Devin** — AI engineering assistant by Cognition (https://devin.ai) — helped assemble, verify, and export the manual.
- **OpenRA contributors** — the engine, documentation, and modding community that produced the source material this manual synthesizes.
- **Game asset owners** — all rendered game assets (sprites, cameos, sounds, terrain tiles, etc.) belong to their respective owners (Westwood/EA for *Command & Conquer*, *Red Alert*, and *Dune 2000*). They are included as fair-use educational reference material; we claim no ownership and will remove or replace them if a rights holder requests it.

### Contributions welcome

Feedback, suggestions, corrections, and contributions are **more than welcome**. The best way to help is to open a GitHub issue or submit a pull request. The entire workflow is documented here and in `build files/EXPORT_PIPELINE.md` so that anyone can:

- Read the combined manual: `OpenRA_Knowledge_Base_Manual.md`.
- Edit the source chapters in `build files/chapters/` and `build files/appendices/`.
- Regenerate the manual and verify it with `build files/build_manual.ps1` or `build files/build_manual.bat`.
- Export to DOCX or PDF with Pandoc (see `EXPORT_PIPELINE.md`).
- Propose changes via GitHub issues and pull requests.

The repository includes the rendered game-asset images (`images/actors/`) so that the manual is complete out-of-the-box. These assets are clearly attributed as fair-use educational reference material and remain the property of their respective owners. If a rights holder ever requests their removal, we will comply and document an alternative way to render the images locally from an installed OpenRA copy.

## Internal documentation

- `build files/EXPORT_PIPELINE.md` — how the manual is assembled, verified, and exported.
- `DEVELOPMENT_LOG.md` — session-by-session development history.
- `PRODUCTION_HANDOFF.md` — current status and remaining blockers.
- `Archive/OpenRA Manual Build Files/BUILD_PLAN.md` — original plan and current completion status.
- `UNLICENSE` — public domain dedication for original work, with third-party asset disclaimer.
