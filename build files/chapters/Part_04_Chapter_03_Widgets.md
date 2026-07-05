# Chapter 4.3 — Widgets and Chrome

## Purpose

OpenRA's user interface is built on a custom [widget](../appendices/Appendix_A_Glossary.md) system. Menus, HUDs, tooltips, and editors are all declared in YAML "[chrome](../appendices/Appendix_A_Glossary.md)" files and driven by C# logic classes. This chapter explains the widget hierarchy, the `WidgetLoader`, the base widget lifecycle, event propagation, and how chrome interacts with the game world.

![Mental model diagram](images/Part_04_Chapter_03_Widgets-learning-objectives-summary-diagram-or-concept-map-showing-h-fe332a.svg)

## Mental Model

Think of the widget tree as a set of nested picture frames on a glass table.

- **The window** is the outermost frame (`Ui.Root`). Inside it are the menu frames (`MenuRootWidget`) and the in-game frames (`WorldRootWidget`).
- **Every widget** is a smaller frame placed inside its parent. It has its own painting (`Draw`), heartbeat (`Tick`), and touch sensor (`HandleInput`).
- **Layout expressions** (`X`, `Y`, `Width`, `Height`) are the ruler and compass the engine uses to place each frame at load time.
- **Events** are like drops of water falling from above. The topmost frame under the drop gets the first chance to catch them; if it catches the drop, the water stops. If it lets the drop pass, the water drips through to the next frame below.
- **Focus** is the same as holding a frame steady so it continues to catch drops even when the mouse moves away. `MouseFocusWidget` keeps drag events on a widget, and `KeyboardFocusWidget` keeps typed text on a text field.
- **Logic classes** (`ChromeLogic`) are the backstage crew. They are attached to a frame and update its state, but they are not the frame itself.

This mental model explains why events stop at the first widget that handles them (a button on top of a scroll panel prevents the panel from scrolling), why hidden frames do not tick or draw (they are removed from the table), and why `OpenWindow`/`CloseWindow` use a stack (opening a new picture covers the old one without throwing it away). The YAML syntax is parsed by the engine described in [Part 2.1 — MiniYaml Parser](Part_02_Chapter_01_MiniYaml.md) and the data-driven rules in [Part 2.4 — Rulesets, Actors, and Weapons](Part_02_Chapter_04_Rules_Weapons.md); for a complete UI walkthrough see [Part 10.3 — Porting, Modding, and Developer Workflows](Part_10_Chapter_03_Port_And_Modding.md).

## Learning Objectives


After studying this chapter, you should be able to:

- Explain the OpenRA widget hierarchy and the roles of Ui.Root, MenuRootWidget, and WorldRootWidget.
- Describe how YAML chrome files define widget layouts and logic classes.
- Trace the widget lifecycle from loading through Tick, Draw, and input handling.
- Use ChromeMetrics to share UI constants across widgets.
- Implement a custom widget type and a ChromeLogic logic class.
- Explain focus management and the window stack behavior.
- Describe how mouse and keyboard events propagate through the widget tree.
- Author a new chrome layout from YAML to a working screen.

## Files

| File | Responsibility |
| :---- | :---- |
| `OpenRA.Game/Widgets/Widget.cs` | Base `Widget` class, `ContainerWidget`, `InputWidget`, `ChromeLogic`, `Ui` root, input handling, focus management. |
| `OpenRA.Game/Widgets/WidgetLoader.cs` | Loads widget definitions from YAML and instantiates them. |
| `OpenRA.Game/Widgets/ChromeMetrics.cs` | Named UI metrics (colors, sizes, offsets) loaded from YAML. |
| `OpenRA.Mods.Common/Widgets/ButtonWidget.cs` | Button widget. |
| `OpenRA.Mods.Common/Widgets/LabelWidget.cs` | Text label widget. |
| `OpenRA.Mods.Common/Widgets/ImageWidget.cs` | Image widget. |
| `OpenRA.Mods.Common/Widgets/TextFieldWidget.cs` | Editable text field. |
| `OpenRA.Mods.Common/Widgets/DropDownButtonWidget.cs` | Dropdown button widget. |
| `OpenRA.Game/Widgets/Widget.cs` | Defines `ContainerWidget` and the base `Widget` class. |
| `OpenRA.Mods.Common/Widgets/ScrollPanelWidget.cs` | Scrollable panel widget. |
| `OpenRA.Mods.Common/Widgets/CheckboxWidget.cs` | Checkbox widget. |
| `OpenRA.Mods.Common/Widgets/SliderWidget.cs` | Slider widget. |
| `OpenRA.Mods.Common/Widgets/*.cs` | Many common widgets (radar, chat, production, lobby, etc.). |
| `OpenRA.Game/Widgets/Logic/*.cs` | Built-in logic classes. |
| `OpenRA.Mods.Common/Widgets/Logic/*.cs` | Common logic classes (lobby, settings, main menu, etc.). |

![Architecture diagram](images/Part_04_Chapter_03_Widgets-architecture-diagram-showing-the-main-classes-interfaces-and-9161e6.svg)

## Architecture


### Widget tree

