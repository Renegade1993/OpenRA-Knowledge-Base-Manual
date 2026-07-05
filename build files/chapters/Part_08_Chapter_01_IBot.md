# Chapter 8.1 — Bot Architecture and IBot

## Purpose

OpenRA's [bot](../appendices/Appendix_A_Glossary.md) framework is built around the idea that **bot logic is not allowed to mutate the [world](../appendices/Appendix_A_Glossary.md) directly**. Instead, a bot is a player-level trait that observes the world, decides what [orders](../appendices/Appendix_A_Glossary.md) to issue, and queues those orders through the normal order system. Because orders go through the same lockstep pipeline as human orders, bot actions are recorded in replays and stay synchronized across clients. This chapter introduces the core interfaces (`IBot`, `IBotInfo`, `IBotTick`) and the modular `[ModularBot](../appendices/Appendix_A_Glossary.md)` that runs them.

## Learning Objectives


After studying this chapter, you should be able to:

1. Explain why bot logic is forbidden from mutating world state directly and must issue orders instead.
2. Describe the responsibilities of `IBot`, `IBotInfo`, and `ModularBot`.
3. List the common bot module callback interfaces (`IBotTick`, `IBotEnabled`, `IBotRespondToAttack`, etc.) and when each is invoked.
4. Trace bot activation, the per-tick decision loop, and attack-response dispatch.
5. Explain how `ModularBot` throttles orders and why `RunUnsynced` is used around bot code.
6. Register a bot type and configure modules in a mod's AI YAML.
7. Diagnose common bot issues such as stalled construction, unresponsive defense, and order flooding.

![Practical example: a bot builds a power plant diagram](images/Part_08_Chapter_01_IBot-end-to-end-worked-example-diagram-showing-the-inputs-interme-5fc6a2.svg)

## Practical Example: A Bot Builds a Power Plant


When a rush-style AI decides it needs more power:

1. **Bot activation.** At game start, the engine creates the bot's `PlayerActor` and calls `IBot.Activate`. `ModularBot` caches references to all modules on the actor that implement `IBotTick` and `IBotRespondToAttack`.
2. **Tick entry.** Every simulation tick, `ModularBot.Tick` runs inside a `PerfSample` and wraps module logic in `Sync.RunUnsynced(...)` so that bot-private calculations do not affect the sync hash.
3. **Base builder decision.** `BaseBuilderBotModule` (an `IBotTick` module) checks the current power surplus, building limits, and building fractions. It decides that a power plant is required.
4. **Order queuing.** The module calls `bot.QueueOrder(Order.StartProduction(...))` with `Subject` set to the construction yard and `TargetString` set to the power plant actor name.
5. **Order throttling.** `ModularBot.Tick` dequeues only a fraction of the pending orders each tick based on `MinOrderQuotientPerTick`. This prevents the bot from dumping a large burst of orders onto the network in a single frame.
6. **Order issue.** The selected order is passed to `world.IssueOrder`, which routes it through `OrderManager` exactly like a human order.
7. **Production resolve.** The construction yard's `ProductionQueue` trait receives the order via `ResolveOrder`, starts production, and eventually places the building when the player has enough funds.
8. **Placement confirmation.** A second queued order (e.g., `PlaceBuilding`) is issued when the power plant is ready, and the building appears on the map on the same simulation frame for every client.

This example shows how a bot decision becomes a sequence of normal orders that stay synchronized, replayable, and fair in multiplayer.

## Files

| File | Responsibility |
| :---- | :---- |
| `OpenRA.Game/Traits/TraitsInterfaces.cs` | Core `IBotInfo` and `IBot` interfaces. |
| `OpenRA.Mods.Common/TraitsInterfaces.cs` | Bot module callback interfaces (`IBotTick`, `IBotEnabled`, `IBotRespondToAttack`, `IBotPositionsUpdated`, etc.). |
| `OpenRA.Mods.Common/Traits/Player/ModularBot.cs` | The `ModularBot` trait that activates bot modules and issues queued orders. |
| `OpenRA.Mods.Common/Traits/BotModules/BaseBuilderBotModule.cs` | Base construction module. |
| `OpenRA.Mods.Common/Traits/BotModules/UnitBuilderBotModule.cs` | Unit production module. |
| `OpenRA.Mods.Common/Traits/BotModules/HarvesterBotModule.cs` | Harvester management module. |
| `OpenRA.Mods.Common/Traits/BotModules/SquadManagerBotModule.cs` | Combat squad management module. |
| `OpenRA.Mods.Common/Traits/BotModules/SupportPowerBotModule.cs` | Support power usage module. |
| `mods/*/rules/ai.yaml` | YAML definitions of bot types and their module configurations. |

