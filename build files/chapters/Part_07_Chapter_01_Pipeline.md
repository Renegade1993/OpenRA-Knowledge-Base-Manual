# Chapter 7.1 — Map Generation Pipeline Overview

## Purpose

This chapter explains how OpenRA turns a user-facing seed/settings panel into a fully realized, playable `Map`. It covers the entire entry-to-output pipeline: the two UI entry points (the map chooser's random-map panel and the editor's map generator tool), the trait-based registration of generators, the settings/options bridge that converts widget state into a serializable `MapGenerationArgs`, and the `IMapGeneratorInfo` / `IEditorMapGeneratorInfo` contracts that make the whole thing modular.

After reading this chapter, you should understand:

- How a click in the UI eventually calls `IMapGeneratorInfo.Generate`.
- What `MapGeneratorSettings` does and how options map to generator parameters.
- How `MapGenerationArgs` carries a deterministic fingerprint of the map to be generated.
- How the generated `Map` is saved, previewed, and either loaded into a game or blitted onto an existing editor map.
- Where to plug in a new generator.

## Learning Objectives


After studying this chapter, you should be able to:

- Explain the end-to-end map generation pipeline from UI click to playable Map.
- Describe the IMapGeneratorInfo and IEditorMapGeneratorInfo contracts.
- Trace how MapGeneratorSettings compiles widget options into MapGenerationArgs.
- Explain the difference between Generate and TryGenerateMetadata.
- Register a new generator in YAML and wire it into the map chooser or editor.
- Describe how generated maps are saved, previewed, or blitted into the editor.

<!-- DEV-NOTE [visual-aid]: RMG pipeline overview diagram showing the full flow from Seed + Settings → UI entry points (map chooser and editor tool) → `MapGenerationArgs` → Part 7.2 data structures (CellLayer, Matrix, MapGrid, Map) → Part 7.3 algorithms → Part 7.4 Terraformer → Part 7.5 MultiBrush → Part 7.6 mod generators → Part 7.7 resources/actors → final `.oramap`. The diagram should also show the parallel metadata-only path (`TryGenerateMetadata`) used for previews. -->

## RMG at a glance

OpenRA's [Random Map Generator (RMG)](../appendices/Appendix_A_Glossary.md) turns a seed and a handful of YAML settings into a playable `.oramap` file. The pipeline is:

```
Seed + Settings
    |
    v
[7.1 Pipeline]           MapGenerationArgs, UI entry points
    |
    v
[7.2 Data Structures]    CellLayer, Matrix, MapGrid, Map
    |
    v
[7.3 Algorithms]         Noise, Symmetry, MatrixUtils
    |
    v
[7.4 Terraformer]        Terrain, elevation, roads
    |
    v
[7.5 MultiBrush]         Tile/actor brush stamps
    |
    v
[7.6 Mod Generators]     Per-mod generator classes
    |
    v
[7.7 Resources/Actors]   Spawns, resources, actor placement
    |
    v
[7.8 Extension Points]   Custom generators, brushes, options
    |
    v
[7.9 File Index]         Source reference
    |
    v
.oramap
```

The rest of this chapter walks through the entry points and contracts that make this pipeline modular.

## Files

> Note: the task requested `OpenRA.Mods.Common/Traits/World/MapGeneratorLogic.cs` and `OpenRA.Mods.Common/Traits/World/MapGeneratorToolLogic.cs`. In this checkout, those files actually live under the `Widgets/Logic` tree, not `Traits/World`. The table below lists the real locations.

