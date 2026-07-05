# Chapter 1.4 — Deterministic Math and Coordinate Systems

## Purpose

OpenRA is a [deterministic](../appendices/Appendix_A_Glossary.md) [lockstep](../appendices/Appendix_A_Glossary.md) RTS engine: every client runs the same simulation from the same initial state and the same ordered inputs, and must arrive at byte-identical world states.  Because floating-point arithmetic can differ between CPU architectures, compiler versions, and optimization settings, the simulation layer performs **no floating-point math at all**.  This chapter documents the integer-only fixed-point primitives and coordinate systems that replace `float`/`double` in all gameplay logic, the deterministic math helpers that support them, and the `MapGrid` rules that convert between logical, world, projected, and rendered spaces.

## Learning Objectives


After studying this chapter, you should be able to:

- Explain why floating-point arithmetic is banned from the simulation layer.
- Convert between [WPos](../appendices/Appendix_A_Glossary.md), `WVec`, `WDist`, `WAngle`, and [CPos](../appendices/Appendix_A_Glossary.md) representations.
- Use the fixed-point 1024-unit convention to reason about distances, angles, and rotations.
- Configure [MapGrid](../appendices/Appendix_A_Glossary.md) settings in `mod.yaml` for rectangular and isometric mods.
- Identify which OpenRA math types are safe for simulation vs. rendering only.
- Trace a position update from WPos through cell conversion to the occupancy grid.

## Files

| File | Responsibility |
| :---- | :---- |
| `OpenRA.Game/WPos.cs` | 3D world position in integer world units (1 cell = 1024 WPos units). |
| `OpenRA.Game/WDist.cs` | 1D world distance / fixed-point scalar; 1024 units = 1 cell. |
| `OpenRA.Game/WAngle.cs` | 1D world angle; 1024 units = 360 degrees; lookup-table sin/cos/tan. |
| `OpenRA.Game/WVec.cs` | 3D world vector (offset, velocity) in world units. |
| `OpenRA.Game/WRot.cs` | 3D world rotation stored as a fixed-point quaternion; converts to/from Euler angles. |
| `OpenRA.Game/CPos.cs` | Packed cell coordinate (X, Y, Layer) used by gameplay logic. |
| `OpenRA.Game/CVec.cs` | 2D cell offset/delta. |
| `OpenRA.Game/MPos.cs` | Rectangular map coordinate (U, V) plus `PPos` projected map position. |
| `OpenRA.Game/Map/MapGrid.cs` | Grid type, sub-cell offsets, ramp definitions, tile distance lookup. |
| `OpenRA.Game/Map/Map.cs` | Coordinate conversions between CPos, MPos, WPos, and PPos. |
| `OpenRA.Game/Exts.cs` | Deterministic integer math utilities: integer square root, power-of-two helpers, rounding, etc. |

> Note: The source files `WPos.cs`, `WDist.cs`, `WAngle.cs`, `WVec.cs`, and `WRot.cs` live directly under `OpenRA.Game`, not in `OpenRA.Game/Primitives`.  `OpenRA.Game/MathUtils.cs` does not exist in this repository; the equivalent deterministic math utilities are in `OpenRA.Game/Exts.cs`.

![Architecture diagram](images/Part_01_Chapter_04_Math-architecture-diagram-showing-the-main-classes-interfaces-and-9161e6.svg)

## Architecture


### Determinism-first type system

All simulation-space quantities are represented by value types that wrap plain integers and perform integer arithmetic.  The core types form a hierarchy:

```
[WDist] --represents 1D distance/scalar--> 1024 units = 1 cell
[WAngle] --represents 1D rotation--> 1024 units = 360 degrees
[WVec]   --3D offset/velocity in WDist units along X, Y, Z
[WPos]   --3D position in WDist units (X, Y, Z)
[WRot]   --3D rotation, internally a fixed-point quaternion
[CPos]   --packed cell coordinate (X, Y, Layer)
[CVec]   --2D cell offset (X, Y)
[MPos]   --rectangular map index (U, V)
[PPos]   --projected map index (U, V) used for height/cell projection
```

These types are deliberately **read-only structs** with value equality.  They expose operators for addition, subtraction, scalar multiplication/division, and dot products, but never division by non-integer values, and never use `float` or `double` in simulation code.

