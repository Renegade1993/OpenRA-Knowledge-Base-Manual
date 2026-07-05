# Chapter 4.4 — Viewport and Input

## Purpose

The [viewport](../appendices/Appendix_A_Glossary.md) maps the simulation world to the screen. It controls scroll position, zoom, and the visible cell region. Input is captured by the platform window and routed through the UI, the [order generator](../appendices/Appendix_A_Glossary.md), and the world. This chapter explains the `Viewport` class, the input pipeline, order generators, and how mouse/keyboard events become game orders.

![Mental model diagram](images/Part_04_Chapter_04_Viewport_Input-learning-objectives-summary-diagram-or-concept-map-showing-h-fe332a.svg)

## Mental Model

Think of the viewport as the camera on a film set, and input as the director's walkie-talkie.

- **The camera** (`Viewport`) maps the 3D world onto the 2D screen. It can zoom in, zoom out, and pan, but it is clamped so it never shows the empty space outside the set.
- **The camera operator** (`WorldRenderer`) uses the viewport to decide which actors are visible and where to place their sprites.
- **The walkie-talkie** (mouse and keyboard events) is picked up by the UI crew first. If a widget cares about the message (for example, a button click), it answers and the message stops there.
- **The stage crew** (`WorldInteractionControllerWidget`) receives any messages the UI did not want. It translates the message into world coordinates and passes it to the current **shooting mode** (`World.OrderGenerator`).
- **The shooting mode** decides what the click means: select, move, attack, guard, or place a building. It turns the click into a formal instruction (`Order`) that is sent to the lockstep scheduler.

This mental model explains why a click on a UI button never issues a move order, why the order generator can change the cursor, and why all game-changing input must become an `Order` (so it can be replayed and synchronized). The actor that produces the order is part of the ECS in [Part 1.1 — Entity-Component-System (ECS) and Actor Lifecycle](Part_01_Chapter_01_ECS.md), and the lockstep scheduler is described in [Part 9.1 — OrderManager and Lockstep Foundation](Part_09_Chapter_01_OrderManager.md).

## Learning Objectives


After studying this chapter, you should be able to:

- Explain how the Viewport maps world coordinates to screen coordinates and vice versa.
- Describe the input dispatch pipeline from platform window to order generator.
- Implement a custom IOrderGenerator for a new command mode.
- Configure WorldViewportSizes and input settings in YAML.
- Trace how mouse events become game orders through World.IssueOrder.
- Identify common pitfalls in input handling and viewport coordinate transforms.
- Explain how drag gestures, multi-tap selection, and viewport scroll clamping work.

## Practical Example: A Ping Order Generator

Suppose you want a "ping" command mode that lets the player place a beacon on the map. The command mode is implemented as an `OrderGenerator`.

### Order generator

```csharp
using System.Collections.Generic;
using OpenRA.Graphics;
using OpenRA.Mods.Common.Orders;
using OpenRA.Traits;

namespace OpenRA.Mods.MyMod.Orders
{
    public class PingOrderGenerator : OrderGenerator
    {
        public PingOrderGenerator(World world) : base(world) { }

        protected override MouseActionType ActionType => MouseActionType.ConfirmOrder;

        protected override string GetCursor(World world, CPos cell, int2 worldPixel, MouseInput mi)
        {
            return "ability"; // cursor name from cursors.yaml
        }

        protected override IEnumerable<Order> OrderInner(World world, CPos cell, int2 worldPixel, MouseInput mi)
        {
            yield return new Order("PingBeacon", null, Target.FromCell(world, cell), false);
        }

        protected override IEnumerable<IRenderable> Render(WorldRenderer wr, World world) { return SpriteRenderable.None; }
        protected override IEnumerable<IRenderable> RenderAboveShroud(WorldRenderer wr, World world) { return SpriteRenderable.None; }
        protected override IEnumerable<IRenderable> RenderAnnotations(WorldRenderer wr, World world) { return SpriteRenderable.None; }
    }
}
```

### UI wiring

```csharp
public class PingButtonLogic : ChromeLogic
{
    public PingButtonLogic(Widget widget, World world)
    {
        var ping = widget.Get<ButtonWidget>("PING");
        ping.OnClick = () => world.OrderGenerator = new PingOrderGenerator(world);
    }
}
```

