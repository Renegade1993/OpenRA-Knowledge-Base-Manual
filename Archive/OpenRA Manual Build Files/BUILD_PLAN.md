# OpenRA Knowledge Base Manual — Build Plan

## 1. Objective

Produce an exhaustive, source-grounded, LLM-friendly OpenRA Knowledge Base Manual that:

- Accounts for every major subsystem, directory, and public API in the cloned `OpenRA/OpenRA` engine.
- Documents cross-subsystem dependencies so future readers (and LLMs) can trace how a change in one area affects others.
- Provides deep, reusable reference material on the random / procedural map generator.
- Sits alongside the existing Modules 1–7 as the canonical reference for the engine.

## 2. Source Inventory

All 36 OpenRA repositories are cloned to:

```
C:\Users\Kmoney\Documents\AI Projects\Cameo Work\Game Sources and Development Reference Materials\OpenRA GitHub Repositories
```

The engine itself lives in `OpenRA GitHub Repositories\OpenRA`. The relevant C# projects are:

| Project | .cs Files | Role |
| :---- | :---- | :---- |
| `OpenRA.Game` | ~226 | Core engine: ECS, game loop, map, orders, network, sound abstraction, file system, VFS, math, settings, input, support powers, graphics abstractions |
| `OpenRA.Mods.Common` | ~1,082 | Shared mod logic: traits, activities, bot modules, Lua scripting, map generator, UI logic, weapons, warheads, projectile, orders, production, terrain, resources |
| `OpenRA.Mods.Cnc` | ~140 | Tiberian Dawn / Tiberian Sun / Red Alert specific logic, TS map generator, C&C-specific traits |
| `OpenRA.Mods.D2k` | ~23 | Dune 2000 specific logic, D2k map generator |
| `OpenRA.Platforms.Default` | ~18 | OpenGL, OpenAL, SDL2, default platform bindings |
| `OpenRA.Server` | ~1 | Dedicated server entry point |
| `OpenRA.Utility` | ~1 | Command-line utility entry point |
| `OpenRA.Launcher` / `OpenRA.WindowsLauncher` | ~2 | Launcher entry points |
| `OpenRA.Test` | ~20 | Unit tests |
| **Total** | **~1,500** | |

In addition to C# source, the engine includes:

- MiniYaml rule files (`mods/*/rules`, `mods/*/weapons`, `mods/*/chrome`, `mods/*/sequences`, `mods/*/voices`, etc.).
- GLSL shaders (`glsl/`).
- Build/packaging scripts (`packaging/`, `Makefile`, `make.cmd`, `make.ps1`).
- Mod SDK reference repo (`OpenRA-Mod-SDK` in the cloned set).

## 3. Manual Structure (Pseudo-TOC)

The manual is organized into **Parts**. Each Part contains **Chapters**. Each Chapter maps to a subsystem directory or a cross-cutting concern. The structure is designed to be read linearly by a new contributor, but also to be used as a reference by an LLM that needs to modify a specific file.

### Part 0 — Foundations

- **Chapter 0.1 — Document Scope and How to Use This Manual**: conventions, how to read code references, how to cross-reference online docs.
- **Chapter 0.2 — Architectural Corrections & Guardrails**: a concise summary of the corrections from Modules 1–7 (e.g., `BlockedByActor` enum, `Map.cs` try/catch custom rules, `Game.Initialize` assembly loading, no `AppDomain.AssemblyResolve` hooking).

### Part 1 — Core Engine Architecture

- **Chapter 1.1 — Entity-Component-System (ECS)**
  - `Actor`, `ITraitInfo`, `Trait`, `TraitDictionary`, `TypeDictionary`, `ActorInitializer`, `ObjectCreator`, `FieldLoader`
  - Interface caches (`IOccupySpace`, `IHealth`, `IFacing`, `ITargetable`, `ISync`, `INotifyIdle`, etc.)
- **Chapter 1.2 — Activities and the Game Loop**
  - `Activity`, `ActivityUtils`, `ActionQueue`, `TickOuter`, `TickChild`, `RunActivity`
  - Integration with `World` and `OrderManager`
- **Chapter 1.3 — World, Tick, and Order Processing**
  - `World`, `WorldRenderer`, `OrderManager`, `Order`, `UnitOrders`, `Sync`
