# Chapter 7.5 — MultiBrush and Tile Placement

## Purpose

`[MultiBrush](../appendices/Appendix_A_Glossary.md)` is OpenRA’s template-based tile (and actor) placement system. It takes a YAML-defined “super-template” — one or more terrain templates, individual terrain tiles, and/or actor placements — and applies it to a map as a single unit. The system is used by the map generator and editor tooling to paint large, coherent terrain features (beaches, cliffs, roads, water-to-land transitions) while respecting which cells are allowed to be overwritten, and by how much.

The core idea is: a modder or generator defines a brush once in a [TileSet](../appendices/Appendix_A_Glossary.md) YAML file, and code can later ask the `MultiBrush` system to stamp that brush onto the map, optionally randomizing tile variants, adjusting heights, and laying down matching actors.

## Learning Objectives


After studying this chapter, you should be able to:

- Explain how MultiBrush provides template-based tile and actor placement.
- Describe the YAML data layer (MultiBrushInfo), segments, and runtime layer (MultiBrush).
- Load brush collections from tileset YAML and paint them onto a Map.
- Understand Replaceability contracts and how they control overwrite behavior.
- Use segments to chain brushes for roads, cliffs, and beaches.
- Implement a new brush definition and validate it with the lint pass.

## Files

| File | Responsibility |
| :---- | :---- |
| `OpenRA.Mods.Common/MapGenerator/MultiBrush.cs` | Contains `MultiBrushInfo`, `MultiBrushSegment`, and `MultiBrush`; the full runtime implementation of brush parsing, composition, and painting. |
| `OpenRA.Mods.Common/MapGenerator/Direction.cs` | Defines the `Direction`/`DirectionMask` values used by segment directions (e.g. `R`, `RD`, `D`, `LD`, `L`, `LU`, `U`, `RU`). |
| `OpenRA.Mods.Common/Terrain/DefaultTerrain.cs` | Loads the `MultiBrushCollections` node from a tileset YAML file and exposes it through `ITemplatedTerrainInfo`. |
| `OpenRA.Mods.Common/Traits/World/TilingPathTool.cs` | Downstream consumer that loads all segmented brushes and chains them into editor placeable paths. |
| `OpenRA.Mods.Common/Lint/CheckMultiBrushes.cs` | Lint pass that instantiates every `MultiBrushInfo` at load time to catch YAML/template errors early. |

![Architecture diagram](images/Part_07_Chapter_05_MultiBrush-architecture-diagram-showing-the-main-classes-interfaces-and-9161e6.svg)

## Architecture


The subsystem is split into three layers:

1. **YAML Data Layer — `MultiBrushInfo`**  
   A plain, immutable, [FieldLoader](../appendices/Appendix_A_Glossary.md)-driven definition. It can be loaded from [MiniYaml](../appendices/Appendix_A_Glossary.md) before a map is available, and is later turned into a `MultiBrush` once a `Map` (and therefore the tileset and rules) exists. `MultiBrushInfo.ParseCollection` is the normal entry point for reading a tileset collection.

2. **Segment Layer — `MultiBrushSegment`**  
   Describes how some brushes link head-to-tail (e.g. a cliff that continues in a straight line or turns a corner). A segment is optional; many brushes are standalone.

3. **Runtime Layer — `MultiBrush`**  
   The actual paintable object. It owns a list of tile ranges, a list of `[ActorPlan](../appendices/Appendix_A_Glossary.md)`s, an optional segment, a weight, and a cached shape/footprint. It knows how to paint itself onto a `Map`, how to merge into another brush, and how to be selected by weighted random choice.

```
Tileset YAML
   |
   v
MultiBrushInfo.ParseCollection
   |
   v
MultiBrushInfo (per-brush definition)
   |
   +--> MultiBrushSegment (optional)
   |
   v
new MultiBrush(map, info)
   |
   v
MultiBrush.Paint / MultiBrush.PaintArea
   |
   v
map.Tiles / map.Height / actorPlans
```

