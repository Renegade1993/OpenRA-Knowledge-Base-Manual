# Chapter 10.3 — Porting, Modding, and Developer Workflows

## Purpose

This chapter provides practical guidance for developers and modders who want to extend OpenRA, port assets from the original games, or create new [mods](../appendices/Appendix_A_Glossary.md). It covers the recommended workflows, common tools, debugging techniques, and migration paths.

## Learning Objectives


After studying this chapter, you should be able to:

1. Set up a new mod project using the OpenRA [Mod SDK](../appendices/Appendix_A_Glossary.md) template.
2. Use the most common [Utility Commands](../appendices/Appendix_A_Glossary.md) (`--check-yaml`, `--check-missing-sprites`, `--extract`, `--map`, etc.).
3. Port original-game assets through the content installer or the `--extract` command.
4. Create a custom C# [trait](../appendices/Appendix_A_Glossary.md) and register it in a mod assembly.
5. Add a new [sequence](../appendices/Appendix_A_Glossary.md) and reference it from an actor's render traits.
6. Debug desyncs, read log files, and use the in-game debug overlays.
7. Package a mod for release using the SDK packaging scripts.
8. Compare the official mod, SDK mod, and common mod project structures and choose the right starting point.
9. Avoid the most common modding mistakes by following the pitfalls checklist.

![Mental model diagram](images/Part_10_Chapter_03_Port_And_Modding-end-to-end-worked-example-diagram-showing-the-inputs-interme-5fc6a2.svg)

## Mental Model


A new modder is building a pipeline. Every custom unit is the answer to five questions:

1. **What is it?** — the actor definition (`RECON`).
2. **What does it shoot?** — the weapon definition (`ReconGun`).
3. **What does it look like?** — the sequence definition (`recon`).
4. **How is it built?** — the build queue and the production building that provides it.
5. **Does it work?** — YAML validation and an in-game test.

Your job as a modder is to walk this pipeline in order. Start with the actor, add the weapon it needs, add the sequence it displays, place it in a build queue, then validate and launch. If any link in the chain is missing, the unit will not appear, will not fire, or will crash on load. This mental model is the fastest way to diagnose mistakes.

For more on the data formats, see [Part 2.1 — MiniYaml Parser](Part_02_Chapter_01_MiniYaml.md), [Part 2.4 — Rulesets, Actors, and Weapons](Part_02_Chapter_04_Rules_Weapons.md), and [Appendix B — Common YAML Patterns](../appendices/Appendix_B_Common_YAML_Patterns.md).

## Practical Example: From zero to first custom unit


Suppose you want to create a small mod named `cameo` that reuses the OpenRA engine but introduces one custom unit.

1. **Clone the SDK template and set up the project.**
   ```bash
   git clone https://github.com/OpenRA/OpenRA-Mod-SDK.git cameo
   cd cameo
   # Windows
   make.cmd all
   # Linux / macOS
   make all
   ```
   The template downloads the pinned engine, compiles the mod assembly, and produces a working launcher. If the build succeeds, you can already run `./launch-game.sh` and see the default SDK mod menu.

2. **Choose an identity and inherit from the common mod.** Edit `mod.yaml`:
   ```yaml
   Metadata:
       Title: Cameo
       Version: {VERSION}
       Author: Your Name

   RequiresMods:
       common: {APP_VERSION}
   ```
   Inherit from the common mod by including its rules, sequences, weapons, chrome, and audio files so you do not have to redeclare every template. See [Part 3.1 — Mod SDK and Project Structure](Part_03_Chapter_01_Mod_SDK.md) and [Part 3.2 — Mod SDK Bootstrap](Part_03_Chapter_02_SDK_Bootstrap.md) for the full SDK layout.

3. **Port or create an asset.** Obtain a sprite file `cameo/bits/recon.shp` either by extracting it from an original game archive with `./utility.sh ra --extract` or by creating a new PNG sequence and converting it with `--png-sheet` or `--convert-shp`. Also place `reconicon.shp` in the same folder. For the art pipeline, see [Part 4.1 — Renderer, Sheet, and Sprite](Part_04_Chapter_01_Renderer.md).

4. **Define a custom weapon.** Create `cameo/weapons/recon.yaml`:
   ```yaml
   ReconGun:
       ReloadDelay: 15
       Range: 4c0
       Report: gun11
       Projectile: InstantHit
       Warhead@1Dam: SpreadDamage
           Spread: 32
           Damage: 1500
           Versus:
               None: 100
               Wood: 50
               Light: 100
               Heavy: 25
               Concrete: 25
   ```
   Register it under `Weapons:` in `mod.yaml`:
   ```yaml
   Weapons:
       common|weapons/smallcaliber.yaml
       cameo|weapons/recon.yaml
   ```
   The weapon name (`ReconGun`) is what the actor's `Armament` trait will reference. For weapon syntax, see [Part 2.4 — Rulesets, Actors, and Weapons](Part_02_Chapter_04_Rules_Weapons.md).

5. **Define a custom unit.** In `cameo/rules/recon.yaml`, add a concrete actor that can be built, move, see, and fight:
   ```yaml
   RECON:
       Inherits: ^Vehicle
       Inherits@GAIN: ^GainsExperience
       Inherits@AUTOTARGET: ^AutoTargetGroundAssaultMove
       Buildable:
           Queue: Vehicle
           BuildPaletteOrder: 330
           Prerequisites: ~vehicles.allies, ~techlevel.low
       Valued:
           Cost: 600
       Tooltip:
           Name: Recon Buggy
       Health:
           HP: 15000
       Armor:
           Type: Light
       Mobile:
           Speed: 200
           Locomotor: wheeled
       RevealsShroud:
           Range: 7c0
       Armament:
           Weapon: ReconGun
           LocalOffset: 0,0,128
       AttackFrontal:
           FacingTolerance: 0
       WithFacingSpriteBody:
       RenderSprites:
           Image: recon
       Voiced:
           VoiceSet: VehicleVoice
   ```
   `Armament` points at the custom `ReconGun` weapon defined in the previous step. See [Part 2.1 — MiniYaml Parser](Part_02_Chapter_01_MiniYaml.md) for indentation and inheritance rules.

6. **Add the sequence and register the files.** In `cameo/sequences/recon.yaml`, reference the sprite:
   ```yaml
   recon:
       Defaults:
           Filename: recon.shp
       idle:
           Facings: 32
           UseClassicFacings: True
       icon:
           Filename: reconicon.shp
   ```
   Then list the new files in `cameo/mod.yaml`:
   ```yaml
   Rules:
       cameo|rules/recon.yaml
   Sequences:
       cameo|sequences/recon.yaml
   Weapons:
       cameo|weapons/recon.yaml
   ```
   The sequence key (`recon`) must match the `RenderSprites.Image` value.

