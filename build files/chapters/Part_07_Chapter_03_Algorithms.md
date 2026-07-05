# Chapter 7.3 — Map Generation Algorithms

## Purpose

This chapter documents the low-level algorithmic primitives that the OpenRA procedural map generator uses to synthesize terrain, roads, rivers, resource patches, and base sites. These primitives are not a complete map pipeline by themselves; rather, they are the mathematical building blocks that higher-level generators (the "[Terraformer](../appendices/Appendix_A_Glossary.md)", tiling, actor placement, and resource distribution systems) compose to produce a finished `Map`. The three files covered here are tightly coupled: `NoiseUtils` produces candidate height fields, `Symmetry` constrains those fields to fair multiplayer layouts, and `MatrixUtils` turns those scalar fields into clean, connected, pathable regions and contour lines. Understanding how they fit together is essential for diagnosing map artifacts, tuning YAML parameters, and extending the generator.

## Learning Objectives


After studying this chapter, you should be able to:

- Explain how Perlin noise and fractal noise are synthesized for terrain generation.
- Apply Symmetry operations to create mirror and rotational-symmetric noise fields.
- Use MatrixUtils to threshold, smooth, morph, and extract contours from boolean masks.
- Trace the typical generator path from noise to mask to path to final placement.
- Configure YAML parameters that drive these algorithms (featureSize, rotations, smoothing, etc.).
- Debug map artifacts by understanding the underlying algorithmic primitives.

## Files

| File | Responsibility |
| :---- | :---- |
| `OpenRA.Mods.Common/MapGenerator/NoiseUtils.cs` | Perlin noise generation, octave summation (fractal noise), symmetric fractal noise, and amplitude-spectrum presets used for terrain features. |
| `OpenRA.Mods.Common/MapGenerator/MatrixUtils.cs` | Boolean morphology, smoothing ("BooleanBlotch"), contour/path extraction, loop/partition optimization, flood fills, distance transforms, and matrix debugging dumps. |
| `OpenRA.Mods.Common/MapGenerator/Symmetry.cs` | Mirror and rotational-symmetry primitives, point projection around centers, and coordinate-system-aware wrappers for `WPos`/`CPos`. |
| `OpenRA.Mods.Common/MapGenerator/Direction.cs` | Direction enum, direction masks, and adjacency helpers used heavily by `MatrixUtils` border tracing. |

![Architecture diagram](images/Part_07_Chapter_03_Algorithms-architecture-diagram-showing-the-main-classes-interfaces-and-9161e6.svg)

## Architecture


These classes are all static helper classes, not object-oriented services. They operate on two shared data types:

- `Matrix<T>` — a 2-D rectangular array of `T` with a flat backing array, an `int2 Size`, and indexers `[x, y]` / `[i]`.
- `[CellLayer<T>](../appendices/Appendix_A_Glossary.md)` — a map-aware layer tied to the grid type (`Rectangular` or `RectangularIsometric`) and used when the generator needs to work in `CPos`/`WPos` space.

```
NoiseUtils
    PerlinNoise          => Matrix<int>
    FractalNoise         => Matrix<int>   (uses PerlinNoise + MatrixUtils.IntegerInterpolate)
    SymmetricFractalNoise=> Matrix<int>   (uses FractalNoise + Symmetry.RotateAndMirrorPointAround)
    SymmetricFractalNoiseIntoCellLayer => CellLayer<int>

Symmetry
    Mirror enum
    WMirror struct
    MirrorPointAround
    RotateAndMirrorPointAround
    RotateAndMirrorWPosAround / CPos
    ProjectionProximity

MatrixUtils
    IntegerInterpolate
    BooleanBlur / BooleanBlotch
    RetainThickRegions / DilateThinRegions
    BordersToPoints
    DirectionMapToPaths / DirectionMapToPathsWithPruning
    RemoveStubsFromDirectionMapInPlace / RemoveJunctionsFromDirectionMap
    MaskPathPoints
    DeflateSpace / ChebyshevRoom / WalkingDistances
    FloodFill / KernelFilter / BinomialBlur
    ColorDump2d / Dump2d / GraphPoints (debug only)
```

The design is deliberately functional: each method transforms one matrix into another and returns both the result and, where useful, a change count. The caller is responsible for deciding when to stop iterating, which is why many methods return `(Output, Changes)`.

