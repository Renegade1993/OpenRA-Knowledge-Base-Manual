# Chapter 2.2 — Manifest, ModData, Ruleset, and RulesetCache

## Purpose

This chapter explains the four pillars that turn a mod's YAML configuration into a playable game world:

1. **`[Manifest](../appendices/Appendix_A_Glossary.md)`** — the static, read-only description of *what* a mod contains (files, metadata, compatibility, custom global data). It is the in-memory representation of the mod's `mod.yaml`.
2. **`[ModData](../appendices/Appendix_A_Glossary.md)`** — the runtime engine wrapper that owns a `Manifest`, mounts the mod's virtual file system, instantiates loaders, and exposes the default ruleset and terrain info.
3. **`[Ruleset](../appendices/Appendix_A_Glossary.md)`** — the compiled, object-oriented result of parsing the [YAML](../appendices/Appendix_A_Glossary.md) rules: actors, weapons, voices, notifications, music, model sequences, and terrain info.
4. **`RulesetCache`** — historically a separate caching layer. In the current codebase it has been removed and its responsibilities merged into `Ruleset` itself.

Together they answer: *How does OpenRA know which YAML files to load, how are they merged, how are map overrides applied, and how does the engine recover from broken map-specific rules?*

## Learning Objectives


After studying this chapter, you should be able to:

- Explain the roles of Manifest, ModData, Ruleset, and the historical RulesetCache.
- Trace how mod.yaml is loaded into a Manifest and how includes are resolved.
- Describe how ModData builds the VFS, loaders, and default ruleset.
- Explain how map-specific rule overrides are merged and fall back to defaults.
- Identify the seven dictionaries contained in a Ruleset.
- Explain the purpose of IRulesetLoaded callbacks.

## Files

| File | Role |
|------|------|
| `OpenRA.Game/Manifest.cs` | Parses `mod.yaml`, exposes `ImmutableArray<string>` lists for every asset category, metadata, filesystem config, and unrecognized global mod-data blocks. |
| `OpenRA.Game/ModData.cs` | Constructs the file system, loaders, object creator, map cache, cursors, default ruleset, and terrain info. Owns `IGlobalModData` instances. |
| `OpenRA.Game/GameRules/Ruleset.cs` | Builds the seven dictionaries/holders of a `Ruleset` (`Actors`, `Weapons`, `Voices`, `Notifications`, `Music`, `TerrainInfo`, `ModelSequences`) and wires `IRulesetLoaded` callbacks. |
| `OpenRA.Game/GameRules/RulesetCache.cs` | **Not present in the current checkout.** Removed by commit `82a9d69a51` ("Remove RulesetCache and push rule parsing to background thread"). Its logic now lives in `Ruleset.cs`. |
| `OpenRA.Game/Map/Map.cs` | Stores the map's custom-rule definitions (`RuleDefinitions`, `WeaponDefinitions`, etc.), applies them during `PostInit()`, and falls back to default rules if parsing fails. |
| `OpenRA.Game/Map/MapPreview.cs` | Mirrors map rule definitions for the shellmap/lobby preview and provides `DefinesUnsafeCustomRules()` and `LoadRuleset()`. |
| `OpenRA.Game/GameRules/ActorInfo.cs` | Parses a single actor node into a collection of [`TraitInfo`](../appendices/Appendix_A_Glossary.md) objects and resolves trait construction order. |
| `OpenRA.Game/Primitives/ActorInfoDictionary.cs` | Wraps the actor dictionary and guarantees that every `SystemActors` enum entry exists. |

![Architecture diagram](images/Part_02_Chapter_02_Manifest-architecture-diagram-showing-the-main-classes-interfaces-and-9161e6.svg)

## Architecture


### 1. Manifest: the mod.yaml object model

`Manifest` is constructed from a mod's `mod.yaml` file via the `Manifest(string modId, IReadOnlyPackage package)` constructor. The constructor performs three phases:

