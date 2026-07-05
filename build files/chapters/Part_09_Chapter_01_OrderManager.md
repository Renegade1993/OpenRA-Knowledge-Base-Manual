# Chapter 9.1 — OrderManager and Lockstep Foundation

## Purpose

This chapter is the canonical reference for OpenRA's lockstep order pipeline. It explains how the `[OrderManager](../appendices/Appendix_A_Glossary.md)` paces the simulation: collecting local orders, separating immediate and normal orders, sending normal orders over the network, buffering remote orders per frame, and dispatching them once every client is ready. It also covers the synchronization machinery (`localOrders`, `localImmediateOrders`, `pendingOrders`, `NetFrameNumber`, `LocalFrameNumber`, sync hashes, and disconnect markers) that keeps every client deterministic. For the anatomy of the `Order` message and the player order entry points that feed this pipeline, see [Part 1.3 — World, OrderManager, and Orders](Part_01_Chapter_03_World_Orders.md). For how bot modules construct and issue orders into the same pipeline, see [Part 8.4 — Bot Order Flow](Part_08_Chapter_04_Order_Flow.md).

## Learning Objectives


After studying this chapter, you should be able to:

1. Explain the client-server lockstep model and why only orders cross the network.
2. Describe the purpose of `localOrders`, `localImmediateOrders`, `pendingOrders`, and `syncForFrame`.
3. Trace a local order from `World.IssueOrder` through serialization, sending, receiving, and processing.
4. Explain how `NetFrameNumber` and `LocalFrameNumber` pace the simulation and prevent one client from running ahead.
5. Contrast immediate orders with normal gameplay orders and give examples of each.
6. Describe how [sync hashes](../appendices/Appendix_A_Glossary.md) and defeat states are sent and compared to detect [desyncs](../appendices/Appendix_A_Glossary.md).
7. Explain how disconnect markers keep the simulation deterministic when a client leaves.

![Practical example: chat vs move in a multiplayer match diagram](images/Part_09_Chapter_01_OrderManager-end-to-end-worked-example-diagram-showing-the-inputs-interme-5fc6a2.svg)

## Practical Example: Chat vs. Move in a Multiplayer Match


Consider two actions that happen at roughly the same moment during a multiplayer match: a chat message and a move order.

1. **Chat message.** The player types a message and presses Enter. The UI creates an `Order` with `OrderString = "Chat"` and `IsImmediate = true`. `OrderManager.IssueOrder` places it in `localImmediateOrders`.
2. **Immediate send.** `TickImmediate()` calls `SendImmediateOrders()` and the chat packet is sent to the server right away. `ReceiveAllOrdersAndCheckSync()` delivers the packet to all clients on the current frame.
3. **Immediate process.** `UnitOrders.ProcessOrder` handles the chat order, displaying the text in the in-game chat panel. Because the chat is immediate, it does not affect the lockstep simulation state.
4. **Move order.** The player right-clicks on the ground. The UI creates an `Order` with `OrderString = "Move"`, `IsImmediate = false`, and `Target` set to the destination cell.
5. **Local buffering.** `OrderManager.IssueOrder` places the move order in `localOrders` instead of `localImmediateOrders`.
6. **Frame-locked submission.** At the end of the net frame, `SendOrders()` serializes the move order and sends it to the server tagged with `NetFrameNumber`.
7. **Server relay.** The server forwards the move order to every other client. Each client stores it in `pendingOrders` keyed by the issuing client index and the frame number.
8. **Ready check.** Before advancing, `OrderManager` checks `IsReadyForNextFrame`. If any client has not yet submitted an order packet for the current frame, the simulation stalls.
9. **Lockstep execution.** Once all packets are present, `ProcessOrders()` dequeues each client's packet for the frame, calls `UnitOrders.ProcessOrder` for the move order, and increments `NetFrameNumber`.
10. **Sync verification.** After processing the frame, the client computes `World.SyncHash()` and a defeat-state bitmask, then sends them to the server via `Connection.SendSync`. The server compares them with the values from other clients; a mismatch triggers an out-of-sync warning.

This example shows how two superficially similar "player inputs" follow completely different paths: chat is immediate and visible, while movement is deterministic and replayable.

