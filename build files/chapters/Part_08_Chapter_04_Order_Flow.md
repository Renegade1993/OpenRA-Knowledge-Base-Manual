# Chapter 8.4 — Bot Order Flow

## Purpose

This chapter focuses specifically on how [ModularBot](../appendices/Appendix_A_Glossary.md) and individual bot modules construct and issue [Order](../appendices/Appendix_A_Glossary.md) objects. It covers the path from a bot module decision through `IBot.QueueOrder` and `ModularBot.Tick` to `World.IssueOrder`, plus the throttling and visual-feedback suppression that are unique to bot orders. It intentionally does *not* re-explain the full lockstep pipeline or the complete field-by-field anatomy of an `Order`; for those, see [Part 9.1 — OrderManager and Lockstep Foundation](Part_09_Chapter_01_OrderManager.md) and [Part 1.3 — World, OrderManager, and Orders](Part_01_Chapter_03_World_Orders.md) respectively.

## Learning Objectives


After studying this chapter, you should be able to:

- Explain how bot orders enter the same lockstep pipeline as human orders.
- Describe the `Order` class fields and how they encode bot decisions.
- Trace an order from bot module construction through `ModularBot.QueueOrder` to `World.IssueOrder`.
- Understand `ModularBot`'s throttling logic and why it exists.
- Configure bot behavior indirectly through YAML-driven modules.
- Implement a new bot order that is compatible with the existing order pipeline.

## Files

| File | Responsibility |
| :---- | :---- |
| `OpenRA.Game/Network/Order.cs` | `Order` class, fields, serialization, named constructors. |
| `OpenRA.Game/Network/OrderManager.cs` | Receives and buffers orders per frame, sync hash checking. |
| `OpenRA.Game/World.cs` | `IssueOrder` wrapper around the order manager. |
| `OpenRA.Mods.Common/Traits/Player/ModularBot.cs` | Bot order queue and throttling. |
| `OpenRA.Mods.Common/Traits/BotModules/SquadManagerBotModule.cs` | Issues squad movement and attack orders. |
| `OpenRA.Mods.Common/Traits/BotModules/BaseBuilderBotModule.cs` | Issues building production and placement orders. |
| `OpenRA.Mods.Common/Traits/BotModules/UnitBuilderBotModule.cs` | Issues unit production orders. |
| `OpenRA.Mods.Common/Traits/BotModules/HarvesterBotModule.cs` | Issues harvest and dock orders. |
| `OpenRA.Mods.Common/Traits/SupportPowers/SupportPowerManager.cs` | Receives support power orders. |
| `OpenRA.Game/Network/UnitOrders.cs` | System-level order handlers (pause, handshake, game state). |
| `OpenRA.Game/Network/OrderIO.cs` | Low-level order packet read/write. |

![Architecture diagram](images/Part_08_Chapter_04_Order_Flow-architecture-diagram-showing-the-main-classes-interfaces-and-9161e6.svg)

## Architecture


### Order as the only cross-boundary message

```
[Bot Module] -> [Order] -> [ModularBot.QueueOrder] -> [ModularBot.Tick] -> [World.IssueOrder] -> [OrderManager] -> [Lockstep Pipeline] -> [Execution]
```

The `Order` class is the only object that leaves the unsynced bot module and enters the deterministic simulation. Everything about the bot's decision—the unit, the target, the command string—is encoded in this object. After `World.IssueOrder`, the order enters the same lockstep pipeline as a human order. For the full serialization, buffering, and frame-pacing details, see [Part 9.1 — OrderManager and Lockstep Foundation](Part_09_Chapter_01_OrderManager.md).

### Order fields in bot modules

Bot modules populate the same `Order` fields that the UI order generators do. For the complete field definitions and their semantic meaning, see [Part 1.3 — World, OrderManager, and Orders](Part_01_Chapter_03_World_Orders.md). The examples in the next section show how specific bot modules use those fields to encode a decision: for example, `TargetString` is set to the actor type to build, `ExtraData` often carries the production queue index, and `SuppressVisualFeedback` is set to true so bot orders do not spam selection brackets and target lines.

![Data flow  code path diagram](images/Part_08_Chapter_04_Order_Flow-sequence-flow-diagram-tracing-the-execution-path-from-trigge-035864.svg)

## Data Flow / Code Path


### Constructing an order in a module

Squad movement:

```csharp
owner.Bot.QueueOrder(new Order("AttackMove", null, owner.Target, false, groupedActors: owner.Units.ToArray()));
```

Building production:

```csharp
bot.QueueOrder(new Order("Build", factory, false)
{
    TargetString = buildingType,
    ExtraData = (uint)queueIndex
});
```

