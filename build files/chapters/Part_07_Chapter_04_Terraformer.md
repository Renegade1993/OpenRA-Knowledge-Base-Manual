# Chapter 7.4 — Terraformer

## Purpose

`[Terraformer](../appendices/Appendix_A_Glossary.md)` is the high-level orchestration class for OpenRA procedural map generation. While the algorithmic primitives live in `NoiseUtils`, `MatrixUtils`, and `Symmetry`, and the brush engine lives in `[MultiBrush](../appendices/Appendix_A_Glossary.md)`, the `Terraformer` is the place where a generator author actually calls those pieces together to create a playable, balanced, and visually coherent map. It provides a single mutable workspace that holds:

- the `Map` being generated,
- a list of `[ActorPlan](../appendices/Appendix_A_Glossary.md)`s that will eventually be baked into the map's actor definitions,
- the symmetry settings (`WMirror`, `Rotations`),
- and convenience wrappers for terrain selection, space analysis, path tiling, resource placement, actor placement, and symmetry enforcement.

A generator typically constructs one `Terraformer` at the start of a run, mutates the map through `Terraformer` calls, and finally calls `BakeMap()` to produce the final map file. The class is deliberately stateful and procedural: it owns the workspace, it expects callers to mutate it in order, and it exposes idempotent or order-dependent helper methods that compose the map one layer at a time.

## Learning Objectives


After studying this chapter, you should be able to:

- Explain the role of Terraformer as the high-level map generation orchestrator.
- Describe the workspace (Map, ActorPlans, symmetry settings) and its lifecycle.
- Use Terraformer methods to generate terrain, roads, actors, and resources.
- Enforce symmetry with ImproveSymmetry and ProjectionSpacing.
- Trace InitMap and BakeMap and explain what they finalize.
- Implement a custom generator phase using the Terraformer toolbox.

## Files

| File | Responsibility |
| :---- | :---- |
| `OpenRA.Mods.Common/MapGenerator/Terraformer.cs` | The `Terraformer` class and all high-level map generation helpers: initialization, symmetry, noise, zoning, painting, path/contour operations, actor placement, and resource planning. |
| `OpenRA.Mods.Common/MapGenerator/CellLayerUtils.cs` | Conversions between `CellLayer`, `Matrix`, `CPos`, and `WPos`; wrappers for `MatrixUtils.BordersToPoints`. |
| `OpenRA.Mods.Common/MapGenerator/MatrixUtils.cs` | Low-level boolean morphology, contour/path extraction, distance transforms, and `BordersToPoints` used by `PlanPassages` and `PlanRoads`. |
| `OpenRA.Mods.Common/MapGenerator/NoiseUtils.cs` | Fractal noise generation consumed by `Terraformer.BooleanNoise`, `ElevationNoiseMatrix`, and `ResourceNoise`. |
| `OpenRA.Mods.Common/MapGenerator/Symmetry.cs` | Rotational and mirror-symmetry operations consumed by `ImproveSymmetry`, actor projection, and `ProjectionSpacing`. |
| `OpenRA.Mods.Common/MapGenerator/MultiBrush.cs` | Tile/actor super-brush engine used by `PaintArea`, `PaintTiling`, `PaintLoopsAndFill`, and `RepaintTiles`. |
| `OpenRA.Mods.Common/MapGenerator/TilingPath.cs` | Path-aware tiling used by `PartitionPath` and `PaintLoopsAndFill`. |
| `OpenRA.Mods.Common/MapGenerator/ActorPlan.cs` | Mutable actor placement plan used by `ActorPlans`, `ProjectPlaceDezoneActor`, and `ReorderPlayerSpawns`. |

![Architecture diagram](images/Part_07_Chapter_04_Terraformer-architecture-diagram-showing-the-main-classes-interfaces-and-9161e6.svg)

## Architecture


`Terraformer` is a single-instance-per-map workspace. The constructor captures everything needed to produce the map, then the public methods mutate the workspace or return derived layers.

```
MapGenerationArgs
       |
       v
new Terraformer(map, modData, actorPlans, mirror, rotations)
       |
       +-- Map  ........................... mutable map tile/height/actor data
       +-- ActorPlans  .................... mutable list of planned actors
       +-- WMirror / Rotations  ........... symmetry settings
       +-- terrainInfo / templatedTerrainInfo  (cached tileset rules)
       +-- lazyProjectionSpacing  ........... Chebyshev distance to nearest symmetry projection
       |
       v
   InitMap()  --> set Map bounds, title, author, mod
       |
       v
   (generate terrain / paths / actors / resources)
       |
       v
   BakeMap()  --> create PlayerDefinitions, ActorDefinitions
```

### Core types defined in `Terraformer`

- **`Terraformer`** — main orchestration class.
- **`ResourceBias`** — describes how to bias or exclude resource placement near a point or actor.
- **`Region`** — metadata for connected regions returned by `FindRegions`.
- **`PathPartitionZone`** — describes a zone segment when partitioning a path (e.g., water, land, road).
- **`Side` enum** — `Out = -1`, `None = 0`, `In = 1`; used by `InsideOutside` and `PaintLoopsAndFill`.
- **`ResourceDensityMode` enum** — controls how resource density is interpreted: `Adjacency` (runtime calculated) or `BakedAdjacency` (saved to map data).
- **`FractionMax = 1000`** — common denominator for fractional arguments; many parameters are expressed as `N / 1000`.

### Key fields and construction

The constructor caches `terrainInfo`, extracts `templatedTerrainInfo` if the current tileset supports templates, and lazily builds a `projectionSpacing` layer. `ProjectionSpacing` computes, for each cell, half the distance to its nearest symmetry-projection copy. It is used everywhere the generator needs to avoid placing an object so close to its own mirror image that the two placements collide.