![Data flow  code path diagram](images/Part_07_Chapter_03_Algorithms-sequence-flow-diagram-tracing-the-execution-path-from-trigge-035864.svg)

## Data Flow / Code Path


A typical high-level generator path through these three files looks like this:

1. **YAML parameters are read** by the higher-level generator (e.g., `Terraformer` or `MapGenerator`). Values such as `featureSize`, `rotations`, `mirror`, `terrainSmoothing`, `minimumThickness`, `threshold`, and `thresholdOutOf` are passed as arguments.

2. **Noise is synthesized**.
   ```
   SymmetricFractalNoise(random, size, rotations, mirror, featureSize, ampFunc)
       FractalNoise(random, size * 2 + 2, featureSize, ampFunc)
           PerlinNoise(random, span) for each octave
           IntegerInterpolate(template, ...) for sub-grid sampling
       RotateAndMirrorPointAround(templateCenter, ...)
   ```

3. **Noise is converted to a boolean mask** by `CalibratedBooleanThreshold` or a custom threshold.

4. **The mask is cleaned up** by `BooleanBlotch`.
   ```
   BooleanBlotch(input, terrainSmoothing, smoothingThreshold,
                 smoothingThresholdOutOf, minimumThickness, bias)
       BooleanBlur
       RetainThickRegions / DilateThinRegions (true, then false)
       optional OverCircle bias fill
   ```

5. **Contours are extracted** from the cleaned mask with `BordersToPoints`, producing one or more `int2[]` loops and open paths.

6. **Paths are optimized** with `DirectionMapToPathsWithPruning`, `MaskPathPoints`, and other utilities to remove stubs, short loops, and off-mask segments.

7. **The final path or region data is consumed** by tile placement, cliff/river/road rendering, resource spawning, and actor placement logic.

![Configuration (yaml) diagram](images/Part_07_Chapter_03_Algorithms-annotated-yaml-snippet-diagram-showing-the-key-fields-and-ho-6a1b98.svg)

## Configuration (YAML)


These three files themselves are not YAML-configured; they are static algorithm libraries. However, the parameters they expose are consumed from YAML by higher-level generators. The table below maps the arguments in these files to the kinds of YAML keys a mod author would edit.

| Parameter | Typical YAML key | Description |
| :---- | :---- | :---- |
| `featureSize` | `TerrainFeatureSize`, `WaterFeatureSize`, `CliffFeatureSize` | Largest wavelength of the noise field, in 1024ths of a cell. |
| `ampFunc` | `Amplitude: White`, `Amplitude: Pink`, `Clumpiness: N` | Preset that controls how much each octave contributes. |
| `rotations` | `Symmetry: N` (rotational count) | Number of copies of the map around its center. |
| `mirror` | `Mirror: None`, `Mirror: LeftMatchesRight`, etc. | Whether to mirror each rotated copy across an axis. |
| `terrainSmoothing` / `smoothingThreshold` / `smoothingThresholdOutOf` | `TerrainSmoothing`, `SmoothingThreshold` | Radius and vote threshold for the cellular-automata smoothing step. |
| `minimumThickness` | `MinimumThickness` | Minimum Chebyshev thickness of land/water regions. |
| `bias` | `Bias` | Tie-breaker used when land and water correction fight. |

Because the arguments are plain integers, booleans, and function delegates, any generator can supply them directly from YAML, from constants, or from random seeds. The `MersenneTwister` instance is the only source of randomness and must be deterministically seeded so that all clients in a multiplayer match generate the same map.

## Interconnectivity

- **Depends on:**
  - `OpenRA.Mods.Common/MapGenerator/Matrix.cs` and `OpenRA.Game/Map/CellLayer.cs` — the underlying grid containers.
  - `OpenRA.Support/MersenneTwister.cs` — deterministic RNG.
  - `OpenRA.Game/Primitives/int2.cs`, `WPos.cs`, `WAngle.cs`, `WDist.cs` — coordinate and fixed-point math.
  - `OpenRA.Mods.Common/MapGenerator/Direction.cs` — adjacency, direction masks, and offsets.
  - `OpenRA.Mods.Common/MapGenerator/CellLayerUtils.cs` — conversions between `Matrix`, `CellLayer`, `CPos`, and `WPos`.

