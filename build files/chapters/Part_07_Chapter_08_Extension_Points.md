# Chapter 7.8 — Random Map Generator Extension Points

## Purpose

The OpenRA [Random Map Generator (RMG)](../appendices/Appendix_A_Glossary.md) is deliberately split into reusable pieces. The shared engine code in `OpenRA.Mods.Common` provides the toolbox—`[Terraformer](../appendices/Appendix_A_Glossary.md)`, `TilingPath`, `[MultiBrush](../appendices/Appendix_A_Glossary.md)`, `MatrixUtils`, `CellLayerUtils`, and `NoiseUtils`—while each [Mod](../appendices/Appendix_A_Glossary.md) provides its own generator class that decides how to use that toolbox. This chapter describes the formal extension points: how to add a brand-new generator, how to expose editor options, how to extend an existing generator without recompiling the engine, and how to add new tileset-specific brush collections.

## Learning Objectives


After studying this chapter, you should be able to:

- Explain the formal extension points for OpenRA's random map generator.
- Implement a new generator by creating IEditorMapGeneratorInfo and IEditorTool classes.
- Configure generator options using MapGeneratorSettings and the four option types.
- Describe how the Parameters class bridges YAML settings to typed generator fields.
- Add new tileset brush collections under MultiBrushCollections.
- Extend an existing generator with new YAML options without recompiling the engine.

## Files

| File | Responsibility |
| :---- | :---- |
| `OpenRA.Game/Traits/TraitsInterfaces.cs` | Core `IMapGeneratorInfo` interface. |
| `OpenRA.Mods.Common/TraitsInterfaces.cs` | `IEditorMapGeneratorInfo`, `IMapGeneratorSettings`, `MapGenerationException`. |
| `OpenRA.Mods.Common/MapGenerator/MapGeneratorSettings.cs` | `MapGeneratorSettings` and the four option types (`Boolean`, `Integer`, `MultiChoice`, `MultiIntegerChoice`). |
| `OpenRA.Mods.Common/Traits/World/ClearMapGenerator.cs` | Minimal example of a generator and editor tool. |
| `OpenRA.Mods.Common/Traits/World/ClassicMapGenerator.cs` | Complex generator with a full `Parameters` class and YAML settings. |
| `OpenRA.Mods.D2k/Traits/World/D2kMapGenerator.cs` | Mod-specific generator example. |
| `OpenRA.Mods.Cnc/Traits/World/TSMapGenerator.cs` | Mod-specific generator example with full-height cliffs. |
| `mods/*/rules/map-generators.yaml` | YAML registration of generators and their options. |
| `mods/*/tilesets/*.yaml` | Tileset `MultiBrushCollections/Segmented` definitions. |

![Architecture diagram](images/Part_07_Chapter_08_Extension_Points-architecture-diagram-showing-the-main-classes-interfaces-and-9161e6.svg)

## Architecture


### Two interfaces every generator must implement

The generator contract is defined in two layers:

```
[IMapGeneratorInfo] <--extends-- [IEditorMapGeneratorInfo]
```

`IMapGeneratorInfo` (engine, `OpenRA.Game/Traits/TraitsInterfaces.cs`) is the runtime contract:

```csharp
public interface IMapGeneratorInfo : ITraitInfoInterface
{
    string Type { get; }
    string Name { get; }
    string MapTitle { get; }
    Map Generate(ModData modData, MapGenerationArgs args);
    bool TryGenerateMetadata(ModData modData, MapGenerationArgs args, out MapPlayers players, out Dictionary<string, MiniYaml> rules);
}
```

`IEditorMapGeneratorInfo` (Common, `OpenRA.Mods.Common/TraitsInterfaces.cs`) adds editor integration:

```csharp
public interface IEditorMapGeneratorInfo : IMapGeneratorInfo
{
    ImmutableArray<string> Tilesets { get; }
    IMapGeneratorSettings GetSettings();
}
```

A generator is a `[TraitInfo](../appendices/Appendix_A_Glossary.md)` placed on `SystemActors.EditorWorld`. The concrete generator class (e.g., `ClearMapGenerator`) only implements `IEditorTool` and is what the editor UI instantiates; the heavy work is done by the `Info` class (e.g., `ClearMapGeneratorInfo`). This mirrors the normal OpenRA trait pattern.