```csharp
public Terraformer(
    MapGenerationArgs mapGenerationArgs,
    Map map,
    ModData modData,
    List<ActorPlan> actorPlans,
    Symmetry.Mirror mirror,
    int rotations)
{
    MapGenerationArgs = mapGenerationArgs;
    Map = map;
    ModData = modData;
    ActorPlans = actorPlans;
    WMirror = new Symmetry.WMirror(mirror, map.Grid.Type);
    Rotations = rotations;
    terrainInfo = modData.DefaultTerrainInfo[map.Tileset];
    templatedTerrainInfo = terrainInfo as ITemplatedTerrainInfo;
    lazyProjectionSpacing = new(ProjectionSpacing);
}
```

![Data flow  code path diagram](images/Part_07_Chapter_04_Terraformer-sequence-flow-diagram-tracing-the-execution-path-from-trigge-035864.svg)

## Data Flow / Code Path


A typical procedural map generator using `Terraformer` follows this sequence:

1. **Create the workspace.**
   ```csharp
   var terraformer = new Terraformer(args, map, modData, actorPlans, mirror, rotations);
   terraformer.InitMap();
   ```

2. **Generate terrain.**
   - Use `ElevationNoiseMatrix` to get a height field.
   - Use `SliceElevation` to threshold the field into land/water masks.
   - Use `BooleanNoise` for additional masks (clumps, roughness, etc.).
   - Paint base terrain via `PaintArea` / `PaintActors` / `RepaintTiles`.
   - Carve passageways with `PlanPassages` and fill them in.

3. **Generate roads / rivers / cliffs.**
   - Use `PlanRoads` or external contour extraction to get point paths.
   - Use `PartitionPath` / `PartitionPaths` to assign segment types to sub-paths.
   - Use `PaintLoopsAndFill` or `PaintTiling` to stamp the path tiles.

4. **Place actors and resources.**
   - Build masks with `CheckSpace` / `GetZoneable`.
   - Place spawns with `ChooseSpawnInZoneable` and `ProjectPlaceDezoneActor`.
   - Place other actors with `AddActor`, `AddDistributedActors`, or `AddActorCluster`.
   - Place resources with `PlanResources` and `GrowResources`.
   - Optionally run `ReorderPlayerSpawns` before baking.

5. **Commit everything.**
   ```csharp
   terraformer.BakeMap();
   ```

### `InitMap`

`InitMap` sets the play area bounds, title, author, and required mod. It accounts for the maximum terrain height when computing the bottom-right bound, because the topmost row of an elevated map is reserved for height projection.

```csharp
public void InitMap()
{
    var maxTerrainHeight = Map.Grid.MaximumTerrainHeight;
    var tl = new PPos(1, 1 + maxTerrainHeight);
    var br = new PPos(Map.MapSize.Width - 2, Map.MapSize.Height - maxTerrainHeight - 2);
    Map.SetBounds(tl, br);
    Map.Title = MapGenerationArgs.Title;
    Map.Author = MapGenerationArgs.Author;
    Map.RequiresMod = ModData.Manifest.Id;
}
```

### `BakeMap`

`BakeMap` turns the mutable workspace into a serializable map. Player definitions are generated based on the count of `mpspawn` actors. Actor definitions are filtered by whether their projected footprint is inside the map, then serialized into a numbered list. The comment in the code is explicit: this can trigger initialization of map data structures, so it should be near the end of the pipeline.

```csharp
public void BakeMap()
{
    var playerCount = ActorsOfType("mpspawn").Count();
    Map.PlayerDefinitions = new MapPlayers(Map.Rules, playerCount).ToMiniYaml();

    bool HasProjectedFootprintInMap(ActorPlan plan)
    {
        return plan.Footprint()
            .SelectMany(f => Map.ProjectedCellsCovering(f.Key.ToMPos(Map)))
            .Any(Map.Contains);
    }

    Map.ActorDefinitions = ActorPlans
        .Where(HasProjectedFootprintInMap)
        .Select((plan, i) => new MiniYamlNode($"Actor{i}", plan.Reference.Save()))
        .ToImmutableArray();
}
```

### `ImproveSymmetry`

`ImproveSymmetry` is the central symmetry enforcement tool. It creates a new `CellLayer` by rotating and mirroring each cell's position to collect all symmetry-projected source cells, then aggregating them with a caller-supplied function. Outside the original layer, the source value is treated as `outsideValue`.

```csharp
public CellLayer<T> ImproveSymmetry<T>(
    CellLayer<T> layer,
    T outsideValue,
    Func<T, T, T> aggregator)
{
    var newLayer = new CellLayer<T>(layer.GridType, layer.Size);
    Symmetry.RotateAndMirrorOverCPos(
        layer,
        Rotations,
        WMirror,
        (sources, destination)
            => newLayer[destination] = sources
                .Select(source => layer.TryGetValue(source, out var value) ? value : outsideValue)
                .Aggregate(aggregator));
    return newLayer;
}
```

Common aggregation functions:

- Boolean "and": `(a, b) => a && b` — used to enforce a strict intersection of allowed cells across all symmetry copies.
- Boolean "or": `(a, b) => a || b` — used to enforce a strict union of required cells.
- Integer `int.Min` / `int.Max` — used to take the minimum or maximum of scored cells.
- For resource plans, `-int.MaxValue` with `int.Min` clamps the lowest (worst) score across all symmetry copies.

### `ActorsOfType`

A simple, frequently used query over `ActorPlans`:

```csharp
public IEnumerable<ActorPlan> ActorsOfType(string type)
{
    return ActorPlans.Where(a => a.Reference.Type == type);
}
```

It is used in `BakeMap` to count player spawns, and by generators to find specific actors (e.g., `mpspawn`, resources seeds, or scripted units) that have been placed earlier.

![Configuration (yaml) diagram](images/Part_07_Chapter_04_Terraformer-annotated-yaml-snippet-diagram-showing-the-key-fields-and-ho-6a1b98.svg)

## Configuration (YAML)


`Terraformer` itself is not YAML-bound; it is a runtime orchestrator. The values passed to its methods normally come from a YAML-driven map generator or from hard-coded generator logic. The table below maps the most common `Terraformer` arguments to typical YAML keys.

