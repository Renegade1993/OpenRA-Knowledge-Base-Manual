# Chapter 7.7 — Resource and Actor Placement

## Purpose

This chapter documents the subsystem that decides **where resources and [actors](../appendices/Appendix_A_Glossary.md) go on procedurally generated maps**. After terrain, elevation, water, and forests have been carved out, the map generator must place player spawns, resource fields, neutral structures, expansion points, and decorative actors without breaking fairness, symmetry, or playability. The code in `[Terraformer](../appendices/Appendix_A_Glossary.md).cs` and `Symmetry.cs` provides the core algorithms; `ClassicMapGenerator.cs` wires them together through YAML-driven parameters.

The placement layer is responsible for:

- Respecting the map's chosen symmetry (rotations and mirror) so that every player receives an equivalent starting position and equivalent access to resources.
- Keeping player spawns away from the map center and away from symmetry axes, while ensuring each spawn has enough buildable room.
- Converting noise patterns into concrete resource fields that cluster near resource-spawn actors and near player bases, but not inside base footprints.
- Placing actors (resource spawns, neutral buildings, civilians) into valid zones without overlapping each other or terrain that cannot hold them.
- Committing the drafted actor placements into the final map's actor and player definitions.

Understanding this subsystem is essential for anyone writing a custom map generator, tuning resource economics, or extending OpenRA with new terrain/resource/actor types.

## Learning Objectives


After studying this chapter, you should be able to:

- Explain how resources and actors are placed on procedurally generated maps while respecting fairness and symmetry.
- Describe the roles of Terraformer, ActorPlan, and Symmetry in placement.
- Build zoneable masks that exclude invalid terrain, ramps, actors, and resources.
- Use ResourceBias and PlanResources/GrowResources to create resource fields.
- Place player spawns, expansion clusters, and neutral buildings without overlapping.
- Trace how ActorPlans are baked into the final map's ActorDefinitions.

## Files

| File | Responsibility |
| :---- | :---- |
| `OpenRA.Mods.Common/MapGenerator/Terraformer.cs` | High-level map-generation utilities. Contains `PlanResources`, `GrowResources`, spawn placement (`ChooseSpawnInZoneable`, `SpawnBias`), actor placement helpers (`AddActor`, `AddDistributedActors`, `AddActorCluster`, `ProjectPlaceDezoneActor`, `DezoneActor`), zone management (`CheckSpace`, `GetZoneable`, `ZoneFromActors`, `ZoneFromResources`), and `BakeMap`. |
| `OpenRA.Mods.Common/MapGenerator/ActorPlan.cs` | Lightweight draft description of an actor to be placed on a map. Tracks location, ownership, footprint, and center offset, and can clone/relocate itself for symmetry projection. |
| `OpenRA.Mods.Common/MapGenerator/Symmetry.cs` | Defines `Mirror`, `WMirror`, and the rotate-and-mirror helpers used to duplicate points, cell layers, and `ActorPlan`s across the map's symmetry group. |
| `OpenRA.Mods.Common/Traits/World/ClassicMapGenerator.cs` | The primary consumer. Parses YAML parameters, orchestrates terrain generation, then calls `Terraformer` to place spawns, resources, expansions, and buildings, and finally calls `ReorderPlayerSpawns` and `BakeMap`. |
| `OpenRA.Mods.Common/MapGenerator/MultiBrush.cs` | Multi-purpose brush that can paint both tiles and embedded `ActorPlan`s; used by terrain/obstacle passes that also need to reserve actor space. |
| `OpenRA.Mods.Common/MapGenerator/CellLayerUtils.cs` | Grid conversion helpers (`CPos`/`WPos`/`MPos`), `OverCircle`, `ChebyshevRoom`, `FindRandomBest`, `PickWeighted`, and other primitives used heavily by placement algorithms. |
| `OpenRA.Mods.Common/Traits/World/ResourceLayer.cs` | Defines `ResourceLayerInfo` / `ResourceTypeInfo` and the `ResourceTypes` table consulted by `PlanResources` and `GrowResources`. |