| File | Responsibility |
| :---- | :---- |
| `OpenRA.Mods.Common/Widgets/Logic/MapGeneratorLogic.cs` | Chrome logic for the map chooser's random-map generation panel (preview, settings, async generation). |
| `OpenRA.Mods.Common/Widgets/Logic/Editor/MapGeneratorToolLogic.cs` | Chrome logic for the editor's map generator tool panel (in-place generation as an undoable editor action). |
| `OpenRA.Mods.Common/MapGenerator/MapGeneratorSettings.cs` | Parses generator settings YAML, exposes the `IMapGeneratorSettings` implementation, and compiles widget state into `MapGenerationArgs`. |
| `OpenRA.Game/Traits/TraitsInterfaces.cs` | Defines the base `IMapGeneratorInfo` interface (`Generate` and `TryGenerateMetadata`). |
| `OpenRA.Mods.Common/TraitsInterfaces.cs` | Defines `IEditorMapGeneratorInfo` (extends `IMapGeneratorInfo` with `Tilesets` and `GetSettings`) and `IMapGeneratorSettings`. |
| `OpenRA.Game/Map/MapGenerationArgs.cs` | The serializable carrier object that uniquely identifies a generated map (generator type, tileset, size, seed, settings, title, author). |
| `OpenRA.Mods.Common/Widgets/Logic/MapChooserLogic.cs` | Loads the generation panel, stores the generated package, and promotes it into the `MapCache`. |
| `OpenRA.Mods.Common/Widgets/Logic/Editor/MapToolsLogic.cs` | Enumerates `IEditorTool` instances and loads their tool panels. |
| `OpenRA.Mods.Common/Traits/World/ClassicMapGenerator.cs` | The standard Red Alert / Tiberian Dawn style generator. |
| `OpenRA.Mods.Common/Traits/World/ClearMapGenerator.cs` | A minimal "clear everything to one tile" generator. |
| `OpenRA.Mods.D2k/Traits/World/D2kMapGenerator.cs` | Dune 2000 generator implementation. |
| `OpenRA.Mods.Cnc/Traits/World/TSMapGenerator.cs` | Tiberian Sun generator implementation. |
| `OpenRA.Game/Map/MapPreview.cs` | Metadata-only preview and lazy full generation of maps on demand. |
| `mods/ra/rules/map-generators.yaml` | Example YAML registration of `ClassicMapGenerator` and `ClearMapGenerator` for the Red Alert mod. |
| `mods/common/chrome/map-chooser.yaml` | Chrome definition for the map chooser generation panel (`MAPCHOOSER_GENERATE_PANEL`). |
| `mods/common/chrome/editor.yaml` | Chrome definition for the editor generator tool panel (`MAP_GENERATOR_TOOL_PANEL`). |

![Architecture diagram](images/Part_07_Chapter_01_Pipeline-architecture-diagram-showing-the-main-classes-interfaces-and-9161e6.svg)

## Architecture


![Architecture](images/Part_07_Chapter_01_Pipeline-Architecture.svg)
### The generator contract

The base contract is `IMapGeneratorInfo` in `OpenRA.Game/Traits/TraitsInterfaces.cs`:

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

- `Type` is the internal identifier used to look up the generator by name.
- `Name` is the human-readable (Fluent) name shown in the UI.
- `MapTitle` is the default title applied to generated maps.
- `Generate` is the heavy lifting: build a `Map` object from the supplied args.
- `TryGenerateMetadata` is a lightweight path that only produces the player count and ruleset required for previews and server-side map selection.

Editor-visible generators extend this with `IEditorMapGeneratorInfo` in `OpenRA.Mods.Common/TraitsInterfaces.cs`:

```csharp
public interface IEditorMapGeneratorInfo : IMapGeneratorInfo
{
    ImmutableArray<string> Tilesets { get; }
    IMapGeneratorSettings GetSettings();
}
```

- `Tilesets` lists which terrain sets the generator knows how to paint.
- `GetSettings()` returns a UI-configurable `IMapGeneratorSettings` object.

### The settings bridge

`IMapGeneratorSettings` (`OpenRA.Mods.Common/TraitsInterfaces.cs`) is the contract that lets both UI logics talk to a generator without knowing its internals:

```csharp
public interface IMapGeneratorSettings
{
    ImmutableArray<MapGeneratorOption> Options { get; }
    int PlayerCount { get; }
    void Randomize(MersenneTwister random);
    void Initialize(MapGenerationArgs args);
    MapGenerationArgs Compile(ITerrainInfo terrainInfo, Size size);
}
```

`MapGeneratorSettings` (`OpenRA.Mods.Common/MapGenerator/MapGeneratorSettings.cs`) is the only concrete implementation. It parses the `Settings` MiniYaml from a generator trait and builds a list of `MapGeneratorOption` objects. The option types are:

| Option class | YAML key | UI widget | What it produces |
| :---- | :---- | :---- | :---- |
| `MapGeneratorBooleanOption` | `BooleanOption@<id>` | checkbox | a single `<Parameter>: True/False` setting |
| `MapGeneratorIntegerOption` | `IntegerOption@<id>` | text field | a single `<Parameter>: <int>` setting |
| `MapGeneratorMultiIntegerChoiceOption` | `MultiIntegerChoiceOption@<id>` | dropdown | a single `<Parameter>: <int>` setting chosen from a fixed list |
| `MapGeneratorMultiChoiceOption` | `MultiChoiceOption@<id>` | dropdown | a block of settings selected by a named choice (can be tileset/player-count filtered) |

All options expose `Id`, `Label`, and `Priority`. `Priority` controls the order in which their settings are merged: lower values are applied first, later values can override them.

### The generation carrier

`MapGenerationArgs` (`OpenRA.Game/Map/MapGenerationArgs.cs`) is the canonical fingerprint of a generated map. It contains:

```csharp
public string Uid;
public string Generator;
public string Tileset;
public Size Size;
public string Title;
public string Author;
public MiniYaml Settings;
```

`Settings` is the merged MiniYaml produced by all selected options. `MapGeneratorSettings.Compile` also stores a separate `Options` dictionary (as a `FrozenDictionary<string, string>`) so the UI can restore the exact panel state later.

![Data flow  code path diagram](images/Part_07_Chapter_01_Pipeline-sequence-flow-diagram-tracing-the-execution-path-from-trigge-035864.svg)

## Data Flow / Code Path


There are two top-level entry points. They share the same generator interface but differ in what they do with the resulting `Map`.

### Path 1: the map chooser random-map panel

1. **Panel creation.** `MapChooserLogic` checks whether the `EditorWorld` actor has any `IEditorMapGeneratorInfo` traits (`OpenRA.Mods.Common/Widgets/Logic/MapChooserLogic.cs`). If so, it calls `SetupGenerateMapPanel`.

2. **Widget loading.** `SetupGenerateMapPanel` loads the chrome widget `MAPCHOOSER_GENERATE_PANEL` (`mods/common/chrome/map-chooser.yaml`). That widget declares `Logic: MapGeneratorLogic`, so the engine creates a `MapGeneratorLogic` instance.

3. **Generator selection.** The constructor grabs the **first** `IEditorMapGeneratorInfo` registered on the `EditorWorld` actor (`MapGeneratorLogic.cs`). It then calls `GetSettings()` to obtain a `MapGeneratorSettings` object (`MapGeneratorLogic.cs`).

4. **UI setup.** The logic manually creates two dropdowns: one for tileset and one for map size (`MapGeneratorLogic.cs`). These are handled outside the generator because the generator itself doesn't expose tileset/size as ordinary options.

5. **Randomize.** The `Generate` button (`MapGeneratorLogic.cs`) calls `settings.Randomize(Game.CosmeticRandom)`, which sets the `Seed` option to a random integer (`MapGeneratorSettings.cs`), then calls `RandomizeSize()` to pick a width/height from the `MapSizes` dictionary with a small grid adjustment (`MapGeneratorLogic.cs`).

6. **Compile arguments.** `GenerateMap()` (`MapGeneratorLogic.cs`) calls `settings.Compile(selectedTerrain, size)` (`MapGeneratorSettings.cs`). `Compile`:
   - reads the current `PlayerCount`;
   - orders options by `Priority`;
   - collects each option's `GetSettings` output into a list of `MiniYamlNode` layers;
   - merges those layers into a single `MiniYaml` via `MiniYaml.Merge`;
   - builds a `FrozenDictionary` of UI option values so the panel can be recreated later;
   - returns a `MapGenerationArgs` with `Generator`, `Tileset`, `Size`, `Title` (from `MapTitle`), `Author` (from `Name`), and the merged `Settings`.

7. **Generate the map.** `MapGeneratorLogic.cs` calls `generator.Generate(modData, args)` on a background thread.

8. **Save and preview.** If generation succeeds, the `Map` is saved to a fresh `ZipFileLoader.ReadWriteZipFile()` (`MapGeneratorLogic.cs`), the UID is copied back into `args.Uid`, and the preview widget is updated. The `onGenerate` callback is invoked with `(args, package)`.

9. **Adoption.** `MapChooserLogic` receives the callback and stores `generatedMapArgs` and `generatedMapPackage` (`MapChooserLogic.cs`). When the player clicks OK, the generated tab is considered selected; `MapCache[generatedMapArgs.Uid]` is updated via `UpdateFromGenerationArgs` and `UpdateFromMap` (`MapChooserLogic.cs`), and the caller's `onSelectGenerated` callback is invoked.

10. **Lazy full generation.** If a generated map is chosen but only metadata exists, `MapPreview.Generate()` (`MapPreview.cs`) does the final full generation on a background thread, saves the result, and again asserts that the resulting `Map.Uid` matches `GenerationArgs.Uid` (`MapPreview.cs`).

### Path 2: the editor map generator tool

1. **Tool discovery.** `MapToolsLogic` enumerates all `IEditorTool` traits on the world actor (`MapToolsLogic.cs`). Each generator class (e.g. `ClassicMapGenerator`, `ClearMapGenerator`) implements `IEditorTool` and exposes a `PanelWidget` and `Label`.

2. **Panel loading.** `MapToolsLogic.cs` loads `MAP_GENERATOR_TOOL_PANEL` (`mods/common/chrome/editor.yaml`), passing the `IEditorTool` as a widget argument. The panel declares `Logic: MapGeneratorToolLogic`, whose constructor receives the `tool`.