![Architecture diagram](images/Part_08_Chapter_01_IBot-architecture-diagram-showing-the-main-classes-interfaces-and-9161e6.svg)

## Architecture


### Core interfaces

The engine defines two minimal interfaces in `OpenRA.Game/Traits/TraitsInterfaces.cs`:

```csharp
public interface IBotInfo : ITraitInfoInterface
{
    string Type { get; }
    string Name { get; }
}

public interface IBot
{
    void Activate(Player p);
    void QueueOrder(Order order);
    IBotInfo Info { get; }
    Player Player { get; }
}
```

Every bot is a player-level [trait](../appendices/Appendix_A_Glossary.md) whose `Info` class implements `IBotInfo` and whose instance class implements `IBot`. The engine activates the bot when the player is created, and the bot then queues orders through `QueueOrder`.

### ModularBot

The current bot system is `ModularBot` in `OpenRA.Mods.Common/Traits/Player/ModularBot.cs`. It is a `TraitInfo` located on `SystemActors.Player` and implements `ITick` and `INotifyDamage`. The class itself is a thin coordinator:

```csharp
public sealed class ModularBot : ITick, IBot, INotifyDamage
{
    readonly Queue<Order> orders = [];
    IBotTick[] tickModules;
    IBotRespondToAttack[] attackResponseModules;
    ...
}
```

`ModularBot` does not contain any AI strategy itself. It discovers modules on the same `PlayerActor` that implement `IBotTick`, `IBotRespondToAttack`, or other bot callback interfaces, and invokes them at the right times.

### Bot module callback interfaces

`OpenRA.Mods.Common/TraitsInterfaces.cs` defines the callbacks that modules can subscribe to:

| Interface | Callback | Purpose |
| :---- | :---- | :---- |
| `IBotEnabled` | `BotEnabled(IBot bot)` | One-time setup when the bot is activated. |
| `IBotTick` | `BotTick(IBot bot)` | Called every tick for ongoing decision-making. |
| `IBotRespondToAttack` | `RespondToAttack(IBot bot, Actor self, AttackInfo e)` | Called when the bot's actor is damaged. |
| `IBotPositionsUpdated` | `UpdatedBaseCenter(CPos)` / `UpdatedDefenseCenter(CPos)` | Receives base/defense center updates from `BaseBuilderBotModule`. |
| `IBotNotifyIdleBaseUnits` | `UpdatedIdleBaseUnits(List<Actor>)` | Receives idle unit counts from `SquadManagerBotModule`. |
| `IBotRequestUnitProduction` | `RequestUnitProduction(...)` / `RequestedProductionCount(...)` | Allows one module to request units from another. |
| `IBotRequestPauseUnitProduction` | `PauseUnitProduction { get; }` | Tells `UnitBuilderBotModule` to pause production. |
| `IBotBaseExpansion` | `UpdateExpansionParams(...)` | Receives base expansion decisions from `McvManagerBotModule`. |
| `IBotSuggestRefineryProduction` | `RequestLocation(...)` | Suggests refinery placement locations. |

A module is a normal `ConditionalTrait<TInfo>` that implements one or more of these interfaces. Modules are placed on the `PlayerActor` in the mod's AI YAML.

![Data flow  code path diagram](images/Part_08_Chapter_01_IBot-sequence-flow-diagram-tracing-the-execution-path-from-trigge-035864.svg)

## Data Flow / Code Path


### Bot activation

When a player is created with a bot type, the engine calls `IBot.Activate`:

```csharp
public void Activate(Player p)
{
    if (p.World.IsReplay)
        return;

    IsEnabled = true;
    player = p;
    tickModules = p.PlayerActor.TraitsImplementing<IBotTick>().ToArray();
    attackResponseModules = p.PlayerActor.TraitsImplementing<IBotRespondToAttack>().ToArray();
    foreach (var ibe in p.PlayerActor.TraitsImplementing<IBotEnabled>())
        ibe.BotEnabled(this);
}
```

Bots are disabled during replays because replays only replay orders, not bot decision-making.

### Per-tick decision loop

`ModularBot.Tick` runs each `IBotTick` module in `Sync.RunUnsynced`, which allows bot code to use world-local state without affecting the sync hash:

```csharp
void ITick.Tick(Actor self)
{
    if (!IsEnabled || self.World.IsLoadingGameSave)
        return;

    using (new PerfSample("bot_tick"))
    {
        Sync.RunUnsynced(Game.Settings.Debug.SyncCheckBotModuleCode, world, () =>
        {
            foreach (var t in tickModules)
                if (t.IsTraitEnabled())
                    t.BotTick(this);
        });
    }

    var ordersToIssueThisTick = Math.Min((orders.Count + info.MinOrderQuotientPerTick - 1) / info.MinOrderQuotientPerTick, orders.Count);
    for (var i = 0; i < ordersToIssueThisTick; i++)
        world.IssueOrder(orders.Dequeue());
}
```

