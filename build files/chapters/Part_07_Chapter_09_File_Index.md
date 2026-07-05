# Chapter 7.9 — Random Map Generator File Index

## Purpose

The OpenRA [Random Map Generator (RMG)](../appendices/Appendix_A_Glossary.md) spans the engine, the common mod code, and the official mods. This chapter is a curated reference of the files involved in random/procedural map generation, grouped by role so a developer can locate the right source when extending or debugging a generator.

## Learning Objectives


After studying this chapter, you should be able to:

- Navigate the file structure of the random map generator across engine, common, and mod code.
- Locate the interface contracts, shared infrastructure, and mod-specific generators.
- Identify YAML configuration files for generator registration and tileset brushes.
- Find the editor and UI files that host generator panels.
- Use this chapter as a reference when extending or debugging a generator.

## Core Engine Contracts

| File | Responsibility |
| :---- | :---- |
| `OpenRA.Game/Traits/TraitsInterfaces.cs` | Defines `IMapGeneratorInfo`, the base interface implemented by every generator. |
| `OpenRA.Game/Map/Map.cs` | The `Map` object being generated; holds `Tiles`, `Resources`, `ActorDefinitions`, `MapPlayers`, and `AllCells`. |
| `OpenRA.Game/Map/MapGrid.cs` | [MapGrid](../appendices/Appendix_A_Glossary.md) coordinate grid and cell geometry; determines how cell indices map to world positions. |
| `OpenRA.Game/MiniYaml.cs` | [MiniYaml](../appendices/Appendix_A_Glossary.md) parsing and merging; `MapGenerationArgs.Settings` is a `MiniYaml` object. |
| `OpenRA.Game/FieldLoader.cs` | [FieldLoader](../appendices/Appendix_A_Glossary.md) loads YAML values into C# fields via attributes such as `[FieldLoader.Require]`, `[FieldLoader.LoadUsing]`, and `[FieldLoader.Ignore]`. |
| `OpenRA.Game/FieldSaver.cs` | Formats C# values back into YAML strings used by option emission. |
| `OpenRA.Game/Support/MersenneTwister.cs` | Deterministic random source used by all generators. |
| `OpenRA.Game/Primitives/TypeDictionary.cs` | Storage of trait info instances on `ActorInfo` objects. |
| `OpenRA.Support/Exts.cs` | Utility helpers such as `TryParseUshortInvariant`. |

## Common Map Generator Infrastructure

| File | Responsibility |
| :---- | :---- |
| `OpenRA.Mods.Common/TraitsInterfaces.cs` | `IEditorMapGeneratorInfo`, `IMapGeneratorSettings`, `MapGenerationException`, `IEditorTool`. |
| `OpenRA.Mods.Common/MapGenerator/MapGeneratorSettings.cs` | `MapGeneratorSettings` and the four option classes (`Boolean`, `Integer`, `MultiChoice`, `MultiIntegerChoice`). |
| `OpenRA.Mods.Common/MapGenerator/Terraformer.cs` | [Terraformer](../appendices/Appendix_A_Glossary.md) high-level orchestration: `InitMap`, `PickTile`, `SliceElevation`, `ElevationNoiseMatrix`, `Symmetry`, `BakeMap`, `ReorderPlayerSpawns`, actor placement. |
| `OpenRA.Mods.Common/MapGenerator/TilingPath.cs` | Path-based tile assignment for coastlines, cliffs, roads, and water cliffs. |
| `OpenRA.Mods.Common/MapGenerator/MultiBrush.cs` | [MultiBrush](../appendices/Appendix_A_Glossary.md) procedural tile brush that combines multiple tiles into a single stamp. |
| `OpenRA.Mods.Common/MapGenerator/RampTiler.cs` | Cliff/ramp tiling for height transitions. |
| `OpenRA.Mods.Common/MapGenerator/LatTiler.cs` | Low-level lookup and transition tiling. |
| `OpenRA.Mods.Common/MapGenerator/MatrixUtils.cs` | Boolean and numeric matrix operations (thresholds, blotch, dilation, contour detection, distance transforms). |
| `OpenRA.Mods.Common/MapGenerator/CellLayerUtils.cs` | Helpers that operate on `[CellLayer<T>](../appendices/Appendix_A_Glossary.md)` objects. |
| `OpenRA.Mods.Common/MapGenerator/NoiseUtils.cs` | Fractal noise generation, smoothing, and turbulence used by `ElevationNoiseMatrix`. |
| `OpenRA.Mods.Common/Traits/World/ClearMapGenerator.cs` | Minimal generator and editor tool reference. |
| `OpenRA.Mods.Common/Traits/World/ClassicMapGenerator.cs` | The Red Alert / Tiberian Dawn generator with full `Parameters` and phases. |
| `OpenRA.Mods.Common/MapGenerator/ActorPlan.cs` | Mutable [ActorPlan](../appendices/Appendix_A_Glossary.md) used by `Terraformer` to stage spawns, resources, and props. |

