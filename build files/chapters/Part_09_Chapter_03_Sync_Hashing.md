# Chapter 9.3 — Sync Hashing and Determinism

## Purpose

OpenRA's multiplayer relies on deterministic simulation. Every client receives the same orders and runs the same code; therefore, every client should reach the same world state after each frame. **[Sync Hash](../appendices/Appendix_A_Glossary.md)** is the mechanism that verifies this: each client computes a hash of the synced world state and sends it to the server, which forwards it to all clients. If any client disagrees, the game has [desynced](../appendices/Appendix_A_Glossary.md). This chapter explains how the sync hash is computed, what it covers, and how to write sync-safe code.

## Learning Objectives


After studying this chapter, you should be able to:

- Explain why sync hashing is essential for deterministic multiplayer.
- Describe the ISync contract and how VerifySync fields contribute to the hash.
- Trace sync hash generation and comparison across clients.
- Use RunUnsynced to safely isolate non-deterministic code.
- Debug desyncs using sync reports.
- Add synced state to a trait correctly.

## Files

| File | Responsibility |
| :---- | :---- |
| `OpenRA.Game/Sync.cs` | Sync hash generation, `ISync` interface, `VerifySyncAttribute`, `RunUnsynced` guard. |
| `OpenRA.Game/World.cs` | `SyncHash()` aggregation over all synced world objects. |
| `OpenRA.Game/Network/OrderManager.cs` | Receives and compares remote sync hashes. |
| `OpenRA.Game/Traits/TraitsInterfaces.cs` | `ISync` marker interface. |
| `OpenRA.Game/Network/SyncReport.cs` | Detailed sync report generation for debugging desyncs. |
| `OpenRA.Game/Traits/Player/Shroud.cs` | Example of a synced trait. |
| `OpenRA.Game/Traits/Player/FrozenActorLayer.cs` | Example of synced state. |

![Architecture diagram](images/Part_09_Chapter_03_Sync_Hashing-architecture-diagram-showing-the-main-classes-interfaces-and-9161e6.svg)

## Architecture


### What contributes to the sync hash

The sync hash is a 32-bit XOR combination of hashes from every object that implements `[ISync](../appendices/Appendix_A_Glossary.md)`. The world iterates over all synced actors and traits and calls `Sync.Hash` on each. Typical synced objects include:

- Actor traits that implement `ISync`.
- Player traits such as `Shroud` and `FrozenActorLayer`.
- [World](../appendices/Appendix_A_Glossary.md) traits that implement `ISync`.
- Effects and projectiles that implement `ISync`.

Client-only state (camera position, audio, UI, selection) does not implement `ISync` and therefore does not affect the hash.

### The ISync contract

```csharp
public interface ISync { }

[AttributeUsage(AttributeTargets.Field | AttributeTargets.Property)]
public sealed class VerifySyncAttribute : Attribute { }
```

Any class implementing `ISync` and marking fields/properties with `[VerifySync]` contributes to the sync hash. The sync system generates an IL-based hash function at runtime for each type.

### Hash function generation

`Sync.GenerateHashFunc` creates a dynamic method that:

1. Casts the object to its concrete type.
2. Initializes a hash accumulator to 0.
3. For each `[VerifySync]` field, loads the field value and XORs it into the accumulator.
4. For each `[VerifySync]` property, calls the getter and XORs the value.
5. Returns the final hash.

The `EmitSyncOpcodes` method handles primitive types and custom hash functions for common OpenRA types:

```csharp
static void EmitSyncOpcodes(Type type, ILGenerator il)
{
    if (CustomHashFunctions.TryGetValue(type, out var hashFunction))
        il.EmitCall(OpCodes.Call, hashFunction, null);
    else if (type == typeof(bool))
        ...
    else if (type != typeof(int))
        throw new NotImplementedException(...);

    il.Emit(OpCodes.Xor);
}
```

Supported custom types include `int2`, `CPos`, `CVec`, `WDist`, `WPos`, `WVec`, `WAngle`, `WRot`, `Actor`, `Player`, and `Target`.

### World sync hash

`World.SyncHash()` aggregates the hashes of all synced objects in the world:

```csharp
public int SyncHash()
{
    var n = 0;
    foreach (var actor in syncHashes)
    {
        if (actor.IsInWorld)
            n += Sync.Hash(actor);
    }

    foreach (var t in syncHashesTraitSet)
    {
        var hash = Sync.Hash(t);
        n += hash;
    }

    return n;
}
```

The result is sent to the server every frame.

