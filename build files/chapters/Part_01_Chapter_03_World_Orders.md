# Chapter 1.3 — World, OrderManager, and Orders

## Purpose

This chapter explains the anatomy of an `Order` from the UI/player perspective: what an `Order` is, what fields it carries, how mouse clicks and hotkeys are converted into an `Order`, and the boundary between the unsynced UI and the synced simulation. It also introduces `World` as the simulation container that owns the authoritative state and `OrderManager` as the gatekeeper that orders pass through, but the full lockstep pipeline, serialization, and frame-pacing details are intentionally left to [Part 9.1 — OrderManager and Lockstep Foundation](Part_09_Chapter_01_OrderManager.md). For how bot modules construct orders, see [Part 8.4 — Bot Order Flow](Part_08_Chapter_04_Order_Flow.md).

At a high level, `World` owns the authoritative game state; `Order` is the only thing that can change that state during a match; and `OrderManager` is the gatekeeper that decides *when* each `Order` may be applied so that every client stays in lock-step. This chapter is the place to learn the shape of the `Order` message and the player-facing entry points that create it.

## Learning Objectives


After studying this chapter, you should be able to:

1. Explain the distinct responsibilities of `World`, `Order`, and `OrderManager` at a high level.
2. Describe the actor lifecycle, including `ActorID` allocation and the role of `TraitDictionary`.
3. Identify the key fields of the `Order` class and how they encode a player intent (command, target, payload, queueing, and visual feedback).
4. Trace the high-level path from a player click or bot decision through `World.IssueOrder` to the traits that change world state.
5. Contrast immediate orders (`IsImmediate`) with lockstep gameplay orders and explain why the UI/order boundary matters.
6. Use `World` queries such as `ActorsWithTrait<T>()` and `ActorsHavingTrait<T>()` to inspect simulation state.

![Practical example: issuing an attack order diagram](images/Part_01_Chapter_03_World_Orders-end-to-end-worked-example-diagram-showing-the-inputs-interme-5fc6a2.svg)

## Practical Example: Issuing an Attack Order


When a player selects a tank and orders it to attack an enemy unit:

1. **Input detection.** The viewport captures the right-click and the selection system knows the active player owns the selected tank.
2. **Order generation.** The active `IOrderGenerator` creates an `Order` with `OrderString = "Attack"`, `Subject` set to the tank, and `Target` pointing to the enemy actor.
3. **World forwards the order.** `World.IssueOrder(order)` delegates to `OrderManager.IssueOrder(order)`.
4. **Lockstep pipeline.** The order enters the `OrderManager` lockstep pipeline. For the full path from client to simulation, see [Part 9.1 — OrderManager and Lockstep Foundation](Part_09_Chapter_01_OrderManager.md).
5. **Actor behavior.** The tank's `Attack` trait receives the order and creates an `Attack` [Activity](../appendices/Appendix_A_Glossary.md), which is queued on the [Actor](../appendices/Appendix_A_Glossary.md)'s activity stack and ticks every simulation frame until the enemy is destroyed or the order is cancelled.

This example shows how a single player action is transformed into a deterministic, replayable, network-synchronized change in world state.

## Files

- `OpenRA.Game/World.cs`
- `OpenRA.Game/Network/OrderManager.cs`
- `OpenRA.Game/Network/Order.cs`
- `OpenRA.Game/Network/UnitOrders.cs`
- `OpenRA.Game/GameRules/ActorInfo.cs`
- `OpenRA.Mods.Common/Traits/Player/ModularBot.cs`

![Architecture diagram](images/Part_01_Chapter_03_World_Orders-architecture-diagram-showing-the-main-classes-interfaces-and-9161e6.svg)

## Architecture


### The `World` as the Simulation Container

`World` is the root object of every running simulation. It is constructed once when a map starts and is owned by `Game.OrderManager.World` after `Game.StartGame` creates it. The class is `sealed` and `IDisposable` because it owns resources such as the map, the sound subsystem, and the `OrderManager` for shellmaps.

Key responsibilities of `World`:

1. **Actor lifecycle.** It maintains the canonical `SortedDictionary<uint, Actor> actors`, allocates `ActorID`s via `NextAID()`, and provides `CreateActor`, `Add`, and `Remove`.
2. **[Trait](../appendices/Appendix_A_Glossary.md) dictionaries.** `internal readonly TraitDictionary TraitDict` is the fast lookup structure used by all `ActorsWithTrait<T>`, `ActorsHavingTrait<T>`, and `ApplyToActorsWithTrait<T>` helpers.
3. **Effects.** `List<IEffect>` stores projectiles, explosions, beacon markers, and similar transient objects. Effects can optionally be spatially partitioned or synced.
4. **Player state.** `Player[] Players`, `LocalPlayer`, and `RenderPlayer` track who owns what and whose view is currently being rendered.
5. **Ticking.** `World.Tick()` is the heart of the simulation: every logic frame it increments `WorldTick`, ticks all actors, ticks all `ITick` traits, ticks effects, and finally drains `frameEndActions`.
6. **Rules lookup.** `World` does not store the rules itself; it uses `Map.Rules` (e.g., `Map.Rules.Actors`). The `Actor` constructor looks up `world.Map.Rules.Actors[name]` to get the `ActorInfo` used to instantiate traits.

`World` is created in one of three modes (`WorldType` enum):

- `Regular` — a normal game or replay.
- `Shellmap` — the background menu map.
- `Editor` — the map editor; uses `SystemActors.EditorWorld` instead of `SystemActors.World`.

### What an `Order` Is

An `Order` (`OpenRA.Game/Network/Order.cs`) is a serializable message that represents a single, deterministic, replayable input. It is the only way the game state is allowed to change during a networked match. The class is deliberately simple: a string `OrderString`, a `Subject` actor, a `Target`, a `TargetString`, flags such as `Queued`, and several payload fields.

Key fields:

- `OrderString` — the command name (e.g., `"Move"`, `"Attack"`, `"StartProduction"`, `"Chat"`, `"PauseGame"`).
- `Subject` — the actor that should resolve the order. `Player` is derived from `Subject.Owner`.
- `Target` — a `Target` struct describing the order target (actor, frozen actor, or terrain/cell position).
- `TargetString` — a free-form string payload, used for chat text, production queue item names, MiniYaml save data, and similar.
- `ExtraData` — an unsigned 32-bit integer payload.
- `ExtraActors` — additional actors involved in the order (e.g., a group selection or a multi-actor command).
- `ExtraLocation` — a `CPos` payload.
- `Queued` — whether the order should be queued behind existing orders (e.g., shift-queue movement).
- `GroupedActors` — if set, `UnitOrders.ProcessOrder` fans the order out to every actor in this array.
- `IsImmediate` — if true, the order bypasses the frame-locked network scheduler and is processed as soon as it is received (chat, pause, server messages, etc.).
- `SuppressVisualFeedback` — used by scripted or bot orders to avoid generating cursor effects.
- `Type` — `OrderType.Fields` for gameplay orders; special values such as `Handshake`, `SyncHash`, `Ping`, etc., are used by the network layer.

`Order` has a rich set of named constructors:

- `Order.Chat(string text, uint teamNumber)` — immediate chat order.
- `Order.FromTargetString(...)` — generic orders that only carry a string payload.
- `Order.StartProduction`, `PauseProduction`, `CancelProduction` — production-related orders.
- `Order.FromGroupedOrder(...)` — re-targets a group order to a single actor.

`Order` is serialized with a versioned binary format (`ProtocolVersion.Orders`). For the exact bit layout, `OrderFields` flags, and lockstep transmission path, see [Part 9.1 — OrderManager and Lockstep Foundation](Part_09_Chapter_01_OrderManager.md).

### The `OrderManager` as the Lockstep Gatekeeper

`OrderManager` (`OpenRA.Game/Network/OrderManager.cs`) is the network client that sits between `World` and the underlying `IConnection`. It owns the local `World` reference, the connection (which may be a `NetworkConnection`, `ReplayConnection`, `EchoConnection`, etc.), and the order queues that keep the game deterministic.

