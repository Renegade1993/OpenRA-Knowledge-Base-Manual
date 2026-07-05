# Chapter 4.2 — WorldRenderer

## Purpose

`WorldRenderer` turns the simulation world into a rendered frame. It collects [renderables](../appendices/Appendix_A_Glossary.md) from actors, effects, and the [order generator](../appendices/Appendix_A_Glossary.md), sorts them, prepares them for the GPU, and draws them in the correct order: terrain, actors, above-world, shroud, overlay, annotations, and post-processing. This chapter explains the render pipeline, [palette](../appendices/Appendix_A_Glossary.md) management, and the interfaces that traits implement to participate in it.

![Mental model diagram](images/Part_04_Chapter_02_WorldRenderer-learning-objectives-summary-diagram-or-concept-map-showing-h-fe332a.svg)

## Mental Model

Think of `WorldRenderer` as a stage director preparing one photograph of a live play.

- **The stage floor** is the terrain layer. It is painted first because everything else stands on top of it.
- **The actors** (units and buildings) are the performers. They are sorted by their depth on stage so that an actor standing in front of another covers the one behind. The engine uses a stable sort so that two actors at the same depth do not flicker back and forth.
- **Special effects** (water wakes, projectiles, etc.) sit on a transparent layer just above the stage floor but below the fog.
- **The fog machine** (shroud) hides parts of the stage the audience is not allowed to see.
- **The director's notes** (selection brackets, health bars, target lines) are drawn on top of the fog so they remain readable.
- **Post-processing passes** are like Instagram filters applied at specific points between layers.

This mental model explains why the draw order is rigid (the floor must exist before the actors), why `IRenderAboveShroud` exists (notes must stay visible even when the stage is foggy), and why `PrepareRenderables` is separate from `Draw` (the director casts the scene before taking the photograph). The actors are produced by the ECS described in [Part 1.1 — Entity-Component-System (ECS) and Actor Lifecycle](Part_01_Chapter_01_ECS.md), their rules come from [Part 2.4 — Rulesets, Actors, and Weapons](Part_02_Chapter_04_Rules_Weapons.md), and the orders that generate preview renderables are described in [Part 4.4 — Viewport and Input](Part_04_Chapter_04_Viewport_Input.md).

## Learning Objectives


After studying this chapter, you should be able to:

- Explain the phases of WorldRenderer.Draw and the purpose of each layer.
- Describe the renderable interfaces (IRenderable, IRenderAboveShroud, etc.) and when to use each.
- Trace how renderables are collected, sorted, and prepared each frame.
- Explain how palette management and modifiers work in the world renderer.
- Configure post-processing passes and depth-buffer options in YAML.
- Implement a custom renderable trait using the correct interface.
- Explain why stable Z-sort matters and how overlay grouping preserves draw behavior.
- Describe the post-processing pass timing and the depth-buffer options.

## Practical Example: Drawing a Range Circle When a Unit Is Selected

Suppose you want a unit to display a circular range indicator whenever it is selected. The cleanest way to do this is to implement `IRenderAnnotationsWhenSelected`, which draws after the shroud and overlay layers and is only visible when the actor is selected.

### YAML wiring

Add the trait to the actor rule in `mods/<mod>/rules/vehicles.yaml`:

```yaml
MYTANK:
    Inherits: ^Vehicle
    RenderRangeCircle:
        Color: FFFF0080
        Width: 2
        BorderColor: 00000080
        BorderWidth: 4
```

`RenderRangeCircle` is already provided by `OpenRA.Mods.Common`. If you want a custom version, you can implement it like this:

```csharp
using System.Collections.Generic;
using OpenRA.Graphics;
using OpenRA.Mods.Common.Graphics;
using OpenRA.Primitives;
using OpenRA.Traits;

namespace OpenRA.Mods.MyMod.Traits
{
    public class MyRangeCircleInfo : TraitInfo<MyRangeCircle> { }

    public class MyRangeCircle : IRenderAnnotationsWhenSelected
    {
        public IEnumerable<IRenderable> RenderAnnotations(Actor self, WorldRenderer wr)
        {
            yield return new RangeCircleAnnotationRenderable(
                self.CenterPosition,
                new WDist(1024 * 5),   // 5 cells
                0,
                Color.Yellow,
                2,
                Color.Black,
                4);
        }

        // Opt out of spatial partitioning so the circle still renders
        // when the unit is near the edge of the viewport.
        bool IRenderAnnotationsWhenSelected.SpatiallyPartitionable => false;
    }
}
```