1. **Load and inline includes.** It reads `mod.yaml` with `[MiniYaml](../appendices/Appendix_A_Glossary.md).FromStream`, then expands every `Include:` node in-place by loading the referenced file and splicing its nodes into the tree. This allows mods to split configuration into reusable files.
2. **Merge inherited overrides.** The entire node tree is merged with `MiniYaml.Merge([nodes])`, then flattened into a `Dictionary<string, MiniYaml>` via `ToDictionary()`.
3. **Populate strongly-typed fields.** Each top-level key (e.g. `Rules`, `Sequences`, `Weapons`, `Voices`, `Music`, `Chrome`, `TileSets`, `Assemblies`, etc.) is read into an immutable array or a custom object.

Special handling:

- `Metadata` is loaded through `FieldLoader.Load<ModMetadata>`.
- `FileSystem` is mandatory and is stored as a raw `MiniYaml` block because the concrete file-system loader is instantiated via `ObjectCreator` later.
- `MapFolders` is parsed as a dictionary of path → classification strings (`System`, `User`, etc.).
- `MapCompatibility` always starts with the mod's own `Id`, then appends any comma-separated values from `SupportsMapsFrom:`.
- Any top-level key not in the `ReservedModuleNames` set is collected into `GlobalModData`, a `FrozenDictionary<string, MiniYaml>` that `ModData` will later convert into `IGlobalModData` instances.

This design means a mod author can declare *what* the engine needs to load; the engine then knows *where* to look before it actually loads the assets.

### 2. ModData: the live mod instance

`ModData` is the runtime owner of everything that belongs to a loaded mod. Its constructor is long and sequential because each subsystem depends on the previous one:

1. **Reload manifest.** It creates a fresh `Manifest` from the supplied manifest/package. This avoids keeping the original object graph.
2. **Create object creator.** `ObjectCreator` loads the engine assembly plus any `Assemblies:` declared in `mod.yaml`. It builds a type cache and resolves `AppDomain` assembly requests.
3. **Mount virtual file system.** `ModFiles` is a `FileSystem` instance created with the mod id and package loaders. The `IFileSystemLoader` named in `Manifest.FileSystem.Value` is instantiated, field-loaded from the `FileSystem` YAML, and asked to mount the manifest's packages. This is the point at which `^EngineDir`, `~^SupportDir|Content/...`, `cnc|rules`, and so on become resolvable paths in the [VFS](../appendices/Appendix_A_Glossary.md).
4. **Load global mod data.** For each entry in `Manifest.GlobalModData`, `ModData` looks up the C# type by key. If it implements `IGlobalModData` and has a `MiniYaml` constructor, that constructor is called directly; otherwise `ObjectCreator` creates the type and `FieldLoader` loads its child nodes. Examples: `MapGrid`, `GameSpeeds`, `AssetBrowser`, `DiscordService`.
5. **Initialize Fluent.** `FluentProvider.Initialize` loads the translation bundles listed in `FluentMessages` and `FluentCulture`.
6. **Load screen (optional).** If `useLoadScreen` is true, the `LoadScreen:` class is instantiated, initialized, and displayed.
7. **Create loaders and caches.** `WidgetLoader`, `MapCache`, `SoundLoaders`, `SpriteLoaders`, `VideoLoaders`, `SpriteSequenceLoader`, `HotkeyManager`, and the frozen cursor dictionary.
8. **Lazily load default rules and terrain.** `defaultRules` and `defaultTerrainInfo` are `Lazy<T>`; they only execute when first accessed.

Important `ModData` members:

- `DefaultRules` → `Ruleset.LoadDefaults(this)`.
- `DefaultTerrainInfo` → parses each `TileSets` file through the loader named by `TerrainFormat`.
- `GetOrCreate<T>()` and `GetOrNull<T>()` → retrieve `IGlobalModData` instances, lazily creating default objects if needed.
- `PrepareMap(Map map)` → reinitializes asset loaders with the map's file system, loads sprites, and loads map music.

### 3. Ruleset: from YAML to typed objects

A `Ruleset` is an immutable snapshot of the game world at a point in time. It contains:

- `Actors` (`ActorInfoDictionary`) — keyed by lower-case actor name.
- `Weapons` (`IReadOnlyDictionary<string, WeaponInfo>`) — keyed by lower-case weapon name.
- `Voices` / `Notifications` (`IReadOnlyDictionary<string, SoundInfo>`) — keyed by sound name.
- `Music` (`IReadOnlyDictionary<string, MusicInfo>`) — keyed by music name.
- `TerrainInfo` (`ITerrainInfo`) — the active tileset for this ruleset.
- `ModelSequences` (`IReadOnlyDictionary<string, MiniYamlNode>`) — raw model sequence nodes.

Construction of a `Ruleset` performs two post-load phases:

1. **Actor ruleset-loaded callbacks.** For every actor and every `IRulesetLoaded` trait on that actor, `RulesetLoaded(this, actor)` is called. Errors are wrapped with the actor name.
2. **Weapon ruleset-loaded callbacks.** For every weapon, the projectile and each warhead that implements `IRulesetLoaded<WeaponInfo>` receives `RulesetLoaded(this, weapon)`. Errors are wrapped with the weapon/pro projectile name.

These callbacks are the engine's way of letting traits resolve cross-references *after* the whole ruleset exists, e.g. looking up another actor or weapon by name.

### 4. RulesetCache (historical)

`OpenRA.Game/GameRules/RulesetCache.cs` existed in older versions. Its job was:

- Maintain per-mod caches (`actorCache`, `weaponCache`, etc.) so that identical YAML inputs reused already-parsed `ActorInfo`/`WeaponInfo` objects.
- Provide a `Load(...)` method that accepted a `Map` and a `TileSet` and produced a `Ruleset`.
- Fire a `LoadingProgress` event used by the load screen.

The class was removed by commit `82a9d69a51` (March 2016). The caching behavior was dropped in favor of simplicity, and rule parsing was moved to a background `Task` inside `Ruleset` (see `LoadDefaults`, `LoadDefaultsForTileSet`, and `Load`).

> **Current status:** `RulesetCache` is no longer in the codebase. All ruleset construction is now handled directly by static methods on `Ruleset`.

![Data flow  code path diagram](images/Part_02_Chapter_02_Manifest-sequence-flow-diagram-tracing-the-execution-path-from-trigge-035864.svg)

## Data Flow / Code Path


### Loading a mod from the command line

1. The game locates the mod package and builds a `Manifest`.
2. `ModData` is constructed with the manifest and the installed-mods list.
3. The first code path that accesses `modData.DefaultRules` triggers `Ruleset.LoadDefaults(this)`.
4. `Ruleset.LoadDefaults` runs on a background `Task` if the caller is on the main thread, allowing the load screen to animate via `modData.HandleLoadingProgress()`.

### Loading a map

1. `Map` constructor reads `map.yaml`, deserializes the `MapField` list, and populates `RuleDefinitions`, `WeaponDefinitions`, `VoiceDefinitions`, `NotificationDefinitions`, `MusicDefinitions`, and `ModelSequenceDefinitions`.
2. `PostInit()` calls `Ruleset.Load(modData, this, Tileset, ...)` with those map-specific YAML blocks.
3. `Ruleset.Load` calls `MiniYaml.Load(fileSystem, m.Rules, mapRules)` for each category. The merged YAML is turned into typed objects.
4. If the load succeeds, the map's `Rules` property is set.
5. If the load throws any exception, `Map.PostInit()` catches it, logs it to `debug`, marks `InvalidCustomRules = true`, stores the exception in `InvalidCustomRulesException`, and falls back to `Ruleset.LoadDefaultsForTileSet(modData, Tileset)`.

### Loading the shellmap / map preview

`MapPreview` keeps its own copy of the map's custom YAML blocks in `innerData`. It offers:

- `DefinesUnsafeCustomRules()` — calls `Ruleset.DefinesUnsafeCustomRules(...)` to decide whether the map should be flagged in the lobby.
- `LoadRuleset()` — calls `Ruleset.Load(modData, this, TileSet, ...)` with the preview's file system.

![Configuration (yaml) diagram](images/Part_02_Chapter_02_Manifest-annotated-yaml-snippet-diagram-showing-the-key-fields-and-ho-6a1b98.svg)