3. **Generator cast.** `MapGeneratorToolLogic` casts the tool's `TraitInfo` to `IEditorMapGeneratorInfo` and calls `GetSettings()` (`MapGeneratorToolLogic.cs`).

4. **Generate.** Clicking the generate button calls `GenerateMap()` -> `GenerateMapMayThrow()` (`MapGeneratorToolLogic.cs`). It:
   - compiles `MapGenerationArgs` from the current map's tileset and size (`MapGeneratorToolLogic.cs`);
   - logs the settings (`MapGeneratorToolLogic.cs`);
   - calls `generator.Generate(modData, args)` (`MapGeneratorToolLogic.cs`);
   - converts the generated map's tiles, resources, and actors into an `EditorBlitSource` and `EditorBlit` (`MapGeneratorToolLogic.cs`);
   - wraps the blit in a `RandomMapEditorAction` (`MapGeneratorToolLogic.cs`);
   - adds the action to the `EditorActionManager` (`MapGeneratorToolLogic.cs`), making it undoable and redoable.

5. **Error handling.** Any `MapGenerationException` or `YamlException` is shown in a confirmation dialog with the exception message; other exceptions are logged and shown as a generic failure prompt (`MapGeneratorToolLogic.cs`).

### Common sub-flow: from `MapGenerationArgs` to `Map`

Both paths eventually call a generator's `Generate` method. The generator's job is:

1. Look up the `ITerrainInfo` for `args.Tileset`.
2. Create a blank `Map` with `new Map(modData, terrainInfo, args.Size)`.
3. Parse its internal `Parameters` from `args.Settings` (usually via a private `Parameters` class using `FieldLoader`).
4. Use a `Terraformer` (or direct tile painting) to fill `map.Tiles`, `map.Resources`, `map.Height`, and add actor plans.
5. Return the `Map`.

For example, `ClassicMapGenerator.Generate` (`ClassicMapGenerator.cs`) constructs a `Parameters`, creates a `Terraformer`, derives many independent `MersenneTwister` RNGs from the seed, paints land/sea, cliffs, forests, roads, resources, and neutral buildings, then returns the map.

![Configuration (yaml) diagram](images/Part_07_Chapter_01_Pipeline-annotated-yaml-snippet-diagram-showing-the-key-fields-and-ho-6a1b98.svg)

## Configuration (YAML)


Generators are registered as traits on the `EditorWorld` actor in a mod's rules YAML. The Red Alert example is `mods/ra/rules/map-generators.yaml`:

```yaml
^MapGenerators:
    ClassicMapGenerator@classic:
        Type: classic
        Name: map-generator-classic
        Tilesets: DESERT, SNOW, TEMPERAT
        MapTitle: label-random-map
        Settings:
            ...
```

Key fields:

- `Type` (required): internal generator ID used by `MapGenerationArgs.Generator`.
- `Name` (required, Fluent reference): shown in the UI and used as the map author.
- `Tilesets` (required): comma-separated list of tileset IDs the generator supports.
- `MapTitle` (optional, Fluent reference): default title for generated maps.
- `PanelWidget` (optional): chrome panel used by the editor tool; default is `MAP_GENERATOR_TOOL_PANEL`.
- `Settings` (required): the options exposed to the user.

### Settings option syntax

```yaml
Settings:
    BooleanOption@DenyWalledArea:
        Label: label-ra-map-generator-option-deny-walled-areas
        Parameter: DenyWalledAreas
        Default: True
        Priority: 1

    IntegerOption@Seed:
        Label: label-ra-map-generator-option-seed
        Parameter: Seed
        Default: 0

    MultiIntegerChoiceOption@Players:
        Label: label-ra-map-generator-option-players
        Parameter: Players
        Choices: 1, 2, 3, 4, 5, 6, 7, 8
        Default: 2
        Priority: 1

    MultiChoiceOption@TerrainType:
        Label: label-ra-map-generator-option-terrain-type
        Default: Plots
        Priority: 2
        Choice@Plots:
            Label: label-ra-map-generator-choice-terrain-type-plots
            Settings:
                Water: 100
                Forests: 300
                ...
        Choice@Plains:
            Label: label-ra-map-generator-choice-terrain-type-plains
            Settings:
                Water: 0
```

- `Label` is a Fluent key for the option's UI label.
- `Parameter` is the generator parameter name the option writes into `Settings`.
- `Default` is the initial value (for `MultiChoiceOption`, a list of fallback keys).
- `Priority` controls merge order (see `MapGeneratorSettings.Compile`, `MapGeneratorSettings.cs`).

For `MultiChoiceOption`, each `Choice` can optionally declare:

- `Tileset: <ids>`: only show this choice when the selected tileset is in the list.
- `Players: <counts>`: only show this choice when the selected player count is in the list.
- `Settings`: a block of parameters that are injected when this choice is selected.