### Why floating-point is banned

Floating-point arithmetic is non-deterministic across platforms for several reasons:

- **x87 vs. SSE**: legacy x87 FPU uses 80-bit extended precision internally, then rounds to 64-bit when storing.  SSE uses strict 64-bit IEEE-754.  The same expression can produce different low bits.
- **ARM vs. x86**: `double`/`float` handling, fusion, and contraction differ; some fused multiply-add instructions introduce extra precision.
- **Compiler optimizations**: `float` expressions may be reordered or constant-folded with different rounding results under different compiler versions.
- **Math library differences**: `Math.Sin`, `Math.Sqrt`, etc. are not guaranteed bit-identical across runtimes.

In OpenRA, even a single bit divergence in a unit position eventually diverges the entire simulation, causing [desyncs](../appendices/Appendix_A_Glossary.md) in multiplayer.  Therefore:

- **Simulation code** uses only `WPos`, `WVec`, `WDist`, `WAngle`, `WRot`, `CPos`, `CVec`, `MPos`, and `PPos`.
- **Rendering code** uses `float2`, `float3`, `int2`, and `WAngle.RendererRadians()` / `RendererDegrees()` only for the renderer, never to influence gameplay state.
- `decimal` is used in a few isolated places (e.g., `WPos.LerpQuadratic`) as a widening intermediate to avoid 32-bit overflow, but the final result is always cast back to `int`.

### Fixed-point conventions

| Type | Unit | Meaning of `1024` | Storage |
| :---- | :---- | :---- | :---- |
| `WDist` | length | 1 cell | `int Length` |
| `WVec` / `WPos` | 3D length | 1024 per cell axis | `int X, Y, Z` |
| `WAngle` | angle | 360 degrees | `int Angle` |
| `WRot` | rotation | quaternion normalized to 1024 = 1.0 | `int x, y, z, w` + Euler angles |

Multiplication and division are scaled by powers of `1024` where needed.  For example, a quaternion product divides by `1024` after each component multiplication because the quaternion components are already stored in 1024-normalized form.

![Data flow  code path diagram](images/Part_01_Chapter_04_Math-sequence-flow-diagram-tracing-the-execution-path-from-trigge-035864.svg)

## Data Flow / Code Path


### 1. Position update

1. An actor holds a `WPos CenterPosition` (via `IOccupySpace`).
2. Each tick, movement code computes a `WVec` delta using `WAngle` and `WDist` operations.
3. The new position is `newPosition = oldPosition + delta`.
4. `Map.CellContaining(newPosition)` converts the world position back into a `CPos` for occupancy, pathfinding, and rendering.
5. The occupancy grid (`ActorMap`) uses `CPos` and `SubCell` to track which units share a cell.

### 2. Angle → direction

1. A facing value (e.g., from `Mobile` or `Turret`) is stored as `WAngle`.
2. `WAngle.Cos()` / `Sin()` return integer values in the range `[-1024, 1024]` via lookup tables.
3. A movement vector is computed as `(dist * cos / 1024, dist * sin / 1024, 0)`.
4. Because the tables are identical on every client, every CPU produces the same integer result.

### 3. Map grid → tile distances

1. `MapGrid` constructor pre-computes `TilesByDistance`.
2. A pathfinder or search algorithm asks for cells at distance `d` and iterates `TilesByDistance[d]`.
3. Each entry is a `CVec`; adding it to a `CPos` yields a candidate neighbor.

### 4. Rendering isolation

1. The renderer reads `WPos` and `WRot` from the actor.
2. It converts to `float3` and `float` radians for OpenGL/Veldrid using `WAngle.RendererRadians()` or `WRot` matrix helpers.
3. The renderer's `float` conversions never write back into simulation state.

![Configuration (yaml) diagram](images/Part_01_Chapter_04_Math-annotated-yaml-snippet-diagram-showing-the-key-fields-and-ho-6a1b98.svg)

## Configuration (YAML)


`MapGrid` is an `IGlobalModData` loaded from each mod's `mod.yaml` under the `MapGrid:` key.  Fields are deserialized by `FieldLoader.Load`.

### Example — `mods/ra/mod.yaml`

```yaml
MapGrid:
	Type: Rectangular
```