7. **Add the unit to a build queue.** The `Buildable.Queue: Vehicle` line on the actor places it in the vehicle production queue. Make sure that queue is provided by a production building. If you are inheriting from an official mod, the `Vehicle` queue already exists. If you are building the queue from scratch, add a `Production` trait to a building such as:
   ```yaml
   VEHICLEFACTORY:
       Inherits: ^Building
       Production:
           Queue: Vehicle
       ProvidesPrerequisite:
           Prerequisite: vehicles.allies
   ```
   Then verify the `Buildable.Prerequisites` on `RECON` are satisfied by that building.

8. **Validate YAML.** Run the utility checks in order:
   ```bash
   ./utility.sh cameo --check-yaml
   ./utility.sh cameo --check-missing-sequences
   ./utility.sh cameo --check-missing-sprites
   ```
   The first command catches syntax errors, missing parents, and broken trait references; the others confirm that the actor references existing sequences and sprite files.

9. **Run locally.** Start the mod with:
   ```bash
   ./launch-game.sh Game.Mod=cameo
   ```
   Use the F12 debug menu to show actor bounds and terrain grid while testing the new unit.

10. **Debug issues.** If the unit does not appear, check `Logs/debug.log` for trait load errors, `Logs/graphics.log` for sprite problems, and `Logs/perf.log` for frame-time issues. If you later add a Lua mission, check `Logs/lua.log` for script errors.

11. **Package.** When the mod is ready, run the SDK packaging scripts (`make version` and platform-specific scripts) to produce Windows, Linux, and macOS installers.

This example shows the complete workflow from a blank mod project to a validated, playable, and packageable custom unit.

## Files

| File | Responsibility |
| :---- | :---- |
| `OpenRA.Utility` / `utility.sh` | Command-line tool for modding tasks (YAML checks, lint, asset conversion). |
| `OpenRA.Launcher` / `launch-game.sh` | Development launcher. |
| `mods/common/mod.yaml` | Reference common mod manifest. |
| `mods/*/mod.yaml` | Official mod manifests for reference. |
| `OpenRA.Game/Traits/TraitsInterfaces.cs` | Trait interface reference. |
| `OpenRA.Game/Graphics/SequenceSet.cs` | Sequence format reference. |
| `OpenRA.Mods.Common/UtilityCommands/*.cs` | Utility command implementations. |
| `OpenRA.Mods.Common/Traits/*.cs` | Common trait reference implementations. |
| `OpenRA.Mods.Common/Scripting/Global/*.cs` | Lua global reference. |
| `OpenRA.Mods.Common/Scripting/Properties/*.cs` | Lua property reference. |

![Architecture diagram](images/Part_10_Chapter_03_Port_And_Modding-architecture-diagram-showing-the-main-classes-interfaces-and-9161e6.svg)

## Architecture


### SDK setup from scratch

If you are starting a new mod, the recommended path is the OpenRA Mod SDK rather than forking the engine.

1. **Clone the SDK template.**
   ```bash
   git clone https://github.com/OpenRA/OpenRA-Mod-SDK.git my-mod
   cd my-mod
   ```
   The template contains a small working mod, packaging scripts, and a `mod.config` file.

2. **Choose an identity.** Edit `mod.yaml` and set:
   ```yaml
   Metadata:
       Title: My Mod
       Version: {VERSION}
       Author: Your Name
   ```
   The `Title` is what players see in the launcher and the server browser.

3. **Pin the engine.** In `mod.config`, set:
   ```bash
   ENGINE_VERSION=playtest-20240628
   ```
   The SDK download scripts fetch this exact engine tag and place it in a sibling directory. Pinning the version keeps your mod reproducible and makes it easy to bump the engine later by changing one value and running `make all` again.

4. **Inherit from the common mod.** Add to `mod.yaml`:
   ```yaml
   RequiresMods:
       common: {APP_VERSION}
   ```
   Also include the common mod's rules, sequences, weapons, and chrome files so you do not have to redeclare every trait. Most SDK mods start as a thin layer on top of `common` or one of the official mods.

5. **Build once.** Run `make all` (Linux/macOS) or `make.cmd all` (Windows). This downloads the pinned engine, compiles the mod assembly, and produces a working launcher. If the build succeeds, you can run `./launch-game.sh` and see the default mod menu.

6. **Create your own directories.** Add folders such as `my-mod/rules/`, `my-mod/sequences/`, `my-mod/audio/`, `my-mod/bits/`, and `my-mod/chrome/`. Register them in `mod.yaml` under `Rules:`, `Sequences:`, `ChromeLayout:`, etc.

### Developer workflow

A typical OpenRA development workflow looks like this:

<!-- DEV-NOTE [tooling]: Microsoft .NET SDK: https://dotnet.microsoft.com — required to build the OpenRA engine and mod projects. -->
1. **Set up the repository** — clone the engine, install the .NET SDK, run `make all`.
2. **Run the game** — use `launch-game.sh Game.Mod=ra` to launch a specific mod.
3. **Edit YAML** — modify rules, sequences, weapons, or chrome in a mod directory.
4. **Validate** — run `make test` or `./utility.sh <mod> --check-yaml`.
5. **Test in-game** — launch the mod and verify the changes.
6. **Debug** — use logging, debug overlays, and the in-game console.
7. **Package** — use `make version` and the platform packaging scripts.

### Modder workflow

A modder using the Mod SDK:

1. **Create a mod project** from the SDK template.
2. **Define `mod.yaml`** — inherit from an official mod or `common`.
3. **Add assets** — sprites, audio, maps, and tile sets.
4. **Write YAML rules** — actors, weapons, traits, missions.
5. **Add custom code** if needed — new C# traits in a mod assembly.
6. **Test locally** — run the mod launcher.
7. **Build releases** — use the SDK packaging scripts.

### Mod structure comparison

| Structure | What it is | Best for | Key files |
| :---- | :---- | :---- | :---- |
| **Official mod** (`mods/ra`, `mods/cnc`, etc.) | Lives inside the engine repository and is built with the engine. | Engine contributors who change both gameplay and engine code. | `mod.yaml`, `rules/`, `sequences/`, `audio/`, `chrome/`, `maps/` under `mods/<mod>/`. |
| **SDK mod** | Separate repository that references a pinned engine and the common mod. | Modders who want stable engine upgrades and a clean project. | `mod.yaml`, `mod.config`, `makefile`, packaging scripts, plus `rules/`, `sequences/`, etc. |
| **Common mod** (`mods/common`) | Shared traits, chrome, assets, and utilities used by official mods and many SDK mods. | Reusing existing UI, effects, or gameplay logic without copying it. | `mods/common/mod.yaml`, `mods/common/rules/`, `mods/common/sequences/`, `mods/common/chrome/`, `mods/common/audio/`. |

