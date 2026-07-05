# Chapter 10.1 — Official Mods

## Purpose

OpenRA ships with four official [mods](../appendices/Appendix_A_Glossary.md) that demonstrate the engine's capabilities and serve as reference implementations: **Red Alert** (`ra`), **Tiberian Dawn** (`cnc`), **Dune 2000** (`d2k`), and **Tiberian Sun** (`ts`). This chapter describes the structure, content, and unique features of each official mod, and how they can be used as templates for new mods.

## Learning Objectives


After studying this chapter, you should be able to:

- Describe the four official OpenRA mods and their unique features.
- Explain how official mods inherit from the shared common mod.
- Understand the structure of mod manifests, content installers, and maps.
- Configure AI personalities, game speeds, and tile sets in YAML.
- Use an official mod as a template for a new mod.
- Identify common pitfalls when modifying official mod content.

## Files

| File | Responsibility |
| :---- | :---- |
| `mods/ra/mod.yaml` | Red Alert manifest. |
| `mods/cnc/mod.yaml` | Tiberian Dawn manifest. |
| `mods/d2k/mod.yaml` | Dune 2000 manifest. |
| `mods/ts/mod.yaml` | Tiberian Sun manifest. |
| `mods/ra*/` directories | Red Alert and its content installer. |
| `mods/cnc*/` directories | Tiberian Dawn and its content installer. |
| `mods/d2k*/` directories | Dune 2000 and its content installer. |
| `mods/ts*/` directories | Tiberian Sun and its content installer. |
| `mods/common/` | Shared chrome, assets, traits, and widgets. |
| `mods/common-content/` | Shared content installer assets. |
| `mods/ra/maps/`, `mods/cnc/maps/`, etc. | Built-in maps and missions. |

![Architecture diagram](images/Part_10_Chapter_01_Official_Mods-architecture-diagram-showing-the-main-classes-interfaces-and-9161e6.svg)

## Architecture


### Shared common mod

The `mods/common/` directory contains assets, rules, [traits](../appendices/Appendix_A_Glossary.md), chrome, and widgets shared by all official mods. Each official mod inherits from `common` by mounting it and referencing its files. The content installers (`mods/ra-content/`, `mods/cnc-content/`, etc.) handle downloading or extracting original game assets.

### Official mod inheritance

Each official mod declares its dependencies and assets in `mod.yaml`. For example:

```yaml
RequiresMods:
    common: {APP_VERSION}
```

This makes the mod a child of `common`, allowing it to override specific files while reusing the rest.

### Mod-specific code

Official mods have dedicated C# assemblies:

- `OpenRA.Mods.Cnc` — C&C-specific traits, sprites, video, and audio loaders.
- `OpenRA.Mods.D2k` — Dune 2000-specific traits (e.g., building on sand, spice, sandworms).
- `OpenRA.Mods.TS` — Tiberian Sun-specific traits (e.g., isometric terrain, jumpjets, voxels).

Red Alert uses `OpenRA.Mods.Common` plus a few C&C-specific features for some assets.

![Data flow  code path diagram](images/Part_10_Chapter_01_Official_Mods-sequence-flow-diagram-tracing-the-execution-path-from-trigge-035864.svg)

## Data Flow / Code Path


### Mod loading

When a player selects a mod, the engine loads its `mod.yaml`, mounts its packages, and creates a `ModData` object. The `ModData` loads the rules, sequences, chrome, and other assets declared in the [Manifest](../appendices/Appendix_A_Glossary.md).

### Content installer

Before an official mod can run, it may need original game assets. The content installer (`mods/*-content/`) checks for the required files and offers to download or copy them. The installer is itself a YAML-defined screen with C# logic.

### Map loading

Official mods ship with built-in maps in `mods/*/maps/`. Multiplayer maps are loaded from the map cache. Missions are single-player or cooperative maps with Lua scripts.

### Mission scripts

Many single-player missions use [Lua scripts](../appendices/Appendix_A_Glossary.md) for objectives, triggers, and cinematics. These are stored in `mods/*/maps/<mission-name>/` alongside the map data.

![Configuration (yaml) diagram](images/Part_10_Chapter_01_Official_Mods-annotated-yaml-snippet-diagram-showing-the-key-fields-and-ho-6a1b98.svg)

## Configuration (YAML)


### Official mod manifest examples

Each official mod has a `mod.yaml` that defines:

- `Metadata` — title, version, website.
- `RequiresMods` — parent mod (usually `common`).
- `FileSystem` — package mounts.
- `MapFolders` — map search paths.
- `Rules`, `Weapons`, `Sequences`, `Cursors`, `Chrome`, `ChromeLayout`, `Voices`, `Notifications`, `Music`, `[TileSets](../appendices/Appendix_A_Glossary.md)`, `FluentMessages`.
- `Assemblies` — mod-specific DLLs.
- `Loaders` — format loaders.

### Tile sets

Each mod defines its own tile sets:

- `ra` — temperate, snow, desert, interior.
- `cnc` — temperate, winter, desert.
- `d2k` — arrakis.
- `ts` — temperate, snow, urban, etc.

### Game speeds

Each mod defines game speeds in `mods/*/rules/misc.yaml` or similar:

```yaml
GameSpeeds:
    DefaultSpeed: normal
    Speeds:
        normal:
            Name: Normal
            Timestep: 40
            OrderLatency: 3
```

## Interconnectivity

