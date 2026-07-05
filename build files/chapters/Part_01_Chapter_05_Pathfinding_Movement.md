# Chapter 1.5 — Pathfinding and Movement

## Purpose

This chapter explains how OpenRA turns a destination cell into a sequence of smooth, deterministic unit motions. The pathfinding and movement subsystem is responsible for:

- Deciding whether a cell is reachable for a given actor type (terrain costs, actor blocking, crush rules, sub-cells, and custom movement layers).
- Searching the map for an efficient route from source to destination.
- Executing that route as a chain of per-tick movement steps, turns, and obstacle-avoidance retries.
- Keeping all of this [deterministic](../appendices/Appendix_A_Glossary.md) so that every client in a multiplayer match sees the same path and the same result.

If you have read [Part 1.1 — Entity-Component-System (ECS) and Actor Lifecycle](Part_01_Chapter_01_ECS.md) and [Part 1.2 — Activities and the Game Loop](Part_01_Chapter_02_Activities.md), you already know that [actors](../appendices/Appendix_A_Glossary.md) are containers of [traits](../appendices/Appendix_A_Glossary.md) and that [activities](../appendices/Appendix_A_Glossary.md) are transient, multi-tick plans. Movement is one of the clearest examples of that split: `Mobile` is the persistent trait that remembers position and facing, while `Move` is the activity that plans and executes a path. The heavy lifting is delegated to the world-level `PathFinder` trait and its hierarchical A* implementation.

## Learning Objectives


After studying this chapter, you should be able to:

1. Distinguish the roles of `Mobile`, `Locomotor`, `PathFinder`, `PathSearch`, `HierarchicalPathFinder`, and `Move`.
2. Trace the complete flow from a player click to a unit arriving at a destination cell.
3. Explain how terrain costs and actor blocking are combined into a movement graph.
4. Describe how A* is used, why the heuristic is weighted, and what the abstract graph in `HierarchicalPathFinder` is for.
5. Understand why paths are returned *reversed* and why source/target asymmetry matters.
6. Read and modify YAML that configures locomotion, movement speed, and pathfinding debug overlays.
7. Use the `/path-debug` command and interpret the pathfinding overlay.
8. Identify common pitfalls: desyncs from non-deterministic movement, stale paths, and lane-bias assumptions.

![Practical example: a unit moves from a to b diagram](images/Part_01_Chapter_05_Pathfinding_Movement-end-to-end-worked-example-diagram-showing-the-inputs-interme-5fc6a2.svg)

## Practical Example: A Unit Moves From A to B


Imagine a player selects a tank and right-clicks on an open cell.

```
[Player clicks cell B]
       |
       v
[MoveOrderTargeter] -> Order(OrderString = "Move", Target = cell B)
       |
       v
[Mobile.ResolveOrder] -> queues a Move activity
       |
       v
[Move.OnFirstRun] -> asks PathFinder for a path
       |
       v
[HierarchicalPathFinder] -> checks domains, runs abstract A*, runs local A*
       |
       v
[PathSearch] -> returns reversed path: [B, ..., A]
       |
       v
[Move.Tick] -> pops next cell, queues MoveFirstHalf then MoveSecondHalf
       |
       v
[MoveFirstHalf/SecondHalf] -> interpolate position, update facing, finish cell
```

Step by step:

1. **Input.** The viewport translates the click into a world position. The `MoveOrderTargeter` in `Mobile` decides the cursor and produces a `Move` [order](../appendices/Appendix_A_Glossary.md). See [Part 1.3 — World, OrderManager, and Orders](Part_01_Chapter_03_World_Orders.md) for how orders are serialized and sent through `OrderManager`, and [Part 9.1 — OrderManager and Lockstep Foundation](Part_09_Chapter_01_OrderManager.md) for why this happens in lockstep.
2. **Order resolution.** `Mobile.ResolveOrder` clamps the target to the map, checks shroud rules, and calls `self.QueueActivity(order.Queued, WrapMove(new Move(...)))`. This is where [Part 1.2 — Activities and the Game Loop](Part_01_Chapter_02_Activities.md)'s activity queue begins to run the movement plan.
3. **Path planning.** The `Move` activity asks `mobile.PathFinder.FindPathToTargetCell` for a path from `mobile.ToCell` to the destination. The returned `List<CPos>` is reversed (target-to-source). `Move` stores it and pops cells one by one. The `CPos` cell coordinate type is defined in the [glossary](../appendices/Appendix_A_Glossary.md).
4. **Traversal.** For each path cell, `Move` computes a `firstFacing` using `Map.FacingBetween`. If the unit must turn first, it queues a `Turn` child; otherwise it queues `MoveFirstHalf` and `MoveSecondHalf` to interpolate the actor's `CenterPosition` and `Facing` over the tick distance.
5. **Completion.** When the path is consumed, `Move` returns `true` and the activity ends. The unit is now idle and the next queued activity (if any) takes over.

