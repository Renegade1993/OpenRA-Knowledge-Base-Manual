# Chapter 7.6 — Mod-Specific Generators

## Purpose

The OpenRA map generator is not a single monolithic program. It is a small ecosystem of **[Mod](../appendices/Appendix_A_Glossary.md)-specific generators** that each decide *what* a procedurally generated map should look like for a particular game, while a shared layer of `OpenRA.Mods.Common` code decides *how* to sculpt terrain, tile paths, grow resources, and place actors. This chapter studies the three current mod-specific generators:

- `D2kMapGenerator` — generates Arrakis-style Dune 2000 maps.
- `TSMapGenerator` — generates Tiberian Sun-style maps with full-height cliffs and ramps.
- `ClassicMapGenerator` — generates Red Alert and Tiberian Dawn style maps.

By reading these three generators side-by-side, you can see how the same shared `[Terraformer](../appendices/Appendix_A_Glossary.md)` toolbox is used for different design goals, how each mod exposes its own YAML settings, and where to add new mod-specific generators of your own.

## Learning Objectives


After studying this chapter, you should be able to:

- Explain the two-level architecture of mod-specific map generators (Info class + tool class).
- Compare the D2k, TS, and Classic generators and their shared algorithmic toolbox.
- Describe how Parameters classes bridge YAML settings to typed generator fields.
- Use deterministic MersenneTwister seeding to keep generators reproducible.
- Trace the common generator phases from base terrain to BakeMap.
- Add a new mod-specific generator by implementing IEditorMapGeneratorInfo.

## Files

- `OpenRA.Mods.D2k/Traits/World/D2kMapGenerator.cs`
- `OpenRA.Mods.Cnc/Traits/World/TSMapGenerator.cs`
- `OpenRA.Mods.Common/Traits/World/ClassicMapGenerator.cs`

Supporting shared infrastructure documented in related chapters ([Part 7.3 — Map Generation Algorithms](Part_07_Chapter_03_Algorithms.md), [Part 7.4 — Terraformer](Part_07_Chapter_04_Terraformer.md), [Part 7.5 — MultiBrush and Tile Placement](Part_07_Chapter_05_MultiBrush.md), and [Part 7.7 — Resource and Actor Placement](Part_07_Chapter_07_Resources_Actors.md)) includes:

- `OpenRA.Mods.Common/MapGenerator/Terraformer.cs`
- `OpenRA.Mods.Common/MapGenerator/TilingPath.cs`
- `OpenRA.Mods.Common/MapGenerator/MultiBrush.cs`
- `OpenRA.Mods.Common/MapGenerator/RampTiler.cs`
- `OpenRA.Mods.Common/MapGenerator/LatTiler.cs`
- `OpenRA.Mods.Common/MapGenerator/MatrixUtils.cs`
- `OpenRA.Mods.Common/MapGenerator/CellLayerUtils.cs`
- `OpenRA.Mods.Common/MapGenerator/NoiseUtils.cs`

YAML configuration:

- `mods/d2k/rules/map-generators.yaml`
- `mods/ts/rules/map-generators.yaml`
- `mods/ra/rules/map-generators.yaml`
- `mods/cnc/rules/map-generators.yaml`

Tileset brush libraries ([MultiBrush](../appendices/Appendix_A_Glossary.md) collections):

- `mods/d2k/tilesets/arrakis.yaml` (`MultiBrushCollections/Segmented`)
- `mods/ra/tilesets/*.yaml` (`MultiBrushCollections/Segmented`)
- `mods/cnc/tilesets/*.yaml` (`MultiBrushCollections/Segmented`)
- `mods/ts/tilesets/*.yaml` (`MultiBrushCollections/Segmented`)

![Architecture diagram](images/Part_07_Chapter_06_Mod_Generators-architecture-diagram-showing-the-main-classes-interfaces-and-9161e6.svg)

## Architecture


### Two-level architecture

Each generator is a `[TraitInfo](../appendices/Appendix_A_Glossary.md)` located on `SystemActors.EditorWorld`. The actual class is split into two parts:

1. **The `Info` class** (`D2kMapGeneratorInfo`, `TSMapGeneratorInfo`, `ClassicMapGeneratorInfo`) — implements `IEditorMapGeneratorInfo` and owns:
   - `Type`, `Name`, `Tilesets`, `MapTitle`, `PanelWidget` metadata.
   - A `Settings` MiniYaml subtree that describes the editor UI options.
   - A `Generate` method that is the real map generation routine.
   - `TryGenerateMetadata` for player count and rule definitions.

2. **The generator tool class** (`D2kMapGenerator`, `TSMapGenerator`, `ClassicMapGenerator`) — implements `IEditorTool` and is what the editor UI instantiates when the tool is selected. It only carries the label and panel name.

This split is consistent with how OpenRA separates trait metadata from runtime trait instances.

### Common interface

All three implement `IMapGeneratorInfo` (from `OpenRA.Game/Traits/TraitsInterfaces.cs`):

```csharp
public interface IMapGeneratorInfo : ITraitInfoInterface
{
    string Type { get; }
    string Name { get; }
    string MapTitle { get; }
    Map Generate(ModData modData, MapGenerationArgs args);
    bool TryGenerateMetadata(...);
}
```

They also implement `IEditorMapGeneratorInfo` (from `OpenRA.Mods.Common/TraitsInterfaces.cs`):

```csharp
public interface IEditorMapGeneratorInfo : IMapGeneratorInfo
{
    ImmutableArray<string> Tilesets { get; }
    IMapGeneratorSettings GetSettings();
}
```

`GetSettings` returns a `MapGeneratorSettings` object that parses the `Settings` MiniYaml and exposes the options the editor UI renders.

### Shared algorithm layer

Every generator follows the same broad pattern:

1. Create a new `Map` from `modData.DefaultTerrainInfo[args.Tileset]` and the requested size.
2. Create an `[ActorPlan](../appendices/Appendix_A_Glossary.md)` list to hold mpspawns, resource spawns, neutral buildings, etc.
3. Build a `Parameters` object by loading the generator-specific YAML settings via `FieldLoader.Load`.
4. Instantiate `Terraformer` with the chosen symmetry (mirror + rotations).
5. Seed a master `MersenneTwister` from `param.Seed`, then derive independent sub-generators for each phase.
6. Initialize the map to a default tile (sand, land, etc.).
7. Run a sequence of terrain phases (water, rock, cliffs, forests, dunes, ramps, etc.), each using `Terraformer` and `MatrixUtils` helpers.
8. Place actors, resources, and decorations.
9. Call `terraformer.ReorderPlayerSpawns()` and `terraformer.BakeMap()` to finalize the map.

The generators differ mostly in the **order** and **parameters** of these phases, not in the underlying tools.

![Data flow  code path diagram](images/Part_07_Chapter_06_Mod_Generators-sequence-flow-diagram-tracing-the-execution-path-from-trigge-035864.svg)

## Data Flow / Code Path


### Entry point

When a user clicks the random-map button in the editor, the engine:

1. Looks up the generator by `Type` under `^MapGenerators:`.
2. Calls `IEditorMapGeneratorInfo.GetSettings()` to build the option panel.
3. Collects the user choices into a `MapGenerationArgs`.
4. Calls `IMapGeneratorInfo.Generate(modData, args)`.
5. Calls `TryGenerateMetadata` to produce player definitions.

Inside `Generate`, the first thing each generator does is:

```csharp
var terrainInfo = modData.DefaultTerrainInfo[args.Tileset];
var size = args.Size;
var map = new Map(modData, terrainInfo, size);
var actorPlans = new List<ActorPlan>();
var param = new Parameters(map, args.Settings);
var terraformer = new Terraformer(args, map, modData, actorPlans, param.Mirror, param.Rotations);
```

The `Parameters` inner class is critical: it is the bridge between the raw YAML settings and the typed data the generator uses. Each `Parameters` constructor:

- Uses `FieldLoader.Load(this, my)` for scalar/boolean values.
- Uses custom `LoadUsing` methods for dictionaries (`BuildingWeightsLoader`, `ResourceSpawnWeightsLoader`), the `Mirror` enum (`MirrorLoader`), and terrain index sets (`ParseTerrainIndexes`).
- Resolves resource types against the `ResourceLayerInfo.ResourceTypes` dictionary.
- Loads `MultiBrush` collections from the tileset via `MultiBrush.LoadCollection(map, ...)`.

### Per-phase random generators

Every generator derives many independent `MersenneTwister` instances from a single seed. For example, in `ClassicMapGenerator`:

```csharp
var random = new MersenneTwister(param.Seed);
var elevationRandom = new MersenneTwister(random.Next());
var coastTilingRandom = new MersenneTwister(random.Next());
var cliffTilingRandom = new MersenneTwister(random.Next());
...
```

This is important for **reproducibility**: changing the forest algorithm should not change the coastline. The source comments explicitly warn that new generators should be appended only, and disused ones replaced with a `random.Next()` call, to keep seeds stable.

### Finalization

At the end of every generator:

```csharp
terraformer.ReorderPlayerSpawns();
terraformer.BakeMap();
return map;
```

`ReorderPlayerSpawns` sorts `mpspawn` actors clockwise around the map center and rotates the sequence so the first spawn is the one with the largest angular gap before it. This makes spawn numbering feel natural in a lobby. `BakeMap` commits the `ActorPlans` list into the map's `ActorDefinitions` and creates a `MapPlayers` block from the actual `mpspawn` count.

## D2kMapGenerator Phases

The Dune 2000 generator (`D2kMapGenerator.cs`) builds an Arrakis map in roughly this order.

### 1. Sand base

```csharp
foreach (var mpos in map.AllCells.MapCoords)
    map.Tiles[mpos] = terraformer.PickTile(pickAnyRandom, param.SandTile);
```

The entire map is seeded with the default sand tile (tile 0). This is the canvas on which everything else is painted.

### 2. Elevation and roughness

```csharp
var elevation = terraformer.ElevationNoiseMatrix(elevationRandom, param.TerrainFeatureSize, param.TerrainSmoothing);
var roughnessMatrix = MatrixUtils.GridVariance(elevation, param.RoughnessRadius);
```

A symmetric fractal elevation map is created, then a local variance (roughness) matrix is computed over a small radius. The roughness matrix drives where cliff transitions occur.

### 3. Rock platforms

```csharp
var cliffMask = MatrixUtils.CalibratedBooleanThreshold(roughnessMatrix, param.RockRoughness, FractionMax);
var plan = terraformer.SliceElevation(elevation, null, param.Rock);
plan = MatrixUtils.BooleanBlotch(plan, param.TerrainSmoothing, param.SmoothingThreshold, FractionMax,
    param.MinimumRockSandThickness, true);
var contours = MatrixUtils.BordersToPoints(plan);
var partitionMask = cliffMask.Map(masked => masked ? sandRockCliffZone : rockSmoothZone);
var tilingPaths = terraformer.PartitionPaths(contours, [rockSmoothZone, sandRockCliffZone],
    partitionMask, param.SegmentedBrushes, param.MinimumRockStraight);
```

The generator slices the elevation map to pick the highest `Rock` fraction of cells. `BooleanBlotch` enforces a minimum thickness, smooths the shape, and removes isolated specks. `BordersToPoints` extracts the contour, and `PartitionPaths` assigns each contour segment either a smooth rock-to-sand transition or a jagged cliff segment based on the roughness mask. The loop is tiled and the interior is filled with the rock tile.

### 4. Sand-sand cliffs

```csharp
if (param.SandCliffs > 0)
{
    var sandMask = CellLayerUtils.Map(rockSmoothSand, s => s == Terraformer.Side.Out);
    var inverseElevation = elevation.Map(v => -v);
    var cliffMask = MatrixUtils.CalibratedBooleanThreshold(roughnessMatrix, param.SandRoughness, FractionMax);
    var plan = terraformer.SliceElevation(inverseElevation, CellLayerUtils.ToMatrix(sandMask, true),
        param.SandCliffs, param.SandContourSpacing);
    plan = MatrixUtils.BooleanBlotch(plan, param.TerrainSmoothing, param.SmoothingThreshold, FractionMax,
        param.MinimumSandCliffThickness, false);
    var contours = MatrixUtils.BordersToPoints(plan);
    var partitionMask = cliffMask.Map(masked => masked ? sandSandCliffZone : sandZone);
    var tilingPaths = terraformer.PartitionPaths(contours, [sandSandCliffZone, sandZone],
        partitionMask, param.SegmentedBrushes, param.MinimumSandCliffStraight);
    foreach (var tilingPath in tilingPaths)
    {
        var brush = tilingPath.OptimizeLoop().ExtendEdge(4).SetAutoEndDeviation().Tile(sandSandCliffTilingRandom)
            ?? throw new MapGenerationException("Could not fit tiles for sand-sand cliffs");
        terraformer.PaintTiling(pickAnyRandom, brush);
    }
}
```

Sand cliffs are carved *inside* the remaining sand areas by inverting the elevation and slicing again. The resulting low-elevation pockets are turned into sand-sand cliffs, giving the map vertical relief without converting the sand into rock.

### 5. Sand detail

```csharp
if (param.SandDetail > 0)
{
    var space = terraformer.CheckSpace(param.PlayableTerrain);
    var passages = terraformer.PlanPassages(topologyRandom, ...);
    var plan = terraformer.BooleanNoise(sandDetailRandom, param.SandDetailFeatureSize,
        param.SandDetail, param.SandDetailClumpiness);
    plan = CellLayerUtils.Subtract([CellLayerUtils.Intersect([plan, terraformer.CheckSpace(param.SandTile, true)]), passages]);
    terraformer.PaintArea(sandDetailTilingRandom, CellLayerUtils.Map(plan, ...), param.SandDetailBrushes, true);
}
```

Small rough patches (`Rough-Sand-Detail` brushes) are scattered over the sand using fractal noise. `PlanPassages` is used to carve corridors through the detail so the map does not become choked.

### 6. Dunes