| Parameter | Typical YAML key | Description |
| :---- | :---- | :---- |
| `mirror` | `Mirror: None`, `LeftMatchesRight`, `TopMatchesBottom`, etc. | Mirror symmetry applied on top of rotations. |
| `rotations` | `Symmetry: N` | Number of rotational copies around the map center. |
| `noiseFeatureSize` | `TerrainFeatureSize`, `WaterFeatureSize`, `CliffFeatureSize`, etc. | Largest wavelength of the noise field, in 1024ths of a cell. |
| `fraction` | `Fraction` / `Threshold` / `ThresholdOutOf` | Fraction of true values desired in a boolean noise layer, expressed as `N / 1000` (`FractionMax`). |
| `clumpiness` | `Clumpiness`, `Amplitude` | Number of times to square-root the wavelength when computing octave amplitude; `0` is pink noise. |
| `smoothing` | `TerrainSmoothing`, `Smoothing` | Radius, in cells, for binomial blur of elevation noise. |
| `minimumContourSpacing` | `MinimumContourSpacing` | Minimum Chebyshev distance between successive elevation slices. |
| `centralReservationFraction` | `CentralReservation` | Fraction of map smallest dimension inside which spawns are biased away. |
| `minimumRadius`, `maximumRadius`, `zoneRadius` | spawn-zone settings | Chebyshev space required for and used by spawn placement. |
| `cutoutRadius` | `PassageCutoutRadius` | Half-thickness of passages planned by `PlanPassages`. |
| `maximumCutoutSpacing` | `MaximumPassageSpacing` | Maximum Chebyshev distance between passages; `0` disables extra passages. |
| `minimumSpacing` | `RoadMinimumSpacing` | Minimum distance between planned roads and the edges of available space. |
| `minimumLength` | `RoadMinimumLength` | Roads shorter than this are merged or pruned. |
| `MultiBrush` collection names | `TerrainType: Land`, `Water`, `Cliff`, `Road`, etc. | Named brush collections from the tileset YAML used by `PaintArea`, `PaintLoopsAndFill`, and `RepaintTiles`. |
| `ResourceType` | `ResourceType` | Default resource type for `PlanResources`. |
| `targetValue` | `ResourceTargetValue` | Total economic value the map should try to grow. |

Because `Terraformer` is method-driven, a YAML generator simply reads these values and forwards them. The `MersenneTwister` used by most `Terraformer` methods must be deterministically seeded from the map generation settings so all clients generate the same result.

## Interconnectivity

- **Depends on:**
  - `OpenRA.Mods.Common/MapGenerator/NoiseUtils.cs` — fractal noise synthesis ([Part 7.3 — Map Generation Algorithms](Part_07_Chapter_03_Algorithms.md)).
  - `OpenRA.Mods.Common/MapGenerator/MatrixUtils.cs` — boolean morphology, contour extraction, path extraction ([Part 7.3 — Map Generation Algorithms](Part_07_Chapter_03_Algorithms.md)).
  - `OpenRA.Mods.Common/MapGenerator/Symmetry.cs` — mirror and rotation primitives ([Part 7.3 — Map Generation Algorithms](Part_07_Chapter_03_Algorithms.md)).
  - `OpenRA.Mods.Common/MapGenerator/CellLayerUtils.cs` — layer conversions and helper shapes.
  - `OpenRA.Mods.Common/MapGenerator/MultiBrush.cs` — tile/actor brush placement ([Part 7.5 — MultiBrush and Tile Placement](Part_07_Chapter_05_MultiBrush.md)).
  - `OpenRA.Mods.Common/MapGenerator/TilingPath.cs` — path-aware tiling ([Part 7.6 — Mod-Specific Generators](Part_07_Chapter_06_Mod_Generators.md)).
  - `OpenRA.Mods.Common/MapGenerator/ActorPlan.cs` — actor placement plans ([Part 7.7 — Resource and Actor Placement](Part_07_Chapter_07_Resources_Actors.md)).
  - `OpenRA.Mods.Common/Terrain/DefaultTerrain.cs` — tileset rules.
  - `OpenRA.Mods.Common/Traits/World/ResourceLayer.cs` / `PlayerResourcesInfo.cs` — resource rules.
  - `OpenRA.Game/Map/Map.cs` — the map object itself.

- **Used by:**
  - Higher-level generator classes in `OpenRA.Mods.Common/Traits/World/` (e.g., `ClassicMapGenerator.cs`, `ClearMapGenerator.cs`) and any custom `IGenerator` implementations.
  - Map generator YAML-driven templates that wire the method calls together.

![Algorithms diagram](images/Part_07_Chapter_04_Terraformer-algorithm-diagram-or-pseudocode-flowchart-for-the-non-trivia-5983ed.svg)

## Algorithms


### 1. Noise generation

`Terraformer` exposes three noise methods, all of which respect the configured symmetry:

#### `BooleanNoise`

Generates a boolean fractal noise mask. It uses `NoiseUtils.SymmetricFractalNoiseIntoCellLayer` to fill a `CellLayer<int>` with symmetric fractal noise, then thresholds it so that approximately `fraction / FractionMax` of the cells are `true`.

```csharp
public CellLayer<bool> BooleanNoise(
    MersenneTwister random,
    int noiseFeatureSize,
    int fraction,
    int clumpiness = 0)
{
    var noise = new CellLayer<int>(Map);
    NoiseUtils.SymmetricFractalNoiseIntoCellLayer(
        random,
        noise,
        Rotations,
        WMirror,
        noiseFeatureSize,
        wavelength => NoiseUtils.ClumpinessAmplitude(wavelength, clumpiness));

    return CellLayerUtils.CalibratedBooleanThreshold(
        noise, fraction, FractionMax);
}
```