Its primary job is to accept every order issued by the local player, bot, or script via `World.IssueOrder`, separate immediate orders from normal orders, and submit the normal orders to the lockstep network scheduler. For the full algorithm, including `localOrders`, `localImmediateOrders`, `pendingOrders`, `NetFrameNumber`, `LocalFrameNumber`, sync hashes, and disconnect handling, see [Part 9.1 — OrderManager and Lockstep Foundation](Part_09_Chapter_01_OrderManager.md).

![Data flow  code path diagram](images/Part_01_Chapter_03_World_Orders-sequence-flow-diagram-tracing-the-execution-path-from-trigge-035864.svg)

## Data Flow / Code Path


### From a Player Click to a World-State Change

1. **Input is converted to an `Order`.** The UI uses `IOrderGenerator` implementations (e.g., `GenericSelectTarget`, `OrderGenerator`) to decide what command the player is issuing. The active order generator returns an `Order` (or many orders) via `World.IssueOrder`.
2. **World forwards to the manager.** `World.IssueOrder(Order o)` is a thin wrapper that hides the manager from mod code: `OrderManager.IssueOrder(o)`.
3. **Manager routes the order.** `OrderManager.IssueOrder` separates immediate orders from normal orders. Normal orders enter the lockstep pipeline. For the full frame-by-frame path, see [Part 9.1 — OrderManager and Lockstep Foundation](Part_09_Chapter_01_OrderManager.md).
4. **Orders are dispatched to the world.** When the agreed frame is reached, `OrderManager.ProcessOrders` calls `UnitOrders.ProcessOrder` for each order. `UnitOrders.ResolveOrder` validates the order and calls `Actor.ResolveOrder`.
5. **Actor distributes the order to its traits.** `Actor.ResolveOrder` iterates over the `IResolveOrder[]` array and invokes `r.ResolveOrder(this, order)` for every trait that implements the interface (e.g., `Mobile`, `AttackMove`, `ProductionQueue`). This is the actual state change.
6. **The world is ticked.** `Game.InnerLogicTick` calls `world.Tick()`, which advances `WorldTick`, ticks every actor, and drains `frameEndActions`.

### Bot and Lua Orders

Bots and Lua scripts do not call the UI order generators. Instead, they create `Order` objects directly and queue them:

- **Bots:** `ModularBot` implements `IBot.QueueOrder(Order order)`. It stores orders in a local `Queue<Order>`. On each tick, `ModularBot.Tick` calls `world.IssueOrder(orders.Dequeue())` for a configurable fraction of the queue. The bot path is described in [Part 8.4 — Bot Order Flow](Part_08_Chapter_04_Order_Flow.md).
- **Lua:** The Lua API can call `World.IssueOrder` directly. Scripting orders are therefore recorded and synced like normal orders.

This is why bot and Lua orders are deterministic and appear in replays: they are issued through the same `World.IssueOrder` path as human orders.

### Grouped Orders

When a group of actors is selected, the order generator typically creates one `Order` with `GroupedActors` set to the selected actors. `UnitOrders.ProcessOrder` detects this and fans it out:

```csharp
if (order.GroupedActors == null)
    ResolveOrder(order, world, orderManager, clientId);
else
    foreach (var subject in order.GroupedActors)
        ResolveOrder(Order.FromGroupedOrder(order, subject), world, orderManager, clientId);
```

`Order.FromGroupedOrder` creates a clone with the individual actor as the `Subject`. This avoids sending one packet per selected unit while still allowing each actor to resolve the order independently.

### Immediate vs. Normal Orders

The distinction is fundamental to both networking and gameplay:

| Aspect | Normal Order | Immediate Order |
|--------|-------------|-----------------|
| Lockstep path | Queued in the lockstep pipeline and executed on the agreed net frame | Processed immediately, outside the lockstep frame loop |
| Determinism | Deterministic and synced across all clients | Not deterministic (may arrive on different clients at different local frames) |
| Typical uses | Move, Attack, Build, Sell, Set Rally Point | Chat, Pause, Server messages, Handshake, Game save metadata |

For the exact buffering, network timing, and dispatch logic, see [Part 9.1 — OrderManager and Lockstep Foundation](Part_09_Chapter_01_OrderManager.md).

Because immediate orders are not frame-locked, they must never change simulation state. The engine uses them for UI notifications, chat, pause toggles, and server administration. If a modder accidentally sets `IsImmediate = true` on a gameplay order, the clients will diverge and the game will desync.