`WorldRenderer` collects this renderable during `GenerateAnnotationRenderables`, then `DrawAnnotations` draws it after the shroud and overlay layers. The range circle stays visible through fog because it is an annotation, while the unit itself is hidden if the cell is shrouded.

## Files

| File | Responsibility |
| :---- | :---- |
| `OpenRA.Game/Graphics/WorldRenderer.cs` | Main world rendering coordinator. |
| `OpenRA.Game/Graphics/Renderable.cs` | Base `IRenderable` interface and helpers. |
| `OpenRA.Game/Graphics/SpriteRenderable.cs` | Simple sprite-based renderable. |
| `OpenRA.Game/Graphics/TargetLineRenderable.cs` | Renderable for target lines. |
| `OpenRA.Mods.Common/Traits/World/TerrainRenderer.cs` | Renders the terrain layer. |
| `OpenRA.Game/Graphics/TerrainSpriteLayer.cs` | Batches terrain tiles into a sprite layer. |
| `OpenRA.Game/Traits/TraitsInterfaces.cs` | Render-related trait interfaces. |
| `OpenRA.Game/Graphics/HardwarePalette.cs` | GPU palette management. |
| `OpenRA.Game/Effects/IEffect.cs` | `IEffect` and `IEffectAboveShroud` interfaces. |
| `OpenRA.Game/Graphics/Viewport.cs` | Viewport used for culling and coordinate transforms. |
| `OpenRA.Game/Traits/TraitsInterfaces.cs` | Defines `PostProcessPassType` and `IRenderPostProcessPass`. |

![Architecture diagram](images/Part_04_Chapter_02_WorldRenderer-architecture-diagram-showing-the-main-classes-interfaces-and-9161e6.svg)

## Architecture


### Render phases

`WorldRenderer.Draw` executes in phases, with post-processing hooks inserted at well-defined boundaries:

1. **Scissor and depth setup** — a scissor rectangle is enabled so nothing outside the world [viewport](../appendices/Appendix_A_Glossary.md) is drawn. If the map grid uses a depth buffer, it is enabled now.
2. **Terrain** — the base map tiles are drawn first. `IRenderTerrain.RenderTerrain` draws the tile layers; for the default mod this is handled by `TerrainRenderer` using `TerrainSpriteLayer`.
3. **Actors and effects** — all on-screen actors, the world actor, the render player's player actor, unpartitioned effects, and on-screen partitioned effects are collected as `IRenderable` objects, sorted by Z, prepared, and drawn. The order generator also contributes renderables in this phase.
4. **Above-world** — `IRenderAboveWorld` traits draw directly above the world layer but below shroud. This layer is not sorted; it is drawn in trait order after the actor layer.
5. **Post-processing after world** — passes of type `AfterWorld` run before the shroud layer.
6. **Shroud** — `IRenderShroud` traits draw the fog of war and explored-area overlay. The depth buffer is disabled before overlays so that 2D UI elements are not depth-tested.
7. **Overlay** — selection brackets, target lines, health bars, range circles, and other UI elements drawn by `IRenderAboveShroud` and `IRenderAboveShroudWhenSelected` traits, plus effects that implement `IEffectAboveShroud`. These are grouped by type for historical draw order.
8. **Post-processing after shroud** — passes of type `AfterShroud` run between the overlay and annotation layers.
9. **Annotations** — `DrawAnnotations` draws text labels, debug geometry, and screen-map overlays. `IRenderAnnotations` and `IRenderAnnotationsWhenSelected` traits contribute here. Anti-aliasing is enabled for this pass.
10. **Post-processing after annotations** — passes of type `AfterAnnotations` run after annotations but before the world buffer is composited into the UI.

Annotations are deliberately separated from overlays because they are drawn with anti-aliasing and are typically translucent or text-heavy, so they should not be obscured by shroud or clipped by the same scissor rules as world geometry.

<!-- DEV-NOTE [visual-aid]: renderable sorting and depth diagram. Left side: a stack of layers (terrain -> actors sorted by Y+Z -> above-world -> shroud -> overlays grouped by type -> annotations). Right side: the composite key for stable sort: high 32 bits = RenderableZPositionComparisonKey(Y+Z+ZOffset), low 32 bits = insertion index. Show the depth buffer on/off toggle between phases and the scissor rectangle around the viewport. -->

