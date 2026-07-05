# OpenRA Knowledge Base Manual — Master Index

This index provides a single-page overview of every chapter and appendix in the manual, grouped by part. Each entry links the file name to the topic so you can navigate quickly.

## Part 0 — Foundations

| File | Topic | Summary |
| :---- | :---- | :---- |
| `chapters/Part_00_Foundations.md` | How to Use This Manual | Learning paths, key concepts, and conventions. |

## Part 1 — Core Engine Architecture

| File | Topic | Summary |
| :---- | :---- | :---- |
| `chapters/Part_01_Chapter_01_ECS.md` | ECS, Actors, and Traits | Actor/Trait split, TraitInfo lifecycle, dependency resolution, caching. |
| `chapters/Part_01_Chapter_02_Activities.md` | Activity System | Multi-tick actor plans, activity chaining, tick loop. |
| `chapters/Part_01_Chapter_03_World_Orders.md` | World, OrderManager, and Orders | Simulation container, order dispatch, lockstep boundary. |
| `chapters/Part_01_Chapter_04_Math.md` | Math, Coordinates, and Determinism | World/cell coordinates, fixed-point math, determinism rules. |
| `chapters/Part_01_Chapter_05_Pathfinding_Movement.md` | Pathfinding and Movement | Locomotor, Mobile, PathFinder, HierarchicalPathFinder, Move activity. |
| `chapters/Part_01_Chapter_06_Combat_Damage.md` | Combat and Damage Resolution | Attack, Armament, projectiles, warheads, Health, Armor. |

## Part 2 — Data and Configuration

| File | Topic | Summary |
| :---- | :---- | :---- |
| `chapters/Part_02_Chapter_01_MiniYaml.md` | MiniYaml Parser | YAML dialect, inheritance, merging, node removal. |
| `chapters/Part_02_Chapter_02_Manifest.md` | Manifest and Mod Metadata | `mod.yaml` structure, mod discovery, global mod data. |
| `chapters/Part_02_Chapter_03_FieldLoader.md` | FieldLoader | YAML-to-C# deserialization, custom loaders, attributes. |
| `chapters/Part_02_Chapter_04_Rules_Weapons.md` | Rulesets, Actors, and Weapons | ActorInfo, WeaponInfo, ruleset loading, warheads. |

## Part 3 — Mod SDK, Build, and Deployment

| File | Topic | Summary |
| :---- | :---- | :---- |
| `chapters/Part_03_Chapter_01_Mod_SDK.md` | Mod SDK and Project Structure | Mod package structure, `mod.yaml`, `ModData`, object creation. |
| `chapters/Part_03_Chapter_02_SDK_Bootstrap.md` | Mod SDK Bootstrap | SDK bootstrap scripts, `mod.config`, engine pinning. |
| `chapters/Part_03_Chapter_03_Build_Packaging.md` | Build Pipeline and Packaging | Makefile, `dotnet publish`, platform packaging, utility commands. |

## Part 4 — Rendering and UI

| File | Topic | Summary |
| :---- | :---- | :---- |
| `chapters/Part_04_Chapter_01_Renderer.md` | Renderer, Sheet, and Sprite | Sprite sheets, palettes, renderables, shader pipeline. |
| `chapters/Part_04_Chapter_02_WorldRenderer.md` | WorldRenderer | World-to-screen rendering, renderable sorting, depth buffer. |
| `chapters/Part_04_Chapter_03_Widgets.md` | Widgets and Chrome | UI tree, chrome layouts, widget logic, input handling. |
| `chapters/Part_04_Chapter_04_Viewport_Input.md` | Viewport and Input | Camera, zoom, coordinate transforms, input dispatch. |

## Part 5 — Audio

| File | Topic | Summary |
| :---- | :---- | :---- |
| `chapters/Part_05_Chapter_01_Audio_Architecture.md` | Audio Architecture | Sound engine, loaders, audio playback lifecycle. |
| `chapters/Part_05_Chapter_02_Spatial_Attenuation.md` | Spatial Attenuation | 3D audio attenuation, OpenAL, listener position. |
| `chapters/Part_05_Chapter_03_Music.md` | Music | MusicPlaylist, track selection, loading. |
| `chapters/Part_05_Chapter_04_Sound_Triggers.md` | Sound Triggers | Notification, voice, and ambient sound triggers. |

## Part 6 — Scripting and Virtual File System

| File | Topic | Summary |
| :---- | :---- | :---- |
| `chapters/Part_06_Chapter_01_Lua_Eluant.md` | Lua Scripting and Eluant | Lua runtime, globals, bindings, safety. |
| `chapters/Part_06_Chapter_02_ScriptContext.md` | ScriptContext Lifecycle and Bindings | Script context creation, tick, death, debugging. |
| `chapters/Part_06_Chapter_03_VFS.md` | Virtual File System | Packages, loaders, mounting, file lookup. |
| `chapters/Part_06_Chapter_04_Crypto.md` | Crypto Utilities and Player Authentication | Cryptography, player IDs, authentication. |
| `chapters/Part_06_Chapter_05_Asset_Loaders.md` | Asset Loaders | Sprite, sound, video, and package loaders. |

## Part 7 — Random / Procedural Map Generator