## Files

| File | Responsibility |
| :---- | :---- |
| `OpenRA.Game/Network/OrderManager.cs` | Central order buffering, frame pacing, sync hash verification. |
| `OpenRA.Game/Network/Order.cs` | `Order` object, serialization, deserialization. |
| `OpenRA.Game/Network/OrderIO.cs` | Order packet packing and unpacking. |
| `OpenRA.Game/Network/UnitOrders.cs` | System-level order handlers (pause, chat, game state, etc.). |
| `OpenRA.Game/Network/ReplayConnection.cs` | Replays saved orders as if they came from the network. |
| `OpenRA.Game/Network/Connection.cs` | Base network connection abstraction. |
| `OpenRA.Game/Server/Server.cs` | Server-side order relay and game state management. |
| `OpenRA.Game/Server/OrderBuffer.cs` | Server-side buffering of client orders per frame. |
| `OpenRA.Game/World.cs` | `IssueOrder` wrapper, `SyncHash` computation. |
| `OpenRA.Game/Sync.cs` | Sync hash generation for `ISync` objects and `RunUnsynced` guard. |

![Architecture diagram](images/Part_09_Chapter_01_OrderManager-architecture-diagram-showing-the-main-classes-interfaces-and-9161e6.svg)

## Architecture


### Client-server lockstep

```
[Client A] --orders--> [Server] --orders--> [Client B]
[Client B] --orders--> [Server] --orders--> [Client A]
```

Every simulation frame, each client sends a packet containing its orders. The server collects packets from all clients and relays them. A client does not advance the simulation until it has received an order packet for the current frame from every other client. This is the **lockstep** model.

### OrderManager state

`OrderManager` maintains:

- `localOrders` — orders generated by the local player/bot this frame.
- `localImmediateOrders` — orders that are processed immediately (chat, pause, system).
- `pendingOrders` — per-client queues of order packets, indexed by frame.
- `syncForFrame` — remote sync hashes used to detect desyncs.
- `NetFrameNumber` — the next frame to execute.
- `LocalFrameNumber` — the next frame for which local orders will be sent.

### Frame pacing

The simulation runs at a fixed `World.Timestep` (usually 40 ms per frame). The order manager can run ahead of the simulation, but it will stall if it is waiting for orders from other clients. The `SuggestedTimestep` can be scaled by the server to slow down the game when clients are struggling.

![Data flow  code path diagram](images/Part_09_Chapter_01_OrderManager-sequence-flow-diagram-tracing-the-execution-path-from-trigge-035864.svg)

## Data Flow / Code Path


> This section is the canonical explanation of the order lockstep, buffering, serialization, and frame-advance path. [Part 1.3 — World, OrderManager, and Orders](Part_01_Chapter_03_World_Orders.md) and [Part 8.4 — Bot Order Flow](Part_08_Chapter_04_Order_Flow.md) intentionally defer to this chapter for the full client-to-simulation details.

### Local order generation

When a player clicks or a bot ticks, the game calls `World.IssueOrder(order)`:

```csharp
public void IssueOrder(Order o) { OrderManager.IssueOrder(o); }
```

`OrderManager.IssueOrder` separates immediate and normal orders:

```csharp
public void IssueOrder(Order order)
{
    if (order.IsImmediate)
        localImmediateOrders.Add(order);
    else
        localOrders.Add(order);
}
```

### Sending orders

At the end of each net frame, the order manager sends the local orders to the server:

```csharp
void SendOrders()
{
    if (GameStarted && GameSaveLastFrame < NetFrameNumber && sentOrdersFrame < NetFrameNumber)
    {
        Connection.Send(NetFrameNumber, localOrders);
        localOrders.Clear();
        sentOrdersFrame = NetFrameNumber;
    }
}
```

The order packet is serialized using `Order.Serialize` and the bit-field flags from `OrderFields`.

### Receiving orders

The server sends back order packets tagged by frame and client. The client stores them:

```csharp
public void ReceiveOrders(int clientId, (int Frame, OrderPacket Orders) orders)
{
    if (pendingOrders.TryGetValue(clientId, out var queue))
        queue.Enqueue((orders.Frame, orders.Orders));
    else
        throw new InvalidDataException($"Received packet from disconnected client '{clientId}'");
}
```