### Key classes

- **`MultiBrushInfo`** — YAML-bound definition. Contains:
  - `Weight` (int, default 1000)
  - `Actors` (`ImmutableArray<ActorInfo>`)
  - `BackingTile` (`TerrainTile?`)
  - `Templates` (`ImmutableArray<TemplateInfo>`)
  - `Tiles` (`ImmutableArray<TileInfo>`)
  - `Segment` (`MultiBrushSegment`)

- **`MultiBrushInfo.ActorInfo`** — actor type plus a `WVec` offset.
- **`MultiBrushInfo.TemplateInfo`** — terrain template ID plus a `CVec` offset.
- **`MultiBrushInfo.TileInfo`** — explicit `TerrainTile` plus a `CVec` offset.

- **`MultiBrushSegment`** — describes chaining:
  - `Start` — required, includes a direction suffix (e.g. `Beach.L`, `Cliff.RD`).
  - `Inner` — optional, no direction suffix (e.g. `Beach`). If omitted, `Start` and `End` can be used as inner types.
  - `End` — required, includes a direction suffix.
  - `Points` — cardinal-step path of `-X-Y` corners of template tiles.

- **`MultiBrush`** — runtime brush. Notable members:
  - `Weight`
  - `tiles` — list of `(CVec XY, TileRange TileRange)`
  - `actorPlans` — list of `ActorPlan`
  - `Segment`
  - `Shape` — cached footprint (tile cells + actor cells)
  - `Area` — footprint cell count
  - `FirstCell` — first cell in the shape ordering (used for alignment)

- **`MultiBrush.Replaceability`** — a mask describing how a cell may be modified:
  - `None` (0) — cannot be touched.
  - `Tile` (1) — the tile may be replaced; an actor may also be placed.
  - `Actor` (2) — the tile must stay, but an actor may be placed.
  - `Any` (3) — both tile and actor may be placed.

- **`MultiBrush.TileRange`** — a tile type plus an optional index range, height offset, and ramp. Supports randomization between `MinIndex` and `MaxIndex`.

![Data flow  code path diagram](images/Part_07_Chapter_05_MultiBrush-sequence-flow-diagram-tracing-the-execution-path-from-trigge-035864.svg)

## Data Flow / Code Path


### 1. Loading from YAML

`DefaultTerrainInfo` (in `DefaultTerrain.cs`) parses the top-level `MultiBrushCollections` node in the tileset YAML. Each collection is stored as `FrozenDictionary<string, ImmutableArray<MultiBrushInfo>>` in `DefaultTerrain.cs`.

When code needs a named collection, it calls:

```csharp
var brushes = MultiBrush.LoadCollection(map, name);  // MultiBrush.cs
```

`LoadCollection` fetches the `MultiBrushInfo` array and constructs a `MultiBrush` for each one:

```csharp
public MultiBrush(Map map, MultiBrushInfo info)
    : this()
{
    WithWeight(info.Weight);
    foreach (var actorInfo in info.Actors)
        WithActor(new ActorPlan(map, actorInfo.Type) { WPosLocation = WPos.Zero + actorInfo.Offset });
    if (info.BackingTile != null)
        WithBackingTile((TerrainTile)info.BackingTile);
    foreach (var templateInfo in info.Templates)
        WithTemplate(map, templateInfo.Type, templateInfo.Offset);
    foreach (var tileInfo in info.Tiles)
        WithTile(tileInfo.Type, tileInfo.Offset);
    ReplaceSegment(info.Segment);
}
```

This is the only bridge between the YAML-bound `MultiBrushInfo` and the runtime `MultiBrush`.

### 2. Composing a brush

A brush can be built incrementally:

- `WithTemplate` — expands a `TerrainTemplateInfo` into one or more tile entries. If `PickAny` is true, the brush stores a single tile with an index range `0..TilesCount-1`; otherwise it stores every non-null template cell at its local `(x, y)` offset.
- `WithTile` — adds a single explicit tile.
- `WithActor` — adds an `ActorPlan`.
- `WithBackingTile` — adds the same tile to every cell currently in the shape. Used to give actors a surface to stand on.
- `ReplaceSegment` — attaches a `MultiBrushSegment`.
- `WithWeight` — sets the selection weight; must be > 0.
- `MergeFrom` — copies tiles and actor plans from another brush at an offset, with an optional height offset.

### 3. Computing the footprint

The shape is the union of all tile offsets and all actor footprint cells:

```csharp
void UpdateShape()
{
    var xys = new HashSet<CVec>();
    foreach (var (xy, _) in tiles)
        xys.Add(xy);
    foreach (var actorPlan in actorPlans)
        foreach (var cpos in actorPlan.Footprint().Keys)
            xys.Add(new CVec(cpos.X, cpos.Y));
    if (xys.Count != 0)
        shape = xys.OrderBy(xy => (xy.Y, xy.X)).ToArray();
    else
        shape = [new CVec(0, 0)];
}
```

This is lazily cached and invalidated whenever tiles or actors are added. The ordering is `(Y, X)`, so `FirstCell` is the left-most cell in the top row.

### 4. Painting a single brush

`Paint` is the direct stamping method:

```csharp
public void Paint(Map map, List<ActorPlan> actorPlans, CPos paintAt,
    short? heightOffset, Replaceability contract, MersenneTwister random)
```

Steps:

1. Determine the final height offset. If `heightOffset` is `null`, the height is sampled from the first occupied cell on the target map; otherwise the supplied value is used.
2. Apply the contract:
   - `Replaceability.None` → throw.
   - `Any` → paint tiles and actors.
   - `Tile` → paint tiles (and also actors, because the tile replacement contract still permits the optional actor part).
   - `Actor` → paint only actors.
3. `PaintTiles` iterates `tiles`, converts each offset to an `MPos`, checks `map.Tiles.Contains`, and writes the picked tile and final height:
   ```csharp
   map.Tiles[mpos] = tile.Pick(random);
   map.Height[mpos] = (byte)Math.Clamp(tile.HeightOffset + heightOffset, byte.MinValue, byte.MaxValue);
   ```
4. `PaintActors` clones each stored `ActorPlan`, shifts it by `paintAt`, and adds it to the supplied `actorPlans` list.

### 5. Painting an area from a replaceability mask

`PaintArea` is the higher-level generator entry point. It consumes a `CellLayer<Replaceability>` mask and fills the marked cells with brushes from `availableBrushes`.

Algorithm:

1. Group brushes by `Area` (descending). Add a final 1×1 pass for any actor-only brush whose area is 1.
2. For each group, compute:
   - `brushTotalArea` and `brushTotalWeight` across all brushes.
   - `brushWeightForArea` and `remainingQuota`:
     - If the brush area is 1 or `alwaysPreferLargerBrushes` is true, the quota is `int.MaxValue`.
     - Otherwise, `remainingQuota = (replaceMposes.Count * brushWeightForArea + brushTotalWeight - 1) / brushTotalWeight`.
3. Refresh the list of remaining target cells and shuffle them.
4. For each candidate cell, pick a weighted random brush from the current group.
5. Compute `paintAt = mpos.ToCPos(map) - brush.FirstCell`.
6. Call `ReserveShape` to check whether the brush fits:
   - Skip cells not contained in the `replace` layer.
   - If any cell in the shape has already been consumed, reject.
   - Intersect the brush’s contract with each cell’s replaceability.
   - If the result is `None`, reject.
   - If accepted, mark every shape cell as consumed.
7. If accepted, call `brush.Paint` with the intersected contract.
8. Decrement `remainingQuota` by `brushArea` and continue until the quota is exhausted.

`ReserveShape` is the gatekeeper: it ensures a brush never overwrites the same cell twice and that the brush’s capabilities match the replaceability mask.