- **Used by:**
  - Higher-level generator classes in `OpenRA.Mods.Common/MapGenerator/` (e.g., `Terraformer.cs`, `TilingPath.cs`, `RampTiler.cs`, `MapGenerator.cs`). These files are covered in subsequent chapters of Part 7.
  - Debugging utilities and the map editor preview, which use the `ColorDump2d` / `Dump2d` helpers.

![Algorithms diagram](images/Part_07_Chapter_03_Algorithms-algorithm-diagram-or-pseudocode-flowchart-for-the-non-trivia-5983ed.svg)

## Algorithms


### 1. Perlin Noise (`NoiseUtils.PerlinNoise`)

OpenRA uses a classic gradient-based Perlin noise implementation. The output is a `Matrix<int>` of size `span × span`. The gradients are random unit vectors; the dot products are accumulated into the four corners of every cell.

**Pseudocode:**
![1. Perlin Noise (`NoiseUtils.PerlinNoise`)](images/Part_07_Chapter_03_Algorithms-Perlin_noise_flowchart.svg)
The output range is documented as `[-5792, +5792]`. The maximum magnitude occurs when every corner of a cell receives the maximum possible projection, which is `2 * 1024 * 2 * sqrt(2) ≈ 5792` in the engine's fixed-point integer representation.

### 2. Fractal Noise (`NoiseUtils.FractalNoise`)

Fractal noise is built by summing several octaves of Perlin noise. Each octave is generated at a wavelength of `featureSize >> i` (halving each octave) and is interpolated into the output matrix using `IntegerInterpolate`. The amplitude of each octave is controlled by `ampFunc`.

**Pseudocode:**
```
function FractalNoise(random, size, featureSize, ampFunc):
    span = max(size.X, size.Y)
    octaveCount = floor(log2(span))
    noise = new Matrix<int>(size).fill(0)
    for i = 0 to octaveCount - 1:
        wavelength = featureSize >> i
        if wavelength <= 1024 / 2:
            break
        amplitude = ampFunc(wavelength)
        subSpan = span * 1024 / wavelength + 2
        subNoise = PerlinNoise(random, subSpan)
        offsetX = random.NextUint() % (wavelength + 1)
        offsetY = random.NextUint() % (wavelength + 1)
        for y = 0 to size.Y - 1:
            for x = 0 to size.X - 1:
                sx = x * 1024 + offsetX
                sy = y * 1024 + offsetY
                ix = sx / wavelength
                iy = sy / wavelength
                wx = sx % wavelength
                wy = sy % wavelength
                noise[x, y] += amplitude * IntegerInterpolate(
                    subNoise, ix, iy, wx, wy, wavelength)
    return noise
```

Key design points:

- `Scale` is fixed at 1024. All sub-pixel coordinates are in 1024ths of a cell.
- Wavelengths below `Scale/2` are skipped because they would no longer contribute meaningful spatial variation.
- The random offsets are in units of the current wavelength so that each octave aligns with the same conceptual grid.
- `IntegerInterpolate` performs bilinear interpolation with fixed-point weights and clamps edge coordinates to the border cells.

### 3. Amplitude Functions (`NoiseUtils`)

The amplitude function decides how loud each octave is.

| Function | Formula | Effect |
| :---- | :---- | :---- |
| `WhiteAmplitude` | `1` for every octave | Uniform spectrum; lots of fine grain, no natural clustering. |
| `PinkAmplitude` | `wavelength` | Amplitude proportional to wavelength; large features dominate. |
| `ClumpinessAmplitude` | `wavelength ** (1 / 2 ** clumpiness)` | Intermediate between pink and white; higher `clumpiness` = more uniform, blob-like terrain. |

The `ClumpinessAmplitude` loop repeatedly applies `Exts.ISqrt` (integer square root) to `wavelength` `clumpiness` times. For `clumpiness == 0`, it is exactly pink noise.

**Pseudocode:**
```
function ClumpinessAmplitude(wavelength, clumpiness):
    amplitude = wavelength
    for i = 0 to clumpiness - 1:
        amplitude = IntegerSqrt(amplitude)
    return amplitude
```

### 4. Symmetric Fractal Noise (`NoiseUtils.SymmetricFractalNoise`)

