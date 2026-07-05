# Chapter 7.2 — Map Generation Data Structures

## Purpose

This chapter explains the core data structures that OpenRA uses to store, index, and transform a map. Map generation code in `OpenRA.Mods.Common.MapGenerator` works mostly with generic, CPos-aligned 2D arrays (`Matrix<T>`), while the runtime engine stores the final map in grid-aware layers (`CellLayer<T>`). The bridge between these two representations, the shape and coordinate rules that govern them, and the top-level `Map` container that holds tile, resource, height, ramp, and actor data are all covered here.

The goal is to give readers a precise mental model of:

- How `[CellLayer<T>](../appendices/Appendix_A_Glossary.md)` stores one scalar value per map cell.
- How `Matrix<T>` provides a grid-agnostic workbench for generator algorithms.
- How `[MapGrid](../appendices/Appendix_A_Glossary.md)` defines the geometry of the world (rectangular vs. isometric, sub-cells, ramps, tile search).
- How `Map` assembles all of these layers into one serializable object.
- How `[CPos](../appendices/Appendix_A_Glossary.md)`, `[MPos](../appendices/Appendix_A_Glossary.md)`, `PPos`, and `[WPos](../appendices/Appendix_A_Glossary.md)` relate to each other and how to convert between them safely.

## Learning Objectives


After studying this chapter, you should be able to:

- Explain the difference between CellLayer<T> and Matrix<T> and when to use each.
- Convert between CPos, MPos, PPos, and WPos using MapGrid rules.
- Describe how MapGrid defines grid geometry, sub-cells, ramps, and tile search.
- Use CellLayerUtils to bridge generator Matrix results into engine CellLayer layers.
- Explain how Map assembles tile, resource, height, ramp, and actor layers.
- Identify coordinate system edge cases on RectangularIsometric grids.

## Files

| File | Role |
|------|------|
| `OpenRA.Game/Map/CellLayerBase.cs` | Abstract base for a flat array of values whose dimensions match a `MapGrid`. |
| `OpenRA.Game/Map/CellLayer.cs` | Generic `CellLayer<T>` with `CPos`/`MPos` indexers and a `CellEntryChanged` event. |
| `OpenRA.Mods.Common/MapGenerator/Matrix.cs` | Generic 2D array indexed by `int2` (or `x,y`) used by map-generator algorithms. |
| `OpenRA.Mods.Common/MapGenerator/CellLayerUtils.cs` | Bridge helpers that copy data between `CellLayer<T>` and `Matrix<T>`. |
| `OpenRA.Game/Map/MapGrid.cs` | Mod-level definition of the grid type, sub-cells, ramps, and `TilesByDistance`. |
| `OpenRA.Game/Map/Map.cs` | Top-level map container: tile/resource/height/ramp layers, bounds, projection, actors. |
| `OpenRA.Game/CPos.cs` | Packed cell coordinate (X, Y, Layer). |
| `OpenRA.Game/MPos.cs` | Raw map coordinate (U, V) plus the `PPos` projected coordinate struct. |
| `OpenRA.Game/WPos.cs` | World-space 3D position (X, Y, Z). |
| `OpenRA.Game/CVec.cs` | 2D cell-space offset vector. |

![Architecture diagram](images/Part_07_Chapter_02_Data_Structures-architecture-diagram-showing-the-main-classes-interfaces-and-9161e6.svg)

## Architecture


### 1. The Layer Abstraction: `CellLayerBase<T>` and `CellLayer<T>`

A `CellLayer<T>` is a dense, one-dimensional array of `T` values that is sized to the map and tagged with the grid type (`Rectangular` or `RectangularIsometric`). The base class handles the raw memory, while the sealed subclass adds coordinate-aware indexers and change notification.

#### `CellLayerBase<T>` (CellLayerBase.cs)

- `Size` — the layer dimensions in raw map cells (`OpenRA.Primitives.Size`).
- `GridType` — either `Rectangular` or `RectangularIsometric`.
- `Entries` — a protected `T[]` of length `Size.Width * Size.Height`.
- `Bounds` — a `Rectangle(0, 0, Size.Width, Size.Height)` used for bounds checks.
- `CopyValuesFrom(CellLayerBase<T>)` — validates that both layers have the same `Size` and `GridType`, then copies the backing span.
- `Clear()` and `Clear(T value)` — fill the backing span with `default(T)` or a specific value.
- `IEnumerable<T>` enumerates `Entries` directly in row-major order.
- `AsReadOnlyMemory()` / `AsMemory()` expose the underlying array for efficient bulk operations.

#### `CellLayer<T>` (CellLayer.cs)

`CellLayer<T>` is the concrete layer that the rest of the engine uses. Its public surface is built around two coordinate systems:

- `this[CPos cell]` — converts the cell coordinate to an `MPos` and reads/writes the entry.
- `this[MPos uv]` — reads/writes the raw array entry directly.

The indexer setter always invokes the `CellEntryChanged` event:

```csharp
public event Action<CPos> CellEntryChanged = null;
```

For `this[CPos]`, the event is raised with the same `CPos`. For `this[MPos]`, the event is raised with `uv.ToCPos(GridType)`.

Important guards:

- `CopyValuesFrom`, `Clear()`, and `Clear(T)` throw `InvalidOperationException` if any listener is attached to `CellEntryChanged`. This prevents silent loss of notifications.
- `Contains(CPos)` and `TryGetValue(CPos, out T)` explicitly reject the case `X < Y` on `RectangularIsometric` grids because `ToMPos()` is symmetric in `X` and `Y` for that grid type.
- `Clamp` clamps an `MPos` to the layer bounds and converts back to the caller’s coordinate type.
- `CellRegion` returns a `CellRegion` spanning the entire layer.

A static helper class `CellLayer` provides:

```csharp
public static CellLayer<T> Resize<T>(CellLayer<T> layer, Size newSize, T defaultValue)
```

This creates a new layer of the same grid type and copies the overlapping top-left region; new cells are filled with `defaultValue`.

### 2. The Generator Workbench: `Matrix<T>`

`Matrix<T>` is a fixed-size 2D array designed for the map-generator pipeline. It does **not** know about `MapGridType` or `CPos` semantics; it stores values in a flat `T[] Data` and indexes them by `int2` or `x,y`.

Key members (Matrix.cs):

- `Data` — public read-only backing array.
- `Size` — dimensions as an `int2`.
- `Index(int2 xy)` / `Index(int x, int y)` — bounds-checked linear index.
- `XY(int index)` — reverse of `Index`.
- `this[int x, int y]` / `this[int2 xy]` / `this[int i]` — indexers.
- `ContainsXY(int2 xy)` / `ContainsXY(int x, int y)` — bounds check.
- `IsEdge(int x, int y)` — true if the coordinate is on the matrix border.
- `ClampXY(int x, int y)` — clamp to the matrix bounds.
- `Transpose()` — returns a new transposed matrix by shallow copying values.
- `Map<R>(Func<T, R>)` — returns a new matrix with transformed values.
- `Fill(T)` — fills the matrix and returns `this` for chaining.
- `Clone()` — returns a shallow copy.
- `Zip<T1, T2, T>(...)` — combines two same-size matrices with a function.
- `CopyTo(Matrix<T>)` — copies `Data` to another matrix of identical size.
- `Enumerate()` — yields `(int2 Xy, T Value)` for every cell.

The matrix is deliberately simple: no events, no grid conversions, no `Layer` field. It is the “scratch pad” for noise, distance transforms, morphological kernels, and other raster algorithms.

### 3. Bridging `Matrix<T>` and `CellLayer<T>`

The conversion between the two is handled by `OpenRA.Mods.Common.MapGenerator.CellLayerUtils`. These helpers are not in the requested file list but are essential for the “conversion to `CellLayer`” topic, so they are documented here.

#### `CellLayerUtils.ToMatrix<T>(CellLayer<T> cellLayer, T defaultValue)`

- Computes the smallest `CPos`-aligned rectangle that contains all cells for the layer’s grid type (`CellBounds`).
- Allocates a `Matrix<T>` of that size and fills it with `defaultValue`.
- Iterates over the layer’s `CellRegion` (which enumerates valid `CPos` cells) and copies each value into the matrix at `matrix[cpos.X - cellBounds.Left, cpos.Y - cellBounds.Top]`.

For `RectangularIsometric` grids, this means the matrix may contain “holes” for `CPos` positions that do not correspond to real cells; those holes stay at `defaultValue`.

#### `CellLayerUtils.FromMatrix<T>(CellLayer<T> cellLayer, Matrix<T> matrix, bool allowOversizedMatrix = false)`

- Computes the destination `CellBounds`.
- If `allowOversizedMatrix` is false, the matrix must exactly match the bounds size; otherwise, the matrix must be at least as large.
- Iterates over the layer’s `CellRegion` and writes `matrix[cpos.X - cellBounds.Left, cpos.Y - cellBounds.Top]` into the layer.

This is the standard way generator algorithms push their results back into a `CellLayer`.

#### Additional coordinate helpers in `CellLayerUtils`