This example ties together ECS (the `Mobile` trait and world traits), activities (the `Move` activity chain), deterministic math (`CPos`, `WPos`, `WAngle`), and the ruleset (`LocomotorInfo` and `MobileInfo` loaded from YAML).

## Files

| File | Responsibility |
| :---- | :---- |
| `OpenRA.Mods.Common/Traits/Mobile.cs` | The per-actor movement trait. Implements `IIssueOrder`, `IResolveOrder`, `IMove`, `IPositionable`, `IFacing`, and `IOccupySpace`. Tracks `FromCell`, `ToCell`, `CenterPosition`, `Facing`, and movement speed. |
| `OpenRA.Mods.Common/Traits/World/Locomotor.cs` | World trait that defines movement costs per terrain type, cell blocking rules, and actor-crush rules. Used by `Mobile` and the pathfinder. |
| `OpenRA.Mods.Common/Traits/World/PathFinder.cs` | World trait that exposes `IPathFinder` and builds a `HierarchicalPathFinder` for every `Locomotor` on the map. |
| `OpenRA.Mods.Common/Pathfinder/HierarchicalPathFinder.cs` | Maintains a low-resolution abstract graph of the map to guide the high-resolution local A* search. |
| `OpenRA.Mods.Common/Pathfinder/PathSearch.cs` | Generic A* search engine. Uses `IPathGraph`, a priority queue, and a weighted heuristic. |
| `OpenRA.Mods.Common/Pathfinder/IPathGraph.cs` | Graph interface plus `GraphEdge`/`GraphConnection` structs and unreachable-cell constants. |
| `OpenRA.Mods.Common/Activities/Move/Move.cs` | The `Move` activity that turns a path into a sequence of cell transitions and child movement activities. |
| `OpenRA.Mods.Common/Activities/Move/MoveWithinRange.cs` | A derived activity that searches for any cell inside a min/max range of a target (used by attack and support powers). |
| `OpenRA.Mods.Common/Traits/World/PathFinderOverlay.cs` | Optional debug overlay that renders the abstract and local search edges explored by the pathfinder. |
| `OpenRA.Mods.Common/TraitsInterfaces.cs` | Defines `IPathFinder`, `IPositionable`, `IMove`, and `BlockedByActor` used by the movement system. |
| `OpenRA.Game/Traits/TraitsInterfaces.cs` | Defines `IOccupySpace`, `IOrderTargeter`, `IIssueOrder`, `IResolveOrder`, and `IActorMap` used by movement and orders. |
| `OpenRA.Game/Map/ActorInitializer.cs` | Provides `LocationInit`, `SubCellInit`, `CenterPositionInit`, and `FacingInit` used when spawning and moving actors. |

![Architecture diagram](images/Part_01_Chapter_05_Pathfinding_Movement-architecture-diagram-showing-the-main-classes-interfaces-and-9161e6.svg)

## Architecture


### The movement stack

Movement in OpenRA is layered. From the data definition down to the pixel position, the layers are:

![The movement stack](images/Part_01_Chapter_05_Pathfinding_Movement-The_movement_stack.svg)
### Key classes and interfaces