Most new mods should start as an SDK mod that depends on `common`. This gives you the smallest project footprint and the smoothest upgrade path when the engine releases new playtests.

![Data flow  code path diagram](images/Part_10_Chapter_03_Port_And_Modding-sequence-flow-diagram-tracing-the-execution-path-from-trigge-035864.svg)

## Data Flow / Code Path


### First custom unit walkthrough

This walkthrough assumes an SDK mod called `my-mod` that depends on the common mod.

1. **Create the actor definition.** In `my-mod/rules/vehicles.yaml`, add a concrete vehicle:
   ```yaml
   RECON:
       Inherits: ^Vehicle
       Inherits@GAINSEXPERIENCE: ^GainsExperience
       Inherits@AUTOTARGET: ^AutoTargetGroundAssaultMove
       Buildable:
           Queue: Vehicle
           BuildPaletteOrder: 330
           Prerequisites: ~vehicles.allies, ~techlevel.low
       Valued:
           Cost: 600
       Tooltip:
           Name: Recon Buggy
       Health:
           HP: 15000
       Armor:
           Type: Light
       Mobile:
           Speed: 160
           Locomotor: wheeled
       RevealsShroud:
           Range: 7c0
       Armament:
           Weapon: M1Carbine
           LocalOffset: 0,0,128
       AttackFrontal:
           FacingTolerance: 0
       WithFacingSpriteBody:
       AutoTarget:
           ScanRadius: 7
       RenderSprites:
           Image: recon
       Voiced:
           VoiceSet: VehicleVoice
   ```

2. **Add the sequence.** In `my-mod/sequences/vehicles.yaml`, reference the sprite file:
   ```yaml
   recon:
       Defaults:
           Filename: recon.shp
       idle:
           Facings: 32
           UseClassicFacings: True
       icon:
           Filename: reconicon.shp
   ```

3. **Place the asset.** Put `recon.shp` and `reconicon.shp` in `my-mod/bits/` or a VFS path that the mod loads. The sequence key (`recon`) must match the `RenderSprites.Image` value.

4. **Register the rules and sequence files.** In `my-mod/mod.yaml`, ensure the files are listed:
   ```yaml
   Rules:
       my-mod|rules/defaults.yaml
       my-mod|rules/vehicles.yaml
   Sequences:
       my-mod|sequences/vehicles.yaml
   ```

5. **Validate.** Run `./utility.sh my-mod --check-yaml` and `./utility.sh my-mod --check-missing-sequences`. The first command catches inheritance and syntax errors; the second confirms `RECON` references an existing sequence.

6. **Test.** Launch with `./launch-game.sh Game.Mod=my-mod`, build the unit from the vehicle queue, and verify it moves, fires, and displays its icon.

7. **Iterate.** If the unit does not appear, check `debug.log` for trait load errors and `graphics.log` for missing sprite references. If the build button is missing, check `Buildable.Queue` and `BuildPaletteOrder`.

### Before/After: Minimal vs. Full Actor Definition

This walkthrough adds a full, playable vehicle in one step. The comparison below shows the same actor as a bare skeleton and as the final, buildable unit.

**Before — minimal skeleton:**

```yaml
RECON:
    Inherits: ^Vehicle
    RenderSprites:
        Image: recon
    WithFacingSpriteBody:
```

**After — full walkthrough actor:**

```yaml
RECON:
    Inherits: ^Vehicle
    Inherits@GAINSEXPERIENCE: ^GainsExperience
    Inherits@AUTOTARGET: ^AutoTargetGroundAssaultMove
    Buildable:
        Queue: Vehicle
        BuildPaletteOrder: 330
        Prerequisites: ~vehicles.allies, ~techlevel.low
    Valued:
        Cost: 600
    Tooltip:
        Name: Recon Buggy
    Health:
        HP: 15000
    Armor:
        Type: Light
    Mobile:
        Speed: 160
        Locomotor: wheeled
    RevealsShroud:
        Range: 7c0
    Armament:
        Weapon: M1Carbine
        LocalOffset: 0,0,128
    AttackFrontal:
        FacingTolerance: 0
    WithFacingSpriteBody:
    AutoTarget:
        ScanRadius: 7
    RenderSprites:
        Image: recon
    Voiced:
        VoiceSet: VehicleVoice
```

The skeleton is only enough to render the actor, while the full version adds economy, production, combat, and voice behavior.

### Utility commands

Common utility commands:

- `--check-yaml` — loads the mod and reports YAML errors.
- `--check-explicit-interfaces` — verifies trait interface implementations.
- `--check-conditional-trait-interface-overrides` — validates conditional trait overrides.
- `--check-missing-sprites` — reports missing sprite references.
- `--check-missing-sequences` — reports missing sequence references.
- `--check-referenced-sequences` — validates sequence references.
- `--extract` — extracts assets from original game files.
- `--png-sheet` — creates a sprite sheet from PNG images.
- `--convert-shp` — converts images to SHP format.
- `--map` — creates or modifies maps.
- `--man-page` — generates a man page.

### Launch arguments

```bash
./launch-game.sh Game.Mod=ra
./launch-game.sh Game.Mod=ra Launch.Connect=127.0.0.1:1234
./launch-game.sh Game.Mod=ra Launch.World=mods/ra/maps/my-map.oramap
```

### Debug overlays

The in-game debug menu (F12) can show:

- Terrain grid.
- Pathfinding cost field.
- Actor bounds.
- Screen map partitions.
- Sync reports.

### Logging

OpenRA uses a log system with channels such as `debug`, `server`, `lua`, `audio`, `graphics`, `map`. Logs are written to `Logs/` in the engine directory.

![Configuration (yaml) diagram](images/Part_10_Chapter_03_Port_And_Modding-annotated-yaml-snippet-diagram-showing-the-key-fields-and-ho-6a1b98.svg)

## Configuration (YAML)


### Mod development manifest

A minimal mod.yaml for development:

```yaml
Metadata:
    Title: My Mod
    Version: {VERSION}

RequiresMods:
    common: {APP_VERSION}

FileSystem:
    LoadScreen: DefaultLoadScreen

MapFolders:
    my-mod|maps: Container

Rules:
    my-mod|rules/defaults.yaml
    my-mod|rules/vehicles.yaml

Assemblies:
    my-mod|OpenRA.Mods.MyMod.dll
```

### Development settings

`settings.yaml` can enable developer features:

```yaml
Debug:
    SyncCheckUnsyncedCode: true
    SyncCheckBotModuleCode: true
    DeveloperMode: true
```

## Interconnectivity