When the player clicks the button, the widget assigns `PingOrderGenerator` to `World.OrderGenerator`. From then on, every mouse click on the world is routed to `PingOrderGenerator.OrderInner`, which converts the screen pixel into a cell via `Viewport.ViewToWorld` and issues a `PingBeacon` order. The order crosses into the deterministic simulation through `World.IssueOrder`, exactly as described in [Part 1.3 — World, OrderManager, and Orders](Part_01_Chapter_03_World_Orders.md).

## Files

| File | Responsibility |
| :---- | :---- |
| `OpenRA.Game/Graphics/Viewport.cs` | `Viewport` class: scroll, zoom, coordinate transforms, visible cells. |
| `OpenRA.Game/WorldViewportSizes.cs` | Default viewport sizes and zoom levels. |
| `OpenRA.Game/Input/IInputHandler.cs` | `IInputHandler`, `MouseInput`, `KeyInput`, `MouseButton`, `Modifiers`. |
| `OpenRA.Game/Input/InputHandler.cs` | `DefaultInputHandler` and `NullInputHandler`. |
| `OpenRA.Game/Input/Keycode.cs` | Keycode enum for keyboard input. |
| `OpenRA.Game/Orders/IOrderGenerator.cs` | Interface for order generators (command cursors). |
| `OpenRA.Mods.Common/Orders/OrderGenerator.cs` | Base order generator class. |
| `OpenRA.Mods.Common/Orders/UnitOrderGenerator.cs` | Default selection and order generator. |
| `OpenRA.Mods.Common/Orders/GuardOrderGenerator.cs` | Guard order generator example. |
| `OpenRA.Mods.Common/Orders/PlaceBuildingOrderGenerator.cs` | Support power / building placement example. |
| `OpenRA.Mods.Common/Widgets/WorldInteractionControllerWidget.cs` | Bridge between world input and order generators. |
| `OpenRA.Game/Game.cs` | Top-level loop and order generator tick. |
| `OpenRA.Game/World.cs` | Order generator property and `IssueOrder`. |
<!-- DEV-NOTE [tooling]: SDL2: https://www.libsdl.org — cross-platform windowing, input, and event library used by OpenRA. -->
| `OpenRA.Platforms.Default/Sdl2Input.cs` | SDL2 input pumping and multi-tap detection. |
| `OpenRA.Platforms.Default/MultiTapDetection.cs` | Multi-tap/double-click logic. |
| `OpenRA.Game/Graphics/WorldRenderer.cs` | Uses viewport for culling and coordinate transforms. |
| `OpenRA.Mods.Common/Widgets/Logic/Ingame/CommandBarLogic.cs` | In-game command bar UI logic. |

![Architecture diagram](images/Part_04_Chapter_04_Viewport_Input-architecture-diagram-showing-the-main-classes-interfaces-and-9161e6.svg)

## Architecture


### Viewport coordinate spaces

OpenRA uses several coordinate spaces:

- **World position** (`WPos`) — 3D world coordinates in world pixels. The Z component represents height above the ground plane.
- **Cell position** (`CPos`) — tile coordinates on the map grid.
- **Map position** (`MPos`) / **Projected position** (`PPos`) — internal grid coordinates used for rectangular and isometric maps.
- **View position** (`int2`) — screen pixels relative to the viewport origin (top-left of the world view).
- **UI position** (`int2`) — screen pixels relative to the window; for a world at the top-left of the window, this is the same as view position.

The `Viewport` converts between these spaces:

- `WorldToViewPx` — world position to screen pixels. Accounts for zoom, UI scale, and the current viewport center.
- `ViewToWorldPx` — screen pixels to world position (the inverse of `WorldToViewPx`).
- `ViewToWorld` — screen pixels to a cell, with isometric cliff handling and fallback to the nearest candidate cell.
- `ProjectedPosition` — world position projected onto the 2D ground plane (Z = 0). This is the inverse of the projection used by `WorldRenderer.ScreenPosition`.
- `CenterPosition` — the `WPos` at the center of the viewport, derived from `CenterLocation` via `ProjectedPosition`.

Because the world is rendered with a projection where `screenY = worldY - worldZ` (and `screenZ = worldY` for depth), the same screen pixel can correspond to many world positions. `ProjectedPosition` resolves this ambiguity by choosing the point with zero elevation. `ViewToWorld` resolves it by testing candidate cells and choosing the one whose center is closest to the projected point.