- `Center<T>(CellLayer<T>)` / `Center(Map)` — world center of the layer.
- `Radius<T>(CellLayer<T>)` / `Radius(Map)` — maximum inscribed circle radius.
- `CornerToWPos(CPos, MapGridType)` / `WPosToCorner(WPos, MapGridType)` — map corner conversions.
- `CPosToWPos(CPos, MapGridType)` / `WPosToCPos(WPos, MapGridType)` — full cell center conversions.
- `MPosToWPos(MPos, MapGridType)` / `WPosToMPos(WPos, MapGridType)` — via `CPos`.
- `CVecToWVec(CVec, MapGridType)` — cell vector to world vector.
- `ToMatrixPoints` / `FromMatrixPoints` — convert arrays of `CPos` to zero-based `int2` coordinates relative to `CellBounds`.

### 4. `MapGrid` — The Geometry Contract

`MapGrid` is an `IGlobalModData` class loaded from the `MapGrid` section of `mod.yaml`. It defines everything the engine needs to know about the shape of one cell.

#### Grid types (MapGrid.cs)

```csharp
public enum MapGridType { Rectangular, RectangularIsometric }
```

- `Rectangular` — classic square cells. One cell step is `1024` world units.
- `RectangularIsometric` — diamond-shaped cells used by Tiberian Sun/Red Alert 2 style tilesets. One cell step along the diagonal world axes is `1448` units; the tile scale is `1448`.

#### Grid properties

- `Type` — grid type.
- `MaximumTerrainHeight` — max map height value (0 disables the height system).
- `MaximumTileSearchRange` — radius used to build `TilesByDistance`.
- `TileScale` — `1024` for rectangular, `1448` for isometric.
- `EnableDepthBuffer` — used by the renderer to handle per-cell depth offsets.
- `SubCellOffsets` — immutable array of world offsets for each sub-cell slot.
- `DefaultSubCell` — default sub-cell index; if omitted, defaults to the middle entry of `SubCellOffsets`.
- `Ramps` — immutable array of `CellRamp` definitions.
- `TilesByDistance` — precomputed `ImmutableArray<ImmutableArray<CVec>>` used by range queries.

#### Sub-cells

The default `SubCellOffsets` array has six entries:

```csharp
new(0, 0, 0),       // full cell - index 0
new(-299, -256, 0), // top left  - index 1
new(256, -256, 0),  // top right - index 2
new(0, 0, 0),       // center    - index 3
new(-299, 256, 0),  // bottom left - index 4
new(256, 256, 0),   // bottom right - index 5
```

`OffsetOfSubCell(SubCell)` returns `WVec.Zero` for `SubCell.Invalid` or `SubCell.Any`, otherwise returns the corresponding offset.

#### Ramps

A `CellRamp` is a struct that defines the 3D shape of one sloped tile.

- `CenterHeightOffset` — precomputed height at the center of the cell.
- `Corners` — four `WVec` corner offsets.
- `Polygons` — one polygon for flat ramps, two triangles for split ramps.
- `Orientation` — a `WRot` describing the ramp’s normal orientation.

The constructor takes the four corner heights (`Low`, `Half`, or `Full`) and a `RampSplit`:

- `RampSplit.Flat` — one quad.
- `RampSplit.X` — split along the X diagonal (`[0,1,3]` and `[1,2,3]`).
- `RampSplit.Y` — split along the Y diagonal (`[0,1,2]` and `[0,2,3]`).

`HeightOffset(int dX, int dY)` locates the triangle containing the point, then uses barycentric interpolation to compute the Z offset at that local position.

`MapGrid` constructs a hardcoded list of 20 ramps (MapGrid.cs) that follow the Tiberian Sun / Red Alert 2 slope conventions. The first ramp is flat, the rest are half-height and full-height combinations with specific orientations.

#### `TilesByDistance`

`CreateTilesByDistance()` builds an array of `CVec` groups indexed by integer distance:

1. For every `i,j` in `[-MaximumTileSearchRange, MaximumTileSearchRange]`, if `i² + j² ≤ MaximumTileSearchRange²`, add the `CVec(i,j)` to bucket `ceil(sqrt(i² + j²))`.
2. Sort each bucket by `LengthSquared`, then hash code, then X, then Y. The hash tie-breaker is intentional: it gives a stable but non-axis-aligned order for equal-distance tiles.

This table is used by `Map.FindTilesInAnnulus` and `Map.FindTilesInCircle`.

### 5. `Map` — The Final Container

`Map` is the object that joins the layers, the grid, the metadata, the rules, and the actor definitions.

#### Metadata and definitions