### Ready check

A client is ready for the next frame only when it has received an order packet for the current frame from every other client:

```csharp
bool IsReadyForNextFrame => GameStarted && pendingOrders.All(p => p.Value.Count > 0);
```

Even if a client has no orders, it still sends an empty packet so that the other clients can advance.

### Order processing

When ready, the order manager processes all orders for the current frame:

![Order processing](images/Part_09_Chapter_01_OrderManager-ProcessOrders-flow.svg)
After processing, the client sends its own sync hash and defeat state to the server for comparison.

### Sync hash verification

Remote sync hashes are compared in `ReceiveSync`:

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

If two clients disagree, the game is marked out of sync and typically cannot continue.

![Configuration (yaml) diagram](images/Part_09_Chapter_01_OrderManager-annotated-yaml-snippet-diagram-showing-the-key-fields-and-ho-6a1b98.svg)

## Configuration (YAML)


There are no direct YAML controls for the OrderManager. However, the following settings influence it:

- `Game.Settings.Debug.SyncCheckUnsyncedCode` — whether `RunUnsynced` should verify sync hashes.
- `Game.Settings.Debug.SyncCheckBotModuleCode` — whether bot module code runs inside a sync check.
- `World.Timestep` — the simulation frame interval in milliseconds.

## Interconnectivity

- **Depends on:** [Part 1.3 — World, OrderManager, and Orders](Part_01_Chapter_03_World_Orders.md) (World, OrderManager, and Orders), [Part 1.1 — ECS, Actors, and Traits](Part_01_Chapter_01_ECS.md) (Actor traits), [Part 2.1 — MiniYaml Parser](Part_02_Chapter_01_MiniYaml.md) (MiniYaml), [Part 8.4 — Bot Order Flow](Part_08_Chapter_04_Order_Flow.md) (Bot Order Flow).
- **Used by:** [Part 9.2 — Server and Connection Layer](Part_09_Chapter_02_Server_Connection.md) (Server/Connection), [Part 9.3 — Sync Hashing and Determinism](Part_09_Chapter_03_Sync_Hashing.md) (Sync Hashing), [Part 1.2 — Activity System](Part_01_Chapter_02_Activities.md) (Activities execute orders), [Part 8.1 — Bot Architecture and IBot](Part_08_Chapter_01_IBot.md) (ModularBot uses orders).

![Algorithms diagram](images/Part_09_Chapter_01_OrderManager-algorithm-diagram-or-pseudocode-flowchart-for-the-non-trivia-5983ed.svg)

## Algorithms


### Order packet serialization

`Order.Serialize` writes a compact binary packet:

1. Order name string.
2. `OrderFields` bit flags.
3. Subject actor ID (if `Subject` flag).
4. Target type and data (if `Target` flag).
5. Target string (if `TargetString` flag).
6. Queued flag (if set).
7. Extra actors, location, data (if respective flags set).
8. Grouped actors (if `Grouped` flag).

This format keeps the per-frame network traffic small.

### Network frame pacing

`OrderManager.TryTick` decides whether the simulation can advance:

```csharp
if (IsNetFrame)
{
    shouldTick = pendingOrders.All(p => p.Key == Connection.LocalClientId || p.Value.Count > 0);

    if (shouldTick)
        SendOrders();

    willTick = IsReadyForNextFrame;
}
```

If the local client is not ready, `willTick` is false and the simulation stalls.

### Disconnect handling

When a client disconnects, the server inserts a special disconnect marker for the next frame. All clients process `World.OnClientDisconnected(clientId)` on the same frame, keeping the simulation deterministic.

### Immediate orders

Immediate orders bypass the lockstep queue. They are sent and processed on the current frame. This is used for chat messages, pause toggles, and system commands that do not affect the deterministic simulation.

![Extension points diagram](images/Part_09_Chapter_01_OrderManager-extension-hook-diagram-showing-the-interface-s-to-implement-b4a27b.svg)

## Extension Points


### Add a new order handler