```csharp
if (param.Dunes > 0)
{
    var duneNoise = terraformer.ElevationNoiseMatrix(duneRandom, param.DuneFeatureSize, param.DuneSmoothing);
    var duneable = terraformer.CheckSpace(param.SandTile, true);
    var plan = terraformer.SliceElevation(duneNoise, CellLayerUtils.ToMatrix(duneable, true),
        param.Dunes, param.DuneContourSpacing);
    plan = MatrixUtils.BooleanBlotch(plan, param.DuneSmoothing, param.SmoothingThreshold, FractionMax,
        param.MinimumDuneThickness, false);
    var contours = CellLayerUtils.FromMatrixPoints(MatrixUtils.BordersToPoints(plan), map.Tiles);
    var tilingPaths = contours.Select(contour => TilingPath.QuickCreate(...)).ToArray();
    _ = terraformer.PaintLoopsAndFill(duneTilingRandom, tilingPaths, plan[0] ? Side.In : Side.Out,
        null, param.DuneBrushes, null, 0);
}
```

Dunes are raised sand areas painted with dedicated `Dune` brushes. They are constrained to existing sand cells and their interiors are left as sand (only the borders are tiled with dune transition graphics), because the dune is a terrain variation, not a different ground type.

### 7. Entity placement (if `CreateEntities`)

The D2k generator is unusual because spawns must be placed on **rock**, not sand:

```csharp
var playable = terraformer.ChoosePlayableRegion(terraformer.CheckSpace(param.PlayableTerrain, true, false, true), null);
var rockZoneable = terraformer.GetZoneable(param.RockZoneableTerrain, playable);
var (regions, regionMask) = terraformer.FindRegions(rockZoneable, DirectionExts.Spread8CVec);
var acceptableRegions = regions.Where(r => r.Area >= param.MinimumSpawnRockArea).Select(r => r.Id).ToHashSet();
```

Only rock regions large enough to hold a base are acceptable. Then spawns are chosen with `ChooseSpawnInZoneable`, and each spawn is projected to all symmetry positions with `ProjectPlaceDezoneActor`.

### 8. Spice blooms

D2k places two kinds of spice blooms:

- **Biased blooms** near player spawns using `TargetWalkingDistance`.
- **Unbiased blooms** scattered randomly across the sand zone.

```csharp
var walkingDistances = terraformer.TargetWalkingDistance(playable, ...);
for (var i = 0; i < param.BiasedResourceSpawns; i++)
    ... ProjectPlaceDezoneActor(new ActorPlan(map, param.ResourceSpawn) { ... }, sandZoneable, ...);
```

### 9. Worms

```csharp
var targetWormSpawnCount = (int)(param.WormSpawns * perSymmetryEntityMultiplier / EntityBonusMax);
for (var i = 0; i < targetWormSpawnCount; i++)
    terraformer.AddActor(expansionRandom, sandZoneable, param.WormSpawn, ...);
```

Worm spawners are placed on sand using the standard `AddActor` helper.

### 10. Growing spice

```csharp
var resourcePattern = terraformer.ResourceNoise(resourceRandom, param.ResourceFeatureSize,
    param.ResourceClumpiness, param.ResourceUniformity * 1024 / FractionMax);
var resourceBiases = ...;
var (plan, typePlan) = terraformer.PlanResources(resourcePattern, spiceZoneable, param.Resource, resourceBiases);
terraformer.GrowResources(plan, typePlan, targetResourceValue);
terraformer.ZoneFromResources(sandZoneable, false);
```

Spice is grown from the resource pattern, biased toward the spice blooms, and its total value is scaled by map area and player count.

## TSMapGenerator Phases

The Tiberian Sun generator (`TSMapGenerator.cs`) is the most complex because it must produce a full height map with ramp tiles.

### 1. Base land and elevation

```csharp
foreach (var mpos in map.AllCells.MapCoords)
    map.Tiles[mpos] = terraformer.PickTile(pickAnyRandom, param.LandTile);

var elevation = terraformer.ElevationNoiseMatrix(elevationRandom, param.TerrainFeatureSize, param.TerrainSmoothing);
var roughnessMatrix = MatrixUtils.GridVariance(elevation, param.RoughnessRadius);

var landPlan = terraformer.SliceElevation(elevation, null, FractionMax - param.Water);
landPlan = MatrixUtils.BooleanBlotch(landPlan, ...);
```

The map is seeded with land, then an elevation map is sliced so that the lowest `Water` fraction becomes water. Note that TS uses `FractionMax - param.Water` because the *high* elevation is land and the *low* is water.

### 2. Coastline

The coastline can be either smooth beaches or jagged water cliffs:

```csharp
if (param.WaterCliffs)
{
    var waterCliffZone = ...;
    var waterCliffMask = MatrixUtils.CalibratedBooleanThreshold(roughnessMatrix, param.WaterRoughness, FractionMax);
    var partitionMask = waterCliffMask.Map(masked => masked ? waterCliffZone : beachZone);
    coastPaths = terraformer.PartitionPaths(coast, [beachZone, waterCliffZone], partitionMask, ...);
}
else
{
    coastPaths = CellLayerUtils.FromMatrixPoints(coast, map.Tiles)
        .Select(beach => TilingPath.QuickCreate(...)).ToList();
}
```

The coast is tiled, and the water side is filled with the water tile.

### 3. Mountains and height map

```csharp
var heightMap = new RampTiler.HeightMap(map);
...
for (var altitude = 0; altitude < param.MaximumAltitude; altitude++)
{
    elevationPlan = terraformer.SliceElevation(elevation, elevationPlan, param.Mountains, param.MinimumTerrainContourSpacing);
    elevationPlan = MatrixUtils.BooleanBlotch(elevationPlan, ...);
    var contours = MatrixUtils.BordersToPoints(elevationPlan);
    var partitionMask = cliffMask.Map(masked => masked ? cliffZone : clearZone);
    ...
    foreach (var tilingPath in tilingPaths)
    {
        var brush = tilingPath.OptimizeLoop().ExtendEdge(4).SetAutoEndDeviation().Tile(cliffTilingRandom);
        terraformer.PaintTiling(pickAnyRandom, brush, baseHeight);
        heightMap.MarkUntileable(brush.Shape.Select(cvec => CPos.Zero + cvec));
    }
    ...
    heightMap.AdjustCellHeights(1, shortMask);
    heightMap.AdjustCellHeights(cliffHeight, tallMask);
}
```

Mountains are built iteratively. At each altitude, a new slice of elevation is taken, and the contour is tiled with cliff segments. The `RampTiler.HeightMap` tracks which cells are already occupied by cliffs and which corner heights are adjustable. Short contours raise the local height by 1, while tall contours raise it by the full cliff height.

### 4. Ramps

