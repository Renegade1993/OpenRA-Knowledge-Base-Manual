# Chapter 3.1 — Mod SDK and Project Structure

## Purpose

OpenRA is designed to be heavily modded. The **[Mod SDK](../appendices/Appendix_A_Glossary.md)** provides the project structure, [manifest](../appendices/Appendix_A_Glossary.md) format, and build conventions for creating standalone mods. This chapter explains the anatomy of a mod package, the `mod.yaml` manifest, the `[ModData](../appendices/Appendix_A_Glossary.md)` object, and how the engine discovers and loads mod assets and code.

## Learning Objectives


After studying this chapter, you should be able to:

- Explain the purpose of the OpenRA Mod SDK and the anatomy of a mod package.
- List the key sections of mod.yaml and what each declares.
- Describe how mods inherit from parent mods using RequiresMods.
- Explain how the engine discovers and registers mods.
- Create custom global mod data and load it via IGlobalModData.
- Outline the steps to add custom C# code and asset loaders to a mod.

## Files

| File | Responsibility |
| :---- | :---- |
| `mod.yaml` (in mod package) | Manifest: metadata, file system, rules, sequences, chrome, loaders, dependencies. |
| `OpenRA.Game/Manifest.cs` | Parses `mod.yaml` and exposes manifest sections. |
| `OpenRA.Game/ModData.cs` | Creates the file system, loaders, rules, widgets, and map cache for a mod. |
| `OpenRA.Game/ObjectCreator.cs` | Creates objects by type name using mod assemblies. |
| `OpenRA.Game/ExternalMods.cs` | Discovers installed mods on the system. |
| `OpenRA.Game/UtilityCommands/RegisterModCommand.cs` | Registers a mod with the system. |
| `OpenRA.Game/UtilityCommands/UnregisterModCommand.cs` | Unregisters a mod. |
| `OpenRA.Game/Platform.cs` | Engine directory and platform detection. |
| `mods/*` | Official mod packages (ra, cnc, d2k, ts). |
| `OpenRA.Mods.*` | C# assemblies containing mod-specific traits. |

![Architecture diagram](images/Part_03_Chapter_01_Mod_SDK-architecture-diagram-showing-the-main-classes-interfaces-and-9161e6.svg)

## Architecture


### Mod package structure

A mod package is a folder or ZIP containing:

```
mods/my-mod/
    mod.yaml
    rules/
    sequences/
    chrome/
    audio/
    bits/
    languages/
    maps/
    ...
```

`mod.yaml` is the entry point. It declares everything the engine needs to load.

### Manifest sections

Key sections of `mod.yaml`:

| Section | Purpose |
| :---- | :---- |
| `Metadata` | Title, version, website, hidden flag. |
| `FileSystem` | Packages to mount and package loader setup. |
| `MapFolders` | Paths for map discovery. |
| `Rules` | [YAML](../appendices/Appendix_A_Glossary.md) files for [actor](../appendices/Appendix_A_Glossary.md) rules. |
| `Weapons` | YAML files for [weapon](../appendices/Appendix_A_Glossary.md) definitions. |
| `Sequences` | YAML files for sprite sequences. |
| `Cursors` | YAML files for cursor definitions. |
| `Chrome` | YAML files for chrome asset definitions. |
| `ChromeLayout` | YAML files for widget layouts. |
| `ChromeMetrics` | YAML files for UI metrics. |
| `Voices` | YAML files for unit voices. |
| `Notifications` | YAML files for audio notifications. |
| `Music` | YAML files for music tracks. |
| `FluentMessages` | `.ftl` localization files. |
| `TileSets` | YAML files for terrain tile sets. |
| `Assemblies` | C# DLLs to load. |
| `Loaders` | [Asset loader](../appendices/Appendix_A_Glossary.md) setup (sprite, sound, video, package, sequence, terrain). |
| `ServerTraits` | Server-side traits. |
| `LoadScreen` | Loading screen class. |
| `DefaultOrderGenerator` | Default order generator class. |
| `RequiresMods` | Parent mod dependencies. |
| `SupportsMapsFrom` | Compatible map sources. |

### Inheritance

Mods can inherit from another mod using `RequiresMods`:

```yaml
RequiresMods:
    ra: {APP_VERSION}
```

This allows the child mod to reuse the parent's assets and override specific files. The file system mounts the parent mod package first, then the child, so child files take precedence.

### Mod discovery

`ExternalMods` scans the engine directory and registered locations for mod packages. Each mod is identified by its `mod.yaml` file and registered with its ID.

### Global mod data

Custom global mod data can be declared in `mod.yaml` under the mod ID:

```yaml
my-mod:
    MyGlobalData:
        Foo: 123
```

The engine creates a singleton `IGlobalModData` object of type `MyGlobalData` and loads it via `FieldLoader`.

![Data flow  code path diagram](images/Part_03_Chapter_01_Mod_SDK-sequence-flow-diagram-tracing-the-execution-path-from-trigge-035864.svg)

## Data Flow / Code Path