**Pseudocode:**
```
function BooleanNoise(random, featureSize, fraction, clumpiness):
    noise = new CellLayer<int>(Map)
    fill noise with symmetric fractal noise
        using amplitude = ClumpinessAmplitude(wavelength, clumpiness)
    threshold = CalibratedBooleanThreshold(noise, fraction, 1000)
    return threshold
```

#### `ElevationNoiseMatrix`

Generates a height field in a `Matrix<int>` sized to the map's cell bounds. The matrix is normalized to the range `[0, 1024]` and then optionally blurred with a binomial kernel.

```csharp
public Matrix<int> ElevationNoiseMatrix(
    MersenneTwister random,
    int noiseFeatureSize,
    int smoothing)
{
    var elevation = NoiseUtils.SymmetricFractalNoise(
        random,
        CellLayerUtils.CellBounds(Map).Size.ToInt2(),
        Rotations,
        WMirror.ForCPos(),
        noiseFeatureSize,
        NoiseUtils.PinkAmplitude);
    MatrixUtils.NormalizeRangeInPlace(elevation, 1024);

    if (smoothing > 0)
        elevation = MatrixUtils.BinomialBlur(elevation, smoothing);

    return elevation;
}
```

**Pseudocode:**
```
function ElevationNoiseMatrix(random, featureSize, smoothing):
    bounds = CellBounds(Map)
    elevation = SymmetricFractalNoise(
        random, bounds.Size, Rotations, WMirror.ForCPos(),
        featureSize, PinkAmplitude)
    NormalizeRangeInPlace(elevation, 1024)
    if smoothing > 0:
        elevation = BinomialBlur(elevation, smoothing)
    return elevation
```

#### `ResourceNoise`

Generates a non-negative, clumped resource placement pattern. The output is calibrated to the range `[uniformity, uniformity + 1024]`. Higher values indicate more desirable resource cells.

```csharp
public CellLayer<int> ResourceNoise(
    MersenneTwister random,
    int noiseFeatureSize,
    int clumpiness,
    int uniformity)
{
    var pattern = new CellLayer<int>(Map);
    NoiseUtils.SymmetricFractalNoiseIntoCellLayer(
        random,
        pattern,
        Rotations,
        WMirror,
        noiseFeatureSize,
        wavelength => NoiseUtils.ClumpinessAmplitude(wavelength, clumpiness));
    {
        CellLayerUtils.CalibrateQuantileInPlace(
            pattern,
            0,
            0, 1);
        var max = pattern.Max();
        foreach (var mpos in Map.AllCells.MapCoords)
            pattern[mpos] = uniformity + 1024 * pattern[mpos] / max;
    }

    return pattern;
}
```

### 2. Elevation slicing

#### `SliceElevation`

`SliceElevation` turns a continuous elevation matrix into a boolean mask. If no mask is provided, it thresholds the entire matrix. If a mask is provided, it only considers cells inside the mask, thresholds based on the masked area, and then enforces a minimum Chebyshev distance (`minimumContourSpacing`) between the new slice's contour and the previous mask's contour.

![`SliceElevation`](images/Part_07_Chapter_04_Terraformer-Slice_elevation_flowchart.svg)
**Pseudocode:**
```
function SliceElevation(elevation, mask, fraction, minimumContourSpacing):
    if mask is null:
        return CalibratedBooleanThreshold(elevation, fraction, 1000)

    filtered = clone(elevation)
    room = ChebyshevRoom(mask, true)
    available = count(mask)
    for each cell n:
        if not mask[n]:
            filtered[n] = -infinity

    slice = CalibratedBooleanThreshold(filtered, available * fraction / 1000, total)
    for each cell n:
        slice[n] &= room[n] >= minimumContourSpacing + 1
    return slice
```

This is the standard way to build layered terrain: a low-elevation slice becomes the base playable area, the next slice becomes water or cliffs, and so on.

### 3. Space and zoning analysis

#### `CheckSpace` / `GetZoneable`

`CheckSpace` returns a boolean layer of where the map currently meets the caller's constraints. It can filter by terrain type, tile type, absence of actors, absence of resources, bounds, and ramps. It has two overloads: one for allowed terrain byte indices, and one for an exact tile type.

`GetZoneable` is the higher-level variant used for object placement. It starts from `CheckSpace` with all the usual constraints (terrain, actors, resources, bounds, ramps), intersects with an optional mask, reserves the center of the map when symmetry is enabled, and finally runs `ImproveSymmetry` with a boolean `&&` aggregation.

```csharp
public CellLayer<bool> GetZoneable(
    IReadOnlySet<byte> zoneableTerrain,
    CellLayer<bool> mask = null)
{
    var zoneable = CheckSpace(zoneableTerrain, true, true, true, true);
    if (mask != null)
        zoneable = CellLayerUtils.Intersect([zoneable, mask]);

    if (Rotations > 1 || WMirror.HasMirror)
    {
        CellLayerUtils.OverCircle(
            cellLayer: zoneable,
            wCenter: CellLayerUtils.Center(Map),
            wRadius: new WDist(1024),
            outside: false,
            action: (mpos, _, _, _) => zoneable[mpos] = false);
    }

    zoneable = ImproveSymmetry(zoneable, false, (a, b) => a && b);
    return zoneable;
}
```

The center reservation is a subtle but important guard: if the map has any symmetry, the exact center cell cannot be mirrored cleanly (it maps to itself), so it is excluded from placement to avoid asymmetry artifacts.

#### `ErodeZones`

`ErodeZones` shrinks zoneable areas by a Chebyshev thickness. It is a convenience wrapper over `CellLayerUtils.ChebyshevRoom` and `CellLayerUtils.Map`.

```
function ErodeZones(zoneable, amount):
    room = ChebyshevRoom(zoneable, false)
    return Map(room, r => r > amount)
```

### 4. Spawn and actor placement

#### `ProjectionSpacing`

This method builds the cached layer that answers: "how far is this cell from the nearest copy of itself created by symmetry?" It is used in `ChooseSpawnInZoneable` and `ChooseInZoneable` to prevent an object from being placed so close to its own mirror image that the placements overlap.