- **`LocomotorInfo` / `Locomotor`** — The [world](../appendices/Appendix_A_Glossary.md) trait that owns the movement rules for a locomotor type. It stores `TerrainSpeeds` (which maps terrain type names to speed and path cost), `SharesCell`, `MoveIntoShroud`, `Crushes`, and more. The runtime `Locomotor` builds per-cell cost layers and a blocking cache that is updated whenever actors or terrain change. It is the single source of truth for "can this actor enter this cell." See [Part 2.4 — Rulesets, Actors, and Weapons](Part_02_Chapter_04_Rules_Weapons.md) for how these infos are loaded from YAML.
- **`MobileInfo` / `Mobile`** — The per-actor trait that makes a unit movable. `MobileInfo` links the actor to a `Locomotor` by name, sets `Speed`, `TurnSpeed`, cursors, and voice responses. `Mobile` implements `IOccupySpace` so the actor has a `CenterPosition` and `OccupiedCells`, and it implements `IMove`/`IPositionable` so activities can query and set position. The `Locomotor` property is resolved in `Created` from the world actor. This is the ECS info/instance split described in [Part 1.1 — Entity-Component-System (ECS) and Actor Lifecycle](Part_01_Chapter_01_ECS.md).
- **`IPathFinder`** — A world-level service that exposes `FindPathToTargetCell`, `FindPathToTargetCells`, `FindPathToTargetCellByPredicate`, and domain checks. `Mobile` caches a reference to it in `Created`.
- **`PathFinder`** — The concrete `IPathFinder` trait. It builds two `HierarchicalPathFinder` instances per `Locomotor`: one that ignores actors (`BlockedByActor.None`) and one that accounts for immovable actors (`BlockedByActor.Immovable`). It also validates inputs, handles the reversed path convention, and routes to the correct HPF.
- **`HierarchicalPathFinder`** — The performance core. It divides the map into a 10x10-cell grid, builds abstract nodes for connected regions within each grid, and connects adjacent grids into an abstract graph. It also assigns a *domain* index to each abstract node; if two cells map to different domains, no path exists. When a real path is requested, it first searches the abstract graph to guide the local search, then runs a local A* with a much better heuristic than straight-line distance.
- **`PathSearch`** — Plain A* over any `IPathGraph`. It maintains an open priority queue of `GraphConnection` and `CellInfo` (status, cost so far, estimated total cost, previous node). It can expand unidirectionally or bidirectionally and supports a `heuristicWeightPercentage`.
- **`IPathGraph` / `MapPathGraph` / `GridPathGraph` / `SparsePathGraph`** — The graph abstraction used by `PathSearch`. `MapPathGraph` expands to neighboring cells using `Locomotor.MovementCostToEnterCell`, while `GridPathGraph` restricts expansion to a bounding box and `SparsePathGraph` is used for the abstract graph.
- **`Move`** — The activity that owns the path and drives execution. It delegates actual per-cell motion to `MoveFirstHalf` and `MoveSecondHalf`, which interpolate `CenterPosition` and `Facing` over the tick distance.
- **`MoveWithinRange`** — A specialization of `MoveAdjacentTo` that calls `FindPathToTargetCells` with a candidate set of cells in an annulus around the target. It is used by `Attack` activities to stay within weapon range while remaining outside minimum range.

### Why the path is reversed

`PathFinder` and `HierarchicalPathFinder` consistently return paths in the form:

```
[target, ..., intermediate, source]
```

The `Move` activity consumes this by repeatedly taking `path[^1]` (the last element, which is the next cell to enter) and then removing it. This convention makes path reconstruction cheap inside `PathSearch.MakePath` and also allows the hierarchical pathfinder to handle an *unreachable source* gracefully: a unit is allowed to be standing on an inaccessible cell (for example, it was dropped there) and must be able to move *out*, but it is never allowed to end a path on an inaccessible target.

### Blocking levels

`BlockedByActor` is an enum in `OpenRA.Mods.Common/TraitsInterfaces.cs` that controls how much other actors obstruct movement:

```
None      -> ignore all actors
Immovable -> ignore immovable actors only
Stationary -> ignore stationary actors (allow moving through moving actors)
All       -> fully blocked by any actor that isn't crushable or friendly-movable
```

`Move` tries the levels in order from most restrictive to least restrictive: `All`, `Stationary`, `Immovable`, `None`. If a path cannot be found while avoiding moving actors, it relaxes the constraint. This is the source of common "nudging" and "waiting" behavior.

![Data flow  code path diagram](images/Part_01_Chapter_05_Pathfinding_Movement-sequence-flow-diagram-tracing-the-execution-path-from-trigge-035864.svg)

## Data Flow / Code Path


### 1. Order generation and resolution

A player right-click on terrain triggers the order targeter in `Mobile.MoveOrderTargeter`. The targeter checks the terrain, shroud, and whether the unit is forced to require a force-move modifier. It returns an `Order` with `OrderString = "Move"`. [Part 1.3 — World, OrderManager, and Orders](Part_01_Chapter_03_World_Orders.md) covers the order pipeline and [Part 9.1 — OrderManager and Lockstep Foundation](Part_09_Chapter_01_OrderManager.md) covers the lockstep network flow that ensures every client receives the same order on the same tick.

### 2. From order to activity

`Mobile.ResolveOrder` receives the order:

```csharp
if (order.OrderString == "Move")
{
    var cell = self.World.Map.Clamp(self.World.Map.CellContaining(order.Target.CenterPosition));
    if (!Info.LocomotorInfo.MoveIntoShroud && !self.Owner.Shroud.IsExplored(cell))
        return;

    self.QueueActivity(order.Queued, WrapMove(new Move(self, cell, WDist.FromCells(8), null, true, Info.TargetLineColor)));
    self.ShowTargetLines();
}
```

`WrapMove` allows other traits (e.g., `Transports` or `Aircraft`) to wrap the ground movement activity in something else via `IWrapMove`. `ShowTargetLines` draws the green line that players see in the viewport.