- **Chapter 1.4 — Deterministic Math and Coordinate Systems**
  - `WPos`, `WDist`, `WAngle`, `WVec`, `CPos`, `MPos`, `MapGrid`, fixed-point math, why floats are banned in simulation

### Part 2 — Data and Configuration

- **Chapter 2.1 — MiniYaml Syntax and Parser**
  - `MiniYaml`, `MiniYamlNode`, `MergePartial`, `MergeNode`, inheritance operators (`^`, `@`), string pooling
- **Chapter 2.2 — Manifest, mod.yaml, and ModData**
  - `Manifest`, `ModData`, `Ruleset`, `RulesetCache`, `Map` rules, `InstalledMusic`, `MapCompatibility`
- **Chapter 2.3 — FieldLoader and ObjectCreator**
  - `TypeParsers`, `GenericTypeParsers`, `BoxedInts`, `BooleanExpressionCache`, `IntegerExpressionCache`, `LoadFieldOrProperty`, `Require` attribute
- **Chapter 2.4 — Rulesets, Traits, Weapons, Warheads, and Projectiles**
  - How `ActorInfo`, `WeaponInfo`, `Warhead`, `Projectile`, `Bullet`, `Missile`, `LaserZap`, etc. are wired together
- **Chapter 2.5 — YAML Reference Baselines**
  - Cross-references to `docs.openra.net` (traits, weapons, Lua, sprite sequences) and how the online docs are generated from the same source

### Part 3 — Mod SDK, Build, and Deployment

- **Chapter 3.1 — Mod SDK Structure and Bootstrapping**
  - `mod.config`, `launch-game.sh`, `launch-game.cmd`, `make.cmd`, `make.ps1`, `Makefile`, `fetch-engine.sh`
- **Chapter 3.2 — Build Pipeline and Packaging**
  - `dotnet` / `msbuild`, `configure-system-libraries.sh`, AppImage, NSIS, macOS `.app`, Windows launcher
- **Chapter 3.3 — Custom DLL Injection and Engine Pinning**
  - `Assemblies` array in `mod.yaml`, `Assembly.LoadFrom`, `ObjectCreator`, `ResolvedAssemblies`, `ENGINE_VERSION` pinning

### Part 4 — Rendering and UI

- **Chapter 4.1 — Asset Pipeline and Sprite Loading**
  - `SpriteLoader`, `VxlLoader`, `SequenceProvider`, `SheetBuilder`, texture atlases, alpha trimming, `Sprite` UV insetting
- **Chapter 4.2 — World Renderer, Viewport, and Shaders**
  - `WorldRenderer`, `Viewport`, `Renderables`, `TerrainRenderer`, `glsl` shaders
- **Chapter 4.3 — Chrome UI and Widgets**
  - `chrome.yaml`, `WidgetLoader`, `Widget`, `Logic` classes, input routing, event bubbling, focus management
- **Chapter 4.4 — DPI Scaling and Framebuffer Isolation**
  - FBO separation of world and UI, fractional scaling, `SDL_GetRendererOutputSize`

### Part 5 — Audio

- **Chapter 5.1 — Audio Architecture**
  - `ISoundEngine`, `SoundDevice`, `Sound`, `OpenAlSoundEngine`, `DummySoundEngine`
- **Chapter 5.2 — Spatial Attenuation**
  - OpenAL distance model, `AL_REFERENCE_DISTANCE`, `AL_MAX_DISTANCE`, listener positioning, source pooling, instance-based attenuation
- **Chapter 5.3 — Music and Streaming**
  - `MusicPlaylist`, `MusicInfo`, `MusicInfo.Load`, VFS streaming, `OpenAlAsyncLoadSound`
- **Chapter 5.4 — Trait-Triggered Sound and Voices**
  - `AttackSounds`, `DeathSounds`, `AmbientSound`, `Voiced`, `SoundPool`, `PlayPredefined`, `PlayVoice` vs `PlayVoiceLocal`

### Part 6 — Scripting and Virtual File System

- **Chapter 6.1 — Lua Integration and Eluant**
  - `Eluant`, `LuaApi`, `LuaValue`, `ScriptContext`, `LuaScript`, sandboxing, memory allocators, coroutine integration
- **Chapter 6.2 — ScriptContext and Mission Scripting**
  - Global table scrubbing, `os`/`io`/`loadstring` removal, debug hooks, yield/resume mapping to `Activity`
