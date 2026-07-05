# OpenRA Knowledge Base Manual — Build and Planning Files

This directory contains the planning, research, and project-tracking files used to construct the OpenRA Knowledge Base Manual.

## Where the readable manual lives

The main, readable manual is in the `Manual/` directory:

- `Manual/OpenRA_Knowledge_Base_Manual.md` — the complete, combined manual.
- `Manual/README.md` — guide to the manual and its organization.
- `Manual/build files/` — the individual source files (MASTER_INDEX, chapters, appendices) and the scripts that assemble them.

## Planning and research files in this directory

| File | Purpose |
| :---- | :---- |
| `README.md` | This file. Overview of the manual and chapter index. |
| `BUILD_PLAN.md` | Original manual construction plan. |
| `COVERAGE_MATRIX.md` | Mapping of OpenRA source directories to manual parts/chapters. |
| `FILE_INDEX.md` | Catalog of C# source files in the cloned OpenRA engine. |
| `TEMPLATE.md` | Template each chapter follows. |
| `DEVELOPMENT_LOG.md` | Detailed development history of the manual. |
| `Module 1_*.md` – `Module 7_*.md` | Research modules covering OpenRA architecture, MiniYaml, Mod SDK, graphics/UI, AI, scripting, procedural generation, audio, and bot AI. |
| `OpenRA Knowledge Base Compilation ....docx.md` | Compiled research review. |
| `OpenRA Knowledgebase Scoping Plan ....docx.md` | Initial scoping document. |

## Source file index

The individual chapters and appendices are in `Manual/build files/`:

| File | Title |
| :---- | :---- |
| `Manual/build files/MASTER_INDEX.md` | Master Index |
| `Manual/build files/chapters/Part_00_Foundations.md` | Foundations and How to Use This Manual |
| `Manual/build files/chapters/Part_01_Chapter_01_ECS.md` | ECS, Actors, and Traits |
| `Manual/build files/chapters/Part_01_Chapter_02_Activities.md` | Activity System |
| `Manual/build files/chapters/Part_01_Chapter_03_World_Orders.md` | World, OrderManager, and Orders |
| `Manual/build files/chapters/Part_01_Chapter_04_Math.md` | Math, Coordinates, and Determinism |
| `Manual/build files/chapters/Part_01_Chapter_05_Pathfinding_Movement.md` | Pathfinding and Movement |
| `Manual/build files/chapters/Part_01_Chapter_06_Combat_Damage.md` | Combat and Damage Resolution |
| `Manual/build files/chapters/Part_02_Chapter_01_MiniYaml.md` | MiniYaml Parser |
| `Manual/build files/chapters/Part_02_Chapter_02_Manifest.md` | Manifest and Mod Metadata |
| `Manual/build files/chapters/Part_02_Chapter_03_FieldLoader.md` | FieldLoader |
| `Manual/build files/chapters/Part_02_Chapter_04_Rules_Weapons.md` | Rulesets, Actors, and Weapons |
| `Manual/build files/chapters/Part_03_Chapter_01_Mod_SDK.md` | Mod SDK and Project Structure |
| `Manual/build files/chapters/Part_03_Chapter_02_SDK_Bootstrap.md` | Mod SDK Bootstrap |
| `Manual/build files/chapters/Part_03_Chapter_03_Build_Packaging.md` | Build Pipeline and Packaging |
| `Manual/build files/chapters/Part_04_Chapter_01_Renderer.md` | Renderer, Sheet, and Sprite |
| `Manual/build files/chapters/Part_04_Chapter_02_WorldRenderer.md` | WorldRenderer |
| `Manual/build files/chapters/Part_04_Chapter_03_Widgets.md` | Widgets and Chrome |
| `Manual/build files/chapters/Part_04_Chapter_04_Viewport_Input.md` | Viewport and Input |
| `Manual/build files/chapters/Part_05_Chapter_01_Audio_Architecture.md` | Audio Architecture |
| `Manual/build files/chapters/Part_05_Chapter_02_Spatial_Attenuation.md` | Spatial Attenuation |
| `Manual/build files/chapters/Part_05_Chapter_03_Music.md` | Music |
| `Manual/build files/chapters/Part_05_Chapter_04_Sound_Triggers.md` | Sound Triggers |
| `Manual/build files/chapters/Part_06_Chapter_01_Lua_Eluant.md` | Lua Scripting and Eluant |
| `Manual/build files/chapters/Part_06_Chapter_02_ScriptContext.md` | ScriptContext Lifecycle and Bindings |
| `Manual/build files/chapters/Part_06_Chapter_03_VFS.md` | Virtual File System |
| `Manual/build files/chapters/Part_06_Chapter_04_Crypto.md` | Crypto Utilities and Player Authentication |
| `Manual/build files/chapters/Part_06_Chapter_05_Asset_Loaders.md` | Asset Loaders |
| `Manual/build files/chapters/Part_07_Chapter_01_Pipeline.md` | RMG Pipeline |
| `Manual/build files/chapters/Part_07_Chapter_02_Data_Structures.md` | RMG Data Structures |
| `Manual/build files/chapters/Part_07_Chapter_03_Algorithms.md` | RMG Algorithms |
| `Manual/build files/chapters/Part_07_Chapter_04_Terraformer.md` | RMG Terraformer |
| `Manual/build files/chapters/Part_07_Chapter_05_MultiBrush.md` | RMG MultiBrush |
| `Manual/build files/chapters/Part_07_Chapter_06_Mod_Generators.md` | RMG Mod Generators |
| `Manual/build files/chapters/Part_07_Chapter_07_Resources_Actors.md` | RMG Resources and Actors |
| `Manual/build files/chapters/Part_07_Chapter_08_Extension_Points.md` | RMG Extension Points |
| `Manual/build files/chapters/Part_07_Chapter_09_File_Index.md` | RMG File Index |
| `Manual/build files/chapters/Part_08_Chapter_01_IBot.md` | IBot and ModularBot |
| `Manual/build files/chapters/Part_08_Chapter_02_Bot_Modules.md` | Bot Modules |
| `Manual/build files/chapters/Part_08_Chapter_03_Squads.md` | Bot Squads and Combat Heuristics |
| `Manual/build files/chapters/Part_08_Chapter_04_Order_Flow.md` | Bot Order Flow |
| `Manual/build files/chapters/Part_09_Chapter_01_OrderManager.md` | OrderManager and Lockstep Foundation |
| `Manual/build files/chapters/Part_09_Chapter_02_Server_Connection.md` | Server and Connection Layer |
| `Manual/build files/chapters/Part_09_Chapter_03_Sync_Hashing.md` | Sync Hashing and Determinism |
| `Manual/build files/chapters/Part_10_Chapter_01_Official_Mods.md` | Official Mods |
| `Manual/build files/chapters/Part_10_Chapter_02_Online_References.md` | Online Services and References |
| `Manual/build files/chapters/Part_10_Chapter_03_Port_And_Modding.md` | Porting, Modding, and Developer Workflows |
| `Manual/build files/appendices/Appendix_A_Glossary.md` | Glossary of OpenRA Terms |
| `Manual/build files/appendices/Appendix_B_Common_YAML_Patterns.md` | Common MiniYaml Patterns |
| `Manual/build files/appendices/Appendix_C_Debugging.md` | Debugging, Logs, and Troubleshooting |
| `Manual/build files/appendices/Appendix_D_Engine_Conventions.md` | Engine Coding and Architectural Conventions |
| `Manual/build files/appendices/Appendix_E_Practical_Recipes.md` | Practical Modding Recipes |
| `Manual/build files/appendices/Appendix_F_Testing.md` | Testing Strategies |

## Note on formatting

The content is written in Markdown. Final formatting (fonts, styles, DOCX conversion, page layout) will be handled by a better-equipped tool (Claude, Google Docs, etc.) in a later step. The focus here is on accuracy, depth, and clear explanations.