```csharp
rampTiler.PullHeightMap(heightMap);
var noise = NoiseUtils.SymmetricFractalNoise(heightMapNoiseRandom, heightMap.Target.Size,
    terraformer.Rotations, terraformer.WMirror.ForCPos(), param.RampFeatureSize, NoiseUtils.PinkAmplitude);
noise = MatrixUtils.BinomialBlur(noise, 1);
noise = MatrixUtils.NormalizeRangeInPlace(noise, 3);
for (var i = 0; i < noise.Data.Length; i++)
    heightMap.Target[i] = (byte)Math.Clamp(noise[i] + heightMap.Target[i], byte.MinValue, byte.MaxValue);

heightMap.Soften(param.RampSoften);
if (!heightMap.Constrain(RampTiler.AdjustmentMode.LowerMiddle))
    throw new MapGenerationException("created unfixable heightmap");

var brush = rampTiler.TileHeightMap(heightMap, rampTilingRandom)
    ?? throw new MapGenerationException("created invalid heightmap");
terraformer.PaintTiling(rampTilingRandom, brush, 0);
```

After cliffs are fixed, a height noise layer is added, the height map is softened, and `RampTiler` selects ramp tiles that fit the required corner heights. This is the phase that makes Tiberian Sun maps look like Tiberian Sun.

### 5. Forests

```csharp
if (param.Forests > 0)
{
    var space = terraformer.CheckSpace(param.ClearTerrain);
    var passages = terraformer.PlanPassages(topologyRandom, ...);
    forestPlan = terraformer.BooleanNoise(forestRandom, param.ForestFeatureSize, param.Forests, param.ForestClumpiness);
    var replace = PlayableToReplaceable();
    foreach (var mpos in map.AllCells.MapCoords)
        if (!forestPlan[mpos] || !space[mpos] || passages[mpos])
            replace[mpos] = MultiBrush.Replaceability.None;
    terraformer.PaintArea(forestTilingRandom, replace, param.ForestObstacles);
}
```

Forests are painted with tree MultiBrushes on clear terrain, leaving passages open so units can move through.

### 6. Enforce symmetry

```csharp
if (param.EnforceSymmetry != 0)
{
    var asymmetries = terraformer.FindAsymmetries(param.DominantTerrain, true, param.EnforceSymmetry == 2);
    terraformer.PaintActors(symmetryTilingRandom, asymmetries, param.ForestObstacles);
}
```

If symmetry is enforced, asymmetric cells are covered with forest actors (or whatever obstacle collection is configured) to hide discrepancies.

### 7. Playable region

```csharp
playable = terraformer.ChoosePlayableRegion(terraformer.CheckSpace(param.PlayableTerrain, true, false, true), null);
if (playable.Count(p => p) < minimumPlayableSpace)
    throw new MapGenerationException("playable space is too small");
if (param.DenyWalledAreas)
    ...
```

The largest symmetric playable region is selected. If it is too small, generation fails. `DenyWalledAreas` fills unplayable pockets with obstructions.

### 8. Spawns, resource spawns, expansions, neutral buildings

These follow the same patterns as Classic (see below), but TS has additional resource bias for `veinhole` actors:

```csharp
resourceBiases.AddRange(
    terraformer.ActorsOfType("veinhole")
        .Select(a => new Terraformer.ResourceBias(a)
        {
            BiasRadius = new WDist(16 * 1024),
            Bias = (value, rSq) => value + (int)(512 * 1024 / (1024 + Exts.ISqrt(rSq))),
        }));
```

### 9. Ground decoration and LAT tiling

```csharp
void DecorateFloorTiles(ushort tile, int fraction, CellLayer<bool> addIn = null)
{
    var tileable = terraformer.CheckSpace(param.LandTile);
    var noise = terraformer.BooleanNoise(groundTypeNoiseRandom, 10240, fraction);
    ...
    foreach (var cpos in map.Tiles.CellRegion)
        if (noise[cpos])
            map.Tiles[cpos] = new TerrainTile(tile, 0);
}

DecorateFloorTiles(param.ForestFloorTile, param.ForestFloor, forestPlan);
foreach (var (tile, fraction) in param.OtherGround)
    DecorateFloorTiles(tile, fraction);

terraformer.PaintTiling(pickAnyRandom, param.LatTiler.OfferReplacements(map, pickAnyRandom), 0);
if (param.UseIceLatTiler)
    terraformer.PaintTiling(pickAnyRandom, param.IceLatTiler.OfferReplacements(map, pickAnyRandom), 0);

terraformer.RepaintTiles(repaintRandom, param.RepaintTiles);
```

TS applies grass/rough/snow floor transitions using noise, then runs `LatTiler` rules to smooth transitions between ground types, and finally repaints specific tiles (such as water edges) with dedicated MultiBrush collections.

## ClassicMapGenerator Phases

The Red Alert and Tiberian Dawn generator (`ClassicMapGenerator.cs`) is the baseline shared generator. It lives in `OpenRA.Mods.Common` so both `ra` and `cnc` mods can use it.

### 1. Base land and elevation

```csharp
foreach (var mpos in map.AllCells.MapCoords)
    map.Tiles[mpos] = terraformer.PickTile(pickAnyRandom, param.LandTile);

var elevation = terraformer.ElevationNoiseMatrix(elevationRandom, param.TerrainFeatureSize, param.TerrainSmoothing);
var roughnessMatrix = MatrixUtils.GridVariance(elevation, param.RoughnessRadius);
```

Same as TS, but Classic has no height system.

### 2. Water

```csharp
Matrix<bool> mapShape;
if (param.ExternalCircularBias == 0)
    mapShape = new Matrix<bool>(CellLayerUtils.CellBounds(map).Size.ToInt2()).Fill(true);
else
    mapShape = CellLayerUtils.ToMatrix(terraformer.CenteredCircle(true, false, externalCircleRadius), false);

var landPlan = terraformer.SliceElevation(elevation, mapShape, FractionMax - param.Water);

if (param.ExternalCircularBias > 0)
    ...

landPlan = MatrixUtils.BooleanBlotch(landPlan, ...);
```

Classic supports `ExternalCircularBias`: 0 = square map, 1 = circle of mountains, -1 = circle of water. The map shape is used to force an outer ring of land or water.

### 3. Coast / water cliffs

```csharp
if (param.WaterRoughness > 0)
{
    var beachZone = ...;
    var waterCliffZone = ...;
    var waterCliffMask = MatrixUtils.CalibratedBooleanThreshold(roughnessMatrix, param.WaterRoughness, FractionMax);
    var partitionMask = waterCliffMask.Map(masked => masked ? waterCliffZone : beachZone);
    coastPaths = terraformer.PartitionPaths(coast, [beachZone, waterCliffZone], partitionMask, ...);
}
else
{
    coastPaths = CellLayerUtils.FromMatrixPoints(coast, map.Tiles)
        .Select(beach => TilingPath.QuickCreate(...)).ToList();
}

var landCoastWater = terraformer.PaintLoopsAndFill(coastTilingRandom, coastPaths, ...,
    [new MultiBrush().WithTemplate(map, param.WaterTile, CVec.Zero)], null, null, 0);
```

The coastline is tiled and the water side is filled with the water tile.

### 4. Cliffs / mountains