- **Chapter 6.3 — Virtual File System**
  - `IPackage`, `Folder`, `MixFile`, `InstallShieldPackage`, `Pak`, `BigFile`, `ZipFile`, priority mounting, VFS traversal
- **Chapter 6.4 — Cryptography and Legacy Archive Decryption**
  - `BlowfishKeyProvider`, asymmetric public key, symmetric Blowfish, MIX index decryption
- **Chapter 6.5 — Asset Loaders**
  - `AudLoader`, `WavLoader`, `ImaAdpcmLoader`, `SpriteLoader`, `PngLoader`, `VxlReader`, `HvaReader`

### Part 7 — Random / Procedural Map Generator *(Deep Dive)*

- **Chapter 7.1 — Map Generation Pipeline Overview**
  - Entry points (`MapGeneratorLogic`, `MapGeneratorToolLogic`), `IEditorMapGeneratorInfo`, `IMapGeneratorInfo`, `MapGeneratorSettings`
- **Chapter 7.2 — Core Data Structures**
  - `CellLayer<T>`, `CellLayerBase`, `Matrix<T>`, `MapGrid`, `Map`, coordinate systems (`CPos`, `MPos`, `WPos`, `PPos`)
- **Chapter 7.3 — Procedural Algorithms**
  - `NoiseUtils` (Perlin, fractal, symmetric, amplitude functions), `MatrixUtils` (`BooleanBlotch`, blur, contour extraction), `Symmetry`
- **Chapter 7.4 — Terraformer**
  - `InitMap`, `BakeMap`, `ImproveSymmetry`, elevation slicing, boolean noise, painting, passages, actor planning
- **Chapter 7.5 — MultiBrush and Tile Placement**
  - `MultiBrush`, `MultiBrushInfo`, `MultiBrushSegment`, `Segment`, `Replaceability`, `Weight`, template-based tile painting
- **Chapter 7.6 — Mod-Specific Generators**
  - `D2kMapGenerator` (Dune 2000 desert, rock, cliffs, dunes, spice, worms)
  - `TSMapGenerator` (Tiberian Sun height maps, ramps, water cliffs, forests, Tiberium)
  - `ClassicMapGenerator` (C&C/RA water, cliffs, forests, roads, ore, civilians)
- **Chapter 7.7 — Resource and Actor Placement**
  - `PlanResources`, `ResourceBias`, spawn placement, symmetry, reserved areas
- **Chapter 7.8 — Generator Extension Points**
  - How to add a new `IEditorMapGeneratorInfo`, custom noise, custom `MatrixUtils` operators, custom `MultiBrush` templates, custom `Terraformer` methods
- **Chapter 7.9 — Generator File-by-File Reference**
  - A concise file-level index of every C# file in `OpenRA.Mods.Common\MapGenerator`, `OpenRA.Mods.D2k`, and `OpenRA.Mods.Cnc` related to generation, with a one-line description of each file's responsibility

### Part 8 — AI and Bot Framework

- **Chapter 8.1 — IBot and ModularBot**
  - `IBot`, `IBotInfo`, `ModularBot`, `DummyBot`, `MinOrderQuotientPerTick`, order throttling
- **Chapter 8.2 — Bot Module Catalog**
  - `BaseBuilderBotModule`, `HarvesterBotModule`, `ResourceMapBotModule`, `UnitBuilderBotModule`, `SquadManagerBotModule`, `SupportPowerBotModule`, `McvManagerBotModule`, `McvExpansionManagerBotModule`, `CaptureManagerBotModule`, `PowerDownBotManager`, `BuildingRepairBotModule`
- **Chapter 8.3 — Squads, States, and Fuzzy Combat**
  - `Squad`, `StateMachine`, `GroundStates`, `AirStates`, `ProtectionStates`, `AttackOrFleeFuzzy`
- **Chapter 8.4 — Deterministic Order Flow**
  - How `QueueOrder` → `World.IssueOrder` → `OrderManager.IssueOrder` → `localOrders`/`localImmediateOrders` preserves lockstep

### Part 9 — Network and Lockstep

- **Chapter 9.1 — OrderManager and Frame Pacing**
  - `TryTick`, `IsNetFrame`, `localOrders`, `localImmediateOrders`, `ProcessOrders`
- **Chapter 9.2 — Server and Connection**
  - `Server`, `Connection`, TCP sockets, handshake, order packet framing, non-blocking I/O