### Settings and option objects

The editor option panel is produced by `IMapGeneratorSettings.GetSettings()`. The canonical implementation is `MapGeneratorSettings` in `OpenRA.Mods.Common/MapGenerator/MapGeneratorSettings.cs`. It parses a `Settings` [MiniYaml](../appendices/Appendix_A_Glossary.md) subtree and creates a typed option object for each `BooleanOption@`, `IntegerOption@`, `MultiChoiceOption@`, and `MultiIntegerChoiceOption@` entry.

Each option subclasses `MapGeneratorOption` and overrides `GetSettings(ITerrainInfo terrainInfo, int playerCount)` to emit `MiniYamlNode` values that the generator will later load through its `Parameters` class. Choices in a `MultiChoiceOption` can be gated by `Tileset` and `Players`, so the same generator can show different defaults for different tilesets and player counts.

### The `Parameters` bridge

Every non-trivial generator defines an inner `Parameters` class. The constructor of `Parameters` receives the map and the `MapGenerationArgs` produced by the settings object, then uses `[FieldLoader](../appendices/Appendix_A_Glossary.md).Load` to turn the emitted MiniYaml into typed fields. `Parameters` is the place where a mod author declares every tunable knob (feature sizes, thresholds, terrain index sets, resource types, spawn counts, etc.) without changing the engine code.

### Editor wiring

The editor discovers generators from the `^MapGenerators:` rule section. It calls `GetSettings()` to build the option panel, collects the user choices into a `MapGenerationArgs`, and then calls `Generate()` and `TryGenerateMetadata()` to produce the final map and player definitions.

![Data flow  code path diagram](images/Part_07_Chapter_08_Extension_Points-sequence-flow-diagram-tracing-the-execution-path-from-trigge-035864.svg)

## Data Flow / Code Path


### Adding a new generator from scratch

1. Create a class `MyMapGeneratorInfo` that inherits `TraitInfo` and implements `IEditorMapGeneratorInfo`.
2. Declare required metadata fields: `Type`, `Name`, `Tilesets`, `MapTitle`, and `PanelWidget`.
3. Add a `Settings` MiniYaml field loaded via `SettingsLoader` and a `GetSettings()` method returning `new MapGeneratorSettings(this, Settings)`.
4. Implement `Generate(ModData, MapGenerationArgs)` to create a `Map`, build a `Parameters`, instantiate `Terraformer`, run the chosen terrain/actor phases, and call `BakeMap()`.
5. Implement `TryGenerateMetadata(...)` to return a `MapPlayers` block and any rule overrides.
6. Implement `Create(...)` to return the `IEditorTool` instance (usually just a wrapper).
7. Add the generator to the mod's `rules/map-generators.yaml` under `^MapGenerators:`.
8. Add Fluent labels for `Name`, option labels, and choice labels.

### Minimal generator example: ClearMapGenerator

`OpenRA.Mods.Common/Traits/World/ClearMapGenerator.cs` is the smallest possible generator. It declares metadata, returns a single `MapGeneratorSettings` that expects a `Tile` parameter, and produces a flat map of that tile:

```csharp
public Map Generate(ModData modData, MapGenerationArgs args)
{
    var random = new MersenneTwister();
    var terrainInfo = modData.DefaultTerrainInfo[args.Tileset];

    if (!Exts.TryParseUshortInvariant(args.Settings.NodeWithKey("Tile").Value.Value, out var tileType))
        throw new YamlException("Illegal tile type");

    if (!terrainInfo.TryGetTerrainInfo(new TerrainTile(tileType, 0), out var _))
        throw new MapGenerationException("Illegal tile type");

    var map = new Map(modData, terrainInfo, args.Size);
    var terraformer = new Terraformer(args, map, modData, [], Symmetry.Mirror.None, 1);

    terraformer.InitMap();

    foreach (var mpos in map.AllCells.MapCoords)
        map.Tiles[mpos] = terraformer.PickTile(random, tileType);

    terraformer.BakeMap();

    return map;
}
```

This generator is useful as a template because it shows every required step: validate settings, create a `Map`, instantiate `Terraformer`, initialize the map, mutate cells, and bake.

### Parameter loading in a real generator

In `ClassicMapGenerator`, the `Parameters` class constructor does something like:

```csharp
public Parameters(Map map, MiniYaml my)
{
    FieldLoader.Load(this, my);
    Mirror = LoadMirror(my);
    Rotations = LoadRotations(my);
    LandTiles = ParseTerrainIndexes(...);
    WaterTiles = ParseTerrainIndexes(...);
    DefaultResource = LoadResourceType(...);
    ResourceSpawnSeeds = LoadResourceSpawnWeights(...);
}
```

These custom loaders are where a mod author translates YAML strings (tile names, resource types, mirror names) into the numeric or object values the generator actually uses.

### Settings option emission

When the user clicks Generate, the editor calls `IMapGeneratorSettings.Compile(...)` to produce a `MapGenerationArgs`. Each option contributes nodes via `GetSettings`. For example, a `MapGeneratorBooleanOption` emits:

```csharp
return [new MiniYamlNode(Parameter, FieldSaver.FormatValue(Value))];
```

A `MapGeneratorMultiChoiceOption` emits the entire `Settings` block of the chosen choice, optionally filtered by tileset and player count. This lets a single generator expose presets such as “Lakes”, “Continents”, or “Oceanic” without code changes.

![Configuration (yaml) diagram](images/Part_07_Chapter_08_Extension_Points-annotated-yaml-snippet-diagram-showing-the-key-fields-and-ho-6a1b98.svg)

## Configuration (YAML)


### Registering a generator

Every generator must be listed under `^MapGenerators:` in a mod's `rules/map-generators.yaml`:

```yaml
^MapGenerators:
    ClassicMapGenerator@classic:
        Type: classic
        Name: map-generator-classic
        Tilesets: DESERT, SNOW, TEMPERAT
        Settings:
            IntegerOption@Seed:
                Label: label-ra-map-generator-option-seed
                Parameter: Seed
                Default: 0
            MultiChoiceOption@TerrainType:
                Label: label-ra-map-generator-option-terrain-type
                Default: Plots
                Choice@Plots:
                    Label: label-ra-map-generator-choice-terrain-type-plots
                    Settings:
                        Water: 100
                        Forests: 300
```

The `Type` value is the key used by the editor to look up the generator. The `Name` is a Fluent reference. `Tilesets` restricts which tilesets the tool appears for.

### Option types

| YAML node | Class | Use case |
| :---- | :---- | :---- |
| `BooleanOption@Id` | `MapGeneratorBooleanOption` | Checkbox (e.g., “Roads”). |
| `IntegerOption@Id` | `MapGeneratorIntegerOption` | Free integer (e.g., “Seed”). |
| `MultiIntegerChoiceOption@Id` | `MapGeneratorMultiIntegerChoiceOption` | Dropdown of integers (e.g., “Players”). |
| `MultiChoiceOption@Id` | `MapGeneratorMultiChoiceOption` | Dropdown of presets with per-choice `Settings` blocks. |

`Parameter` names the emitted YAML key. `Default` is used when the option has not been touched. `Priority` influences panel ordering (higher values appear first). `MultiChoiceOption` entries can filter by `Tileset` and `Players` so that, for example, a symmetry choice that only works for 2 or 4 players is hidden otherwise.

### Hidden presets

It is common to use two `MultiChoiceOption` entries with hidden defaults and tileset overrides:

```yaml
MultiChoiceOption@hidden_defaults:
    Choice@hidden_defaults:
        Settings:
            TerrainFeatureSize: 20480
            Water: 200
            ...
MultiChoiceOption@hidden_tileset_overrides:
    Choice@desert:
        Tileset: DESERT
        Settings:
            LandTile: 255
            WaterTile: 256
```

These are not shown in the UI (they have no `Label` or are otherwise invisible), but their `Settings` blocks are emitted before the visible options, giving each tileset a base profile and each visible preset a tunable delta.

### Tileset brush collections

Generators that use `MultiBrush` rely on `MultiBrushCollections/Segmented` entries in the tileset YAML. For example, from the Red Alert tileset:

```yaml
MultiBrushCollections:
    Segmented:
        Cliff:
            ...
        WaterCliff:
            ...
```

A mod can add new collections and load them in the generator's `Parameters` class:

```csharp
var cliffCollection = MultiBrush.LoadCollection(map, "Segmented", "Cliff");
```