Symmetric fractal noise is the same as fractal noise but sampled in a way that makes the output invariant under a chosen symmetry group. The engine creates a larger template (`size * 2 + 2`) to avoid cropping and rotation artifacts. For each output cell, it computes the cell's coordinate relative to the output center, projects that point through every rotation and mirror, and accumulates the bilinear samples.

**Pseudocode:**
```
function SymmetricFractalNoise(random, size, rotations, mirror, featureSize, ampFunc):
    templateSpan = max(size.X, size.Y) * 2 + 2
    templateSize = (templateSpan, templateSpan)
    template = FractalNoise(random, templateSize, featureSize, ampFunc)
    templateCenter = (templateSpan - 1) * 1024 / 2
    outputMid = (size - 1) * 1024 / 2
    output = new Matrix<int>(size)
    for y = 0 to size.Y - 1:
        for x = 0 to size.X - 1:
            fromCenter = (x * 1024, y * 1024) - outputMid
            // sqrt(2) scaling so diagonal samples don't alias
            fromCenter *= (1448 / 1024)
            templateXY = fromCenter + templateCenter
            projections = RotateAndMirrorPointAround(templateXY, templateCenter,
                                                     rotations, mirror)
            for p in projections:
                output[x, y] += IntegerInterpolate(template,
                    p.X / 1024, p.Y / 1024,
                    p.X % 1024, p.Y % 1024, 1024)
    return output
```

The `ScaledSqrt2 = 1448` constant is `floor(1024 * sqrt(2))`, ensuring that the radius of the sample circle stays consistent when the coordinate is rotated by arbitrary angles.

### 5. Symmetry (`Symmetry.cs`)

#### 5.1 Mirror Modes

The `Symmetry.Mirror` enum gives four reflection axes, plus `None`:

| Enum | Axis | Mapping |
| :---- | :---- | :---- |
| `None` | — | No mirror. |
| `LeftMatchesRight` | Vertical | `(x, y) -> (2*cx - x, y)` |
| `TopMatchesBottom` | Horizontal | `(x, y) -> (x, 2*cy - y)` |
| `TopLeftMatchesBottomRight` | Diagonal (NW-SE) | `(x, y) -> (cy - y + cx, cx - x + cy)` |
| `TopRightMatchesBottomLeft` | Anti-diagonal (NE-SW) | `(x, y) -> (cx + y - cy, cy + x - cx)` |

#### 5.2 WMirror and Coordinate Systems

`WMirror` pairs a `Mirror` with a `MapGridType`. The isometric grid (`RectangularIsometric`) rotates the conceptual axis by two steps because the `CPos` coordinate system is rotated 45 degrees relative to `WPos`. `ForCPos()` returns `((mirror + 2) & 0b11) + 1` for isometric grids; otherwise it returns the same mirror.

#### 5.3 Rotational and Mirror Projection

`RotateAndMirrorPointAround` computes the full orbit of an original point under the symmetry group. The rotation count `N` produces `N` equally spaced angles around 360 degrees. If mirroring is enabled, each rotated point is also mirrored, doubling the total count.

**Pseudocode:**
```
function RotateAndMirrorPointAround(original, center, rotations, mirror):
    total = (mirror == None) ? rotations : rotations * 2
    projections = new int2[total]
    idx = 0
    for r = 0 to rotations - 1:
        angle = r * 1024 / rotations
        cos = WAngle(angle).Cos()
        sin = WAngle(angle).Sin()
        rel = original - center
        px = (rel.X * cos - rel.Y * sin) / 1024 + center.X
        py = (rel.X * sin + rel.Y * cos) / 1024 + center.Y
        projections[idx++] = (px, py)
        if mirror != None:
            projections[idx++] = MirrorPointAround(mirror, (px, py), center)
    return projections
```

`ProjectionProximity` computes the smallest Euclidean distance between any two projections in the set, which is used by higher-level code to verify that the symmetry is not so dense that base sites or terrain features overlap.

### 6. BooleanBlur (`MatrixUtils.BooleanBlur`)

`BooleanBlur` is a thresholded median blur. It counts `true` cells in a square `(2*r+1)²` neighborhood around each cell. If the count is above `trueThreshold`, the cell becomes `true`; if below `falseThreshold`, it becomes `false`; otherwise it keeps its original value.

The implementation is optimized with a two-pass sliding window:

1. First pass produces horizontal counts `hTrueCounts` in `O((size.X + radius) * size.Y)`.
2. Second pass sums the vertical windows over `hTrueCounts` in `O(size.X * (size.Y + radius))`.

**Pseudocode:**
![6. BooleanBlur (`MatrixUtils.BooleanBlur`)](images/Part_07_Chapter_03_Algorithms-Boolean_blur_flowchart.svg)
The `threshold` controls the "aggressiveness" of the smoothing. A threshold of `1/2` is a pure majority-vote median; a threshold like `20/25` (80%) requires an overwhelming majority to flip a cell, which preserves larger regions while only smoothing very ragged edges.

### 7. BooleanBlotch (`MatrixUtils.BooleanBlotch`)

`BooleanBlotch` is the higher-level cleanup routine that converts a noisy boolean mask into "blobby" regions. It combines three operations:

1. **Thresholded smoothing** via repeated `BooleanBlur`.
2. **Minimum thickness enforcement** via `RetainThickRegions` and `DilateThinRegions`.
3. **Diagonal disconnect fix** via `OverCircle` bias filling.

**Pseudocode:**
```
function BooleanBlotch(input, terrainSmoothing, threshold, thresholdOutOf,
                       minimumThickness, bias):
    maxSpan = max(input.Size.X, input.Size.Y)
    matrix = BooleanBlur(input, terrainSmoothing, 1, 2).output
    for outerPass = 0 to 15:
        // Smooth until stable
        for innerPass = 0 to maxSpan - 1:
            changesAcc = 0
            for r = 1 to terrainSmoothing:
                (matrix, changes) = BooleanBlur(matrix, r, threshold, thresholdOutOf)
                changesAcc += changes
            if changesAcc == 0: break

        // Enforce thickness
        changesAcc = 0
        (matrix, changes) = RetainThickRegions(matrix, true, minimumThickness)
        changesAcc += changes
        changesAcc += DilateThinRegionsInPlaceFull(matrix, true, minimumThickness)
        midFixLandmass = matrix.clone()
        (matrix, changes) = RetainThickRegions(matrix, false, minimumThickness)
        changesAcc += changes
        changesAcc += DilateThinRegionsInPlaceFull(matrix, false, minimumThickness)
        if changesAcc == 0: break

        // If we are stuck and oscillating, bias-fill the difference
        if outerPass >= 8 and outerPass % 4 == 0:
            diff = matrix != midFixLandmass
            for each cell (x, y) where diff:
                OverCircle(matrix, center=(x*1024+512, y*1024+512),
                           radius=minimumThickness*2048,
                           outside=false, action: matrix[cell] = bias)
    return matrix
```

The 16-outer-pass cap is a hard guardrail. The inner loops can also terminate early if no cell changes. The final bias fill prevents land/water corrections from flipping forever by forcibly painting a circular region in the direction of the `bias` parameter.

### 8. Thickness Enforcement (`RetainThickRegions` / `DilateThinRegions`)

`RetainThickRegions` keeps a foreground cell only if an `span × span` square centered on it (which may extend outside the matrix) contains no background cells. It is effectively an erosion that removes thin spikes.

`DilateThinRegions` is the opposite: it finds the thinnest remaining background cells and flips them to foreground. It uses a `cornerMask` that encodes how far from a foreground corner a cell is. The mask value is `1 + width + width - x - y`, with the `(0,0)` corner set to zero (ignored). The algorithm scans each cell, checks which combinations of the four cardinal neighbors are foreground, and writes the appropriate mask values into the four diagonal quadrants. It then flips every cell that has the maximum thinness score.

**Pseudocode for `DilateThinRegionsInPlace`:**
![8. Thickness Enforcement (`RetainThickRegions` / `DilateThinRegions`)](images/Part_07_Chapter_03_Algorithms-Dilate_thin_regions_flowchart.svg)
The loop is repeated by `DilateThinRegionsInPlaceFull` until no more changes occur.

### 9. Contour Extraction (`MatrixUtils.BordersToPoints`)

`BordersToPoints` converts a boolean matrix into a set of closed loops and open paths that trace the boundary between `true` and `false` cells. The algorithm:

1. Computes two signed gradient matrices:
   - `gradientH[x, y] = matrix[x, y] - matrix[x, y-1]` (vertical edge)
   - `gradientV[x, y] = matrix[x, y] - matrix[x-1, y]` (horizontal edge)
   Positive values mean the edge is oriented so that `true` is on the right as the path travels forward.