### 3. The Move activity starts

`Move.OnFirstRun` runs once before the first tick. It sets `mobile.MoveResult = MoveResult.InProgress`, optionally recalculates the nearest movable cell, and then tries to find a path with increasingly relaxed blocking:

```csharp
foreach (var check in PathSearchOrder) // All, Stationary, Immovable, None
{
    (alreadyAtDestination, path) = EvalPath(check);
    if (alreadyAtDestination || path.Count > 0)
        return;
}
```

`EvalPath` calls the `getPath` delegate created in the `Move` constructor. The default delegate looks roughly like this:

```csharp
getPath = check =>
{
    if (mobile.ToCell == destination)
        return (true, PathFinder.NoPath);

    return (false, mobile.PathFinder.FindPathToTargetCell(
        self, [mobile.ToCell], destination, check, ignoreActor: ignoreActor));
};
```

### 4. PathFinder routes the request

`PathFinder.FindPathToTargetCell` does several important things:

1. Resolves the actor's `Locomotor` from `Mobile` (a cached shortcut because `PathFinder` requires `Mobile`).
2. Validates the target cell: it must be inside the map, on a valid layer, and have a finite movement cost.
3. For a single source, picks the appropriate `HierarchicalPathFinder` and calls `FindPath`.
4. For multiple sources, uses the same HPF but with a unidirectional search.
5. If a specific actor is to be ignored, it uses the `BlockedByActor.None` HPF to avoid accidentally routing through the ignored actor that the `Immovable` HPF might have cached as blocking.

### 5. HierarchicalPathFinder finds a route

For a typical long-distance move, the HPF does the following:

1. **Domain check.** It maps source and target to abstract nodes and compares their `abstractDomains`. If the domains differ, there is no path.
2. **Short-distance shortcut.** If source and target are within two grid distances, it attempts a local A* in a small bounding box first to avoid the cost of the abstract search.
3. **Abstract search.** It inserts temporary edges from the source and target cells into the abstract graph, then runs a `PathSearch` over the abstract graph using the default cost estimator. This produces an abstract route that is aware of obstacles such as cliffs, lakes, and buildings.
4. **Local search.** It creates a local `PathSearch` over the full map with a heuristic derived from the abstract search. The heuristic estimates remaining cost to the target by looking at the next abstract node along the abstract route, rather than using a straight-line distance. This dramatically reduces the number of cells explored.
5. **Bidirectional search.** For single-source/single-target requests, the HPF runs two local searches in opposite directions and joins them when they meet (`PathSearch.FindBidiPath`).
6. **Return.** The resulting path is reversed and returned to `PathFinder`, which returns it to `Move`.

### 6. PathSearch (A*)

`PathSearch` is the generic engine:

```
1. Add initial cells to the priority queue with cost = heuristic * weight / 100.
2. While the queue is not empty:
   a. Pop the lowest estimated-cost cell.
   b. If it is the target, reconstruct path and return.
   c. Mark it Closed.
   d. For each neighbor from IPathGraph.GetConnections:
      i. Compute new cost so far.
      ii. If neighbor is Closed or the new cost is not better, skip.
      iii. Compute estimated remaining cost via heuristic.
      iv. Update CellInfo and push to queue.
3. If the queue empties, return PathFinder.NoPath.
```

The heuristic is weighted by `HeuristicWeightPercentage` (default 125). A weight above 100 makes the search faster but the path may be up to that percentage longer than optimal. A weight of 100 produces an admissible A* search and the shortest path. The Red Alert mod leaves the default at 125, which is a good trade-off for typical RTS maps.

### 7. Move executes the path

Back in `Move.Tick`, the activity pops the next cell from the path. If the cell is blocked, it waits briefly, notifies blockers, and may repath. If the path is still valid, it queues the actual movement children:

- `MoveFirstHalf` interpolates from the current sub-cell position to the midpoint between cells, updating `CenterPosition` and `Facing` each tick.
- `MoveSecondHalf` interpolates from the midpoint to the center of the new cell.
- If the next cell requires a sharp turn, a `Turn` child is queued first.

When `MoveSecondHalf` completes, it calls `mobile.SetPosition(self, mobile.ToCell)`, which snaps the actor to the new cell, updates `ActorMap` influence, and triggers `FinishedMoving` notifications (including crushing). The `Move` activity then proceeds to the next path cell on the following tick.

### 8. Movement speed

`MoveFirstHalf.Tick` advances `progress` by `mobile.MovementSpeedForCell(mobile.ToCell)` per tick unless the previous part completed on the same tick. `Mobile.MovementSpeedForCell` applies the unit's base `Speed` to the terrain speed from `Locomotor.MovementSpeedForCell`, then multiplies by any `ISpeedModifier` traits. This is where YAML-defined speeds become world-unit motion. See [Part 1.4 — Deterministic Math and Coordinate Systems](Part_01_Chapter_04_Math.md) for the fixed-point [WPos](../appendices/Appendix_A_Glossary.md)/`WDist` math used in the interpolation.