This is how mods implement "terrain presets" or "resource presets" that change many underlying parameters at once.

### Hidden defaults and overrides

Because `MapGeneratorSettings.Compile` merges layers by priority, a common pattern is to define a `MultiChoiceOption` with no UI label that acts as a hidden defaults layer, and then subsequent choices override it. For example, in `mods/ra/rules/map-generators.yaml` the `MultiChoiceOption@hidden_defaults` injects the baseline `ClassicMapGenerator` parameters, while the visible `TerrainType` choice overrides only the values that change.

## Practical Example: Adding a New Generator to the Skirmish Lobby

Suppose you want a "Large Open Plains" generator that always creates a flat, resource-light map with fixed settings.

1. Create a C# class that implements `IMapGeneratorInfo` (or inherit from the existing `ClassicMapGenerator` if you only need to override terrain parameters):

```csharp
public class OpenPlainsGeneratorInfo : TraitInfo<OpenPlainsGenerator>, IMapGeneratorInfo
{
    public string Type => "openplains";
    public string Name => "map-generator-openplains";
    public string MapTitle => "label-openplains-map";

    public Map Generate(ModData modData, MapGenerationArgs args) { /* ... */ }
    public bool TryGenerateMetadata(...) { /* ... */ }
}

public class OpenPlainsGenerator { }
```

2. Register it on the `EditorWorld` actor in your mod's `rules/map-generators.yaml`:

```yaml
^MapGenerators:
    OpenPlainsGenerator@openplains:
        Type: openplains
        Name: map-generator-openplains
        Tilesets: TEMPERAT, DESERT, SNOW
        MapTitle: label-openplains-map
```

3. Because the generator implements `IEditorMapGeneratorInfo` (via the base trait), the map chooser's `MapGeneratorLogic` discovers it through `TraitInfos<IEditorMapGeneratorInfo>().First()` and exposes a "Generate" button. The editor tool panel will list it alongside the other generators.

This example shows the three pipeline steps every new generator needs: a `TraitInfo` class implementing the generator contract, YAML registration on `EditorWorld`, and UI discovery through the `IEditorMapGeneratorInfo` interface.

## Interconnectivity

### Depends on

- **Trait system** ([Part 1.1 — ECS, Actors, and Traits](Part_01_Chapter_01_ECS.md) / [Part 1.2 — Activity System](Part_01_Chapter_02_Activities.md)): generators are registered as `TraitInfo` on the `EditorWorld` actor and discovered via `TraitInfos<T>`.
- **MiniYaml / FieldLoader** ([Part 2.1 — MiniYaml Parser](Part_02_Chapter_01_MiniYaml.md) / [Part 2.3 — FieldLoader](Part_02_Chapter_03_FieldLoader.md)): all settings, options, and `MapGenerationArgs` are loaded and saved through `FieldLoader` and `MiniYaml`.
- **Fluent localization**: all user-visible labels are Fluent keys (`Label`, `Name`, `MapTitle`).
- **Map / [CellLayer](../appendices/Appendix_A_Glossary.md) / [MapGrid](../appendices/Appendix_A_Glossary.md)** ([Part 7.2 — Map Generation Data Structures](Part_07_Chapter_02_Data_Structures.md)): the final output is a `Map` object with `CellLayer` tile, resource, and height layers.
- **TerrainInfo**: generators validate tile types against `modData.DefaultTerrainInfo`.
- **[Terraformer](../appendices/Appendix_A_Glossary.md) / [MultiBrush](../appendices/Appendix_A_Glossary.md) / Matrix** ([Part 7.4 — Terraformer](Part_07_Chapter_04_Terraformer.md), [Part 7.5 — MultiBrush and Tile Placement](Part_07_Chapter_05_MultiBrush.md)): the standard generators use these to build the actual terrain.
- **Editor action system** (`MapGeneratorToolLogic.cs`): editor generation is applied as an undoable `IEditorAction`.
- **MapCache / MapPreview** (`OpenRA.Game/Map/MapPreview.cs`): generated maps are registered as `MapClassification.Generated` with lazy full generation.

### Used by

- **Map chooser UI** (`MapChooserLogic`): provides the "Generate" tab; see [Part 4.3 — Widgets and Chrome](Part_04_Chapter_03_Widgets.md) for the chrome/widget system that hosts it.
- **Editor tools UI** (`MapToolsLogic`): lists generator tools; see [Part 4.4 — Viewport and Input](Part_04_Chapter_04_Viewport_Input.md) for the editor's UI entry points.
- **Server / map pool logic**: uses `MapPreview.UpdateFromGenerationArgs` to display and select generated maps without generating the full tile grid.
- **`--fuzz-map-generator` utility command** (`OpenRA.Mods.Common/UtilityCommands/FuzzMapGeneratorCommand.cs`): exercises generators by iterating through combinations of settings and tilesets.