2. Traces paths by following non-zero gradients, always keeping `true` on the right-hand side.
3. First traces open paths that start at the matrix edge.
4. Then traces internal loops.
5. Zeros out each gradient as it is used so no segment is traced twice.

**Pseudocode:**
```
function BordersToPoints(matrix, mask):
    gradientH = Matrix<sbyte>(matrix.Size)
    gradientV = Matrix<sbyte>(matrix.Size)
    for y:
        for x:
            if mask allows (x-1, y) and (x, y):
                gradientV[x, y] = (matrix[x, y] ? 1 : 0) - (matrix[x-1, y] ? 1 : 0)
            if mask allows (x, y-1) and (x, y):
                gradientH[x, y] = (matrix[x, y] ? 1 : 0) - (matrix[x, y-1] ? 1 : 0)

    paths = []
    function TracePath(sx, sy, direction):
        points = []
        x, y = sx, sy
        points.add((x, y))
        loop:
            move one step in direction
            clear the gradient used by the step
            points.add((x, y))
            R = gradientH[x, y] > 0
            D = gradientV[x, y] < 0
            L = gradientH[x-1, y] < 0
            U = gradientV[x, y-1] > 0
            // Prefer turning left to keep true region on the right
            if direction == R and U: direction = U
            else if direction == D and R: direction = R
            else if direction == L and D: direction = D
            else if direction == U and L: direction = L
            else if R: direction = R
            else if D: direction = D
            else if L: direction = L
            else if U: direction = U
            else: break
        while (x, y) != (sx, sy)
        paths.add(points)

    // Trace open paths from the boundary
    for x = 1 to size.X - 1:
        if gradientV[x, 0] < 0: TracePath(x, 0, D)
        if gradientV[x, size.Y-1] > 0: TracePath(x, size.Y, U)
    for y = 1 to size.Y - 1:
        if gradientH[0, y] > 0: TracePath(0, y, R)
        if gradientH[size.X-1, y] < 0: TracePath(size.X, y, L)

    // Trace remaining loops
    for y:
        for x:
            if gradientH[x, y] > 0: TracePath(x, y, R)
            else if gradientH[x, y] < 0: TracePath(x+1, y, L)
            if gradientV[x, y] < 0: TracePath(x, y, D)
            else if gradientV[x, y] > 0: TracePath(x, y+1, U)

    return paths
```

The result is an array of `int2[]`. For loops, the first and last point are identical; for open paths, they are the two edge-intersection points.

### 10. Path Partitioning and Optimization

After extraction, paths often contain stubs, junctions, and very short loops. `MatrixUtils` provides several utilities to clean them.

#### 10.1 Direction Map Representation

A direction map is a `Matrix<byte>` where each byte is a `DirectionMask` bit field. A bit set in a cell means there is a path link from that cell to its neighbor in the corresponding direction. The path must be bidirectional: if cell A has the `MR` bit, cell B must have the `ML` bit.

#### 10.2 Removing Stubs (`RemoveStubsFromDirectionMapInPlace`)

A stub is a direction link that is not reciprocated. The method iterates every cell, checks every set direction, and clears the link if the neighbor does not have the reverse bit.

#### 10.3 Removing Junctions (`RemoveJunctionsFromDirectionMap`)

A junction is a cell with more than two direction links. The method clones the input, scans for cells where `DirectionMask.Count() > 2`, and clears that cell and all connected links. This splits a complex intersection into separate path endpoints.

#### 10.4 Direction Map to Paths (`DirectionMapToPaths`)

After stub/junction removal, the direction map is a collection of 2-degree paths and isolated loops. `DirectionMapToPaths` traces each path from an endpoint until it cannot continue, and then traces loops by picking the lowest bit direction. It returns both the forward and reverse versions of every path.

#### 10.5 Pruning (`DirectionMapToPathsWithPruning`)

`DirectionMapToPathsWithPruning` repeatedly removes stubs, extracts paths, measures their lengths, and deletes the shortest paths until every remaining path is at least `minimumLength`. The `minimumJunctionSeparation` parameter causes short paths to sever neighboring junctions instead of merging them. The `preserveEdgePaths` flag prevents paths that touch the matrix edge from being pruned.