![Configuration (yaml) diagram](images/Part_01_Chapter_05_Pathfinding_Movement-annotated-yaml-snippet-diagram-showing-the-key-fields-and-ho-6a1b98.svg)

## Configuration (YAML)


### Locomotor

Locomotors are defined on the world actor. In the Red Alert mod this is in `mods/ra/rules/defaults.yaml` or `mods/ra/rules/world.yaml` under the `World` actor:

```yaml
World:
    Locomotor@default:
        Name: default
        Crushes: crate, wall
        SharesCell: false
        MoveIntoShroud: true
        TerrainSpeeds:
            Clear: 100
                PathingCost: 100
            Rough: 70
            Road: 110
            Water: 0
```

Field reference:

| YAML key | C# field | Meaning |
| :---- | :---- | :---- |
| `Name` | `LocomotorInfo.Name` | Identifier referenced by `Mobile`. |
| `SharesCell` | `LocomotorInfo.SharesCell` | Allows multiple infantry-style units in one cell using sub-cells. |
| `MoveIntoShroud` | `LocomotorInfo.MoveIntoShroud` | Whether the unit can be ordered into unexplored terrain. |
| `Crushes` | `LocomotorInfo.Crushes` | Bitset of `CrushClass` types this locomotor can drive over. |
| `CrushDamageTypes` | `LocomotorInfo.CrushDamageTypes` | Damage types applied to crushed actors. |
| `TerrainSpeeds` | `LocomotorInfo.TerrainSpeeds` | Dictionary of terrain type to speed and optional `PathingCost`. A speed of `0` or missing entry means impassable. |
| `WaitAverage` / `WaitSpread` | `LocomotorInfo.WaitAverage` / `WaitSpread` | How long a unit waits before repathing when blocked. |

The `PathingCost` field is important: it is separate from the displayed speed. A terrain can have high speed but high pathing cost (e.g., a long detour), or low speed but low cost (e.g., a shortcut). The default cost is `10000 / speed`.

### Mobile

Mobile is attached to the actor itself:

```yaml
1TNK:
    Inherits: ^Vehicle
    Mobile:
        Locomotor: tracked
        Speed: 128
        TurnSpeed: 16
        Cursor: move
        TerrainCursors:
            Clear: move
            Water: move-blocked
```

Field reference:

| YAML key | C# field | Meaning |
| :---- | :---- | :---- |
| `Locomotor` | `MobileInfo.Locomotor` | Name of the `Locomotor` to use. Must exist on the world actor. |
| `Speed` | `MobileInfo.Speed` | Base speed applied to terrain speed. |
| `TurnSpeed` | `MobileInfo.TurnSpeed` | How fast the actor turns, in `WAngle` units per tick. |
| `AlwaysTurnInPlace` | `MobileInfo.AlwaysTurnInPlace` | Infantry-style; never use curved trajectories. |
| `TurnsWhileMoving` | `MobileInfo.TurnsWhileMoving` | Turn continuously during movement rather than stopping. |
| `CanMoveBackward` | `MobileInfo.CanMoveBackward` | Allows reversing. |
| `MaxBackwardCells` | `MobileInfo.MaxBackwardCells` | Maximum path length for which reversing is allowed. |
| `RequireForceMoveCondition` | `MobileInfo.RequireForceMoveCondition` | Boolean expression that forces the player to use force-move. |
| `ImmovableCondition` | `MobileInfo.ImmovableCondition` | Boolean expression that makes this actor immovable (affects pathfinder blocking). |
| `TerrainCursors` | `MobileInfo.TerrainCursors` | Cursor overrides per terrain type. |

### PathFinder

Also on the world actor:

```yaml
World:
    PathFinder:
        HeuristicWeightPercentage: 125
```

| YAML key | C# field | Meaning |
| :---- | :---- | :---- |
| `HeuristicWeightPercentage` | `PathFinderInfo.HeuristicWeightPercentage` | Weight applied to the A* heuristic. 100 = optimal, >100 = faster but possibly suboptimal. |

### PathFinderOverlay (debug)

```yaml
World:
    PathFinderOverlay:
        ShowCosts: true
```

This enables the `/path-debug` chat command when `DeveloperMode` is active. It renders the abstract graph (green lines) and the local search edges (yellow lines) for the selected actor, plus cost labels if `ShowCosts` is true.

### MapGrid