## Configuration (YAML)


### mod.yaml

`mod.yaml` is the single entry point a `Manifest` requires. A minimal logical skeleton looks like this:

```yaml
Metadata:
    Title: My Mod
    Version: {DEV_VERSION}

PackageFormats: Mix
FileSystem: ContentInstallerFileSystem
    ...

MapFolders:
    mymod|maps: System

Rules:
    mymod|rules/defaults.yaml
    mymod|rules/vehicles.yaml

Sequences:
    mymod|sequences/vehicles.yaml

Weapons:
    mymod|weapons.yaml

Voices:
    mymod|audio/voices.yaml

Notifications:
    mymod|audio/notifications.yaml

Music:
    mymod|audio/music.yaml

TileSets:
    mymod|tilesets/desert.yaml

Cursors:
    mymod|cursors.yaml

Chrome:
    mymod|chrome.yaml

Assemblies: OpenRA.Mods.MyMod.dll

LoadScreen: MyLoadScreen
    ...

TerrainFormat: DefaultTerrain
SpriteSequenceFormat: ClassicTilesetSpecificSpriteSequence
```

Key observations:

- The order of the lists matters. Files are loaded in order and later files override earlier ones via `MiniYaml.Merge`.
- `^` prefixes in the `Rules` list identify abstract (template) actors that are filtered out of the final `Actors` dictionary.
- `Include: filename.yaml` can appear anywhere and is expanded before the rest of the tree is merged.
- Any unrecognized top-level block whose name matches a C# type implementing `IGlobalModData` becomes a global mod data module.

### map.yaml

A map can override mod rules by declaring any of these optional blocks:

```yaml
Rules:
    e6:
        Health:
            HP: 1000

Weapons:
    ...

Voices:
    ...

Notifications:
    ...

Music:
    ...

Sequences:
    ...

ModelSequences:
    ...
```

Each block is deserialized into the corresponding `MiniYaml` field on `Map`. `Ruleset.Load` then merges these nodes *after* the mod files, so map entries always win. If a map wants to pull rules from an external file, it can use the inline-file syntax:

```yaml
Rules: mymap|rules.yaml
```

`MiniYaml.Load` detects this by reading `mapRules.Value`, splitting it into a list of file paths, and concatenating those files to the mod file list before merging.

## Interconnectivity

```
mod.yaml
   |
   v
Manifest  ----> ObjectCreator (assemblies, type lookup)
   |
   v
ModData  ----> FileSystem (ModFiles)
   |----> MapCache
   |----> WidgetLoader
   |----> Loaders (sound, sprite, video, sequence)
   |----> Cursors (frozen dict)
   |----> defaultRules (Lazy<Ruleset>)
   |----> defaultTerrainInfo (Lazy<...>)
   |----> IGlobalModData modules
   |
   +----> Ruleset.LoadDefaults(ModData)
            |
            +----> MiniYaml.Load(...)
            +----> ActorInfo, WeaponInfo, SoundInfo, MusicInfo
            +----> ActorInfoDictionary
            +----> IRulesetLoaded callbacks
   |
   +----> Map.PostInit()
            |
            +----> Ruleset.Load(..., mapRules, ...)
            +----> on failure: Ruleset.LoadDefaultsForTileSet(...)
```

Key contracts:

- `Manifest` never touches the file system after parsing `mod.yaml`. It only stores *paths*.
- `ModData` owns the file system and is the only thing that knows how to resolve `cnc|rules/foo.yaml`.
- `Ruleset` is a pure data object. It knows nothing about the file system; it only consumes already-loaded `MiniYaml` nodes.
- `Map` is both an `IReadOnlyFileSystem` and a consumer of rules. It provides the map-specific YAML to `Ruleset.Load`.

![Algorithms diagram](images/Part_02_Chapter_02_Manifest-algorithm-diagram-or-pseudocode-flowchart-for-the-non-trivia-5983ed.svg)

## Algorithms


### 1. YAML merging and inheritance

`MiniYaml.Load(fileSystem, files, mapRules)` is the engine's canonical way to produce a merged rule tree:

1. If `mapRules.Value` is non-null, parse it as a list of extra file paths and append them.
2. Load every file via `MiniYaml.FromStream`.
3. If `mapRules.Nodes` is non-empty, append the inline nodes as an additional source.
4. Run `MiniYaml.Merge(sources)`.

`Merge` first calls `MergeSelfPartial` on each source to resolve internal inheritance (`Inherits:`, `Inherits@`, `RemoveInherits`, removal prefixes), then combines sources with `MergePartial`. The result is a flat list of top-level nodes where later sources override earlier ones.

For `Ruleset`, the merged nodes are converted into a dictionary using `ToDictionaryWithConflictLog`, which reports duplicate keys with useful source-location information.

### 2. Abstract actor filtering

When loading actors, `Ruleset` passes a filter:

```csharp
filterNode: n => n.Key.StartsWith(ActorInfo.AbstractActorPrefix)
```

`AbstractActorPrefix` is the character `'^'`. Abstract actors are templates meant to be inherited by concrete actors, not spawned directly, so they are excluded from the final dictionary. This is the same behavior used by `SequenceSet`.

### 3. System actor guarantee

`ActorInfoDictionary` wraps the loaded actor dictionary and adds an empty `ActorInfo` for every value of the `SystemActors` enum (`world`, `editorworld`, `player`, etc.) that is not already present in the rules. This ensures that critical system actors always exist even if the mod YAML does not define them.

### 4. Default rules caching

The current implementation does **not** use a `RulesetCache`. Instead:

- `ModData.defaultRules` is a `Lazy<Ruleset>`.
- `Ruleset.LoadDefaults` builds the rules from the manifest lists.
- `Ruleset.LoadDefaultsForTileSet` reuses the same `Actors`, `Weapons`, `Voices`, `Notifications`, `Music`, and `ModelSequences` from the default ruleset and only swaps in the requested `TerrainInfo`.

This is the modern replacement for the old per-item caches: the default ruleset object is built once, then shared for tileset-specific variants.

### 5. Unsafe custom rule detection

`Ruleset.DefinesUnsafeCustomRules` decides whether a map's custom rules are "unsafe" for multiplayer lobbies that want to enforce no custom rules.

The algorithm is:

1. If the map defines any `Weapons`, `Voices`, `Notifications`, or `Sequences` overrides, it is immediately unsafe.
2. If the map defines `Rules`, inspect every actor's traits:
   - Strip the `@` instance suffix from the trait key.
   - Look up the trait type as `traitName + "Info"` via `ObjectCreator.FindType`.
   - If the type exists and does **not** implement `ILobbyCustomRulesIgnore`, the map is unsafe.
   - If the type lookup fails, the exception is logged and ignored for that trait.
3. If the map rules are inline files (`mapRules.Value` is non-null), repeat the trait check on each file's parsed nodes.

Traits such as `TerrainLightingInfo`, `WeatherOverlayInfo`, `TerrainTunnelInfo`, `ElevatedBridgePlaceholderInfo`, `TintPostProcessEffectInfo`, and `TerrainLightSourceInfo` implement `ILobbyCustomRulesIgnore` so that maps can use purely visual/environmental overrides without being flagged as unsafe.

### 6. Map custom rule fallback

`Map.PostInit()` loads the map ruleset inside a `try` block:

```csharp
Rules = Ruleset.Load(modData, this, Tileset, RuleDefinitions, WeaponDefinitions,
    VoiceDefinitions, NotificationDefinitions, MusicDefinitions, ModelSequenceDefinitions);
```

If any exception escapes, the map is marked invalid and the engine falls back to the default ruleset for the map's tileset:

```csharp
InvalidCustomRules = true;
InvalidCustomRulesException = e;
Rules = Ruleset.LoadDefaultsForTileSet(modData, Tileset);
```

This is the **correct architectural handling** for invalid map custom rules: a runtime `try/catch` fallback in `Map`, not a pre-validation or reflective exemption parser. The map remains loadable and the user can see/inspect it in the shellmap, but gameplay will use the mod defaults.

