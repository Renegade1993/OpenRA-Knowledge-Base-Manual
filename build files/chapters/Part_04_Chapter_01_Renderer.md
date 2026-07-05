# Chapter 4.1 — Renderer, Sheet, and Sprite

## Purpose

OpenRA's graphics engine is a 2D [sprite](../appendices/Appendix_A_Glossary.md) renderer built on top of a thin platform abstraction. It uploads sprite frames to GPU [sheets](../appendices/Appendix_A_Glossary.md), draws them as textured quads, supports indexed ([palette](../appendices/Appendix_A_Glossary.md)) and true-color sprites, and applies blend modes. This chapter explains the core renderer interfaces, the `Sheet`/`Sprite` model, the palette system, and how the CPU-side game loop drives the GPU frame by frame.

![Mental model diagram](images/Part_04_Chapter_01_Renderer-learning-objectives-summary-diagram-or-concept-map-showing-h-fe332a.svg)

## Mental Model

Think of the renderer as an industrial print shop that produces a flip-book of every frame.

- **The artist** (mod author) creates individual frames as sprites and sequences in YAML.
- **The print shop** (`SpriteCache` and `SheetBuilder`) packs those frames onto large sheets of paper (GPU texture atlases) so they can be printed in a single pass.
- **The colorist** (`HardwarePalette` and palette traits) keeps a tray of indexed inks; indexed sprites are just numbered dents on a sheet, and the palette decides which real color fills each dent.
- **The press operator** (`Renderer` / `SpriteRenderer`) runs the sheets through the press in a strict order: `BeginFrame` sets up the shop, `BeginWorld` loads the world canvas, `BeginUI` switches to the UI canvas, and `EndFrame` presents the final page to the player.
- **The shop manager** (world and UI code) decides which sprites appear where, which palette row to use, and which blend mode (transparent ink, additive ink, etc.) applies.

This mental model explains why the engine cares so much about batching (draw every sprite that shares the same sheet and palette before changing paper), why UV insets exist (so the press does not accidentally smudge a neighboring frame), and why the world and UI are rendered separately (they use different scaling, projection, and depth settings). The sequence data that points the renderer at a sprite comes from [Part 6.5 — Asset Loaders](Part_06_Chapter_05_Asset_Loaders.md), the rules that bind it to an actor live in [Part 2.4 — Rulesets, Actors, and Weapons](Part_02_Chapter_04_Rules_Weapons.md), and the trait that actually produces renderables is part of the ECS described in [Part 1.1 — Entity-Component-System (ECS) and Actor Lifecycle](Part_01_Chapter_01_ECS.md).

## Learning Objectives


After studying this chapter, you should be able to:

1. Describe the renderer stack from game code through `Renderer`, `SpriteRenderer`, and the platform abstraction to the GPU.
2. Explain the `Sheet`/`Sprite` model and why sprite packing reduces draw calls.
3. Distinguish indexed (palette) sprites from true-color sprites and explain how `HardwarePalette` works.
4. Trace a sprite frame from asset file through `SpriteCache` to a GPU sheet upload.
<!-- DEV-NOTE [tooling]: Khronos GLSL reference: https://www.khronos.org/opengl/wiki/OpenGL_Shading_Language — reference for the shader dialect used by the engine. -->
5. Configure renderer constants, shader references, and palette definitions in YAML.
6. Identify common rendering pitfalls such as texture bleeding, sheet size limits, and threading violations.
7. Explain the purpose of UV inset and channel packing for indexed sprites.
8. Describe the frame lifecycle and the exact roles of `BeginFrame`, `BeginWorld`, `BeginUI`, `Flush`, and `EndFrame`.

![Practical example: rendering a new infantry sprite diagram](images/Part_04_Chapter_01_Renderer-end-to-end-worked-example-diagram-showing-the-inputs-interme-5fc6a2.svg)

## Practical Example: Rendering a New Infantry Sprite


Suppose you have created a new infantry sprite file `commando.shp` and want to see it in-game.

<!-- DEV-NOTE [visual-aid]: sprite-loading pipeline diagram: commando.shp on disk -> VFS -> ISpriteLoader -> ISpriteFrame[] -> SpriteCache reserves -> SheetBuilder packs into Indexed/BGRA sheet (channel packing) -> Sprite with UVs -> SequenceSet -> Render trait -> WorldRenderer.Draw. Show palette texture sampling for indexed path. -->

1. **Place the asset.** Copy `commando.shp` into the mod's VFS path, for example `mods/ra/bits/commando.shp` (see [Part 6.3 — Virtual File System](Part_06_Chapter_03_VFS.md)).
2. **Define the [sequence](../appendices/Appendix_A_Glossary.md).** In `mods/ra/sequences/infantry.yaml`, add a sequence entry for the actor that uses the sprite:
   ```yaml
   e9:
       idle:
           Start: 0
           Length: 1
           ShadowStart: 410
       run:
           Start: 8
           Length: 6
           Facings: 8
           ShadowStart: 418
   ```
