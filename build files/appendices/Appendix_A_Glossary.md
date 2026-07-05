# Appendix A — Glossary

This glossary defines the terms used throughout the OpenRA engine and this manual. Terms are grouped by domain for easier navigation.

## Core Engine

| Term | Definition | See also |
| :---- | :---- | :---- |
| **Actor** | An object in the game world. It is an empty container that gains behavior from attached traits. Actors have an `ActorID`, an owner, a position, and a ruleset definition (`ActorInfo`). | [Part 1.1 — Entity-Component-System (ECS) and Actor Lifecycle](../chapters/Part_01_Chapter_01_ECS.md), [Part 2.4 — Rulesets, Actors, and Weapons](../chapters/Part_02_Chapter_04_Rules_Weapons.md) |
| **Trait** | A C# object attached to an actor that implements one or more engine interfaces. Traits hold runtime state and respond to tick, order, render, and other events. | [Part 1.1 — Entity-Component-System (ECS) and Actor Lifecycle](../chapters/Part_01_Chapter_01_ECS.md) |
| **TraitInfo** | The immutable, YAML-loaded configuration for a trait. One `TraitInfo` instance exists per actor definition; many actors may share it. | [Part 1.1 — Entity-Component-System (ECS) and Actor Lifecycle](../chapters/Part_01_Chapter_01_ECS.md), [Part 2.4 — Rulesets, Actors, and Weapons](../chapters/Part_02_Chapter_04_Rules_Weapons.md) |
| **ActorInfo** | The rules-level definition of an actor: a name plus a collection of `TraitInfo` objects. | [Part 1.1 — Entity-Component-System (ECS) and Actor Lifecycle](../chapters/Part_01_Chapter_01_ECS.md), [Part 2.4 — Rulesets, Actors, and Weapons](../chapters/Part_02_Chapter_04_Rules_Weapons.md) |
| **World** | The root simulation object. It owns all actors, the map, trait dictionaries, effects, order generation, and the game loop. | [Part 1.3 — World, OrderManager, and Orders](../chapters/Part_01_Chapter_03_World_Orders.md) |
| **WorldRenderer** | The object that renders the simulation world each frame. It collects renderables, sorts them, and drives the rendering pipeline. | [Part 4.2 — WorldRenderer](../chapters/Part_04_Chapter_02_WorldRenderer.md) |
| **Ruleset** | The immutable set of actor definitions, weapons, voices, notifications, music, and terrain info loaded for a game session. | [Part 2.2 — Manifest, ModData, Ruleset, and RulesetCache](../chapters/Part_02_Chapter_02_Manifest.md) |
| **Activity** | A queued task for an actor. Activities are stacked; the topmost activity is ticked each frame. | [Part 1.2 — Activities and the Game Loop](../chapters/Part_01_Chapter_02_Activities.md) |
| **Order** | The data object that carries a player or bot command from the unsynced world into the deterministic simulation. | [Part 1.3 — World, OrderManager, and Orders](../chapters/Part_01_Chapter_03_World_Orders.md), [Part 9.1 — OrderManager and Lockstep Foundation](../chapters/Part_09_Chapter_01_OrderManager.md) |
| **Target** | A struct that can represent an actor, a frozen actor, a cell, or a world position. Used by orders and weapon targeting. | [Part 1.6 — Combat and Damage Resolution](../chapters/Part_01_Chapter_06_Combat_Damage.md) |
| **Sync Hash** | A deterministic hash of all simulation state that must match across all clients. Used to detect desyncs. | [Part 9.3 — Sync Hashing and Determinism](../chapters/Part_09_Chapter_03_Sync_Hashing.md) |
| **Desync** | A condition where two clients have different simulation states. The game cannot continue reliably after a desync. | [Part 9.3 — Sync Hashing and Determinism](../chapters/Part_09_Chapter_03_Sync_Hashing.md) |

## Data and Configuration