- **Chapter 9.3 — Sync Hashing and Desync Detection**
  - `SyncReport`, `World.SyncHash`, `ISync`, integer hashing, circular buffer

### Part 10 — Official Mods, Online References, and Mod Ecosystem

- **Chapter 10.1 — Official Mods (ra, cnc, d2k, ts)**
  - `mods/` directory, how each mod is a self-contained MiniYaml + asset package
- **Chapter 10.2 — Online Documentation**
  - `docs.openra.net` (release/playtest), trait/weapon/Lua/sprite-sequence references, how docs are generated
- **Chapter 10.3 — Community Resources**
  - `openra.net/book`, SteamsDev Lua tutorial, OpenRA Resource Center, Discord/wiki

### Appendices

- **Appendix A — File-to-Section Coverage Matrix**
- **Appendix B — Glossary of OpenRA Terms**
- **Appendix C — Quick Reference: Random Map Generator**
- **Appendix D — Quick Reference: Bot AI Module Interfaces**
- **Appendix E — Quick Reference: Audio Signal Chain**

## 4. Phased Build Plan

> **Status as of 2026-06-29:** The manual content is **complete**. All phases below are finished, and the project is now in the final production-polish phase (feedback triage, export pipeline, and licensing). The unchecked boxes in this section have been updated to `[x]` to reflect the actual state of the source files.

The build was split into **phases**. Each phase documented one or more Parts. Subagents ran in parallel within a phase, but phases were sequential so the manual could be reviewed and validated incrementally.

### Phase 0 — Infrastructure & Catalog

- [x] Create this `BUILD_PLAN.md`.
- [x] Generate a machine-readable file catalog (project → directory → file count → responsible section).
- [x] Generate a `RandomMapGenerator` file-by-file index.
- [x] Create a `Manual/` directory for the final compiled manual.
- [x] Establish documentation standards (template, citation format, required sections per chapter).

### Phase 1 — Part 1 (Core Engine Architecture)

- [x] Document ECS, Actor lifecycle, Trait interface caches.
- [x] Document Activities, `TickOuter`/`TickChild`, `ActionQueue`.
- [x] Document `World`, `OrderManager`, `Order`, `Sync`.
- [x] Document deterministic math and coordinate systems.
- [x] **Added:** Document Pathfinding & Movement (`Part_01_Chapter_05_Pathfinding_Movement.md`).
- [x] **Added:** Document Combat & Damage Resolution (`Part_01_Chapter_06_Combat_Damage.md`).

### Phase 2 — Part 2 (Data and Configuration)

- [x] Document MiniYaml parser, inheritance, merging.
- [x] Document `Manifest`, `ModData`, `Ruleset`, `RulesetCache`.
- [x] Document `FieldLoader` and `ObjectCreator`.
- [x] Document rules, weapons, warheads, projectiles.

### Phase 3 — Part 3 (Mod SDK, Build, Deployment)

- [x] Document Mod SDK and Project Structure (`Part_03_Chapter_01_Mod_SDK.md`).
- [x] **Added:** Document SDK Bootstrap (`Part_03_Chapter_02_SDK_Bootstrap.md`).
- [x] Document build pipeline, packaging, CI/CD (`Part_03_Chapter_03_Build_Packaging.md`).
- [x] Document custom DLL injection and engine pinning.

### Phase 4 — Part 4 (Rendering and UI)

- [x] Document asset pipeline and sprite loading.
- [x] Document world renderer, viewport, shaders.
- [x] Document Chrome UI and widgets.
- [x] Document FBO/DPI scaling.

### Phase 5 — Part 5 (Audio)

- [x] Document audio architecture.
- [x] Document spatial attenuation and OpenAL integration.
- [x] Document music streaming and VFS.
- [x] Document trait-triggered sound and voices.

### Phase 6 — Part 6 (Scripting and VFS)

- [x] Document Lua/Eluant integration.
- [x] Document `ScriptContext` sandbox.
- [x] Document VFS, packages, MIX decryption.
- [x] Document asset loaders.

### Phase 7 — Part 7 (Random Map Generator — Deep Dive)

- [x] Expand Module 7 into the full Part 7 chapters.
- [x] Produce file-by-file reference for every generator file.
- [x] Document algorithms with pseudocode.
- [x] Document extension points and worked examples.

### Phase 8 — Part 8 (AI)

