# Chapter 6.3 — Virtual File System

## Purpose

OpenRA's assets come from many sources: loose mod directories, ZIP archives, Westwood MIX files, and even InstallShield CAB archives. The **Virtual File System** ([VFS](../appendices/Appendix_A_Glossary.md)) unifies these sources into a single layered namespace where code can open files by name without knowing the underlying container. This chapter explains how [packages](../appendices/Appendix_A_Glossary.md) are loaded, mounted, and resolved.

## Learning Objectives


After studying this chapter, you should be able to:

- Explain the purpose of the Virtual File System and the layered package model.
- Describe how IPackageLoader implementations handle different archive formats.
- Trace file resolution through explicit mounts, the file index cache, and fallback package scanning.
- Configure Packages and [Package loaders](../appendices/Appendix_A_Glossary.md) in mod.yaml.
- Understand how map-local files override mod files through mount priority.
- Add a new package format by implementing IPackageLoader.

## Files

| File | Responsibility |
| :---- | :---- |
| `OpenRA.Game/FileSystem/FileSystem.cs` | The main `FileSystem` class, mount table, file index, and `IReadOnlyFileSystem` implementation. |
| `OpenRA.Game/FileSystem/IPackage.cs` | `IPackageLoader`, `IReadOnlyPackage`, `IReadWritePackage` interfaces. |
| `OpenRA.Game/FileSystem/Folder.cs` | `Folder` package and `FolderLoader` for raw directories. |
| `OpenRA.Game/FileSystem/ZipFile.cs` | `ZipFile` package and `ZipFileLoader` for ZIP archives. |
| `OpenRA.Mods.Cnc/FileSystem/MixFile.cs` | `MixFile` package and `MixLoader` for Westwood MIX files. |
| `OpenRA.Mods.Common/FileSystem/InstallShieldPackage.cs` | `InstallShieldPackage` loader for InstallShield archives; includes InstallShield CAB decompression. |
| `OpenRA.Game/ModData.cs` | Creates the default `FileSystem` and mounts mod packages. |
| `OpenRA.Game/Map/Map.cs` | Mounts map packages and exposes map-local files. |
| `OpenRA.Game/Manifest.cs` | Declares `Packages` and `MapFolders` to mount. |

![Architecture diagram](images/Part_06_Chapter_03_VFS-architecture-diagram-showing-the-main-classes-interfaces-and-9161e6.svg)

## Architecture


### Layered package model

The VFS is a stack of `IReadOnlyPackage` instances. When a file is requested, the `FileSystem` looks up the most recently mounted package that contains the file. This allows mods to override base game assets by mounting later packages after the base packages.

### Package loaders

Each package format implements `IPackageLoader`:

```csharp
public interface IPackageLoader
{
    bool TryParsePackage(Stream s, string filename, FileSystem context, out IReadOnlyPackage package);
}
```

Loaders are registered in the mod manifest. The `FileSystem` tries each loader in order until one succeeds. The `ZipFileLoader` is always appended as a fallback.

### File index

`FileSystem` maintains a `Cache<string, List<IReadOnlyPackage>>` that maps each file name to the packages that contain it. The list is ordered by mount priority, so the last entry is the most authoritative.

<!-- DEV-NOTE [visual-aid]: VFS mount/lookup flow diagram showing manifest `Packages` → `FileSystem.Mount()` → `IPackageLoader` selection → package mounting → file index cache → explicit mount (`name|file`) or `TryOpen` cache/fallback scan → returned `Stream`. Include the `~` optional prefix and the `$` mod-reference edge cases, and show that later mounts override earlier ones. -->

![Data flow  code path diagram](images/Part_06_Chapter_03_VFS-sequence-flow-diagram-tracing-the-execution-path-from-trigge-035864.svg)

## Data Flow / Code Path


### Mod initialization

`ModData` creates a `FileSystem` and mounts the packages listed in the manifest:

```csharp
public FileSystem(string modID, IReadOnlyDictionary<string, Manifest> installedMods, IPackageLoader[] packageLoaders)
{
    this.modID = modID;
    this.installedMods = installedMods;
    this.packageLoaders = packageLoaders.Append(new ZipFileLoader()).ToArray();
}
```

The manifest's `Packages` section lists package paths to mount.

### Mounting a package

```csharp
public void Mount(string name, string explicitName = null)
{
    var optional = name.StartsWith('~');
    if (optional)
        name = name[1..];

    try
    {
        IReadOnlyPackage package;
        if (name.StartsWith('$'))
        {
            name = name[1..];
            if (!installedMods.TryGetValue(name, out var mod))
                throw new InvalidOperationException(...);

            package = mod.Package;
            modPackages.Add(package);
        }
        else
        {
            package = OpenPackage(name);
            if (package == null)
                throw new InvalidOperationException(...);
        }

        Mount(package, explicitName);
    }
    catch when (optional)
    {
    }
}
```