| Term | Definition | See also |
| :---- | :---- | :---- |
| **MiniYaml** | OpenRA's simplified YAML-like configuration format used for rules, weapons, sequences, UI, and other data. | [Part 2.1 — MiniYaml Parser and Inheritance](../chapters/Part_02_Chapter_01_MiniYaml.md) |
| **Manifest** | The `mod.yaml` file that declares a mod's metadata, file system, rules, assets, and loader configuration. | [Part 2.2 — Manifest, ModData, Ruleset, and RulesetCache](../chapters/Part_02_Chapter_02_Manifest.md) |
| **FieldLoader** | The reflection-based system that converts MiniYaml values into C# object fields. | [Part 2.3 — FieldLoader and ObjectCreator](../chapters/Part_02_Chapter_03_FieldLoader.md) |
| **Inherits** | A MiniYaml directive that merges a parent node's values into the current node. | [Part 2.1 — MiniYaml Parser and Inheritance](../chapters/Part_02_Chapter_01_MiniYaml.md) |
| **Abstract Actor** | An actor whose YAML key starts with `^`. It exists for inheritance but is not spawned directly. | [Part 2.1 — MiniYaml Parser and Inheritance](../chapters/Part_02_Chapter_01_MiniYaml.md), [Part 2.4 — Rulesets, Actors, and Weapons](../chapters/Part_02_Chapter_04_Rules_Weapons.md) |
| **Instance Name** | A suffix after `@` in a trait key (e.g., `Armament@PRIMARY`). It allows multiple instances of the same trait on one actor. | [Part 2.1 — MiniYaml Parser and Inheritance](../chapters/Part_02_Chapter_01_MiniYaml.md), [Part 2.4 — Rulesets, Actors, and Weapons](../chapters/Part_02_Chapter_04_Rules_Weapons.md) |
| **WeaponInfo** | The immutable, YAML-loaded definition of a weapon: range, projectile, warheads, reload, sounds, etc. | [Part 2.4 — Rulesets, Actors, and Weapons](../chapters/Part_02_Chapter_04_Rules_Weapons.md) |
| **Warhead** | The part of a weapon that determines what happens when a projectile hits (damage, spread, effects, etc.). | [Part 2.4 — Rulesets, Actors, and Weapons](../chapters/Part_02_Chapter_04_Rules_Weapons.md), [Part 1.6 — Combat and Damage Resolution](../chapters/Part_01_Chapter_06_Combat_Damage.md) |
| **Sequence** | A named animation definition that maps frames from a sprite file to an actor state. | [Part 4.1 — Renderer, Sheet, and Sprite](../chapters/Part_04_Chapter_01_Renderer.md), [Part 6.5 — Asset Loaders](../chapters/Part_06_Chapter_05_Asset_Loaders.md) |
| **TileSet** | A definition of terrain tiles, colors, and movement properties for a particular map style. | [Part 2.4 — Rulesets, Actors, and Weapons](../chapters/Part_02_Chapter_04_Rules_Weapons.md), [Part 6.5 — Asset Loaders](../chapters/Part_06_Chapter_05_Asset_Loaders.md) |

## Rendering and UI

| Term | Definition | See also |
| :---- | :---- | :---- |
| **Sheet** | A large GPU texture that holds many sprite frames. Used to reduce draw calls and texture switches. | [Part 4.1 — Renderer, Sheet, and Sprite](../chapters/Part_04_Chapter_01_Renderer.md) |
| **Sprite** | A reference to a rectangle within a sheet, including UV coordinates and draw metadata. | [Part 4.1 — Renderer, Sheet, and Sprite](../chapters/Part_04_Chapter_01_Renderer.md) |
| **Palette** | A 256-color lookup table. Used for 8-bit indexed sprites. | [Part 4.1 — Renderer, Sheet, and Sprite](../chapters/Part_04_Chapter_01_Renderer.md) |
| **Renderable** | An object that can be drawn by the world renderer. Renderables are sorted and batched each frame. | [Part 4.2 — WorldRenderer](../chapters/Part_04_Chapter_02_WorldRenderer.md) |
| **Chrome** | OpenRA's UI system. Widgets, layouts, and logic are declared in YAML and driven by C#. | [Part 4.3 — Widgets and Chrome](../chapters/Part_04_Chapter_03_Widgets.md) |
| **Widget** | A node in the UI tree. Widgets handle input, tick logic, and drawing. | [Part 4.3 — Widgets and Chrome](../chapters/Part_04_Chapter_03_Widgets.md) |
| **Viewport** | The camera view into the world. It controls scroll position, zoom, and visible cell region. | [Part 4.4 — Viewport and Input](../chapters/Part_04_Chapter_04_Viewport_Input.md) |
| **Order Generator** | The active command mode that translates mouse/keyboard input into orders and renders cursors. | [Part 4.4 — Viewport and Input](../chapters/Part_04_Chapter_04_Viewport_Input.md), [Part 1.3 — World, OrderManager, and Orders](../chapters/Part_01_Chapter_03_World_Orders.md) |
| **Asset Visual Reference** | A quick-lookup table for file formats, YAML definitions, and engine classes for OpenRA art, audio, and data assets. | [Appendix H — Asset Visual Reference](Appendix_H_Asset_Visual_Reference.md) |

## Audio