![Widget tree](images/Part_04_Chapter_03_Widgets-Widget_tree.svg)

All UI widgets are nodes in a single tree rooted at `Ui.Root`. The engine maintains two main subtrees: the menu chrome (`MenuRootWidget`) and the in-game chrome (`WorldRootWidget`). Windows can be pushed onto a stack so that closing one restores the previous window. Every widget has a `Parent`, a list of `Children`, and `Bounds` expressed in screen coordinates.

### YAML-driven layout

A widget is defined in YAML like this:

```yaml
MainMenu:
    Container:
        X: (WINDOW_WIDTH - WIDTH)/2
        Y: (WINDOW_HEIGHT - HEIGHT)/2
        Width: 400
        Height: 300
        Children:
            Label@TITLE:
                X: 0
                Y: 0
                Width: 400
                Height: 40
                Text: OpenRA
            Button@START:
                X: 50
                Y: 80
                Width: 300
                Height: 40
                Text: Start Game
                Font: Bold
```

The widget type is the node key (e.g., `Container`, `Label`, `Button`). The `@NAME` suffix sets the widget's `Id`. The type name `Foo` in YAML maps to a C# class named `FooWidget` by naming convention. `FieldLoader` maps the remaining YAML keys to public fields or properties on the widget class.

### Logic classes

Widgets can have one or more `Logic` classes declared in YAML:

```yaml
MainMenu:
    Container:
        Logic: MainMenuLogic
        ...
```

The logic class must inherit `ChromeLogic` and is instantiated when the widget is loaded. It receives the widget and any `WidgetArgs` passed during loading. Logic classes handle events, update widget state, and implement screen behavior. The `Logic` field can be a single string or a comma-separated list; multiple logic objects are created in order and each receives `Tick`, `BecameHidden`, and `BecameVisible`.

### Metrics

`ChromeMetrics` is a global dictionary of UI values shared across widgets:

```yaml
Metrics:
    TextfieldColorHighlight: 3A8C3A
    ButtonTextColor: FFFFFF
    ButtonTextColorDisabled: 808080
```

Widgets reference these keys in code via `ChromeMetrics.Get<T>("key")`. They are loaded from the files listed in the manifest's `ChromeMetrics` section. Metrics are commonly used for colors, default cursors, button sizes, and spacing constants.

### Widget lifecycle

The complete lifecycle of a widget is:

```
WidgetLoader.LoadWidget
  -> NewWidget (ObjectCreator creates FooWidget by naming convention)
  -> AddChild to parent
  -> Load Id from "Type@Id"
  -> FieldLoader loads fields from YAML (except Children)
  -> Initialize(args)        // evaluates layout expressions, sets Bounds
  -> recursively LoadWidget for each child
  -> PostInit(args)          // creates ChromeLogic objects
  -> TickOuter() each frame  // calls Tick(), then children, then Logic.Tick()
  -> DrawOuter() each frame  // calls Draw(), then children
  -> HandleMouseInputOuter() / HandleKeyPressOuter() / HandleTextInputOuter()
  -> Hidden() / Removed()    // logic objects receive BecameHidden / Dispose
```

Important lifecycle details:

- `Initialize` is called after the widget object is created and its fields are loaded, but before children are created. This is where `Bounds` is evaluated from the `X`, `Y`, `Width`, `Height` expressions.
- `PostInit` is called after all children are created. It instantiates the `ChromeLogic` classes listed in the `Logic` field, adds them to `LogicObjects`, and subscribes them to the `Ui` mediator.
- `TickOuter` visits children in order and then ticks each logic object. Only visible widgets tick; hidden widgets are skipped entirely.
- `DrawOuter` visits children in order. Only visible widgets draw.
- `Hidden()` is called when a widget is removed from its parent by `HideChild` (for example, when a new window is opened and the old one is hidden). It forces the widget to yield mouse and keyboard focus and propagates `Hidden()` to children. The logic objects receive `BecameHidden` from `Ui.OpenWindow`/`CloseWindow`.
- `Removed()` is called when a widget is permanently removed. It yields focus and disposes logic objects.

### Event propagation

Mouse and keyboard events travel from the root down to the leaves. The first widget that consumes the event stops propagation. Focus widgets receive keyboard events even if they are not under the mouse.

#### Mouse events

`Ui.HandleInput` is the entry point:

1. If a widget already owns `MouseFocusWidget`, it is given the event first. This allows a widget to continue receiving drag events even when the cursor leaves its bounds.
2. If the focus widget does not consume the event, the event is dispatched to `Root.HandleMouseInputOuter`, which recurses from the root down to the deepest visible child whose `EventBounds` contains the mouse position.
3. For each candidate widget, `HandleMouseInputOuter` first forwards the event to its children in reverse order (topmost child first), then calls `HandleMouseInput` on itself.
4. If a child handles the event, propagation stops immediately.
5. On `MouseInputEvent.Move`, the deepest widget that is not marked `IgnoreMouseOver` becomes `Ui.MouseOverWidget`. `MouseEntered`/`MouseExited` are raised when the mouse-over widget changes.