### Renderable types

Traits can participate in rendering through several interfaces:

- `IRenderable` — returns world renderables for the actor. These are sorted by Z and drawn before the shroud. Most [sprite](../appendices/Appendix_A_Glossary.md) traits implement this.
- `IRenderAboveShroud` — returns renderables drawn after the shroud layer. Useful for selection brackets, health bars, range circles, and target lines that should remain visible under fog.
- `IRenderAboveShroudWhenSelected` — returns renderables only when the actor is selected. The selection-specific version of `IRenderAboveShroud`.
- `IRenderAnnotations` — returns annotation renderables (text, debug geometry). Annotations are drawn with anti-aliasing after the overlay layer.
- `IRenderAnnotationsWhenSelected` — annotations only when selected.
- `IRenderAboveWorld` — draws directly above the world layer but below shroud. This is not sorted by Z and is intended for effects like water wakes or projectiles that must sit above terrain but below shroud.
- `IRenderShroud` — draws the shroud overlay.
- `IRenderPostProcessPass` — full-screen post-processing pass with a specific timing.

Effects participate through parallel interfaces: `IEffect` (rendered in the actor layer), `IEffectAboveShroud` (overlay layer), and `IEffectAnnotation` (annotation layer). Effects are not spatially partitioned unless they opt into the screen map.

### Spatial partitioning

`World.ScreenMap` keeps track of which actors and effects are on screen. `WorldRenderer` only renders actors inside the viewport, reducing per-frame work. The `SpatiallyPartitionable` flag on render interfaces allows traits to opt out of culling when they need to render even off-screen (for example, long-range target lines).

### Palette management

`WorldRenderer` initializes palettes during construction and refreshes them each frame to apply `IPaletteModifier` effects. `PaletteReference` objects are cached so sequences can look up palette indices quickly.

The palette lifecycle in `WorldRenderer`:

1. **Construction** — every world trait implementing `ILoadsPalettes` calls `LoadPalettes(this)` and registers immutable palettes via `WorldRenderer.AddPalette`. Traits that implement `ILoadsPlayerPalettes` create per-player palettes later via `UpdatePalettesForPlayer`.
2. **Palette registration** — `AddPalette` adds an `ImmutablePalette` to the internal `HardwarePalette`. If `AllowModifiers` is true, a mutable copy is also kept. If the palette texture height changes, `PaletteInvalidated` is raised so that cached `PaletteReference` objects can be re-resolved.
3. **Palette reference cache** — `Palette(string name)` returns a cached `PaletteReference` containing the `IPalette`, the GPU texture index, and a reference to the `HardwarePalette`. This avoids string lookups and dictionary lookups in the hot render loop.
4. **Per-frame refresh** — `PrepareRenderables` calls `RefreshPalette`, which runs all `IPaletteModifier` traits, copies the mutable palettes into the GPU buffer, and calls `Renderer.SetPalette`. The mutable palettes are then reset to their original values so modifiers can be applied again next frame.
5. **Color shifts** — `SetPaletteColorShift` stores a per-palette HSV shift in the `ColorShifts` texture. This is used for effects like desert palette shifts or team color overlays.

![Data flow  code path diagram](images/Part_04_Chapter_02_WorldRenderer-sequence-flow-diagram-tracing-the-execution-path-from-trigge-035864.svg)

## Data Flow / Code Path


### Construction

```csharp
internal WorldRenderer(ModData modData, World world)
{
    World = world;
    TileSize = World.Map.Rules.TerrainInfo.TileSize;
    TileScale = World.Map.Grid.TileScale;
    Viewport = new Viewport(this, world.Map);

    createPaletteReference = CreatePaletteReference;

    var mapGrid = modData.GetOrCreate<MapGrid>();
    enableDepthBuffer = mapGrid.EnableDepthBuffer;

    foreach (var pal in world.TraitDict.ActorsWithTrait<ILoadsPalettes>())
        pal.Trait.LoadPalettes(this);

    Player.SetupRelationshipColors(world.Players, world.LocalPlayer, this, true);

    palette.Initialize();

    TerrainLighting = world.WorldActor.TraitOrDefault<ITerrainLighting>();
    renderers = world.WorldActor.TraitsImplementing<IRenderer>().ToArray();
    terrainRenderer = world.WorldActor.TraitOrDefault<IRenderTerrain>();

    debugVis = Exts.Lazy(world.WorldActor.TraitOrDefault<DebugVisualizations>);

    postProcessPasses = world.WorldActor.TraitsImplementing<IRenderPostProcessPass>().ToArray();
}
```