### Viewport state

A `Viewport` stores:

- `CenterLocation` — the world pixel position at the center of the screen (the unprojected screen coordinate).
- `Zoom` — the current zoom level. Higher values zoom in; lower values zoom out.
- `ViewportSize` — the visible world area in world pixels, derived from `NativeResolution / Zoom * UIScale`.
- `MinZoom` / `MaxZoom` — zoom limits computed from `WorldViewportSizes` and the native resolution.
- `mapBounds` — the clamping rectangle so the camera cannot scroll past the edge of the map. Computed from the map's projected corners in world pixels.
- `VisibleCellsInsideBounds` / `AllVisibleCells` — cached `ProjectedCellRegion` of the visible map cells.

### Input dispatch

```
[SDL2 window] -> [Sdl2Input] -> [IInputHandler] -> [Game] -> [Ui.HandleInput / HandleKeyPress / HandleTextInput]
                                              -> [WorldInteractionControllerWidget] -> [World.OrderGenerator.Order]
                                              -> [World.IssueOrder] -> [OrderManager.IssueOrder]
```

The platform window (SDL2) pumps input events into the `IInputHandler` provided by `Game`. The default handler is `DefaultInputHandler`, which wraps `Ui.HandleInput` for mouse events and `Ui.HandleKeyPress`/`Ui.HandleTextInput` for keyboard events. These are run inside `Sync.RunUnsynced` so that input handling does not affect the deterministic simulation.

<!-- DEV-NOTE [visual-aid]: input-routing flow diagram. A horizontal swim-lane showing: SDL2 window -> Sdl2Input -> DefaultInputHandler/Sync.RunUnsynced -> Ui.HandleInput (widget tree) -> WorldInteractionControllerWidget -> World.OrderGenerator.Order -> Viewport coordinate transforms -> World.IssueOrder -> OrderManager.IssueOrder. Show two branches: UI consumes (event stops) and world consumes (event becomes an Order). -->

`WorldInteractionControllerWidget` is a special [widget](../appendices/Appendix_A_Glossary.md) that covers the world viewport. It receives mouse events after the UI [chrome](../appendices/Appendix_A_Glossary.md) has had a chance to consume them. It converts screen coordinates to world coordinates and asks the current `World.OrderGenerator` to produce orders. The orders are then issued through `World.IssueOrder`, which forwards them to the `OrderManager` for local execution and network synchronization (see [Part 9.1 — OrderManager and Lockstep Foundation](Part_09_Chapter_01_OrderManager.md)).

Keyboard events are handled entirely by the widget system unless a widget consumes them. If no widget consumes a key press, it may be interpreted as a hotkey by the command bar logic.

### Order generators

An order generator is the active command mode. It determines the cursor, draws target lines and preview [sprites](../appendices/Appendix_A_Glossary.md), and produces `Order` objects when the player clicks. Examples include:

- `UnitOrderGenerator` — default selection, movement, and attack. It is active when no special command mode is set.
- `DeployOrderGenerator` — orders selected units to deploy (for example, MCVs or GIs).
- `AttackMoveOrderGenerator` / `GuardOrderGenerator` — attack-move and guard commands.
- `PlaceBuildingOrderGenerator` — support power placement and building placement previews.
- `RepairOrderGenerator` — repair cursor for buildings.
- `BeaconOrderGenerator` — places a beacon/ping on the map.

Order generators are not registered in YAML; they are created by UI widgets, hotkey handlers, or command bar logic and assigned to `World.OrderGenerator` at runtime. The previous order generator is deactivated (its `Deactivate` method is called) when replaced, and the default `UnitOrderGenerator` is restored by `World.CancelInputMode`.

![Data flow  code path diagram](images/Part_04_Chapter_04_Viewport_Input-sequence-flow-diagram-tracing-the-execution-path-from-trigge-035864.svg)

## Data Flow / Code Path


### Viewport construction