Conversely, if a normal order is used for something that should be instantaneous (e.g., a chat message), every client will wait until the next net frame before seeing it, which feels laggy.

![Configuration (yaml) diagram](images/Part_01_Chapter_03_World_Orders-annotated-yaml-snippet-diagram-showing-the-key-fields-and-ho-6a1b98.svg)

## Configuration (YAML)


There is no direct YAML configuration for `World`, `OrderManager`, or `Order` themselves. However, they are deeply shaped by YAML rules:

- **Actor definitions** (`ActorInfo`) come from the mod YAML and the map YAML. `World` only knows about these through `Map.Rules`.
- **Game speed** (`GameSpeed`) is chosen from the `gamespeed` lobby option in the `World` constructor and determines `World.Timestep`.
- **Net frame interval** (`LobbyInfo.GlobalSettings.NetFrameInterval`) controls how often the order manager synchronizes clients. See [Part 9.1 — OrderManager and Lockstep Foundation](Part_09_Chapter_01_OrderManager.md) for how `OrderManager` uses it.
- **[Order](../appendices/Appendix_A_Glossary.md) strings** are arbitrary strings defined by traits. For example, `"Move"`, `"Attack"`, `"DeployTransform"`, and `"StartProduction"` are order names that any trait can implement. There is no central registry; the contract is between the order generator and the `IResolveOrder` trait.
- **Default order generator** is named in `mod.yaml` via `DefaultOrderGenerator` and instantiated by `World`.

Because `Order.OrderString` is free-form, mods can add new order types without changing the engine, provided that:

1. Some order generator (UI, bot, or Lua) produces the order string.
2. Some actor trait implements `IResolveOrder` and handles that string.

## Interconnectivity

### `World` ↔ `OrderManager`

- `World` is created with an `OrderManager` reference and `World.IssueOrder` delegates to `OrderManager.IssueOrder`.
- `OrderManager` owns the authoritative `World` reference and calls `World.Tick()` indirectly via `Game.InnerLogicTick`.
- `OrderManager.ProcessOrders` calls `World.SyncHash()` and `World.OnClientDisconnected`.
- `World.Dispose` disposes the shellmap `OrderManager` because shellmaps own their own manager.
- See [Part 9.1 — OrderManager and Lockstep Foundation](Part_09_Chapter_01_OrderManager.md) for the order scheduling, serialization, and network transport details.

### `World` ↔ `Map` / `ActorInfo`

- `World.Map` is passed to the constructor. `Map.Rules` contains `ActorInfo` objects for every actor type in the current mod/map.
- `World.CreateActor` constructs an `Actor` with the actor name and a `TypeDictionary` of initializers. The `Actor` constructor uses `world.Map.Rules.Actors[name]` to fetch the `ActorInfo` and instantiate its traits.
- `World.OrderValidators` is initialized from the `WorldActor` traits implementing `IValidateOrder`. These validators are invoked before every gameplay order resolves.

### `OrderManager` ↔ `IConnection`

- `OrderManager` is transport-agnostic. `IConnection` is responsible for sending/receiving order packets and sync frames.
- Concrete implementations include `NetworkConnection`, `ReplayConnection`, `EchoConnection`, and `OrderManagerConnection` for local/replay playback.
- `Connection.Receive(this)` routes incoming packets into `ReceiveOrders`, `ReceiveImmediateOrders`, `ReceiveSync`, or `ReceiveDisconnect`.
- See [Part 9.1 — OrderManager and Lockstep Foundation](Part_09_Chapter_01_OrderManager.md) for the serialization and lockstep protocol.

### `World` ↔ `Sync`

- `World.SyncHash()` is the deterministic fingerprint of the entire world. It hashes:
  - All actors by `ActorID`.
  - All `ISync` traits on actors via `actor.SyncHashes`.
  - All synced effects (`SyncedEffects`).
  - The shared random generator.
  - Render-player unlock status.
- `OrderManager.ProcessOrders` sends this hash to the server via `Connection.SendSync` once per net frame. See [Part 9.3 — Sync Hashing and Determinism](Part_09_Chapter_03_Sync_Hashing.md) for sync verification.