- **Depends on:** [Part 1.1 — ECS, Actors, and Traits](Part_01_Chapter_01_ECS.md) (ECS/trait lifecycle), [Part 2.1 — MiniYaml Parser](Part_02_Chapter_01_MiniYaml.md) (MiniYaml), [Part 2.4 — Rulesets, Actors, and Weapons](Part_02_Chapter_04_Rules_Weapons.md) (rulesets and weapons), [Part 3.1 — Mod SDK and Project Structure](Part_03_Chapter_01_Mod_SDK.md) (mod SDK), [Part 3.2 — Mod SDK Bootstrap](Part_03_Chapter_02_SDK_Bootstrap.md) (SDK bootstrap), [Part 3.3 — Build Pipeline and Packaging](Part_03_Chapter_03_Build_Packaging.md) (build), [Part 4.3 — Widgets and Chrome](Part_04_Chapter_03_Widgets.md) (chrome), [Part 6.1 — Lua Scripting and Eluant](Part_06_Chapter_01_Lua_Eluant.md) (Lua), [Part 9.3 — Sync Hashing and Determinism](Part_09_Chapter_03_Sync_Hashing.md) (sync debugging), [Part 10.1 — Official Mods](Part_10_Chapter_01_Official_Mods.md) (official mods), [Appendix B — Common YAML Patterns](../appendices/Appendix_B_Common_YAML_Patterns.md) (YAML patterns), [Appendix E — Practical Modding Recipes](../appendices/Appendix_E_Practical_Recipes.md) (practical recipes), [Appendix I — Actor Reference](../appendices/Appendix_I_Actor_Reference.md) (actor reference).
- **Used by:** All other chapters; this is the practical capstone.

![Algorithms diagram](images/Part_10_Chapter_03_Port_And_Modding-algorithm-diagram-or-pseudocode-flowchart-for-the-non-trivia-5983ed.svg)

## Algorithms


### Asset porting

1. Identify the original asset format (SHP, TMP, MIX, AUD, VQA, etc.).
2. Use the content installer or the `--extract` utility command to obtain the file.
3. Place the file in the mod's VFS path.
4. Reference the file in sequences, rules, or audio YAML.
5. Test in-game and adjust offsets, palettes, or sequence frames.

### Trait creation checklist

1. Create a class inheriting `TraitInfo` and the trait class.
2. Implement the necessary interfaces.
3. Add `[Desc]` attributes for documentation.
4. Register the trait in the actor's YAML.
5. Run `--check-yaml` and `--check-explicit-interfaces`.
6. Test sync safety if the trait changes state.

### Sequence creation checklist

1. Create a sprite file or reference existing assets.
2. Add a sequence entry in YAML with `Start`, `Length`, `Facings`, etc.
3. Reference the sequence from an actor's `RenderSprites` or `WithSpriteBody` trait.
4. Run `--check-missing-sequences`.
5. Verify in-game animation.

### Lua script workflow

1. Add the script file to `World: LuaScript: Scripts` in the map rules.
2. Implement `Tick()` and event callbacks.
3. Use `print()` for debugging; check `lua.log`.
4. Test the mission in a skirmish or mission load.
5. Watch for fatal Lua errors that disable the script context.

### Debugging desyncs

1. Enable `EnableSyncReports` in the lobby.
2. Reproduce the desync.
3. Compare sync reports between clients.
4. Identify the first diverged trait/field.
5. Check for unsynced code, random sources, or floating-point math.

### Performance profiling

1. Use the in-game perf graph (if enabled).
2. Check `perf.log` for frame timings.
3. Use `PerfSample` in code to measure custom sections.
4. Profile slow paths: pathfinding, rendering, bot modules, Lua scripts.

![Extension points diagram](images/Part_10_Chapter_03_Port_And_Modding-extension-hook-diagram-showing-the-interface-s-to-implement-b4a27b.svg)

## Extension Points


### Create a new utility command

Implement `IUtilityCommand` in a mod assembly. Run it with `./utility.sh <mod> --command-name`. Utility commands are powerful for batch processing and CI.

### Add custom debug overlays

Implement `IRenderAnnotations` or subscribe to the debug visualization trait to draw custom debug information.

### Add custom settings

Add entries to `settings.yaml` and read them via `Game.Settings`. Use the settings UI to expose user-configurable options.

### Add custom mod content installer

Create `mods/<mod>-content/` with `downloads.yaml` and `installer.yaml`. Define the required files and extraction steps.

### Add custom map generator

Create a world trait implementing `IMapGenerator` or extend the existing random map generator. Register it in the mod's `map-generators.yaml`.

### Next steps

After the basic workflow is comfortable, follow these chapters for deeper topics:
- **Custom traits:** [Part 1.1 — ECS, Actors, and Traits](Part_01_Chapter_01_ECS.md) for the trait lifecycle, [Part 2.4 — Rulesets, Actors, and Weapons](Part_02_Chapter_04_Rules_Weapons.md) for ruleset/weapon context, and [Appendix D — Engine Conventions and Style](../appendices/Appendix_D_Engine_Conventions.md) for engine conventions.
- **Custom weapons and units:** [Part 2.4 — Rulesets, Actors, and Weapons](Part_02_Chapter_04_Rules_Weapons.md), [Appendix E — Practical Modding Recipes](../appendices/Appendix_E_Practical_Recipes.md).
- **Custom UI/chrome:** [Part 4.3 — Widgets and Chrome](Part_04_Chapter_03_Widgets.md).
- **Scripted missions:** [Part 6.1 — Lua Scripting and Eluant](Part_06_Chapter_01_Lua_Eluant.md) and [Part 6.2 — ScriptContext Lifecycle and Bindings](Part_06_Chapter_02_ScriptContext.md).
- **Packaging and release:** [Part 3.3 — Build Pipeline and Packaging](Part_03_Chapter_03_Build_Packaging.md).

![Common pitfalls checklist diagram](images/Part_10_Chapter_03_Port_And_Modding-checklist-infographic-style-diagram-summarizing-the-top-pitf-fb069e.svg)

## Common Pitfalls Checklist


Use this checklist before committing a change or sharing a build, especially for a new mod project:

- [ ] The project is an SDK mod with the engine version pinned in `mod.config`.
- [ ] The mod ID in `mod.yaml` and the directory name match the package name and `Game.Mod=` argument.
- [ ] The `RequiresMods` version in `mod.yaml` matches the engine version.
- [ ] The actor inherits a valid template (`^Vehicle`, `^Infantry`, `^Building`, etc.).
- [ ] The sequence key matches `RenderSprites.Image` or the actor ID when `RenderSprites` is omitted.
- [ ] For buildings, `Footprint` matches `Building.Dimensions` and every cell is passable for the exit.
- [ ] Every new YAML file is listed in the correct manifest section (`Rules`, `Sequences`, `Weapons`, `Audio`, `ChromeLayout`, etc.) and listed after inherited files if it overrides them.
- [ ] `BuildPaletteOrder` values are unique within the same queue.
- [ ] The `Buildable.Queue` on the actor matches a `Production` queue on a production building.
- [ ] Custom trait assemblies are listed in `mod.yaml` `Assemblies:` and built against the same engine version.
- [ ] New C# traits that affect gameplay use `[Sync]` or `[VerifySync]` on relevant fields and use `world.SharedRandom` for randomness.
- [ ] No unsynced code (UI, AI, or render-only logic) changes simulation state.
- [ ] Asset paths use the VFS syntax (`my-mod|path/to/file`) and lowercase names for Linux compatibility.
- [ ] `--check-yaml` passes after every non-trivial YAML change.
- [ ] `--check-missing-sequences` and `--check-missing-sprites` pass after adding new artwork.
- [ ] Replays are re-tested after gameplay rule changes because replays require the same ruleset.

### Guardrails for new mod projects

- **Do not edit generated files:** files under `bin/` or `obj/` are generated. Edit source files and rebuild.
- **YAML indentation:** MiniYaml is sensitive to indentation. Use tabs or spaces consistently.
- **Trait order:** `NotBefore` and `Requires` matter. A trait that reads another trait's state must be initialized after it.
- **Sync safety:** any state that affects gameplay must be marked `[Sync]` or `[VerifySync]`. Client-only state must not.
- **Random sources:** use `world.SharedRandom` for simulation. `world.LocalRandom` is for UI/AI only.
- **Asset paths:** use the VFS path syntax (`mod|path/to/file`). Do not hardcode absolute paths.
- **Case sensitivity:** Windows and Linux handle filename case differently. Use lowercase paths consistently.
- **Mod version:** keep `RequiresMods` versions synchronized with the engine version.
- **Testing:** run `--check-yaml` after every non-trivial YAML change. It catches many errors before launch.
- **Replay compatibility:** changing gameplay rules can break old replays. Replays encode only orders; they require the same ruleset.

![How to debug a broken actor definition diagram](images/Part_10_Chapter_03_Port_And_Modding-asset-pipeline-diagram-external-tool-gimp-aseprite-audacity-d68ae7.svg)

## How to debug a broken actor definition


When an actor fails to load or does not appear in-game, follow this workflow in order.

1. **Validate the YAML.**
   ```bash
   ./utility.sh <mod> --check-yaml
   ```
   This catches syntax errors, inheritance problems, missing parents, and trait references that do not exist. If `--check-yaml` fails, fix the first reported error and run it again; later errors often disappear once the first one is resolved.

2. **Confirm the actor is registered.**
   - The actor's YAML file must be listed under `Rules:` in `mod.yaml`.
   - The actor ID must be unique and not shadowed by another file loaded later in the manifest.
   - The actor must inherit a valid template (for example `^Vehicle`, `^Infantry`, or `^Building`).