### 6. Editor/export path

`ToEditorBlitSource` converts the brush into an `EditorBlitSource`, allowing the editor to preview or stamp the brush as a single blit. It handles actor ownership defaults and randomizes tiles when a `MersenneTwister` is provided.

![Configuration (yaml) diagram](images/Part_07_Chapter_05_MultiBrush-annotated-yaml-snippet-diagram-showing-the-key-fields-and-ho-6a1b98.svg)

## Configuration (YAML)


`MultiBrush` definitions live inside the tileset YAML under a top-level `MultiBrushCollections` node. Each collection is a named list of brushes.

### Collection structure

```yaml
MultiBrushCollections:
    Segmented:
        MultiBrush@3:
            Template: 3
            Segment:
                Start: Beach.L
                End: Beach.L
                Points: 4,1, 4,2, 3,2, 2,2, 1,2, 1,3, 0,3
```

### Per-brush keys

| Key | C# target | Description |
| :---- | :---- | :---- |
| `Template` | `MultiBrushInfo.TemplateInfo` | A template ID. Optional `Offset: x,y` shifts the template origin. |
| `Tile` | `MultiBrushInfo.TileInfo` | An explicit tile string, e.g. `Tile: Clear,0`. Optional `Offset: x,y`. |
| `Actor` | `MultiBrushInfo.ActorInfo` | An actor type. Optional `Offset: x,y,z` (world-space). |
| `BackingTile` | `MultiBrushInfo.BackingTile` | A tile that is placed under every cell of the brush’s current footprint. |
| `Weight` | `MultiBrushInfo.Weight` | Selection weight; default 1000, must be > 0. |
| `Segment` | `MultiBrushInfo.Segment` | Head/tail chaining metadata. |

### Segment sub-keys

| Key | C# target | Description |
| :---- | :---- | :---- |
| `Start` | `MultiBrushSegment.Start` | Required. Type with direction, e.g. `Beach.L`. |
| `End` | `MultiBrushSegment.End` | Required. Type with direction, e.g. `Beach.L`. |
| `Inner` | `MultiBrushSegment.Inner` | Optional. Type without direction, e.g. `Beach`. If omitted, `Start`/`End` types are eligible as inner types. |
| `Points` | `MultiBrushSegment.Points` | Comma-separated `x,y` sequence of `-X-Y` corners of template tiles. Each step must be a single cardinal cell (Manhattan distance == 1). |

### Bulk generators

`MultiBrushInfo.ParseCollection` supports two shorthand entries for collections:

- `FromTemplates: 1, 2, 3` — creates one brush per template ID, sharing any other nodes on the same entry (e.g. `Weight` or `Segment`).
- `FromActors: vlk, vlk, 3tnk` — creates one brush per actor type.

These are convenient when many brushes share the same metadata.

### Example: actor-only brush

```yaml
MultiBrushCollections:
    Decorations:
        MultiBrush@Rocks:
            Actor: rock1
            Weight: 500
```

### Example: explicit tile with segment

```yaml
MultiBrush@45:
    Template: 45
    Segment:
        Start: Beach.L
        End: Beach.U
        Points: 3,1, 2,1, 1,1, 1,0, 2,0
```

## Interconnectivity

### Depends on

- **Tileset / `ITemplatedTerrainInfo`** — `MultiBrush` reads `Templates`, `TerrainInfo`, and `MultiBrushCollections` from the active tileset.
- **`ActorPlan`** — actors are stored and emitted as `ActorPlan` objects so the caller can finalize actor placement.
- **`Direction`/`DirectionMask`** — segment directions are parsed against the `Direction` enum (R, RD, D, LD, L, LU, U, RU).
- **`CellLayer<T>` / `Map.Tiles` / `Map.Height`** — the final output is written to the map’s height and tile layers.
- **`EditorBlitSource`** — the editor export path reuses the same data as an editor-stampable object.

### Used by