```
function ProjectionSpacing():
    spacing = new CellLayer<int>(Map)
    for each cell and its symmetry projections:
        spacing[cell] = ProjectionProximity(projections) / 2
    return spacing
```

#### `ChooseSpawnInZoneable`

Spawns are placed differently from generic actors because they must be:

- far enough from the map center and symmetry axes (to avoid center conflicts and overlapping mirror copies),
- in a space with at least `minimumRadius` Chebyshev room,
- in a space where the projection spacing can accommodate `zoneRadius`.

The method builds a `spawnBias` layer (via `SpawnBias`) and combines it with `ChebyshevRoom` to score each cell. The best valid cell is chosen at random among ties.

**Pseudocode:**
```
function ChooseSpawnInZoneable(random, zoneable, centralFraction, minR, maxR, zoneR):
    projectionSpacing = lazyProjectionSpacing.Value
    spawnBias = SpawnBias(centralFraction)
    room = ChebyshevRoom(zoneable, false)

    for each cell:
        if room[cell] >= minR and projectionSpacing[cell] * 2 >= zoneR + minR:
            score[cell] = spawnBias[cell] * min(maxR, room[cell])
        else:
            score[cell] = 0

    return FindRandomBest(score, random)
```

#### `ChooseInZoneable`

A simpler variant that picks the cell with the most free space, capped by `maximumSpace` and by projection spacing.

```
function ChooseInZoneable(random, zoneable, maximumSpace):
    room = ChebyshevRoom(zoneable, false)
    for each cell:
        room[cell] = min(maximumSpace, room[cell], projectionSpacing[cell])
    return FindRandomBest(room, random)
```

#### `ProjectPlaceDezoneActor`

One of the most common compound operations: place an actor, add all its symmetry-projected copies to `ActorPlans`, and subtract their footprints from `zoneable`.

```csharp
public void ProjectPlaceDezoneActor(
    ActorPlan actorPlan,
    CellLayer<bool> zoneable = null,
    WDist? dezoneRadius = null)
{
    var projections = Symmetry.RotateAndMirrorActorPlan(
        actorPlan, Rotations, WMirror);
    ActorPlans.AddRange(projections);
    if (zoneable != null)
        foreach (var projection in projections)
            DezoneActor(projection, zoneable, dezoneRadius);
}
```

#### `AddActor`

A convenience wrapper for placing a single actor type. It computes a required space from the actor's `MaxSpan`, chooses a location, and projects, places, and dezones.

```
function AddActor(random, zoneable, actorType, dezoneRadius):
    plan = new ActorPlan(Map, actorType)
    requiredSpace = plan.MaxSpan() * 1024 / 1448 + 2
    (cpos, room) = ChooseInZoneable(random, zoneable, requiredSpace)
    if room < requiredSpace:
        return false
    plan.WPosCenterLocation = CPosToWPos(cpos, Map.Grid.Type)
    ProjectPlaceDezoneActor(plan, zoneable, dezoneRadius)
    return true
```

#### `AddDistributedActors`

Places a target number of actors from a weighted actor-type pool, using a caller-supplied distribution layer. Each placed actor subtracts a circle around itself from the distribution layer so subsequent actors are spread out.

#### `AddActorCluster`

Places a cluster of actors around a chosen center. It builds a circular distribution with an optional inner reservation (hole) and a radius limit, then delegates to `AddDistributedActors`.

#### `TargetWalkingDistance`

This is used to place objects near (or far from) walking routes. It computes the walking distance from a set of seed points through a `walkable` mask, then scores each cell by how close its walking distance is to a `targetRange`. Cells outside the mask or beyond `maximumRange` receive `-int.MaxValue`.

```
function TargetWalkingDistance(walkable, mask, seeds, targetRange, maxRange):
    distances = WalkingDistances(walkable, seeds, maxRange)
    for each cell:
        if not mask[cell]:
            score[cell] = -inf
        else if distance <= targetRange:
            score[cell] = distance / 1024
        else:
            score[cell] = (2 * targetRange - distance) / 1024
    return score
```

### 5. Terrain painting methods

`Terraformer` does not itself paint tiles; it delegates to `MultiBrush`. What it provides are the policy wrappers that decide which cells are allowed to be painted and which brush collections to use.

#### `PaintArea`

The most general painter. It takes a `CellLayer<MultiBrush.Replaceability>` indicating which cells may be overwritten and how, and a list of `MultiBrush` candidates. The `alwaysPreferLargerBrushes` flag biases brush selection toward larger brushes.

```csharp
public void PaintArea(
    MersenneTwister random,
    CellLayer<MultiBrush.Replaceability> replace,
    IReadOnlyList<MultiBrush> brushes,
    bool alwaysPreferLargerBrushes = false)
{
    MultiBrush.PaintArea(
        Map,
        ActorPlans,
        replace,
        brushes,
        random,
        alwaysPreferLargerBrushes);
}
```

#### `PaintActors`

A convenience wrapper that treats a boolean mask as "tiles stay, actors can be placed" (`Replaceability.Actor`).

```
function PaintActors(random, mask, brushes, alwaysPreferLargerBrushes):
    replace = Map(mask, b => b ? Actor : None)
    PaintArea(random, replace, brushes, alwaysPreferLargerBrushes)
```

#### `PaintTiling`

Paints a single already-tiled `MultiBrush` (typically the result of `TilingPath.Tile`).

#### `PaintLoopsAndFill`

This is the "loops and fill" method used for water bodies, cliffs, or any closed terrain feature. It:

1. Tiles each `TilingPath` into a `MultiBrush`.
2. Paints each brush onto the map.
3. Runs `InsideOutside` to determine which cells are inside the closed loops.
4. Paints the inside and outside regions with separate brush collections.

If any tiling fails, the method returns `null` without modifying the map.