```csharp
if (param.Mountains > 0)
{
    var cliffMask = MatrixUtils.CalibratedBooleanThreshold(roughnessMatrix, param.Roughness, FractionMax);
    var cliffPlan = Matrix<bool>.Zip(landPlan, mapShape, (a, b) => a && b);

    for (var altitude = 0; altitude < param.MaximumAltitude; altitude++)
    {
        cliffPlan = terraformer.SliceElevation(elevation, cliffPlan, param.Mountains, param.MinimumTerrainContourSpacing);
        cliffPlan = MatrixUtils.BooleanBlotch(cliffPlan, ...);
        var unmaskedCliffs = MatrixUtils.BordersToPoints(cliffPlan);
        var maskedCliffs = MatrixUtils.MaskPathPoints(unmaskedCliffs, cliffMask);
        var cliffs = CellLayerUtils.FromMatrixPoints(maskedCliffs, map.Tiles)
            .Where(cliff => cliff.Length >= param.MinimumCliffLength).ToArray();
        foreach (var cliff in cliffs)
        {
            var cliffPath = TilingPath.QuickCreate(...);
            var brush = cliffPath.Tile(cliffTilingRandom);
            terraformer.PaintTiling(pickAnyRandom, brush);
        }
    }
}
```

Mountains are carved as impassable cliffs. Classic uses `MaskPathPoints` to place cliffs only on rough parts of the contour.

### 5. Forests

Identical in spirit to TS but with no height offset:

```csharp
if (param.Forests > 0)
{
    var space = terraformer.CheckSpace(param.ClearTerrain);
    var passages = terraformer.PlanPassages(topologyRandom, ...);
    var forestNoise = terraformer.BooleanNoise(forestRandom, ...);
    var replace = PlayableToReplaceable();
    ...
    terraformer.PaintArea(forestTilingRandom, replace, param.ForestObstacles);
}

if (param.EnforceSymmetry != 0)
    ...
```

### 6. Playable region

Same as TS but with the `poison` circle handling for `ExternalCircularBias`.

### 7. Roads

Classic is the only generator that generates roads:

```csharp
if (param.Roads)
{
    const int RoadMinimumShrinkLength = 12;
    const int RoadStraightenShrink = 4;
    const int RoadStraightenGrow = 2;
    const int RoadInertialRange = 8;

    var roadPaths = terraformer.PlanRoads(
        terraformer.CheckSpace(param.ClearTerrain, true, false),
        param.RoadSpacing,
        RoadMinimumShrinkLength + 2 * (RoadStraightenShrink + param.RoadShrink));
    foreach (var roadPath in roadPaths)
    {
        var tilingPath = TilingPath.QuickCreate(...)
            .StraightenEnds(RoadStraightenShrink + param.RoadShrink, RoadStraightenGrow,
                RoadMinimumShrinkLength, RoadInertialRange)
            .RetainIfValid();
        if (tilingPath.Points == null)
            continue;
        var brush = tilingPath.Tile(roadTilingRandom);
        terraformer.PaintTiling(pickAnyRandom, brush);
    }
}
```

Roads are planned by `PlanRoads`, which finds the medial axis of clear space, then straightens the ends and tiles with road MultiBrushes.

### 8. Resources and entities

Classic places spawns, expansion resource spawns, neutral buildings, and grows resources using the same helpers as TS. The main differences are:

- No `veinhole` bias.
- No `RampTiler` or `LatTiler` post-processing.
- Resources are grown with `ResourceDensityMode.Adjacency` (default), whereas TS uses `BakedAdjacency`.

### 9. Civilian buildings

```csharp
if (param.CivilianBuildings > 0)
{
    var decorationNoise = terraformer.DecorationPattern(...);
    terraformer.PaintActors(decorationTilingRandom, decorationNoise, param.CivilianBuildingsObstacles,
        alwaysPreferLargerBrushes: true);
}
```

Civilian buildings are scattered using `DecorationPattern`, which ensures clusters of minimum density.

### 10. Repaint

```csharp
terraformer.RepaintTiles(repaintRandom, param.RepaintTiles);
```

Classic ends with a simple repaint pass; it does not use `LatTiler` because the terrain system does not require it.

![Configuration (yaml) diagram](images/Part_07_Chapter_06_Mod_Generators-annotated-yaml-snippet-diagram-showing-the-key-fields-and-ho-6a1b98.svg)

## Configuration (YAML)


### Generator registration

Each mod registers its generator under `^MapGenerators:`:

```yaml
^MapGenerators:
    D2kMapGenerator@d2k:
        Type: d2k
        Name: map-generator-d2k
        Tilesets: ARRAKIS
        Settings:
            ...
```

The `Type` string is what the engine uses to select the generator. The `Name` is a Fluent reference key for the UI label. `Tilesets` restricts which tilesets the generator can be used with.

### Settings options

Settings use the option system from `MapGeneratorSettings`:

- `IntegerOption` — integer value (e.g., `Seed`).
- `MultiChoiceOption` — one of several named choices (e.g., `TerrainType`, `Symmetry`, `Resources`).
- `MultiIntegerChoiceOption` — integer choice list (e.g., `Players`).

A hidden default block is typically placed under `MultiChoiceOption@hidden_defaults:Choice@hidden_defaults:Settings` so that every option has a base value before user overrides are applied.

### Tileset overrides

Because Classic and TS support multiple tilesets, the YAML uses a hidden `MultiChoiceOption@hidden_tileset_overrides` to patch settings per tileset. For example:

```yaml
MultiChoiceOption@hidden_tileset_overrides:
    Choice@temperat:
        Tileset: TEMPERATE
        Settings:
            ForestFloorTile: 626
            OtherGround:
                535: 150
                150: 250
            LatTiler:
                Rule@Rough:
                    ...
```

These overrides are merged at runtime by `MapGeneratorSettings.Compile`.

### Key parameters by generator