The constructor creates the `Viewport`, loads static palettes, initializes the `HardwarePalette`, and caches the `IRenderer`, `IRenderTerrain`, and `IRenderPostProcessPass` traits. The `enableDepthBuffer` flag is read from `MapGrid` and is used throughout `Draw` to decide when to enable, clear, or disable the depth buffer.

### Preparing renderables

```csharp
public void PrepareRenderables()
{
    if (World.WorldActor.Disposed)
        return;

    RefreshPalette();

    onScreenActors.UnionWith(World.ScreenMap.RenderableActorsInBox(Viewport.TopLeft, Viewport.BottomRight));

    GenerateRenderables();
    GenerateOverlayRenderables();
    GenerateAnnotationRenderables();

    onScreenActors.Clear();
}
```

`PrepareRenderables` is called once per frame before `Draw`. It refreshes palettes, collects the set of on-screen actors, and then generates the three prepared renderable lists. The `onScreenActors` hash set is reused to avoid allocation; it is cleared after generation.

### Generating world renderables

```csharp
void GenerateRenderables()
{
    foreach (var actor in onScreenActors)
        renderablesBuffer.AddRange(actor.Render(this));

    renderablesBuffer.AddRange(World.WorldActor.Render(this));

    if (World.RenderPlayer != null)
        renderablesBuffer.AddRange(World.RenderPlayer.PlayerActor.Render(this));

    if (World.OrderGenerator != null)
        renderablesBuffer.AddRange(World.OrderGenerator.Render(this, World));

    // Unpartitioned effects
    foreach (var e in World.UnpartitionedEffects)
        renderablesBuffer.AddRange(e.Render(this));

    // Partitioned, currently on-screen effects
    foreach (var e in World.ScreenMap.RenderableEffectsInBox(Viewport.TopLeft, Viewport.BottomRight))
        renderablesBuffer.AddRange(e.Render(this));

    // Renderables must be ordered using a stable sorting algorithm to avoid flickering artefacts
    if (renderablesKeysBuffer.Length < renderablesBuffer.Count)
        renderablesKeysBuffer = new long[Exts.NextPowerOf2(renderablesBuffer.Count)];
    for (var i = 0; i < renderablesBuffer.Count; i++)
        renderablesKeysBuffer[i] = ((long)RenderableZPositionComparisonKey(renderablesBuffer[i]) << 32) + i;
    var keys = renderablesKeysBuffer.AsSpan(0, renderablesBuffer.Count);
    keys.Sort(CollectionsMarshal.AsSpan(renderablesBuffer));

    foreach (var renderable in renderablesBuffer)
        preparedRenderables.Add(renderable.PrepareRender(this));

    renderablesBuffer.Clear();
}
```

World renderables come from on-screen actors, the world actor, the render player's player actor, the current order generator, and both unpartitioned and partitioned effects. They are then sorted using a stable sort with a composite key, and finally prepared into `IFinalizedRenderable` objects that can be drawn quickly.

### Drawing

```csharp
public void Draw()
{
    if (World.WorldActor.Disposed)
        return;

    debugVis.Value?.UpdateDepthBuffer();

    var bounds = Viewport.GetScissorBounds(World.Type != WorldType.Editor);
    Game.Renderer.EnableScissor(bounds);

    if (enableDepthBuffer)
        Game.Renderer.Context.EnableDepthBuffer();

    terrainRenderer?.RenderTerrain(this, Viewport);

    Game.Renderer.Flush();

    for (var i = 0; i < preparedRenderables.Count; i++)
        preparedRenderables[i].Render(this);

    if (enableDepthBuffer)
        Game.Renderer.ClearDepthBuffer();

    ApplyPostProcessing(PostProcessPassType.AfterActors);

    World.ApplyToActorsWithTrait<IRenderAboveWorld>((actor, trait) =>
    {
        if (actor.IsInWorld && !actor.Disposed)
            trait.RenderAboveWorld(actor, this);
    });

    if (enableDepthBuffer)
        Game.Renderer.ClearDepthBuffer();

    ApplyPostProcessing(PostProcessPassType.AfterWorld);

    World.ApplyToActorsWithTrait<IRenderShroud>((actor, trait) => trait.RenderShroud(this));

    if (enableDepthBuffer)
        Game.Renderer.Context.DisableDepthBuffer();

    Game.Renderer.DisableScissor();

    // HACK: Keep old grouping behaviour
    var groupedOverlayRenderables = preparedOverlayRenderables.GroupBy(prs => prs.GetType());
    foreach (var g in groupedOverlayRenderables)
        foreach (var r in g)
            r.Render(this);

    ApplyPostProcessing(PostProcessPassType.AfterShroud);

    Game.Renderer.Flush();
}
```