```
function PaintLoopsAndFill(random, tilingPaths, fallback, outside, inside, replaceMask, heightOffset):
    tilings = empty list
    for path in tilingPaths:
        tiling = path.Tile(random)
        if tiling is null:
            return null
        tilings.add(tiling)

    for tiling in tilings:
        tiling.Paint(Map, ActorPlans, origin, heightOffset, Any, random)

    if inside is null and outside is null:
        return null

    sides = InsideOutside(tilings, fallback)

    for (brushes, side) in [(inside, In), (outside, Out)]:
        if brushes is null:
            continue
        replace = Map(sides, s => s == side ? replaceMask or Any : None)
        PaintArea(random, replace, brushes)

    return sides
```

#### `InsideOutside`

Determines which cells are inside or outside a set of closed, tiled loops. It uses `MatrixUtils.PointsChirality` to compute a winding-number-like field. Tiled cells are `Side.None`. Cells with positive chirality are `Side.In`; negative chirality is `Side.Out`. If no valid chirality matrix exists (e.g., no paths contained in the map), it falls back to the caller's default side.

#### `FillUnmaskedSideAndBorder`

Used to "undo" or extend a side assignment. For example, after painting a water body, you may want to flood-fill a connected unmasked region (and a one-cell border) so it can be replaced with deep water. The method flood-fills from cells matching `fillSide` that are not in the mask, only moving into cells that are not the opposite side.

```
function FillUnmaskedSideAndBorder(mask, sides, fillSide, fillAction):
    if fillSide == None:
        error
    notFillSide = opposite(fillSide)
    seeds = cells where sides == fillSide and not mask[cell] and in bounds
    seeds = ImproveSymmetry(seeds, false, ||)
    fillable = Map(sides, s => s != notFillSide)
    SimpleFloodFill(fillable, seeds, fillAction, cardinal spread)
```

#### `RepaintTiles`

Repaints all cells whose tile type matches one of the keys in a `tile -> MultiBrush collection` dictionary. Useful for post-processing: for example, replacing a generic water tile with varied shore details.

```
function RepaintTiles(random, rules):
    for (tile, brushes) in rules sorted by tile:
        replace = Map(all cells, c => Map.Tiles[c].Type == tile ? Any : None)
        MultiBrush.PaintArea(Map, ActorPlans, replace, brushes, random)
```

### 6. Path and contour operations

#### `PartitionPath`

This is the most complex algorithm in `Terraformer`. It takes a single matrix path (open or closed loop) and a `zoneMask` that assigns each path point a preferred zone, and divides the path into `TilingPath` segments whose segment types match the zones as closely as possible.

The algorithm:

1. Detects whether the path is a loop (`path[0] == path[^1]`). If so, it normalizes the loop start with `NormalizeLoopStart` to a point near the map center.
2. Samples `zoneMask` at each path point to build a `zones` array.
3. Precomputes prefix sums (`partitionAcc`) for each zone so it can count how many points of a given zone appear in any sub-path in O(1).
4. Defines a `Vote(from, length, checkMinLength)` function that returns the number of mismatched points if the best zone is chosen for that sub-path.
5. Identifies "straight" points and "valid terminal" points where a segment boundary is allowed (subject to `minimumStraight`).
6. Runs a Dijkstra / best-first search over sub-path lengths to minimize the total number of mismatched points while satisfying each zone's `MinimumLength`.
7. Backtracks to find the optimal boundaries, then builds one `TilingPath` per segment with appropriate start/end/inner segment types.

**Pseudocode for the core optimization:**
```
function PartitionPath(path, allZones, zoneMask, brushes, minimumStraight):
    isLoop = path[0] == path[end]
    if isLoop:
        path = NormalizeLoopStart(path)

    zones = [zoneMask[path[i]] for each point i]
    precompute prefix sums for each zone

    function Vote(from, length, checkMinLength):
        if checkMinLength and length < min(allZones.MinimumLength):
            return infinity
        best = -1
        for each zone i:
            count = points of zone i in range [from, from+length)
            if checkMinLength and length < zone[i].MinimumLength:
                skip
            best = max(best, count)
        return totalNonWildcards - best

    validTerminal = points where both forward and backward straight runs
                    are at least minimumStraight deep

    solutions = []
    for each valid start offset in the loop:
        costs = array filled with infinity
        costs[0] = 0
        priority queue from 0
        while queue not empty:
            from = popMin()
            if from == end:
                break
            for length from minLength to end - from:
                to = from + length
                if not validTerminal[Idx(offset + to)]:
                    continue
                mismatch = Vote(offset + from, length, true)
                if mismatch is infinity:
                    continue
                if costs[from] + mismatch < costs[to]:
                    costs[to] = costs[from] + mismatch
                    push(to)

        if costs[end] is infinity:
            continue
        backtrack to recover boundaries
        solutions.add((costs[end], boundaries))

    if no solutions:
        return SinglePath(fallbackZone)

    best = solutions with minimum cost
    choose the one with the most boundaries among ties
    build TilingPath for each segment
    return segments
```

#### `PartitionPaths`

A simple wrapper that applies `PartitionPath` to each path in an enumerable.

```
function PartitionPaths(paths, zones, partitionMask, brushes, minStraight):
    return paths.flatMap(p => PartitionPath(p, zones, partitionMask, brushes, minStraight))
```

#### `NormalizeLoopStart`

For a closed loop, the start point affects whether the loop and its symmetry projections align. This method chooses the point closest to the map center as the start, with tie-breaking based on the furthest point, so that different symmetry copies of the same loop start at corresponding points.

#### `BordersToPoints` (not in `Terraformer.cs`)

`Terraformer` does not contain a `BordersToPoints` method. The functionality is provided by `MatrixUtils.BordersToPoints` in `MatrixUtils.cs` and the `CellLayerUtils.BordersToPoints` wrapper in `CellLayerUtils.cs`. The generator uses these helpers to extract contour paths from boolean masks. For example, an elevation slice or a water mask is converted into a set of closed loops, which are then passed to `PartitionPath` and `PaintLoopsAndFill`.