| Parameter | D2k | Classic | TS |
|-----------|-----|---------|----|
| TerrainFeatureSize | yes | yes | yes |
| SandDetailFeatureSize | yes | no | no |
| DuneFeatureSize | yes | no | no |
| ForestFeatureSize | no | yes | yes |
| ResourceFeatureSize | yes | yes | yes |
| CivilianBuildingsFeatureSize | no | yes | yes |
| RampFeatureSize | no | no | yes |
| Water | no | yes | yes |
| Mountains | no | yes | yes |
| Forests | no | yes | yes |
| Dunes | yes | no | no |
| SandCliffs | yes | no | no |
| SandDetail | yes | no | no |
| RockRoughness / SandRoughness | yes | no | no |
| Roughness | no | yes | yes |
| WaterRoughness | no | yes | yes |
| WaterCliffs | no | no | yes |
| ExternalCircularBias | no | yes | no |
| Roads | no | yes | no |
| RampTiles | no | no | yes |
| LatTiler | no | no | yes |
| UseIceLatTiler | no | no | yes |
| ForestFloor / OtherGround | no | no | yes |
| RepaintTiles | no | yes | yes |
| MaximumAltitude | no | yes | yes |
| RampSoften | no | no | yes |
| MinimumBeachLength | no | yes | yes |
| MinimumWaterCliffLength | no | yes | yes |
| MinimumCoastStraight | no | yes | yes |
| MinimumCliffStraight | no | no | yes |
| MinimumCliffLength | no | yes | yes |
| MinimumClearLength | no | no | yes |
| MinimumLandSeaThickness | no | yes | yes |
| MinimumMountainThickness | no | yes | yes |
| MinimumRockSandThickness | yes | no | no |
| MinimumSandCliffThickness | yes | no | no |
| MinimumDuneThickness | yes | no | no |
| MinimumRockStraight | yes | no | no |
| MinimumSandCliffStraight | yes | no | no |
| MinimumRockSmoothLength | yes | no | no |
| MinimumSandRockCliffLength | yes | no | no |
| MinimumSandSandCliffLength | yes | no | no |
| MinimumSandLength | yes | no | no |
| SandContourSpacing | yes | no | no |
| DuneContourSpacing | yes | no | no |
| SandDetailCutout | yes | no | no |
| MaximumSandDetailCutoutSpacing | yes | no | no |
| ForestCutout | no | yes | yes |
| MaximumCutoutSpacing | no | yes | yes |
| ForestClumpiness | no | yes | yes |
| SandDetailClumpiness | yes | no | no |
| ResourceClumpiness | yes | no | no |
| OreClumpiness | no | yes | yes |
| ResourceUniformity | yes | no | no |
| OreUniformity | no | yes | yes |
| SpawnBuildSize | no | yes | yes |
| SpawnRegionSize | yes | yes | yes |
| MinimumSpawnRadius | yes | yes | yes |
| SpawnReservation | yes | yes | yes |
| SpawnResourceSpawns | no | yes | yes |
| SpawnResourceBias | no | yes | yes |
| ResourcesPerPlayer | yes | yes | yes |
| MaximumExpansionResourceSpawns | no | yes | yes |
| MaximumResourceSpawnsPerExpansion | no | yes | yes |
| MinimumExpansionSize | no | yes | yes |
| MaximumExpansionSize | no | yes | yes |
| ExpansionInner | no | yes | yes |
| ExpansionBorder | no | yes | yes |
| MinimumBuildings | no | yes | yes |
| MaximumBuildings | no | yes | yes |
| BuildingWeights | no | yes | yes |
| CivilianBuildings | no | yes | yes |
| CivilianBuildingDensity | no | yes | yes |
| MinimumCivilianBuildingDensity | no | yes | yes |
| CivilianBuildingDensityRadius | no | yes | yes |
| CreateEntities | yes | yes | yes |
| AreaEntityBonus | yes | yes | yes |
| PlayerCountEntityBonus | yes | yes | yes |
| CentralSpawnReservationFraction | yes | yes | yes |
| DenyWalledAreas | no | yes | yes |
| EnforceSymmetry | no | yes | yes |
| Mirror | yes | yes | yes |
| Rotations | yes | yes | yes |
| Seed | yes | yes | yes |

### Resource spawn seeds

Classic and TS define which actor types seed which resource type during the resource growth phase:

```yaml
ResourceSpawnSeeds:
    mine: Ore
    gmine: Gems
```

```yaml
ResourceSpawnSeeds:
    tibtre01: Tiberium
    tibtre02: Tiberium
    tibtre03: Tiberium
    bigblue: BlueTiberium
    veinhole: Veins
```

D2k only has a single `ResourceSpawn: spicebloom.spawnpoint` and `Resource: Spice`, because the spice bloom actor is the seed.

## Interconnectivity

### Generator → Terraformer

Every generator delegates almost all work to `Terraformer`:

- `terraformer.InitMap()` — sets map bounds, title, author, mod ID.
- `terraformer.ElevationNoiseMatrix(...)` — creates symmetric fractal elevation.
- `terraformer.BooleanNoise(...)` — creates boolean noise for forests, sand detail, etc.
- `terraformer.SliceElevation(...)` — turns elevation into boolean masks.
- `terraformer.PartitionPath` / `PartitionPaths` — splits contour paths into segment-typed sub-paths.
- `terraformer.PaintLoopsAndFill(...)` — tiles a loop and fills one side.
- `terraformer.PaintTiling(...)` — paints a single tiled brush.
- `terraformer.PaintArea(...)` — paints MultiBrushes over a replaceability mask.
- `terraformer.PaintActors(...)` — places actors over a boolean mask.
- `terraformer.CheckSpace(...)` — builds boolean masks of valid terrain.
- `terraformer.GetZoneable(...)` — builds a mask of cells safe for actor/resource placement.
- `terraformer.ChoosePlayableRegion(...)` — finds the largest symmetric playable region.
- `terraformer.ChooseSpawnInZoneable(...)` — picks a spawn location.
- `terraformer.ProjectPlaceDezoneActor(...)` — places an actor and its symmetry projections.
- `terraformer.AddActor(...)` / `AddActorCluster(...)` / `AddDistributedActors(...)` — places actors/resources.
- `terraformer.ResourceNoise(...)` / `PlanResources(...)` / `GrowResources(...)` — resource growth.
- `terraformer.TargetWalkingDistance(...)` / `PlanRoads(...)` / `PlanPassages(...)` — pathfinding-based planning.
- `terraformer.ImproveSymmetry(...)` / `FindAsymmetries(...)` — symmetry helpers.
- `terraformer.ReorderPlayerSpawns()` / `BakeMap()` — finalization.

### Generator → MatrixUtils / CellLayerUtils

Low-level matrix operations are performed by static utilities:

- `MatrixUtils.CalibratedBooleanThreshold(...)` — converts a real-valued matrix to a boolean mask at a target fraction.
- `MatrixUtils.BooleanBlotch(...)` — smooths, thickens, and removes isolated cells from boolean masks.
- `MatrixUtils.BordersToPoints(...)` — extracts contour points from a boolean matrix.
- `MatrixUtils.GridVariance(...)` — computes local variance to detect roughness.
- `MatrixUtils.PointsChirality(...)` — determines inside/outside of a loop.
- `MatrixUtils.MaskPathPoints(...)` — filters contour points by a mask.
- `MatrixUtils.DeflateSpace(...)` / `KernelDilateOrErode(...)` — morphological operations.
- `MatrixUtils.DirectionMapToPaths(...)` / `RemoveStubsFromDirectionMapInPlace(...)` — skeleton-to-path conversion.
- `CellLayerUtils.CheckSpace(...)` / `Intersect(...)` / `Union(...)` / `Subtract(...)` — boolean cell-layer algebra.
- `CellLayerUtils.ToMatrix(...)` / `FromMatrix(...)` / `FromMatrixPoints(...)` — conversions between `CellLayer` and `Matrix`.
- `CellLayerUtils.ChebyshevRoom(...)` / `OverCircle(...)` — distance transforms and circular masks.
- `CellLayerUtils.FindRandomBest(...)` / `PickWeighted(...)` — selection helpers.

### Generator → TilingPath / MultiBrush

After a generator decides *where* a path should go, `TilingPath` decides *how* to tile it:

- `TilingPath.QuickCreate(...)` — builds a path from a contour and segment types.
- `OptimizeLoop()`, `ExtendEdge(...)`, `SetAutoEndDeviation()`, `StraightenEnds(...)`, `RetainIfValid()` — path refinements.
- `Tile(random)` — chooses a chain of `MultiBrush` segments that fit the path.