```csharp
public Viewport(WorldRenderer wr, Map map)
{
    worldRenderer = wr;
    tileSize = map.Rules.TerrainInfo.TileSize;
    viewportSizes = Game.ModData.GetOrCreate<WorldViewportSizes>();
    graphicSettings = Game.Settings.Graphics;
    defaultScale = viewportSizes.DefaultScale;

    // Calculate map bounds in world-px
    if (wr.World.Type == WorldType.Editor)
    {
        var width = map.MapSize.Width * tileSize.Width;
        var height = map.MapSize.Height * tileSize.Height;
        if (wr.World.Map.Grid.Type == MapGridType.RectangularIsometric)
            height /= 2;

        mapBounds = new Rectangle(0, 0, width, height);
        CenterLocation = new int2(width / 2, height / 2);
    }
    else
    {
        var tl = wr.ScreenPxPosition(map.ProjectedTopLeft);
        var br = wr.ScreenPxPosition(map.ProjectedBottomRight);
        mapBounds = Rectangle.FromLTRB(tl.X, tl.Y, br.X, br.Y);
        CenterLocation = (tl + br) / 2;
    }

    UpdateViewportZooms();
}
```

The viewport is created by `WorldRenderer` during world construction. It computes the initial camera center and the scroll bounds from the map's projected corners. In the editor, the bounds are the full map rectangle; in the game, they are the projected bounding box of the playable map.

### Zoom adjustment

```csharp
public void AdjustZoom(float dz)
{
    Zoom = (zoom * (float)Math.Exp(dz)).Clamp(unlockMinZoom ? unlockedMinZoom : MinZoom, MaxZoom);
}

public void AdjustZoom(float dz, int2 center)
{
    var oldCenter = worldRenderer.Viewport.ViewToWorldPx(center);
    AdjustZoom(dz);
    var newCenter = worldRenderer.Viewport.ViewToWorldPx(center);

    var candidateCenterLocation = CenterLocation + oldCenter - newCenter;
    CenterLocation = candidateCenterLocation.Clamp(mapBounds);
}
```

Zoom is exponential so that zooming in and out by the same amount produces the same visual change. When zooming around a point (for example, the mouse cursor), the viewport adjusts the center so that the world point under the cursor stays stationary. The result is then clamped to `mapBounds`.

### Coordinate transforms

The core transforms are:

```csharp
public int2 ViewToWorldPx(int2 view)
    => (graphicSettings.UIScale / Zoom * view.ToFloat2() + CenterLocation - ViewportSize.ToInt2() / 2).ToInt2();

public int2 WorldToViewPx(int2 world)
    => (Zoom / graphicSettings.UIScale * (world - CenterLocation + ViewportSize.ToInt2() / 2)).ToInt2();

public WPos CenterPosition => worldRenderer.ProjectedPosition(CenterLocation.ToInt2());
```

`WorldRenderer` provides the complementary projection:

```csharp
public int2 ScreenPxPosition(WPos pos)
{
    var px = ScreenPosition(pos);
    return new int2((int)Math.Round(px.X), (int)Math.Round(px.Y));
}

public float2 ScreenPosition(WPos pos)
    => new float2((float)TileSize.Width * pos.X / TileScale, (float)TileSize.Height * (pos.Y - pos.Z) / TileScale);

public WPos ProjectedPosition(int2 screenPx)
    => new WPos(TileScale * screenPx.X / TileSize.Width, TileScale * screenPx.Y / TileSize.Height, 0);
```

`ScreenPxPosition` converts a 3D world position to a 2D screen pixel. `ProjectedPosition` is the inverse for a point on the ground plane. The subtraction of `pos.Z` in `ScreenPosition` is what makes objects higher in the world appear higher on the screen, enabling isometric depth.

### Input handling

The game implements `IInputHandler` through `DefaultInputHandler`:

```csharp
public class DefaultInputHandler : IInputHandler
{
    readonly World world;
    public DefaultInputHandler(World world) { this.world = world; }

    public void ModifierKeys(Modifiers mods) { Game.HandleModifierKeys(mods); }
    public void OnKeyInput(KeyInput input) { Sync.RunUnsynced(world, () => Ui.HandleKeyPress(input)); }
    public void OnTextInput(string text) { Sync.RunUnsynced(world, () => Ui.HandleTextInput(text)); }
    public void OnMouseInput(MouseInput input) { Sync.RunUnsynced(world, () => Ui.HandleInput(input)); }
}
```

`MouseInput` contains the event type (`Down`, `Move`, `Up`, `Scroll`), button, location, delta, modifiers, and multi-tap count. `KeyInput` contains the event type, key, modifiers, multi-tap count, unicode character, and repeat flag.