### `Order` ↔ `Actor` / `ActorInfo`

- `Order.Subject` is an `Actor` instance. `Order` serialization uses `ActorID` and `world.GetActorById` for deserialization.
- `Actor.ResolveOrder` distributes the order to `IResolveOrder` traits.
- `ActorInfo` describes which traits exist on an actor type, which determines which `IResolveOrder` handlers are available.

![Algorithms diagram](images/Part_01_Chapter_03_World_Orders-algorithm-diagram-or-pseudocode-flowchart-for-the-non-trivia-5983ed.svg)

## Algorithms


### ActorInfo Trait Resolution

`ActorInfo.TraitsInConstructOrder()` is a dependency-resolution algorithm that sorts trait infos based on the `Requires<T>` and `NotBefore<T>` interfaces they implement. It works in passes:

1. Start with all traits that have no dependencies.
2. Repeatedly find traits whose dependencies are already resolved and whose optional-dependency peers are also resolved.
3. If any trait remains unresolved, throw an exception listing missing and unresolved dependencies.

This guarantees that when an actor is created, its traits are initialized in a valid order (e.g., `Health` before `SelectionDecorations`, `Mobile` before `AttackMove`).

![Extension points diagram](images/Part_01_Chapter_03_World_Orders-extension-hook-diagram-showing-the-interface-s-to-implement-b4a27b.svg)

## Extension Points


The following extension points are the normal way mods and new engine features interact with the world/order system:

1. **`IResolveOrder`** (`OpenRA.Game/Traits/TraitsInterfaces.cs`) — Implement on a trait to handle a gameplay order. Example: `Mobile` handles `"Move"`, `AttackMove` handles `"AttackMove"`.
2. **`IIssueOrder`** — Implement on a trait to expose orders that the cursor/order-generator system can issue. `IssueOrder` returns an `Order` object for a given target.
3. **`IOrderTargeter`** — Implement to define how the mouse cursor targets an actor or cell and what modifiers are supported.
4. **`IValidateOrder`** — Implement on the `WorldActor` to reject illegal orders before they reach `Actor.ResolveOrder`. Used for cheat prevention and sanity checks.
5. **`ISync`** (`OpenRA.Game/Sync.cs`) — Implement and mark fields/properties with `[VerifySync]` to include the object in the sync hash. Required for any state that affects gameplay determinism.
6. **`INotifyAddedToWorld`** / **`INotifyRemovedFromWorld`** — React to actor lifecycle events.
7. **`IWorldLoaded`** / **`IPostWorldLoaded`** — Run one-time setup after the world is created.
8. **Custom `IOrderGenerator`** — Replace or extend the default order generator to create new input modes (e.g., directional support powers, target-area selection).
9. **Custom `IConnection`** — Implement a new transport or replay format for orders. See [Part 9.1 — OrderManager and Lockstep Foundation](Part_09_Chapter_01_OrderManager.md) for the network layer details.
10. **Custom `ActorInfo` rules** — Add new actor types, traits, and order strings in YAML without changing C# if matching trait/order handlers exist.

![Common pitfalls  guardrails diagram](images/Part_01_Chapter_03_World_Orders-checklist-infographic-style-diagram-summarizing-the-top-pitf-fb069e.svg)

## Common Pitfalls / Guardrails