Modules call `bot.QueueOrder(order)` to add orders. The bot issues a configurable fraction of the queue each tick to avoid network spikes and to keep the bot from looking too robotic.

### Attack response

When the bot player actor is damaged, `INotifyDamage.Damaged` dispatches to `IBotRespondToAttack` modules:

```csharp
void INotifyDamage.Damaged(Actor self, AttackInfo e)
{
    ...
    Sync.RunUnsynced(..., () =>
    {
        foreach (var t in attackResponseModules)
            if (t.IsTraitEnabled())
                t.RespondToAttack(this, self, e);
    });
}
```

This is how the harvester or base defense modules react to raids without waiting for the next tick.

### Order issuing

`world.IssueOrder` places the order into the local order manager. From there, the order follows the same path as human orders: it is serialized to the local command queue, sent to the server if multiplayer, and executed on the next simulation tick.

![Configuration (yaml) diagram](images/Part_08_Chapter_01_IBot-annotated-yaml-snippet-diagram-showing-the-key-fields-and-ho-6a1b98.svg)

## Configuration (YAML)


### Bot registration

Bots are defined in the mod's AI YAML, typically `mods/*/rules/ai.yaml`:

```yaml
Player:
    ModularBot@rush:
        Type: rush
        Name: bot-rush
        MinOrderQuotientPerTick: 5
    BaseBuilderBotModule:
        ConstructionYardTypes: fact
        RefineryTypes: proc
        PowerTypes: powr, apwr
        ProductionTypes: barr, tent, weap, afld, hpred
        BuildingFractions:
            powr: 20
            tent: 10
            weap: 20
            proc: 20
        BuildingLimits:
            weap: 2
            afld: 2
    UnitBuilderBotModule:
        UnitQueues: Infantry, Vehicle, Aircraft
        UnitsToBuild:
            e1: 80
            e2: 20
            jeep: 10
    SquadManagerBotModule:
        ...
```

The `Type` string is the key used by the lobby dropdown. The `Name` is a Fluent reference.

### Conditional traits

Bot modules are `ConditionalTrait<TInfo>` subclasses. They can be enabled or disabled by external conditions (e.g., a game mode that turns off base building), though in practice most AI modules are always enabled.

## Interconnectivity

- **Depends on:** [Part 1.1 — ECS, Actors, and Traits](Part_01_Chapter_01_ECS.md) (Actor/Trait system), [Part 1.3 — World, OrderManager, and Orders](Part_01_Chapter_03_World_Orders.md) (World/Orders), [Part 2.4 — Rulesets, Actors, and Weapons](Part_02_Chapter_04_Rules_Weapons.md) (Rulesets and production queues), [Part 3.1 — Mod SDK and Project Structure](Part_03_Chapter_01_Mod_SDK.md) (PlayerActor setup), [Part 9.1 — OrderManager and Lockstep Foundation](Part_09_Chapter_01_OrderManager.md) (OrderManager and lockstep).
- **Used by:** [Part 8.2 — Bot Modules](Part_08_Chapter_02_Bot_Modules.md) (Bot Modules), [Part 8.3 — Bot Squads and Combat Heuristics](Part_08_Chapter_03_Squads.md) (Squads), [Part 8.4 — Bot Order Flow](Part_08_Chapter_04_Order_Flow.md) (Order Flow), [Part 9.1 — OrderManager and Lockstep Foundation](Part_09_Chapter_01_OrderManager.md) (network orders originate from bot `QueueOrder`).

![Algorithms diagram](images/Part_08_Chapter_01_IBot-algorithm-diagram-or-pseudocode-flowchart-for-the-non-trivia-5983ed.svg)

## Algorithms


### Order throttling

`MinOrderQuotientPerTick` controls the maximum fraction of the queue issued per tick:

```csharp
var ordersToIssueThisTick = Math.Min((orders.Count + info.MinOrderQuotientPerTick - 1) / info.MinOrderQuotientPerTick, orders.Count);
```

With `MinOrderQuotientPerTick = 5`, at least one fifth of the pending queue is issued each tick. This smooths bot output and prevents a single tick from being flooded with orders.

### Module discovery

`ModularBot` discovers modules at activation time using `TraitsImplementing<T>()`. This means modules are plain traits; no central registry is needed. A mod can add new AI behavior by adding new trait modules.

### Sync isolation

```csharp
Sync.RunUnsynced(Game.Settings.Debug.SyncCheckBotModuleCode, world, () =>
{
    foreach (var t in tickModules)
        ...
});
```

Bot code runs unsynced, so it can use random numbers, local state, and pathfinding without affecting the deterministic simulation. The only thing that crosses the sync boundary is the `Order` issued afterward.