Packages can be identified by:

- A relative path to a file or directory.
- A mod reference starting with `$` (e.g., `$ra` to mount the Red Alert mod).
- An optional prefix `~` that suppresses errors if the package is missing.

### Explicit mounts

A package can be mounted with an explicit name:

```csharp
Mount(package, "audio");
```

Files in that package can then be accessed via `audio|filename.wav`. The `|` separator forces the lookup to a specific mount.

### File lookup

`FileSystem.TryOpen` resolves a file request:

```csharp
public bool TryOpen(string filename, out Stream s)
{
    var explicitSplit = filename.IndexOf('|');
    if (explicitSplit > 0 && explicitMounts.TryGetValue(filename[..explicitSplit], out var explicitPackage))
    {
        s = explicitPackage.GetStream(filename[(explicitSplit + 1)..]);
        if (s != null)
            return true;
    }

    s = GetFromCache(filename);
    if (s != null)
        return true;

    ...
}
```

First, explicit mounts are checked. Then the file index cache is used. If neither finds the file, the system falls back to scanning mounted packages.

### Map-local files

Each map is itself a package. When a map is loaded, its package is mounted so that scripts and rules can reference files inside the map (e.g., `script.lua`, custom tiles, or local audio). Map files take precedence over mod files because the map package is mounted after the mod packages.

### Unmounting

`Unmount` decrements the mount count. When the count reaches zero, the package is removed from the file index and disposed (unless it is a mod package). `UnmountAll` disposes all non-mod packages and clears the index.

![Configuration (yaml) diagram](images/Part_06_Chapter_03_VFS-annotated-yaml-snippet-diagram-showing-the-key-fields-and-ho-6a1b98.svg)

## Configuration (YAML)


### Manifest packages

The mod manifest declares which packages to mount:

```yaml
Packages:
    - ^Content|ra
    - assets|bits
    - audio
    - ~missing-optional
```

The order matters: later packages override earlier ones for the same filename.

### Package loaders

Loaders are registered in the manifest:

```yaml
Loaders:
    Package:
        - OpenRA.Mods.Cnc.FileSystem.MixLoader
        - OpenRA.Mods.Common.FileSystem.InstallShieldLoader
```

`ZipFileLoader` is always added automatically.

### Map packages

Maps are loaded as packages automatically. The map's rules, scripts, and assets are accessible relative to the map package.

## Practical Example: Shipping a Custom Audio Package

Suppose you want to distribute a small mod pack that replaces a few in-game sounds without editing the base mod files.

1. Put the replacement WAV files in a new folder next to your mod content, e.g. `mods/my-mod/audio/`.
2. Declare the folder as a package in `mod.yaml`:

```yaml
Packages:
    - ^Content|ra
    - audio
    - my-mod-audio
```

3. Reference the files in your weapon or notification YAML using the explicit mount syntax:

```yaml
M1Carbine:
    Report: my-mod-audio|gun_custom.wav
```

Because `my-mod-audio` is mounted after the base `audio` package, `gun_custom.wav` takes precedence for any request that uses the explicit mount. If the file is optional, you can prefix the package with `~` so a missing folder does not crash the game.

This example shows how the VFS layers packages, uses explicit mounts, and lets mod authors override assets without touching the original files.

## Interconnectivity

- **Depends on:** [Part 2.1 — MiniYaml Parser](Part_02_Chapter_01_MiniYaml.md), [Part 3.1 — Mod SDK and Project Structure](Part_03_Chapter_01_Mod_SDK.md), [Part 6.1 — Lua Scripting and Eluant](Part_06_Chapter_01_Lua_Eluant.md).
- **Used by:** [Part 2.4 — Rulesets, Actors, and Weapons](Part_02_Chapter_04_Rules_Weapons.md), [Part 5.1 — Audio Architecture](Part_05_Chapter_01_Audio_Architecture.md), [Part 5.3 — Music](Part_05_Chapter_03_Music.md), [Part 6.1 — Lua Scripting and Eluant](Part_06_Chapter_01_Lua_Eluant.md), [Part 6.5 — Asset Loaders](Part_06_Chapter_05_Asset_Loaders.md), [Part 4.1 — Renderer, Sheet, and Sprite](Part_04_Chapter_01_Renderer.md), [Part 10.1 — Official Mods](Part_10_Chapter_01_Official_Mods.md).

For a categorical lookup of package formats and the asset classes that flow through the VFS, see [Appendix H — Asset Visual Reference](../appendices/Appendix_H_Asset_Visual_Reference.md).

![Algorithms diagram](images/Part_06_Chapter_03_VFS-algorithm-diagram-or-pseudocode-flowchart-for-the-non-trivia-5983ed.svg)

## Algorithms


### Package format detection

`OpenPackage` resolves a path and tries to parse it as a package:

```csharp
public IReadOnlyPackage OpenPackage(string filename)
{
    var resolvedPath = Platform.ResolvePath(filename);
    if (!resolvedPath.Contains('|') && Directory.Exists(resolvedPath))
        return new Folder(resolvedPath);

    if (TryGetPackageContaining(filename, out var parent, out var subPath))
        return parent.OpenPackage(subPath, this);

    var stream = Open(filename);
    if (TryParsePackage(stream, filename, out var package))
        return package;

    stream.Dispose();
    return null;
}
```

Directories are opened as `Folder` packages. Files are opened as streams and passed to each package loader.

### Loader chain

```csharp
public bool TryParsePackage(Stream stream, string filename, out IReadOnlyPackage package)
{
    package = null;
    foreach (var packageLoader in packageLoaders)
        if (packageLoader.TryParsePackage(stream, filename, this, out package))
            return true;

    return false;
}
```

A loader that recognizes the stream takes ownership of it. If no loader recognizes the stream, the caller must dispose it.

### File index priority

When a package is mounted, its contents are added to the file index. Re-mounting the same package moves it to the end of the list for each file, increasing its priority. The `GetFromCache` method uses `LastOrDefault` to select the highest-priority package.

### Case insensitivity

`ResolveCaseInsensitivePath` normalizes paths to support case-insensitive lookups. This is important because many legacy game archives store filenames in uppercase while mod YAML uses lowercase.

![Extension points diagram](images/Part_06_Chapter_03_VFS-extension-hook-diagram-showing-the-interface-s-to-implement-b4a27b.svg)

## Extension Points


### Add a new package format

Implement `IPackageLoader` and a matching `IReadOnlyPackage` class. Register the loader in the mod manifest. The loader must:

- Recognize the stream format.
- Take ownership of the stream on success.
- Reset the stream position on failure.

### Add custom mount logic

Mods can call `FileSystem.Mount(package, name)` at runtime to add explicit mounts. This is used by maps and dynamic asset loading.

### Implement a writable package

Implement `IReadWritePackage` to support modifying package contents. This is used by the map editor when saving maps.

![Common pitfalls  guardrails diagram](images/Part_06_Chapter_03_VFS-checklist-infographic-style-diagram-summarizing-the-top-pitf-fb069e.svg)

## Common Pitfalls / Guardrails


- **Stream ownership:** a package loader must dispose the stream when it takes ownership, or reset the stream position when it does not. Leaked streams can cause file locks or memory leaks.
- **Mount order:** because later mounts override earlier ones, the manifest order matters. Put optional or mod-specific packages after the base packages.
- **Optional packages:** use the `~` prefix for packages that may not exist. The VFS will ignore the mount if the package is missing.
- **Mod references:** mod packages referenced with `$` are owned by the mod manager and are not disposed by the VFS.
- **Explicit mounts:** the `|` syntax is powerful but can fail silently if the explicit mount name is misspelled.
- **Case sensitivity:** Windows and Linux handle case differently. Use the VFS `Exists` and `TryOpen` methods rather than direct file system checks.
- **Map package lifecycle:** map packages are mounted when the map loads and unmounted when the world is disposed. Do not hold streams from map packages after the map is unloaded.

## What to read next

- [Part 6.5 — Asset Loaders](Part_06_Chapter_05_Asset_Loaders.md) for the loaders that consume files exposed by the VFS.
- [Part 4.1 — Renderer, Sheet, and Sprite](Part_04_Chapter_01_Renderer.md) for how sprite data is loaded from the VFS into GPU sheets.
- [Part 2.2 — Manifest and Mod Metadata](Part_02_Chapter_02_Manifest.md) for the manifest that declares packages and package loaders.
- [Appendix A — Glossary](../appendices/Appendix_A_Glossary.md) for definitions of VFS, Package, and Package Loader.
- [Appendix H — Asset Visual Reference](../appendices/Appendix_H_Asset_Visual_Reference.md) for a categorical lookup of the asset formats that flow through the VFS.

## Summary

This chapter explains how OpenRA's Virtual File System mounts packages and resolves asset paths across MIX, ZIP, CAB, and loose mod directories.

If any of the concepts above feel unclear, review the relevant section before continuing. For source files and further reading, see the References section.


## References

- `OpenRA.Game/FileSystem/FileSystem.cs` — main VFS.
- `OpenRA.Game/FileSystem/IPackage.cs` — package interfaces.
- `OpenRA.Game/FileSystem/Folder.cs` — folder package.
- `OpenRA.Game/FileSystem/ZipFile.cs` — ZIP package.
- `OpenRA.Mods.Cnc/FileSystem/MixFile.cs` — MIX package.
- `OpenRA.Mods.Common/FileSystem/InstallShieldPackage.cs` — InstallShield package, including InstallShield CAB decompression.
- `OpenRA.Game/ModData.cs` — VFS creation.
- `OpenRA.Game/Map/Map.cs` — map package mounting.
- `OpenRA.Game/Manifest.cs` — manifest package declarations.