3. **Reserve the sprite.** At startup, `SequenceSet` asks the `SpriteCache` to reserve the frames referenced by the sequence. `SpriteCache` records the reservation as a token grouped by filename, so duplicate frames can be deduplicated and loaded in one pass.
4. **Load the sprite.** During `SpriteCache.LoadReservations`, the registered `ISpriteLoader` implementations try to parse `commando.shp`. The winning loader returns an `ISpriteFrame[]` array. The cache orders frames by height to pack rows tightly, then calls `SheetBuilder.Add` for each distinct frame.
5. **Pack into sheets.** The `SheetBuilder` chooses an `Indexed` sheet (because `commando.shp` is an 8-bit SHP) and allocates a rectangle with a one-pixel margin. `Util.FastCopyIntoChannel` writes the frame into the chosen channel of the sheet's CPU buffer. When the current channel fills up, the builder advances to the next RGBA channel; when the sheet fills, it allocates a new sheet and releases the old buffer.
6. **Create a `Sprite` reference.** For each frame, `SheetBuilder.Add` returns a `Sprite` that stores the rectangle inside the sheet, the UV coordinates (inset by `1/128` of a pixel to avoid bleeding), and the `TextureChannel` (for indexed sprites). `SpriteCache` caches the sprite under the reservation token.
7. **Bind to an actor.** The actor's `RenderSprites` and `WithInfantryBody` traits reference the sequence name `e9`. During `WorldRenderer.Draw`, the body trait creates `SpriteRenderable` objects that submit the sprite to the `WorldSpriteRenderer` batch.
8. **Apply a palette.** `commando.shp` is an indexed sprite. The [renderable](../appendices/Appendix_A_Glossary.md) selects the appropriate palette row (e.g., `player` for the owning player's color). The shader samples the palette texture using the index from the sprite and the palette row, producing the final color. If the unit uses player color remapping, the palette row itself was created by remapping base indices to the player's color.
9. **Draw the frame.** `Renderer.BeginWorld` binds the world framebuffer and clears it; `WorldRenderer.Draw` submits terrain and actor renderables; `SpriteRenderer` batches the quads by blend mode, sheet, and palette. After the world is complete, `Renderer.BeginUI` composites the world buffer into the screen buffer and draws the [chrome](../appendices/Appendix_A_Glossary.md). Finally, `Renderer.EndFrame` flushes the remaining draw calls and presents the framebuffer.

This example shows how a single sprite asset travels through asset loading, sequence resolution, sheet packing, palette sampling, and batch rendering to become a colored, animated unit on the screen.

### Wiring the sprite to an actor

To actually see the sprite in-game, you need a sequence entry (already shown above) and an actor rule that references it. The actor rule below is the same pattern used by infantry in the default mods and can be copy-pasted into `mods/<mod>/rules/infantry.yaml`:

```yaml
COMMANDO:
    Inherits: ^Infantry
    RenderSprites:
        Image: e9
    WithInfantryBody:
        StandSequences: idle
    Mobile:
        Speed: 71
    Health:
        HP: 10000
    Armament:
        Weapon: Colt45
    AttackFrontal:
    Selectable:
        Bounds: 12,17,0,-9
```

The `RenderSprites` trait tells the engine which sequence image this actor uses, and `WithInfantryBody` creates the per-frame `SpriteRenderable` objects that `WorldRenderer` sorts and draws. These traits are part of the ECS described in [Part 1.1 — Entity-Component-System (ECS) and Actor Lifecycle](Part_01_Chapter_01_ECS.md); the rule syntax is covered in [Part 2.4 — Rulesets, Actors, and Weapons](Part_02_Chapter_04_Rules_Weapons.md).

## Files

| File | Responsibility |
| :---- | :---- |
| `OpenRA.Game/Renderer.cs` | Main renderer class, frame begin/end, viewport, renderables, shader management. |
| `OpenRA.Game/Graphics/PlatformInterfaces.cs` | Platform abstraction: `IPlatform`, `IPlatformWindow`, `IGraphicsContext`, `ITexture`, `IShader`, `IVertexBuffer`, `IFrameBuffer`, `IFont`. |
| `OpenRA.Game/Graphics/Sheet.cs` | GPU texture sheet with CPU buffer. |
| `OpenRA.Game/Graphics/Sprite.cs` | Reference to a rectangle inside a sheet, UVs, offset, blend mode. |
| `OpenRA.Game/Graphics/SpriteCache.cs` | Caches sprite frames and packs them into sheets. |
| `OpenRA.Game/Graphics/SheetBuilder.cs` | Allocates rectangles on sheets and manages channel packing. |
| `OpenRA.Game/Graphics/SpriteRenderer.cs` | Batches sprite quads and issues draw calls. |
| `OpenRA.Game/Graphics/Palette.cs` | `IPalette`, `ImmutablePalette`, `MutablePalette`, palette remapping. |
| `OpenRA.Game/Graphics/HardwarePalette.cs` | Uploads palettes to the GPU as textures. |
| `OpenRA.Game/Graphics/Util.cs` | CPU-side helpers for copying sprite data into sheets and creating quads. |
| `OpenRA.Game/Graphics/Vertex.cs` | `Vertex` struct and `CombinedShaderBindings`. |
| `OpenRA.Game/Graphics/ShaderBindings.cs` | Base class for shader bindings and vertex attributes. |
<!-- DEV-NOTE [tooling]: SDL2: https://www.libsdl.org — cross-platform windowing, input, and event library used by OpenRA. -->
| `OpenRA.Platforms.Default/*.cs` | Default SDL2/OpenGL platform implementation. |
| `OpenRA.Game/Manifest.cs` | `RendererConstants` manifest section. |
| `OpenRA.Game/Graphics/SequenceSet.cs` | Loads sequences and creates the `SpriteCache`. |

![Architecture diagram](images/Part_04_Chapter_01_Renderer-architecture-diagram-showing-the-main-classes-interfaces-and-9161e6.svg)

## Architecture


### Renderer layers

```
[Game code] -> [Renderer / WorldRenderer] -> [SpriteRenderer] -> [IGraphicsContext / IShader] -> [OpenGL / SDL2]
```

The `Renderer` class is the high-level coordinator. It manages the platform window, the graphics context, the shader state, and the sprite rendering batches. The `WorldRenderer` ([Part 4.2 — WorldRenderer](Part_04_Chapter_02_WorldRenderer.md)) builds renderables and submits them to the renderer. The UI layer ([Part 4.3 — Widgets and Chrome](Part_04_Chapter_03_Widgets.md)) draws chrome through the same `Renderer` path after the world has been rendered.

### Platform abstraction

All platform-specific graphics code is hidden behind interfaces:

- `IPlatformWindow` — window creation, input pumping, clipboard, cursor, display management.
- `IGraphicsContext` — vertex buffers, textures, framebuffers, shaders, draw calls.
- `ITexture` — GPU texture upload/download.
- `IShader` — shader uniform/texture binding.
- `IPlatform` — factory for window, sound, and fonts.

The default implementation lives in `OpenRA.Platforms.Default` and uses SDL2 for windowing/input and OpenGL for rendering.

### Frame lifecycle

Each frame is produced in a strict sequence so that the world and the UI are rendered into separate compositor buffers before being blitted to the screen.

```csharp
Game.Renderer.BeginWorld(viewportLocation, viewportSize);
worldRenderer.Draw();          // terrain, actors, overlays, shroud, post-processing
Game.Renderer.BeginUI();
Ui.Draw();                     // chrome and HUD
Game.Renderer.EndFrame(inputHandler);
```

1. `BeginWorld` — `Renderer.BeginFrame()` is called internally. It clears the screen, ensures the world framebuffer is sized to the viewport, and updates the viewport/projection uniforms for the world sprite renderer. The world render target is bound.
2. `WorldRenderer.Draw()` — submits all world renderables, runs the shroud layer, and draws overlays (see [Part 4.2 — WorldRenderer](Part_04_Chapter_02_WorldRenderer.md)). Each draw call is batched by `SpriteRenderer`; nothing is sent to the GPU until `Flush()` is triggered.
3. `Renderer.Flush()` — `WorldRenderer` calls `Flush()` between phases so that batched geometry is actually drawn before the render state changes (for example, between terrain and actor layers, or before a post-processing pass).
4. `BeginUI` — first flushes the world pass, unbinds the world framebuffer, and binds the screen framebuffer. It then draws the world buffer into the screen buffer with pixel-art scaling. If the world was not rendered, it simply begins a new UI frame. The UI sprite renderer is now active.
5. `Ui.Draw()` — traverses the widget tree from `Ui.Root` and draws chrome, tooltips, and windows.
6. `EndFrame` — flushes the final UI batch, unbinds the screen buffer, draws the screen buffer to the actual window, pumps input, and calls `Context.Present()` to swap the front buffer.

The `Renderer` tracks which render type is active (`None`, `World`, or `UI`) and throws an exception if the sequence is violated. This separation is essential because world and UI rendering use different viewport parameters, depth-buffer settings, and scaling behavior.

### Sheet model

A `Sheet` is a large GPU texture with a CPU-side buffer. Sprites are small rectangles inside the sheet. By packing many sprites into a few large sheets, the engine reduces texture switching and draw calls.

`Sheet` has two important states:

- **Buffered** — the CPU `byte[] data` exists. Mods can read or write it, and the texture is marked dirty until `GetTexture()` uploads it.
- **Unbuffered** — the CPU buffer has been released after upload to save memory. Only the GPU texture remains.

Sheets are created by `SheetBuilder` in two sizes: `SequenceBgraSheetSize` for true-color sprites and `SequenceIndexedSheetSize` for indexed sprites. The maximum size is limited by GPU texture size support (modern hardware usually supports 8192 or 16384, but OpenRA defaults to 2048 for compatibility).

### Sprite reference

A `Sprite` stores:

- `Sheet` — the sheet containing the texture.
- `Bounds` — the rectangle within the sheet, in pixels.
- `Top/Left/Bottom/Right` — UV coordinates (slightly inset to avoid texture bleeding).
- `Channel` — which texture channel to use (for indexed sheets).
- `BlendMode` — how to blend with the framebuffer.
- `Offset` — world-space offset relative to the actor's position.
- `ZRamp` — fake depth scaling for isometric mods.
- `Size` — scaled world size used by the renderer to place the quad.

The `Sprite` constructor insets the UVs by `1/128` of a pixel. This compensates for GPU precision issues when rendering into non-1:1 framebuffers, preventing a stray line of texels from sampling outside the sprite rectangle. `SpriteWithSecondaryData` extends a sprite with a secondary sheet and bounds, used for per-pixel depth offset maps.

### Channel packing and sheet grouping

OpenRA keeps two kinds of sheets: `Indexed` (1 byte per effective channel) and `BGRA` (32-bit color). `SheetBuilder.FrameTypeToSheetType` maps decoded sprite formats to these buckets:

- `SpriteFrameType.Indexed8` -> `SheetType.Indexed`
- `SpriteFrameType.Bgra32`, `Bgr24`, `Rgba32`, `Rgb24` -> `SheetType.BGRA`

For indexed sheets, four sprite frames can be packed into the RGBA channels of a single texture. The `TextureChannel` enum (`Red`, `Green`, `Blue`, `Alpha`) selects which channel to sample. The shader reconstructs the index by taking the dot product of the sampled texel and the channel mask (`SelectChannelMask` in the vertex shader), then samples the palette texture at `(index, paletteRow)`. This multiplies effective sheet capacity by four and keeps all indexed artwork in the same texture format.

True-color sprites use `TextureChannel.RGBA` and are sampled directly; the palette texture is only used for color-shift effects if one is configured.

### Palette system

OpenRA palettes are 256-entry lookup tables. The core interfaces are:

- `IPalette` — read-only indexed color accessor (`uint this[int index]`).
- `ImmutablePalette` — a fixed 256-color palette loaded from a `.pal` file or another palette.
- `MutablePalette` — a mutable copy that `IPaletteModifier` traits can adjust each frame.
- `IPaletteRemap` — remaps a single color at a time, used for player color palettes.
- `HardwarePalette` — collects all registered palettes into a GPU texture.

Palette loading in YAML is done by world traits such as:

- `PaletteFromFile` — loads a `.pal` file from the VFS.
- `PaletteFromPaletteWithAlpha` — derives a palette from another with alpha adjustments.
- `PlayerColorPalette` — remaps a base palette to a player's color using `IPaletteRemap`.
- `PaletteFromPlayerPaletteWithHue` — derives a hue-shifted copy for another purpose.

Each palette row is registered in `HardwarePalette` with a flag `AllowModifiers`. If modifiers are allowed, the palette is kept as a `MutablePalette`; otherwise, the immutable copy is written directly into the GPU palette buffer. The first row of the palette texture is reserved as a no-op row for non-paletted sprites, avoiding a palette lookup for most RGBA sprites.

<!-- DEV-NOTE [visual-aid]: palette system diagram: a 2D texture where rows are palettes and columns are 256 color indices. Show arrows from a `.pal` file row, from a PlayerColorPalette remapped row, and from an IPaletteModifier writing into a MutablePalette. Add a magnified view of the fragment shader sampling (index, paletteRow) to produce the final RGBA color. -->

| Concept | Real-world analogy | Source / registration |
| :---- | :---- | :---- |
| `ImmutablePalette` | A pre-mixed tray of 256 inks | `PaletteFromFile` or `PaletteFromPaletteWithAlpha` in `rules/world.yaml` |
| `MutablePalette` | A tray that can be tinted each frame | `AllowModifiers: true` keeps a copy for `IPaletteModifier` traits |
| `PlayerColorPalette` | Replacing a few inks in the tray with a house color | `RemapIndex` selects which indices are recolored per player |
| `HardwarePalette` | The master ink chart uploaded to the GPU | Created by `WorldRenderer` and refreshed every frame via `RefreshPalette` |
| `IPaletteRemap` | A recipe that recolors one ink at a time | Used by `PlayerColorPalette` to build per-player palette rows |

Palette traits are world traits, so they are declared in the `World` actor definition (see [Part 2.4 — Rulesets, Actors, and Weapons](Part_02_Chapter_04_Rules_Weapons.md)). The per-frame color effects that drive `MutablePalette` are often triggered by gameplay code, such as the nuke flash or the desert theater tint, which are described alongside the simulation logic in [Part 1.1 — Entity-Component-System (ECS) and Actor Lifecycle](Part_01_Chapter_01_ECS.md).

### Shader pipeline

The current engine uses a single combined sprite shader defined in `glsl/combined.vert` and `glsl/combined.frag`. The C# binding is `CombinedShaderBindings` in `OpenRA.Game/Graphics/Vertex.cs`, which inherits `ShaderBindings` and declares the vertex attributes:

```csharp
new ShaderVertexAttribute("aVertexPosition", ShaderVertexAttributeType.Float, 3, 0),
new ShaderVertexAttribute("aVertexTexCoord", ShaderVertexAttributeType.Float, 4, 12),
new ShaderVertexAttribute("aVertexAttributes", ShaderVertexAttributeType.UInt, 1, 28),
new ShaderVertexAttribute("aVertexTint", ShaderVertexAttributeType.Float, 4, 32)
```

At startup `Renderer` creates two `SpriteRenderer` instances, one for the world and one for the UI, both sharing the same `CombinedShaderBindings` compiled via `Context.CreateShader`. The platform layer compiles and caches the shader program.

Uniforms and textures are bound each frame or each batch:

- `SetViewportParams` sends `Scroll`, `p1`, `p2`, and `PaletteRows` to the vertex shader.
- `SpriteRenderer.SetPalette` binds the `Palette` and `ColorShifts` textures and sets `PaletteRows`.
- `SetTexture("TextureN", sheet.GetTexture())` binds up to eight sprite sheets to samplers `Texture0` through `Texture7`.
- `EnableDepthPreview`, `DepthPreviewParams`, `DepthTextureScale`, and `EnablePixelArtScaling` are toggled as needed.

The vertex shader decodes the packed `aVertexAttributes` integer into:

- channel type (paletted R/G/B/A, RGBA, or raw color)
- secondary depth channel
- primary and secondary sampler indices
- palette row index

The fragment shader then samples the correct sheet, looks up the palette if needed, applies color shifting, depth offsets, tinting, and blending.

> **Note:** Older versions of OpenRA configured separate `SpriteShader`, `SpriteDepthShader`, `WorldShader`, and `WorldDepthShader` in `RendererConstants`. The modern engine has unified these into the `combined` shader, with depth and world behavior controlled by uniforms and vertex attributes.

![Data flow  code path diagram](images/Part_04_Chapter_01_Renderer-sequence-flow-diagram-tracing-the-execution-path-from-trigge-035864.svg)

## Data Flow / Code Path


### Frame rendering

```csharp
Game.Renderer.BeginWorld(viewportLocation, viewportSize);
worldRenderer.Draw();
Game.Renderer.BeginUI();
Ui.Draw();
Game.Renderer.EndFrame(inputHandler);
```

`BeginWorld` internally calls `BeginFrame`, which clears the context, ensures the screen and world framebuffers are allocated at the correct power-of-two size, and sets the UI viewport parameters. `BeginWorld` then binds the world framebuffer and sets the world viewport parameters. `WorldRenderer.Draw` submits renderables. `BeginUI` flushes the world pass, composites the world buffer into the screen buffer, and sets the render type to UI. `Ui.Draw` draws the chrome. `EndFrame` flushes everything, blits the screen buffer to the window, pumps input, and presents.

### Sprite loading pipeline

The complete path from asset file to GPU is:

1. YAML `SequenceSet` references `commando.shp` and a set of frame indices.
2. `SequenceSet` creates a `SpriteCache` with the configured `SequenceBgraSheetSize` and `SequenceIndexedSheetSize`.
3. `SpriteCache.ReserveSprites` records the file and frame indices as a reservation token.
4. During `LoadReservations`, `ISpriteLoader` implementations attempt to parse the file. The successful loader returns `ISpriteFrame[]`.
5. The cache orders frames by height, then for each frame calls `SheetBuilder.Add`.
6. `SheetBuilder` chooses `SheetType.Indexed` or `SheetType.BGRA`, allocates a rectangle with a one-pixel margin, copies the frame data with `Util.FastCopyIntoChannel`, and calls `CommitBufferedData` to mark the sheet dirty.
7. `SheetBuilder` returns a `Sprite` with UVs, channel, and bounds. `SpriteCache` stores it keyed by `(filename, frameIndex, premultiplied, adjustFrame)`.
8. The first time the sheet is needed for rendering, `Sheet.GetTexture()` creates a GPU texture and calls `texture.SetData(data, width, height)`. After upload, the CPU buffer may be released if `ReleaseBuffer` was requested.

### Texture upload

```csharp
public ITexture GetTexture()
{
    if (texture == null)
    {
        texture = Game.Renderer.Context.CreateTexture();
        dirty = true;
    }

    if (data != null && dirty)
    {
        texture.SetData(data, Size.Width, Size.Height);
        dirty = false;
        if (releaseBufferOnCommit)
            data = null;
    }

    return texture;
}
```

Sheets are uploaded lazily. This is important for load screens: the engine can decode hundreds of frames into CPU buffers during startup and only upload the texture when the first renderable using that sheet is drawn.

### Palette upload

`HardwarePalette` builds a texture where each row is a palette and each column is a color index. The shader samples the palette texture using the sprite index and the selected palette row. The first row is reserved for non-indexed sprites that do not need a color shift.

Each frame `WorldRenderer.RefreshPalette` calls `ApplyModifiers` on all `IPaletteModifier` traits, copies the mutable palettes into the CPU buffer, and uploads the buffer to the GPU. The mutable palettes are then reset to their original values so modifiers can be applied again next frame.

### Batching

`SpriteRenderer` collects sprite quads into a large vertex buffer and draws them with a single shader. Quads are grouped by blend mode, sheet, and palette. The renderer flushes the batch when any of these change, or when the vertex buffer is full. Up to eight sheets can be bound simultaneously (`SheetCount = 8`); if a ninth sheet is needed, the current batch is flushed first.

`Renderer.CurrentBatchRenderer` is the mechanism that triggers the flush: when a different batch renderer becomes active, the previous one is flushed. This allows the world renderer, UI renderer, line renderers, and post-process passes to interleave without losing batch state.

![Configuration (yaml) diagram](images/Part_04_Chapter_01_Renderer-annotated-yaml-snippet-diagram-showing-the-key-fields-and-ho-6a1b98.svg)

## Configuration (YAML)


### Renderer constants

`RendererConstants` is a section in the mod manifest (`OpenRA.Game/Manifest.cs`). The engine defaults are:

```yaml
RendererConstants:
    FontSheetSize: 512
    CursorSheetSize: 512
    SequenceBgraSheetSize: 2048
    SequenceIndexedSheetSize: 2048
```

Increasing `SequenceBgraSheetSize` or `SequenceIndexedSheetSize` can reduce the number of sheets and therefore the number of batch flushes, but it must not exceed the maximum texture size supported by the target hardware. The `FontSheetSize` controls how many glyphs are packed into a single font sheet; large translations or high-DPI windows may need a larger value.

### Shader definitions

Shaders are loaded by `ShaderBindings` from `glsl/<name>.vert` and `glsl/<name>.frag` relative to the engine directory. The default sprite shader is `glsl/combined.vert` and `glsl/combined.frag`. The platform layer (`IGraphicsContext.CreateShader`) compiles and links these into an `IShader` program and caches the program by `IShaderBindings`. Mods can add custom post-processing passes with their own shader bindings; these are not declared in YAML but are referenced by the trait code that implements `IRenderPostProcessPass` (see [Part 4.2 — WorldRenderer](Part_04_Chapter_02_WorldRenderer.md)).

### Palette definitions

Palettes are defined by world traits in `rules/world.yaml` or similar:

```yaml
World:
    PaletteFromFile:
        Name: player
        Filename: temperat.pal
        AllowModifiers: true
    PlayerColorPalette:
        BasePalette: player
        BasePaletteName: player
        RemapIndex: 16, 17, 18, 19, 20, 21, 22, 23
        AllowModifiers: true
```

`AllowModifiers: true` means the palette is copied into a `MutablePalette` and can be modified each frame by `IPaletteModifier` traits (for example, the nuke flash effect). `RemapIndex` lists the palette indices that should be replaced with the player's color.

## Interconnectivity

- **Depends on:** [Part 1.1 — Entity-Component-System (ECS) and Actor Lifecycle](Part_01_Chapter_01_ECS.md), [Part 1.3 — World, OrderManager, and Orders](Part_01_Chapter_03_World_Orders.md), [Part 2.4 — Rulesets, Actors, and Weapons](Part_02_Chapter_04_Rules_Weapons.md), [Part 3.1 — Mod SDK and Project Structure](Part_03_Chapter_01_Mod_SDK.md), [Part 6.3 — Virtual File System](Part_06_Chapter_03_VFS.md), [Part 6.5 — Asset Loaders](Part_06_Chapter_05_Asset_Loaders.md).
- **Used by:** [Part 4.2 — WorldRenderer](Part_04_Chapter_02_WorldRenderer.md), [Part 4.3 — Widgets and Chrome](Part_04_Chapter_03_Widgets.md), [Part 4.4 — Viewport and Input](Part_04_Chapter_04_Viewport_Input.md), [Part 5.1 — Audio Architecture](Part_05_Chapter_01_Audio_Architecture.md), [Part 7.8 — Random Map Generator Extension Points](Part_07_Chapter_08_Extension_Points.md) (tile rendering for generated maps), [Part 1.2 — Activity System](Part_01_Chapter_02_Activities.md), [Part 10.3 — Porting, Modding, and Developer Workflows](Part_10_Chapter_03_Port_And_Modding.md).

![Algorithms diagram](images/Part_04_Chapter_01_Renderer-algorithm-diagram-or-pseudocode-flowchart-for-the-non-trivia-5983ed.svg)

## Algorithms


### Sheet packing

`SpriteCache` uses a `SheetBuilder` to allocate rectangles on sheets. The algorithm:

1. Sort pending frames by height so that rows contain sprites of similar height, minimizing wasted space.
2. Place sprites left-to-right along a row, leaving a one-pixel margin on all sides.
3. When the current row exceeds the sheet width, advance to the next row with `rowHeight + margin`.
4. When the sheet height is exceeded, advance to the next channel (for indexed sheets) or allocate a new sheet (for BGRA sheets, or when all indexed channels are exhausted).
5. Reuse the CPU buffer between sheets when possible to reduce GC pressure.

### UV inset

To prevent texture bleeding when scaling, sprites inset their UVs by `1/128` of a pixel:

```csharp
const float Inset = 1 / 128f;
Left = (Math.Min(bounds.Left, bounds.Right) + Inset) / sheet.Size.Width;
Top = (Math.Min(bounds.Top, bounds.Bottom) + Inset) / sheet.Size.Height;
Right = (Math.Max(bounds.Left, bounds.Right) - Inset) / sheet.Size.Width;
Bottom = (Math.Max(bounds.Top, bounds.Bottom) - Inset) / sheet.Size.Height;
```

The one-pixel margin in the sheet builder, combined with the UV inset, ensures that bilinear filtering and downscaling never sample from a neighboring sprite.

### Channel packing

Indexed sheets pack four sprite frames into the RGBA channels of a single texture. The shader uses the sprite's `Channel` to select which channel to sample. The vertex shader encodes the channel as a `vChannelMask` (e.g., `(1,0,0,0)` for `Red`) and the fragment shader takes the dot product of the sampled texel and the mask to recover the index.

This packing is transparent to sequences but requires that all indexed frames placed in the same channel respect the margin so that channel data does not bleed.

### Palette remapping

`PlayerColorPalette` and similar traits create an `IPaletteRemap` that replaces specific indices with the player's color. `ImmutablePalette` has a constructor that accepts a base palette and a remap, producing a new palette where every index in the remap range is remapped. The remapped palette is then registered in `HardwarePalette` with the player's name suffix (e.g., `player0`), so units owned by different players can share the same sheet but use different palette rows.

### Color shifting

`HardwarePalette.SetColorShift` stores a per-palette hue/saturation/value shift in the `ColorShifts` texture. The fragment shader reads the range and shift vectors and applies them only to colors whose hue falls within the range. This is used for effects like the desert theater palette shift or team color highlighting.

![Extension points diagram](images/Part_04_Chapter_01_Renderer-extension-hook-diagram-showing-the-interface-s-to-implement-b4a27b.svg)

## Extension Points


### Add a new platform

Implement `IPlatform` and `IPlatformWindow` to target a new operating system or graphics API. Register the platform in the engine startup.

### Add a new shader

Add a GLSL vertex and fragment shader pair under `glsl/`, create a `ShaderBindings` subclass that declares the vertex attributes, and create it via `Renderer.CreateShader`. Use it from a custom renderer or post-processing pass.

### Add a custom palette source

Create a world trait that implements `ILoadsPalettes` or `IPaletteModifier` to add or modify palettes at runtime. `ILoadsPlayerPalettes` is used for per-player palette variants.

### Add a custom renderable

Implement `IRenderable` or `IAboveShroud` and submit it to the `WorldRenderer` during the render phase (see [Part 4.2 — WorldRenderer](Part_04_Chapter_02_WorldRenderer.md)).

![Common pitfalls  guardrails diagram](images/Part_04_Chapter_01_Renderer-checklist-infographic-style-diagram-summarizing-the-top-pitf-fb069e.svg)

## Common Pitfalls / Guardrails


- **Sheet size limits:** GPU textures have a maximum size. OpenRA defaults to 2048 for indexed and BGRA sequence sheets; older hardware may support only 1024. Very large sprites may need to be split or sheet sizes increased. Always verify the target hardware's `GL_MAX_TEXTURE_SIZE` before raising these values.
- **Texture bleeding:** always use the UV inset and keep the one-pixel margin between packed sprites. If you see a colored fringe around a sprite, the UVs are likely not inset or the margin was removed.
- **Palette row count:** the hardware palette texture has a limited number of rows. Adding too many palettes can exceed the texture height. Raise awareness when adding new palettes, especially per-player variants.
- **Channel mismatch:** indexed sprites must be placed on `SheetType.Indexed` and sampled with the correct `TextureChannel`. BGRA sprites use `TextureChannel.RGBA`. Sampling an indexed sprite as RGBA produces garbage colors.
- **Premultiplied vs non-premultiplied:** `SpriteCache` stores premultiplied and non-premultiplied versions of the same frame separately because blending math differs. Do not mix them in the same batch unless the blend mode is set correctly.
- **CPU buffer lifetime:** sheets can release their CPU buffer after uploading to save memory. Mods that need to read sheet pixels (for example, screenshots or editor tools) must keep the buffer or call `CreateBuffer` before reading. Do not access `Sheet.GetData()` on an unbuffered sheet unless you have recreated the buffer.
- **Threading:** all rendering calls must happen on the main thread. Do not upload textures, call `Sheet.GetTexture()`, or call `Draw` from background threads. The only thread-safe rendering operation is `ThreadPool.QueueUserWorkItem` for screenshot encoding after `SaveScreenshot` has already read the buffer on the main thread.
- **Calling `GetTexture()` on the render thread:** `Sheet.GetTexture()` triggers GPU upload if the sheet is dirty. This must happen on the main render thread, not during async asset loading or from a worker thread. Decoding and buffer writes can happen on load threads, but upload must wait for the main thread.
- **Flushing the wrong batch:** `Renderer.Flush()` clears `CurrentBatchRenderer`, which flushes whichever batch renderer was active. If you manually change render state (scissor, depth buffer) without flushing, later draw calls may use the wrong state. Always call `Flush()` before a state change that affects the batch.
- **Palette invalidation:** if you add or replace palettes after world initialization, raise `WorldRenderer.PaletteInvalidated` so that cached `PaletteReference` objects and sequences are re-resolved.

## What to read next

- [Part 4.2 — WorldRenderer](Part_04_Chapter_02_WorldRenderer.md) for the world render pipeline and renderable sorting.
- [Part 4.3 — Widgets and Chrome](Part_04_Chapter_03_Widgets.md) for UI rendering through the same renderer path.
- [Part 6.5 — Asset Loaders](Part_06_Chapter_05_Asset_Loaders.md) for how raw sprite, audio, and video files are parsed before they reach the renderer.
- [Appendix H — Asset Visual Reference](../appendices/Appendix_H_Asset_Visual_Reference.md) for a categorical lookup of sprite, palette, cursor, and chrome file formats and their engine classes.

## Summary

This chapter explains how OpenRA's 2D [sprite](../appendices/Appendix_A_Glossary.md) renderer uploads frames to GPU sheets, applies palettes, and draws the world and UI.

After reading this chapter, you should be able to:

- Describe the renderer stack from game code through `Renderer`, `SpriteRenderer`, and the platform abstraction to the GPU.
- Explain the `Sheet`/`Sprite` model and why sprite packing reduces draw calls.
- Distinguish indexed (palette) sprites from true-color sprites and explain how `HardwarePalette` works.
- Trace a sprite frame from asset file through `SpriteCache` to a GPU sheet upload.

If any of the concepts above feel unclear, review the relevant section before continuing. For source files and further reading, see the References section.


## References

- `OpenRA.Game/Renderer.cs` — main renderer.
- `OpenRA.Game/Graphics/PlatformInterfaces.cs` — platform abstraction.
- `OpenRA.Game/Graphics/Sheet.cs` — texture sheet.
- `OpenRA.Game/Graphics/Sprite.cs` — sprite reference.
- `OpenRA.Game/Graphics/SpriteCache.cs` — sprite cache.
- `OpenRA.Game/Graphics/SheetBuilder.cs` — sheet packing.
- `OpenRA.Game/Graphics/SpriteRenderer.cs` — sprite batching.
- `OpenRA.Game/Graphics/Palette.cs` — palette data.
- `OpenRA.Game/Graphics/HardwarePalette.cs` — GPU palette texture.
- `OpenRA.Game/Graphics/Util.cs` — CPU copy helpers.
- `OpenRA.Game/Graphics/Vertex.cs` — `Vertex` and `CombinedShaderBindings`.
- `OpenRA.Game/Graphics/ShaderBindings.cs` — shader binding base class.
- `OpenRA.Game/Manifest.cs` — `RendererConstants`.
- `OpenRA.Platforms.Default/*.cs` — default SDL2/OpenGL implementation.
- `OpenRA.Game/Graphics/SequenceSet.cs` — sequence loading and `SpriteCache` creation.
- `glsl/combined.vert` and `glsl/combined.frag` — default sprite shader.


### External resources

- [OpenRA sprite sequences](https://docs.openra.net/en/release/sprite-sequences/)
- [OpenRA playtest docs](https://docs.openra.net/en/playtest/)