### Mouse to order

When a mouse event reaches the world, the current order generator converts it to orders:

```csharp
public interface IOrderGenerator
{
    MouseButton ActionButton { get; }
    IEnumerable<Order> Order(World world, CPos cell, int2 worldPixel, MouseInput mi);
    void Tick(World world);
    IEnumerable<IRenderable> Render(WorldRenderer wr, World world);
    IEnumerable<IRenderable> RenderAboveShroud(WorldRenderer wr, World world);
    IEnumerable<IRenderable> RenderAnnotations(WorldRenderer wr, World world);
    string GetCursor(World world, CPos cell, int2 worldPixel, MouseInput mi);
    void Deactivate();
    bool HandleKeyPress(KeyInput e);
    void SelectionChanged(World world, IEnumerable<Actor> selected);
}
```

`WorldInteractionControllerWidget.ApplyOrders` is the bridge:

```csharp
void ApplyOrders(World world, MouseInput mi)
{
    if (world.OrderGenerator == null)
        return;

    var cell = worldRenderer.Viewport.ViewToWorld(mi.Location);
    var worldPixel = worldRenderer.Viewport.ViewToWorldPx(mi.Location);
    var orders = world.OrderGenerator.Order(world, cell, worldPixel, mi).ToArray();
    orders.PlayVoiceForOrders();

    foreach (var o in orders)
    {
        if (o == null)
            continue;

        // Visual feedback flashes
        ...

        world.IssueOrder(o);
    }
}
```

### Order issue

When the order generator returns orders, the game issues them through `World.IssueOrder`:

```csharp
public void IssueOrder(Order o) { OrderManager.IssueOrder(o); }
```

`OrderManager.IssueOrder` queues the order for the local player and, in network games, serializes it for transmission to other clients (see [Part 9.1 — OrderManager and Lockstep Foundation](Part_09_Chapter_01_OrderManager.md)).

![Configuration (yaml) diagram](images/Part_04_Chapter_04_Viewport_Input-annotated-yaml-snippet-diagram-showing-the-key-fields-and-ho-6a1b98.svg)

## Configuration (YAML)


### Viewport sizes

`WorldViewportSizes` is a global mod data object defined in the mod manifest:

```yaml
WorldViewportSizes:
    CloseWindowHeights: 480, 600
    MediumWindowHeights: 600, 900
    FarWindowHeights: 900, 1300
    DefaultScale: 1.0
    MaxZoomScale: 2.0
    MaxZoomWindowHeight: 240
    AllowNativeZoom: true
```

- `CloseWindowHeights`, `MediumWindowHeights`, `FarWindowHeights` — height ranges for the three viewport distances (selected by the player in settings as `WorldViewport.Close`, `Medium`, or `Far`).
- `DefaultScale` — the base scale applied to the native resolution before computing zoom limits.
- `MaxZoomScale` — the maximum zoom-in factor relative to the minimum zoom.
- `MaxZoomWindowHeight` — the smallest window height considered when computing the maximum zoom.
- `AllowNativeZoom` — if true, the player can select a "native" viewport distance that uses `DefaultScale` directly.

The `WorldViewport` setting is stored in the player's `settings.yaml` under `Graphics.ViewportDistance`, not in mod YAML. The mod only provides the allowable size ranges.

### Input settings

Input settings are in `settings.yaml`:

```yaml
Input:
    MouseButtonPreference: Left
    UseClassicMouseStyle: false
    KeyboardLayout: Default
```

`MouseButtonPreference` and `UseClassicMouseStyle` change how left/right clicks are interpreted by `UnitOrderGenerator` and `WorldInteractionControllerWidget`. The classic style uses left-click for orders and right-click for selection, while the default style is the opposite.

### Order generator registration

Order generators are typically created by UI widgets or hotkey handlers. They are not registered in YAML; they are set on `World.OrderGenerator` at runtime. For example, `CommandBarLogic` creates an `AttackMoveOrderGenerator` when the attack-move button is clicked, and `PlaceBuildingOrderGenerator` is created when a support power is selected.

## Interconnectivity

