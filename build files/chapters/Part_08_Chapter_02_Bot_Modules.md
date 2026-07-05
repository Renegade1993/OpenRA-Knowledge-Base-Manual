# Chapter 8.2 — Bot Modules

## Purpose

`[ModularBot](../appendices/Appendix_A_Glossary.md)` is only a coordinator; the actual AI behavior lives in specialized **[bot modules](../appendices/Appendix_A_Glossary.md)**. Each module is a player-level trait that observes one slice of the world (base construction, units, harvesters, squads, support powers) and issues [orders](../appendices/Appendix_A_Glossary.md) through the bot's `QueueOrder`. This chapter surveys the major modules, their responsibilities, and the heuristics that guide them.

## Learning Objectives


After studying this chapter, you should be able to:

- Explain the modular bot architecture and how modules are discovered as player traits.
- Describe the responsibilities of the major bot modules (base builder, unit builder, harvester, squad, support power, etc.).
- Understand how modules coordinate through shared callback interfaces.
- Trace the data flow and heuristics in BaseBuilderBotModule and UnitBuilderBotModule.
- Configure bot modules in YAML to tune AI behavior.
- Implement a new bot module that integrates with ModularBot.

## Files

| File | Responsibility |
| :---- | :---- |
| `OpenRA.Mods.Common/Traits/BotModules/BaseBuilderBotModule.cs` | Base layout, building queues, power management, refinery placement. |
| `OpenRA.Mods.Common/Traits/BotModules/UnitBuilderBotModule.cs` | Unit production queues and idle-unit tracking. |
| `OpenRA.Mods.Common/Traits/BotModules/HarvesterBotModule.cs` | Assigns harvesters to resource fields and refineries. |
| `OpenRA.Mods.Common/Traits/BotModules/ResourceMapBotModule.cs` | Builds a coarse resource map for base/expansion decisions. |
| `OpenRA.Mods.Common/Traits/BotModules/SquadManagerBotModule.cs` | Groups idle units into squads and assigns combat roles. |
| `OpenRA.Mods.Common/Traits/BotModules/SupportPowerBotModule.cs` | Decides when and where to use support powers. |
| `OpenRA.Mods.Common/Traits/BotModules/McvManagerBotModule.cs` | Deploys MCVs and requests new ones when needed. |
| `OpenRA.Mods.Common/Traits/BotModules/McvExpansionManagerBotModule.cs` | Decides when to move/undeploy an MCV for expansion. |
| `OpenRA.Mods.Common/Traits/BotModules/CaptureManagerBotModule.cs` | Manages engineer-style capture orders. |
| `OpenRA.Mods.Common/Traits/BotModules/BuildingRepairBotModule.cs` | Automatically orders building repairs. |
| `OpenRA.Mods.Common/Traits/BotModules/PowerDownBotManager.cs` | Powers down buildings when low on power. |
| `OpenRA.Mods.Common/Traits/BotModules/BotModuleLogic/MinelayerBotModule.cs` | Orders minelayers to lay mines. |
| `OpenRA.Mods.Common/Traits/BotModules/BotModuleLogic/SupportPowerDecision.cs` | YAML-decodable decision rules for support powers. |
| `OpenRA.Mods.Common/AIUtils.cs` | Shared helpers for queue lookup, actor counting, etc. |

![Architecture diagram](images/Part_08_Chapter_02_Bot_Modules-architecture-diagram-showing-the-main-classes-interfaces-and-9161e6.svg)

## Architecture


### Module as a player trait

Every module is a `ConditionalTrait<TInfo>` located on `SystemActors.Player`. The `Info` class carries YAML-configurable parameters and the runtime class implements one or more bot callback [trait](../appendices/Appendix_A_Glossary.md) interfaces. For example:

```csharp
public class BaseBuilderBotModule : ConditionalTrait<BaseBuilderBotModuleInfo>,
    IGameSaveTraitData, IBotTick, IBotPositionsUpdated, IBotRespondToAttack,
    IBotRequestPauseUnitProduction, IBotSuggestRefineryProduction, INotifyActorDisposing
```