- [x] Expand Module 7 AI section into full Part 8.
- [x] Document every bot module.
- [x] Document squad state machines and fuzzy logic.

### Phase 9 — Part 9 (Network)

- [x] Document `OrderManager`, server, connection, sync hashing.

### Phase 10 — Part 10 and Appendices

- [x] Document official mods and online resources.
- [x] Compile coverage matrix, glossary, quick references.
- [x] Merge all chapters into a single master manual (`OpenRA_Knowledge_Base_Manual.md`).
- [x] Final review pass for consistency, dead links, and missing sections.
- [x] **Added:** Appendices F (Testing), G (Asset Visual Reference), H (Advanced Modding Walkthroughs), I (Actor Reference).

## 5. Coverage Strategy: "Every Line of Code"

Because the engine has ~1,500 C# files, the manual cannot literally contain one paragraph per line. Instead, coverage is guaranteed by:

1. **Directory-level ownership**: every top-level directory in `OpenRA.Game` and `OpenRA.Mods.Common` is assigned to a Part/Chapter.
2. **File-level index**: every file in high-priority areas (map generator, bot modules, core ECS) gets a one-line responsibility entry in the file-by-file reference.
3. **Cross-referencing**: when a chapter mentions a class, it links to the file path and the chapter that owns the subsystem it depends on.
4. **Code-path tracing**: each chapter includes a "how it flows" subsection that shows the call chain from user/mod input through engine execution.
5. **Glossary**: every OpenRA-specific term (`Actor`, `Trait`, `Activity`, `Order`, `CellLayer`, `MapGrid`, etc.) is defined once and referenced consistently.
6. **Online docs sync**: trait/weapon/Lua API descriptions are cross-referenced with `docs.openra.net` so the manual does not duplicate generated reference material, but explains *how* that material is generated and *how* to extend it.

## 6. Subagent and Parallelization Strategy

Each phase launches multiple background `subagent_explore` or `subagent_general` agents:

- **One agent per chapter** (or one per major subsystem if a chapter is large).
- Agents receive:
  - The exact source directory or file list.
  - The chapter outline from this plan.
  - A documentation template (see Section 7).
  - A list of upstream/downstream dependencies they must cross-reference.
- Agents return a markdown chapter draft.
- The orchestrator (this session) reviews, merges, resolves cross-references, and writes the final file.

Special handling for the random map generator:

- A dedicated agent per sub-chapter in Part 7.
- A dedicated agent to produce the file-by-file index.
- A dedicated agent to produce pseudocode/algorithm descriptions for `NoiseUtils`, `MatrixUtils`, `Terraformer`, and `MultiBrush`.

## 7. Documentation Template for Each Chapter

Every chapter should follow this template:

```markdown
# Chapter X.Y — Title

## Purpose
One-paragraph statement of what this subsystem does and why it exists.

## Files
| File | Responsibility |
| :---- | :---- |
| `Relative/Path/To/File.cs` | Brief description |

## Architecture
- Key classes and interfaces.
- Class diagram in text (parent/child, composition, dependency arrows).

## Data Flow / Code Path
Step-by-step trace from trigger to output.

## Configuration (YAML)
Relevant MiniYaml keys and their relationship to C# fields.

## Interconnectivity
- What this subsystem depends on (with links).
- What depends on this subsystem (with links).

## Algorithms
Pseudocode or plain-language description of non-trivial algorithms.

## Extension Points
How a modder or engine developer can add to or override this subsystem.

## Common Pitfalls / Guardrails
Determinism rules, performance constraints, and known issues.

## References
- Internal chapters.
- Online docs URLs.
- Source file paths.
```

## 8. Output Structure

Final manual will be stored in:

```
C:\Users\Kmoney\Documents\AI Projects\Cameo Work\Game Sources and Development Reference Materials\1. OpenRA Manual\Manual\
```

As either:

- A single master `OpenRA Knowledge Base Manual.md` (if the final size is manageable), or
- A directory of per-part markdown files plus a master `INDEX.md`.

The random map generator will additionally be extracted as a standalone `Random Map Generator Deep Dive.md` so it can be consumed independently by an LLM.

## 9. First Action Items

1. Approve this plan or request changes.
2. Create the `Manual/` directory and file catalog.
3. Begin Phase 1 with parallel subagents documenting ECS, Activities, World/Orders, and Deterministic Math.

---

## Phase B/C/D Plan — Final Text-Only Polish and AI Scrutiny Round