**Pseudocode:**
```
function BordersToPoints(matrix, mask):
    trace the boundary between true and false cells
    return array of closed/open point loops
```

#### `PlanPassages`

`PlanPassages` ensures that a given `space` remains connected even after obstructions are carved into it. It produces a boolean layer of passages that should be kept open.

The algorithm:

1. If `maximumCutoutSpacing > 0`, repeatedly carve holes in a cloned `space` at the points with the largest Chebyshev room until no room is larger than the maximum spacing. This guarantees that any two points in the space are within the required distance of a passage.
2. Convert the (possibly modified) `space` to a matrix.
3. Deflate the space (convert cell squares to grid points) using `MatrixUtils.DeflateSpace`.
4. Dilate the deflated grid with a circular kernel of radius `cutoutRadius` using `MatrixUtils.KernelDilateOrErode`.
5. Return the result as a `CellLayer<bool>`.

**Pseudocode:**
```
function PlanPassages(random, space, cutoutRadius, maximumCutoutSpacing):
    if cutoutRadius <= 0:
        return empty passages

    if maximumCutoutSpacing > 0:
        space = clone(space)
        room = ChebyshevRoom(space, false)
        cap room at maximumCutoutSpacing
        loop:
            (chosen, room) = FindRandomBest(room, random)
            if room < maximumCutoutSpacing:
                break
            for each symmetry projection of chosen:
                mark space[projection] = false
                clear room in a (4*spacing - 3) square around projection

    matrixSpace = ToMatrix(space, false)
    deflated = DeflateSpace(matrixSpace, false)
    kernel = filled bool matrix of size (2*cutoutRadius, 2*cutoutRadius)
    inflated = KernelDilateOrErode(
        deflated.Map(v => v != 0),
        kernel,
        (cutoutRadius - 1, cutoutRadius - 1),
        true)

    passages = FromMatrix(inflated, true)
    return passages
```

The result is meant to be subtracted from obstacle layers: any cell marked `true` in the returned layer must remain walkable.

#### `PlanRoads`

`PlanRoads` finds the skeleton of the open space where roads can run. It uses the medial-axis-like path extracted from the eroded space.

The algorithm:

1. Creates an enlarged, symmetric copy of the available space.
2. Dilates the space inward by `minimumSpacing` using a circular kernel.
3. Deflates the result back to grid points.
4. If the symmetry is imperfect (mirrors, 3-fold, or 5+ rotations), iteratively removes short stubs and prunes paths that are not consistent across all symmetry projections.
5. Converts the remaining direction map to paths, keeps disjoint paths only, and normalizes their chirality.

### 7. Region analysis and playable-area selection

#### `FindRegions`

Flood-fill connected components in a boolean space. Returns an array of `Region` metadata and a `RegionMap` layer assigning each cell its region ID (`-1` for background).

#### `ChoosePlayableRegion`

Selects the largest connected region that is both unpoisoned and sufficiently symmetric. A region is disqualified if fewer than half of its cells have matching region IDs across all their symmetry projections.

```
function ChoosePlayableRegion(playable, poison):
    (regions, regionMask) = FindRegions(playable, Spread8)
    disqualify regions containing poison cells

    symmetryScore = count of cells whose projections all share the same region id
    if symmetryScore[id] < area[id] / 2:
        disqualify region[id]

    return largest remaining region
```

#### `FindAsymmetries`

Compares the current map against its symmetry projections. Cells that are "dominant" (matching terrain, or covered by actors if `dominantActors` is true) and whose projections are not dominant, or cells with terrain-type mismatches, are marked as asymmetries. This is useful for debugging or for post-generation correction passes.

### 8. Resource planning and growth

#### `PlanResources`

Builds a placement-score layer and a per-cell resource-type layer from a noise pattern, a mask, and a list of `ResourceBias` objects.

The algorithm:

1. Reads all resource types from the world's `ResourceLayerInfo`.
2. Builds a `strength` layer per resource type, initialized to `1`.
3. Applies each `ResourceBias` by calling its `Bias` function over a circle around its `WPos`.
4. For each cell, picks the resource type with the highest strength.
5. Multiplies the input pattern by the maximum strength to get the final score.
6. Invalidates cells outside the mask, on incompatible terrain, or inside an exclusion radius.
7. Runs `ImproveSymmetry` on the score.

#### `GrowResources`

Grows resources onto the map greedily by picking the highest-scoring cell, placing its symmetry-projected copies, and subtracting their economic value from the target until the target is reached or no valid cells remain.

The method uses a `PriorityArray<int>` keyed by `MPos` to repeatedly find the minimum `-score` (i.e., the maximum score). It also supports `BakedAdjacency` mode, where the density saved in the map is computed from the number of adjacent matching resources.

### 9. Spawn reordering

#### `ReorderPlayerSpawns`

After spawns are placed, the `mpspawn` actors in `ActorPlans` are in an arbitrary order. `ReorderPlayerSpawns` sorts them clockwise around the map center, then rotates the list so that the first spawn is the one after the largest angular gap. This makes the lobby spawn order more intuitive and naturally suggests team groupings.

```
function ReorderPlayerSpawns():
    mpspawns = ActorPlans.Where(type == "mpspawn").ToList()
    if count <= 1: return

    ActorPlans.RemoveAll(type == "mpspawn")
    mpspawns = sort by polar angle around center

    for each spawn i in order:
        gap = angle from previous spawn to this spawn
        choices.add((gap, x, y, i))

    best = max gap
    candidates = choices where gap >= best - 2
    bestIndex = candidate with min (x, y, index)

    mpspawns = rotate so bestIndex is first
    ActorPlans.AddRange(mpspawns)
```

![Extension points diagram](images/Part_07_Chapter_04_Terraformer-extension-hook-diagram-showing-the-interface-s-to-implement-b4a27b.svg)

## Extension Points