![Algorithms diagram](images/Part_07_Chapter_01_Pipeline-algorithm-diagram-or-pseudocode-flowchart-for-the-non-trivia-5983ed.svg)

## Algorithms


### Merging option layers

`MapGeneratorSettings.Compile` (simplified from `MapGeneratorSettings.cs`):

```text
playerCount = PlayerCount
layers = Options.OrderBy(Priority).Select(o => o.GetSettings(terrainInfo, playerCount))
merged = MiniYaml.Merge(layers)
options = { optionId -> formattedValue for each option }
return new MapGenerationArgs {
    Generator = generatorInfo.Type,
    Tileset = terrainInfo.Id,
    Size = size,
    Title = FluentProvider.GetMessage(generatorInfo.MapTitle),
    Author = FluentProvider.GetMessage(generatorInfo.Name),
    Settings = merged,
    Options = frozen options
}
```

The merge is order-sensitive: a `MultiChoiceOption` choice can override a default value, and an `IntegerOption` can override a preset.

### Deterministic RNG derivation

Generators like `ClassicMapGenerator` take a single `Seed` and then create many independent `MersenneTwister` instances from it (`ClassicMapGenerator.cs`). This is a deliberate design to keep different algorithmic stages decoupled: changing one part of the generator does not perturb the random sequence used by unrelated parts. It also makes parallel or future threaded work easier.

### MultiChoice fallback

When a `MultiChoiceOption` is compiled, it may discover that the current `value` is not valid for the selected tileset or player count. It then falls back to:

1. The first entry of `Default` that is valid.
2. The first valid choice overall.

If no valid choice exists, the option contributes no settings (`MapGeneratorSettings.cs`). This is important for symmetry options that only make sense for certain player counts.

### Metadata-only path

`TryGenerateMetadata` exists so the map chooser, server, and lobby can display a generated map's player count, spawn points, and rules without running the full (potentially expensive) terrain generation. `ClassicMapGenerator.TryGenerateMetadata` (`ClassicMapGenerator.cs`) extracts the `Players` parameter from `args.Settings` and creates a `MapPlayers` with that count. The runtime later fills in placeholder spawn points and custom rules (`MapPreview.cs`).

![Extension points diagram](images/Part_07_Chapter_01_Pipeline-extension-hook-diagram-showing-the-interface-s-to-implement-b4a27b.svg)

## Extension Points


### Adding a brand-new generator

1. **Implement `IMapGeneratorInfo` (or `IEditorMapGeneratorInfo`).**
   - Create a `TraitInfo` subclass.
   - Add `[TraitLocation(SystemActors.EditorWorld)]` so it is attached to the editor world.
   - Implement `Type`, `Name`, `MapTitle`.
   - Implement `Generate` and `TryGenerateMetadata`.
   - If editor-visible, implement `IEditorMapGeneratorInfo.Tilesets` and `GetSettings()`.

2. **Provide a runtime `IEditorTool` class** (only if editor-visible).
   - The class must expose `Label`, `PanelWidget`, `IsEnabled`, and `TraitInfo`.
   - `IsEnabled` can filter by current map tileset (e.g. `ClassicMapGenerator.cs`).
   - The trait's `Create` override returns this runtime object.

3. **Add the YAML entry.** Register the trait under the `EditorWorld` actor or a template like `^MapGenerators`:

```yaml
MyWorld:
    MyMapGeneratorInfo@mygen:
        Type: mygen
        Name: my-generator-name
        Tilesets: TEMPERAT, DESERT
        MapTitle: label-random-map
        Settings:
            IntegerOption@Seed:
                Parameter: Seed
                Default: 0
            ...
```

4. **Add chrome if needed.** If the editor tool uses a custom panel, define the widget in `mods/<mod>/chrome/editor.yaml` and reference it via `PanelWidget`.

5. **Implement `Generate`.** Start with `new Map(modData, terrainInfo, args.Size)`, fill `map.Tiles`, and call `map.Save` if the caller needs it.

6. **Implement `TryGenerateMetadata`.** Return `true` with a `MapPlayers` matching the `Players` parameter and an empty or appropriate rules dictionary.

7. **Test with the fuzzer.** `OpenRA.Utility.exe --fuzz-map-generator --generator=mygen --tilesets=TEMPERAT --sizes=64x64,96x96` will iterate through option combinations and report failures.

### Custom option types