No engine change is required; the generator only needs to know the collection name.

## Interconnectivity

- **Depends on:** [Part 2.1 — MiniYaml Parser](Part_02_Chapter_01_MiniYaml.md) (MiniYaml parsing), [Part 2.3 — FieldLoader](Part_02_Chapter_03_FieldLoader.md) (FieldLoader), [Part 3.1 — Mod SDK and Project Structure](Part_03_Chapter_01_Mod_SDK.md) (Manifest and ModData), [Part 7.2 — Map Generation Data Structures](Part_07_Chapter_02_Data_Structures.md) (data structures such as `CellLayer` and `Map`), [Part 7.4 — Terraformer](Part_07_Chapter_04_Terraformer.md) (Terraformer), [Part 7.5 — MultiBrush and Tile Placement](Part_07_Chapter_05_MultiBrush.md) (MultiBrush).
- **Used by:** the map editor (not otherwise documented), [Part 10.1 — Official Mods](Part_10_Chapter_01_Official_Mods.md) (official mods that ship their own generators), and mod authors who want to add new procedural map styles.

![Algorithms diagram](images/Part_07_Chapter_08_Extension_Points-algorithm-diagram-or-pseudocode-flowchart-for-the-non-trivia-5983ed.svg)

## Algorithms


### Settings resolution order

The final `MapGenerationArgs.Settings` is built by merging option emissions in the order they appear in the `Settings` list. Later options override earlier ones. The `MultiChoiceOption` therefore works as a preset: the hidden defaults run first, the tileset override runs next, and the visible choice (such as “Lakes” or “Continents”) runs last, overriding any earlier parameter.

### Validating the generated map

Most generators call `Terraformer.BakeMap()` at the end. `BakeMap` commits the `ActorPlans` list into the map's `ActorDefinitions` and creates a `MapPlayers` block from the actual `mpspawn` count. Before that, `ReorderPlayerSpawns()` sorts spawns clockwise and rotates the sequence so spawn numbering feels natural. A custom generator must either call these helpers or construct its own `MapPlayers` and actor definitions manually.

### Reproducibility when adding options

The `ClassicMapGenerator` derives many independent `MersenneTwister` instances from the seed. When adding a new option, the generator author should add a new `random.Next()` call only at the end of the chain. Changing the order or number of calls changes every map previously generated with the same seed, breaking reproducibility.

![Extension points diagram](images/Part_07_Chapter_08_Extension_Points-extension-hook-diagram-showing-the-interface-s-to-implement-b4a27b.svg)

## Extension Points


### Add a new generator

Create a new `TraitInfo` class in a mod or in `OpenRA.Mods.Common` that implements `IEditorMapGeneratorInfo`. The only engine requirement is the `Type` string and the `Generate` method. Everything else—the terrain phases, the resource model, the actor placement logic—is mod code.

### Extend an existing generator via subclassing

Because `ClassicMapGenerator`, `D2kMapGenerator`, and `TSMapGenerator` are ordinary classes, a mod can subclass them, override `Generate`, call `base.Generate(...)`, and then perform additional post-processing (placing custom props, stamping special zones, etc.) before returning the map.

### Add new editor options

A mod can add `BooleanOption`, `IntegerOption`, or `MultiChoiceOption` entries to a generator's `Settings` YAML without touching C#. As long as the existing `Parameters` class already has a matching field name (or the custom generator handles the new node), the option works immediately. If the option is brand-new, a custom generator is required to read it.

### Add new tileset brushes

Adding a `MultiBrushCollections/Segmented` entry to a tileset YAML is enough to make new brushes available to any generator that loads that collection name. This is the standard way to add new cliff styles, water cliff styles, or forest obstacles.

### Add custom resource/actor placement logic

The `ActorPlans` list passed into `Terraformer` is mutable. A custom generator can place actors manually using `ActorPlan.Add`, and `Terraformer.BakeMap()` will commit them. Resources are placed as actors with `ResourceLayer` traits, so the same actor mechanism applies.

### Implement custom ruleset overrides

`TryGenerateMetadata` can return rule definitions in the `out Dictionary<string, MiniYaml> rules` parameter. This is how a generator can inject custom map rules (for example, spawn-related settings or special game-mode rules) without editing the mod's default rules.