### Loading a mod

```csharp
public ModData(Manifest mod, InstalledMods mods, bool useLoadScreen = false)
{
    Manifest = new Manifest(mod.Id, mod.Package);
    ObjectCreator = new ObjectCreator(Manifest, mods);
    PackageLoaders = ObjectCreator.GetLoaders<IPackageLoader>(Manifest.PackageFormats, "package");
    ModFiles = new FS(mod.Id, mods, PackageLoaders);

    FileSystemLoader = ObjectCreator.GetLoader<IFileSystemLoader>(Manifest.FileSystem.Value, "filesystem");
    FieldLoader.Load(FileSystemLoader, Manifest.FileSystem);
    FileSystemLoader.Mount(Manifest, ModFiles, ObjectCreator);
    ModFiles.TrimExcess();

    ...
    WidgetLoader = new WidgetLoader(Manifest, DefaultFileSystem);
    MapCache = new MapCache(Manifest, ModFiles);
    SoundLoaders = ObjectCreator.GetLoaders<ISoundLoader>(Manifest.SoundFormats, "sound");
    SpriteLoaders = ObjectCreator.GetLoaders<ISpriteLoader>(Manifest.SpriteFormats, "sprite");
    VideoLoaders = ObjectCreator.GetLoaders<IVideoLoader>(Manifest.VideoFormats, "video");
    SpriteSequenceLoader = ObjectCreator.GetLoader<ISpriteSequenceLoader>(Manifest.SpriteSequenceFormat, "sequence");
    Hotkeys = new HotkeyManager(ModFiles, ObjectCreator, Manifest);
    Cursors = ParseCursors(Manifest, DefaultFileSystem);

    defaultRules = Exts.Lazy(() => Ruleset.LoadDefaults(this));
    defaultTerrainInfo = Exts.Lazy(() => ...);
}
```

### Object creation

`ObjectCreator` resolves class names to types by scanning the mod assemblies and the engine assemblies:

```csharp
public T CreateObject<T>(string className, object[] args)
{
    ...
}
```

This is how YAML entries like `Mobile` or `Health` map to `OpenRA.Mods.Common.Traits.Mobile`.

### File system loader

`IFileSystemLoader` is created from the `FileSystem` section of `mod.yaml`. It mounts the mod packages, optional content packages, and inherited mod packages.

### Mod registration

The `RegisterModCommand` utility command registers a mod so it appears in the mod chooser. `UnregisterModCommand` removes the registration.

![Configuration (yaml) diagram](images/Part_03_Chapter_01_Mod_SDK-annotated-yaml-snippet-diagram-showing-the-key-fields-and-ho-6a1b98.svg)

## Configuration (YAML)


### Example mod.yaml

```yaml
Metadata:
    Title: My Custom Mod
    Version: {VERSION}
    Website: https://example.com

RequiresMods:
    ra: {APP_VERSION}

FileSystem:
    LoadScreen: DefaultLoadScreen
    DefaultOrderGenerator: OpenRA.Orders.GenericSelect

MapFolders:
    my-mod|maps: Container
    ^UserMapsDir/my-mod: User

Rules:
    my-mod|rules/defaults.yaml
    my-mod|rules/infantry.yaml
    my-mod|rules/vehicles.yaml

Sequences:
    my-mod|sequences/infantry.yaml

Assemblies:
    my-mod|OpenRA.Mods.MyMod.dll

Loaders:
    Sprite:
        - OpenRA.Mods.Common.SpriteLoaders.ShpTSLoader
    Sound:
        - OpenRA.Mods.Common.AudioLoaders.AudLoader
    Sequence:
        - OpenRA.Mods.Common.SpriteLoaders.DefaultSpriteSequenceLoader
```

### Map compatibility

`SupportsMapsFrom` allows the mod to load maps from another mod:

```yaml
SupportsMapsFrom: ra, cnc
```

### Global mod data

```yaml
my-mod:
    MyGlobalData:
        Foo: 123
```

## Interconnectivity

- **Depends on:** [Part 2.1 — MiniYaml and the Rules File Format](Part_02_Chapter_01_MiniYaml.md), [Part 2.2 — Manifest, ModData, Ruleset, and RulesetCache](Part_02_Chapter_02_Manifest.md), [Part 2.3 — FieldLoader and Type Conversions](Part_02_Chapter_03_FieldLoader.md), [Part 2.4 — Rulesets, Actors, and Weapons](Part_02_Chapter_04_Rules_Weapons.md), [Part 6.3 — Virtual File System](Part_06_Chapter_03_VFS.md).
- **Used by:** [Part 3.2 — Mod SDK Bootstrapping](Part_03_Chapter_02_SDK_Bootstrap.md) reads `mod.config`, [Part 3.3 — Build Pipeline and Packaging](Part_03_Chapter_03_Build_Packaging.md) uses `mod.yaml`, [Part 4.1 — Renderer, Sheet, and Sprite](Part_04_Chapter_01_Renderer.md) provides renderer constants, [Part 4.3 — Widgets and Chrome](Part_04_Chapter_03_Widgets.md) provides chrome, [Part 5.1 — Audio Architecture](Part_05_Chapter_01_Audio_Architecture.md) provides audio loaders, [Part 6.5 — Asset Loaders](Part_06_Chapter_05_Asset_Loaders.md) loads assets, and [Part 10.1 — Official Mods](Part_10_Chapter_01_Official_Mods.md) documents the mods.