### Example — `mods/ts/mod.yaml`

```yaml
MapGrid:
	EnableDepthBuffer: True
	Type: RectangularIsometric
	MaximumTerrainHeight: 16
	SubCellOffsets: 0,0,0, -362,0,0, 0,362,0, 362,0,0
	DefaultSubCell: 2
```

### Field reference

| YAML key | C# field | Default | Meaning |
| :---- | :---- | :---- | :---- |
| `Type` | `MapGridType Type` | `Rectangular` | `Rectangular` or `RectangularIsometric`. |
| `MaximumTerrainHeight` | `byte MaximumTerrainHeight` | `0` | Max height layer for terrain cliffs. |
| `SubCellOffsets` | `ImmutableArray<WVec> SubCellOffsets` | 6-entry default | World offsets (X,Y,Z) for each sub-cell index. |
| `DefaultSubCell` | `SubCell DefaultSubCell` | middle index | Sub-cell index used when no specific sub-cell is requested. |
| `MaximumTileSearchRange` | `int MaximumTileSearchRange` | `50` | Radius used to build `TilesByDistance`. |
| `EnableDepthBuffer` | `bool EnableDepthBuffer` | `false` | Whether the renderer uses a depth-aware drawing order for isometric heights. |

### Default sub-cell offsets

From `MapGrid.cs`:

```csharp
new(0, 0, 0),       // full cell - index 0
new(-299, -256, 0), // top left - index 1
new(256, -256, 0),  // top right - index 2
new(0, 0, 0),       // center - index 3
new(-299, 256, 0),  // bottom left - index 4
new(256, 256, 0),   // bottom right - index 5
```

Tiberian Sun overrides this in `mod.yaml` with a 4-offset layout (indices 0–3) and sets `DefaultSubCell: 2`.

## Interconnectivity

### Depends on

- **Random number generation** (`MersenneTwister`) — `WDist.FromPDF` and `WVec.FromPDF` sample deterministic distributions using the shared RNG.
- **Map loading / MiniYaml** — `MapGrid` is constructed from `mod.yaml` via `FieldLoader`.
- **Scripting bridge** (`Eluant`) — all W* and C* types implement `IScriptBindable` so Lua maps can query positions and angles without exposing raw integers.

### Used by

- **Actor movement / pathfinding** — `CPos`, `CVec`, `WPos`, `WVec`, `WAngle`.
- **Combat / weapons** — `WDist`, `WPos`, `WAngle` for range, accuracy, and firing arcs.
- **World renderer** — converts `WPos`/`WRot` to `float3` for drawing.
- **Map editor** — `MPos`, `PPos`, `CPos` for tile and cell selection.
- **Orders** — `CPos` is serialized in orders and sent over the network.

![Algorithms diagram](images/Part_01_Chapter_04_Math-algorithm-diagram-or-pseudocode-flowchart-for-the-non-trivia-5983ed.svg)

## Algorithms


### WAngle: 1024 = 360 degrees

`WAngle` stores an integer in `[0, 1023]` normalized on construction:

```csharp
public WAngle(int a)
{
    Angle = a % 1024;
    if (Angle < 0)
        Angle += 1024;
}
```

Key angle values:

| Direction | `WAngle` | Facing |
| :---- | :---- | :---- |
| North | `0` | `0` |
| East | `256` | `64` |
| South | `512` | `128` |
| West | `768` | `192` |
| Full circle | `1024` (stored as `0`) | `256` |

`FromFacing(int facing)` multiplies by `4` because the original game sprites use 256 facing steps.  `FromDegrees(int degrees)` multiplies by `1024 / 360`.

`Cos()` and `Sin()` use two precomputed 256-entry tables.  Because the first quadrant is symmetric, the code mirrors the index into `[0, 256]`:

```csharp
public int Cos()
{
    if (Angle <= 256) return CosineTable[Angle];
    if (Angle <= 512) return -CosineTable[512 - Angle];
    return -new WAngle(Angle - 512).Cos();
}
```

`Sin()` simply phases the angle by `-256` (90 degrees) and calls `Cos()`.  `Tan()` uses a separate `TanTable` with the same quadrant mirroring.  `ArcTan`, `ArcSin`, and `ArcCos` search the tables to find the closest matching value, yielding deterministic inverse trigonometric results without any floating point.