- **Depends on:** [Part 1.1 — Entity-Component-System (ECS) and Actor Lifecycle](Part_01_Chapter_01_ECS.md), [Part 1.3 — World, OrderManager, and Orders](Part_01_Chapter_03_World_Orders.md), [Part 2.2 — Manifest and Mod Metadata](Part_02_Chapter_02_Manifest.md), [Part 2.3 — FieldLoader](Part_02_Chapter_03_FieldLoader.md), [Part 2.4 — Rulesets, Actors, and Weapons](Part_02_Chapter_04_Rules_Weapons.md), [Part 4.1 — Renderer, Sheet, and Sprite](Part_04_Chapter_01_Renderer.md), [Part 4.2 — WorldRenderer](Part_04_Chapter_02_WorldRenderer.md), [Part 4.3 — Widgets and Chrome](Part_04_Chapter_03_Widgets.md), [Part 6.3 — Virtual File System](Part_06_Chapter_03_VFS.md), [Part 7.8 — Random Map Generator Extension Points](Part_07_Chapter_08_Extension_Points.md) (camera bounds for generated maps).
- **Used by:** [Part 1.3 — World, OrderManager, and Orders](Part_01_Chapter_03_World_Orders.md), [Part 4.2 — WorldRenderer](Part_04_Chapter_02_WorldRenderer.md), [Part 4.3 — Widgets and Chrome](Part_04_Chapter_03_Widgets.md), [Part 8.1 — IBot and ModularBot](Part_08_Chapter_01_IBot.md), [Part 9.1 — OrderManager and Lockstep Foundation](Part_09_Chapter_01_OrderManager.md), [Part 10.3 — Porting, Modding, and Developer Workflows](Part_10_Chapter_03_Port_And_Modding.md).

![Algorithms diagram](images/Part_04_Chapter_04_Viewport_Input-algorithm-diagram-or-pseudocode-flowchart-for-the-non-trivia-5983ed.svg)

## Algorithms


### Visible cell region

The viewport computes the set of visible cells (`ProjectedCellRegion`) from the current view rectangle. The algorithm in `CalculateVisibleCells`:

1. Project the top-left and bottom-right corners of the view rectangle onto the ground plane with `WorldRenderer.ProjectedPosition`.
2. Convert the projected points to map cells.
3. For rectangular-isometric maps, expand the rectangle by one cell in each direction because isometric edges are not axis-aligned.
4. Clamp to the map bounds if `insideBounds` is true.

The result is cached in `VisibleCellsInsideBounds` and `AllVisibleCells` until `CenterLocation` or `Zoom` changes (which sets `cellsDirty`/`allCellsDirty`). This region is used by `TerrainRenderer` to decide which tiles to draw and by `World.ScreenMap` for culling.

### Scroll clamping

`CenterLocation` is clamped to `mapBounds` so the camera cannot scroll past the edge of the map:

```csharp
public void Scroll(float2 delta, bool ignoreBorders)
{
    CenterLocation += 1f / Zoom * delta;
    cellsDirty = true;
    allCellsDirty = true;

    if (!ignoreBorders)
        CenterLocation = CenterLocation.Clamp(mapBounds);
}

public void AdjustZoom(float dz, int2 center)
{
    var oldCenter = worldRenderer.Viewport.ViewToWorldPx(center);
    AdjustZoom(dz);
    var newCenter = worldRenderer.Viewport.ViewToWorldPx(center);

    var candidateCenterLocation = CenterLocation + oldCenter - newCenter;
    CenterLocation = candidateCenterLocation.Clamp(mapBounds);
}
```

The `GetBlockedDirections` helper returns which edge of the map the camera is currently touching, useful for disabling scroll arrows or edge-scroll in those directions.

### Zoom extents

`MinZoom` and `MaxZoom` are computed in `UpdateViewportZooms`:

1. Read `graphicSettings.ViewportDistance` (Close/Medium/Far/Native).
2. If `AllowNativeZoom` and the distance is `Native`, use `DefaultScale` as `MinZoom`.
3. Otherwise, use `CalculateMinimumZoom` to find a clean zoom factor that keeps the native resolution within the selected height range.
4. `MaxZoom` is the smaller of `MinZoom * MaxZoomScale` and `NativeResolution.Height * defaultScale / MaxZoomWindowHeight`.
5. If the mod has unlocked the minimum zoom (for spectators or the editor), compute `unlockedMinZoom` and allow zooming out further.

The final zoom is clamped to `[MinZoom, MaxZoom]` (or `[unlockedMinZoom, MaxZoom]` if unlocked). The renderer is notified of the maximum viewport size so the world framebuffer can be allocated accordingly.