Unit production:

```csharp
bot.QueueOrder(new Order("StartProduction", factory, false)
{
    TargetString = unitType,
    ExtraData = (uint)queueIndex
});
```

Support power:

```csharp
bot.QueueOrder(new Order(sp.Key, supportPowerManager.Self, Target.FromCell(world, attackLocation.Value), false)
{
    SuppressVisualFeedback = true,
    ExtraData = uint.MaxValue
});
```

Each module constructs the exact `Order` that a human player would produce for the same action.

### Queuing in the bot

`ModularBot.QueueOrder` simply stores the order:

```csharp
void IBot.QueueOrder(Order order)
{
    orders.Enqueue(order);
}
```

### Throttling and issuing

During `ModularBot.Tick`, a subset of the queue is issued:

```csharp
var ordersToIssueThisTick = Math.Min((orders.Count + info.MinOrderQuotientPerTick - 1) / info.MinOrderQuotientPerTick, orders.Count);
for (var i = 0; i < ordersToIssueThisTick; i++)
    world.IssueOrder(orders.Dequeue());
```

`World.IssueOrder` forwards to the order manager:

```csharp
public void IssueOrder(Order o) { OrderManager.IssueOrder(o); }
```

At this point the bot order is indistinguishable from a human order. From here it follows the same lockstep path as human orders. For the exact serialization, server relay, ready check, and frame-pacing algorithm, see [Part 9.1 — OrderManager and Lockstep Foundation](Part_09_Chapter_01_OrderManager.md).

### Execution

Once the lockstep pipeline delivers the order (see [Part 9.1 — OrderManager and Lockstep Foundation](Part_09_Chapter_01_OrderManager.md) for the frame dispatch), `UnitOrders.ProcessOrder` resolves it by the `Subject` actor's traits or by the support power manager, exactly as it would be for a human order. For example, an `"AttackMove"` order with `GroupedActors` is resolved by the `AttackMove` [activity](../appendices/Appendix_A_Glossary.md) on each actor. See [Part 1.3 — World, OrderManager, and Orders](Part_01_Chapter_03_World_Orders.md) for the order-to-trait dispatch path.

![Configuration (yaml) diagram](images/Part_08_Chapter_04_Order_Flow-annotated-yaml-snippet-diagram-showing-the-key-fields-and-ho-6a1b98.svg)

## Configuration (YAML)


There are no direct YAML controls for the order flow itself. However, the behavior that flows through orders is entirely YAML-driven:

- `SquadManagerBotModule` parameters decide when and how many orders are generated.
- `BaseBuilderBotModule` and `UnitBuilderBotModule` decide which actors are produced.
- `SupportPowerBotModule` decides which powers are ordered and when.

## Interconnectivity

- **Depends on:** [Part 8.1 — Bot Architecture and IBot](Part_08_Chapter_01_IBot.md) (IBot and ModularBot), [Part 8.2 — Bot Modules](Part_08_Chapter_02_Bot_Modules.md) (Bot Modules), [Part 8.3 — Bot Squads and Combat Heuristics](Part_08_Chapter_03_Squads.md) (Squads), [Part 1.3 — World, OrderManager, and Orders](Part_01_Chapter_03_World_Orders.md) (World, Orders, and OrderManager), [Part 9.1 — OrderManager and Lockstep Foundation](Part_09_Chapter_01_OrderManager.md) (OrderManager and lockstep).
- **Used by:** [Part 9.1 — OrderManager and Lockstep Foundation](Part_09_Chapter_01_OrderManager.md) (network orders are the bridge between bot and simulation), [Part 1.2 — Activity System](Part_01_Chapter_02_Activities.md) (Activities execute the orders).

![Algorithms diagram](images/Part_08_Chapter_04_Order_Flow-algorithm-diagram-or-pseudocode-flowchart-for-the-non-trivia-5983ed.svg)

## Algorithms


### Grouped actor orders

For orders that affect multiple units, the `GroupedActors` array contains the selected actors. When the order is resolved, the engine iterates over the grouped actors and applies the command to each of them. This is how a squad attack-move is implemented:

```csharp
new Order("AttackMove", null, owner.Target, false, groupedActors: owner.Units.ToArray())
```

The subject is `null` because the order applies to the group, not a single actor.

### Order throttling

The throttling fraction is:

```csharp
var ordersToIssueThisTick = Math.Min((orders.Count + info.MinOrderQuotientPerTick - 1) / info.MinOrderQuotientPerTick, orders.Count);
```

This ensures that a large backlog of orders is issued over multiple ticks. For example, with `MinOrderQuotientPerTick = 5`, a queue of 100 orders issues at most 20 orders per tick.