### WRot: fixed-point quaternion

`WRot` stores Euler angles (`Roll`, `Pitch`, `Yaw`) for public use and a fixed-point quaternion (`x`, `y`, `z`, `w`) for internal math.  Quaternion components are normalized to `1024 == 1.0`.

Construction from Euler angles:

```csharp
var qr = new WAngle(-Roll.Angle / 2);
var qp = new WAngle(-Pitch.Angle / 2);
var qy = new WAngle(-Yaw.Angle / 2);
var cr = (long)qr.Cos(); // etc.
x = (int)((sr * cp * cy - cr * sp * sy) / 1048576); // 1024^2
y = (int)((cr * sp * cy + sr * cp * sy) / 1048576);
z = (int)((cr * cp * sy - sr * sp * cy) / 1048576);
w = (int)((cr * cp * cy + sr * sp * sy) / 1048576);
```

The product `sin/cos` values are each in `[-1024, 1024]`, so their product is divided by `1048576` (1024²) to land back in the 1024-normalized quaternion space.

A vector is rotated by the 4×4 integer matrix produced by `WRot.AsMatrix()`:

```csharp
var lx = (long)X;
// ...
return new WVec(
    (int)((lx * mtx.M11 + ly * mtx.M21 + lz * mtx.M31) / mtx.M44),
    ...);
```

`mtx.M44` holds the squared quaternion length, which keeps the rotation correctly normalized despite accumulated integer rounding.

### Cell coordinate systems

OpenRA uses four related coordinate spaces:

| Space | Type | Purpose | Coordinates |
| :---- | :---- | :---- | :---- |
| Cell | `CPos` | Gameplay grid; what players think of as "a tile". | X, Y, Layer |
| Map | `MPos` | Rectangular array index into `CellLayer<T>`; always U, V. | U, V |
| World | `WPos` | Continuous 3D position in world units. | X, Y, Z |
| Projected | `PPos` | Screen-space-ish map index for height projection. | U, V |

`CPos` is packed into a single `int`:

```csharp
// XXXX XXXX XXXX YYYY YYYY YYYY LLLL LLLL
// X and Y are 12 bits signed: -2048..2047
// Layer is an unsigned byte
Bits = (x & 0xFFF) << 20 | (y & 0xFFF) << 8 | layer;
```

This packing makes equality and hashing cheap and network-order safe.

#### Rectangular grid conversions

For `Rectangular` maps:

```csharp
CPos <-> MPos: identical (X=U, Y=V)
CenterOfCell(CPos c): new WPos(1024 * c.X + 512, 1024 * c.Y + 512, 0)
CellContaining(WPos p): new CPos(p.X / 1024, p.Y / 1024)
```

One cell is 1024×1024 world units; its center is offset by 512 units.

#### Rectangular-isometric grid conversions

For `RectangularIsometric` maps (Tiberian Sun style):

```csharp
// CPos -> MPos
var v = X + Y;
var u = (v - (v & 1)) / 2 - Y;
return new MPos(u, v);

// MPos -> CPos
var y = (V - (V & 1)) / 2 - U;
var x = V - y;
return new CPos(x, y);

// CenterOfCell(CPos c)
var z = Height[cell] * 724 + Grid.Ramps[Ramp[cell]].CenterHeightOffset;
return new WPos(724 * (cell.X - cell.Y + 1), 724 * (cell.X + cell.Y + 1), z);

// CellContaining(WPos p)
var u = (p.Y + p.X - 724) / 1448;
var v = (p.Y - p.X + (p.Y > p.X ? 724 : -724)) / 1448;
return new CPos(u, v);
```

The factor `724` is `512 * sqrt(2)` rounded to an integer; the cell diagonal is `1448` = `1024 * sqrt(2)`.  These approximations are deterministic because they are integer constants.

### Sub-cells

A [`SubCell`](../appendices/Appendix_A_Glossary.md) is a byte index into `MapGrid.SubCellOffsets`.  The enum definition is:

```csharp
public enum SubCell : byte { Invalid = byte.MaxValue, Any = byte.MaxValue - 1, FullCell = 0, First = 1 }
```