- **Depends on:** [Part 3.1 — Mod SDK and Project Structure](Part_03_Chapter_01_Mod_SDK.md) (mod.yaml and manifest), [Part 3.3 — Build Pipeline and Packaging](Part_03_Chapter_03_Build_Packaging.md) (build and packaging), [Part 2.1 — MiniYaml Parser](Part_02_Chapter_01_MiniYaml.md) (MiniYaml), [Part 6.3 — Virtual File System](Part_06_Chapter_03_VFS.md) (VFS for mod assets), [Part 6.1 — Lua Scripting and Eluant](Part_06_Chapter_01_Lua_Eluant.md) (Lua scripts), [Part 2.2 — Manifest and Mod Metadata](Part_02_Chapter_02_Manifest.md) (maps).
- **Used by:** [Part 10.2 — Online Services and References](Part_10_Chapter_02_Online_References.md) (online references point to official mods), [Part 10.3 — Porting, Modding, and Developer Workflows](Part_10_Chapter_03_Port_And_Modding.md) (porting guides use official mods as source).

![Algorithms diagram](images/Part_10_Chapter_01_Official_Mods-algorithm-diagram-or-pseudocode-flowchart-for-the-non-trivia-5983ed.svg)

## Algorithms


### Asset extraction

The content installer reads installer definitions in YAML (e.g., `downloads.yaml`) to know which original game files are needed and where to obtain them. It can download from the OpenRA mirrors or extract from a local installation/CD.

### Mission objective system

`MissionObjectiveProperties` and `MissionObjective` are Lua-exposed classes that track primary and secondary objectives. Missions add objectives via Lua and mark them as completed or failed.

### AI personalities

Official mods define AI bot configurations in YAML under the `Player` actor:

```yaml
Player:
    ModularBot:
        ...
    SquadManagerBotModule:
        ...
```

Each mod has different default values for squad sizes, attack intervals, and unit types.

### Mod-specific rendering

- `TS` uses `EnableDepthBuffer` for isometric terrain and buildings.
- `TS` supports voxel models for some units.
- `D2k` uses `SpriteAlpha` for spice bloom overlays.
- `Cnc` and `D2k` use custom building placement logic.

![Extension points diagram](images/Part_10_Chapter_01_Official_Mods-extension-hook-diagram-showing-the-interface-s-to-implement-b4a27b.svg)

## Extension Points


### Create a new official-style mod

Copy an official mod directory, rename it, update `mod.yaml`, and replace assets and rules. Use `RequiresMods` to inherit from `common` or from another mod.

### Add a new faction

Add a faction entry in the `Faction` world trait YAML and add faction-specific actors or palettes.

### Add custom missions

Create a map in `mods/<mod>/maps/`, add a Lua script, and define mission objectives. Reference the mission in `mod.yaml` under `Missions`.

### Add custom AI

Copy the `Player` actor definition from an official mod and adjust the bot modules and their parameters. Define multiple AI personalities by varying the YAML.

### Add custom content installer

Create a `mods/<mod>-content/` directory with `installer.yaml` and `downloads.yaml`. Define the required files and download sources.

![Common pitfalls  guardrails diagram](images/Part_10_Chapter_01_Official_Mods-checklist-infographic-style-diagram-summarizing-the-top-pitf-fb069e.svg)

## Common Pitfalls / Guardrails


- **Asset dependencies:** official mods require original game assets. Make sure the content installer is configured correctly.
- **Mod version:** the `RequiresMods` version must match the engine version.
- **Map compatibility:** `SupportsMapsFrom` controls which mods can load a map. Make sure maps are compatible with the mod's tile sets and rules.
- **Common mod overrides:** when overriding files from `common`, list them after the common entries in `mod.yaml`.
- **Mission scripts:** Lua scripts are not validated by `make test` unless the map is included in the test list. Test missions manually.
- **TS isometric rendering:** Tiberian Sun uses a different coordinate system and depth buffer. Mods based on TS should understand the isometric pipeline.
- **D2k tile rules:** Dune 2000 has unique terrain rules (buildable sand, rock, spice). Modifying these can break the building and harvester logic.

## What to read next

- [Part 3.1 — Mod SDK and Project Structure](Part_03_Chapter_01_Mod_SDK.md) for how manifests and `ModData` are structured.
- [Part 10.3 — Porting, Modding, and Developer Workflows](Part_10_Chapter_03_Port_And_Modding.md) for practical workflows when using an official mod as a template.
- [Appendix E — Practical Modding Recipes](../appendices/Appendix_E_Practical_Recipes.md) for copy-paste examples based on the official mods.

## Summary

This chapter describes the four official OpenRA [mods](../appendices/Appendix_A_Glossary.md) — Red Alert, Tiberian Dawn, Dune 2000, and Tiberian Sun — and how they serve as reference implementations.

If any of the concepts above feel unclear, review the relevant section before continuing. For source files and further reading, see the References section.


## References

- `mods/ra/mod.yaml` — Red Alert manifest.
- `mods/cnc/mod.yaml` — Tiberian Dawn manifest.
- `mods/d2k/mod.yaml` — Dune 2000 manifest.
- `mods/ts/mod.yaml` — Tiberian Sun manifest.
- `mods/common/mod.yaml` — Common mod manifest.
- `mods/*-content/installer.yaml` — content installer definitions.
- `OpenRA.Mods.Cnc/` — C&C-specific code.
- `OpenRA.Mods.D2k/` — Dune 2000-specific code.
- `OpenRA.Mods.TS/` — Tiberian Sun-specific code.