- **`TilingPathTool`** — loads every `Segment` brush from every `MultiBrushCollection` and chains them along editor-drawn paths.
- **Map generators** — call `MultiBrush.PaintArea` to fill `CellLayer<Replaceability>` masks with terrain/actor variations.
- **`CheckMultiBrushes`** — lint pass validates every `MultiBrushInfo` by instantiating it against a 1×1 map.

![Algorithms diagram](images/Part_07_Chapter_05_MultiBrush-algorithm-diagram-or-pseudocode-flowchart-for-the-non-trivia-5983ed.svg)

## Algorithms


### Weighted random selection

Both `MultiBrush.PickAny` and `PaintArea` use `MersenneTwister.PickWeighted(int[])`:

```
weights = [b1.Weight, b2.Weight, ...]
index = random.PickWeighted(weights)
return brushes[index]
```

The default weight is 1000. A weight of 0 or negative is rejected by `WithWeight`.

### Shape reservation

`ReserveShape` is the collision/contract check:

```
contract = brush.Contract()    // None / Tile / Actor / Any
for each cvec in brush.Shape:
    cpos = paintAt + cvec
    if replace not contains cpos: continue
    if remaining[cpos] == false: return None
    contract &= replace[cpos]
    if contract == None: return None

for each cvec in brush.Shape:
    cpos = paintAt + cvec
    if replace contains cpos:
        remaining[cpos] = false

return contract
```

A cell can be revisited only if the layer does not contain it (e.g., outside the map). Cells inside the map are consumed immediately on success.

### Area-filling quota

`PaintArea` tries to spend roughly the same proportion of the replaceable area on each brush-area group:

```
quota = (replaceableCellCount * groupWeight + totalWeight - 1) / totalWeight
```

The integer ceiling ensures that, on average, a group’s weight is reflected in the number of brush placements. One-cell brushes and `alwaysPreferLargerBrushes` bypass the quota entirely, giving them a final pass over the leftovers.

### Segment type matching

`MultiBrushSegment.MatchesType` is permissive:

```
MatchesType(type, matcher):
    if type == matcher: return true
    return type.StartsWith(matcher + ".")
```

This allows a matcher like `Beach` to match `Beach.L`, `Beach.RD`, etc. `HasInnerType` uses the explicit `Inner` if present, otherwise falls back to the start and end types.

![Extension points diagram](images/Part_07_Chapter_05_MultiBrush-extension-hook-diagram-showing-the-interface-s-to-implement-b4a27b.svg)

## Extension Points


The primary extension mechanism is **YAML-defined brushes** inside the tileset. Modders can add new `MultiBrush` entries, new collections, or new `FromTemplates`/`FromActors` generators without touching C#.

For code-level extension, the class is `sealed`, so the extension points are composition and the public static helpers:

- `MultiBrush.LoadCollection(map, name)` — load a named tileset collection.
- `MultiBrush.PaintArea(...)` — fill a `CellLayer<Replaceability>` mask.
- `MultiBrush.PickAny(brushes, random)` — weighted selection from a pre-filtered list.
- `MultiBrush.MergeFrom(other, at, mapGridType, heightOffset)` — compose larger brushes from smaller ones.
- `MultiBrush.ToEditorBlitSource(...)` — turn a brush into an editor preview/stamp.
- `MultiBrush.MaxHeightOfBrushes` / `MaxHeightOfSegmentType` — utility queries for terrain-aware generation.

Because `MultiBrush` exposes `Shape`, `Area`, `FirstCell`, `GetHeightsAndRamps()`, and `PossibleTiles()`, custom map generators can inspect a brush before deciding where to place it.

![Common pitfalls  guardrails diagram](images/Part_07_Chapter_05_MultiBrush-checklist-infographic-style-diagram-summarizing-the-top-pitf-fb069e.svg)

## Common Pitfalls / Guardrails