A widget can request mouse focus by calling `TakeMouseFocus`. It should yield focus with `YieldMouseFocus` when the drag or click ends. Without focus, a widget only receives mouse events while the cursor is inside its `EventBounds`.

#### Keyboard events

`Ui.HandleKeyPress` is the entry point:

1. If `KeyboardFocusWidget` is set, the key press goes to `KeyboardFocusWidget.HandleKeyPressOuter`.
2. Otherwise, the event is dispatched from `Root.HandleKeyPressOuter`, which recurses through children in reverse order and calls `HandleKeyPress` if no child consumed it.
3. `Ui.HandleTextInput` follows the same pattern for text input events.

Text fields should call `TakeKeyboardFocus` when activated; otherwise typed characters will bubble up to the root and may be interpreted as hotkeys.

#### Event propagation example

Consider a settings panel with a button and a scrollable list. The panel is the parent, the scrollable list is a child, and the button is a child of the list.

```yaml
SettingsPanel:
    Container:
        X: (WINDOW_WIDTH - WIDTH) / 2
        Y: (WINDOW_HEIGHT - HEIGHT) / 2
        Width: 500
        Height: 400
        Logic: SettingsPanelLogic
        Children:
            ScrollPanel@LIST:
                X: 20
                Y: 20
                Width: 460
                Height: 300
                Children:
                    Button@OK:
                        X: 0
                        Y: 0
                        Width: 100
                        Height: 40
                        Text: OK
```

```csharp
public class SettingsPanelLogic : ChromeLogic
{
    public SettingsPanelLogic(Widget widget)
    {
        var list = widget.Get<ScrollPanelWidget>("LIST");
        var ok = list.Get<ButtonWidget>("OK");

        ok.OnClick = () =>
        {
            // This click is handled by the button. The scroll panel
            // never sees the event, so it cannot scroll while the
            // button is being clicked.
            Ui.CloseWindow();
        };

        list.OnMouseDown = mi =>
        {
            // Clicks that miss the button fall through to the scroll
            // panel, which can use them for drag-scrolling.
            return true;
        };
    }
}
```

If the cursor is over the button, `HandleMouseInputOuter` visits the button first. The button returns `true` from `OnMouseDown`, so the event stops. If the cursor is over the scroll panel but not over the button, the button still receives the event first because it is a child, but it returns `false` (or is outside `EventBounds`), so the event reaches the scroll panel. This is why a click on a button inside a scroll panel does not scroll the list.

### Focus management

`Ui.MouseFocusWidget`, `Ui.KeyboardFocusWidget`, and `Ui.MouseOverWidget` are static references that track which widget currently owns input focus. Widgets can request focus in `OnMouseDown` or `OnKeyPress`. Focus is yielded automatically when a widget is hidden or removed, but widgets can also override `YieldMouseFocus` or `YieldKeyboardFocus` to refuse focus loss (for example, a modal dialog).

![Data flow  code path diagram](images/Part_04_Chapter_03_Widgets-sequence-flow-diagram-tracing-the-execution-path-from-trigge-035864.svg)

## Data Flow / Code Path


### Loading chrome

`WidgetLoader` reads the files listed in the manifest's `ChromeLayout`:

```csharp
public WidgetLoader(Manifest manifest, IReadOnlyFileSystem fileSystem)
{
    var stringPool = new HashSet<string>(); // Reuse common strings in YAML
    foreach (var file in manifest.ChromeLayout.Select(
        a => MiniYaml.FromStream(fileSystem.Open(a), a, stringPool: stringPool)))
        foreach (var w in file)
        {
            var key = w.Key[(w.Key.IndexOf('@') + 1)..];
            if (widgets.ContainsKey(key))
                throw new InvalidDataException($"Widget has duplicate Key `{w.Key}` at {w.Location}");
            widgets.Add(key, w);
        }
}
```

Each top-level key in a chrome YAML file becomes the name that can be passed to `Ui.OpenWindow`. The loader stores the whole YAML node under that key, so layout definitions can be instantiated many times.

### Instantiating a widget

```csharp
public Widget LoadWidget(WidgetArgs args, Widget parent, MiniYamlNode node)
{
    var widget = NewWidget(node.Key, args);
    parent?.AddChild(widget);

    if (node.Key.Contains('@'))
        FieldLoader.LoadFieldOrProperty(widget, "Id", node.Key.Split('@')[1]);

    foreach (var child in node.Value.Nodes)
        if (child.Key != "Children")
            FieldLoader.LoadFieldOrProperty(widget, child.Key, child.Value.Value);

    widget.Initialize(args);

    foreach (var child in node.Value.Nodes)
        if (child.Key == "Children")
            foreach (var c in child.Value.Nodes)
                LoadWidget(args, widget, c);

    var logicNode = node.Value.NodeWithKeyOrDefault("Logic");
    var logic = logicNode?.Value.ToDictionary();
    args.Add("logicArgs", logic);

    widget.PostInit(args);

    args.Remove("logicArgs");

    return widget;
}
```