- **Changing the order protocol.** `Order.Serialize`/`Deserialize` use `ProtocolVersion.Orders`. If you change the binary format, you must bump the protocol version; otherwise, clients will corrupt each other's orders. See [Part 9.1 — OrderManager and Lockstep Foundation](Part_09_Chapter_01_OrderManager.md) for the packet format.
- **Forgetting `IsImmediate`.** A normal order is not visible until the next net frame. If you want a chat or pause effect to happen right away, set `IsImmediate = true`.
- **Using `IsImmediate` for gameplay.** Never mark an order that changes simulation state as immediate. It will be processed at different local times on each client and will cause a [Desync](../appendices/Appendix_A_Glossary.md).
- **Using `CosmeticRandom` for gameplay.** `World.SharedRandom` is the deterministic RNG; `Game.CosmeticRandom` is unsynced and must only be used for visual or UI effects.
- **Mutating state in unsynced code.** `Sync.RunUnsynced` is used for UI, bot, and input code. It can optionally assert that the world sync hash does not change. If it does, an exception is thrown. This prevents accidental state changes from code that is supposed to be side-effect-free.
- **Missing `[VerifySync]`.** Only fields/properties with this attribute are included in the sync hash. If a gameplay-relevant field is unmarked, a desync will not be detected immediately and will cause a mismatch later.
- **Non-deterministic trait initialization.** `ActorInfo` requires `Requires<T>` and `NotBefore<T>` to be declared correctly. Missing dependencies throw a `YamlException` from `TraitsInConstructOrder()`.
- **Assuming `order.Subject` is alive.** `UnitOrders.ResolveOrder` checks `IsDead` before resolving. Handlers should still be defensive because the actor may have died between order creation and execution.
- **[World](../appendices/Appendix_A_Glossary.md) disposal order.** `World.Dispose()` disposes actors in reverse order, then drains `frameEndActions`, then optionally disposes the shellmap `OrderManager`. Disposing in the wrong order can leak map or sound resources.
- **Replay integrity.** Because bot orders are issued through the same path as human orders, they are recorded in the replay. If a bot's decision logic is not deterministic, replays will desync even though the orders were recorded.

## What to read next

- If you want to understand how the lockstep network layer schedules orders, read [Part 9.1 — OrderManager and Lockstep Foundation](Part_09_Chapter_01_OrderManager.md).
- If you want to see how orders become multi-tick actor behavior, read [Part 1.2 — Activities and the Game Loop](Part_01_Chapter_02_Activities.md).
- If you want to learn how bots and AI issue orders, read [Part 8.4 — Bot Order Flow](Part_08_Chapter_04_Order_Flow.md).

## Summary

This chapter explains the anatomy of an `Order` from the player/UI perspective and the boundary between the unsynced world of input and the synced world of simulation. It introduces the `World` (the simulation container), the `Order` (the serialized intent that crosses the boundary), and the `OrderManager` (the gatekeeper that schedules orders), with an emphasis on the fields, construction, and entry points that turn a mouse click or hotkey into a deterministic, replayable state change.

After reading this chapter, you should be able to:

- Explain the distinct responsibilities of `World`, `Order`, and `OrderManager`.
- Describe the actor lifecycle, including `ActorID` allocation and the role of `TraitDictionary`.
- Identify the key fields of the `Order` class and how they affect targeting and queuing.
- Trace the high-level path from a player click or bot decision to a world-state change.
- Contrast immediate orders (`IsImmediate`) with lockstep gameplay orders.
- Use `World` queries such as `ActorsWithTrait<T>()` and `ActorsHavingTrait<T>()` to inspect simulation state.

If any of the concepts above feel unclear, review the relevant section before continuing. For source files and further reading, see the References section.


## References

- `OpenRA.Game/World.cs` — Simulation container, actor/effect ownership, tick loop, sync hash.
- `OpenRA.Game/Network/OrderManager.cs` — Order scheduling, network transport, sync reporting, frame pacing.
- `OpenRA.Game/Network/Order.cs` — `Order` message, serialization, named constructors.
- `OpenRA.Game/Network/UnitOrders.cs` — Order dispatch switch, group order fan-out, `IValidateOrder` gate.
- `OpenRA.Game/Sync.cs` — `ISync` interface, `[VerifySync]`, deterministic hash generation, `RunUnsynced` guard.
- `OpenRA.Game/GameRules/ActorInfo.cs` — Trait info container, dependency resolution, rules lookup.
- `OpenRA.Game/Actor.cs` — `ResolveOrder`, `SyncHashes`, trait array construction.
- `OpenRA.Game/Traits/TraitsInterfaces.cs` — `IResolveOrder`, `IIssueOrder`, `IOrderTargeter`, `IValidateOrder`.
- `OpenRA.Game/Game.cs` — `InnerLogicTick`, `LogicTick`, `StartGame`, `OrderManager` lifecycle.
- `OpenRA.Mods.Common/Traits/Player/ModularBot.cs` — Bot order queue and `World.IssueOrder` integration.