- **Weight must be positive.** `WithWeight` throws `ArgumentException` if `weight <= 0`.
- **Segment points must be cardinal unit steps.** Diagonal steps fail validation with `non-unit steps`.
- **Segment points must be even-length.** An odd number of coordinates triggers `InvalidValueAction`.
- **Only one `Segment` per brush.** The parser throws on duplicate `Segment` keys.
- **`Inner` has no direction suffix; `Start`/`End` must have one.** `TypeDirection` expects the last dot-separated token to parse as a `Direction` enum value.
- **Unknown `MultiBrush` collection keys are rejected.** Only `MultiBrush`, `FromTemplates`, and `FromActors` are valid.
- **Template IDs must exist.** `WithTemplate(ITemplatedTerrainInfo, ...)` throws `ArgumentException` if the template is missing.
- **PickAny templates are treated as one randomized tile.** The brush stores a single cell with an index range `0..TilesCount-1` rather than expanding every tile index.
- **`WithBackingTile` requires a non-zero shape.** If the brush has no tiles or actors, it only has the default `(0,0)` cell and the backing tile is placed there.
- **`PaintArea` decrements quota even if a placement fails.** If a brush’s shape cannot fit at a candidate cell, the loop still subtracts its area from `remainingQuota`. This prevents infinite looping but means the final fill may be slightly under the statistical target when space is tight.
- **`PaintArea` processes larger-area brushes first.** Small brushes (area > 1) are deferred to later groups; a 1×1 actor-only brush is always given a final pass.
- **`FirstCell` is not the bounding-box top-left.** It is the top-left-most occupied cell according to the shape’s `(Y, X)` ordering.
- **`Replaceability.Tile` still permits actors.** The `Tile` flag means “tile must be replaced, actor may be added.” If a tile+actor brush is placed on a tile-only cell, the tile *and* the actor are placed.
- **Actor offsets are world-space (`WVec`), tile offsets are cell-space (`CVec`).** Mixing them up will misalign actors relative to the terrain.
- **Out-of-bounds shape cells are ignored during reservation but not counted as failures.** If a brush’s footprint extends past the replaceability layer, it may still be placed if the in-bounds portion is available. The actual tile write is then guarded by `map.Tiles.Contains` in `PaintTiles`.
- **The replaceability layer is consumed immediately.** Once a cell is reserved by a brush, no subsequent brush can use it, regardless of whether the later brush is smaller or larger.

## What to read next

- [Part 7.4 — Terraformer](Part_07_Chapter_04_Terraformer.md) for the orchestrator that uses `MultiBrush` to paint terrain.
- [Part 7.6 — Mod-Specific Generators](Part_07_Chapter_06_Mod_Generators.md) to see how mod generators load and apply brush collections.
- [Part 7.8 — Random Map Generator Extension Points](Part_07_Chapter_08_Extension_Points.md) for adding custom brush definitions to a tileset.

## Summary

This chapter explains how `[MultiBrush](../appendices/Appendix_A_Glossary.md)` places terrain templates and actors during procedural map generation.

After reading this chapter, you should be able to:

- **YAML Data Layer — `MultiBrushInfo`**

If any of the concepts above feel unclear, review the relevant section before continuing. For source files and further reading, see the References section.


## References

- Source: `OpenRA.Mods.Common/MapGenerator/MultiBrush.cs`
- Source: `OpenRA.Mods.Common/MapGenerator/Direction.cs`
- Source: `OpenRA.Mods.Common/Terrain/DefaultTerrain.cs`
- Source: `OpenRA.Mods.Common/Traits/World/TilingPathTool.cs`
- Source: `OpenRA.Mods.Common/Lint/CheckMultiBrushes.cs`
- Tileset examples: `mods/ra/tilesets/temperat.yaml`, `mods/cnc/tilesets/temperat.yaml`, `mods/ts/tilesets/temperate.yaml`, `mods/d2k/tilesets/arrakis.yaml`
- Related manual chapters (to be linked): Tileset & Terrain System, Map Generator, Editor Tools, `ActorPlan`.