### Visual feedback suppression

`SuppressVisualFeedback = true` tells the order resolver to skip target-line drawing and selection flash effects. This is important for bot orders so that observers do not see constant target lines from every bot action.

![Extension points diagram](images/Part_08_Chapter_04_Order_Flow-extension-hook-diagram-showing-the-interface-s-to-implement-b4a27b.svg)

## Extension Points


### Add a new order command

Define a new order string and a handler. Order handlers can be implemented in traits (e.g., `IResolveOrder`) or in the support power manager. A bot module can then issue the order just like any other.

### Add a new bot module that issues orders

Any new module can call `bot.QueueOrder(new Order(...))`. The order will flow through the same pipeline as existing modules.

### Immediate orders

Set `IsImmediate = true` for orders that should not cross the lockstep pipeline and should be processed immediately. This is used for system orders such as chat, pause, and game saves. Most bot orders should not be immediate. See [Part 9.1 — OrderManager and Lockstep Foundation](Part_09_Chapter_01_OrderManager.md) for the immediate-order path and the lockstep distinction.

![Common pitfalls  guardrails diagram](images/Part_08_Chapter_04_Order_Flow-checklist-infographic-style-diagram-summarizing-the-top-pitf-fb069e.svg)

## Common Pitfalls / Guardrails


- **Order subject must exist:** if the `Subject` actor dies before the order is executed, the order is dropped. Use `null` subject for group orders to avoid this.
- **Target validity:** a target that is invalid when the order executes (e.g., a dead actor) will cause the order to be ignored or produce an error. Modules should re-check targets when re-issuing orders.
- **Order latency:** an order issued in frame N is executed in frame N+1 or later. Bot modules must not assume immediate effect.
- **Desync risk:** bot orders must be deterministic on all clients. Do not include unsynced random values or client-only state in the order payload.
- **Suppress visual feedback:** always set `SuppressVisualFeedback = true` for bot orders to avoid visual clutter.
- **Queue order from the right thread:** `IBot.QueueOrder` is called from the bot tick. Do not call it from async callbacks or background threads.
- **Replay correctness:** because bot logic is disabled during replays, only the orders are replayed. If a bot order depends on unsynced state that was not deterministic, the replay may differ from the original game.

## What to read next

- [Part 1.3 — World, OrderManager, and Orders](Part_01_Chapter_03_World_Orders.md) for the complete anatomy of an `Order` and the player order entry points.
- [Part 9.1 — OrderManager and Lockstep Foundation](Part_09_Chapter_01_OrderManager.md) for the full lockstep buffering, serialization, and frame-pacing path.
- [Part 1.2 — Activity System](Part_01_Chapter_02_Activities.md) for how orders become actor activities once they reach the simulation.
- [Part 8.1 — Bot Architecture and IBot](Part_08_Chapter_01_IBot.md) for the broader `IBot` and `ModularBot` architecture.

## Summary

This chapter focuses on how bot modules construct [orders](../appendices/Appendix_A_Glossary.md) and how `[ModularBot](../appendices/Appendix_A_Glossary.md)` queues, throttles, and issues them through the same `World.IssueOrder` entry point as human orders. It does not cover the full field-by-field `Order` anatomy or the complete lockstep pipeline; those are the responsibilities of [Part 1.3 — World, OrderManager, and Orders](Part_01_Chapter_03_World_Orders.md) and [Part 9.1 — OrderManager and Lockstep Foundation](Part_09_Chapter_01_OrderManager.md) respectively.

If any of the concepts above feel unclear, review the relevant section before continuing. For source files and further reading, see the References section.


## References

- `OpenRA.Game/Network/Order.cs` — `Order` class and serialization.
- `OpenRA.Game/Network/OrderManager.cs` — order buffering and network transmission.
- `OpenRA.Game/Network/OrderIO.cs` — order packet format.
- `OpenRA.Game/Network/UnitOrders.cs` — system order handlers.
- `OpenRA.Game/World.cs` — `IssueOrder` wrapper.
- `OpenRA.Mods.Common/Traits/Player/ModularBot.cs` — bot order queue and throttling.
- `OpenRA.Mods.Common/Traits/BotModules/SquadManagerBotModule.cs` — squad order construction.
- `OpenRA.Mods.Common/Traits/BotModules/BaseBuilderBotModule.cs` — building orders.
- `OpenRA.Mods.Common/Traits/BotModules/UnitBuilderBotModule.cs` — unit production orders.
- `OpenRA.Mods.Common/Traits/SupportPowers/SupportPowerManager.cs` — support power order resolution.