3. **Confirm the trait exists and is valid in this context.**
   - Search the [OpenRA traits reference](https://docs.openra.net/en/release/traits/) for the trait name.
   - Check the `OpenRA.Mods.Common/Traits/` directory for the source `.cs` file.
   - See [Appendix I — Actor Reference](../appendices/Appendix_I_Actor_Reference.md) for actor/trait combinations.

4. **Check sequence and sprite references.**
   - Run `./utility.sh <mod> --check-missing-sequences`.
   - Run `./utility.sh <mod> --check-missing-sprites`.
   - Make sure the sequence key matches `RenderSprites.Image`.
   - Verify the asset file exists in the mod VFS path and that the filename case matches exactly.

5. **Read the logs.**
   - `Logs/debug.log` — trait load errors and actor instantiation failures.
   - `Logs/graphics.log` — missing sprites, palette errors, and sequence problems.
   - `Logs/perf.log` — performance warnings.
   - `Logs/lua.log` — Lua errors for scripted maps.

6. **Use the in-game debug overlays.**
   - Press F12 and enable actor bounds, terrain grid, and pathfinding overlays to verify the unit appears in the world.

7. **Isolate the change.**
   - Temporarily remove half the actor's traits to find which trait causes the error.
   - Compare your actor against a known-good example from the same mod or from `mods/ra/rules/vehicles.yaml`.

For more details, see [Appendix C — Debugging](../appendices/Appendix_C_Debugging.md) and [Appendix F — Testing](../appendices/Appendix_F_Testing.md).

## How to find the trait you need


OpenRA has dozens of common traits. The fastest way to locate one is to work backward from the behavior you want.

1. **Check the official documentation.** The [OpenRA traits reference](https://docs.openra.net/en/release/traits/) lists every trait with a one-line description and the fields it exposes. Use the browser search to find keywords like `Buildable`, `Armament`, `Mobile`, `RenderSprites`, or `RevealsShroud`.

2. **Search the official mods.** Most common behaviors are already used in `mods/ra`, `mods/cnc`, `mods/d2k`, or `mods/common`. Search the rules YAML for the trait name and copy the related trait block. If you want a UI trait, look at `mods/common/chrome/` and the rules for `Player` or `World`.

3. **Read the trait source.** The `OpenRA.Mods.Common/Traits/` directory contains the authoritative implementation. Open the matching `.cs` file to see the `[Desc("...")]` documentation, which interfaces the trait implements, and which fields are required.

4. **Use the [Appendix I -- Actor Reference](../appendices/Appendix_I_Actor_Reference.md) actor reference.** [Appendix I — Actor Reference](../appendices/Appendix_I_Actor_Reference.md) provides a generated list of actors and the traits they use across the official mods.

5. **Test the trait.** When you find a candidate, add it to the actor YAML and run `./utility.sh <mod> --check-yaml` to confirm it is valid in that context.

See also [Part 1.1 — ECS, Actors, and Traits](Part_01_Chapter_01_ECS.md) for the trait lifecycle and [Part 2.4 — Rulesets, Actors, and Weapons](Part_02_Chapter_04_Rules_Weapons.md) for how rules are loaded.

## Asset Creation Pipeline


This section describes the journey from raw source assets to playable mod content, and the recommended workflow for adding a new unit. It focuses on the four asset classes that most mods touch: art, audio, maps, and YAML. For copy-paste examples, see [Appendix E — Practical Modding Recipes](../appendices/Appendix_E_Practical_Recipes.md).

### IDE setup and asset tooling

Before you create new assets, make sure you have the following tools available:

- **.NET SDK:** Required to build the OpenRA engine and mod projects. Download it from https://dotnet.microsoft.com.
- **Code editor:** VS Code, Visual Studio, or JetBrains Rider with C# support for editing engine and mod C# code.
- **Sprite art:** [GIMP](https://www.gimp.org) or [Aseprite](https://www.aseprite.org) for creating and editing indexed sprites.
- **Audio samples:** [Audacity](https://www.audacityteam.org) for recording and editing WAV/OGG samples.
- **3D/pre-rendered art:** [Blender](https://www.blender.org) for rendering frames or producing source artwork.
- **OpenRA Utility:** The command-line tool for converting and linting assets. See the [Utility documentation](https://docs.openra.net/en/release/utility/) for available commands.

### Asset-creation pipeline overview

A new asset usually flows through four stages:

<!-- DEV-NOTE [tooling]: GIMP: https://www.gimp.org — raster image editing for indexed sprites and palette work. -->
1. **Create the source file** in an external tool (GIMP, Photoshop, Aseprite, Audacity, etc.).
2. **Convert it to an engine-friendly format** if necessary (SHP, WAV, etc.).
3. **Describe it in YAML** so the engine knows how to load and use it.
4. **Register the YAML file in `mod.yaml`** so it is loaded when the mod starts.

The sections below show how each asset class fits into that flow.

#### Art: sprites, SHP files, and sequences

OpenRA draws most world objects as 2D sprites. The typical art pipeline is:

- Draw frames as a PNG strip, sprite sheet, or individual PNGs, or produce a Westwood-style SHP file with indexed palette colors.
- Place the compiled file in the mod's VFS path, such as `my-mod/bits/`.
- Add a sequence entry in a `sequences/*.yaml` file:
  ```yaml
  myunit:
      Defaults:
          Filename: myunit.shp
      idle:
          Start: 0
          Length: 1
          Facings: 32
      icon:
          Filename: myuniticon.shp
  ```
- Reference the sequence key from the actor's render traits, for example `RenderSprites: Image: myunit`. The sequence key must match the image name.

See [Part 4.1 — Renderer, Sheet, and Sprite](Part_04_Chapter_01_Renderer.md) for how `SequenceSet`, `SpriteCache`, and `SheetBuilder` turn sequence definitions into GPU-drawn sprites.

### Sprite and palette conventions

Beyond the basic file-and-sequence setup, the art pipeline has a few conventions that control how colors are interpreted at runtime. Getting them right keeps units from rendering as solid blocks or the wrong player color.

#### Indexed vs. true-color sprites

OpenRA traditionally uses 8-bit indexed PNGs or SHPs. Each pixel stores an index (0-255) into a palette, rather than a full RGB color. The engine can also load true-color PNGs (RGB/RGBA), but those bypass the palette system entirely and are drawn as-is. For most mod art, especially when reusing Westwood-style assets or wanting player color remapping, 8-bit indexed is the expected format.

Index 0 is conventionally transparent in most mods, although the exact transparent indices depend on the palette and sequence settings. When authoring indexed art, reserve index 0 for fully transparent areas unless your mod defines a different convention.

#### Palette files

Palettes live in the mod VFS as `.pal` files (VGA 768-byte palette format). Common locations include `mods/<mod>/bits/palette.pal` or tileset-specific palettes such as `mods/ra/bits/temperat.pal`. They are declared in `mod.yaml` under the `Rules` section as world traits, typically in a `rules/palettes.yaml` file that is then listed under `Rules:` in the manifest.

A typical `rules/palettes.yaml` entry looks like:

```yaml
^Palettes:
    PaletteFromFile@player:
        Name: player
        Filename: temperat.pal
        ShadowIndex: 4
```

`PaletteFromFile` (in `OpenRA.Mods.Common/Traits/Palettes/PaletteFromFile.cs`) reads the 256-entry palette, applies the configured `TransparentIndex` and `ShadowIndex` overrides, and registers the result with `WorldRenderer` under `Name`. The palette named `player` is then used as the base for the player-color remapped palette.

#### Player-remappable colors

Many mods want faction-colored areas on units (red for Soviet, blue for Allies, etc.). The convention is to reserve a specific index range in the source palette for these remappable pixels. The artist draws the unit's base colors in the normal palette entries, then places the faction-colored pixels in the reserved range. Common ranges are the last 16 entries (240-255), the range 80-95 in the Red Alert mod, or 16-31 in Tiberian Sun.

At runtime, the engine creates a per-player copy of the palette using `PlayerColorPalette` (in `OpenRA.Mods.Common/Traits/Palettes/PlayerColorPalette.cs`). This builds an `IPaletteRemap` via `OpenRA.Game/Graphics/PlayerColorRemap.cs`, which replaces each remappable index with a color derived from the player's chosen color while preserving the original brightness. The mod author must ensure the artist places player-remappable pixels at the exact indices listed in `RemapIndex`; otherwise the colors will not change per player.

Example from `mods/ra/rules/palettes.yaml`:

```yaml
PlayerColorPalette:
    BasePalette: player
    RemapIndex: 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95
```

Any pixel in the source art that uses index 80-95 will render in the owning player's color.

#### Shadow rendering

Shadows are also drawn via palette indices. A palette file can mark one or more indices as shadow entries (`ShadowIndex`), which causes the engine to draw them with partial transparency. In `mods/ra` the default shadow index is `4`, while Tiberian Sun often uses `1`. The actual transparency value comes from the palette loader, which writes a fixed alpha for shadow indices.

In sequences, artists can split a frame into a body and a shadow by using `ShadowStart` and `ShadowLength`, or use a separate palette via the actor's `Palette`/`PlayerPalette` traits. If a sprite is drawn with the `player` palette, the shadow pixels use the shadow index configured on that palette. For a non-shadow draw, use a palette variant with the shadow index also listed as `TransparentIndex` (for example `player-noshadow` in `mods/ra/rules/palettes.yaml`).

#### SHP conversion and frame layout

Legacy Westwood SHP files are 8-bit indexed and can be produced from PNG source frames. The `--convert-shp` (or `--shp`) utility command, implemented in `OpenRA.Mods.Cnc/UtilityCommands/ConvertPngToShpCommand.cs`, takes a list of same-size indexed PNGs and writes a single `ShpTDSprite` file. The `--png-sheet`/`--png-sheet-import` commands in `OpenRA.Mods.Common/UtilityCommands` go the other direction, exporting engine sheets back to PNGs for editing.

For modern PNG sequences, the engine supports both horizontal strips and sheets. A strip is a single PNG whose frames are laid out left-to-right (and top-to-bottom if needed). A sheet is a multi-frame PNG with embedded metadata defining the per-frame rectangles. In either case, the sequence YAML maps the continuous frame list to named sequences by `Start`, `Length`, and `Facings`:

```yaml
myunit:
    Defaults:
        Filename: myunit.png
    idle:
        Start: 0
        Length: 1
        Facings: 32
    run:
        Start: 32
        Length: 6
        Facings: 8
    icon:
        Filename: myuniticon.png
```

#### Complete example

Putting the pieces together, a Red Alert style vehicle with player-remappable colors and a palette shadow looks like this.

`rules/palettes.yaml` (registered under `Rules:` in `mod.yaml`):

```yaml
^Palettes:
    PaletteFromFile@player:
        Name: player
        Filename: myunit.pal
        ShadowIndex: 4
    PlayerColorPalette:
        BasePalette: player
        RemapIndex: 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95
```

`sequences/vehicles.yaml`:

```yaml
myunit:
    Defaults:
        Filename: myunit.shp
        Palette: player
    idle:
        Facings: 32
        UseClassicFacings: True
    icon:
        Filename: myuniticon.shp
```

`rules/vehicles.yaml`:

```yaml
MYUNIT:
    Inherits: ^Vehicle
    RenderSprites:
        Image: myunit
        PlayerPalette: player
    WithFacingSpriteBody:
```

For this to work, the source `myunit.shp` must be 8-bit indexed using `myunit.pal`, player-remappable pixels must use indices 80-95, and shadow pixels must use index 4. The `Palette: player` sequence default plus the `PlayerPalette: player` render trait tells the engine to apply the per-player remapped palette.

For a complete copy-paste walkthrough of adding a vehicle, see Recipe 2 in `Appendix_E_Practical_Recipes.md`.

#### Audio: WAV/AUD and sound manifests

OpenRA plays three categories of sound: unit voices, notifications, and music.

- Prepare samples as WAV, OGG, or MP3. Classic Westwood AUD/VOC files can be used directly when the mod loader is registered.
- Place the files in `my-mod/audio/` or another loaded VFS path.
- Define voice sets in `audio/voices.yaml`:
  ```yaml
  MyUnitVoice:
      Inherits: VehicleVoice
      Voices:
          Select: mysel1, mysel2
          Move: mymov1, mymov2
          Attack: myatk1
  ```
- Define notifications in `audio/notifications.yaml`:
  ```yaml
  MyNotification:
      Notifications: mynote1
      InterruptType: Overlap
  ```
- Define music tracks in `audio/music.yaml`:
  ```yaml
  Music:
      mytrack:
          Title: My Track
          Filename: mytrack
          Extension: wav
  ```
- Register the voice, notification, and music files under `Voices:`, `Notifications:`, and `Music:` in `mod.yaml`.

See [Part 5.1 — Audio Architecture](Part_05_Chapter_01_Audio_Architecture.md) for the `Sound` class, loader order, source pooling, and player filtering.

#### Maps: editor, export/import, and Lua

Maps are self-contained packages that include terrain, actors, rules overrides, and scripts.

- Build the map in the in-game map editor.
- Save the map as an `.oramap` file. The package contains `map.yaml`, `map.bin`, `map.png`, and optional Lua scripts.
- Export or import maps with the editor's file dialogs, or import legacy maps with the `--map-import` utility command.
- Add Lua mission logic under the map's `Rules` section:
  ```yaml
  Rules:
      World:
          LuaScript:
              Scripts: my-mission.lua
  ```

See [Part 7.1 — Map Generation Pipeline Overview](Part_07_Chapter_01_Pipeline.md) for the generation pipeline and how `MapGenerationArgs` is turned into a playable `Map`.

#### YAML: rules, weapons, chrome, sequences, and tilesets

YAML is the glue that ties assets to behavior.

- `rules/` define actors and their traits.
- `weapons/` define weapons, projectiles, and warheads.
- `chrome/` defines UI layouts.
- `sequences/` define sprite animation.
- `tilesets/` define terrain tile sets.
- `mod.yaml` registers all of these under the matching manifest sections:
  ```yaml
  Rules:
      my-mod|rules/defaults.yaml
      my-mod|rules/vehicles.yaml
  Weapons:
      my-mod|weapons/smallcaliber.yaml
  Sequences:
      my-mod|sequences/vehicles.yaml
  ChromeLayout:
      my-mod|chrome/layout.yaml
  TileSets:
      my-mod|tilesets/temperat.yaml
  ```

### Recommended workflow for adding a new unit

A typical workflow for a new unit from concept to package is:

1. **Concept** — decide the unit's role, size, faction, and whether it needs a new sprite or can reuse existing art.
2. **Art** — draw or extract the sprite frames and icon. Place the compiled SHP or PNG in `my-mod/bits/`.
3. **Sequences** — add a sequence entry in `my-mod/sequences/*.yaml` that references the sprite file, facings, and icon.
4. **Rules** — add the actor in `my-mod/rules/*.yaml` with traits such as `Buildable`, `Valued`, `Mobile`, `Armament`, `RenderSprites`, and `Voiced`.
5. **Audio** — add voice and weapon sounds if needed, and register them in `audio/voices.yaml` and `audio/notifications.yaml`.
6. **Register** — list the new YAML files and asset paths in `mod.yaml`.
7. **Test** — run `./utility.sh my-mod --check-yaml` and `./utility.sh my-mod --check-missing-sequences`, then launch the mod and build the unit.
8. **Package** — run the SDK packaging scripts (`make version` and platform scripts) to produce release installers.

### Useful modding utility commands

| Command | What it validates or produces |
| :---- | :---- |
| `--check-yaml` | Loads the mod and reports YAML syntax errors, inheritance problems, and broken trait references. |
| `--check-sequences` | Validates sequence definitions. |
| `--check-missing-sequences` | Reports sequence references that do not resolve to a loaded sequence. |
| `--check-missing-sprites` | Reports sprite filenames that cannot be found in the mod file system. |
| `--extract` | Extracts (exports) art, audio, or video assets from original game MIX archives. |
| `--map-import` | Imports legacy map files into the OpenRA `.oramap` format. |
| `--png-sheet` | Creates a sprite sheet from individual PNG frames. |
| `--convert-shp` | Converts PNG images into Westwood SHP format. |

These commands can be chained in CI so that every commit is validated before it is merged.

### File naming and packaging conventions

- `mod.yaml` is the mod manifest. Every rules, sequence, weapon, chrome, audio, and tileset file must be listed here.
- `mod.config` in the SDK controls the pinned engine version, assembly name, and packaging settings.
- Asset folders:
  - `my-mod/bits/` — small loose sprites, icons, and cursors.
  - `my-mod/audio/` — voice, notification, and music files.
  - `my-mod/sequences/` — sequence YAML.
  - `my-mod/rules/` — actor and weapon YAML.
  - `my-mod/maps/` — map packages.
- Use lowercase names and forward slashes for cross-platform compatibility. Windows is case-insensitive; Linux players will fail to load `MyUnit.shp` if the YAML references `myunit.shp`.
- The Mod SDK packages these folders into platform installers. The packaging scripts read `mod.config` to determine the engine version, mod ID, and output names.

### Common asset-creation pitfalls

- **Wrong sequence frame count.** If `Length` or `Facings` exceeds the number of frames in the sprite file, the sequence will fail to load or the animation will glitch. Use `--check-sequences` and `--check-missing-sprites` to catch this early.
- **Missing palette.** Indexed SHP sprites need a palette registered in `mod.yaml` under `Palettes:` or `SpriteSequenceFormat`. If the palette is missing, the unit renders as a solid color or invisible.
- **Unregistered asset file.** A new SHP, WAV, or YAML file is ignored until it is listed in `mod.yaml` or placed in a loaded package such as `bits/`.
- **Audio sample rate mismatch.** WAV files should be 22050 Hz or 44100 Hz mono/stereo. Unexpected rates can cause pitch shifts or load failures depending on the loader.
- **Path case mismatch on Linux.** A sequence that references `MyUnit.shp` will work on Windows but fail on Linux if the file is named `myunit.shp`. Use lowercase everywhere.
- **Sequence key mismatch.** The sequence key in `sequences/*.yaml` must match the `RenderSprites.Image` value on the actor.

### Cross-references

- [Part 2.1 — MiniYaml Parser](Part_02_Chapter_01_MiniYaml.md) — MiniYaml syntax, inheritance, and overrides.
- [Part 2.4 — Rulesets, Actors, and Weapons](Part_02_Chapter_04_Rules_Weapons.md) — ruleset loading, actor definitions, and weapon definitions.
- [Part 3.1 — Mod SDK and Project Structure](Part_03_Chapter_01_Mod_SDK.md) — SDK layout, `mod.yaml`, and the dependency model.
- [Part 3.2 — Mod SDK Bootstrap](Part_03_Chapter_02_SDK_Bootstrap.md) — engine download, bootstrap scripts, and first build.
- [Part 4.1 — Renderer, Sheet, and Sprite](Part_04_Chapter_01_Renderer.md) — sprite sheets, palettes, `SequenceSet`, and the rendering path.
- [Part 4.3 — Widgets and Chrome](Part_04_Chapter_03_Widgets.md) — UI layout, chrome YAML, and widget trees.
- [Part 5.1 — Audio Architecture](Part_05_Chapter_01_Audio_Architecture.md) — sound loaders, voices, notifications, and music.
- [Part 6.1 — Lua Scripting and Eluant](Part_06_Chapter_01_Lua_Eluant.md) — mission scripting and the Lua API.
- [Part 7.1 — Map Generation Pipeline Overview](Part_07_Chapter_01_Pipeline.md) — map generation, editor integration, and `MapGenerationArgs`.
- [Appendix B — Common YAML Patterns](../appendices/Appendix_B_Common_YAML_Patterns.md) — reusable patterns for inheritance, overrides, and conditional logic.
- [Appendix E — Practical Modding Recipes](../appendices/Appendix_E_Practical_Recipes.md) — copy-paste recipes for adding units, weapons, buildings, and support powers.
- [Appendix H — Asset Visual Reference](../appendices/Appendix_H_Asset_Visual_Reference.md) — categorical lookup of the file formats, YAML definitions, and engine classes for every asset type covered in this workflow.
- [Appendix G — Advanced Modding Walkthroughs](../appendices/Appendix_G_Advanced_Modding_Walkthroughs.md) — complete walkthroughs for Chrome UI, Lua missions, custom AI, crates, resources, shroud, capture, cloak, and voxels.
- [Appendix I — Actor Reference](../appendices/Appendix_I_Actor_Reference.md) — generated reference of actors and their traits across the official mods.

## References

- `utility.sh` — utility command launcher.
- `launch-game.sh` — development launcher.
- `OpenRA.Game/IUtilityCommand.cs` — utility command interface.
- `OpenRA.Mods.Common/UtilityCommands/*.cs` — utility command implementations.
- `OpenRA.Game/Traits/TraitsInterfaces.cs` — trait interfaces.
- `OpenRA.Mods.Common/Traits/*.cs` — reference trait implementations.
- `OpenRA.Game/Settings.cs` — settings definitions.
- `mods/common/mod.yaml` — common mod manifest.
- Official mod directories for reference rules and sequences.


### External resources

- [OpenRA traits reference](https://docs.openra.net/en/release/traits/)
- [OpenRA weapons reference](https://docs.openra.net/en/release/weapons/)
- [OpenRA sprite sequences](https://docs.openra.net/en/release/sprite-sequences/)
- [OpenRA Lua API](https://docs.openra.net/en/release/lua/)

## Summary

This chapter provides practical guidance for developers and modders who want to extend OpenRA, port assets from the original games, or create new [mods](../appendices/Appendix_A_Glossary.md).

After reading this chapter, you should be able to:

- Set up a new mod project using the OpenRA [Mod SDK](../appendices/Appendix_A_Glossary.md) template.
- Use the most common [Utility Commands](../appendices/Appendix_A_Glossary.md) (`--check-yaml`, `--check-missing-sprites`, `--extract`, `--map`, etc.).
- Port original-game assets through the content installer or the `--extract` command.
- Create a custom C# [trait](../appendices/Appendix_A_Glossary.md) and register it in a mod assembly.
- Add a new [sequence](../appendices/Appendix_A_Glossary.md) and reference it from an actor's render traits.
- Debug desyncs, read log files, and use the in-game debug overlays.
- Package a mod for release using the SDK packaging scripts.
- Compare the official mod, SDK mod, and common mod project structures and choose the right starting point.
- Avoid the most common modding mistakes by following the pitfalls checklist.

If any of the concepts above feel unclear, review the relevant section before continuing. For source files and further reading, see the References section above.

## What to read next

- If you are starting a new mod project, read [Part 3.1 — Mod SDK and Project Structure](Part_03_Chapter_01_Mod_SDK.md) next to learn the manifest, package layout, and dependency model.
- Now that you have seen the end-to-end workflow for adding a unit, read [Appendix E — Practical Modding Recipes](../appendices/Appendix_E_Practical_Recipes.md) for copy-paste recipes for units, weapons, buildings, and support powers.
- If you need to diagnose a broken actor or trait, read [Appendix C — Debugging](../appendices/Appendix_C_Debugging.md) and [Appendix I — Actor Reference](../appendices/Appendix_I_Actor_Reference.md).
- If you plan to write custom C# traits, read [Appendix D — Engine Conventions and Style](../appendices/Appendix_D_Engine_Conventions.md) for sync-safety rules and coding conventions.