- `MapFormat` / `SupportedMapFormat` / `CurrentMapFormat` — map format versioning.
- `RequiresMod`, `Title`, `Author`, `Tileset`, `Categories`, `Visibility`.
- `MapSize` — dimensions of the backing layers.
- `Bounds` — playable area rectangle.
- `PlayerDefinitions` — `MiniYamlNode` collection for player slots.
- `ActorDefinitions` — `MiniYamlNode` collection for actor placements.
- `RuleDefinitions`, `SequenceDefinitions`, `WeaponDefinitions`, etc. — optional custom YAML.

#### Core layers

- `Tiles` — `CellLayer<TerrainTile>`; stores the tile type and tile index for each cell.
- `Resources` — `CellLayer<ResourceTile>`; stores resource type and density.
- `Height` — `CellLayer<byte>`; stores the terrain height value.
- `Ramp` — `CellLayer<byte>`; stores the ramp index, derived from the tile type.
- `CustomTerrain` — `CellLayer<byte>`; runtime override of the terrain type index.

All layers are created with the same `Grid.Type` and `MapSize` (Map.cs).

#### Projection state

When `MaximumTerrainHeight > 0`, the map builds a 3D-to-2D projection used for shroud, targeting, and rendering:

- `CellLayer<PPos[]> cellProjection` — for each `MPos`, the list of projected screen positions it covers.
- `CellLayer<List<MPos>> inverseCellProjection` — for each `PPos`, the list of `MPos` cells that project onto it.
- `CellLayer<byte> projectedHeight` — the visible height at each projected position.
- `PPos[] ProjectedCells` — cached array of all valid projected cells inside the bounds.
- `event Action<CPos> CellProjectionChanged` — raised when a cell’s projection changes.

The projection is lazily initialized in `InitializeCellProjection()` and updated on `Tiles.CellEntryChanged` and `Height.CellEntryChanged`.

#### Other useful state

- `AllCells` — a `CellRegion` covering the entire map.
- `AllEdgeCells` — list of `CPos` cells on the edge of the playable area.
- `ReplacedInvalidTerrainTiles` — dictionary of tiles that were invalid for the current tileset and were replaced on load.
- `ProjectedTopLeft` / `ProjectedBottomRight` — legacy world bounds of the playable area.

#### Events tied to the layers

During construction, `Map` subscribes to the layer events:

```csharp
if (Grid.MaximumTerrainHeight > 0)
{
    Tiles.CellEntryChanged += UpdateRamp;
    Tiles.CellEntryChanged += UpdateProjection;
    Height.CellEntryChanged += UpdateProjection;
}

CustomTerrain.CellEntryChanged += InvalidateTerrainIndex;
Tiles.CellEntryChanged += InvalidateTerrainIndex;
```

- `UpdateRamp` recomputes `Ramp[cell]` from the terrain info.
- `UpdateProjection` recomputes the cell’s projection and raises `CellProjectionChanged`.
- `InvalidateTerrainIndex` clears the cached terrain index for the cell.

### 6. Coordinate Systems

OpenRA uses four coordinate types and two vector types for cells. Understanding them is the biggest source of bugs in map code.

#### `CPos` — Cell Position

- Stored as a packed 32-bit integer: `XXXX XXXX XXXX YYYY YYYY YYYY LLLL LLLL`.
- `X` and `Y` are 12-bit signed values; `Layer` is an unsigned byte.
- `CPos` is the coordinate system actors and the user interface usually speak.
- For rectangular maps, `X` and `Y` are the raw map coordinates.
- For isometric maps, `X` and `Y` form a staggered cell grid; many valid combinations do not exist as real cells.
- Conversions:
  - `CPos.ToMPos(Map)` / `CPos.ToMPos(MapGridType)` — returns the raw map coordinate.
  - For rectangular: `new MPos(X, Y)`.
  - For isometric: `v = X + Y`, `u = (v - (v & 1)) / 2 - Y`.
- Explicit cast from `int2` to `CPos`.
- Supports `+`/`-` with `CVec`.

#### `MPos` — Map Position

- Raw 2D coordinate `(U, V)` that directly maps to the backing array.
- For rectangular maps, `U == X` and `V == Y`.
- For isometric maps, `U` and `V` are the non-staggered row/column coordinates.
- Conversions:
  - `MPos.ToCPos(Map)` / `MPos.ToCPos(MapGridType)`.
  - For rectangular: `new CPos(U, V)`.
  - For isometric: `y = (V - (V & 1)) / 2 - U`, `x = V - y`.
- `MPos.Clamp(Rectangle)` clamps `U` and `V`.

#### `PPos` — Projected Position

- Defined in the same file as `MPos` (MPos.cs).
- A 2D coordinate `(U, V)` used for the screen-space projection of an isometric map.
- Explicit casts connect it to `MPos`:
  - `(MPos)puv` → `new MPos(puv.U, puv.V)`.
  - `(PPos)uv` → `new PPos(uv.U, uv.V)`.