![Extension points diagram](images/Part_02_Chapter_02_Manifest-extension-hook-diagram-showing-the-interface-s-to-implement-b4a27b.svg)

## Extension Points


### IGlobalModData

Any C# class implementing `IGlobalModData` can be declared as a top-level `mod.yaml` block by name. `ModData` will instantiate it and expose it via `GetOrCreate<T>()` / `GetOrNull<T>()`. Examples in the stock mods include `MapGrid`, `GameSpeeds`, `AssetBrowser`, and `DiscordService`.

### IFileSystemLoader

The `FileSystem:` block names a class implementing `IFileSystemLoader`. The loader is responsible for mounting packages into `ModFiles`. Mods can implement custom loaders if they have unusual archive formats.

### ILoadScreen

The `LoadScreen:` block names an `ILoadScreen` implementation. It receives the `LoadScreen` YAML block and can render progress while the mod loads.

### IRulesetLoaded

Traits and weapon components can implement `IRulesetLoaded` or `IRulesetLoaded<T>` to receive a callback after the full `Ruleset` is built. This is the standard place to resolve actor/weapon references that cannot be resolved during YAML parsing.

### ILobbyCustomRulesIgnore

A marker interface. If a trait's `Info` class implements it, map overrides for that trait will not cause the map to be flagged as having unsafe custom rules.

![Common pitfalls  guardrails diagram](images/Part_02_Chapter_02_Manifest-checklist-infographic-style-diagram-summarizing-the-top-pitf-fb069e.svg)

## Common Pitfalls / Guardrails


### 1. RulesetCache does not exist anymore

Documentation and older tutorials may refer to `RulesetCache.Load(...)`. In the current engine, call `Ruleset.LoadDefaults`, `Ruleset.LoadDefaultsForTileSet`, or `Ruleset.Load` directly. `ModData.DefaultRules` is the recommended entry point for the default ruleset.

### 2. Case sensitivity of actor keys

`Ruleset` lower-cases actor names when building the dictionary (`k.Key.ToLowerInvariant()`), but the YAML keys themselves are case-sensitive during merging. Keep actor names consistent across rules, sequences, and map files.

### 3. The `^` abstract prefix

Abstract template actors must start with `^`. They are filtered out of the runtime `Actors` dictionary. If you accidentally name a real actor `^MyTank`, it will not be spawnable.

### 4. Missing `FileSystem` section

`Manifest` throws `InvalidDataException` if `FileSystem` is missing. This is the only top-level block treated as mandatory inside `Manifest` (besides `mod.yaml` itself and `LoadScreen`).

### 5. Thread affinity

`ModData` records the thread that constructed it in `initialThreadId`. `HandleLoadingProgress` only updates the load screen when the current thread is that thread. `Ruleset` parsing may run on a background `Task` so the load screen can animate, but it will only do so when `modData.IsOnMainThread` is true.

### 6. Invalid map custom rules are swallowed

If a map's custom rules throw, the map still loads using default rules. This is intentional for usability, but it means the engine silently ignores broken overrides. Check the `debug` log for `Failed to load rules for ...` messages. The `InvalidCustomRules` and `InvalidCustomRulesException` properties on `Map` expose this state to UI code.

### 7. `ILobbyCustomRulesIgnore` is not a runtime exemption

The interface only affects the *lobby safety check* (`DefinesUnsafeCustomRules`). It does **not** exempt a trait from YAML parsing or from overriding mod defaults. The phrase "reflective exemption parser" is a misnomer: the engine does not use reflection to skip rule parsing; it uses reflection in `AnyFlaggedTraits` only to decide whether a trait's presence makes a map "unsafe" for a no-custom-rules lobby.

### 8. Map rule overrides can break terrain validation

`PostInit()` replaces invalid terrain tiles with the default tile from the ruleset's `TerrainInfo`. If the fallback ruleset (after a failed custom rule load) does not match the map's tileset, the map may still be playable but the terrain could differ from the author's intent.

### 9. `GlobalModData` types must exist and implement the interface

If a top-level `mod.yaml` block is not in the reserved list and its C# type cannot be found or does not implement `IGlobalModData`, `ModData` throws `InvalidDataException`. This is a common error when adding custom mod-data modules.