## Mod-Specific Generators

| File | Responsibility |
| :---- | :---- |
| `OpenRA.Mods.D2k/Traits/World/D2kMapGenerator.cs` | Dune 2000 Arrakis generator (sand, rock platforms, spice, dunes). |
| `OpenRA.Mods.Cnc/Traits/World/TSMapGenerator.cs` | Tiberian Sun generator (full-height cliffs, ramps, Blue/Green Tiberium, forests). |

![Yaml configuration diagram](images/Part_07_Chapter_09_File_Index-annotated-yaml-snippet-diagram-showing-the-key-fields-and-ho-6a1b98.svg)

## YAML Configuration


| File | Responsibility |
| :---- | :---- |
| `mods/ra/rules/map-generators.yaml` | Red Alert generator registration, presets, and options. |
| `mods/cnc/rules/map-generators.yaml` | Tiberian Dawn generator registration, presets, and options. |
| `mods/d2k/rules/map-generators.yaml` | Dune 2000 generator registration, presets, and options. |
| `mods/ts/rules/map-generators.yaml` | Tiberian Sun generator registration, presets, and options. |
| `mods/ra/tilesets/*.yaml` | Red Alert tilesets including `MultiBrushCollections/Segmented`. |
| `mods/cnc/tilesets/*.yaml` | Tiberian Dawn tilesets including `MultiBrushCollections/Segmented`. |
| `mods/d2k/tilesets/arrakis.yaml` | Arrakis tileset including `MultiBrushCollections/Segmented`. |
| `mods/ts/tilesets/*.yaml` | Tiberian Sun tilesets including `MultiBrushCollections/Segmented`. |
| `mods/*/rules/defaults.yaml` | Abstract actor definitions inherited by generated actors. |
| `mods/*/rules/palettes.yaml` | Palettes referenced by generated terrain and actors. |

## Editor and UI

| File | Responsibility |
| :---- | :---- |
| `OpenRA.Mods.Common/Widgets/Logic/Editor/MapToolsLogic.cs` | Discovers editor tools via `world.WorldActor.TraitsImplementing<IEditorTool>()`. |
| `OpenRA.Mods.Common/Widgets/Logic/Editor/MapGeneratorToolLogic.cs` | Logic that wires the generator option panel to the generator's `GetSettings()` and `Generate()` calls. |
| `mods/*/chrome/*.yaml` | Chrome definitions for the editor panels and the default `MAP_GENERATOR_TOOL_PANEL`. |

## Related Manual Chapters

- [Part 2.1 — MiniYaml Parser](Part_02_Chapter_01_MiniYaml.md)
- [Part 2.3 — FieldLoader](Part_02_Chapter_03_FieldLoader.md)
- [Part 3.1 — Mod SDK and Project Structure](Part_03_Chapter_01_Mod_SDK.md)
- [Part 7.2 — Map Generation Data Structures](Part_07_Chapter_02_Data_Structures.md)
- [Part 7.3 — Map Generation Algorithms](Part_07_Chapter_03_Algorithms.md)
- [Part 7.4 — Terraformer](Part_07_Chapter_04_Terraformer.md)
- [Part 7.5 — MultiBrush and Tile Placement](Part_07_Chapter_05_MultiBrush.md)
- [Part 7.6 — Mod-Specific Generators](Part_07_Chapter_06_Mod_Generators.md)
- [Part 7.7 — Resource and Actor Placement](Part_07_Chapter_07_Resources_Actors.md)
- [Part 7.8 — Random Map Generator Extension Points](Part_07_Chapter_08_Extension_Points.md)

## How to Use This Index

When extending a generator, start with the interface and settings files in the Core and Common sections, then read the mod-specific generator closest to your desired style. When debugging a crash or unexpected output, use the Infrastructure section to find the helper class responsible for the phase producing the bad result. When adding new tilesets or presets, use the YAML Configuration section as the source of truth for syntax and existing values.

## Summary

This chapter indexes the files that make up the OpenRA [Random Map Generator (RMG)](../appendices/Appendix_A_Glossary.md), grouped by engine contracts, common infrastructure, mod-specific generators, editor UI, and YAML configuration.

## What to read next

- [Part 7.1 — Map Generation Pipeline Overview](Part_07_Chapter_01_Pipeline.md) for the end-to-end pipeline and UI entry points.
- [Part 7.4 — Terraformer](Part_07_Chapter_04_Terraformer.md) for the high-level orchestration code referenced in the Common Infrastructure section.
- [Part 7.8 — Random Map Generator Extension Points](Part_07_Chapter_08_Extension_Points.md) for the formal extension points when adding new generators or brushes.