Although not part of movement directly, the `MapGrid` configuration in `mod.yaml` defines sub-cell offsets and whether the grid is rectangular or isometric. See [Part 1.4 — Deterministic Math and Coordinate Systems](Part_01_Chapter_04_Math.md) for the full `MapGrid` field reference. Sub-cells are central to `SharesCell` locomotors and `Locomotor.GetAvailableSubCell`.

## Interconnectivity

- **Depends on:**
  - **[Part 1.1 — Entity-Component-System (ECS) and Actor Lifecycle](Part_01_Chapter_01_ECS.md)** — `Actor`, `TraitInfo`/`Trait`, `IOccupySpace`, `Trait<T>` queries, and `Created`/`Tick` hooks.
  - **[Part 1.2 — Activities and the Game Loop](Part_01_Chapter_02_Activities.md)** — `Activity` lifecycle, `TickOuter`, `ChildActivity`, `QueueChild`, and `OnFirstRun`/`OnLastRun`.
  - **[Part 1.3 — World, OrderManager, and Orders](Part_01_Chapter_03_World_Orders.md)** — How `Move` orders are generated, buffered, and resolved.
  - **[Part 1.4 — Deterministic Math and Coordinate Systems](Part_01_Chapter_04_Math.md)** — `CPos`, `WPos`, `WVec`, `WAngle`, `WDist`, and `MapGrid` conversions.
  - **[Part 2.4 — Rulesets, Actors, and Weapons](Part_02_Chapter_04_Rules_Weapons.md)** — YAML loading of `LocomotorInfo` and `MobileInfo`, `IRulesetLoaded`, and `ActorInfo` dependency resolution.
  - **[Part 9.1 — OrderManager and Lockstep Foundation](Part_09_Chapter_01_OrderManager.md)** — Why only orders cross the network and why all movement must be deterministic.

- **Used by:**
  - Attack activities (`Attack`, `AttackMoveActivity`) that call `Mobile.MoveWithinRange` or `MoveToTarget`.
  - Harvester AI, which chains `Move` activities between resource fields and refineries.
  - [Part 8.3 — Bot Squads and Combat Heuristics](Part_08_Chapter_03_Squads.md), which issues move orders programmatically.
  - Lua map scripts (`Actor.Move` and `Actor.MoveTo`) that create `Move` activities via the actor's `IMove` interface.
  - The pathfinder overlay and debugging tools described in this chapter.

![Algorithms diagram](images/Part_01_Chapter_05_Pathfinding_Movement-algorithm-diagram-or-pseudocode-flowchart-for-the-non-trivia-5983ed.svg)

## Algorithms


### A* with a weighted heuristic

`PathSearch` implements A* on a graph where nodes are `CPos` cells and edges are movement costs. The cost of an edge from cell A to adjacent cell B is given by `Locomotor.MovementCostToEnterCell`. The heuristic used by default is the *diagonal distance* on the grid, scaled by the minimum terrain cost.

The weighted heuristic function is:

```
f(n) = g(n) + h(n) * weight / 100
```

where `g(n)` is the cost from the source to `n` and `h(n)` is the estimated cost from `n` to the target. When `weight = 100` the heuristic is admissible and A* is guaranteed optimal. When `weight > 100` the search expands fewer nodes but may return a path up to `weight - 100` percent longer than optimal.

### Hierarchical pathfinding

The map is divided into a 10x10 abstract grid. For each grid cell, the HPF flood-fills the reachable cells on each layer and creates one abstract node per connected region. Edges between abstract nodes are computed at grid boundaries and custom movement layer transitions. Each abstract node is also assigned a domain index via another flood fill; equal domains mean a path exists (ignoring movable actors).

When a real path is requested:

1. Source and target cells are mapped to abstract nodes.
2. An abstract A* search from source to target gives the high-level route.
3. The local A* heuristic at any cell `n` is the cost from `n` to the next abstract node along the abstract route, plus the remaining abstract cost. This guides the local search around obstacles rather than blindly toward the target.

This is a one-level abstraction. It handles terrain and immovable actors well, but it cannot predict congestion from other moving units, which is why `Move` can repath with a relaxed blocking level.

### Domain check

`HierarchicalPathFinder` assigns each abstract node a domain index. `PathFinder.PathExistsForLocomotor` and `PathMightExistForLocomotorBlockedByImmovable` compare domains to answer "is there any path?" cheaply. This is used by activities that want to avoid expensive path searches when the destination is on a different island of passable terrain.

### Cell blocking and crush logic

`Locomotor.CanMoveFreelyInto` is the authoritative rule. It checks:

1. Is the cell inside the map and on a valid layer?
2. Is the terrain cost finite?
3. Does the requested `BlockedByActor` level allow the actors currently in the cell?
4. Is the actor able to crush any occupant that would otherwise block it?