### 10. `Map` is the file system for map assets

Because `Map` implements `IReadOnlyFileSystem`, `Ruleset.Load` can resolve paths relative to the map package (e.g. `mymap|rules.yaml`). This is why map-specific files and inline rules are merged with the same `MiniYaml.Load` path used for mod files.

## Summary

This chapter explains the four pillars that turn a mod's YAML configuration into a playable game world.

After reading this chapter, you should be able to:

- **Load and inline includes.** It reads `mod.yaml` with `[MiniYaml](../appendices/Appendix_A_Glossary.md).FromStream`, then expands every `Include:` node in-place by loading the referenced file and splicing its nodes into the tree. This allows mods to split configuration into reusable files.
- **Merge inherited overrides.** The entire node tree is merged with `MiniYaml.Merge([nodes])`, then flattened into a `Dictionary<string, MiniYaml>` via `ToDictionary()`.
- **Populate strongly-typed fields.** Each top-level key (e.g. `Rules`, `Sequences`, `Weapons`, `Voices`, `Music`, `Chrome`, `TileSets`, `Assemblies`, etc.) is read into an immutable array or a custom object.

If any of the concepts above feel unclear, review the relevant section before continuing. For source files and further reading, see the References section.


## References

- `OpenRA.Game/Manifest.cs` — `Manifest` class, `ModMetadata`, `RendererConstants`, `ReservedModuleNames`.
- `OpenRA.Game/ModData.cs` — `ModData` constructor, `IGlobalModData` loading, lazy default rules, `PrepareMap`.
- `OpenRA.Game/GameRules/Ruleset.cs` — `Ruleset` construction, `LoadDefaults`, `LoadDefaultsForTileSet`, `Load`, `DefinesUnsafeCustomRules`, `AnyFlaggedTraits`.
- `OpenRA.Game/GameRules/ActorInfo.cs` — `ActorInfo`, `AbstractActorPrefix`, `TraitInstanceSeparator`, trait loading, construction order.
- `OpenRA.Game/Primitives/ActorInfoDictionary.cs` — system actor guarantee.
- `OpenRA.Game/Map/Map.cs` — `MapField`, `RuleDefinitions`, `PostInit`, invalid custom rule fallback.
- `OpenRA.Game/Map/MapPreview.cs` — `DefinesUnsafeCustomRules`, `LoadRuleset`.
- `OpenRA.Game/Traits/TraitsInterfaces.cs` — `ILobbyCustomRulesIgnore`, `IRulesetLoaded`, `IGlobalModData`.
- `OpenRA.Game/ObjectCreator.cs` — assembly loading, type resolution, `CreateObject`.
- `OpenRA.Game/MiniYaml.cs` — `MiniYaml.Merge`, `MiniYaml.Load`, `MergePartial`, `ToDictionaryWithConflictLog`.

## What to read next

- [Part 2.4 — Rulesets, Actors, and Weapons](Part_02_Chapter_04_Rules_Weapons.md): the `Ruleset` built by `ModData` is the central data structure described here; continue there for the actor and weapon dictionaries.
- [Part 3.1 — Mod SDK and Project Structure](Part_03_Chapter_01_Mod_SDK.md): the `mod.yaml` manifest and `ModData` are the core of the SDK; this chapter explains them from a mod-author perspective.
- [Part 2.3 — FieldLoader and Type Conversions](Part_02_Chapter_03_FieldLoader.md): after `MiniYaml` is parsed, `FieldLoader` converts YAML values into C# trait and global-mod-data fields.
- [Appendix H — Asset Visual Reference](../appendices/Appendix_H_Asset_Visual_Reference.md): for a categorical lookup of the asset manifest keys (Sequences, TileSets, Cursors, Chrome, Voices, Notifications, Music, etc.) and their engine loaders.
- Git history: commit `82a9d69a51` ("Remove RulesetCache and push rule parsing to background thread.") removed `OpenRA.Game/GameRules/RulesetCache.cs` and moved its logic into `Ruleset.cs`.