![Algorithms diagram](images/Part_03_Chapter_01_Mod_SDK-algorithm-diagram-or-pseudocode-flowchart-for-the-non-trivia-5983ed.svg)

## Algorithms


### Include processing

`Manifest` supports inline `Include` directives:

```yaml
Include: other.yaml
```

The included file is loaded and its nodes are inserted at the include location.

### Reserved module names

`mod.yaml` has a reserved set of top-level keys. Custom global mod data must be declared under the mod ID, not at the top level.

### Loader discovery

Loaders are discovered by naming convention. The manifest lists class names; `ObjectCreator` resolves them by looking for types in the loaded assemblies.

### Lazy ruleset loading

`DefaultRules` and `DefaultTerrainInfo` are loaded lazily. They are not parsed until first use, which improves startup time for menu screens.

![Extension points diagram](images/Part_03_Chapter_01_Mod_SDK-extension-hook-diagram-showing-the-interface-s-to-implement-b4a27b.svg)

## Extension Points


### Create a new mod

Start from the OpenRA Mod SDK template, or copy an official mod. Customize `mod.yaml`, rules, sequences, and assets. Register the mod with the utility command.

### Add custom code

Create a new C# project referencing `OpenRA.Game` and `OpenRA.Mods.Common`. Build the DLL and add it to `Assemblies`. Define custom traits, weapons, activities, and widgets.

### Add custom global mod data

Implement `IGlobalModData` and declare it in `mod.yaml`. Access it via `modData.GetOrCreate<T>()`.

### Add custom file system behavior

Implement `IFileSystemLoader` and reference it in the `FileSystem` section. This is useful for mods that need to mount files from non-standard locations.

### Add custom load screen

Implement `ILoadScreen` and reference it in `LoadScreen`. The load screen can display mod-specific artwork and progress.

![Common pitfalls  guardrails diagram](images/Part_03_Chapter_01_Mod_SDK-checklist-infographic-style-diagram-summarizing-the-top-pitf-fb069e.svg)

## Common Pitfalls / Guardrails


- **Mod ID consistency:** the mod ID must match the package name and the manifest references. Mismatches cause the mod to fail to load.
- **RequiresMods version:** the version string must match the engine's `AppVersion`. A mismatch produces a "mod is not compatible" error.
- **Assembly loading:** mod DLLs must be built against the same engine version. Mismatched assemblies can cause runtime errors or crashes.
- **YAML overrides:** inherited mods are loaded first; child files override them. Make sure child files are listed after parent files if they depend on parent definitions.
- **MapFolders:** paths must be valid. `^UserMapsDir` maps to the user's local maps directory.
- **Global mod data naming:** must be declared under the mod ID key, not a reserved top-level key.
- **Loader registration:** each format loader must be listed in the correct `Loaders` category (sprite, sound, video, package, sequence, terrain).
- **Localization:** `FluentMessages` must point to valid `.ftl` files. Missing messages will show as their keys.

## Summary

This chapter explains the OpenRA [Mod SDK](../appendices/Appendix_A_Glossary.md) structure: the `mod.yaml` manifest, the `ModData` object, and how the engine loads mod assets and code.

If any of the concepts above feel unclear, review the relevant section before continuing. For source files and further reading, see the References section.


## References

- `mod.yaml` files in official mods.
- `OpenRA.Game/Manifest.cs` — manifest parser.
- `OpenRA.Game/ModData.cs` — mod data initialization.
- `OpenRA.Game/ObjectCreator.cs` — object creation.
- `OpenRA.Game/ExternalMods.cs` — mod discovery.
- `OpenRA.Game/UtilityCommands/RegisterModCommand.cs` — mod registration.
- `OpenRA.Game/UtilityCommands/UnregisterModCommand.cs` — mod unregistration.
- `OpenRA.Game/Platform.cs` — engine/platform paths.

## What to read next

- Now that you understand the anatomy of a mod package and the `mod.yaml` manifest, read [Part 3.2 — Mod SDK Bootstrapping](Part_03_Chapter_02_SDK_Bootstrap.md) to learn how `mod.config` and the SDK launch scripts turn that package into a running game.
- For the engine internals behind `Manifest` and `ModData`, continue to [Part 2.2 — Manifest, ModData, Ruleset, and RulesetCache](Part_02_Chapter_02_Manifest.md).
- Now that you can load a mod project, read [Part 3.3 — Build Pipeline and Packaging](Part_03_Chapter_03_Build_Packaging.md) to learn how the SDK compiles, packages, and ships a mod from the project structure defined here.