- `FullCell` (0) is the first entry in the offset array and is usually `(0,0,0)`.
- `Invalid` means "not on the map".
- `Any` asks the occupancy system to pick a free sub-cell.

`Map.CenterOfSubCell(CPos cell, SubCell subCell)` returns:

```csharp
center + offset + rampHeightCorrection
```

If the cell has a ramp, the sub-cell's Z offset is adjusted by the ramp's height at that local offset so infantry standing on a slope are at the correct world height.

### Ramps and terrain orientation

`CellRamp` defines the 3D geometry of a sloped tile.  Each corner can be `Low` (0), `Half` (1), or `Full` (2), and the tile can be split into two triangles along `X` or `Y` to form non-planar slopes.

Corner vectors for rectangular:

```csharp
new WVec(-512, -512, 512 * tl),
new WVec(512, -512, 512 * tr),
new WVec(512, 512, 512 * br),
new WVec(-512, 512, 512 * bl)
```

For rectangular-isometric:

```csharp
new WVec(0, -724, 724 * tl),
new WVec(724, 0, 724 * tr),
new WVec(0, 724, 724 * br),
new WVec(-724, 0, 724 * bl)
```

`CellRamp.HeightOffset(dX, dY)` performs barycentric interpolation over the triangle(s) that contain `(dX, dY)` to return the Z offset at that point.  `MapGrid` hardcodes the 20 ramp types from the Tiberian Sun / Red Alert 2 map format.

### TilesByDistance

`MapGrid.CreateTilesByDistance()` builds concentric square rings of `CVec` offsets:

```csharp
for (j = -range .. range)
    for (i = -range .. range)
        if (range*range >= i*i + j*j)
            buckets[ISqrt(i*i + j*j, Ceiling)].Add(new CVec(i, j));
```

Each bucket is then sorted by real squared length, then by hash code, then X, then Y to produce a deterministic iteration order.  This is heavily used by `PathSearch` and area-effect searches.

### Integer square root

`Exts.ISqrt` implements the classic digit-by-digit (long division style) square root algorithm for `uint`/`ulong` and wraps it for `int`/`long`.  It supports three rounding modes:

```csharp
public enum ISqrtRoundMode { Floor, Nearest, Ceiling }
```

`WVec.Length` uses `Exts.ISqrt(LengthSquared)` for deterministic distance.  `MapGrid.TilesByDistance` uses `Ceiling` to assign cells to the correct ring.

![Extension points diagram](images/Part_01_Chapter_04_Math-extension-hook-diagram-showing-the-interface-s-to-implement-b4a27b.svg)

## Extension Points


### Mod-level grid configuration

A mod can override `MapGrid` in `mod.yaml` to change the grid type, sub-cell layout, or maximum terrain height.  For example, Tiberian Sun switches to `RectangularIsometric` with custom sub-cell offsets.

### New ramp types

`MapGrid` hardcodes ramp definitions, but the geometry data (corner heights, split axis, orientation) is structurally defined.  A future engine extension could load ramp definitions from YAML or add new `CellRamp` constructors.

### Custom deterministic math

All new math that affects simulation state must:

1. Use integer arithmetic only.
2. Use `Exts.ISqrt` for square roots.
3. Use `WAngle`/`WRot` for trigonometry.
4. Avoid `float`/`double` intermediates except in renderer-only code.

### Scripting

Lua can read and manipulate `WPos`, `WVec`, `WDist`, `WAngle`, `CPos`, and `CVec` through the `IScriptBindable` interfaces.  These are read-only from scripts; creation is done via `WPos.New`, `WVec.New`, etc.

![Common pitfalls  guardrails diagram](images/Part_01_Chapter_04_Math-checklist-infographic-style-diagram-summarizing-the-top-pitf-fb069e.svg)

## Common Pitfalls / Guardrails


### Never use `float` in simulation

- `float2`, `float3`, `Math.Sin`, `Math.Cos`, `Math.Sqrt`, and `Vector3` are for rendering only.
- Even a single `float` multiplication in a movement or damage calculation can desync cross-platform multiplayer.

### Integer overflow