- `PPos` is **not** the same as `MPos`; using it properly requires the projection tables in `Map`.

#### `WPos` — World Position

- 3D position in world units: `X`, `Y`, `Z`.
- `Z` is height in the same units as `X` and `Y`.
- One rectangular cell is `1024` units wide.
- One isometric cell is `1448` units along the world diagonal axes.
- `WPos` = `WPos + WVec`; `WPos - WPos` = `WVec`.
- `WPos` is used by physics, movement, targeting, and rendering.

#### `CVec` — Cell Vector

- 2D integer offset `(X, Y)` in cell space.
- Supports arithmetic, scaling, dot product, length, clamping, and the eight `Directions`.
- `CPos + CVec` → `CPos`.
- `CPos - CPos` → `CVec`.

#### `WVec` — World Vector

- 3D integer vector in world units.
- Used for movement deltas, sub-cell offsets, and ramp normals.
- `WPos` operators are defined in `WPos.cs`.

![Data flow  code path diagram](images/Part_07_Chapter_02_Data_Structures-sequence-flow-diagram-tracing-the-execution-path-from-trigge-035864.svg)

## Data Flow / Code Path


### Loading a map

1. `Map` constructor reads `map.yaml`.
2. It reads `MapSize` and creates the four layers (`Tiles`, `Resources`, `Height`, `Ramp`) using `Grid.Type` and `MapSize`.
3. It reads `map.bin` and writes `Tiles`, `Resources`, and `Height` by `MPos`.
4. `PostInit()`:
   - Loads the `Ruleset` and `SequenceSet`.
   - Builds `AllCells` from the map corners.
   - Calls `SetBounds` to compute the playable rectangle and the projection.
   - Creates `CustomTerrain` and fills it with `byte.MaxValue`.
   - Replaces invalid tiles with the default tile and records them in `ReplacedInvalidTerrainTiles`.
   - Fills `Ramp` from the terrain info.
   - Computes `AllEdgeCells`.
   - Attaches layer event handlers.
5. If the map has height, `InitializeCellProjection()` is triggered lazily on the first projection query.

### Map generation pipeline

1. A generator creates one or more `CellLayer<T>` objects, usually from `Map.Tiles` or `Map.Height`.
2. `CellLayerUtils.ToMatrix(layer, defaultValue)` converts the layer into a `Matrix<T>` that the generator can process.
3. Algorithms (noise, blur, distance transforms, boolean morphology) operate on `Matrix<T>`.
4. `CellLayerUtils.FromMatrix(layer, matrix)` writes the result back.
5. Because the layer setter fires `CellEntryChanged`, any dependent state (`Ramp`, projection, terrain-index cache) is automatically refreshed.

### Runtime query path

1. An actor or widget asks `Map` for a world position or a cell.
2. `Map` uses `Grid.Type` to choose the correct conversion formula.
3. For height-aware maps, the query may be routed through the projection tables (`ProjectedCellsCovering`, `Unproject`, `ProjectedHeight`).
4. The final `MPos` or `CPos` is used to read `CellLayer<T>` entries.

![Configuration (yaml) diagram](images/Part_07_Chapter_02_Data_Structures-annotated-yaml-snippet-diagram-showing-the-key-fields-and-ho-6a1b98.svg)

## Configuration (YAML)


### `MapGrid` in `mod.yaml`

`MapGrid` is an `IGlobalModData` block. The most relevant fields are:

```yaml
MapGrid:
    Type: Rectangular
    MaximumTerrainHeight: 0
    SubCellOffsets: 0,0,0, -299,-256,0, 256,-256,0, 0,0,0, -299,256,0, 256,256,0
    DefaultSubCell: 3
    MaximumTileSearchRange: 50
    EnableDepthBuffer: false
```

- `Type` — `Rectangular` or `RectangularIsometric`.
- `MaximumTerrainHeight` — max value for the `Height` layer; `0` disables ramps and projection.
- `SubCellOffsets` — world offsets for each sub-cell slot. Index 0 is the full cell; the remaining entries are per-unit offsets.
- `DefaultSubCell` — index of the default sub-cell when an actor is spawned without a specific sub-cell. If omitted, it defaults to the middle of the array.
- `MaximumTileSearchRange` — radius for `TilesByDistance`.
- `EnableDepthBuffer` — renderer hint.

### `map.yaml`

The map file declares the top-level metadata and points to the binary data:

```yaml
MapFormat: 12
RequiresMod: ra
Title: Example
Author: Author
Tileset: TEMPERAT
MapSize: 128,128
Bounds: 1,1,126,126
Visibility: Lobby
Categories: Conquest
Actors:
    Actor0: ...
```