Modules are not owned by `ModularBot`; they are discovered by interface query when the bot is activated.

### Shared data structures

Many modules use `ActorIndex` to efficiently track subsets of the world by owner and actor names:

```csharp
readonly ActorIndex.OwnerAndNamesAndTrait<BuildingInfo> constructionYardBuildings;
readonly ActorIndex.OwnerAndNamesAndTrait<BuildingInfo> refineries;
```

These indices are created in the constructor and queried during each tick. They are much cheaper than scanning `world.Actors` every tick.

### Inter-module coordination

Modules coordinate through the callback interfaces defined in `OpenRA.Mods.Common/TraitsInterfaces.cs`. Examples:

- `BaseBuilderBotModule` updates `initialBaseCenter` and `DefenseCenter` via `IBotPositionsUpdated` for other modules.
- `UnitBuilderBotModule` pauses production when `IBotRequestPauseUnitProduction.PauseUnitProduction` is true (controlled by `BaseBuilderBotModule`).
- `SquadManagerBotModule` reports idle base units via `IBotNotifyIdleBaseUnits`.
- `McvManagerBotModule` requests MCV production via `IBotRequestUnitProduction`.
- `BaseBuilderBotModule` and `HarvesterBotModule` share the `ResourceMapBotModule`.

![Data flow  code path diagram](images/Part_08_Chapter_02_Bot_Modules-sequence-flow-diagram-tracing-the-execution-path-from-trigge-035864.svg)

## Data Flow / Code Path


### BaseBuilderBotModule

`BaseBuilderBotModule` maintains a set of `BaseBuilderQueueManager` instances, one for each building queue and one for each defense queue. Each tick, the module rotates through the managers and asks them to process their queue.

Key decisions:

1. **Refinery-first rule:** `PauseUnitProduction` returns true until the bot has a minimum number of refineries, so `UnitBuilderBotModule` does not waste cash on units before the economy is established.
2. **Building fractions:** `BuildingFractions` defines the target percentage of each building type. The queue manager picks the building whose actual count is furthest below its target.
3. **Power management:** when excess power is low, the queue manager prioritizes power plants.
4. **Placement:** `BaseBuilderQueueManager` finds a valid placement near the base center, handles naval adjacency, and issues a production order.
5. **Defense center:** `DefenseCenter` can be set toward the nearest enemy or combat hotspot so defenses face the front.

### UnitBuilderBotModule

`UnitBuilderBotModule` iterates over unit production queues every `FeedbackTime` ticks (30 ticks by default). It checks:

1. **Pending requests:** if another module requested a specific unit, build it first.
2. **Idle unit cap:** if `IdleBaseUnitsMaximum` is reached, stop producing units.
3. **Cash:** only produce when `playerResources.GetCashAndResources() >= ProductionMinCashRequirement`.
4. **Unit fractions:** `UnitsToBuild` is a dictionary of actor names to desired counts. The module picks the unit whose actual count is furthest below its target.

![UnitBuilderBotModule](images/Part_08_Chapter_02_Bot_Modules-UnitBuilderBotModule-queue-rotation-flow.svg)
### HarvesterBotModule

`HarvesterBotModule` tracks harvesters in a `Dictionary<Actor, HarvesterTraitWrapper>` and assigns them to resource fields. On each tick:

1. Scan for idle or low-yield harvesters.
2. Find a resource cell in a desirable resource patch.
3. Issue a `Harvest` order to the closest refinery.
4. If attacked, briefly flee or call for help.

It uses the `ResourceMapBotModule` to find the best resource areas.

### ResourceMapBotModule

`ResourceMapBotModule` divides the map into a coarse grid of `ResourceIndice` cells. Each cell tracks:

- `ResourceCellsCount` — how many valuable resource cells are in the area.
- `ResourceCellsCenter` — centroid of the resource cells.
- `PlayerRefineryCount` / `PlayerHarvesterCount` — bot presence.
- `EnemyUnitCount` / `EnemyBaseCount` — enemy presence.
- `FriendlyBaseCount` / `FriendlyUnitCount` — friendly presence.