`Terraformer` is not an interface; it is a concrete class that a generator instantiates. Extensions therefore happen in one of two ways:

1. **Write a new generator that uses `Terraformer` differently.** Any class that has access to `Map`, `ModData`, and `MapGenerationArgs` can create a `Terraformer` and call its methods in a new order. This is the intended path for custom map generators.

2. **Add new helper methods to `Terraformer`.** The class is a natural home for cross-cutting map generation utilities. New methods can follow the existing patterns: validate input shape with `CheckHasMapShape`, use `ImproveSymmetry` when symmetry must be enforced, and delegate actual tile placement to `MultiBrush`.

3. **Provide new brush collections in the tileset YAML.** Because all terrain painting flows through `MultiBrush`, adding new brush collections to `DefaultTerrainInfo.MultiBrushCollections` lets generators use them without changing `Terraformer`.

4. **Subclass `ResourceBias` or create custom bias functions.** The `Bias` delegate in `ResourceBias` is a clean hook for custom resource distribution logic (e.g., falloff curves, cluster-based biasing, or avoiding specific actor types).

5. **Add new `PathPartitionZone` types.** The zone system in `PartitionPath` is data-driven; new zones can be defined and used by the same partitioning algorithm.

![Common pitfalls  guardrails diagram](images/Part_07_Chapter_04_Terraformer-checklist-infographic-style-diagram-summarizing-the-top-pitf-fb069e.svg)

## Common Pitfalls / Guardrails


- **Determinism.** `Terraformer` relies on a caller-supplied `MersenneTwister`. Every method that uses `random` must receive the same seeded instance on every client, or the generated map will desync. Do not use `System.Random` or `DateTime.Now` inside generator code.

- **Shape checking.** Most methods call `CheckHasMapShape` or `CheckHasMapShapeOrNull`. A `CellLayer` or `Matrix` that is not the same size as the map will throw `ArgumentException`. Always derive layers from the map or from `Terraformer` helpers rather than constructing them by hand.

- **Symmetry after the fact.** `ImproveSymmetry` returns a new layer; it does not modify the map directly. If you want the map to be symmetric, you must apply the result back to the map (e.g., by painting through `PaintArea` or by modifying `ActorPlans` via `Symmetry.RotateAndMirrorActorPlan`).

- **Center cell reservation.** `GetZoneable` reserves the center cell when symmetry is active. If a generator bypasses `GetZoneable` and manually picks symmetric cells, it must handle the center cell itself to avoid collisions.

- **Projection spacing.** Placing objects near the center or near symmetry axes can cause overlapping projections. Always check `ProjectionSpacing` or use `ChooseSpawnInZoneable` / `ChooseInZoneable` when placing anything that must have a clear footprint.

- **Baking order.** `BakeMap` should be one of the last calls. It initializes map cell projections and may invalidate assumptions that earlier helper methods hold.

- **Tileset assumptions.** Some methods assume `templatedTerrainInfo` is non-null (e.g., `PickTile`). On a non-templated terrain (very rare), these will fail at runtime. Check the tileset type before calling template-dependent methods.

- **Resource density.** `GrowResources` uses a greedy priority queue. The economic target may not be reached exactly if the mask is too small or the value per cell is high. Always check the remaining value after generation if exact resource budgets matter.

- **Path partitioning complexity.** `PartitionPath` uses a dynamic-programming/Dijkstra search over the entire path. Very long paths with many zones can be expensive. Keep the number of zones and the path length reasonable for the target map size.

- **Loop normalization.** `NormalizeLoopStart` only makes sense for loops that do not overlap their own symmetry projections. If a loop overlaps itself, the normalized start point may not correspond correctly across symmetries.

- **Inside/outside chirality.** `InsideOutside` assumes that clockwise loops enclose the inside. If a path is self-intersecting or degenerate, the chirality field may be ambiguous and the fallback side will be used.

## What to read next

- [Part 7.5 — MultiBrush and Tile Placement](Part_07_Chapter_05_MultiBrush.md) for the brush engine that `Terraformer` calls to paint terrain.
- [Part 7.7 — Resource and Actor Placement](Part_07_Chapter_07_Resources_Actors.md) for how `ActorPlan`s are placed and baked into the final map.
- [Part 7.8 — Random Map Generator Extension Points](Part_07_Chapter_08_Extension_Points.md) if you want to implement a custom generator phase using the `Terraformer` toolbox.

## Summary

This chapter explains how `[Terraformer](../appendices/Appendix_A_Glossary.md)` orchestrates the high-level procedural map generation pipeline.

After reading this chapter, you should be able to:

- **Create the workspace.**

If any of the concepts above feel unclear, review the relevant section before continuing. For source files and further reading, see the References section.


## References

- Source file: `OpenRA.Mods.Common/MapGenerator/Terraformer.cs`.
- [Part 7.3 — Map Generation Algorithms](Part_07_Chapter_03_Algorithms.md) (`NoiseUtils`, `MatrixUtils`, `Symmetry`).
- [Part 7.5 — MultiBrush and Tile Placement](Part_07_Chapter_05_MultiBrush.md).
- [Part 7.6 — Mod-Specific Generators](Part_07_Chapter_06_Mod_Generators.md).
- [Part 7.7 — Resource and Actor Placement](Part_07_Chapter_07_Resources_Actors.md).
- OpenRA source: `OpenRA.Mods.Common/MapGenerator/CellLayerUtils.cs` (for `BordersToPoints` wrapper).
- OpenRA source: `OpenRA.Mods.Common/MapGenerator/MatrixUtils.cs` (for `BordersToPoints` implementation and `DirectionMapToPathsWithPruning`).
- OpenRA source: `OpenRA.Mods.Common/MapGenerator/ActorPlan.cs`.
- OpenRA source: `OpenRA.Mods.Common/Traits/World/ResourceLayer.cs`.
- OpenRA source: `OpenRA.Mods.Common/Terrain/DefaultTerrain.cs`.