`MultiBrush` segments are defined in tileset YAML with `Start`, `Inner`, and `End` type strings, and `Points` that describe the path geometry they cover. The generator passes segment type names like `RockSmooth`, `SandRockCliff`, `Cliff`, `Beach`, `Road`, `Clear`, etc.

### Generator → RampTiler / LatTiler (TS only)

- `RampTiler.HeightMap` — tracks target and bounds for corner heights.
- `RampTiler.PullHeightMap(...)` / `TileHeightMap(...)` — converts a height map into ramp tiles.
- `LatTiler.OfferReplacements(...)` — applies transition rules between ground types.

### Generator → ModData / Rules

The generator frequently queries the ruleset:

- `map.Rules.TerrainInfo` and `modData.DefaultTerrainInfo[tileset]` for terrain type lookups.
- `map.Rules.Actors[SystemActors.World].TraitInfoOrDefault<ResourceLayerInfo>().ResourceTypes` for resource type resolution.
- `map.Rules.Actors[SystemActors.Player].TraitInfoOrDefault<PlayerResourcesInfo>().ResourceValues` for resource value calculation.

![Algorithms diagram](images/Part_07_Chapter_06_Mod_Generators-algorithm-diagram-or-pseudocode-flowchart-for-the-non-trivia-5983ed.svg)

## Algorithms


### Symmetric fractal noise

All terrain patterns begin with `NoiseUtils.SymmetricFractalNoise` or `NoiseUtils.SymmetricFractalNoiseIntoCellLayer`. These generate diamond-square / midpoint-displacement noise that is already consistent with the chosen symmetry. The `Terraformer.WMirror` and `Rotations` are passed in so that noise values at symmetric points are identical.

### Elevation slicing

`Terraformer.SliceElevation` converts a continuous elevation matrix into a boolean mask by finding a threshold that leaves a target fraction of the masked cells as `true`. It respects an optional minimum contour spacing so that successive slices do not overlap too closely.

### Boolean blotch

`MatrixUtils.BooleanBlotch` is a morphological smoothing step. It:

1. Dilates / erodes the mask to enforce minimum thickness.
2. Removes small isolated components.
3. Optionally biases the result toward the majority (e.g., if water is less than half the map, keep more land).

The `SmoothingThreshold` controls how aggressively small holes and peninsulas are closed.

### Contour partitioning

`Terraformer.PartitionPath` is one of the most important algorithms. It:

1. Takes a closed or open contour (array of `int2` points).
2. Uses a voting / dynamic-programming approach to find the best way to split the contour into segments whose `PathPartitionZone` matches the majority of points in that segment.
3. Builds a `TilingPath` per segment with correct start/end segment types and directions.
4. Honors `MinimumLength`, `MinimumStraight`, and `MaximumDeviation` constraints.

This is what allows a single coastline to be partly smooth beach and partly rocky cliff, or a rock border to alternate between smooth and jagged transitions.

### Inside/outside fill

`PaintLoopsAndFill` uses `InsideOutside` to determine which cells are inside each tiled loop. It relies on `MatrixUtils.PointsChirality`: for a clockwise loop, the right-hand side is inside; for counter-clockwise, the left-hand side. The generator then fills the appropriate side with a MultiBrush or a single tile.

### Path planning for passages

`Terraformer.PlanPassages` takes a space mask and a cutout radius, and returns a mask of passageways that, when subtracted, keep the space connected. It uses `MatrixUtils.DeflateSpace` to shrink the space to a skeleton, then dilates by the cutout radius. If `maximumCutoutSpacing` is set, it also adds extra corridors to ensure no region is too far from a passage.

### Road planning

`Terraformer.PlanRoads` finds the medial axis of clear space by:

1. Enlarging the map to an even-multiple size for isometric grid compatibility.
2. Improving symmetry.
3. Dilating the obstacles by `minimumSpacing`.
4. Deflating the remaining free space to a skeleton.
5. Removing stubs and asymmetric paths.
6. Converting the skeleton back to paths.

This produces roads that run through the middle of clear areas.

### Spawn placement

`ChooseSpawnInZoneable` uses a `SpawnBias` layer that combines:

- Distance from the map center (`CentralSpawnReservationFraction`).
- Distance from symmetry projections (so spawns are not placed too close to their mirrored copies).
- Local free-space room (`ChebyshevRoom`).

The chosen cell maximizes these factors while satisfying `MinimumSpawnRadius` and `SpawnReservation`.

### Resource growth

`PlanResources` combines a noise pattern with per-resource strength maps. Each `ResourceBias` adds or excludes value around actors. The result is a plan of resource type and placement score.

`GrowResources` is a greedy priority algorithm:

1. Sorts all cells by score (highest first).
2. Places resources in symmetry-projected groups.
3. Computes the actual value of the 3×3 neighborhood using the same density logic as the runtime `ResourceLayer`.
4. Stops when the target value is reached.

`ResourceDensityMode.Adjacency` means density is calculated at runtime; `BakedAdjacency` saves the density into the map.

### Decoration pattern

`DecorationPattern` places civilian buildings or other decorations in out-of-the-way locations. It uses white noise for placement, pink noise for density, and a repeated boolean-blur filter to enforce a minimum local density so that villages do not consist of a single isolated building.

![Extension points diagram](images/Part_07_Chapter_06_Mod_Generators-extension-hook-diagram-showing-the-interface-s-to-implement-b4a27b.svg)

## Extension Points


### Adding a new mod-specific generator

The cleanest way to add a new generator is to follow the same two-class pattern:

1. Create a new assembly or mod-specific traits file.
2. Define a `TraitInfo` class that implements `IEditorMapGeneratorInfo`.
3. Add a small companion class that implements `IEditorTool`.
4. Register the generator in the mod's YAML under `^MapGenerators:`.

The generator class must provide:

```csharp
public sealed class MyMapGeneratorInfo : TraitInfo, IEditorMapGeneratorInfo
{
    public readonly string Type = ...;
    public readonly string Name = ...;
    public readonly ImmutableArray<string> Tilesets = ...;
    public readonly string MapTitle = ...;
    public readonly string PanelWidget = ...;
    public readonly MiniYaml Settings; // loaded via SettingsLoader

    string IMapGeneratorInfo.Type => Type;
    string IMapGeneratorInfo.Name => Name;
    string IMapGeneratorInfo.MapTitle => MapTitle;
    ImmutableArray<string> IEditorMapGeneratorInfo.Tilesets => Tilesets;

    public IMapGeneratorSettings GetSettings()
        => new MapGeneratorSettings(this, Settings);

    public Map Generate(ModData modData, MapGenerationArgs args) { ... }
    public bool TryGenerateMetadata(...) { ... }

    public override object Create(ActorInitializer init)
        => new MyMapGenerator(this);
}
```

### Reusing ClassicMapGenerator

If the new mod's terrain system is similar to Red Alert or Tiberian Dawn, you do not need to write a new generator class. You can simply add a new `ClassicMapGenerator` entry in the mod's YAML with different tilesets, terrain sets, and option overrides. `ClassicMapGenerator` already reads all its parameters from YAML and does not hardcode game-specific behavior.