The map is updated one indice per tick to spread the cost. Other modules use this data to decide where to place refineries, expand, or send harvesters.

### SquadManagerBotModule

`SquadManagerBotModule` is covered in detail in [Part 8.3 — Bot Squads and Combat Heuristics](Part_08_Chapter_03_Squads.md). In short, it scans idle units, assigns them to existing [squads](../appendices/Appendix_A_Glossary.md) or creates new squads, and sends squads to attack targets or defend the base.

### SupportPowerBotModule

`SupportPowerBotModule` uses a YAML-defined `SupportPowerDecision` for each support power. Each tick:

1. Iterate over the player's `SupportPowerManager.Powers`.
2. Skip powers that are disabled, not ready, or recently scanned.
3. For ready powers, run a coarse scan (`FindCoarseAttackLocationToSupportPower`) to find a target area.
4. Run a fine scan (`FindFineAttackLocationToSupportPower`) to refine the target cell.
5. Queue the power order with `Target.FromCell`.

The decision rules include minimum target counts, target type filters, and scan intervals.

### McvManagerBotModule

`McvManagerBotModule` handles construction-yard deployment:

1. On first tick, deploy all idle MCVs.
2. Every `ScanForNewMcvInterval` ticks, deploy idle MCVs and check whether a new MCV should be built.
3. If the construction yard count is below `MinimumConstructionYardCount` and the bot has no MCV in the field, request one.
4. If `RestrictMCVDeploymentFallbackToBase` is enabled, deployment is limited to the base radius when explicit deploy locations are unavailable.

### CaptureManagerBotModule

`CaptureManagerBotModule` tracks actors with the `Captures` trait and assigns them to capture enemy buildings. It evaluates targets by value (e.g., construction yards, power plants) and ensures the capture actor survives the approach.

### BuildingRepairBotModule

`BuildingRepairBotModule` listens to damage notifications and automatically issues repair orders for damaged buildings. It respects cash availability and a cooldown to avoid spamming repair orders.

### PowerDownBotManager

`PowerDownBotManager` monitors the player's power state. When power is negative, it selectively powers down low-priority buildings until the deficit is resolved. When power is restored, it powers them back up.

![Configuration (yaml) diagram](images/Part_08_Chapter_02_Bot_Modules-annotated-yaml-snippet-diagram-showing-the-key-fields-and-ho-6a1b98.svg)

## Configuration (YAML)


### AI YAML layout

Each bot personality is a block on the `Player` actor. A typical block contains:

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
        IdleBaseUnitsMaximum: 20
        ProductionMinCashRequirement: 500
    SquadManagerBotModule:
        SquadSize: 10
        RushInterval: 2500
        AssignRolesInterval: 150
        AttackForceInterval: 250
        MinimumAttackForceDelay: 1000
        DangerScanRadius: 10
    SupportPowerBotModule:
        Decisions:
            airstrike:
                OrderName: airstrike
                MinimumAttractiveness: 200
                Consideration: target-anything
                ...
    HarvesterBotModule:
        RefineryTypes: proc
        HarvesterTypes: harv
        InitialHarvesters: 4
    ResourceMapBotModule:
        ValuableResourceTypes: Ore, Gems
        ResourceMapStrideRadius: 12
    McvManagerBotModule:
        McvTypes: mcv
        ConstructionYardTypes: fact
        MinimumConstructionYardCount: 1
    CaptureManagerBotModule:
        CapturingActorTypes: e6
        CapturableActorTypes: fact, powr, weap, barr