![Extension points diagram](images/Part_08_Chapter_01_IBot-extension-hook-diagram-showing-the-interface-s-to-implement-b4a27b.svg)

## Extension Points


### Add a new bot module

Create a `ConditionalTrait<TInfo>` that implements `IBotTick` (and optionally `IBotRespondToAttack`, `IBotPositionsUpdated`, etc.). Add it to the `PlayerActor` in the AI YAML. The module can queue orders via `bot.QueueOrder(order)` and access the world through `bot.Player.World`.

### Add a new bot personality

Define a new `ModularBot@<type>` entry in the AI YAML with a different combination of modules and different module settings. Because modules are traits, the same bot framework can produce many personalities by changing YAML alone.

### Replace ModularBot

A custom bot can implement `IBot` and `IBotInfo` directly. This is useful if the modular approach is not appropriate, for example, a scripted campaign AI or a machine-learning bot that needs centralized control.

### Add new bot callbacks

Define a new interface in `OpenRA.Mods.Common/TraitsInterfaces.cs`, discover implementers in `ModularBot.Activate`, and trigger the callback from an appropriate event. This is how the existing callbacks were added incrementally.

![Common pitfalls  guardrails diagram](images/Part_08_Chapter_01_IBot-checklist-infographic-style-diagram-summarizing-the-top-pitf-fb069e.svg)

## Common Pitfalls / Guardrails


- **No direct world mutation:** bot modules must not call `actor.QueueActivity`, set actor state, or mutate the world directly. All changes must flow through orders.
- **Replays:** bot logic is disabled during replays. If a bot mutates state without an order, the replay will desync.
- **Order latency:** bot modules should account for order latency. A module that checks "is this building being built?" must consider that the order it issued earlier has not yet executed.
- **Sync isolation:** bot code runs unsynced, so it must not call simulation-only APIs that assume sync context. Random choices should use `world.LocalRandom`, not `world.SharedRandom`.
- **Trait enabled checks:** `ModularBot` only invokes modules whose `IsTraitEnabled()` is true. If a module is conditional, it should handle being skipped gracefully.
- **Performance:** bot ticks are wrapped in `PerfSample("bot_tick")`. Expensive pathfinding or scanning should be rate-limited with tick counters, as seen in `BaseBuilderBotModule` and `HarvesterBotModule`.

## What to read next

- [Part 8.2 — Bot Modules](Part_08_Chapter_02_Bot_Modules.md) for the individual modules that `ModularBot` coordinates.
- [Part 8.4 — Bot Order Flow](Part_08_Chapter_04_Order_Flow.md) for how bot orders enter the lockstep pipeline.
- [Part 9.1 — OrderManager and Lockstep Foundation](Part_09_Chapter_01_OrderManager.md) for the network frame pacing that makes bot orders deterministic.

## Summary

This chapter explains how OpenRA's [bot](../appendices/Appendix_A_Glossary.md) framework issues [orders](../appendices/Appendix_A_Glossary.md) through the lockstep pipeline instead of mutating the [world](../appendices/Appendix_A_Glossary.md) directly.

After reading this chapter, you should be able to:

- Explain why bot logic is forbidden from mutating world state directly and must issue orders instead.
- Describe the responsibilities of `IBot`, `IBotInfo`, and `ModularBot`.
- List the common bot module callback interfaces (`IBotTick`, `IBotEnabled`, `IBotRespondToAttack`, etc.) and when each is invoked.
- Trace bot activation, the per-tick decision loop, and attack-response dispatch.
- Explain how `ModularBot` throttles orders and why `RunUnsynced` is used around bot code.
- Register a bot type and configure modules in a mod's AI YAML.
- Diagnose common bot issues such as stalled construction, unresponsive defense, and order flooding.

If any of the concepts above feel unclear, review the relevant section before continuing. For source files and further reading, see the References section.


## References

- `OpenRA.Game/Traits/TraitsInterfaces.cs` — `IBot`, `IBotInfo`.
- `OpenRA.Mods.Common/TraitsInterfaces.cs` — bot callback interfaces.
- `OpenRA.Mods.Common/Traits/Player/ModularBot.cs` — bot coordinator.
- `OpenRA.Mods.Common/Traits/BotModules/BaseBuilderBotModule.cs` — base building.
- `OpenRA.Mods.Common/Traits/BotModules/UnitBuilderBotModule.cs` — unit production.
- `OpenRA.Mods.Common/Traits/BotModules/HarvesterBotModule.cs` — harvester logic.
- `OpenRA.Mods.Common/Traits/BotModules/SquadManagerBotModule.cs` — combat squads.
- `mods/ra/rules/ai.yaml` — example bot definitions.


### External resources

- [OpenRA traits reference](https://docs.openra.net/en/release/traits/)