![Data flow  code path diagram](images/Part_09_Chapter_03_Sync_Hashing-sequence-flow-diagram-tracing-the-execution-path-from-trigge-035864.svg)

## Data Flow / Code Path


### Syncing during a frame

1. The order manager processes all orders for the frame.
2. After the simulation tick completes, the world state is updated.
3. `World.SyncHash()` is called.
4. The hash is sent to the server bundled with the next order packet.
5. The server forwards the hash to all clients.
6. Each client compares the received hash with the local hash for that frame.
7. If they differ, the game is marked out of sync.

### Remote sync comparison

```csharp
public void ReceiveSync((int Frame, int SyncHash, ulong DefeatState) sync)
{
    if (syncForFrame.TryGetValue(sync.Frame, out var s))
    {
        if (s.SyncHash != sync.SyncHash || s.DefeatState != sync.DefeatState)
            OutOfSync(sync.Frame);
    }
    else
        syncForFrame.Add(sync.Frame, (sync.SyncHash, sync.DefeatState));
}
```

The first client to report a hash stores it; subsequent clients are compared against it.

### Out of sync handling

When a desync is detected, the order manager:

1. Marks `IsOutOfSync = true`.
2. Dumps a sync report if sync reports are enabled.
3. Notifies the player that the game cannot continue reliably.

![Configuration (yaml) diagram](images/Part_09_Chapter_03_Sync_Hashing-annotated-yaml-snippet-diagram-showing-the-key-fields-and-ho-6a1b98.svg)

## Configuration (YAML)


There are no direct YAML controls for sync hashing, but the following settings matter:

- `Game.Settings.Debug.SyncCheckUnsyncedCode` — when true, `RunUnsynced` verifies the hash before and after the call.
- `Game.Settings.Debug.SyncCheckBotModuleCode` — when true, bot module ticks run inside a sync check.
- `LobbyInfo.GlobalSettings.EnableSyncReports` — enables detailed sync reports for debugging.

## Interconnectivity

- **Depends on:** [Part 1.1 — ECS, Actors, and Traits](Part_01_Chapter_01_ECS.md) (Actor/Trait system), [Part 1.3 — World, OrderManager, and Orders](Part_01_Chapter_03_World_Orders.md) (World/Orders), [Part 9.1 — OrderManager and Lockstep Foundation](Part_09_Chapter_01_OrderManager.md) (OrderManager), [Part 9.2 — Server and Connection Layer](Part_09_Chapter_02_Server_Connection.md) (Server/Connection).
- **Used by:** [Part 9.1 — OrderManager and Lockstep Foundation](Part_09_Chapter_01_OrderManager.md) (OrderManager receives sync hashes), [Part 8.1 — Bot Architecture and IBot](Part_08_Chapter_01_IBot.md) (bot code runs in `RunUnsynced`), and every trait that implements `ISync`.

![Algorithms diagram](images/Part_09_Chapter_03_Sync_Hashing-algorithm-diagram-or-pseudocode-flowchart-for-the-non-trivia-5983ed.svg)

## Algorithms


### Type-specific hash functions

The `CustomHashFunctions` dictionary provides stable hashes for common types:

```csharp
public static int HashCPos(CPos i2) => i2.Bits;
public static int HashActor(Actor a) => a != null ? (int)(a.ActorID << 16) : 0;
public static int HashPlayer(Player p) => p != null ? (int)(p.PlayerActor.ActorID << 16) * 0x567 : 0;
public static int HashTarget(Target t) => ...;
```

These are stable across platforms because they do not rely on default `GetHashCode` implementations that may vary.

### Bool hash

Booleans are hashed with distinct values:

```csharp
il.Emit(OpCodes.Ldc_I4, 0xaaa);
il.Emit(OpCodes.Brtrue, l);
il.Emit(OpCodes.Pop);
il.Emit(OpCodes.Ldc_I4, 0x555);
```

This ensures that `true` and `false` produce different and stable hash contributions.

### Unsynced code guard

`Sync.RunUnsynced` allows code that does not affect the simulation to run safely:

```csharp
public static T RunUnsynced<T>(bool checkSyncHash, World world, Func<T> fn)
{
    unsyncCount++;
    var sync = unsyncCount == 1 && checkSyncHash && world != null ? world.SyncHash() : 0;

    try
    {
        return fn();
    }
    finally
    {
        unsyncCount--;
        if (unsyncCount == 0 && checkSyncHash && world != null && !world.Disposing && sync != world.SyncHash())
            throw new InvalidOperationException("RunUnsynced: sync-changing code may not run here");
    }
}
```