```

### Building fractions

`BuildingFractions` is a dictionary of actor names to percentages. The AI tries to keep the share of each building near its target fraction. For example, if the base has 10 buildings and `weap` has a fraction of 20, the AI aims for 2 weapons factories.

### Unit build counts

`UnitsToBuild` is a dictionary of actor names to desired counts. Unlike `BuildingFractions`, these are absolute counts, not percentages. The AI builds the unit whose current count is furthest below its target.

## Interconnectivity

- **Depends on:** [Part 8.1 — Bot Architecture and IBot](Part_08_Chapter_01_IBot.md) (IBot and ModularBot), [Part 1.1 — ECS, Actors, and Traits](Part_01_Chapter_01_ECS.md) (Actor/Trait), [Part 2.4 — Rulesets, Actors, and Weapons](Part_02_Chapter_04_Rules_Weapons.md) (Ruleset and production queues), [Part 1.3 — World, OrderManager, and Orders](Part_01_Chapter_03_World_Orders.md) (Orders), [Part 9.1 — OrderManager and Lockstep Foundation](Part_09_Chapter_01_OrderManager.md) (lockstep order flow).
- **Used by:** [Part 8.3 — Bot Squads and Combat Heuristics](Part_08_Chapter_03_Squads.md) (Squads), [Part 8.4 — Bot Order Flow](Part_08_Chapter_04_Order_Flow.md) (Order flow), [Part 10.1 — Official Mods](Part_10_Chapter_01_Official_Mods.md) (official mod AI personalities).

![Algorithms diagram](images/Part_08_Chapter_02_Bot_Modules-algorithm-diagram-or-pseudocode-flowchart-for-the-non-trivia-5983ed.svg)

## Algorithms


### BaseBuilder rotation

`BaseBuilderBotModule` rotates through `builders` with `currentBuilderIndex` so that only one queue manager is processed per tick. This prevents a single tick from being dominated by placement searches and mirrors the way a human can only click one build button at a time.

### Unit selection under-production

```csharp
var unitsToBuild = Info.UnitsToBuild.RandomSubset(
    world.LocalRandom, Info.UnitsToBuild.Count).Where(kvp =>
        kvp.Value > unitsToBuildCount[kvp.Key]);