### Custom terrain phases

Because the `Terraformer` API is public, a new generator can mix and match the phases in any order. For example, you could:

- Add a new phase that places crater MultiBrushes using `terraformer.PaintArea`.
- Add a new phase that carves rivers using `PaintLoopsAndFill` with a water-side fill.
- Add a new phase that places mod-specific actor seeds using `AddActorCluster`.

### Custom segment types

You can define new segment types in tileset YAML under `MultiBrushCollections/Segmented` and then reference them from the generator YAML:

```yaml
MultiBrushCollections:
    Segmented:
        MultiBrush@MyCliff:
            Template: 123
            Segment:
                Start: MyCliff.R
                End: MyCliff.R
                Points: 0,0, 1,0
```

The generator can then use `SegmentType = "MyCliff"` in a `PathPartitionZone`.

### Custom resource density modes

The `Terraformer.ResourceDensityMode` enum currently has `Adjacency` and `BakedAdjacency`. A new generator could add a third mode by modifying the enum and `GrowResources`, but this is a deeper change to shared code.

### Custom option UI

The `Settings` MiniYaml uses the option classes from `OpenRA.Mods.Common/MapGenerator/MapGeneratorSettings.cs`. If you need new UI behavior, you may need to add a new option type there and in the editor UI.

![Common pitfalls  guardrails diagram](images/Part_07_Chapter_06_Mod_Generators-checklist-infographic-style-diagram-summarizing-the-top-pitf-fb069e.svg)

## Common Pitfalls / Guardrails


### 1. Seed stability

The source code explicitly warns that new `MersenneTwister` derivatives should be **appended only** to the list of sub-generators. Reordering or removing them changes the random sequence for all subsequent phases. If you remove a generator, replace it with a `random.Next()` call.

### 2. Symmetry validation

`ClassicMapGenerator.Validate` and `TSMapGenerator` enforce that:

- `Rotations` must be 1, 2, or 4 for `EnforceSymmetry` to work.
- `Players` must be divisible by the symmetry projection count.
- `Players` must not exceed 32.

D2k does not have these explicit validations in `Parameters`, but the same logic is implicit in `ProjectPlaceDezoneActor`.

### 3. Minimum thickness values

`BooleanBlotch` requires `MinimumLandSeaThickness`, `MinimumMountainThickness`, etc. to be at least 1. If a thickness is too small, tiled paths may fail because the contour is too narrow for the MultiBrush segments.

### 4. Tileset mismatch

The generator's `Tilesets` list must match the tileset being used. If a tileset is missing a required MultiBrush collection (e.g., `Segmented`), the generator will throw during `MultiBrush.LoadCollection`.

### 5. Resource value mismatch

`GrowResources` uses the `PlayerResourcesInfo.ResourceValues` dictionary. If a resource type in `ResourceSpawnSeeds` or `DefaultResource` is not in that dictionary, the value calculation will fail.

### 6. Height map constraints (TS)

TS must produce a height map that `RampTiler` can tile. If cliffs are too tall or too close, `heightMap.Constrain(...)` may fail and throw `"created unfixable heightmap"`. The `RampSoften` and `MaximumAltitude` parameters are the main levers for avoiding this.

### 7. Playable region not found

If the map is too small or the water/mountain coverage is too high, `ChoosePlayableRegion` returns `null` and the generator throws `"could not find a playable region"`. Increase the map size or reduce the terrain coverage.

### 8. Actor placement exhaustion

`AddActor` returns `false` when there is no room. Generators generally use this as a signal to stop trying, rather than throwing. However, if `CreateEntities` is true but the map is too constrained, target counts may not be met and the resulting map will have fewer resources/buildings than expected.

### 9. Mirror enum parsing

The `Mirror` field in YAML must be parseable by `Symmetry.TryParseMirror`. The `MirrorLoader` helper throws a `YamlException` for invalid values.

### 10. Fluent references

The `FluentReferences` field in each `Info` class is loaded by reflecting over the `Settings` MiniYaml and collecting all `Label` keys. If you add a new option label, make sure the corresponding Fluent string exists or the linter will complain.

## What to read next

- [Part 7.4 — Terraformer](Part_07_Chapter_04_Terraformer.md) for the shared toolbox that all three generators use.
- [Part 7.7 — Resource and Actor Placement](Part_07_Chapter_07_Resources_Actors.md) for how the `ActorPlan` list is turned into player spawns and resources.
- [Part 7.8 — Random Map Generator Extension Points](Part_07_Chapter_08_Extension_Points.md) for adding your own mod-specific generator from scratch.

## Summary

This chapter explains how the OpenRA map generator is split into mod-specific generators and shared engine tooling.

After reading this chapter, you should be able to:

- **The `Info` class** (`D2kMapGeneratorInfo`, `TSMapGeneratorInfo`, `ClassicMapGeneratorInfo`) — implements `IEditorMapGeneratorInfo` and owns:

If any of the concepts above feel unclear, review the relevant section before continuing. For source files and further reading, see the References section.


## References

- `OpenRA.Mods.D2k/Traits/World/D2kMapGenerator.cs` — Dune 2000 generator.
- `OpenRA.Mods.Cnc/Traits/World/TSMapGenerator.cs` — Tiberian Sun generator.
- `OpenRA.Mods.Common/Traits/World/ClassicMapGenerator.cs` — Red Alert / Tiberian Dawn generator.
- `OpenRA.Mods.Common/MapGenerator/Terraformer.cs` — shared terraforming toolkit.
- `OpenRA.Mods.Common/MapGenerator/TilingPath.cs` — path tiling.
- `OpenRA.Mods.Common/MapGenerator/MultiBrush.cs` — tile/actor brush definitions.
- `OpenRA.Mods.Common/MapGenerator/RampTiler.cs` — ramp tile fitting for TS.
- `OpenRA.Mods.Common/MapGenerator/LatTiler.cs` — ground-type transition rules.
- `OpenRA.Mods.Common/MapGenerator/MapGeneratorSettings.cs` — option UI model.
- `OpenRA.Game/Traits/TraitsInterfaces.cs` — `IMapGeneratorInfo` contract.
- `OpenRA.Mods.Common/TraitsInterfaces.cs` — `IEditorMapGeneratorInfo` contract.
- `mods/d2k/rules/map-generators.yaml` — D2k generator YAML.
- `mods/ts/rules/map-generators.yaml` — TS generator YAML.
- `mods/ra/rules/map-generators.yaml` — RA generator YAML.
- `mods/cnc/rules/map-generators.yaml` — CNC generator YAML.
- `mods/d2k/tilesets/arrakis.yaml` — D2k MultiBrush collections.
- `mods/ra/tilesets/*.yaml`, `mods/cnc/tilesets/*.yaml`, `mods/ts/tilesets/*.yaml` — Classic/TS MultiBrush collections.

For a deeper treatment of the shared algorithms, see Part 7 Chapter 4 (Terraformer), Chapter 5 (MultiBrush), and Chapter 7 (Resources and Actors).