### Multi-tap detection

The input layer counts rapid successive clicks on the same button. The `MultiTapDetection` class keeps a history of the last three releases for each button/key and returns a tap count of 1, 2, or 3 if the releases are within 250 ms and 4 pixels of each other:

```csharp
static bool CloseEnough((DateTime Time, int2 Location) a, (DateTime Time, int2 Location) b)
{
    return a.Time - b.Time < TimeSpan.FromMilliseconds(250)
        && (a.Location - b.Location).Length < 4;
}
```

`MultiTapCount` is stored in `MouseInput` and `KeyInput`. In `WorldInteractionControllerWidget`, a `MultiTapCount >= 2` on the left mouse up triggers double-click selection of all on-screen actors that share the same selection class as the actor under the cursor.

### Mouse delta handling

For drag operations, the mouse delta is tracked between frames in `MouseInput.Delta`. `WorldInteractionControllerWidget` tracks `dragStart` and `mousePos` in world pixels and uses `SelectionUtils.SelectActorsInBoxWithDeadzone` to select actors inside the drag box. The drag box is only considered valid if the cursor has moved more than `Game.Settings.Game.SelectionDeadzone` pixels, preventing accidental selection on a single click.

### Drag gesture flow

A typical drag selection works like this:

1. `MouseInputEvent.Down` on left button in `WorldInteractionControllerWidget` calls `TakeMouseFocus` and records `dragStart = ViewToWorldPx(location)`.
2. `MouseInputEvent.Move` updates `mousePos` and draws the selection rectangle in `Draw()`.
3. `MouseInputEvent.Up` checks `IsValidDragbox` and, if valid, selects all actors in the box. If the drag is too small, it is treated as a single click and may issue an order instead.
4. On mouse up, `YieldMouseFocus` is called and the drag state is cleared.

### Order generator selection logic

`UnitOrderGenerator` is the default order generator. It decides whether a click should select or order by calling `InputOverridesSelection`:

- If the target is an actor and the selected units have a valid order against that target (for example, attack or repair), the click issues an order.
- Otherwise, the click selects the actor.
- With the classic mouse style, the logic is reversed: left-click orders and right-click selects.

Custom order generators (such as `GuardOrderGenerator`) override `InputOverridesSelection` to always return true, so the cursor is never interpreted as a selection cursor while the special mode is active.

![Extension points diagram](images/Part_04_Chapter_04_Viewport_Input-extension-hook-diagram-showing-the-interface-s-to-implement-b4a27b.svg)

## Extension Points


### Add a custom order generator

Implement `IOrderGenerator` and set it as `World.OrderGenerator`. The generator can draw a custom cursor via `GetCursor`, render target lines and preview sprites via `Render`/`RenderAboveShroud`, and issue orders via `Order`. This is how support power placement and attack-move work. Inherit from `OrderGenerator` in `OpenRA.Mods.Common` to reuse the `ActionButton`/`CancelButton` plumbing.

### Add custom input handling

Widgets can override `HandleMouseInput` and `HandleKeyInput` to consume input before it reaches the order generator. The main menu and lobby are entirely widget-driven. For world input, create a custom widget and add it to the world chrome; it will receive events after the command bar but before `WorldInteractionControllerWidget` if it is higher in the tree.

### Add a custom viewport controller

Implement `INotifyViewportZoomExtentsChanged` to react to zoom limit changes. The default controller uses `WorldViewportSizes`, but mods can override this. The viewport also exposes `ViewportCenterProvider` and `ViewportTick` for scripted camera movement.

### Add custom cursors

The cursor is chosen by the active order generator's `GetCursor` method. The `CursorManager` maps cursor names to animated or static cursor sequences defined in `mods/<mod>/cursors.yaml`.

![Common pitfalls  guardrails diagram](images/Part_04_Chapter_04_Viewport_Input-checklist-infographic-style-diagram-summarizing-the-top-pitf-fb069e.svg)

## Common Pitfalls / Guardrails