`MapSize` is the raw backing size of all `CellLayer` instances. `Bounds` defines the playable rectangle. `Actors` is the `ActorDefinitions` collection that `Map` stores as `MiniYamlNode` objects.

### `map.bin`

The binary companion stores the per-cell data:

- `TileFormat` byte.
- Width and height.
- Offsets for tiles, heights, and resources.
- Tile data as `ushort type` + `byte index`.
- Height data as `byte` (only if `MaximumTerrainHeight > 0`).
- Resource data as `byte type` + `byte density`.

The offsets are written by `SaveBinaryData()` in Map.cs.

## Interconnectivity

![Interconnectivity](images/Part_07_Chapter_02_Data_Structures-Interconnectivity.svg)
`Map` is the root: it owns the grid, the layers, and the projection. `CellLayer<T>` is the storage primitive. `Matrix<T>` is the algorithmic primitive. `CellLayerUtils` is the adapter. `MapGrid` is the geometric contract that every coordinate conversion and layer indexing follows.

![Algorithms diagram](images/Part_07_Chapter_02_Data_Structures-algorithm-diagram-or-pseudocode-flowchart-for-the-non-trivia-5983ed.svg)

## Algorithms


### CellLayer Index Calculation

`CellLayer<T>.Index(CPos)` inlines `CPos.ToMPos` for performance:

- Rectangular:
  - `index = Y * Size.Width + X`
- RectangularIsometric:
  - `u = (x - y) / 2`
  - `v = x + y`
  - `index = v * Size.Width + u`

`Index(MPos)` simply checks `Bounds.Contains(u, v)` and returns `v * Size.Width + u`. These two indexers are the reason coordinate conversion is hot in the engine.

### `CPos` ↔ `MPos` for Isometric Maps

Forward (`CPos` → `MPos`):

```
v = X + Y
u = (v - (v & 1)) / 2 - Y
```

Reverse (`MPos` → `CPos`):

```
y = (V - (V & 1)) / 2 - U
x = V - y
```

These formulas account for the staggered rows of isometric cells.

### `Map` Projection

When a cell has height, it may project onto several screen-space tiles.

- `ProjectCellInner(MPos uv)`:
  - If height is 0, returns `(PPos)uv`.
  - If height is odd and the cell has a non-zero ramp, height is rounded up to the next even value.
  - Odd heights project to four candidate `PPos` cells.
  - Even heights project to one `PPos` cell.
  - Candidates are filtered to those that are in bounds.

- `ProjectedCellHeightInner(PPos puv)`:
  - Walks the inverse projection downward until it finds an `MPos` that projects onto the `PPos`.
  - Returns `Height[uv] - TerrainHeight[uv]`, because the top of a cliff is treated like the bottom of the cliff in the original games.

- `UpdateProjection(CPos cell)`:
  - Removes the old reverse mapping.
  - Computes the new projection.
  - Adds the new reverse mapping.
  - Propagates the height up cliff faces.
  - Raises `CellProjectionChanged`.

### `MapGrid.Ramps`

`CellRamp` constructs four corners based on the grid type and the four corner heights:

- RectangularIsometric corners are at `±724` on the world axes.
- Rectangular corners are at `±512`.

For split ramps, the quad is divided into two triangles. `HeightOffset` uses a barycentric test: for each triangle with vertices `p0, p1, p2`, it solves for `u` and `v` such that the point is inside the triangle, then computes the interpolated Z as:

```
(u * p0.Z + v * p1.Z + (1024 - u - v) * p2.Z) / 1024
```

This is how `Map.CenterOfSubCell` and `Map.DistanceAboveTerrain` produce ramp-aware world positions.

### `TilesByDistance`

This is a rasterized circle table. For each `(i, j)` in range, it computes the ceiling of the Euclidean distance and places the offset in that bucket. Sorting is stable by design, using hash codes as a tie-breaker so that equal-distance tiles are not biased toward the top-left.

### `Matrix<T>` Algorithms

`Matrix<T>` itself only provides primitives. The heavy algorithms live in `MatrixUtils` (boolean blur, Chebyshev distance, walking distance, dilation/erosion, direction maps, chirality, etc.). They consume `Matrix<T>` and produce `Matrix<T>` or arrays of points. The generator then converts those back to `CellLayer<T>` via `CellLayerUtils.FromMatrix`.

### `CellLayerUtils` Bulk Operations