| Term | Definition | See also |
| :---- | :---- | :---- |
| **ISoundEngine** | The platform abstraction for audio playback. | [Part 5.1 — Audio Architecture](../chapters/Part_05_Chapter_01_Audio_Architecture.md) |
| **ISoundSource** | A cached, playable audio buffer (e.g., a sound effect). | [Part 5.1 — Audio Architecture](../chapters/Part_05_Chapter_01_Audio_Architecture.md) |
| **ISound** | An active instance of a playing sound. | [Part 5.1 — Audio Architecture](../chapters/Part_05_Chapter_01_Audio_Architecture.md) |
| **Spatial Attenuation** | The reduction of sound volume based on distance from the listener. | [Part 5.2 — Spatial Sound Attenuation](../chapters/Part_05_Chapter_02_Spatial_Attenuation.md) |
| **MusicPlaylist** | The subsystem that manages background music tracks and playback. | [Part 5.3 — Music](../chapters/Part_05_Chapter_03_Music.md) |

![Scripting and vfs diagram](images/Appendix_A_Glossary-layered-mount-stack-diagram-showing-package-priority-order-a-b8c51c.svg)

## Scripting and VFS


| Term | Definition | See also |
| :---- | :---- | :---- |
| **VFS** | Virtual File System. A layered namespace that unifies files from directories, ZIP archives, MIX files, and other packages. | [Part 6.3 — Virtual File System](../chapters/Part_06_Chapter_03_VFS.md) |
| **Package** | A container that the VFS can mount. Examples: folders, ZIP files, MIX files. | [Part 6.3 — Virtual File System](../chapters/Part_06_Chapter_03_VFS.md) |
| **Package Loader** | A class that parses a specific package format and exposes it as an `IReadOnlyPackage`. | [Part 6.3 — Virtual File System](../chapters/Part_06_Chapter_03_VFS.md), [Part 6.5 — Asset Loaders](../chapters/Part_06_Chapter_05_Asset_Loaders.md) |
| **Lua Script** | A script file loaded by a map. Used for missions, objectives, and custom game logic. | [Part 6.1 — Lua Scripting and Eluant](../chapters/Part_06_Chapter_01_Lua_Eluant.md) |
| **ScriptContext** | The runtime environment that hosts Lua scripts and binds C# objects to Lua. | [Part 6.2 — ScriptContext Lifecycle and Bindings](../chapters/Part_06_Chapter_02_ScriptContext.md) |
| **ScriptGlobal** | A C# class exposed as a global Lua table. | [Part 6.2 — ScriptContext Lifecycle and Bindings](../chapters/Part_06_Chapter_02_ScriptContext.md) |
| **ScriptActorProperties** | A C# class that exposes actor properties and methods to Lua. | [Part 6.2 — ScriptContext Lifecycle and Bindings](../chapters/Part_06_Chapter_02_ScriptContext.md) |
| **ScriptPlayerProperties** | A C# class that exposes player properties and methods to Lua. | [Part 6.2 — ScriptContext Lifecycle and Bindings](../chapters/Part_06_Chapter_02_ScriptContext.md) |
| **Eluant** | The C# Lua runtime library used by OpenRA. | [Part 6.1 — Lua Scripting and Eluant](../chapters/Part_06_Chapter_01_Lua_Eluant.md) |

## AI and Networking

| Term | Definition | See also |
| :---- | :---- | :---- |
| **Bot** | A computer-controlled player driven by `IBot` modules. | [Part 8.1 — Bot Architecture and IBot](../chapters/Part_08_Chapter_01_IBot.md) |
| **ModularBot** | The standard OpenRA bot implementation that coordinates multiple bot modules. | [Part 8.1 — Bot Architecture and IBot](../chapters/Part_08_Chapter_01_IBot.md) |
| **Bot Module** | A trait that implements one aspect of AI behavior (production, base building, squads, support powers, etc.). | [Part 8.2 — Bot Modules](../chapters/Part_08_Chapter_02_Bot_Modules.md) |
| **Squad** | A group of units managed by the bot as a single combat force. | [Part 8.3 — Bot Squads and Combat Heuristics](../chapters/Part_08_Chapter_03_Squads.md) |
| **Fuzzy Logic** | A rule system that uses degrees of truth rather than strict boolean logic. OpenRA uses it for attack/flee decisions. | [Part 8.3 — Bot Squads and Combat Heuristics](../chapters/Part_08_Chapter_03_Squads.md) |
| **OrderManager** | The client-side coordinator that buffers orders and advances the lockstep simulation. | [Part 9.1 — OrderManager and Lockstep Foundation](../chapters/Part_09_Chapter_01_OrderManager.md), [Part 1.3 — World, OrderManager, and Orders](../chapters/Part_01_Chapter_03_World_Orders.md) |
| **Lockstep** | The networking model where every client waits for all orders before advancing the simulation frame. | [Part 9.1 — OrderManager and Lockstep Foundation](../chapters/Part_09_Chapter_01_OrderManager.md) |
| **Server Trait** | A plugin that runs on the server to add custom behavior (e.g., master server pinging, vote kick). | [Part 9.2 — Server and Connection Layer](../chapters/Part_09_Chapter_02_Server_Connection.md) |