The result is cached in `Locomotor.blockingCache` per cell, with `CellFlag` bits for `HasMovingActor`, `HasStationaryActor`, `HasMovableActor`, `HasCrushableActor`, `HasTemporaryBlocker`, and `HasTransitOnlyActor`. The cache is marked dirty when `ActorMap.CellUpdated` fires and refreshed on the next read.

![Extension points diagram](images/Part_01_Chapter_05_Pathfinding_Movement-extension-hook-diagram-showing-the-interface-s-to-implement-b4a27b.svg)

## Extension Points


### Adding a new movement type

The most common extension is defining a new `Locomotor` and making actors use it. For example, a "hover" locomotor could ignore rough terrain by giving it a high speed on `Clear`, `Rough`, and `Road` while keeping `Water` at 0.

```yaml
Locomotor@hover:
    Name: hover
    SharesCell: false
    Crushes: crate
    TerrainSpeeds:
        Clear: 120
        Rough: 100
        Road: 120
        Water: 0
```

Then attach `Mobile` to an actor with `Locomotor: hover`.

### Custom movement layers

Implement `ICustomMovementLayer` (e.g., tunnels, subterranean travel, elevated bridges, jumpjets) to create movement layers above the ground layer. A locomotor must be enabled for the layer (`EnabledForLocomotor`) and provide entry/exit costs. The HPF automatically connects ground-layer grids to custom-layer grids when these costs are finite. This is an advanced topic; the existing TS/RA2 mods contain the primary examples.

### Custom path cost

`FindPathToTargetCell` accepts a `Func<CPos, int> customCost`. Returning `PathGraph.PathCostForInvalidPath` from this delegate marks the cell as impassable for this specific search. This is used by attack activities to avoid cells near the target that are already occupied by allies, or by scripted missions to mark no-go zones.

### Speed modifiers

Implement `ISpeedModifier` on a trait and add it to the actor. `Mobile.MovementSpeedForCell` collects all enabled modifiers and applies them as percentage multipliers to the final speed. This is used by veterancy, crates, and terrain-specific effects without changing the locomotor definition.

### IWrapMove

Implement `IWrapMove` to intercept every `Move` activity created by `Mobile`. `Transports` uses this to tell units to move into a transport rather than across the ground. This is an activity-level extension point, not a pathfinding one.

### PathFinderOverlay colors

The `PathFinderOverlayInfo` trait exposes colors and cost display. Mods can change the overlay appearance or disable cost labels by YAML overrides.

![Common pitfalls  guardrails diagram](images/Part_01_Chapter_05_Pathfinding_Movement-checklist-infographic-style-diagram-summarizing-the-top-pitf-fb069e.svg)

## Common Pitfalls / Guardrails


### Determinism

All pathfinding and movement must be [deterministic](../appendices/Appendix_A_Glossary.md). The OpenRA simulation layer contains no floating-point math for gameplay state. Use `WPos`, `WAngle`, `WDist`, `CPos`, and `CVec` ([Part 1.4 — Deterministic Math and Coordinate Systems](Part_01_Chapter_04_Math.md)). Do not use `Math.Sqrt`, `Random`, or `float` in path cost calculations. The world random (`self.World.SharedRandom`) is deterministic and seeded from the game state, but it should not be used in path cost evaluation because it would produce different paths on different clients.

### Source/target asymmetry

Path searches are deliberately asymmetric: a unit may leave an inaccessible cell but may never enter one. Swapping source and target arguments will often produce a `NoPath` result. Always call the correct API: `FindPathToTargetCell` for one target, `FindPathToTargetCells` for multiple targets, and `FindPathToTargetCellByPredicate` for a predicate search.

### Reversed paths

`PathFinder` returns paths in the form `[target, ..., source]`. Activities that forget this and try to read index `0` as the next step will move to the destination immediately. `Move` handles this by repeatedly reading the last element.

### Stale paths and repathing

A path is computed at a single tick in time. Other actors move, buildings are destroyed, and terrain may change. `Move` validates that the next cell is still adjacent (`Util.AreAdjacentCells`) and still enterable (`mobile.CanEnterCell`). If not, it repaths. Do not cache long paths across many ticks without revalidation.

### Heuristic weight and player perception

`PathFinderInfo.HeuristicWeightPercentage` default 125 can produce visibly non-optimal short paths. The HPF mitigates this by forcing a weight of 100 for short-distance local searches. If you increase the global weight, be aware that players may report "units taking the long way around."

### Blocking cache consistency