- **UI consumes input first:** if a widget is under the mouse, it will receive the event before the world. Order generators must not assume they always receive mouse events. Check `WorldInteractionControllerWidget` for the actual dispatch point.
- **Keyboard focus:** only the widget with `KeyboardFocusWidget` receives typed text. Ensure text fields acquire focus when activated and yield it when done.
- **Zoom and UI scale:** `Zoom` affects the world view but not the UI scale. `Game.Renderer.WindowScale` is separate. Coordinate transforms must account for both `Zoom` and `graphicSettings.UIScale`.
- **Viewport bounds:** when the map is smaller than the window, the clamping bounds may be larger than the map. Handle edge cases in minimap and overview modes.
- **Coordinate precision:** `WPos` is integer world pixels. Use `ProjectedPosition` for screen-space calculations, not raw world coordinates. Remember that `ViewToWorldPx` returns a screen-space pixel coordinate, not a cell; use `ViewToWorld` for the cell.
- **Order generator cleanup:** call `Deactivate` when switching order generators to clean up cursors and renderables. `World.CancelInputMode` restores the default `UnitOrderGenerator` and deactivates the current one.
- **Mouse capture:** for dragging operations, the widget should grab mouse focus so it receives events even when the cursor leaves the widget bounds. `WorldInteractionControllerWidget` does this via `TakeMouseFocus`/`YieldMouseFocus`.
- **Multi-tap timing:** `MultiTapCount` is based on the last three releases within 250 ms and 4 pixels. If your UI needs stricter double-click behavior, do not rely solely on `MultiTapCount`; add your own timing or distance check.
- **Sync safety:** input handling runs inside `Sync.RunUnsynced`. Do not change world simulation state directly from input handlers; issue `Order` objects so that the change happens deterministically on the next tick.
- **Order generator Tick:** `World.OrderGenerator.Tick(world)` is called once per simulation tick in `Game.Run`. Use it for per-frame preview updates (for example, moving a building placement ghost) but do not issue orders from `Tick` unless the order is deterministic and independent of input.

## What to read next

- [Part 1.3 — World, OrderManager, and Orders](Part_01_Chapter_03_World_Orders.md) for how the generated orders enter the deterministic simulation.
- [Part 4.3 — Widgets and Chrome](Part_04_Chapter_03_Widgets.md) for the widget tree that dispatches input before it reaches the world.
- [Part 9.1 — OrderManager and Lockstep Foundation](Part_09_Chapter_01_OrderManager.md) for the network and lockstep boundary that orders cross.

## Summary

This chapter explains how the [viewport](../appendices/Appendix_A_Glossary.md) maps the simulation world to the screen and routes input through order generators.

After reading this chapter, you should be able to:

- Convert between world, cell, view, and UI coordinate spaces using the `Viewport`.
- Describe the input dispatch pipeline from the SDL2 window to the active order generator and `World.IssueOrder`.
- Implement a custom `IOrderGenerator` that changes the cursor and issues orders.
- Configure `WorldViewportSizes` and input settings in YAML.
- Explain drag gestures, multi-tap selection, scroll clamping, and zoom extents.

If any of the concepts above feel unclear, review the relevant section before continuing. For source files and further reading, see the References section.


## References

- `OpenRA.Game/Graphics/Viewport.cs` — viewport.
- `OpenRA.Game/WorldViewportSizes.cs` — viewport sizes.
- `OpenRA.Game/Input/IInputHandler.cs` — input handler interface and input structs.
- `OpenRA.Game/Input/InputHandler.cs` — default and null input handlers.
- `OpenRA.Game/Input/Keycode.cs` — keycodes.
- `OpenRA.Game/Orders/IOrderGenerator.cs` — order generator interface.
- `OpenRA.Mods.Common/Orders/OrderGenerator.cs` — base order generator.
- `OpenRA.Mods.Common/Orders/UnitOrderGenerator.cs` — default order generator.
- `OpenRA.Mods.Common/Orders/GuardOrderGenerator.cs` — guard order generator.
- `OpenRA.Mods.Common/Orders/PlaceBuildingOrderGenerator.cs` — placement order generator.
- `OpenRA.Mods.Common/Widgets/WorldInteractionControllerWidget.cs` — input-to-order bridge.
- `OpenRA.Game/Game.cs` — top-level loop.
- `OpenRA.Game/World.cs` — `IssueOrder` and `OrderGenerator` property.
- `OpenRA.Platforms.Default/Sdl2Input.cs` — SDL2 input pumping.
- `OpenRA.Platforms.Default/MultiTapDetection.cs` — multi-tap detection.