As of this codebase, the option type system is **not** open for extension without modifying `MapGeneratorSettings.cs`. The parser uses a hardcoded `switch` (`MapGeneratorSettings.cs`) that only recognizes `BooleanOption`, `IntegerOption`, `MultiIntegerChoiceOption`, and `MultiChoiceOption`. If you need a new option type (e.g., a slider, color picker, or coordinate entry), you must add a new `MapGeneratorOption` subclass and update the `switch` in `MapGeneratorSettings` and the UI logics in `MapGeneratorLogic` and `MapGeneratorToolLogic`.

### Customizing an existing generator

Most of the real "modding" is done through YAML overrides:

- Change `Tilesets` to enable/disable a generator for a tileset.
- Add new `Choice` blocks to `MultiChoiceOption` to create new presets.
- Change `BuildingWeights` or `ResourceSpawnWeights` to alter the mix of neutral buildings/resources.
- Override the hidden defaults layer to tweak parameters without changing code.

![Common pitfalls  guardrails diagram](images/Part_07_Chapter_01_Pipeline-checklist-infographic-style-diagram-summarizing-the-top-pitf-fb069e.svg)

## Common Pitfalls / Guardrails


- **UID determinism.** Generated maps are identified by `Map.Uid`. The `MapCache` expects `map.Uid` to equal `GenerationArgs.Uid` (`MapPreview.cs`). If the generator's output depends on anything outside `args.Settings` (e.g., the current time, ambient randomness, or global mutable state), the UID check will fail and the map will be rejected. Always derive randomness from the `Seed` parameter.

- **MapGenerationException is the expected error type.** `MapGeneratorToolLogic` and the map chooser UI only display user-friendly messages for `MapGenerationException` and `YamlException`. Other exceptions are treated as bugs and either crash or log a generic message. Use `MapGenerationException` for expected failure modes like "map too small" or "could not fit tiles".

- **Thread safety.** `MapGeneratorLogic.GenerateMap` runs generation on a thread-pool task. Only the `Game.RunAfterTick` lambda may touch the UI. Keep generator algorithms free of UI assumptions.

- **PlayerCount contract.** `MapGeneratorSettings.PlayerCount` specifically looks for an option with `Id == "Players"` and expects either a `MapGeneratorIntegerOption` or `MapGeneratorMultiIntegerChoiceOption` (`MapGeneratorSettings.cs`). If you rename or omit the `Players` option, the player count logic will report `0`.

- **Seed option convention.** `MapGeneratorSettings.Randomize` looks for an option with `Id == "Seed"` and treats it as an integer (`MapGeneratorSettings.cs`). If you want a randomize button, expose a seed option with that ID.

- **Tileset/size are not ordinary options.** Both UI logics create tileset and size dropdowns manually, not through the `MapGeneratorSettings` option system. The generator receives them via `MapGenerationArgs.Tileset` and `MapGenerationArgs.Size`. Do not rely on finding them in `args.Settings`.

- **MultiChoice defaults must be valid.** If the `Default` array of a `MultiChoiceOption` contains keys that are not valid for the current tileset/player count, the option will fall back to the first valid choice. This can cause the UI to display a different value than the one in `Settings` after a tileset change.

- **Isometric size handling.** `MapGeneratorLogic.RandomizeSize` doubles the height for `RectangularIsometric` grids and adds a border based on `MaximumTerrainHeight` (`MapGeneratorLogic.cs`). Generators must tolerate non-square sizes for isometric tilesets.

- **Editor resource layer hack.** `MapGeneratorToolLogic` casts `resourceLayer.Info` to `EditorResourceLayerInfo` to map resource indices back to resource type names (`MapGeneratorToolLogic.cs`). This is brittle and assumes the editor resource layer is always present.

- **Metadata generation must agree with full generation.** `TryGenerateMetadata` should report the same effective player count and rules as the full `Generate` path for the same `args`. If they disagree, the lobby preview and the actual generated map will be inconsistent.

- **Only the first generator is used by the map chooser.** `MapGeneratorLogic` calls `TraitInfos<IEditorMapGeneratorInfo>().First()` (`MapGeneratorLogic.cs`). If a mod registers multiple editor-visible generators, the map chooser will ignore all but the first one. The editor tool panel, however, will list all of them through `MapToolsLogic`.

- **The `MapGeneratorSettings` option parser is case-sensitive.** It expects keys of the form `<OptionType>@<Id>` and only recognizes the four option types listed above.

## What to read next