- `Entries<T>` — flattens a layer into a linear array in row-major order.
- `CalibrateQuantileInPlace` — shifts all values so that a given quantile hits a target.
- `CalibratedBooleanThreshold` — converts a numeric layer into a boolean layer with a calibrated fraction of true cells.
- `FloodFill` — generic breadth-first propagation with a user-defined filler function.
- `SimpleFloodFill` — boolean masked fill.
- `Intersect` / `Union` / `Subtract` — boolean set operations across layers.
- `Aggregate` — generic per-cell fold across multiple layers.
- `Clone` — shallow copy of a layer.
- `Map` — per-cell transform into a new layer.
- `Create` — initialize a layer from a function over `MPos` or `CPos`.

![Extension points diagram](images/Part_07_Chapter_02_Data_Structures-extension-hook-diagram-showing-the-interface-s-to-implement-b4a27b.svg)

## Extension Points


### Custom `CellLayer<T>`

Because `CellLayer<T>` is generic, mods and tools can create new layers for any cell-attached data. Examples include occupancy masks, influence maps, or pathfinding cost layers. The only requirement is that the layer is created with the same `MapGridType` and `Size` as the map.

### Custom terrain via `CustomTerrain`

`Map.CustomTerrain` lets gameplay code override the terrain type index of a cell at runtime. The cached terrain index in `Map` is invalidated automatically via `CellEntryChanged`, so new queries reflect the override.

### Sub-cell configuration

Mods can customize `SubCellOffsets` and `DefaultSubCell` in `MapGrid` to change how many units can occupy a cell and where they stand. The default array supports up to five sub-cells plus the full-cell slot.

### Map generator algorithms

New generators can freely use `Matrix<T>` with `CellLayerUtils.ToMatrix`/`FromMatrix` to implement custom raster operations. The `Matrix<T>` API is generic, so any value type can be used.

### `IMapPreviewSignatureInfo`

Mods can implement `IMapPreviewSignatureInfo` to influence how actors and terrain features are drawn in the map preview and minimap. The `Map.SavePreview` method queries these traits.

### Grid type extension

Adding a new `MapGridType` is not a simple YAML change. The entire engine assumes one of the two existing grid types in the conversion functions inside `CPos`, `MPos`, `Map`, `CellLayerUtils`, and the renderer. A new grid type would require coordinated changes in all of those locations.

![Common pitfalls  guardrails diagram](images/Part_07_Chapter_02_Data_Structures-checklist-infographic-style-diagram-summarizing-the-top-pitf-fb069e.svg)

## Common Pitfalls / Guardrails


### `CellLayer<T>` with listeners

Never call `Clear()` or `CopyValuesFrom()` on a `CellLayer<T>` that still has `CellEntryChanged` subscribers. `CellLayer<T>` explicitly throws `InvalidOperationException` in that case (CellLayer.cs). Detach listeners first, or operate on the layer one cell at a time so each change is notified.

### RectangularIsometric `X < Y` cells

For isometric grids, many `CPos` coordinates are invalid. `CellLayer.Contains(CPos)` and `CellLayer.TryGetValue(CPos, out T)` reject `X < Y` before calling `ToMPos()` (CellLayer.cs). If you bypass these helpers and index by a raw `CPos`, you may read the wrong cell because `ToMPos()` is symmetric in `X` and `Y`.

### `Matrix<T>` vs `CellLayer<T>` bounds

`Matrix<T>` uses `int2` coordinates and is **not** grid-aware. A `Matrix<T>` that corresponds to a `CellLayer<T>` on an isometric map will be larger than the raw layer because it covers the bounding `CPos` rectangle. The unused cells (holes) are filled with the default value passed to `CellLayerUtils.ToMatrix`. Always copy back with `CellLayerUtils.FromMatrix` so that only valid cells are written.

### `MPos` and `PPos` are not interchangeable

`PPos` and `MPos` are both `(U, V)` structs, but they mean different things. `PPos` is screen-space; `MPos` is raw array space. The explicit casts make them cheap to convert, but they do not validate bounds or projection. Use `Map.ProjectedCellsCovering`, `Map.Unproject`, and `Map.ProjectedHeight` for real projection-aware queries.

### `Height` and `Ramp` are derived

`Map.Ramp` is computed from `Map.Tiles` during `PostInit` and kept in sync via `UpdateRamp`. If you manually set `Ramp` without changing the tile, the next tile change will overwrite it. If you want custom slopes, you usually change the tile to one with the desired ramp type in the tileset.

### `DefaultSubCell` validation

`MapGrid` validates the configured default index. If the offset array has more than one entry, the default must be greater than 0 (index 0 is the full-cell slot, not a sub-cell). An invalid index throws `InvalidDataException`.

### `Contains` semantics

`Map.Contains(CPos)` and `Map.Contains(MPos)` differ:

- `Contains(CPos)` may do a quick rectangular check for flat maps or the `X < Y` pre-filter for isometric maps.
- `Contains(MPos)` checks `CustomTerrain.Contains(uv)` and then calls `ContainsAllProjectedCellsCovering(uv)` for height-aware maps.
- `Contains(PPos)` is a simple bounds check against the playable rectangle.

### Projection safe bounds

`Map.SetBounds` computes a `projectionSafeBounds` rectangle. Inside this rectangle, any `MPos` is guaranteed to project to cells that are within the map. Outside it, the engine must run the full `ProjectedCellsCovering` check. Do not assume all cells near the map edge have a one-to-one projection when height is enabled.

### World coordinates

- Rectangular: one cell step = `1024` world units.
- Isometric: one cell step along the diagonal axes = `1448` world units (`sqrt(2) * 1024`), and the half-height step is `724`.
- `Map.CellHeightStep` returns `724` for isometric and `512` for rectangular.
- Do not confuse `MPos`/`CPos` height values (small integers) with `WPos.Z` (world units). `Map.CenterOfCell` multiplies the cell height by `724` for isometric and adds the ramp center offset.

### `CellLayer.Resize` is not a geometric transformation

`CellLayer.Resize` copies the overlapping top-left region of the old layer into the new layer and fills the rest with the default value. It does not scale, rotate, or reproject. After resizing, `Map.Resize` also rebuilds `AllCells` and resets the bounds.

### `ToMatrix` default value matters

For isometric layers, `CellLayerUtils.ToMatrix` fills matrix cells that do not correspond to real map cells with `defaultValue`. Choose a default that is harmless to your algorithm. For example, when converting a boolean passability mask, use `false` for the holes so that algorithms do not treat non-existent cells as passable.

### `FindTilesInCircle` range limit

`Map.FindTilesInCircle` and `FindTilesInAnnulus` use `Grid.TilesByDistance`, which is only precomputed up to `MaximumTileSearchRange`. Requesting a larger range throws `ArgumentOutOfRangeException`. If your mod needs larger range queries, increase `MaximumTileSearchRange` in `MapGrid`.

## What to read next

- [Part 7.3 — Map Generation Algorithms](../chapters/Part_07_Chapter_03_Algorithms.md) for the noise, symmetry, and matrix operations that consume these data structures.
- [Part 7.4 — Terraformer](../chapters/Part_07_Chapter_04_Terraformer.md) for the high-level orchestrator that uses `CellLayer` and `Matrix` together.
- [Part 1.4 — Deterministic Math and Coordinate Systems](../chapters/Part_01_Chapter_04_Math.md) for the full CPos/MPos/WPos conversion rules used by the engine.

## Summary

This chapter explains the core data structures that OpenRA uses to store, index, and transform a map.

After reading this chapter, you should be able to:

- For every `i,j` in `[-MaximumTileSearchRange, MaximumTileSearchRange]`, if `i² + j² ≤ MaximumTileSearchRange²`, add the `CVec(i,j)` to bucket `ceil(sqrt(i² + j²))`.
- Sort each bucket by `LengthSquared`, then hash code, then X, then Y. The hash tie-breaker is intentional: it gives a stable but non-axis-aligned order for equal-distance tiles.

If any of the concepts above feel unclear, review the relevant section before continuing. For source files and further reading, see the References section.


## References

- `OpenRA.Game/Map/CellLayerBase.cs` — `CellLayerBase<T>` definition, backing array, copying, clearing, memory access.
- `OpenRA.Game/Map/CellLayer.cs` — `CellLayer<T>` indexers, `CellEntryChanged`, `Contains`, `Clamp`, `Resize`.
- `OpenRA.Mods.Common/MapGenerator/Matrix.cs` — `Matrix<T>` generic 2D array and matrix operations.
- `OpenRA.Mods.Common/MapGenerator/CellLayerUtils.cs` — `ToMatrix`, `FromMatrix`, `CellBounds`, coordinate conversions, bulk helpers.
- `OpenRA.Game/Map/MapGrid.cs` — `MapGridType`, `CellRamp`, `SubCellOffsets`, `Ramps`, `TilesByDistance`.
- `OpenRA.Game/Map/Map.cs` — `Map` container, layer ownership, projection, loading, saving, bounds.
- `OpenRA.Game/CPos.cs` — `CPos` packed coordinate and `ToMPos`.
- `OpenRA.Game/MPos.cs` — `MPos` and `PPos` definitions and conversions.
- `OpenRA.Game/WPos.cs` — `WPos` world position and vector arithmetic.
- `OpenRA.Game/CVec.cs` — `CVec` cell vector and directions.


---

<a id="file-chapters-Part_07_Chapter_03_Algorithms"></a>

<!-- --- FILE: chapters/Part_07_Chapter_03_Algorithms.md --- -->