### Goal
After Phase A structural improvements, complete the remaining medium-priority text-only fixes from the external LLM triage, then package the manual for a second round of AI review.

### Phase B — Technical Cleanup and Navigation

| Task | Status | What to do | Deliverable |
| :---- | :---- | :---- | :---- |
| **B1. Remove exact source line numbers** | ✅ Done | Regex-search all chapter files for patterns like `line 30`, `lines 178–235`, and `Actor.cs:129`. Replace with class/method/section references. Keep file and class references intact. | All chapters cite classes/methods, not exact line numbers. |
| **B2. Add source-version note** | ✅ Done | Insert a prominent “Current as of [OpenRA tag/date]” note in Part 0 and in the combined manual header. Update `assemble_manual.py` to stamp the header with the date/engine tag. | Part 0 and combined manual carry a clear version/date stamp. |
| **B3. Add combined-manual ToC** | ✅ Done | Extend `assemble_manual.py` to prepend a hyperlinked Markdown table of contents to the single-file edition, using `MASTER_INDEX` entries. | `OpenRA_Knowledge_Base_Manual.md` has a clickable top-level ToC. |
| **B4. Glossary cross-links** | ✅ Done | Add back-links in Appendix A from each term to the chapter(s) where it is discussed. | Glossary terms link to Part/Chapter references. |
| **B5. Cross-reference audit** | 🔄 In progress | Fix outdated references (e.g., `Part 3.2 (UI/Chrome)` → `Part 4.3`). Ensure all `See Part X.Y` links are consistent. | No stale or incorrect Part/Chapter references. |

### Phase C — Content Expansion

| Task | Status | What to do | Deliverable |
| :---- | :---- | :---- | :---- |
| **C1. Expand Appendix B** | 🔄 In progress | Add “good vs. bad” side-by-side YAML patterns and complete minimal actor examples for infantry, vehicle, building, and weapon. | Appendix B becomes a practical MiniYaml pattern reference. |
| **C2. Expand Appendix C** | ✅ Done | Add troubleshooting decision trees for: unit won’t move, weapon doesn’t fire, trait isn’t loading, and desync investigation. Include a top-10 desync-causes list. | Appendix C becomes a practical debugging playbook. |
| **C3. Full minimal-actor YAML examples** | 🔄 In progress | Ensure Part 2 and Part 10 contain complete before/after YAML snippets for common modding tasks. | Every major chapter has at least one concrete YAML example. |
| **C4. Optional “Part 7 at a glance”** | ⏸️ Deferred | Add a concise summary chapter for readers who want the RMG big picture without the full detail. | New optional chapter or section in Part 0. |

### Phase D — Optional Deep Dives

| Task | Status | What to do | Deliverable |
| :---- | :---- | :---- | :---- |
| **D1. Testing strategies** | ✅ Done | Add a new chapter or appendix covering unit tests, sync testing, and replay testing. | Standalone testing reference section. |
| **D2. Lobby/match setup** | ⏸️ Deferred | Expand Part 9.2 with the lobby state machine and `Session` data transition to `Game.StartGame`. | Part 9.2 covers lobby flow. |
| **D3. Asset-creation pipeline** | ⏸️ Deferred | Expand Part 10.3 with 8-bit palettes, remappable colors, and shadow rendering. | Asset-creation guidance for modders. |
| **D4. ASCII diagrams** | ✅ Done | Add text-only diagrams to Part 0 and Part 1.1 where they help beginners. | Diagrams in `Part_00_Foundations.md` and `Part_01_Chapter_01_ECS.md`. |

### Phase E — Verification and Packaging

1. ✅ Run `assemble_manual.py`.
2. ✅ Run `verify_paths.py` and fix any broken references.
3. ✅ Run a final consistency check: no exact line numbers, no emojis, all chapters follow the template, all cross-references valid.
4. 🔄 Create a review package: a clean copy of `OpenRA_Knowledge_Base_Manual.md` plus a review prompt.

### Phase F — AI Scrutiny Round (current)

1. 🔄 Prepare a focused review prompt covering the changed areas and asking for remaining gaps.
2. ⏳ Run one or more LLM reviews on the combined manual.
3. ⏳ Triage the new feedback into a Phase G plan.

### Out of scope (deferred until the text is stable)

- Raster images, non-ASCII diagrams, PDF formatting, and visual polish.