- `WVec.LengthSquared` is a `long` to prevent overflow of `X*X + Y*Y + Z*Z`.
- `WPos.Lerp` and `WPos.LerpQuadratic` use `long` and `decimal` intermediates respectively.
- Matrix multiplications in `WVec.Rotate` and `WRot` use `long` intermediates before dividing back to `int`.

### Division rounding

- Integer division truncates toward zero.  `Exts.IntegerDivisionRoundingAwayFromZero` is available when the rounding direction matters.
- Be careful with negative angles: `WAngle` normalizes them to `[0, 1023]`, but intermediate subtraction can produce negative values.

### Angle wrap-around

- `WAngle.Lerp` handles the 1024 wrap-around by comparing the two angles and subtracting 1024 from the larger if the gap exceeds 512.
- Facing (256-step) is converted to `WAngle` by multiplying by 4.

### Coordinate system confusion

- `CPos` is the gameplay cell; `MPos` is the rectangular array index.  They are identical in `Rectangular` maps but very different in `RectangularIsometric` maps.
- Always use `cell.ToMPos(map)` or `map.Grid.Type` when indexing into `CellLayer<T>`.
- `PPos` is the screen-space projected cell used for height and visibility; it is **not** the same as `MPos` when terrain height is non-zero.

### SubCell index validity

- `SubCell.Invalid` and `SubCell.Any` are sentinel values (`byte.MaxValue` and `byte.MaxValue - 1`).  They must be resolved before indexing `SubCellOffsets`.
- `MapGrid` validates `DefaultSubCell` in the constructor and throws if it is out of range.

### Determinism across platforms

- The `WAngle` trig tables and `Exts.ISqrt` are the same on every architecture because they are pure integer lookups and shift/subtract loops.
- `MersenneTwister` is used for deterministic randomness; never use `System.Random` for simulation.
- Hash codes for the coordinate structs use `X ^ Y ^ Z` (or `X ^ Y` for 2D types).  These are stable across .NET versions because they are custom implementations.

## Summary

This chapter explains the deterministic, integer-only math foundations that keep OpenRA's lockstep simulation consistent across clients and platforms.

After reading this chapter, you should be able to:

- An actor holds a `WPos CenterPosition` (via `IOccupySpace`).
- Each tick, movement code computes a `WVec` delta using `WAngle` and `WDist` operations.
- The new position is `newPosition = oldPosition + delta`.
- `Map.CellContaining(newPosition)` converts the world position back into a `CPos` for occupancy, pathfinding, and rendering.
- The occupancy grid (`ActorMap`) uses `CPos` and `SubCell` to track which units share a cell.

If any of the concepts above feel unclear, review the relevant section before continuing. For source files and further reading, see the References section.


## References

- Source files:
  - `OpenRA.Game/WPos.cs`
  - `OpenRA.Game/WDist.cs`
  - `OpenRA.Game/WAngle.cs`
  - `OpenRA.Game/WVec.cs`
  - `OpenRA.Game/WRot.cs`
  - `OpenRA.Game/CPos.cs`
  - `OpenRA.Game/CVec.cs`
  - `OpenRA.Game/MPos.cs`
  - `OpenRA.Game/Map/MapGrid.cs`
  - `OpenRA.Game/Map/Map.cs`
  - `OpenRA.Game/Exts.cs`
  - `OpenRA.Game/Traits/TraitsInterfaces.cs` (SubCell enum)
- Mod YAML:
  - `mods/ra/mod.yaml`
  - `mods/ts/mod.yaml`
  - `mods/cnc/mod.yaml`
  - `mods/d2k/mod.yaml`

## What to read next

- [Part 1.5 — Pathfinding and Movement](Part_01_Chapter_05_Pathfinding_Movement.md): the pathfinding and movement systems are the biggest consumers of `WPos`, `CPos`, `WAngle`, and `MapGrid`.
- [Part 1.6 — Combat and Damage Resolution](Part_01_Chapter_06_Combat_Damage.md): see how range, facing, and projectile positions use the same fixed-point math.
- [Part 9.1 — OrderManager and Lockstep Foundation](Part_09_Chapter_01_OrderManager.md): understand why the deterministic math in this chapter is required for multiplayer lockstep.
- Related manual chapters:
  - Chapter 1.1 — ECS / Actor model
  - Chapter 1.2 — Activities
  - Chapter 1.3 — World Orders