![Common pitfalls  guardrails diagram](images/Part_07_Chapter_08_Extension_Points-checklist-infographic-style-diagram-summarizing-the-top-pitf-fb069e.svg)

## Common Pitfalls / Guardrails


- **Tileset validation:** always validate that a tile index exists in `terrainInfo` before writing it into `map.Tiles`. `ClearMapGenerator` does this explicitly and other generators should follow suit.
- **Player count consistency:** `TryGenerateMetadata` must produce a `MapPlayers` block whose count matches the `mpspawn` actors placed by the generator; otherwise lobby logic will misreport the map.
- **Deterministic seeds:** `MapGeneratorSettings.Randomize` sets the `Seed` option to `random.Next()` from the editor's random source. If you add a new random source inside `Generate`, seed it from a deterministic chain based on the `Seed` parameter.
- **Linter requirements:** `MapGeneratorSettings` collects `FluentReferences` from options so the translation linter can verify them. Add a `FluentReferencesLoader` that calls `GetSettings().Options.SelectMany(o => o.GetFluentReferences())` to keep labels linted.
- **Inheritance prefix:** abstract actors used by the generator (e.g., resource actors) begin with `^`. Do not accidentally register these as real units; the generator must load them as templates, not as spawnable actors.
- **PanelWidget:** every generator must specify a `PanelWidget` widget tree name that the editor can open. The default `MAP_GENERATOR_TOOL_PANEL` works for most generators; a custom UI requires a matching YAML definition.

## What to read next

- [Part 7.1 — Map Generation Pipeline Overview](Part_07_Chapter_01_Pipeline.md) for the entry points and contracts that new generators must implement.
- [Part 7.6 — Mod-Specific Generators](Part_07_Chapter_06_Mod_Generators.md) for concrete examples of full generator implementations.
- [Part 3.1 — Mod SDK and Project Structure](Part_03_Chapter_01_Mod_SDK.md) for how manifest and `ModData` discovery work.

## Summary

This chapter explains how the OpenRA [Random Map Generator (RMG)](../appendices/Appendix_A_Glossary.md) is split into reusable extension points and how to add new generators or brushes.

After reading this chapter, you should be able to:

- Create a class `MyMapGeneratorInfo` that inherits `TraitInfo` and implements `IEditorMapGeneratorInfo`.
- Declare required metadata fields: `Type`, `Name`, `Tilesets`, `MapTitle`, and `PanelWidget`.
- Add a `Settings` MiniYaml field loaded via `SettingsLoader` and a `GetSettings()` method returning `new MapGeneratorSettings(this, Settings)`.
- Implement `Generate(ModData, MapGenerationArgs)` to create a `Map`, build a `Parameters`, instantiate `Terraformer`, run the chosen terrain/actor phases, and call `BakeMap()`.
- Implement `TryGenerateMetadata(...)` to return a `MapPlayers` block and any rule overrides.
- Implement `Create(...)` to return the `IEditorTool` instance (usually just a wrapper).
- Add the generator to the mod's `rules/map-generators.yaml` under `^MapGenerators:`.
- Add Fluent labels for `Name`, option labels, and choice labels.

If any of the concepts above feel unclear, review the relevant section before continuing. For source files and further reading, see the References section.


## References

- `OpenRA.Game/Traits/TraitsInterfaces.cs` — `IMapGeneratorInfo`.
- `OpenRA.Mods.Common/TraitsInterfaces.cs` — `IEditorMapGeneratorInfo`, `IMapGeneratorSettings`, `MapGenerationException`.
- `OpenRA.Mods.Common/MapGenerator/MapGeneratorSettings.cs` — `MapGeneratorSettings` and option classes.
- `OpenRA.Mods.Common/Traits/World/ClearMapGenerator.cs` — minimal generator reference.
- `OpenRA.Mods.Common/Traits/World/ClassicMapGenerator.cs` — full generator reference.
- `OpenRA.Mods.D2k/Traits/World/D2kMapGenerator.cs` — mod-specific generator example.
- `OpenRA.Mods.Cnc/Traits/World/TSMapGenerator.cs` — mod-specific generator example with ramps.
- `mods/ra/rules/map-generators.yaml` — YAML registration example.
- `mods/ra/tilesets/temperat.yaml` — tileset brush collection example.