`Draw` is called after `PrepareRenderables`. It sets up scissor and depth state, draws terrain, draws the sorted actor/effect renderables, clears the depth buffer before above-world and shroud layers, and then draws overlays grouped by type. `DrawAnnotations` is called separately from `Game` after `Draw` so that annotations can be drawn with anti-aliasing and without the world scissor.

![Configuration (yaml) diagram](images/Part_04_Chapter_02_WorldRenderer-annotated-yaml-snippet-diagram-showing-the-key-fields-and-ho-6a1b98.svg)

## Configuration (YAML)


### Depth buffer

The map grid can enable a depth buffer for isometric mods:

```yaml
MapGrid:
    EnableDepthBuffer: true
```

When enabled, the depth buffer is used during the terrain and actor phases to sort isometric sprites by depth. The depth buffer is cleared before the above-world and shroud layers so that overlays are not incorrectly depth-tested. Top-down mods typically leave this disabled because Y-based Z-sort is sufficient.

### Post-processing passes

A post-processing pass is a world trait:

```yaml
World:
    MyPostProcessPass:
```

The trait implements `IRenderPostProcessPass` and specifies when it runs via the `Type` property:

- `AfterActors` — after the actor/effect layer but before above-world.
- `AfterWorld` — after above-world but before shroud.
- `AfterShroud` — after overlays but before annotations.
- `AfterAnnotations` — after annotations but before the world buffer is composited into the UI.

The engine flushes the current batch before invoking each pass, so passes can bind the current framebuffer or render their own full-screen geometry without interfering with batched sprites.

### Palette traits

Palettes are loaded by world traits:

```yaml
World:
    PaletteFromFile:
        Name: terrain
        Filename: temperat.pal
    PlayerColorPalette:
        BasePalette: player
        BasePaletteName: player
        RemapIndex: 16, 17, 18, 19, 20, 21, 22, 23
```

`AllowModifiers: true` on a palette causes `WorldRenderer` to keep a mutable copy that can be modified each frame by `IPaletteModifier` traits. Modifiers are applied in `RefreshPalette` before the GPU palette texture is updated.

## Interconnectivity

- **Depends on:** [Part 1.1 — Entity-Component-System (ECS) and Actor Lifecycle](Part_01_Chapter_01_ECS.md), [Part 1.3 — World, OrderManager, and Orders](Part_01_Chapter_03_World_Orders.md), [Part 2.2 — Manifest and Mod Metadata](Part_02_Chapter_02_Manifest.md), [Part 2.3 — FieldLoader](Part_02_Chapter_03_FieldLoader.md), [Part 2.4 — Rulesets, Actors, and Weapons](Part_02_Chapter_04_Rules_Weapons.md), [Part 4.1 — Renderer, Sheet, and Sprite](Part_04_Chapter_01_Renderer.md), [Part 4.3 — Widgets and Chrome](Part_04_Chapter_03_Widgets.md), [Part 4.4 — Viewport and Input](Part_04_Chapter_04_Viewport_Input.md), [Part 6.3 — Virtual File System](Part_06_Chapter_03_VFS.md).
- **Used by:** [Part 4.4 — Viewport and Input](Part_04_Chapter_04_Viewport_Input.md), [Part 5.3 — Music](Part_05_Chapter_03_Music.md), [Part 7.8 — Random Map Generator Extension Points](Part_07_Chapter_08_Extension_Points.md) (RMG maps render like normal maps), Part 8 (bot orders produce target-line renderables), [Part 1.2 — Activity System](Part_01_Chapter_02_Activities.md), [Part 10.3 — Porting, Modding, and Developer Workflows](Part_10_Chapter_03_Port_And_Modding.md).

![Algorithms diagram](images/Part_04_Chapter_02_WorldRenderer-algorithm-diagram-or-pseudocode-flowchart-for-the-non-trivia-5983ed.svg)

## Algorithms


### Stable Z sort

Renderables are sorted by a composite key:

```csharp
public static readonly Func<IRenderable, int> RenderableZPositionComparisonKey =
    r => r.Pos.Y + r.Pos.Z + r.ZOffset;
```

The Y coordinate, Z height, and explicit Z offset are combined so that sprites lower on the screen are drawn later. Because the sort key can be identical for many renderables (for example, units standing on the same cell), the original index `i` is packed into the low 32 bits of the sort key. This makes the sort stable, which is critical: an unstable sort would cause sprites with equal Z to swap order every frame, producing visible flicker. The sort uses `CollectionsMarshal.AsSpan` and `keys.Sort` to sort both the keys and the renderables in place without extra allocations.

### On-screen actor culling

`World.ScreenMap` partitions actors spatially. `RenderableActorsInBox` returns only actors whose bounds intersect the viewport. This is much faster than iterating over every actor in the world. The culling is conservative: an actor whose bounding box touches the viewport is rendered even if its actual sprite is not visible, so render traits must still clip their own output if necessary.

### Overlay grouping

Overlay renderables are grouped by type to maintain historical draw behavior:

```csharp
var groupedOverlayRenderables = preparedOverlayRenderables.GroupBy(prs => prs.GetType());
foreach (var g in groupedOverlayRenderables)
    foreach (var r in g)
        r.Render(this);
```

Grouping by `GetType()` means all health bars of one type are drawn together, then all selection brackets of another type, and so on. This preserves the original draw order from before the overlay renderables were batched and prepared. Without grouping, interleaving different overlay types could cause one type to draw on top of another in an inconsistent order depending on the spatial sort of the underlying actors.

### Palette refresh

Each frame, palette modifiers are applied:

```csharp
public void RefreshPalette()
{
    palette.ApplyModifiers(World.WorldActor.TraitsImplementing<IPaletteModifier>());
    Game.Renderer.SetPalette(palette);
}
```

This allows effects such as flashing, color cycling, or faction tinting to update the GPU palette without changing sprite data. `ApplyModifiers` modifies the `MutablePalette` copies, uploads the result, and then resets the mutable palettes back to their originals so that each frame starts from a known baseline.

### Renderable collection

`GenerateRenderables` pulls renderables from five sources:

1. On-screen actors (`actor.Render(this)`).
2. The world actor (`World.WorldActor.Render(this)`), which holds world-level render traits.
3. The render player's player actor, if any.
4. The current order generator (`World.OrderGenerator.Render(this, World)`), used for cursors, target lines, and preview sprites.
5. Effects, both unpartitioned and partitioned.

`GenerateOverlayRenderables` and `GenerateAnnotationRenderables` use `World.ApplyToActorsWithTrait<T>` to iterate all actors with the relevant interface, then additionally process selected actors (for the `WhenSelected` variants) and effects that implement the matching effect interface. This three-stage collection keeps the main actor layer sorted by Z while letting overlays and annotations bypass the Z-sort.

### Depth buffer usage

When `MapGrid.EnableDepthBuffer` is true, the depth buffer is enabled during the terrain and actor phases. The depth value for each sprite is derived from its world position and any per-pixel depth offset provided by a secondary `SpriteWithSecondaryData`. The depth buffer is cleared twice during `Draw`: once after the actor layer (so above-world effects do not depth-fight with actors) and once after the above-world layer (so the shroud and overlays are not depth-tested). It is disabled before overlays are drawn because UI indicators should always be visible regardless of world depth.

![Extension points diagram](images/Part_04_Chapter_02_WorldRenderer-extension-hook-diagram-showing-the-interface-s-to-implement-b4a27b.svg)

## Extension Points


### Add a custom renderable trait

Implement `IRenderable` on an actor trait. The `Render` method returns one or more `IRenderable` objects. Implement `PrepareRender` to convert them to `IFinalizedRenderable` for the GPU. Most traits do not implement `IRenderable` directly; instead they return one of the built-in renderable types such as `SpriteRenderable`.

### Draw above shroud

Implement `IRenderAboveShroud` to draw after the shroud layer. This is useful for selection indicators, range circles, and target lines. Use `IRenderAboveShroudWhenSelected` if the overlay should only appear when the actor is selected.

### Draw annotations

Implement `IRenderAnnotations` to draw text or debug graphics. Annotations are drawn with anti-aliasing enabled. Use `IRenderAnnotationsWhenSelected` for selection-only annotations.

### Add a post-processing pass