![Architecture diagram](images/Part_07_Chapter_07_Resources_Actors-architecture-diagram-showing-the-main-classes-interfaces-and-9161e6.svg)

## Architecture


### Core Objects

```
[Terraformer] --owns--> [Map, ModData, ActorPlans]
[Terraformer] --uses--> [Symmetry.WMirror]
[Terraformer] --creates--> [ActorPlan]
[ActorPlan] --references--> [ActorReference, ActorInfo, Map]
[ClassicMapGenerator] --orchestrates--> [Terraformer]
[MultiBrush] --embeds--> [ActorPlan]
```

### `Terraformer`

`Terraformer` is the central utility class for a single map generation pass. It is constructed with:

- `MapGenerationArgs` — title, author, tileset, size, seed, settings YAML.
- `Map` — the mutable map being generated.
- `ModData` — rules and terrain info.
- `List<[ActorPlan](../appendices/Appendix_A_Glossary.md)>` — the shared draft list of all actors to be baked later.
- `Symmetry.Mirror` and `int Rotations` — the symmetry group.

It exposes `WMirror` (a grid-aware wrapper around the raw mirror) and `Rotations`, and it lazily computes `ProjectionSpacing`, a `[CellLayer](../appendices/Appendix_A_Glossary.md)<int>` that records, for each cell, half the minimum distance to any of its symmetry-projected positions. This layer is used to prevent placements from colliding with their own mirror images.

### `ActorPlan`

`ActorPlan` is a draft actor. It stores:

- `Map` and `ActorInfo` (resolved from the actor type in the rules).
- `ActorReference` — the actual YAML-ready reference, including `LocationInit` and `OwnerInit`.
- `Location` (CPos) and `WPosLocation` / `WPosCenterLocation` (convenience accessors that convert between cell and world coordinates).
- `Footprint()` — the occupied cells derived from `IOccupySpaceInfo.OccupiedCells`, falling back to the single location cell.
- `MaxSpan()` — the larger of footprint width/height, used to reserve enough space.
- `Clone()` — clones the underlying `ActorReference` so the same actor type can be placed at multiple symmetry projections.

By convention, `ActorPlan`s created by `Terraformer` constructors are owned by the neutral player unless explicitly changed.

### `Symmetry`

`Symmetry` defines the symmetry group abstractly:

- `Mirror` enum: `None`, `LeftMatchesRight`, `TopLeftMatchesBottomRight`, `TopMatchesBottom`, `TopRightMatchesBottomLeft`.
- `WMirror` adapts a mirror from the `WPos` (world) coordinate system to `CPos` (cell) coordinates. For `RectangularIsometric` grids, the mirror index is rotated by 2 because the cell grid is sheared relative to world space.
- `RotateAndMirrorActorPlan` clones an `ActorPlan` at each projected position.
- `RotateAndMirrorOverCPos` iterates every cell and applies a callback to each symmetry orbit, used by `ImproveSymmetry` to aggregate values.

The projection count is `rotations` if there is no mirror, otherwise `rotations * 2`.

### `ResourceBias`

`ResourceBias` is a small configuration object that tells `PlanResources` how to treat a specific location:

- `WPos` — the anchor point (e.g., an actor's center).
- `ExclusionRadius` — if set, no resources will be placed within this distance.
- `BiasRadius` — if set, the bias function is applied to every cell within this distance.
- `Bias` — a function `(int value, long wrSq) => int` that transforms the per-resource strength value based on squared world distance from the anchor.
- `ResourceType` — if set, the bias only affects that resource type; otherwise it affects all resources.

![Data flow  code path diagram](images/Part_07_Chapter_07_Resources_Actors-sequence-flow-diagram-tracing-the-execution-path-from-trigge-035864.svg)

## Data Flow / Code Path


The canonical caller is `ClassicMapGenerator.Generate`. The relevant portion of the flow, after terrain and water have been resolved, is:

### 1. Build the zoneable mask

```
zoneable = terraformer.GetZoneable(param.ZoneableTerrain, playable)
```

`GetZoneable`:
- Starts with `CheckSpace(zoneableTerrain, checkActors: true, checkResources: true, checkBounds: true, checkRamps: true)`.
- Intersects with the `playable` mask.
- For non-trivial symmetry, clears the central cell to avoid symmetry collisions at the origin.
- Runs `ImproveSymmetry(zoneable, false, (a, b) => a && b)` so a cell is only zoneable if all of its symmetry projections are also zoneable.

### 2. Place player spawns

```
for each symmetry group:
    chosenCPos = terraformer.ChooseSpawnInZoneable(...)
    spawn = new ActorPlan(map, "mpspawn") { Location = chosenCPos }
    resourceSpawnPreferences = terraformer.TargetWalkingDistance(...)
    terraformer.AddDistributedActors(
        zoneable, resourceSpawnPreferences,
        param.ResourceSpawnWeights,
        param.SpawnResourceSpawns,
        weighted: false,
        actorDezoneRadius: ResourceSpawnReservation)
    terraformer.ProjectPlaceDezoneActor(spawn, zoneable, SpawnReservation)
```

Only one `mpspawn` is chosen per symmetry group; `ProjectPlaceDezoneActor` automatically mirrors it into `symmetryCount` total spawns.

### 3. Place expansion clusters

```
while resourceSpawnsRemaining > 0:
    added = terraformer.AddActorCluster(...)
    resourceSpawnsRemaining -= added
```

Each cluster picks a random spot with enough room and fills a ring/annulus around it with resource-spawn actors.

### 4. Place neutral buildings

```
for each target building:
    terraformer.AddActor(buildingRandom, zoneable, buildingType)
```

Buildings are placed one at a time into the remaining zoneable space.

### 5. Plan resources

```
resourcePattern = terraformer.ResourceNoise(...)
resourceBiases = [
    biases toward each resource-spawn actor type,
    biases toward player spawns (with exclusion zone for base)
]
(plan, typePlan) = terraformer.PlanResources(
    resourcePattern, mask, param.DefaultResource, resourceBiases)
```

### 6. Grow resources

```
targetResourceValue = param.ResourcesPerPlayer * entityMultiplier / EntityBonusMax
terraformer.GrowResources(plan, typePlan, targetResourceValue)
terraformer.ZoneFromResources(zoneable, false)
```

### 7. Place civilian decorations

```
decorationNoise = terraformer.DecorationPattern(...)
terraformer.PaintActors(decorationTilingRandom, decorationNoise, ...)
```

### 8. Finalize

```
terraformer.RepaintTiles(repaintRandom, param.RepaintTiles)
terraformer.ReorderPlayerSpawns()
terraformer.BakeMap()
```

`ReorderPlayerSpawns` sorts `mpspawn` actors clockwise around the map center and rotates the list so the first spawn is the one after the largest angular gap. `BakeMap` converts the `ActorPlans` list into `Map.ActorDefinitions` and derives `Map.PlayerDefinitions` from the number of `mpspawn` actors.

![Configuration (yaml) diagram](images/Part_07_Chapter_07_Resources_Actors-annotated-yaml-snippet-diagram-showing-the-key-fields-and-ho-6a1b98.svg)

## Configuration (YAML)


`ClassicMapGenerator` loads a `Settings` MiniYaml block. The keys most relevant to resource and actor placement are listed below. They map to fields in the nested `Parameters` class.

### Symmetry

| Key | C# Field | Meaning |
| :---- | :---- | :---- |
| `Rotations` | `Rotations` | Rotational symmetry count. Allowed: 1, 2, 4. |
| `Mirror` | `Mirror` | Mirror symmetry; parsed by `Symmetry.TryParseMirror`. |
| `CentralSpawnReservationFraction` | `CentralSpawnReservationFraction` | Fraction (out of `FractionMax` = 1000) of the map's smallest dimension used as a central/axis reservation for spawns. |

### Player Spawn Placement

| Key | C# Field | Meaning |
| :---- | :---- | :---- |
| `MinimumSpawnRadius` | `MinimumSpawnRadius` | Minimum Chebyshev room a spawn cell must have. |
| `SpawnRegionSize` | `SpawnRegionSize` | Maximum region radius considered for spawn preference. |
| `SpawnBuildSize` | `SpawnBuildSize` | Radius of the base-building area reserved around each spawn (resource exclusion). |
| `SpawnReservation` | `SpawnReservation` | General clear radius around each spawn. |
| `SpawnResourceSpawns` | `SpawnResourceSpawns` | Number of resource-spawn actors placed near each spawn. |
| `ResourceSpawnReservation` | `ResourceSpawnReservation` | Clear radius around each resource-spawn actor. |

### Resource Generation

| Key | C# Field | Meaning |
| :---- | :---- | :---- |
| `ResourcesPerPlayer` | `ResourcesPerPlayer` | Target resource value per player. |
| `ResourceFeatureSize` | `ResourceFeatureSize` | Noise wavelength for resource pattern. |
| `OreClumpiness` | `OreClumpiness` | Clumpiness of the resource noise. |
| `OreUniformity` | `OreUniformity` | Minimum value added to the noise pattern (in 1024ths). |
| `SpawnResourceBias` | `SpawnResourceBias` | Strength of the bias pulling resources toward player spawns. |
| `DefaultResource` | `DefaultResource` | Fallback resource type when no bias selects a type. |
| `ResourceSpawnSeeds` | `ResourceSpawnSeeds` | Mapping from actor type name to resource type name; biases resources toward each placed seed actor. |
| `ResourceSpawnWeights` | `ResourceSpawnWeights` | Weighted table of resource-spawn actor types used by `AddDistributedActors` and `AddActorCluster`. |

### Expansion and Neutral Buildings

| Key | C# Field | Meaning |
| :---- | :---- | :---- |
| `MaximumExpansionResourceSpawns` | `MaximumExpansionResourceSpawns` | Budget for expansion resource spawns. |
| `MaximumResourceSpawnsPerExpansion` | `MaximumResourceSpawnsPerExpansion` | Max actors per expansion cluster. |
| `MinimumExpansionSize` / `MaximumExpansionSize` | `MinimumExpansionSize` / `MaximumExpansionSize` | Cluster radius bounds. |
| `ExpansionInner` | `ExpansionInner` | Inner radius kept clear within a cluster. |
| `ExpansionBorder` | `ExpansionBorder` | Outer spacing required beyond the cluster radius. |
| `MinimumBuildings` / `MaximumBuildings` | `MinimumBuildings` / `MaximumBuildings` | Range of neutral buildings to place. |
| `BuildingWeights` | `BuildingWeights` | Weighted table of neutral building types. |
| `CivilianBuildings` | `CivilianBuildings` | Fraction of map to cover with civilian decoration actors. |

All fraction fields use `FractionMax = 1000` as the denominator.

## Interconnectivity

- **Depends on:**
  - **Terrain generation** (`Terraformer` elevation slicing, `CheckSpace`, `GetZoneable`) — placement is only valid on `playable` / `zoneable` cells.
  - **Noise utilities** (`NoiseUtils.SymmetricFractalNoiseIntoCellLayer`, `ResourceNoise`) — produces the raw resource pattern before biasing.
  - **Symmetry** (`Symmetry.cs`) — every actor placement and many cell layers are mirrored/rotated through the symmetry group.
  - **Cell layer utilities** (`CellLayerUtils`) — distance transforms, random-best selection, weighted picks, circle iteration, and coordinate conversion.
  - **Ruleset** (`ResourceLayerInfo`, `PlayerResourcesInfo`) — resolves `ResourceTypeInfo` and per-resource values/densities.

- **Used by:**
  - **Map generator UI** (`ClassicMapGeneratorInfo` implements `IEditorMapGeneratorInfo`) — exposes the YAML settings to the editor.
  - **Map save/load** — `BakeMap` produces the final `Map.ActorDefinitions` and `Map.PlayerDefinitions`.
  - **Custom map generators** — can reuse `Terraformer` placement helpers for new algorithms.

![Algorithms diagram](images/Part_07_Chapter_07_Resources_Actors-algorithm-diagram-or-pseudocode-flowchart-for-the-non-trivia-5983ed.svg)

## Algorithms


### PlanResources

`PlanResources` takes:

- `pattern` — a `CellLayer<int>` noise pattern (values ≥ 0 are candidates, negative values are ignored).
- `mask` — a `CellLayer<bool>` limiting where resources may appear.
- `defaultResource` — the fallback `ResourceTypeInfo`.
- `resourceBiases` — a list of `ResourceBias` objects.

It returns a tuple `(plan, typePlan)` where `plan` is a scored `CellLayer<int>` and `typePlan` selects the resource type per cell.

Steps:

1. **Collect resource types.** Read `ResourceTypes` from the world's `ResourceLayerInfo`, ordered by key.
2. **Build allowed terrain combos.** For each resource type, collect `(resourceTypeInfo, terrainIndex)` pairs for every terrain name in `AllowedTerrainTypes`. Only these combinations can hold a resource.
3. **Initialize per-resource strengths.** Each resource type gets a `CellLayer<int>` filled with `1`.
4. **Apply biases.** For each `ResourceBias` with both `Bias` and `BiasRadius` set:
   - Determine the target types: either `ResourceType` if specified, or all resource types.
   - For each target type, iterate over the circle defined by `BiasRadius` and apply `Bias(strength, wrSq)` to every cell, where `wrSq` is the squared world distance from the bias anchor.
5. **Select the winning type per cell.** For each cell, pick the resource type with the highest strength and record it in `bestResource`. Initialize `bestResource` to `defaultResource`.
6. **Score the plan.** `plan[mpos] = pattern[mpos] * maxStrength1024ths[mpos]` for candidate cells; otherwise `-int.MaxValue`.
7. **Apply mask and terrain legality.** Any cell that is masked out or whose terrain does not support the winning resource type is set to `-int.MaxValue`.
8. **Apply exclusions.** For each `ResourceBias` with `ExclusionRadius`, mark all cells inside the radius as `-int.MaxValue`.
9. **Improve symmetry.** Run `ImproveSymmetry(plan, -int.MaxValue, int.Min)` so that the plan is consistent across the symmetry group. The aggregator `int.Min` keeps the worst score among projections; if any projection is illegal, the whole orbit is illegal.

Important: `ResourceBias` functions are applied in input order, but **exclusions always take precedence** because they run after the scoring phase.

### GrowResources

`GrowResources` consumes the `plan` and `typePlan` from `PlanResources` and places actual resource tiles until a target value is reached.

Steps:

1. Clear `Map.Resources`.
2. Build a `PriorityArray<int>` where lower values mean higher priority. Each cell's priority is `-plan[value]`.
3. Repeatedly pop the minimum-priority cell, mirror it through the symmetry group, and place resources for every valid projection.
4. For each placed cell, compute the density using the same adjacency logic as the runtime `ResourceLayer` (or save a baked density if `BakedAdjacency` is selected).
5. The value contributed by a cell is the 3×3 sum of `resourceValue * density`.
6. Stop when `remaining` target value drops to zero or no legal cells remain.

The density hack uses a lerp to `9` even though the maximum adjacent resources is `8` because changing it would disrupt existing generated maps.

### ResourceBias

A `ResourceBias` is the primary mechanism for shaping resource fields around actors.

- **Exclusion radius** (`ExclusionRadius`) creates a hard no-resource zone. This is used to keep the base-building area around a player spawn free of ore.
- **Bias radius** (`BiasRadius`) creates a soft zone where the custom function modifies the strength score.
- **Bias function** receives `(int currentValue, long squaredWorldDistance)` and returns the new value. The squared distance is in `WDist` units (1024 per cell). A typical function adds a falloff term such as `1024*1024 / (1024 + sqrt(rSq))`.
- **Resource type** (`ResourceType`) restricts the bias to a single resource type. When omitted, the bias affects all resources equally, which means it can boost the likelihood of *any* resource appearing near that anchor, but the type-plan still picks the highest-strength type.

### Spawn Placement

`ChooseSpawnInZoneable` finds a player spawn using a multi-stage scoring process:

1. **Spawn bias.** `SpawnBias(centralReservationFraction)` creates a `CellLayer<int>` that is low near the center and symmetry axes and rises toward the edges. It is computed by:
   - Creating a circle around the map center with radius `minSpan * centralReservationFraction / FractionMax`.
   - For each cell inside the circle, the value is the distance from the center in cells.
   - Clamping by `ProjectionSpacing` so that cells close to their own symmetry projections are not preferred.
2. **Roominess.** `CellLayerUtils.ChebyshevRoom` computes the Chebyshev distance to the nearest non-zoneable cell.
3. **Preference filter.** A cell is valid only if its roominess ≥ `minimumRadius` and its projection spacing can accommodate `zoneRadius + minimumRadius`. Valid cells are scored as `spawnBias * min(maximumRadius, roominess)`; invalid cells are zero.
4. **Random best.** `FindRandomBest` picks uniformly among the highest-scoring cells.

After a spawn is chosen, `ProjectPlaceDezoneActor` clones it across the symmetry group and subtracts its reservation radius from `zoneable`.

### Actor Planning and Symmetry Projection

Every actor placement in `Terraformer` goes through the same projection pipeline:

```
ActorPlan original
    -> Symmetry.RotateAndMirrorActorPlan(original, Rotations, WMirror)
        -> for each projection point:
               clone = original.Clone()
               clone.WPosCenterLocation = point
               projections.Add(clone)
    -> ActorPlans.AddRange(projections)
    -> foreach projection:
           DezoneActor(projection, zoneable, dezoneRadius)
```

`DezoneActor` first marks every cell in the actor's `Footprint()` as non-zoneable, then optionally clears a circle around the actor's center.

### BakeMap

`BakeMap` is the final commit step:

1. Count `mpspawn` actors to determine the number of players.
2. Create `MapPlayers` from the rules and assign `Map.PlayerDefinitions`.
3. Filter out any `ActorPlan` whose projected footprint does not intersect the map (using `Map.ProjectedCellsCovering` and `Map.Contains`).
4. Save each surviving plan as a `MiniYamlNode` named `Actor0`, `Actor1`, etc., and assign `Map.ActorDefinitions`.

Note: `HasProjectedFootprintInMap` calls `Map.ProjectedCellsCovering`, which can initialize the map's cell projection caches. After `BakeMap`, further edits to height or tile data could invalidate those caches.

### ReorderPlayerSpawns

After all symmetry-projected spawns are in `ActorPlans`, `ReorderPlayerSpawns` ensures the lobby order is intuitive:

1. Extract all `mpspawn` actors.
2. Compute polar coordinates relative to the map center (`WAngle.ArcTan(dy, dx)` and radius squared).
3. Sort clockwise by angle.
4. Find the largest angular gap between consecutive spawns; the spawn after that gap becomes "A".
5. Tie-breakers prefer the leftmost, then topmost, spawn.
6. Rotate the list so "A" is first and append it back to `ActorPlans`.

This makes the spawn order in the map file correspond to the visual clockwise order, which is important for the lobby and team assignment UI.

![Extension points diagram](images/Part_07_Chapter_07_Resources_Actors-extension-hook-diagram-showing-the-interface-s-to-implement-b4a27b.svg)

## Extension Points


### Writing a New Map Generator

The most direct extension is to implement a new `IEditorMapGeneratorInfo` / `IMapGeneratorInfo` trait (see `ClassicMapGeneratorInfo` for the pattern) and call `Terraformer` helpers directly. The recommended approach is:

1. Create a `List<ActorPlan>`.
2. Construct a `Terraformer` with the desired `Mirror` and `Rotations`.
3. Build masks using `CheckSpace`, `GetZoneable`, and `ChoosePlayableRegion`.
4. Place `mpspawn` actors with `ChooseSpawnInZoneable` and `ProjectPlaceDezoneActor`.
5. Place other actors with `AddActor`, `AddDistributedActors`, or `AddActorCluster`.
6. Generate resources with `ResourceNoise`, `PlanResources`, and `GrowResources`.
7. Call `ReorderPlayerSpawns` and `BakeMap`.

### Custom Resource Biases

A new generator can supply arbitrary `ResourceBias` functions. For example:

```csharp
new Terraformer.ResourceBias(actorPlan)
{
    ExclusionRadius = new WDist(5 * 1024),
    BiasRadius = new WDist(20 * 1024),
    Bias = (value, rSq) => value + (int)(1024L * 1024L / Math.Max(rSq, 1024L)),
    ResourceType = myResourceType
}
```

Because the bias function receives squared world distance, it can implement any radial falloff: linear, inverse, Gaussian, step, etc.

### New Resource Types

Adding a resource type is mostly a rules/YAML change:

1. Define a new `ResourceTypeInfo` under the world's `ResourceLayer` trait.
2. Ensure `AllowedTerrainTypes` lists terrain names that exist in the tileset.
3. Add the resource to `PlayerResourcesInfo.ResourceValues` so `GrowResources` can compute its value.
4. Reference the new type by name in `DefaultResource` or `ResourceSpawnSeeds`.

`PlanResources` will automatically discover the new type from `ResourceTypes`.

### New Actor Types

Actors used by the generator need:

- A valid `ActorInfo` in the rules.
- An `IOccupySpaceInfo` implementation (usually `BuildingInfo` or `MobileInfo`) so `Footprint()` returns occupied cells.
- For `mpspawn`, the actor type name must be exactly `"mpspawn"` because `BakeMap` and `ReorderPlayerSpawns` key off it.

### Custom Symmetry

`Symmetry.Mirror` is a closed enum, but `WMirror` handles the coordinate-system conversion. If you add a new mirror, you must implement `MirrorPointAround` in both `int2` and `WPos` forms and update `RotateAndMirrorProjectionCount`. Grid-aware consumers like `WMirror.ForCPos` must also know how to transform the mirror for `RectangularIsometric` grids.

### Adding New Placement Algorithms

`Terraformer` provides composable primitives:

- `ChooseInZoneable` — random cell with maximum Chebyshev room.
- `TargetWalkingDistance` — score cells by walk distance from seeds, useful for road/resource placement.
- `ErodeZones` / `DilateZones` — shrink/grow zoneable masks.
- `ImproveSymmetry` — aggregate a cell layer across the symmetry group.
- `ProjectionSpacing` — distance to the nearest symmetry projection.

These can be combined into new high-level placement strategies without modifying the existing helpers.

![Common pitfalls  guardrails diagram](images/Part_07_Chapter_07_Resources_Actors-checklist-infographic-style-diagram-summarizing-the-top-pitf-fb069e.svg)

## Common Pitfalls / Guardrails


### Determinism

Map generation is expected to be deterministic for a given seed. `Terraformer` does not use global `Random`; every call site receives a `MersenneTwister` derived from the master seed. When adding a new random-consuming step, derive a new `MersenneTwister(random.Next())` and do not reorder existing derivations, or previously generated maps will change.

### Symmetry Count Mismatch

`ClassicMapGenerator.Validate` enforces `Players % symmetryCount == 0`. The symmetry count is `Rotations` if `Mirror == None`, else `Rotations * 2`. If you add spawns manually, ensure the total number of `mpspawn` actors equals the desired player count; `BakeMap` derives the player count from this.

### WPos vs. CPos vs. MPos

- `WPos` is world coordinates (1024 units per cell). Symmetry math is performed in `WPos` for accuracy, then snapped to `CPos` for grid placement.
- `CPos` is the canonical cell coordinate. `ActorPlan.Location` is a `CPos`.
- `MPos` is the internal map-array coordinate. `CellLayer<T>` is indexed by `MPos`.

Functions like `CellLayerUtils.OverCircle` operate on `CellLayer` and take `WPos` centers, so distances are accurate even on non-rectangular grids.

### Grid Type Differences

`RectangularIsometric` grids shear the CPos grid relative to WPos. `WMirror.ForCPos` rotates the mirror index by 2 to compensate. If you write a new symmetry-aware function, use `WMirror` consistently rather than raw `Mirror` values.

### Footprint Projection

`BakeMap` filters actors by their **projected footprint**, not by `Map.Tiles.Contains` or `Map.Bounds.Contains`. An actor whose center is inside the map but whose footprint extends partially outside can still be saved if any projected cell is inside `Map.Contains`. Conversely, an actor whose center is outside but whose footprint reaches inside can also be saved.

### Resource Density

`GrowResources` density computation contains a deliberate off-by-one (`lerp` to `9` instead of `8`). Fixing it would change the visual density and economic value of generated maps. Any new density mode must be explicitly added to `ResourceDensityMode`.

### Zoneable After BakeMap

`BakeMap` can trigger cell-projection initialization. Modifying the map after calling it (e.g., changing tiles or heights) may leave cached projection data inconsistent. Perform all terrain and actor edits before `BakeMap`.

### Ordering of Biases

`PlanResources` applies bias functions in the order supplied, but exclusions are applied last. If two biases overlap, the later one wins for the strength value, but any exclusion from any bias will still force `-int.MaxValue`. Plan your bias list carefully when mixing multiple resource types and spawn anchors.

### Avoiding the Center

`GetZoneable` automatically clears the central cell when symmetry is non-trivial. If you write a custom zoneable builder, remember to do this; otherwise actors or resources placed at the center can collide with their own projections at the origin.

## What to read next

- [Part 7.4 — Terraformer](Part_07_Chapter_04_Terraformer.md) for the full set of helper methods used during actor and resource placement.
- [Part 7.6 — Mod-Specific Generators](Part_07_Chapter_06_Mod_Generators.md) to see how `ClassicMapGenerator` wires placement into a complete generator.
- [Part 7.8 — Random Map Generator Extension Points](Part_07_Chapter_08_Extension_Points.md) for custom generator and placement options.

## Summary

This chapter documents the subsystem that decides **where resources and [actors](../appendices/Appendix_A_Glossary.md) go on procedurally generated maps**.

After reading this chapter, you should be able to:

- **Collect resource types.** Read `ResourceTypes` from the world's `ResourceLayerInfo`, ordered by key.
- **Build allowed terrain combos.** For each resource type, collect `(resourceTypeInfo, terrainIndex)` pairs for every terrain name in `AllowedTerrainTypes`. Only these combinations can hold a resource.
- **Initialize per-resource strengths.** Each resource type gets a `CellLayer<int>` filled with `1`.
- **Apply biases.** For each `ResourceBias` with both `Bias` and `BiasRadius` set:

If any of the concepts above feel unclear, review the relevant section before continuing. For source files and further reading, see the References section.


## References

- `OpenRA.Mods.Common/MapGenerator/Terraformer.cs` — core placement helpers.
- `OpenRA.Mods.Common/MapGenerator/ActorPlan.cs` — draft actor representation.
- `OpenRA.Mods.Common/MapGenerator/Symmetry.cs` — rotate-and-mirror primitives.
- `OpenRA.Mods.Common/MapGenerator/CellLayerUtils.cs` — grid and distance utilities.
- `OpenRA.Mods.Common/MapGenerator/MultiBrush.cs` — brushes that embed actors.
- `OpenRA.Mods.Common/Traits/World/ClassicMapGenerator.cs` — primary orchestrator.
- `OpenRA.Mods.Common/Traits/World/ResourceLayer.cs` — `ResourceLayerInfo` / `ResourceTypeInfo` definitions.
- `OpenRA.Game/Map/Map.cs` — `Map.ActorDefinitions`, `Map.PlayerDefinitions`, `ProjectedCellsCovering`.
- `OpenRA.Game/Map/MapPlayers.cs` — player definition generation from spawn count.