**Pseudocode:**
```
function DirectionMapToPathsWithPruning(input, minimumLength, minimumJunctionSeparation, preserveEdgePaths):
    links = input.clone()
    while true:
        RemoveStubsFromDirectionMapInPlace(links)
        pointArrays = DirectionMapToPaths(links)
        removeable = preserveEdgePaths
            ? pointArrays where neither endpoint is on the edge
            : pointArrays
        if removeable is empty: return pointArrays
        shortest = min length of removeable
        if shortest >= minimumLength: return pointArrays
        toDelete = []
        for path in removeable where path.length == shortest:
            for point in path:
                toDelete.add(point)
                if path.length < minimumJunctionSeparation:
                    for each neighbor linked from point:
                        toDelete.add(neighbor)
        for point in toDelete:
            links[point] = 0
```

#### 10.6 Masking Paths (`MaskPathPoints`)

`MaskPathPoints` filters a set of point arrays through a boolean mask. It splits sequences where they exit the mask and wraps around looped paths. Segments with fewer than two points are dropped.

### 11. Distance Transforms and Space Shrinkwrapping

#### 11.1 ChebyshevRoom (`MatrixUtils.ChebyshevRoom`)

This computes a Chebyshev distance transform. For each cell, it stores the distance to the nearest opposite-valued cell. Positive values mean the cell is `true` and the distance is to the nearest `false`; negative values mean the opposite. The algorithm seeds the flood fill at all boundary cells (3x3 neighborhoods that contain both values) and propagates outward using 8-directional adjacency.

#### 11.2 DeflateSpace (`MatrixUtils.DeflateSpace`)

`DeflateSpace` is a rough Voronoi shrinkwrap. It identifies each connected background region ("hole"), floods the foreground to assign every foreground cell to its nearest hole, and then produces a `(size + 1)` direction map that marks which of the four cell-to-cell edges separate different hole assignments. This is used to build cliff and river edges that are guaranteed to be topologically safe.

#### 11.3 WalkingDistances (`MatrixUtils.WalkingDistances`)

A Dijkstra distance transform on a boolean passability matrix. It uses `PriorityArray` to extract the closest unprocessed cell and supports a `maxDistance` cutoff. Diagonal steps cost 1448 (1024 * sqrt(2)) and straight steps cost 1024.

### 12. Flood Fill (`MatrixUtils.FloodFill`)

A generic breadth-first propagation primitive. It takes a set of seeds, each with a propagation value `P`. For each cell, it calls `filler(xy, prop)`, which may return an updated `P` to propagate or `null` to stop. The fill expands layer by layer, so `filler` is called in order of increasing distance from the nearest seed. This single method is reused by `ChebyshevRoom`, `DeflateSpace`, and `WalkingDistances`.

**Pseudocode:**
```
function FloodFill(size, seeds, filler, spread):
    current = []
    next = seeds
    while next is not empty:
        swap(current, next)
        next.clear()
        for (source, prop) in current:
            newProp = filler(source, prop)
            if newProp is not null:
                for offset in spread:
                    destination = source + offset
                    if destination in bounds:
                        next.add((destination, newProp))
```

![Extension points diagram](images/Part_07_Chapter_03_Algorithms-extension-hook-diagram-showing-the-interface-s-to-implement-b4a27b.svg)

## Extension Points


The map generator is designed to be extended without modifying these core files:

- **Custom amplitude functions.** Any `Func<int, int>` that maps a wavelength to an integer amplitude can be passed to `FractalNoise` or `SymmetricFractalNoise`. Mods can implement brown noise, blue noise, or tile-size-aware spectra.
- **Custom symmetry groups.** `Symmetry.RotateAndMirrorPointAround` and the `WMirror` wrapper are the canonical primitives. A generator could extend the family to support non-rectangular or translation symmetries, but it would need to add a new helper rather than reusing these existing ones.
- **Post-processing masks.** After `BooleanBlotch`, a generator can apply any additional `Matrix<bool>` kernel through `KernelDilateOrErode`, `ChebyshevRoom`, or `DeflateSpace` before contour extraction.
- **Custom path optimizers.** `DirectionMapToPathsWithPruning` accepts `minimumLength`, `minimumJunctionSeparation`, and `preserveEdgePaths`. More elaborate criteria can be applied by calling `DirectionMapToPaths` and implementing a custom pruning loop.
- **Debug visualization.** The `ColorDump2d`, `EnumDump2d`, `Dump2d`, and `GraphPoints` methods are intended for development and can be enabled to print intermediate matrices to the console.