Implement `IRenderPostProcessPass` and add it as a world trait. The pass can render a full-screen effect using the framebuffer. Choose the `PostProcessPassType` carefully: `AfterWorld` is the most common for full-screen tinting, while `AfterAnnotations` is useful for effects that must include the UI overlays.

### Custom terrain renderer

Implement `IRenderTerrain` on a world trait to replace the default tile rendering. The default implementation uses `TerrainSpriteLayer` and `TerrainRenderer`.

![Common pitfalls  guardrails diagram](images/Part_04_Chapter_02_WorldRenderer-checklist-infographic-style-diagram-summarizing-the-top-pitf-fb069e.svg)

## Common Pitfalls / Guardrails


- **Render thread only:** all rendering code must run on the main thread. Do not create renderables from background threads.
- **Disposal:** `WorldRenderer` is disposable. It must be cleaned up when the world is destroyed; it also disposes the `World` it owns.
- **Palette invalidation:** if you add palettes after initialization, raise `PaletteInvalidated` so that sequences can re-resolve their palette references.
- **Renderable lifetime:** `IRenderable` objects are created each frame. Do not cache them between frames unless they are independent of world state.
- **Sorting cost:** very large numbers of renderables increase sort cost. Use spatial partitioning to keep the count low.
- **Depth buffer:** enabling the depth buffer changes the draw order semantics. Isometric mods need it; top-down mods typically do not. Do not rely on depth sorting for overlays, because the depth buffer is cleared before the overlay layer.
- **Overlay grouping:** if you add a new overlay type, be aware that `GroupBy(prs => prs.GetType())` will draw all instances of your type together. If your overlay depends on being drawn relative to another type, you may need to coordinate the order or choose a different render interface.
- **PrepareRender before Draw:** `Draw` expects `PrepareRenderables` to have been called first. Calling `Draw` without preparation will result in empty render lists.
- **Scissor and annotations:** annotations are drawn outside `WorldRenderer.Draw`, after the scissor has been disabled. If your annotation needs world clipping, compute the clip rectangle yourself from `Viewport.GetScissorBounds`.

## What to read next

- [Part 4.1 — Renderer, Sheet, and Sprite](Part_04_Chapter_01_Renderer.md) for the sprite, sheet, and palette foundations that feed the world renderer.
- [Part 4.4 — Viewport and Input](Part_04_Chapter_04_Viewport_Input.md) for the camera and order-generator context that drives world rendering.
- [Part 6.5 — Asset Loaders](Part_06_Chapter_05_Asset_Loaders.md) for how sprite, sequence, and video data are loaded into renderables.

## Summary

This chapter explains how `WorldRenderer` turns the simulation world into a rendered frame.

After reading this chapter, you should be able to:

- Trace the layered render pipeline from terrain through actors/effects, above-world, post-processing, shroud, overlays, annotations, and final post-processing.
- Choose the correct renderable interface (`IRenderable`, `IRenderAboveShroud`, `IRenderAnnotations`, etc.) for a trait.
- Explain why `PrepareRenderables` is split from `Draw` and why stable Z-sort matters.
- Configure depth buffer and post-processing passes in YAML.
- Implement a custom renderable trait using `IRenderAnnotationsWhenSelected` or a similar interface.

If any of the concepts above feel unclear, review the relevant section before continuing. For source files and further reading, see the References section.


## References

- `OpenRA.Game/Graphics/WorldRenderer.cs` — world renderer.
- `OpenRA.Game/Graphics/Renderable.cs` — renderable interface.
- `OpenRA.Game/Graphics/SpriteRenderable.cs` — sprite renderable.
- `OpenRA.Game/Graphics/TargetLineRenderable.cs` — target line renderable.
- `OpenRA.Mods.Common/Traits/World/TerrainRenderer.cs` — terrain renderer.
- `OpenRA.Game/Graphics/TerrainSpriteLayer.cs` — terrain sprite batching.
- `OpenRA.Game/Traits/TraitsInterfaces.cs` — render interfaces.
- `OpenRA.Game/Graphics/HardwarePalette.cs` — GPU palette.
- `OpenRA.Game/Effects/IEffect.cs` — effect interfaces.
- `OpenRA.Game/Graphics/Viewport.cs` — viewport and culling.


### External resources

- [OpenRA sprite sequences](https://docs.openra.net/en/release/sprite-sequences/)
- [OpenRA playtest docs](https://docs.openra.net/en/playtest/)