| File | Topic | Summary |
| :---- | :---- | :---- |
| `chapters/Part_07_Chapter_01_Pipeline.md` | RMG Pipeline | End-to-end map generation pipeline. |
| `chapters/Part_07_Chapter_02_Data_Structures.md` | RMG Data Structures | CellLayer, MapGrid, actor plans, geometry. |
| `chapters/Part_07_Chapter_03_Algorithms.md` | RMG Algorithms | Noise, pathfinding, partitioning, terrain selection. |
| `chapters/Part_07_Chapter_04_Terraformer.md` | RMG Terraformer | Terrain generation and tile placement. |
| `chapters/Part_07_Chapter_05_MultiBrush.md` | RMG MultiBrush | Multi-tile brushes and stamping. |
| `chapters/Part_07_Chapter_06_Mod_Generators.md` | RMG Mod Generators | Per-mod generator registration and configuration. |
| `chapters/Part_07_Chapter_07_Resources_Actors.md` | RMG Resources and Actors | Resource placement, actor placement, base setup. |
| `chapters/Part_07_Chapter_08_Extension_Points.md` | RMG Extension Points | How to add custom generators and brushes. |
| `chapters/Part_07_Chapter_09_File_Index.md` | RMG File Index | Reference list of RMG source files. |

## Part 8 — AI and Bot Framework

| File | Topic | Summary |
| :---- | :---- | :---- |
| `chapters/Part_08_Chapter_01_IBot.md` | IBot and ModularBot | Bot interfaces, modular bot architecture, activation. |
| `chapters/Part_08_Chapter_02_Bot_Modules.md` | Bot Modules | Production, building, support power, and support modules. |
| `chapters/Part_08_Chapter_03_Squads.md` | Bot Squads and Combat Heuristics | Squad lifecycle, state machine, fuzzy attack/flee. |
| `chapters/Part_08_Chapter_04_Order_Flow.md` | Bot Order Flow | How bot orders enter the simulation. |

## Part 9 — Network and Lockstep

| File | Topic | Summary |
| :---- | :---- | :---- |
| `chapters/Part_09_Chapter_01_OrderManager.md` | OrderManager and Lockstep Foundation | Client-side order buffering and frame advancement. |
| `chapters/Part_09_Chapter_02_Server_Connection.md` | Server and Connection Layer | Server, connection, packet handling, lobby. |
| `chapters/Part_09_Chapter_03_Sync_Hashing.md` | Sync Hashing and Determinism | Sync hash, deterministic state, desync detection. |

## Part 10 — Official Mods and Ecosystem

| File | Topic | Summary |
| :---- | :---- | :---- |
| `chapters/Part_10_Chapter_01_Official_Mods.md` | Official Mods | RA, C&C, D2K, TS structure and mod-specific code. |
| `chapters/Part_10_Chapter_02_Online_References.md` | Online Services and References | Master server, LAN, map download, replay, web services. |
| `chapters/Part_10_Chapter_03_Port_And_Modding.md` | Porting, Modding, and Developer Workflows | Asset porting, trait creation, debugging, workflows. |

## Appendices

| File | Topic | Summary |
| :---- | :---- | :---- |
| `appendices/Appendix_A_Glossary.md` | Glossary | Definitions of OpenRA terms. |
| `appendices/Appendix_B_Common_YAML_Patterns.md` | Common YAML Patterns | Reusable MiniYaml patterns and examples. |
| `appendices/Appendix_C_Debugging.md` | Debugging and Troubleshooting | Logs, debug overlays, common problems. |
| `appendices/Appendix_D_Engine_Conventions.md` | Engine Conventions and Style | Coding style, trait conventions, sync safety. |
| `appendices/Appendix_E_Practical_Recipes.md` | Practical Modding Recipes | Copy-paste recipes for weapons, units, buildings, powers, conditions, traits, queues. |
| `appendices/Appendix_F_Testing.md` | Testing Strategies | Unit tests, sync testing, replay testing, performance testing, and common pitfalls. |
| `appendices/Appendix_H_Asset_Visual_Reference.md` | Asset Visual Reference | File formats, YAML definitions, and engine classes for every OpenRA asset category. |
| `appendices/Appendix_G_Advanced_Modding_Walkthroughs.md` | Advanced Modding Walkthroughs | Complete walkthroughs for Chrome UI, Lua missions, crates, resources, shroud, capture, cloak, voxels, and AI. |
| `appendices/Appendix_I_Actor_Reference.md` | Actor Reference | Auto-generated cameo + stat tables for every buildable actor in the ra, cnc, and d2k mods. |
| `appendices/Appendix_J_Terrain_Tiles.md` | Terrain Tile Reference | Per-mod tileset terrain types and representative templates for RA, C&C, D2K, and TS. |
| `appendices/Appendix_K_Environmental_Actors.md` | Environmental Actor Reference | Trees, rocks, civilian buildings, bridges, walls, gates, crates, and resource spawns across the four official mods. |

## Reference Files

| File | Purpose |
| :---- | :---- |
| `MASTER_INDEX.md` | This file — single-page master navigation. |
| `README.md` | Manual root README — start here for navigation. |
| `build files/README.md` | Manual introduction and chapter index. |
| `OpenRA Manual Build Files/TEMPLATE.md` | Chapter template. |
| `OpenRA Manual Build Files/FILE_INDEX.md` | C# source file listing by directory. |
| `OpenRA Manual Build Files/COVERAGE_MATRIX.md` | Source-to-chapter coverage mapping. |
| `DEVELOPMENT_LOG.md` | Project development log. |
| `OpenRA Manual Build Files/BUILD_PLAN.md` | Manual build plan. |