`NewWidget` strips the `@Id` suffix and appends `Widget` to find the C# class, then creates it via `ObjectCreator`. Fields are loaded before children so that children can reference parent state during their own initialization. `Logic` is loaded after children because logic classes often look up child widgets by ID in their constructor.

### Opening a window

```csharp
public static Widget OpenWindow(string id, WidgetArgs args)
{
    if (!args.ContainsKey("modData"))
        args = new WidgetArgs(args) { { "modData", modData } };

    var window = Game.ModData.WidgetLoader.LoadWidget(args, Root, id);
    if (WindowList.Count > 0)
        Root.HideChild(WindowList.Peek());
    WindowList.Push(window);
    return window;
}
```

`OpenWindow` loads the top-level widget definition, adds it to `Ui.Root`, and pushes it onto the window stack. If a window is already open, it is hidden (not removed) so that `CloseWindow` can restore it. Hidden windows have their logic objects receive `BecameHidden` so they can pause animations or stop ticking expensive logic.

### Per-frame tick

```csharp
public static void Tick() { Root.TickOuter(); }
```

Widgets receive `Tick` from root to leaves. `TickOuter` first checks `IsVisible`, calls the widget's `Tick`, recurses into children, and then ticks each `LogicObject`. Logic classes can also implement `LogicTick` indirectly through `ChromeLogic.Tick`. Because hidden widgets do not tick, opening a modal window naturally pauses the screen underneath.

### Drawing

```csharp
public static void Draw()
{
    if (!WidgetsVisible)
        return;
    Root.DrawOuter();
}
```

Widgets draw from root to leaves. Each widget is responsible for its own background and children. `DrawOuter` short-circuits invisible subtrees, so hiding a container hides all of its children.

### Input handling

```csharp
public static bool HandleInput(MouseInput mi)
{
    var wasMouseOver = MouseOverWidget;

    if (mi.Event == MouseInputEvent.Move)
        MouseOverWidget = null;

    var handled = false;
    if (MouseFocusWidget != null && MouseFocusWidget.HandleMouseInputOuter(mi))
        handled = true;

    if (!handled && Root.HandleMouseInputOuter(mi))
        handled = true;

    if (mi.Event == MouseInputEvent.Move)
    {
        Viewport.LastMousePos = mi.Location;
        Viewport.LastMoveRunTime = Game.RunTime;
    }

    if (wasMouseOver != MouseOverWidget)
    {
        wasMouseOver?.MouseExited();
        MouseOverWidget?.MouseEntered();
    }

    return handled;
}
```

Mouse and keyboard events are dispatched down the tree. The first widget that consumes the event stops propagation. Focus widgets receive keyboard events. The `MouseOverWidget` is recalculated on every move event so that widgets can respond to hover state.

![Configuration (yaml) diagram](images/Part_04_Chapter_03_Widgets-annotated-yaml-snippet-diagram-showing-the-key-fields-and-ho-6a1b98.svg)

## Configuration (YAML)


### Chrome layout

```yaml
ChromeLayout:
    - mods/common/chrome/mainmenu.yaml
    - mods/common/chrome/ingame.yaml
    - mods/common/chrome/lobby.yaml
```

### Chrome metrics

```yaml
ChromeMetrics:
    - mods/common/metrics.yaml
```

### Widget type registration

Widget classes are discovered by naming convention: `FooWidget` in YAML maps to class `FooWidget` in the loaded assemblies. The `WidgetLoader` constructs the class by passing the name to `ObjectCreator`, which looks for `FooWidget` in all loaded assemblies.

### Logic registration

Logic classes are instantiated via `ObjectCreator`. They must have a constructor that matches the provided `WidgetArgs`. The `widget` argument is always added before `PostInit` and removed afterward. Other common arguments include `modData`, `world`, `orderManager`, and `onExit`.

![Chrome authoring workflow diagram](images/Part_04_Chapter_03_Widgets-widget-tree-diagram-showing-parent-child-nesting-focus-path-3925dd.svg)

## Chrome authoring workflow


To add a new screen or panel to a mod, follow this workflow:

1. **Create a YAML chrome layout file.** Add a new file under `mods/<mod>/chrome/` or `mods/common/chrome/`. The top-level key is the ID that will be passed to `Ui.OpenWindow`.
2. **Pick a root widget type.** Usually a `Container` or `Background` with `X`, `Y`, `Width`, and `Height` expressions that center the window on screen. Use `WINDOW_WIDTH`, `WINDOW_HEIGHT`, `PARENT_WIDTH`, `PARENT_HEIGHT`, `WIDTH`, and `HEIGHT` in expressions.
3. **Add child widgets.** Use `Label`, `Button`, `ImageWidget`, `TextField`, `DropDownButton`, `Checkbox`, `Slider`, `ScrollPanel`, etc. Give each child an `@Id` so it can be looked up from logic code.
4. **Bind a logic class.** Add `Logic: MyScreenLogic` to the root widget. Create `MyScreenLogic` inheriting `ChromeLogic` in `OpenRA.Mods.Common/Widgets/Logic/` (or the mod's widget logic folder). In the constructor, look up child widgets with `widget.Get<ButtonWidget>("START")` and attach event handlers.
5. **Add ChromeMetrics entries.** If the screen uses shared colors, sizes, or cursors, add them to the mod's `metrics.yaml` and load them with `ChromeMetrics.Get<T>("MyKey")`.
6. **Register the layout in mod.yaml.** Add the new chrome file to the `ChromeLayout` list.
7. **Open the window.** Call `Ui.OpenWindow("MyScreen", new WidgetArgs { { "world", world }, { "onExit", onExit } })` from a button, console command, or hotkey handler. Use `Ui.CloseWindow()` to return to the previous window.

A minimal example:

```yaml
MyScreen:
    Container:
        X: (WINDOW_WIDTH - WIDTH)/2
        Y: (WINDOW_HEIGHT - HEIGHT)/2
        Width: 400
        Height: 200
        Logic: MyScreenLogic
        Children:
            Label@TITLE:
                X: 0
                Y: 20
                Width: 400
                Height: 30
                Text: My Screen
                Align: Center
            Button@CLOSE:
                X: 150
                Y: 120
                Width: 100
                Height: 40
                Text: Close
```

```csharp
public class MyScreenLogic : ChromeLogic
{
    public MyScreenLogic(Widget widget, World world)
    {
        var closeButton = widget.Get<ButtonWidget>("CLOSE");
        closeButton.OnClick = () => Ui.CloseWindow();
    }
}
```

## Widget conventions

When working with widgets, follow these conventions:

- **Naming convention.** A widget class must be named `FooWidget` and be declared in YAML as `Foo`. The class must inherit `Widget` (or a subclass like `ContainerWidget`).
- **ID syntax.** Use `Type@Id` in YAML to set the widget's `Id` field. IDs must be unique within their subtree for `Get<T>` to be unambiguous.
- **FieldLoader mapping.** YAML keys map to public fields or properties by exact name. Types must be compatible with `FieldLoader.GetValue<T>`. For example, `Text: Hello` sets the `Text` field; `Font: Bold` sets the `Font` field.
- **Logic classes live in `Widgets/Logic`.** Keep UI behavior in logic classes, not in widget classes. Widget classes should be reusable presentation components; logic classes own screen-specific state and event wiring.
- **Common widget types.**
  - `ButtonWidget` — clickable button with text and optional key binding.
  - `LabelWidget` — read-only text label.
  - `ImageWidget` — static or animated [sprite](../appendices/Appendix_A_Glossary.md) image.
  - `TextFieldWidget` — editable text field; takes keyboard focus.
  - `DropDownButtonWidget` — button that opens a dropdown panel.
  - `CheckboxWidget` — boolean toggle.
  - `SliderWidget` — numeric value slider.
  - `ScrollPanelWidget` — scrollable container.
  - `ContainerWidget` — non-visual grouping container with optional click-through.
- **Layout expressions.** `X`, `Y`, `Width`, and `Height` can be integer expressions using the variables `WINDOW_WIDTH`, `WINDOW_HEIGHT`, `PARENT_WIDTH`, `PARENT_HEIGHT`, `WIDTH`, `HEIGHT`, and `DROPDOWN_WIDTH` (for dropdown panels). Earlier engine versions used `WINDOW_RIGHT`, `WINDOW_BOTTOM`, `PARENT_RIGHT`, and `PARENT_BOTTOM`; those are now `WINDOW_WIDTH`/`WINDOW_HEIGHT` and `PARENT_WIDTH`/`PARENT_HEIGHT`. Expressions are evaluated at initialization time.
- **Focus management.** Mouse-driven widgets should not call `TakeKeyboardFocus` unless they need typed input. Keyboard-driven widgets should yield focus when done so hotkeys work again.
- **Visibility.** Set `Visible = false` to hide a widget and its entire subtree. Hidden widgets do not tick, draw, or receive input. Use `IsVisible` as a lambda if visibility depends on runtime state.

## Interconnectivity

- **Depends on:** [Part 1.1 — Entity-Component-System (ECS) and Actor Lifecycle](Part_01_Chapter_01_ECS.md), [Part 1.3 — World, OrderManager, and Orders](Part_01_Chapter_03_World_Orders.md), [Part 2.1 — MiniYaml Parser](Part_02_Chapter_01_MiniYaml.md), [Part 2.4 — Rulesets, Actors, and Weapons](Part_02_Chapter_04_Rules_Weapons.md), [Part 3.1 — Mod SDK and Project Structure](Part_03_Chapter_01_Mod_SDK.md), [Part 4.1 — Renderer, Sheet, and Sprite](Part_04_Chapter_01_Renderer.md), [Part 4.4 — Viewport and Input](Part_04_Chapter_04_Viewport_Input.md), [Part 6.3 — Virtual File System](Part_06_Chapter_03_VFS.md).
- **Used by:** [Part 4.2 — WorldRenderer](Part_04_Chapter_02_WorldRenderer.md), [Part 4.4 — Viewport and Input](Part_04_Chapter_04_Viewport_Input.md), [Part 7.8 — Random Map Generator Extension Points](Part_07_Chapter_08_Extension_Points.md), [Part 8.1 — IBot and ModularBot](Part_08_Chapter_01_IBot.md), [Part 9.2 — Server and Connection Layer](Part_09_Chapter_02_Server_Connection.md), [Part 10.3 — Porting, Modding, and Developer Workflows](Part_10_Chapter_03_Port_And_Modding.md).

![Algorithms diagram](images/Part_04_Chapter_03_Widgets-algorithm-diagram-or-pseudocode-flowchart-for-the-non-trivia-5983ed.svg)

## Algorithms


### Widget lookup

Widgets can be found by ID: `widget.Get<ButtonWidget>("START")` or `widget.GetOrNull<ButtonWidget>("START")`. The lookup searches the subtree recursively. `Get` throws if the widget is missing or the wrong type; `GetOrNull` returns null. For performance, lookups should be done once in the logic constructor and cached, not every frame.

### Focus management

`Ui.MouseFocusWidget`, `Ui.KeyboardFocusWidget`, and `Ui.MouseOverWidget` track which widget currently owns input focus. Widgets can request focus in `OnMouseDown` or `OnKeyPress`. `TakeMouseFocus` and `TakeKeyboardFocus` first ask the current focus owner to yield; if the owner refuses, focus is not stolen. This prevents, for example, a modal dialog from losing focus to a background click.

### Window stack

`Ui.OpenWindow` pushes a new window onto a stack and hides the previous one. `Ui.CloseWindow` pops the stack and restores the previous window. This makes modal dialogs easy to implement. The window stack lives in `Ui` as a static `Stack<Widget>`. Only the window at the top of the stack is attached to `Ui.Root`; hidden windows are detached but not disposed, so their state is preserved.

### Visible/hidden lifecycle

When a widget is hidden, its `LogicObjects` receive `BecameHidden`. When a hidden widget is restored, they receive `BecameVisible`. This is used to pause/resume animations or tick logic. The widget itself receives `Hidden()` and `Removed()`; `Removed()` also disposes the logic objects and unsubscribes them from the `Ui` mediator.

### Layout expressions

Widget positions/sizes can be expressions using variables like `WINDOW_WIDTH`, `WINDOW_HEIGHT`, `PARENT_WIDTH`, `PARENT_HEIGHT`, `WIDTH`, `HEIGHT`, and `DROPDOWN_WIDTH` (historically `WINDOW_RIGHT`, `WINDOW_BOTTOM`, `PARENT_RIGHT`, `PARENT_BOTTOM`). These are evaluated by `Widget.Initialize` through `IntegerExpression.Evaluate`. The expressions are evaluated once at load time, so they do not respond to window resizing unless the widget is reloaded or its bounds are explicitly updated in code.

### Layout variable reference

The layout evaluator in `OpenRA.Game/Widgets/Widget.cs` exposes the following integer symbols when it evaluates a widget's `X`, `Y`, `Width`, and `Height` expressions:

| Variable | Source | Meaning |
| :---- | :---- | :---- |
| `WINDOW_WIDTH` | `OpenRA.Game/Widgets/Widget.cs` | Width of the game window in screen pixels. |
| `WINDOW_HEIGHT` | `OpenRA.Game/Widgets/Widget.cs` | Height of the game window in screen pixels. |
| `PARENT_WIDTH` | `OpenRA.Game/Widgets/Widget.cs` | Width of the widget's parent container. For a root widget, this equals `WINDOW_WIDTH`. |
| `PARENT_HEIGHT` | `OpenRA.Game/Widgets/Widget.cs` | Height of the widget's parent container. For a root widget, this equals `WINDOW_HEIGHT`. |
| `WIDTH` | `OpenRA.Game/Widgets/Widget.cs` | The evaluated width of this widget; can be used in `X` and `Y` expressions. |
| `HEIGHT` | `OpenRA.Game/Widgets/Widget.cs` | The evaluated height of this widget; can be used in `X` and `Y` expressions. |
| `DROPDOWN_WIDTH` | `OpenRA.Mods.Common/Widgets/DropDownButtonWidget.cs` | Width of the dropdown button that opened a panel; injected into the panel's `substitutions` widget args so the panel can align to the button. |

`WIDTH` and `HEIGHT` are evaluated before `X` and `Y`, so a widget can reference its own size when positioning itself. For example, `X: (WINDOW_WIDTH - WIDTH) / 2` centers the widget horizontally.

Older versions of OpenRA provided `WINDOW_RIGHT`, `WINDOW_BOTTOM`, `PARENT_RIGHT`, and `PARENT_BOTTOM` as layout symbols. These were renamed to `WINDOW_WIDTH`, `WINDOW_HEIGHT`, `PARENT_WIDTH`, and `PARENT_HEIGHT` because the right and bottom edges of the window or parent equal the width and height in the top-left-anchored coordinate system. The update rule `OpenRA.Mods.Common/UpdateRules/Rules/20231010/RenameWidgetSubstitutions.cs` can migrate old chrome files that still use the old names. In current YAML, use `WINDOW_WIDTH` where older examples used `WINDOW_RIGHT`, and `PARENT_WIDTH` where they used `PARENT_RIGHT`.

There are no `HORIZONTAL_ALIGNMENT` or `VERTICAL_ALIGNMENT` layout symbols. Alignment is handled by widget-specific fields such as `Align` on `LabelWidget`, or by explicit layout expressions.

#### Common anchor patterns

These expressions cover the most common placements:

| Result | X | Y | Width | Height |
| :---- | :---- | :---- | :---- | :---- |
| Center horizontally | `(WINDOW_WIDTH - WIDTH) / 2` | N/A | N/A | N/A |
| Center vertically | N/A | `(WINDOW_HEIGHT - HEIGHT) / 2` | N/A | N/A |
| Bottom-right corner | `WINDOW_WIDTH - WIDTH` | `WINDOW_HEIGHT - HEIGHT` | N/A | N/A |
| Top-left corner | `0` | `0` | N/A | N/A |
| Full window width | `0` | N/A | `WINDOW_WIDTH` | N/A |
| Fill parent | `0` | `0` | `PARENT_WIDTH` | `PARENT_HEIGHT` |

An `N/A` entry means the field is not dictated by the pattern and can be set to a fixed value or another expression.

#### Percentages

Percentage values are not natively supported in layout expressions. Use fractional arithmetic instead: `WINDOW_WIDTH / 4` gives 25% of the window width, `PARENT_HEIGHT * 2 / 3` gives two-thirds of the parent height, and `(WINDOW_WIDTH - WIDTH) / 2` centers the widget.

### Event bubbling

Mouse and keyboard events bubble from the leaf back to the root if unhandled. `HandleMouseInputOuter` and `HandleKeyPressOuter` first ask children, then ask the widget itself. Returning `true` from `HandleMouseInput`/`HandleKeyPress` stops the bubble. This is why clicking a button on top of a scroll panel does not also scroll the panel: the button consumes the event.

![Extension points diagram](images/Part_04_Chapter_03_Widgets-extension-hook-diagram-showing-the-interface-s-to-implement-b4a27b.svg)

## Extension Points


### Add a new widget type

Create a class inheriting `Widget` and name it `MyWidgetWidget`. Declare it in YAML as `MyWidget`. Override `Draw`, `Tick`, and input methods as needed. If the widget should be cloneable, override `Clone()`. Add the new assembly to the mod manifest if it is not already loaded.

### Add a new logic class

Create a class inheriting `ChromeLogic`. Reference it in YAML via `Logic: MyLogic`. Add event handlers to the widget in the constructor. Common patterns include subscribing to `Ui` mediator notifications, caching child widget references, and updating widget state in `Tick`.

### Add custom metrics

Add entries to the mod's chrome metrics YAML. Use `ChromeMetrics.Get<T>("MyKey")` in code. Keep metrics in one file so that theming and localization are easier to maintain.

### Add a custom layout

Create a new YAML file and add it to the manifest's `ChromeLayout`. The top-level keys are the widget IDs that can be opened with `Ui.OpenWindow`. Use the same file for related screens (for example, all settings tabs) so that shared chrome can be referenced by ID.

### Add a widget command

UI commands can be exposed to the console or hotkeys. The `UiCommands` class maps commands to widget actions. Alternatively, logic classes can subscribe to `INotificationHandler<T>` notifications sent via `Ui.Send<T>`.

## Practical Example

![Practical example: updating a label from chromelogic diagram](images/Part_04_Chapter_03_Widgets-diagram-showing-the-chromelogic-widget-yaml-binding-map-yaml-10bb2b.svg)

### Practical Example: Updating a Label from ChromeLogic


This example shows how to declare a `LabelWidget` in YAML and drive its text from a `ChromeLogic` class that runs every frame.

`chrome.yaml`:

```yaml
MyLabelPanel:
    Container:
        Logic: MyLabelLogic
        X: (WINDOW_WIDTH - WIDTH) / 2
        Y: (WINDOW_HEIGHT - HEIGHT) / 2
        Width: 200
        Height: 40
        Children:
            Label@MY_LABEL:
                X: 0
                Y: 0
                Width: 200
                Height: 40
                Text: Waiting...
                Align: Left
```

`MyLabelLogic.cs`:

```csharp
public class MyLabelLogic : ChromeLogic
{
    readonly LabelWidget label;
    string status;

    [ObjectCreator.UseCtor]
    public MyLabelLogic(Widget widget)
    {
        label = widget.Get<LabelWidget>("MY_LABEL");
        label.GetText = () => status;
    }

    public override void Tick()
    {
        // Update the backing string each frame; GetText reads it when the label draws.
        status = "Game time: " + Game.LocalTick;
    }
}
```

The pattern is: the widget is declared in `chrome.yaml`, the `ChromeLogic` class is written in C# and referenced in YAML via `Logic: MyLabelLogic`, and data flows from the simulation or UI state to the widget text through `GetText`. OpenRA calls `Tick()` on each logic object every frame, so the label stays in sync with the source data without extra polling or timers.

For a static label, assign `GetText` once in the constructor; for data that changes every frame, update the backing value in `Tick` and let the label read it via `GetText`.

![Common pitfalls  guardrails diagram](images/Part_04_Chapter_03_Widgets-checklist-infographic-style-diagram-summarizing-the-top-pitf-fb069e.svg)

## Common Pitfalls / Guardrails


- **Widget IDs must be unique:** duplicate keys in chrome YAML cause a runtime error.
- **Logic class constructor:** the logic class must have a constructor that matches the `WidgetArgs`. Missing arguments cause a runtime error. The `widget` argument is always added before `PostInit`.
- **Dispose logic:** logic classes are not automatically disposed on hide; they are disposed on `Removed()`. Use `BecameHidden` or `BecameVisible` for cleanup when a window is hidden but may be restored.
- **Threading:** widgets run on the UI thread. Do not update widget state from background threads; use `Game.RunAfterTick` to schedule updates on the next tick.
- **Layout evaluation:** expression-based layout is evaluated at runtime. Syntax errors produce exceptions when the widget is drawn. Use parentheses and only the documented variables.
- **Modal dialogs:** use `Ui.OpenWindow`/`Ui.CloseWindow` rather than manually adding/removing children to preserve focus and restore behavior.
- **Widget state:** widgets are recreated when the screen changes. Do not store long-lived state in widgets; use `Game.GlobalData` or a static service, or pass state through `WidgetArgs`.
- **Keyboard focus:** only the widget with `KeyboardFocusWidget` receives typed text. Ensure text fields acquire focus when activated and yield it when closed.
- **Mouse capture:** for dragging operations, the widget should grab mouse focus with `TakeMouseFocus` so it receives events even when the cursor leaves the widget bounds. Remember to yield focus on mouse up.
- **Event bounds vs render bounds:** `EventBounds` defaults to `RenderBounds`, but some widgets override it (for example, to make a small button easier to hit). Make sure `EventBoundsContains` is not abused to steal input from overlapping widgets.
- **Visible vs IsVisible:** `Visible` is a field; `IsVisible` is a lambda. Setting `Visible` directly affects ticking and drawing. Changing `IsVisible` without updating `Visible` may have no effect unless the widget checks `IsVisible()` in its own code.

## What to read next

- [Part 4.4 — Viewport and Input](Part_04_Chapter_04_Viewport_Input.md) for the world-interaction widget and order-generator UI.
- [Part 4.1 — Renderer, Sheet, and Sprite](Part_04_Chapter_01_Renderer.md) for the renderer path that draws chrome.
- [Part 10.3 — Porting, Modding, and Developer Workflows](Part_10_Chapter_03_Port_And_Modding.md) for practical UI and modding recipes.
- [Appendix H — Asset Visual Reference](../appendices/Appendix_H_Asset_Visual_Reference.md) for a reference of chrome, cursor, and UI asset formats and engine classes.
- [Appendix G — Advanced Modding Walkthroughs](../appendices/Appendix_G_Advanced_Modding_Walkthroughs.md) for a complete Chrome UI panel walkthrough.

## Summary

This chapter explains how OpenRA's custom [widget](../appendices/Appendix_A_Glossary.md) and chrome system builds menus, HUDs, and in-game UI.

After reading this chapter, you should be able to:

- Describe the widget tree, the roles of `Ui.Root`, `MenuRootWidget`, and `WorldRootWidget`, and the window-stack behavior.
- Read and write YAML chrome layouts that bind widgets to C# `ChromeLogic` classes.
- Trace the widget lifecycle from `WidgetLoader.LoadWidget` through `Initialize`, `PostInit`, `Tick`, `Draw`, input handling, and `Removed`.
- Use `ChromeMetrics` and layout expressions (`WINDOW_WIDTH`, `PARENT_WIDTH`, etc.) to build responsive UI.
- Explain how mouse and keyboard events propagate and how focus prevents unwanted bubbling.
- Implement a custom widget type and a `ChromeLogic` logic class.

If any of the concepts above feel unclear, review the relevant section before continuing. For source files and further reading, see the References section.


## References

- `OpenRA.Game/Widgets/Widget.cs` — widget base class, `ContainerWidget`, `InputWidget`, `ChromeLogic`, and `Ui` root.
- `OpenRA.Game/Widgets/WidgetLoader.cs` — widget loading.
- `OpenRA.Game/Widgets/ChromeMetrics.cs` — UI metrics.
- `OpenRA.Mods.Common/Widgets/ButtonWidget.cs` — button widget.
- `OpenRA.Mods.Common/Widgets/LabelWidget.cs` — label widget.
- `OpenRA.Mods.Common/Widgets/ImageWidget.cs` — image widget.
- `OpenRA.Mods.Common/Widgets/TextFieldWidget.cs` — text field widget.
- `OpenRA.Mods.Common/Widgets/DropDownButtonWidget.cs` — dropdown button widget.
- `OpenRA.Mods.Common/Widgets/*.cs` — common widget implementations.
- `OpenRA.Mods.Common/Widgets/Logic/*.cs` — common logic classes.


### External resources

- [OpenRA traits reference](https://docs.openra.net/en/release/traits/)
- [OpenRA playtest docs](https://docs.openra.net/en/playtest/)