var unit = unitsToBuild.MaxByOrDefault(kvp => kvp.Value - unitsToBuildCount[kvp.Key]);
```

The deficit between the desired count and the actual count drives unit selection. Random subsetting prevents the AI from always picking the same unit first.

### Resource indice update

`ResourceMapBotModule` updates one indice per tick using a sliding index:

```csharp
UpdateResourceMap(updateResourceMapIndex);
updateResourceMapIndex = (updateResourceMapIndex + 1) % resourceMapIndices.Length;
```

This amortizes the cost of scanning the entire map over many ticks.

### Support power target scoring

`SupportPowerDecision` assigns an attractiveness score to each candidate cell based on the number and type of targets. The coarse scan finds the highest-scoring region; the fine scan finds the best cell within that region.

### MCV expansion trigger

`BaseBuilderBotModule` decides whether to expand based on:

```csharp
AI will move mcv when refinery count <= productions + tech - ExpansionTolerate
```

If the bot has too few refineries relative to its production/tech buildings, it will try to move an MCV to a new resource patch.

![Extension points diagram](images/Part_08_Chapter_02_Bot_Modules-extension-hook-diagram-showing-the-interface-s-to-implement-b4a27b.svg)

## Extension Points


### Add a new module

Create a new `ConditionalTrait<TInfo>` that implements `IBotTick` (or another callback), and add it to the AI YAML. The module can read any world state and queue any order.

### Tune existing personalities

Because all module behavior is driven by YAML parameters, new AI personalities can be created by copying an existing bot block and adjusting the numbers. No recompilation is needed.

### Add custom support power decisions

Create `SupportPowerDecision` entries in YAML for each support power. The decision defines minimum attractiveness, target types, and scan intervals.

### Add a new base builder queue

Add a new queue name to `BuildingQueues` or `DefenseQueues` and ensure the production building has a matching `ProductionQueue` trait.

![Common pitfalls  guardrails diagram](images/Part_08_Chapter_02_Bot_Modules-checklist-infographic-style-diagram-summarizing-the-top-pitf-fb069e.svg)

## Common Pitfalls / Guardrails


- **Module dependencies:** modules can declare `Requires<>` or `NotBefore<>` dependencies on trait info. For example, `BaseBuilderBotModuleInfo` requires `ResourceMapBotModuleInfo`.
- **Order latency:** a module must not assume that an order it issued is instantly reflected in the world state. Most modules check actual actor counts rather than pending orders.
- **Cash checks:** building and unit production modules guard against spending cash below `ProductionMinCashRequirement`. Removing this guard can bankrupt the AI.
- **Idle unit maximum:** `UnitBuilderBotModule` stops producing when idle units exceed the cap. This prevents the AI from endlessly producing units that it cannot manage.
- **Replays:** modules run unsynced and only influence the world through orders. If a module mutates state directly, replays will desync.
- **Pathfinding cost:** modules that pathfind for placement or movement should rate-limit the search, as seen in the `ScanFor...Interval` fields.

## What to read next

- [Part 8.1 — Bot Architecture and IBot](Part_08_Chapter_01_IBot.md) for the `ModularBot` coordinator that discovers and invokes these modules.
- [Part 8.3 — Bot Squads and Combat Heuristics](Part_08_Chapter_03_Squads.md) for the squad manager module and combat decision-making.
- [Part 8.4 — Bot Order Flow](Part_08_Chapter_04_Order_Flow.md) for how the orders produced by modules enter the simulation.
- [Appendix G — Advanced Modding Walkthroughs](../appendices/Appendix_G_Advanced_Modding_Walkthroughs.md) for a complete custom YAML AI bot walkthrough.

## Summary

This chapter explains how `[ModularBot](../appendices/Appendix_A_Glossary.md)` coordinates specialized **[bot modules](../appendices/Appendix_A_Glossary.md)** that each handle one slice of AI behavior.

After reading this chapter, you should be able to:

- **Refinery-first rule:** `PauseUnitProduction` returns true until the bot has a minimum number of refineries, so `UnitBuilderBotModule` does not waste cash on units before the economy is established.
- **Building fractions:** `BuildingFractions` defines the target percentage of each building type. The queue manager picks the building whose actual count is furthest below its target.
- **Power management:** when excess power is low, the queue manager prioritizes power plants.
- **Placement:** `BaseBuilderQueueManager` finds a valid placement near the base center, handles naval adjacency, and issues a production order.
- **Defense center:** `DefenseCenter` can be set toward the nearest enemy or combat hotspot so defenses face the front.

If any of the concepts above feel unclear, review the relevant section before continuing. For source files and further reading, see the References section.


## References

- `OpenRA.Mods.Common/Traits/Player/ModularBot.cs` — bot coordinator.
- `OpenRA.Mods.Common/Traits/BotModules/BaseBuilderBotModule.cs` — base construction.
- `OpenRA.Mods.Common/Traits/BotModules/UnitBuilderBotModule.cs` — unit production.
- `OpenRA.Mods.Common/Traits/BotModules/HarvesterBotModule.cs` — harvester logic.
- `OpenRA.Mods.Common/Traits/BotModules/ResourceMapBotModule.cs` — resource map.
- `OpenRA.Mods.Common/Traits/BotModules/SquadManagerBotModule.cs` — squads.
- `OpenRA.Mods.Common/Traits/BotModules/SupportPowerBotModule.cs` — support powers.
- `OpenRA.Mods.Common/Traits/BotModules/BotModuleLogic/SupportPowerDecision.cs` — support power decision rules.
- `OpenRA.Mods.Common/Traits/BotModules/McvManagerBotModule.cs` — MCV management.
- `OpenRA.Mods.Common/Traits/BotModules/McvExpansionManagerBotModule.cs` — MCV expansion.
- `OpenRA.Mods.Common/Traits/BotModules/CaptureManagerBotModule.cs` — capture logic.
- `OpenRA.Mods.Common/Traits/BotModules/BuildingRepairBotModule.cs` — repair automation.
- `OpenRA.Mods.Common/Traits/BotModules/PowerDownBotManager.cs` — power management.
- `OpenRA.Mods.Common/AIUtils.cs` — shared helpers.
- `mods/ra/rules/ai.yaml` — example bot configurations.