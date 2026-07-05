# Chapter 6.2 — ScriptContext Lifecycle and Bindings

## Purpose

`ScriptContext` is the bridge between the OpenRA world and the Lua runtime. It manages the [Eluant](../appendices/Appendix_A_Glossary.md) runtime instance, discovers and registers C# bindings, loads map scripts, executes the per-frame tick, and handles fatal errors. This chapter focuses on the internal lifecycle of the context and the mechanics of how C# objects become Lua tables.

## Learning Objectives


After studying this chapter, you should be able to:

- Explain the lifecycle of a [ScriptContext](../appendices/Appendix_A_Glossary.md) from creation to disposal.
- Describe how the Eluant runtime is created, sanitized, and configured.
- Trace the binding discovery process for [ScriptGlobal](../appendices/Appendix_A_Glossary.md), ScriptActorProperties, and ScriptPlayerProperties.
- Explain how ScriptObjectWrapper and ScriptMemberWrapper bridge C# and Lua.
- Handle fatal Lua errors and understand why the context stops ticking after an error.
- Implement conditional actor bindings using Requires<> constraints.

## Files

| File | Responsibility |
| :---- | :---- |
| `OpenRA.Game/Scripting/ScriptContext.cs` | `ScriptContext` plus the `ScriptGlobal`, `ScriptActorProperties`, `ScriptPlayerProperties` base classes and the `ScriptGlobalAttribute` / `ScriptPropertyGroupAttribute` metadata. |
| `OpenRA.Game/Scripting/ScriptObjectWrapper.cs` | Wraps one or more C# objects as a single Lua table. |
| `OpenRA.Game/Scripting/ScriptMemberWrapper.cs` | Wraps individual C# properties and methods. |
| `OpenRA.Game/Scripting/ScriptMemberExts.cs` | Extension methods for reflecting over script-exposed members. |
| `OpenRA.Game/Scripting/ScriptActorInterface.cs` | Builds the actor property table for a given actor. |
| `OpenRA.Game/Scripting/ScriptPlayerInterface.cs` | Builds the player property table for a given player. |
| `OpenRA.Game/Scripting/ScriptTypes.cs` | Conversion registry for C# <=> Lua values. |
| `OpenRA.Mods.Common/Scripting/ScriptTriggers.cs` | Binds Lua functions to trait notifications. |

![Architecture diagram](images/Part_06_Chapter_02_ScriptContext-architecture-diagram-showing-the-main-classes-interfaces-and-9161e6.svg)

## Architecture


### Context ownership

```
[World] -> [LuaScript trait] -> [ScriptContext] -> [MemoryConstrainedLuaRuntime]
                                          -> [ScriptGlobal bindings]
                                          -> [Actor/Player interface bindings]
                                          -> [Loaded scripts]
```

There is exactly one `ScriptContext` per loaded map that uses scripts. The context is created during `IWorldLoaded.WorldLoaded` and disposed when the world is disposed.

### Object wrappers

The core abstraction is `ScriptObjectWrapper`. It takes one or more C# objects and exposes them as a Lua table. For each public property or method, it creates a `ScriptMemberWrapper` that handles the Lua-to-C# invocation.

### Global registration

Globals are registered by iterating over all types implementing `ScriptGlobal` and invoking the constructor that takes a `ScriptContext`. The resulting object is wrapped and assigned to the Lua global table under the name specified by `[ScriptGlobal("Name")]`.

### Actor and player registration

Actors and players are not pre-bound. Instead, `ScriptContext` maintains a cache of "command" types per `ActorInfo`. When Lua accesses an actor object, `ScriptActorInterface` builds a fresh wrapper containing the property classes that apply to that actor's traits. The same applies to players via `ScriptPlayerInterface`.

![Data flow  code path diagram](images/Part_06_Chapter_02_ScriptContext-sequence-flow-diagram-tracing-the-execution-path-from-trigge-035864.svg)

## Data Flow / Code Path


### Constructor

The `ScriptContext` constructor performs the following steps:

1. Create the Eluant runtime.
2. Add a dedicated `lua` log channel.
3. Discover `ScriptActorProperties` and `ScriptPlayerProperties` types.
4. Filter player commands against the `Player` actor rules.
5. Sanitize the Lua global environment:
   - Remove all non-whitelisted globals.
   - Remove `math.random` and `math.randomseed`.
6. Register the `EngineDir`, `FatalError`, `print`, and `MaxUserScriptInstructions` globals.
7. Register all `ScriptGlobal` subclasses.
8. Set the memory limit based on current usage plus the user allowance.
9. Load and execute each script file.
10. Cache the global `Tick` function for later use.