- [Part 7.2 — Map Generation Data Structures](Part_07_Chapter_02_Data_Structures.md) for the grid and layer types that generators manipulate.
- [Part 7.4 — Terraformer](Part_07_Chapter_04_Terraformer.md) and [Part 7.5 — MultiBrush and Tile Placement](Part_07_Chapter_05_MultiBrush.md) for the high-level tools that turn settings into terrain.
- [Part 7.8 — Random Map Generator Extension Points](Part_07_Chapter_08_Extension_Points.md) if you want to add a new generator or brush collection.
- [Appendix A — Glossary](../appendices/Appendix_A_Glossary.md) for definitions of RMG, CellLayer, MapGrid, Terraformer, and MultiBrush.
- [Part 2.2 — Manifest and Mod Metadata](Part_02_Chapter_02_Manifest.md) for the mod YAML and `ModData` plumbing that loads generator traits.

## Summary

This chapter explains how OpenRA turns a user-facing seed/settings panel into a fully realized, playable `Map`.

After reading this chapter, you should be able to:

- Explain the end-to-end map generation pipeline from UI click to playable Map.
- Describe the `IMapGeneratorInfo` and `IEditorMapGeneratorInfo` contracts.
- Trace how `MapGeneratorSettings` compiles widget options into `MapGenerationArgs`.
- Explain the difference between `Generate` and `TryGenerateMetadata`.
- Register a new generator in YAML and wire it into the map chooser or editor.
- Describe how generated maps are saved, previewed, or blitted into the editor.

If any of the concepts above feel unclear, review the relevant section before continuing. For source files and further reading, see the References section.


## References

### Source files

- `OpenRA.Game/Traits/TraitsInterfaces.cs` — `IMapGeneratorInfo` definition.
- `OpenRA.Mods.Common/TraitsInterfaces.cs` — `IEditorMapGeneratorInfo`, `IMapGeneratorSettings`, and `MapGenerationException`.
- `OpenRA.Game/Map/MapGenerationArgs.cs` — the serializable args carrier.
- `OpenRA.Mods.Common/MapGenerator/MapGeneratorSettings.cs` — options and `IMapGeneratorSettings` implementation.
- `OpenRA.Mods.Common/Widgets/Logic/MapGeneratorLogic.cs` — map chooser generation panel.
- `OpenRA.Mods.Common/Widgets/Logic/MapChooserLogic.cs` — integration with the map chooser, generated tab setup.
- `OpenRA.Mods.Common/Widgets/Logic/Editor/MapGeneratorToolLogic.cs` — editor tool logic.
- `OpenRA.Mods.Common/Widgets/Logic/Editor/MapToolsLogic.cs` — editor tool discovery.
- `OpenRA.Mods.Common/Traits/World/ClassicMapGenerator.cs` — example generator implementation.
- `OpenRA.Mods.Common/Traits/World/ClearMapGenerator.cs` — minimal example generator.
- `OpenRA.Mods.D2k/Traits/World/D2kMapGenerator.cs` — Dune 2000 generator.
- `OpenRA.Mods.Cnc/Traits/World/TSMapGenerator.cs` — Tiberian Sun generator.
- `OpenRA.Game/Map/MapPreview.cs` — metadata preview and lazy generation.
- `OpenRA.Mods.Common/UtilityCommands/FuzzMapGeneratorCommand.cs` — command-line generator exerciser.

### YAML / chrome

- `mods/ra/rules/map-generators.yaml` — Red Alert generator registration and options.
- `mods/cnc/rules/map-generators.yaml` — Tiberian Dawn generator registration.
- `mods/ts/rules/map-generators.yaml` — Tiberian Sun generator registration.
- `mods/d2k/rules/map-generators.yaml` — Dune 2000 generator registration.
- `mods/common/chrome/map-chooser.yaml` — map chooser generation panel (`MAPCHOOSER_GENERATE_PANEL`).
- `mods/common/chrome/editor.yaml` — editor generator tool panel (`MAP_GENERATOR_TOOL_PANEL`).
- `mods/cnc/chrome/editor.yaml` — CNC editor tool panel container (`MAP_GENERATOR_TOOL_PANEL`).

### Related manual chapters

- [Part 7.2 — Map Generation Data Structures](Part_07_Chapter_02_Data_Structures.md)
- [Part 7.3 — Map Generation Algorithms](Part_07_Chapter_03_Algorithms.md)
- [Part 7.4 — Terraformer](Part_07_Chapter_04_Terraformer.md)
- [Part 7.5 — MultiBrush and Tile Placement](Part_07_Chapter_05_MultiBrush.md)
- [Part 7.6 — Mod-Specific Generators](Part_07_Chapter_06_Mod_Generators.md)
- [Part 7.7 — Resource and Actor Placement](Part_07_Chapter_07_Resources_Actors.md)
- [Part 7.8 — Random Map Generator Extension Points](Part_07_Chapter_08_Extension_Points.md)
- [Part 7.9 — Random Map Generator File Index](Part_07_Chapter_09_File_Index.md)


### External resources

- [OpenRA playtest docs](https://docs.openra.net/en/playtest/)