`Locomotor.UpdateCellBlocking` and `HierarchicalPathFinder.ActorIsBlocking`/`ActorCellIsBlocking` replicate the same blocking logic. If you change one, you must change the other. The source comments explicitly call this out. If they drift, the HPF may think a cell is blocked when the local pathfinder does not, or vice versa, causing inconsistent paths or failed domain checks.

### PathFinderOverlay is a cheat

`/path-debug` requires `DeveloperMode` to be enabled. It is intended for debugging only and should not be enabled in normal multiplayer rules. The overlay itself does not affect simulation state, but it is only accurate for the selected actor's most recent search.

### No exact path through dynamic crowds

The abstract graph only accounts for `BlockedByActor.Immovable` actors (buildings, trees, walls). It does not know where other moving units are. A path through a chokepoint may be valid at search time but blocked by a crowd when the unit arrives. The `Move` activity handles this by waiting, nudging, and repathing, but it can still fail if no route opens. Do not assume pathfinding will perfectly route around traffic jams.

## Summary

This chapter explains how OpenRA turns a destination cell into a sequence of smooth, deterministic unit motions.

After reading this chapter, you should be able to:

- Distinguish the roles of `Mobile`, `Locomotor`, `PathFinder`, `PathSearch`, `HierarchicalPathFinder`, and `Move`.
- Trace the complete flow from a player click to a unit arriving at a destination cell.
- Explain how terrain costs and actor blocking are combined into a movement graph.
- Describe how A* is used, why the heuristic is weighted, and what the abstract graph in `HierarchicalPathFinder` is for.
- Understand why paths are returned *reversed* and why source/target asymmetry matters.
- Read and modify YAML that configures locomotion, movement speed, and pathfinding debug overlays.
- Use the `/path-debug` command and interpret the pathfinding overlay.
- Identify common pitfalls: desyncs from non-deterministic movement, stale paths, and lane-bias assumptions.

If any of the concepts above feel unclear, review the relevant section before continuing. For source files and further reading, see the References section.


## References

- [Part 1.1 — Entity-Component-System (ECS) and Actor Lifecycle](Part_01_Chapter_01_ECS.md)
- [Part 1.2 — Activities and the Game Loop](Part_01_Chapter_02_Activities.md)
- [Part 1.3 — World, OrderManager, and Orders](Part_01_Chapter_03_World_Orders.md)
- [Part 1.4 — Deterministic Math and Coordinate Systems](Part_01_Chapter_04_Math.md)
- [Part 2.4 — Rulesets, Actors, and Weapons](Part_02_Chapter_04_Rules_Weapons.md)
- [Part 9.1 — OrderManager and Lockstep Foundation](Part_09_Chapter_01_OrderManager.md)
- `OpenRA.Mods.Common/Traits/World/PathFinder.cs`
- `OpenRA.Mods.Common/Pathfinder/PathSearch.cs`
- `OpenRA.Mods.Common/Pathfinder/HierarchicalPathFinder.cs`
- `OpenRA.Mods.Common/Pathfinder/IPathGraph.cs`
- `OpenRA.Mods.Common/Traits/World/Locomotor.cs`
- `OpenRA.Mods.Common/Traits/Mobile.cs`
- `OpenRA.Mods.Common/Activities/Move/Move.cs`
- `OpenRA.Mods.Common/Activities/Move/MoveWithinRange.cs`
- `OpenRA.Mods.Common/Traits/World/PathFinderOverlay.cs`
- `OpenRA.Mods.Common/TraitsInterfaces.cs` (`IPathFinder`, `IPositionable`, `IMove`, `BlockedByActor`)
- `OpenRA.Game/Traits/TraitsInterfaces.cs` (`IOccupySpace`, `IOrderTargeter`, `IIssueOrder`, `IResolveOrder`, `IActorMap`)
- `OpenRA.Game/Map/ActorInitializer.cs` (`LocationInit`, `SubCellInit`, `CenterPositionInit`, `FacingInit`)
- Amit Patel's game programming heuristics guide, referenced in `PathSearch.DefaultCostEstimator`: https://theory.stanford.edu/~amitp/GameProgramming/Heuristics.html

## What to read next

- [Part 1.6 — Combat, Damage, and Projectiles](Part_01_Chapter_06_Combat_Damage.md): movement exists mainly to put units in position to attack; this chapter shows how combat uses the same pathfinding, target, and trait patterns.
- [Part 9.1 — OrderManager and Lockstep Foundation](Part_09_Chapter_01_OrderManager.md): understand why every movement order is a deterministic, replayable order and how the network enforces the same tick for all clients.
- [Part 2.4 — Rulesets, Actors, and Weapons](Part_02_Chapter_04_Rules_Weapons.md): continue from YAML definitions to runtime traits, especially `LocomotorInfo` and `MobileInfo` loading.