```csharp
public ScriptContext(World world, WorldRenderer worldRenderer, IEnumerable<string> scripts)
{
    runtime = new MemoryConstrainedLuaRuntime();
    ...
    runtime.MaxMemoryUse = runtime.MemoryUse + MaxUserScriptMemory;

    foreach (var script in scripts)
        runtime.DoBuffer(world.Map.Open(script).ReadAllText(), script).Dispose();

    tick = runtime.Globals["Tick"] as LuaFunction;
}
```

### WorldLoaded

After construction, `LuaScript.WorldLoaded` calls `Context.WorldLoaded()`. This gives globals a chance to run setup code. The default `ScriptContext.WorldLoaded` iterates over registered globals and calls any `WorldLoaded` logic they expose.

### Tick

`Context.Tick()` calls the Lua `Tick` function once per frame:

```csharp
public void Tick()
{
    if (disposed || FatalErrorOccurred)
        return;

    try
    {
        using (tick)
            tick?.Call();
    }
    catch (Exception e)
    {
        FatalError(e);
    }
}
```

The function is disposed each call because Eluant `LuaFunction` references are single-use wrappers.

### Fatal error handling

If a script throws or violates a limit, `FatalError` is called:

```csharp
public void FatalError(Exception e)
{
    ErrorMessage = e.Message;
    FatalErrorOccurred = true;
    Log.Write("lua", $"Fatal Lua Error: {e.Message}");
    ...
}
```

Once a fatal error has occurred, the context stops ticking and the mission script is effectively disabled.

### Disposal

When the world is disposed, `LuaScript.Disposing` calls `Context.Dispose()`, which releases the Lua runtime and all bound objects.

![Configuration (yaml) diagram](images/Part_06_Chapter_02_ScriptContext-annotated-yaml-snippet-diagram-showing-the-key-fields-and-ho-6a1b98.svg)

## Configuration (YAML)


ScriptContext behavior is mostly controlled through the `LuaScript` trait:

```yaml
World:
    LuaScript:
        Scripts: script1.lua, script2.lua
```

The memory and instruction limits are hardcoded in `ScriptContext`:

- `MaxUserScriptMemory = 50 * 1024 * 1024` (50 MB).
- `MaxUserScriptInstructions = 1,000,000`.

## Interconnectivity

- **Depends on:** [Part 1.1 — ECS, Actors, and Traits](Part_01_Chapter_01_ECS.md), [Part 2.4 — Rulesets, Actors, and Weapons](Part_02_Chapter_04_Rules_Weapons.md), [Part 3.1 — Mod SDK and Project Structure](Part_03_Chapter_01_Mod_SDK.md), [Part 6.1 — Lua Scripting and Eluant](Part_06_Chapter_01_Lua_Eluant.md), [Part 6.3 — Virtual File System](Part_06_Chapter_03_VFS.md).
- **Used by:** [Part 6.1 — Lua Scripting and Eluant](Part_06_Chapter_01_Lua_Eluant.md), [Part 6.3 — Virtual File System](Part_06_Chapter_03_VFS.md), Part 10 (campaign scripts).

![Algorithms diagram](images/Part_06_Chapter_02_ScriptContext-algorithm-diagram-or-pseudocode-flowchart-for-the-non-trivia-5983ed.svg)

## Algorithms


### Binding discovery

Globals are discovered via `ObjectCreator.GetTypesImplementing<ScriptGlobal>()`:

```csharp
var bindings = Game.ModData.ObjectCreator.GetTypesImplementing<ScriptGlobal>();
foreach (var b in bindings)
{
    var ctor = b.GetConstructors(...).FirstOrDefault(c =>
    {
        var p = c.GetParameters();
        return p.Length == 1 && p[0].ParameterType == typeof(ScriptContext);
    });

    if (ctor == null)
        throw new InvalidOperationException(...);

    var binding = (ScriptGlobal)ctor.Invoke([this]);
    using (var obj = binding.ToLuaValue(this))
        runtime.Globals.Add(binding.Name, obj);
}
```

Each global must have a public constructor taking exactly one `ScriptContext` parameter.

### Actor command filtering

```csharp
Type[] FilterActorCommands(ActorInfo actorInfo)
{
    return knownActorCommands
        .Where(t => t.GetInterfaces().Any(i =>
            i.IsGenericType &&
            i.GetGenericTypeDefinition() == typeof(Requires<>) &&
            actorInfo.HasTraitInfo(i.GetGenericArguments()[0])))
        .ToArray();
}
```