## Map Generation

| Term | Definition | See also |
| :---- | :---- | :---- |
| **RMG** | Random Map Generator. The subsystem that procedurally generates skirmish maps. | [Part 7.1 — Map Generation Pipeline Overview](../chapters/Part_07_Chapter_01_Pipeline.md) |
| **CellLayer** | A 2D grid indexed by map cells, used to store terrain data, distance fields, and placement masks. | [Part 7.2 — Map Generation Data Structures](../chapters/Part_07_Chapter_02_Data_Structures.md) |
| **MapGrid** | The definition of the map coordinate system, including tile shape and depth-buffer settings. | [Part 7.2 — Map Generation Data Structures](../chapters/Part_07_Chapter_02_Data_Structures.md) |
| **Terraformer** | The RMG phase that builds terrain from parameterized templates. | [Part 7.4 — Terraformer](../chapters/Part_07_Chapter_04_Terraformer.md) |
| **MultiBrush** | A brush that can stamp multiple tiles at once, used by the RMG for terrain features. | [Part 7.5 — MultiBrush and Tile Placement](../chapters/Part_07_Chapter_05_MultiBrush.md) |
| **ActorPlan** | A planned actor placement in the RMG output. | [Part 7.7 — Resource and Actor Placement](../chapters/Part_07_Chapter_07_Resources_Actors.md) |

## Modding and Build

| Term | Definition | See also |
| :---- | :---- | :---- |
| **Mod** | A set of YAML, assets, and optional C# code that defines a game using the OpenRA engine. | [Part 3.1 — Mod SDK and Project Structure](../chapters/Part_03_Chapter_01_Mod_SDK.md) |
| **Mod SDK** | The project template and tooling for building standalone mods. | [Part 3.1 — Mod SDK and Project Structure](../chapters/Part_03_Chapter_01_Mod_SDK.md) |
| **Content Installer** | The system that downloads or extracts original game assets for official mods. | [Part 3.2 — Mod SDK Bootstrapping](../chapters/Part_03_Chapter_02_SDK_Bootstrap.md) |
| **Utility Command** | A command-line tool implemented in C# for modding and validation tasks. | [Part 10.3 — Porting, Modding, and Developer Workflows](../chapters/Part_10_Chapter_03_Port_And_Modding.md) |
| **Launch Script** | A shell script that starts the game with a specific mod during development. | [Part 3.2 — Mod SDK Bootstrapping](../chapters/Part_03_Chapter_02_SDK_Bootstrap.md), [Part 10.3 — Porting, Modding, and Developer Workflows](../chapters/Part_10_Chapter_03_Port_And_Modding.md) |

![Coordinate system diagram showing the relationship between WPos, CPos,](images/Appendix_A_Glossary-coordinate-system-diagram-showing-the-relationship-between-w-287536.svg)

## Coordinates


| Term | Definition | See also |
| :---- | :---- | :---- |
| **CPos** | Cell position. Integer coordinates on the map grid. | [Part 1.4 — Deterministic Math and Coordinate Systems](../chapters/Part_01_Chapter_04_Math.md) |
| **WPos** | World position. Integer coordinates in world pixels (usually 1024 per cell). | [Part 1.4 — Deterministic Math and Coordinate Systems](../chapters/Part_01_Chapter_04_Math.md) |
| **WVec** | World vector. Difference between two world positions. | [Part 1.4 — Deterministic Math and Coordinate Systems](../chapters/Part_01_Chapter_04_Math.md) |
| **WAngle** | A fixed-point angle used for facings and orientations. | [Part 1.4 — Deterministic Math and Coordinate Systems](../chapters/Part_01_Chapter_04_Math.md) |
| **WDist** | A fixed-point distance in world pixels. | [Part 1.4 — Deterministic Math and Coordinate Systems](../chapters/Part_01_Chapter_04_Math.md) |
| **SubCell** | A subdivision within a cell for infantry placement. | [Part 1.4 — Deterministic Math and Coordinate Systems](../chapters/Part_01_Chapter_04_Math.md) |

## Summary

This glossary defines the key terms used throughout the OpenRA engine and this manual. Use it as a quick reference when you encounter unfamiliar terminology in the architecture chapters or in the source code.

## What to read next

- **For the actor/trait model:** [Part 1.1 — Entity-Component-System (ECS) and Actor Lifecycle](../chapters/Part_01_Chapter_01_ECS.md)
- **For the Virtual File System:** [Part 6.3 — Virtual File System](../chapters/Part_06_Chapter_03_VFS.md)
- **For common YAML syntax patterns:** [Appendix B — Common YAML Patterns](Appendix_B_Common_YAML_Patterns.md)
- **For copy-paste modding examples:** [Appendix E — Practical Modding Recipes](Appendix_E_Practical_Recipes.md)