The guard checks that the world sync hash did not change while running unsynced code. If it did, the code is not truly unsynced.

### Sync report generation

`SyncReport` records, for every synced object, the value of each `[VerifySync]` field. When a desync occurs, the report can be compared between clients to pinpoint the exact object and field that diverged.

![Extension points diagram](images/Part_09_Chapter_03_Sync_Hashing-extension-hook-diagram-showing-the-interface-s-to-implement-b4a27b.svg)

## Extension Points


### Add synced state to a trait

1. Implement `ISync` on the trait class.
2. Mark the relevant fields/properties with `[VerifySync]`.
3. Ensure the field type is supported (int, bool, or a custom type in `CustomHashFunctions`).

Example:

```csharp
public class MySyncedTrait : ISync
{
    [VerifySync]
    public int Health;

    [VerifySync]
    public bool IsActive;
}
```

### Add custom hash support

If you need to sync a new struct type, add a custom hash function to `Sync.CustomHashFunctions` and make it stable across platforms. Do not use `GetHashCode` for structs unless you are certain it is deterministic.

### Debug desyncs

Enable `EnableSyncReports` in the lobby. After a desync, the game will generate a sync report. Compare the reports from two clients to find the first object whose hash differs.

### Mark code as unsynced

Use `Sync.RunUnsynced` to wrap code that reads world state but does not change it. This is useful for AI, UI, audio, and rendering. If the code accidentally mutates state, the sync check will catch it.

![Common pitfalls  guardrails diagram](images/Part_09_Chapter_03_Sync_Hashing-checklist-infographic-style-diagram-summarizing-the-top-pitf-fb069e.svg)

## Common Pitfalls / Guardrails


- **Do not use `GetHashCode` for custom types:** default .NET hash codes are not deterministic across platforms or runs. Use the custom hash functions in `Sync.cs`.
- **Floating point:** do not use `float` or `double` in synced state. Floating-point math can differ across CPUs and compilers. Use fixed-point math (`WPos`, `WDist`, `WAngle`, etc.).
- **Random sources:** only use `world.SharedRandom` inside simulation code. `world.LocalRandom` and `Game.CosmeticRandom` are for unsynced code.
- **Dictionaries and sets:** standard .NET dictionaries/sets have non-deterministic iteration order. Do not iterate over them in simulation code unless the order does not matter.
- **LINQ ordering:** ensure that any ordering in simulation code is stable. `OrderBy` with a non-unique key can produce non-deterministic order.
- **Culture:** string formatting and parsing can be culture-dependent. Use invariant culture when converting values that affect simulation.
- **Threading:** simulation code runs on a single thread. Do not spawn threads that touch simulation state.
- **Client-only code:** camera, audio, selection, and UI must not implement `ISync` and must not modify `ISync` state.
- **RunUnsynced reentry:** `RunUnsynced` can be nested. The sync hash check only runs at the outermost level.

## What to read next

- [Part 9.1 — OrderManager and Lockstep Foundation](Part_09_Chapter_01_OrderManager.md) for where `World.SyncHash()` is sent and compared each frame.
- [Part 8.1 — Bot Architecture and IBot](Part_08_Chapter_01_IBot.md) for how bot code is isolated from the sync hash using `RunUnsynced`.
- [Appendix D — Engine Conventions and Style](../appendices/Appendix_D_Engine_Conventions.md) for the full sync-safety coding guidelines.

## Summary

This chapter explains how OpenRA's sync-hash mechanism verifies that every client stays in lockstep during multiplayer games.

After reading this chapter, you should be able to:

- Casts the object to its concrete type.
- Initializes a hash accumulator to 0.
- For each `[VerifySync]` field, loads the field value and XORs it into the accumulator.
- For each `[VerifySync]` property, calls the getter and XORs the value.
- Returns the final hash.

If any of the concepts above feel unclear, review the relevant section before continuing. For source files and further reading, see the References section.


## References

- `OpenRA.Game/Sync.cs` — sync hash generation and guards.
- `OpenRA.Game/World.cs` — `SyncHash()` aggregation.
- `OpenRA.Game/Network/OrderManager.cs` — sync hash comparison.
- `OpenRA.Game/Network/SyncReport.cs` — sync report debugging.
- `OpenRA.Game/Traits/TraitsInterfaces.cs` — `ISync` interface.
- `OpenRA.Game/Traits/Player/Shroud.cs` — example synced trait.
- `OpenRA.Game/Traits/Player/FrozenActorLayer.cs` — example synced state.