This ensures an actor only exposes the Lua properties that are meaningful for its traits.

### Member caching

`ScriptMemberWrapper` caches the reflected method/property info so repeated Lua calls do not pay the reflection cost each time. The wrapper also handles argument conversion and return value conversion.

### ToLuaValue conversion

`ScriptObjectWrapper.ToLuaValue` creates a Lua table that forwards index access to the wrapped C# members. The table is cached by Eluant's runtime, so multiple Lua references to the same object reuse the same wrapper.

![Extension points diagram](images/Part_06_Chapter_02_ScriptContext-extension-hook-diagram-showing-the-interface-s-to-implement-b4a27b.svg)

## Extension Points


### Add custom global setup

A `ScriptGlobal` can override `WorldLoaded` to perform initialization after all scripts are loaded. For example, the `MapGlobal` or `WorldGlobal` may cache commonly used world state.

### Add script triggers

Implement `ScriptTriggers` patterns to let Lua subscribe to trait events. This is done by adding a trait that stores Lua callbacks and invoking them when the corresponding notification fires.

### Custom type conversion

`ScriptTypes` is the central registry. To add a new convertible type, implement a conversion function and register it with `ScriptTypes`. For example, convert a custom struct to a Lua table.

### Conditional actor bindings

Use `Requires<>` on a `ScriptActorProperties` class to conditionally expose properties based on actor traits. Use `NotBefore<>` to control initialization order.

![Common pitfalls  guardrails diagram](images/Part_06_Chapter_02_ScriptContext-checklist-infographic-style-diagram-summarizing-the-top-pitf-fb069e.svg)

## Common Pitfalls / Guardrails


- **Constructor signature:** a `ScriptGlobal` must have a public constructor with exactly one `ScriptContext` parameter. Multiple constructors or different signatures will cause a runtime error.
- **Duplicate global names:** two `[ScriptGlobal]` attributes with the same name will collide when registering in `runtime.Globals`.
- **Lua reference disposal:** always dispose `LuaValue` and `LuaFunction` objects obtained from the runtime. Failing to do so leaks Lua memory.
- **Re-entrancy:** the Lua runtime is single-threaded. Do not call Lua from multiple threads or from inside Lua callbacks in a way that re-enters the runtime.
- **Fatal errors:** once a fatal error occurs, the context stops. Mission scripts should handle errors gracefully to avoid breaking the entire mission.
- **Script order:** scripts are loaded in the order listed in YAML. Later scripts can override functions defined by earlier scripts.
- **Memory limit:** the limit is set once after loading system libraries. If a script loads a very large table early, it may consume most of the budget.

## What to read next

- [Part 6.1 — Lua Scripting and Eluant](Part_06_Chapter_01_Lua_Eluant.md) for the Lua runtime and binding basics that ScriptContext wraps.
- [Part 6.3 — Virtual File System](Part_06_Chapter_03_VFS.md) for how script files are loaded from the VFS.
- [Part 10.3 — Porting, Modding, and Developer Workflows](Part_10_Chapter_03_Port_And_Modding.md) for debugging and extending script bindings.
- [Appendix G — Advanced Modding Walkthroughs](../appendices/Appendix_G_Advanced_Modding_Walkthroughs.md) for a complete single-player Lua mission walkthrough.

## Summary

This chapter explains how `ScriptContext` bridges the OpenRA world and the Lua runtime.

After reading this chapter, you should be able to:

- Create the Eluant runtime.
- Add a dedicated `lua` log channel.
- Discover `ScriptActorProperties` and `ScriptPlayerProperties` types.
- Filter player commands against the `Player` actor rules.
- Sanitize the Lua global environment:

If any of the concepts above feel unclear, review the relevant section before continuing. For source files and further reading, see the References section.


## References

- `OpenRA.Game/Scripting/ScriptContext.cs` — context lifecycle.
- `OpenRA.Game/Scripting/ScriptObjectWrapper.cs` — object wrappers.
- `OpenRA.Game/Scripting/ScriptMemberWrapper.cs` — member binding.
- `OpenRA.Game/Scripting/ScriptActorInterface.cs` — actor interface.
- `OpenRA.Game/Scripting/ScriptPlayerInterface.cs` — player interface.
- `OpenRA.Game/Scripting/ScriptTypes.cs` — type conversion.
- `OpenRA.Mods.Common/Scripting/ScriptTriggers.cs` — event triggers.


### External resources

- [OpenRA Lua API](https://docs.openra.net/en/release/lua/)
- [OpenRA Lua tutorial](https://steamsdev.github.io/content/openratut/home.html)