Order handlers are typically implemented as traits implementing `IResolveOrder` or as methods in `UnitOrders` for system commands. The order string is matched to the handler.

### Add a new order type

For most gameplay commands, the existing `OrderType.Fields` is sufficient. For system-level commands, you can add a new `OrderType` value and extend `Order.Serialize`/`Deserialize`. This is rarely needed.

### Custom network connection

Implement `IConnection` to replace the default network layer. This is how `ReplayConnection` replays saved games and how unit tests can simulate network traffic.

### Sync report generation

When `generateSyncReport` is true, the order manager records the state of every synced object each frame. This is used for debugging desyncs.

![Common pitfalls  guardrails diagram](images/Part_09_Chapter_01_OrderManager-checklist-infographic-style-diagram-summarizing-the-top-pitf-fb069e.svg)

## Common Pitfalls / Guardrails


- **Deterministic execution:** every order must produce the same result on every client. Do not use `Game.CosmeticRandom` or `world.LocalRandom` in order resolution.
- **Order timing:** orders are processed at the beginning of the frame. The world state at that moment is the state all clients have.
- **Empty packets:** a client must send a packet even if it has no orders, or the other clients will stall.
- **Immediate orders:** do not mark gameplay orders as immediate, or they will bypass the lockstep and may cause desyncs.
- **Sync hash changes:** only fields marked with `[Sync]` or `[VerifySync]` contribute to the sync hash. If you add a state that affects gameplay, mark it appropriately.
- **Bot order isolation:** bot code runs unsynced via `Sync.RunUnsynced`. The orders it issues are the only sync-crossing data.

## What to read next

- [Part 9.2 — Server and Connection Layer](Part_09_Chapter_02_Server_Connection.md) for the server-side relay and connection layer that sits behind `OrderManager`.
- [Part 9.3 — Sync Hashing and Determinism](Part_09_Chapter_03_Sync_Hashing.md) for how `World.SyncHash()` is generated and compared.
- [Part 1.3 — World, OrderManager, and Orders](Part_01_Chapter_03_World_Orders.md) for the anatomy of an `Order` and the player/bot entry points that feed this pipeline.
- [Part 8.4 — Bot Order Flow](Part_08_Chapter_04_Order_Flow.md) for how bot modules construct and queue orders into `OrderManager`.

## Summary

This chapter is the canonical reference for OpenRA's lockstep order pipeline. It explains how OpenRA's [OrderManager](../appendices/Appendix_A_Glossary.md) coordinates the deterministic multiplayer lockstep loop: collecting, sending, buffering, and dispatching orders so that every client advances the simulation in perfect sync.

After reading this chapter, you should be able to:

- Explain the client-server lockstep model and why only orders cross the network.
- Describe the purpose of `localOrders`, `localImmediateOrders`, `pendingOrders`, and `syncForFrame`.
- Trace a local order from `World.IssueOrder` through serialization, sending, receiving, and processing.
- Explain how `NetFrameNumber` and `LocalFrameNumber` pace the simulation and prevent one client from running ahead.
- Contrast immediate orders with normal gameplay orders and give examples of each.
- Describe how [sync hashes](../appendices/Appendix_A_Glossary.md) and defeat states are sent and compared to detect [desyncs](../appendices/Appendix_A_Glossary.md).
- Explain how disconnect markers keep the simulation deterministic when a client leaves.

If any of the concepts above feel unclear, review the relevant section before continuing. For source files and further reading, see the References section.


## References

- `OpenRA.Game/Network/OrderManager.cs` — order coordination.
- `OpenRA.Game/Network/Order.cs` — order object and serialization.
- `OpenRA.Game/Network/OrderIO.cs` — packet I/O.
- `OpenRA.Game/Network/UnitOrders.cs` — system order handlers.
- `OpenRA.Game/Network/Connection.cs` — connection abstraction.
- `OpenRA.Game/Server/Server.cs` — server relay.
- `OpenRA.Game/Server/OrderBuffer.cs` — server-side buffering.
- `OpenRA.Game/World.cs` — sync hash and `IssueOrder`.
- `OpenRA.Game/Sync.cs` — sync hash generation and unsynced guards.


### External resources

- [OpenRA main site](https://www.openra.net)