![Common pitfalls  guardrails diagram](images/Part_07_Chapter_03_Algorithms-checklist-infographic-style-diagram-summarizing-the-top-pitf-fb069e.svg)

## Common Pitfalls / Guardrails


- **Determinism.** Every algorithm here is deterministic given a seed. The `MersenneTwister` must be created with the same seed on all clients; consuming it in a different order between client and server will desync the map.
- **Parameter validity.** `BooleanBlur` throws if `threshold < 1`, `thresholdOutOf < 1`, or `threshold * 2 < thresholdOutOf`. `ClumpinessAmplitude` requires `clumpiness >= 0`. `SymmetricFractalNoise` requires `rotations >= 1`. Always validate YAML before calling.
- **Boundary clamping.** `IntegerInterpolate`, `KernelFilter`, and `BooleanBlur` clamp out-of-bounds coordinates to the nearest edge cell. This means the map border is never sampled from outside; large features can appear to "flatten" near the edge.
- **Rotation precision.** `RotateAndMirrorPointAround` uses `WAngle` cos/sin values, which are integer approximations. The comment notes that accuracy could be improved with dedicated lookup tables for exotic rotation counts.
- **Isometric mirroring.** `WMirror.ForCPos()` adds a 2-step offset for `RectangularIsometric` grids. Forgetting to use `WMirror` and using raw `Mirror` values in `CPos` space will produce asymmetric maps on isometric tile sets.
- **Loop-vs-open-path handling.** `BordersToPoints` returns loops with identical start/end points. Downstream consumers must check `pointArray[0] == pointArray[^1]` to detect loops.
- **Performance of `BooleanBlotch`.** The outer loop is capped at 16 passes, but the inner smoothing can run `maxSpan` times. On very large maps or very high `terrainSmoothing` values, the cleanup can become the dominant cost of generation.
- **Memory alignment.** The symmetric fractal noise template is `2 * max(size) + 2` on each side. For a 256x256 map, the template is 514x514 integers, which is large but manageable; for very large custom maps, watch memory pressure.

## What to read next

- [Part 7.2 — Map Generation Data Structures](Part_07_Chapter_02_Data_Structures.md) for the `Matrix` and `CellLayer` containers these algorithms operate on.
- [Part 7.4 — Terraformer](Part_07_Chapter_04_Terraformer.md) for the orchestrator that calls these algorithms in sequence.
- [Part 7.5 — MultiBrush and Tile Placement](Part_07_Chapter_05_MultiBrush.md) for the brush system that stamps the final tile output.

## Summary

This chapter documents the low-level algorithmic primitives that the OpenRA procedural map generator uses to synthesize terrain, roads, rivers, resource patches, and base sites.

After reading this chapter, you should be able to:

- **YAML parameters are read** by the higher-level generator (e.g., `Terraformer` or `MapGenerator`). Values such as `featureSize`, `rotations`, `mirror`, `terrainSmoothing`, `minimumThickness`, `threshold`, and `thresholdOutOf` are passed as arguments.

If any of the concepts above feel unclear, review the relevant section before continuing. For source files and further reading, see the References section.


## References

- Source files:
  - `OpenRA.Mods.Common/MapGenerator/NoiseUtils.cs`
  - `OpenRA.Mods.Common/MapGenerator/MatrixUtils.cs`
  - `OpenRA.Mods.Common/MapGenerator/Symmetry.cs`
  - `OpenRA.Mods.Common/MapGenerator/Direction.cs`
- Related engine files:
  - `OpenRA.Game/Map/CellLayer.cs`
  - `OpenRA.Mods.Common/MapGenerator/Matrix.cs`
  - `OpenRA.Support/MersenneTwister.cs`
  - `OpenRA.Mods.Common/MapGenerator/CellLayerUtils.cs`
- External references:
  - Ken Perlin, "Improving Noise", SIGGRAPH 2002 (fractal noise / octave summation).
  - Standard references on binary morphology and distance transforms for the `BooleanBlotch` and `ChebyshevRoom` operations.