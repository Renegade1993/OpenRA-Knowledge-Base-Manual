# Chapter 6.1 — Lua Scripting and Eluant

## Purpose

OpenRA supports [Lua scripting](https://docs.openra.net/en/release/lua/) for mission logic, custom game modes, and [map-specific behavior](https://steamsdev.github.io/content/openratut/mapscript.html). The Lua runtime is embedded through the **[Eluant](../appendices/Appendix_A_Glossary.md)** library, which is a C# wrapper around Lua. The engine exposes a curated set of C# objects to Lua as globals, actor properties, and player properties, and scripts can trigger game events, query state, and issue orders. This chapter introduces the Lua runtime, the binding model, and the sandbox.

## Learning Objectives


After studying this chapter, you should be able to:

- Explain how OpenRA embeds Lua through the Eluant library and sandboxes scripts.
- Describe the three binding layers: globals, actor properties, and player properties.
- Configure a map to load [Lua script](../appendices/Appendix_A_Glossary.md) files via the LuaScript trait.
- Implement a new [ScriptGlobal](../appendices/Appendix_A_Glossary.md), ScriptActorProperties, or ScriptPlayerProperties class.
- Trace the per-frame tick flow and how ScriptTriggers connect C# events to Lua callbacks.
- Understand the memory and instruction limits that constrain user scripts.

## Files

| File | Responsibility |
| :---- | :---- |
| `OpenRA.Mods.Common/Scripting/LuaScript.cs` | World trait that loads and runs map scripts. |
| `OpenRA.Game/Scripting/ScriptContext.cs` | Creates the Lua runtime, registers globals, and loads scripts. Also defines the `ScriptGlobal`, `ScriptActorProperties`, `ScriptPlayerProperties`, `ScriptGlobalAttribute`, and `ScriptPropertyGroupAttribute` base classes. |
| `OpenRA.Game/Scripting/ScriptObjectWrapper.cs` | Wraps a C# object as a Lua table. |
| `OpenRA.Game/Scripting/ScriptMemberWrapper.cs` | Wraps a C# property/method as a Lua function. |
| `OpenRA.Game/Scripting/ScriptTypes.cs` | Type conversions between C# and Lua. |
| `OpenRA.Game/Scripting/ScriptActorInterface.cs` | Exposes actor properties to Lua. |
| `OpenRA.Game/Scripting/ScriptPlayerInterface.cs` | Exposes player properties to Lua. |
| `OpenRA.Mods.Common/Scripting/ScriptTriggers.cs` | Connects Lua events to trait notifications. |
| `OpenRA.Mods.Common/Scripting/Properties/*.cs` | Script property implementations for actors and players. |
| `OpenRA.Mods.Common/Scripting/Global/*.cs` | Global Lua tables (e.g., `Media`, `Map`, `Player`, `Utils`, `World`). |
| `Eluant` (external library) | `MemoryConstrainedLuaRuntime` is the Lua runtime wrapper used by `ScriptContext` to enforce memory and instruction limits. |

![Architecture diagram](images/Part_06_Chapter_01_Lua_Eluant-architecture-diagram-showing-the-main-classes-interfaces-and-9161e6.svg)

## Architecture


### Lua runtime per map

Each map that uses scripts gets a fresh `ScriptContext` created by the `LuaScript` world trait when the world is loaded. The context owns a `MemoryConstrainedLuaRuntime` (Eluant), loads the specified script files, and registers global bindings.

### Sandboxing

The runtime is heavily sandboxed:

- Most standard Lua globals are removed except for safe ones (`ipairs`, `pairs`, `tonumber`, `tostring`, `math`, `string`, `table`, etc.).
- `math.random` and `math.randomseed` are removed to prevent desyncs.
- Scripts are limited to 50 MB of memory and 1,000,000 instructions per function call.
- `print` is redirected to a Lua log channel.
- A `FatalError` global is provided so scripts can report unrecoverable errors.

### Three binding layers

OpenRA exposes three kinds of Lua bindings:

1. **Globals** — top-level Lua tables such as `World`, `Map`, `Player`, `Media`, `Utils`. These are defined by classes inheriting `ScriptGlobal` and marked with `[ScriptGlobalAttribute("Name")]`.
2. **Actor properties** — properties attached to actor objects. These are defined by classes inheriting `ScriptActorProperties` and marked with `[ScriptPropertyGroupAttribute("Category")]`.
3. **Player properties** — properties attached to player objects. These are defined by classes inheriting `ScriptPlayerProperties` and marked with `[ScriptPropertyGroupAttribute("Category")]`.

### Automatic binding discovery

`ScriptContext` uses reflection to find all `ScriptGlobal`, `ScriptActorProperties`, and `ScriptPlayerProperties` subclasses and register them. Actor properties are filtered by actor type so each actor only exposes the properties relevant to its traits.

![Data flow  code path diagram](images/Part_06_Chapter_01_Lua_Eluant-sequence-flow-diagram-tracing-the-execution-path-from-trigge-035864.svg)

## Data Flow / Code Path


### Loading scripts

When the world is loaded, `LuaScript.WorldLoaded` creates a `ScriptContext`:

```csharp
void IWorldLoaded.WorldLoaded(World world, WorldRenderer worldRenderer)
{
    var scripts = info.Scripts ?? Enumerable.Empty<string>();
    Context = new ScriptContext(world, worldRenderer, scripts);
    Context.WorldLoaded();
}
```

The context constructor:

1. Creates the Eluant runtime.
2. Clears unsafe globals.
3. Registers global tables.
4. Loads each script file via `runtime.DoBuffer`.
5. Looks up a global `Tick` function to call each frame.

### Per-frame tick

`LuaScript.Tick` calls `Context.Tick`, which calls the Lua `Tick` function if it exists:

```csharp
void ITick.Tick(Actor self)
{
    Context.Tick();
}
```

### Calling Lua from C# events

`ScriptTriggers` wires trait notifications to Lua callbacks. For example, when an actor is killed, a Lua `OnKilled` function can be invoked. This is how mission scripts respond to game events.

### Calling C# from Lua

When Lua accesses a property or method on a bound object, the `ScriptObjectWrapper` and `ScriptMemberWrapper` translate the call to C#. Return values are converted to Lua values via `ScriptTypes` and `ToLuaValue`.

![Configuration (yaml) diagram](images/Part_06_Chapter_01_Lua_Eluant-annotated-yaml-snippet-diagram-showing-the-key-fields-and-ho-6a1b98.svg)

## Configuration (YAML)


### Enabling scripts on a map

The world actor in a map's rules YAML declares the script files:

```yaml
World:
    LuaScript:
        Scripts: script.lua
```

Multiple scripts can be listed. Paths are relative to the map [package](../appendices/Appendix_A_Glossary.md).

### Registering a global table

A C# class can be exposed as a Lua global:

```csharp
[ScriptGlobal("MyGlobal")]
[Desc("My custom global table.")]
public class MyGlobal : ScriptGlobal
{
    public MyGlobal(ScriptContext context) : base(context) { }

    [Desc("Does something useful.")]
    public void DoSomething() { ... }
}
```

### Registering actor properties

```csharp
[ScriptPropertyGroup("MyProperties")]
[Desc("Properties for my custom actor.")]
public class MyActorProperties : ScriptActorProperties
{
    public MyActorProperties(ScriptContext context, Actor self) : base(context, self) { }

    [Desc("Returns the actor's custom value.")]
    public int CustomValue => Self.Trait<MyTrait>().Value;
}
```

### Registering player properties

```csharp
[ScriptPropertyGroup("MyPlayerProperties")]
public class MyPlayerProperties : ScriptPlayerProperties
{
    public MyPlayerProperties(ScriptContext context, Player player) : base(context, player) { }

    [Desc("Returns the player's score.")]
    public int Score => Player.PlayerActor.Trait<MyScoreTrait>().Score;
}
```

## Interconnectivity

- **Depends on:** [Part 1.1 — ECS, Actors, and Traits](Part_01_Chapter_01_ECS.md), [Part 2.1 — MiniYaml Parser](Part_02_Chapter_01_MiniYaml.md), [Part 3.1 — Mod SDK and Project Structure](Part_03_Chapter_01_Mod_SDK.md), [Part 6.3 — Virtual File System](Part_06_Chapter_03_VFS.md), [Part 1.3 — World, OrderManager, and Orders](Part_01_Chapter_03_World_Orders.md).
- **Used by:** [Part 6.2 — ScriptContext Lifecycle and Bindings](Part_06_Chapter_02_ScriptContext.md), Part 10 (official campaigns use Lua scripts), and map authors.

![Algorithms diagram](images/Part_06_Chapter_01_Lua_Eluant-algorithm-diagram-or-pseudocode-flowchart-for-the-non-trivia-5983ed.svg)

## Algorithms


### Instruction counting

`MemoryConstrainedLuaRuntime` hooks into the Lua runtime to count instructions. If a script exceeds `MaxUserScriptInstructions`, the runtime throws an exception, preventing infinite loops from hanging the game.

### Memory tracking

The runtime tracks Lua memory use and sets a hard limit. The limit is initialized after system libraries are loaded so that only user script memory counts toward the cap.

### Type conversion

`ScriptTypes` and `ScriptObjectWrapper` handle conversions between C# and Lua:

- Primitive types (int, float, bool, string) pass directly.
- `Actor`, `Player`, `World`, and `WorldRenderer` are wrapped as script objects.
- `IEnumerable<T>` and arrays are converted to Lua tables.
- `LuaValue` and `LuaFunction` are passed as Lua references.

### Property filtering

Actor properties are filtered per actor type by checking which property classes are applicable:

```csharp
Type[] FilterActorCommands(ActorInfo actorInfo)
{
    return knownActorCommands
        .Where(t => t.GetInterfaces().Any(i => i.IsGenericType && i.GetGenericTypeDefinition() == typeof(Requires<>)
            && actorInfo.HasTraitInfo(i.GetGenericArguments()[0])))
        .ToArray();
}
```

A property class that declares `Requires<MyTraitInfo>` is only exposed on actors that have `MyTrait`.

![Extension points diagram](images/Part_06_Chapter_01_Lua_Eluant-extension-hook-diagram-showing-the-interface-s-to-implement-b4a27b.svg)

## Extension Points


### Add a new global table

Create a `ScriptGlobal` subclass with a `[ScriptGlobal]` attribute and a constructor taking `ScriptContext`. The runtime will discover it automatically.

### Add new actor properties

Create a `ScriptActorProperties` subclass with a `[ScriptPropertyGroup]` attribute and `Requires<>` constraints. Lua scripts can then access these properties through actor objects.

### Add new player properties

Create a `ScriptPlayerProperties` subclass with a `[ScriptPropertyGroup]` attribute.

### Add Lua event triggers

Use `ScriptTriggers` to map trait notifications to Lua function names. For example, add an `OnCaptured` event that maps to a Lua callback.

### Custom Lua libraries

The sandbox removes most standard libraries. If you need additional safe functions, you can register them as globals from a `ScriptGlobal` class.

![Common pitfalls  guardrails diagram](images/Part_06_Chapter_01_Lua_Eluant-checklist-infographic-style-diagram-summarizing-the-top-pitf-fb069e.svg)

## Common Pitfalls / Guardrails


- **Determinism:** Lua scripts must not use `math.random` or external I/O. Use `world.SharedRandom` or `world.LocalRandom` through C# bindings if needed.
- **Memory limits:** heavy scripts can hit the 50 MB limit. Avoid large tables and excessive closures.
- **Instruction limits:** infinite loops or very expensive computations will trigger the instruction limit and abort the script.
- **Disposal:** `LuaValue` and `LuaFunction` references must be disposed to avoid leaking Lua memory. Use `using` statements.
- **Actor lifetime:** do not hold Lua references to dead actors. Use `ScriptActorPropertyActivityAttribute` for properties that are safe to call on destroyed actors.
- **Error handling:** a fatal Lua error disables the script context for the rest of the game. Mission scripts should validate preconditions and avoid throwing.
- **Thread safety:** Lua scripts run on the main simulation thread. Do not use async operations.

## Practical Example

![Practical example: reinforcement trigger diagram](images/Part_06_Chapter_01_Lua_Eluant-sequence-diagram-of-the-mission-flow-map-yaml-lua-script-wor-2bcbe0.svg)

### Practical Example: Reinforcement Trigger


The snippet below is a complete, minimal mission script for the playtest-20260614 build. When the player's engineer (`e6`) enters the named `extractionZone` cell region, a group of allied units is spawned at the landing zone and a message is displayed.

```lua
ReinforcementsSpawned = false

WorldLoaded = function()
    -- The human player in this mission
    player = Player.GetPlayer("Greece")

    -- Cell region the engineer must reach
    extractionZone = { CPos.New(45, 30), CPos.New(46, 30), CPos.New(47, 30),
                       CPos.New(45, 31), CPos.New(46, 31), CPos.New(47, 31) }

    -- Fire once when the player's engineer enters the zone
    Trigger.OnEnteredFootprint(extractionZone, function(a, id)
        if not ReinforcementsSpawned and a.Owner == player and a.Type == "e6" then
            ReinforcementsSpawned = true
            SpawnReinforcements()
        end
    end)
end

SpawnReinforcements = function()
    local entry = CPos.New(5, 5)

    Actor.Create("mcv", true, { Owner = player, Location = entry })
    Actor.Create("jeep", true, { Owner = player, Location = entry + CVec.New(1, 0) })
    Actor.Create("jeep", true, { Owner = player, Location = entry + CVec.New(2, 0) })
    Actor.Create("e1", true, { Owner = player, Location = entry + CVec.New(0, 1) })
    Actor.Create("e1", true, { Owner = player, Location = entry + CVec.New(1, 1) })

    Media.DisplayMessage("Reinforcements have arrived. Establish your base.")
end
```

Register the script in the map's rules YAML:

```yaml
World:
    LuaScript:
        Scripts: script.lua
```

Adjust the actor types (`e6`, `mcv`, `jeep`, `e1`), player names (`Greece`), and coordinates for the map you are building.

## What to read next

- [Part 6.2 — ScriptContext Lifecycle and Bindings](Part_06_Chapter_02_ScriptContext.md) for the runtime lifecycle that hosts Lua scripts.
- [Part 7.1 — RMG Pipeline](Part_07_Chapter_01_Pipeline.md) for how procedural maps can use Lua-driven logic.
- [Part 10.3 — Porting, Modding, and Developer Workflows](Part_10_Chapter_03_Port_And_Modding.md) for practical mission-scripting workflows.
- [Appendix G — Advanced Modding Walkthroughs](../appendices/Appendix_G_Advanced_Modding_Walkthroughs.md) for a complete single-player Lua mission walkthrough.

## Summary

This chapter explains how OpenRA embeds Lua through the Eluant library to script missions, custom game modes, and map-specific behavior.

After reading this chapter, you should be able to:

- **Globals** — top-level Lua tables such as `World`, `Map`, `Player`, `Media`, `Utils`. These are defined by classes inheriting `ScriptGlobal` and marked with `[ScriptGlobalAttribute("Name")]`.
- **Actor properties** — properties attached to actor objects. These are defined by classes inheriting `ScriptActorProperties` and marked with `[ScriptPropertyGroupAttribute("Category")]`.
- **Player properties** — properties attached to player objects. These are defined by classes inheriting `ScriptPlayerProperties` and marked with `[ScriptPropertyGroupAttribute("Category")]`.

If any of the concepts above feel unclear, review the relevant section before continuing. For source files and further reading, see the References section.


## References

- `OpenRA.Mods.Common/Scripting/LuaScript.cs` — world trait entry point.
- `OpenRA.Game/Scripting/ScriptContext.cs` — runtime creation, binding, and base classes for `ScriptGlobal` / `ScriptActorProperties` / `ScriptPlayerProperties`.
- `OpenRA.Game/Scripting/ScriptObjectWrapper.cs` — object-to-table wrapper.
- `OpenRA.Game/Scripting/ScriptMemberWrapper.cs` — member binding.
- `OpenRA.Game/Scripting/ScriptTypes.cs` — type conversion.
- `Eluant` (external library) — `MemoryConstrainedLuaRuntime` used by `ScriptContext`.
- `OpenRA.Mods.Common/Scripting/Global/*.cs` — global tables.
- `OpenRA.Mods.Common/Scripting/Properties/*.cs` — actor/player properties.


### External resources

- [OpenRA Lua API](https://docs.openra.net/en/release/lua/)
- [OpenRA Lua API reference](https://docs.openra.net/en/release/lua/)
- [OpenRA Lua tutorial](https://steamsdev.github.io/content/openratut/home.html)
- [OpenRA Lua scripting community tutorial](https://steamsdev.github.io/content/openratut/mapscript.html)