# Appendix G — Advanced Modding Walkthroughs

This appendix provides complete, copy-paste-friendly walkthroughs for advanced OpenRA [modding](Appendix_A_Glossary.md) tasks that are rarely covered in one place. Each walkthrough explains the files to edit, the minimum viable example, how the engine interprets it, and how to verify it. The examples are written against the Red Alert mod structure, but the same patterns apply to any mod using the OpenRA engine.

> **Note:** All file paths are relative to your mod folder, e.g. `mods/ra/` or `mods/my-mod/`.

---

## Walkthrough 1 — Creating a Custom Chrome UI Panel

**Goal:** Add a new in-game panel with a label and a close button, and open it from a hotkey or a menu button.

**What you need to know first:** [Part 4.3 — Widgets and Chrome](../chapters/Part_04_Chapter_03_Widgets.md) for the Chrome/Widget system, [Part 3.1 — Mod SDK and Project Structure](../chapters/Part_03_Chapter_01_Mod_SDK.md) for `mod.yaml` structure, and [Appendix B — Common YAML Patterns](Appendix_B_Common_YAML_Patterns.md) for inheritance.

**Files to edit:**
- `mods/ra/chrome.yaml` (or your mod's chrome collection) — add the panel image collection entry
- `mods/ra/chrome/my-panel.yaml` (new) — layout definition
- `OpenRA.Mods.MyMod/Widgets/Logic/MyPanelLogic.cs` (or a new custom assembly) — `ChromeLogic` class
- `mods/ra/mod.yaml` — register the new `ChromeLayout` file and the assembly if needed
- `mods/ra/hotkeys.yaml` (optional) — define the hotkey used by the panel

**Complete example:**

`mods/ra/chrome.yaml` — add a reusable dialog background collection (or reuse `^Dialog`):

```yaml
^Dialog:
    Image: dialog.png

my-panel-bg:
    Inherits: ^Dialog
    PanelRegion: 0, 0, 5, 5, 120, 120, 5, 5
```

`mods/ra/chrome/my-panel.yaml` — define the panel widget tree:

```yaml
Background@MY_PANEL:
    Logic: MyPanelLogic
    X: (WINDOW_WIDTH - WIDTH) / 2
    Y: (WINDOW_HEIGHT - HEIGHT) / 2
    Width: 400
    Height: 200
    Background: my-panel-bg
    Children:
        Label@TITLE:
            X: 0
            Y: 20
            Width: PARENT_WIDTH
            Height: 25
            Font: Bold
            Align: Center
            Text: label-my-panel-title
        Button@CLOSE_BUTTON:
            X: PARENT_WIDTH - WIDTH - 20
            Y: PARENT_HEIGHT - 45
            Width: 120
            Height: 25
            Text: button-close
            Font: Bold
            Key: escape
```

`OpenRA.Mods.MyMod/Widgets/Logic/MyPanelLogic.cs` (create this file in your custom assembly):

```csharp
using System.Collections.Generic;
using OpenRA.Mods.Common.Lint;
using OpenRA.Widgets;

namespace OpenRA.Mods.MyMod.Widgets.Logic
{
    [ChromeLogicArgsHotkeys("ToggleMyPanelKey")]
    public class MyPanelLogic : ChromeLogic
    {
        [ObjectCreator.UseCtor]
        public MyPanelLogic(Widget widget, Dictionary<string, MiniYaml> logicArgs)
        {
            widget.Get<ButtonWidget>("CLOSE_BUTTON").OnClick = Ui.CloseWindow;
        }
    }
}
```

Hotkey registration in `mods/ra/hotkeys.yaml`:

```yaml
ToggleMyPanel: F8
    Description: hotkey-description-toggle-my-panel
    Types: Menu
    Contexts: player
```

Wire the hotkey to an existing ingame handler. For example, add `MyPanelHotkeyLogic` to `mods/common/chrome/ingame.yaml` or create a dedicated logic widget in your custom assembly:

```csharp
using System.Collections.Generic;
using OpenRA.Widgets;

namespace OpenRA.Mods.MyMod.Widgets.Logic
{
    public class MyPanelHotkeyLogic : ChromeLogic
    {
        [ObjectCreator.UseCtor]
        public MyPanelHotkeyLogic(Widget widget, ModData modData, Dictionary<string, MiniYaml> logicArgs)
        {
            var key = new HotkeyReference();
            if (logicArgs.TryGetValue("ToggleMyPanelKey", out var yaml))
                key = modData.Hotkeys[yaml.Value];

            var keyhandler = widget.Get<LogicKeyListenerWidget>("WORLD_KEYHANDLER");
            keyhandler.AddHandler(e =>
            {
                if (e.Event == KeyInputEvent.Down && key.IsActivatedBy(e))
                {
                    Ui.OpenWindow("MY_PANEL", new WidgetArgs());
                    return true;
                }

                return false;
            });
        }
    }
}
```

In `mods/ra/chrome/ingame.yaml` (or the file that defines the world-root key handler), add the logic to the existing `LogicKeyListener@WORLD_KEYHANDLER`:

```yaml
LogicKeyListener@WORLD_KEYHANDLER:
    Logic: MyPanelHotkeyLogic, MusicHotkeyLogic, ...
    ToggleMyPanelKey: ToggleMyPanel
```

Register the new layout in `mods/ra/mod.yaml`:

```yaml
ChromeLayout:
    ...
    ra|chrome/my-panel.yaml
```

**How it works:**
- `Background@MY_PANEL` creates a top-level widget. The `Logic:` key tells the engine which `ChromeLogic` class to instantiate when the widget is opened.
- `Ui.OpenWindow("MY_PANEL", ...)` looks up the widget by its declared ID and creates it from the loaded Chrome layouts.
- `Ui.CloseWindow()` destroys the current top-level window. The button's `OnClick` is wired to that in the logic class.
- `ChromeLogicArgsHotkeys` tells the linter which `logicArgs` keys are hotkey references, so `--check-yaml` can verify `ToggleMyPanelKey` points to a real hotkey definition.

**How to verify it works:**
- Run `OpenRA.Utility.exe ra --check-yaml`.
- Start a skirmish or mission and press the bound key (or trigger the button that calls `Ui.OpenWindow("MY_PANEL")`); the panel should appear centered.
- Click the close button or press Escape; the panel should close.

**Common pitfalls:**
- The top-level widget ID passed to `Ui.OpenWindow` must match the `Background@` ID exactly (e.g. `MY_PANEL`).
- The `Logic:` class name must be fully discoverable. If it lives in a custom assembly, the assembly must be listed under `Assemblies:` in `mod.yaml`.
- `ChromeLayout` files must be listed in `mod.yaml`; otherwise `--check-yaml` may not see the widget at all.
- If you add a hotkey, the `Description` fluent key must exist in your fluent files or `--check-fluent` will complain.

---

## Walkthrough 2 — Creating a Complete Single-Player Lua Mission

**Goal:** Build a simple single-player mission with an initial base, enemy attack waves, primary objectives, and victory/defeat conditions.

**What you need to know first:** [Part 6.1 — Lua and Eluant](../chapters/Part_06_Chapter_01_Lua_Eluant.md) for the Lua runtime, [Part 1.1 — ECS, Actors, and Traits](../chapters/Part_01_Chapter_01_ECS.md) for actors and players, and [Appendix E — Practical Modding Recipes](Appendix_E_Practical_Recipes.md) for actor YAML basics.

**Files to edit:**
- `mods/ra/maps/my-mission/map.yaml` — map metadata, player references, and pre-placed actors
- `mods/ra/maps/my-mission/map.lua` (or `my-mission.lua`) — the script
- `mods/ra/maps/my-mission/rules.yaml` (optional) — map-specific overrides
- `mods/ra/maps/my-mission/map.ftl` (optional) — mission text strings

**Complete example:**

`mods/ra/maps/my-mission/map.yaml` (excerpt):

```yaml
MapFormat: 12
RequiresMod: ra
Title: My Custom Mission
Author: Your Name
Tileset: TEMPERAT
MapSize: 96,96
Bounds: 16,16,64,64
Visibility: MissionSelector
Categories: Campaign
LockPreview: True

Rules: ra|rules/campaign-rules.yaml, ra|rules/campaign-tooltips.yaml, ra|rules/campaign-palettes.yaml, rules.yaml

FluentMessages: ra|fluent/lua.ftl, ra|fluent/campaign.ftl, map.ftl

Players:
    PlayerReference@USSR:
        Name: USSR
        Playable: True
        Required: True
        Faction: soviet
        LockFaction: True
        Enemies: Germany
    PlayerReference@Germany:
        Name: Germany
        Faction: allies
        Color: 5050F0
        Enemies: USSR
        Bot: campaign

Actors:
    Actor0: fact
        Location: 30,30
        Owner: USSR
    Actor1: harv
        Location: 32,32
        Owner: USSR
    Actor2: e1
        Location: 28,30
        Owner: USSR
        Facing: 128
    Actor3: weap
        Location: 45,45
        Owner: Germany
    Actor4: 2tnk
        Location: 47,47
        Owner: Germany
        Facing: 64
    Waypoint1: waypoint
        Location: 30,35
        Owner: Neutral
    EnemyEntry: waypoint
        Location: 79,79
        Owner: Neutral
```

`mods/ra/maps/my-mission/map.lua`:

```lua
--[[
   Copyright (c) The OpenRA Developers and Contributors
   This file is part of OpenRA, which is free software. It is made
   available to you under the terms of the GNU General Public License
   as published by the Free Software Foundation, either version 3 of
   the License, or (at option) any later version. For more
   information, see COPYING.
]]

WorldLoaded = function()
    USSR = Player.GetPlayer("USSR")
    Germany = Player.GetPlayer("Germany")

    InitObjectives(USSR)

    -- Primary objective: destroy the German weapons factory.
    DestroyFactoryObjective = AddPrimaryObjective(USSR, "destroy-enemy-factory")

    -- Schedule an attack wave after 2 minutes.
    Trigger.AfterDelay(DateTime.Seconds(120), function()
        Media.PlaySpeechNotification(USSR, "ReinforcementsArrived")
        local wave = Reinforcements.Reinforce(Germany, { "e1", "e1", "e3", "2tnk" }, { EnemyEntry.Location }, 10)
        Utils.Do(wave, function(a)
            a.AttackMove(Actor3.Location)
        end)
    end)

    -- Defeat condition: lose the Construction Yard (destroyed, sold, or captured).
    Trigger.OnRemovedFromWorld(Actor0, function()
        USSR.MarkFailedObjective(DestroyFactoryObjective)
    end)

    Trigger.OnCapture(Actor0, function()
        USSR.MarkFailedObjective(DestroyFactoryObjective)
    end)

    -- Victory condition: destroy the enemy factory.
    Trigger.OnRemovedFromWorld(Actor3, function()
        USSR.MarkCompletedObjective(DestroyFactoryObjective)
    end)
end

Tick = function()
    -- Fallback: if the Construction Yard is gone or no longer ours, fail.
    if Actor0.IsDead or Actor0.Owner ~= USSR then
        USSR.MarkFailedObjective(DestroyFactoryObjective)
    end

    -- Fallback: if the enemy factory is gone, win.
    if Actor3.IsDead then
        USSR.MarkCompletedObjective(DestroyFactoryObjective)
    end
end
```

Map-specific rules in `mods/ra/maps/my-mission/rules.yaml`:

```yaml
Player:
    ModularBot@CampaignAI:
        Name: bot-campaign-ai.name
        Type: campaign
    PlayerResources:
        DefaultCash: 5000

World:
    LuaScript:
        Scripts: campaign.lua, utils.lua, map.lua
    MissionData:
        Briefing: briefing
```

The `LuaScript` trait's field is `Scripts` (a comma-separated list), not `Script`. The list must include the shared `campaign.lua` and `utils.lua` (from `mods/ra/scripts/` and `mods/common/scripts/`) because they define the mission helpers used above — `InitObjectives` lives in `campaign.lua` and `AddPrimaryObjective` lives in `utils.lua`. (By contrast, `MarkCompletedObjective` and `MarkFailedObjective` are engine bindings, so they work without any shared script.) The map's own `map.lua` is listed last so it can call them.

`MissionData` provides the mission briefing shown in the mission selector. Its `Briefing:` field is a Fluent key; the actual text lives in `map.ftl`.

> **Why the `Player` block is needed:** `ModularBot@CampaignAI` registers the `campaign` bot type used by the Germany player. `PlayerResources.DefaultCash` overrides the campaign rules' default of `0` so the player can actually build units. The `map.yaml` also loads the full engine campaign rules (`ra|rules/campaign-rules.yaml`) which disable `SpawnStartingUnits` / `MapStartingLocations` and set up the campaign lobby, but adding these two pieces directly in the map's `rules.yaml` makes the mission robust against cases where the mod rules are not resolved as expected.

> **Why the defeat condition uses `OnRemovedFromWorld` and `OnCapture`:** `Trigger.OnKilled` only fires when an actor is destroyed. Selling a building removes it from the world without killing it, and an engineer capture changes the owner without destroying it. `OnRemovedFromWorld` catches both destruction and sale, while `OnCapture` catches ownership change. Always cover all three paths when a building must survive for the player to win.

Mission translations in `mods/ra/maps/my-mission/map.ftl`:

```ftl
briefing = Destroy the German weapons factory to win the mission. Protect your Construction Yard at all costs.

destroy-enemy-factory = Destroy the German weapons factory.
```

`AddPrimaryObjective` (and the other objective helpers) take a **Fluent translation key**, not raw text. The key must exist in a `.ftl` file that is loaded by `FluentMessages:` in `map.yaml`. If the key is missing, the escape menu will display the raw key string instead of the readable description. If `MissionData` is missing, the mission selector may show no briefing or retain the briefing from the previously selected mission.

> **Note:** Real RA campaign maps use exactly this pattern, e.g. `Scripts: campaign.lua, utils.lua, allies01.lua` in `mods/ra/maps/allies-01/rules.yaml`. The scripts are merged in order, so list shared helpers before the map-specific script.

**How it works:**
- `WorldLoaded` runs once when the simulation starts. It is the standard entry point for mission setup.
- `Player.GetPlayer("Name")` returns the script handle for the player defined in `map.yaml`.
- `AddPrimaryObjective` registers a mission objective; `MarkCompletedObjective`/`MarkFailedObjective` update the win/loss state.
- `Trigger.AfterDelay` schedules delayed events; `Trigger.OnRemovedFromWorld` and `Trigger.OnCapture` handle win/loss when a critical building is destroyed, sold, or captured.
- `Reinforcements.Reinforce` spawns a list of actors at a waypoint and moves them onto the map.
- `Tick` runs every simulation tick; use it for lightweight win/loss checks (avoid heavy logic here).

**How to verify it works:**

1. **Package the map as an `.oramap`.** OpenRA's mission selector loads packaged maps, not loose folders. Two ways to do this:
   - Use the in-game map editor's **Save As** and pick the `.oramap` format.
   - Or, from the map folder, zip these files at the **root** (not inside a subfolder) and rename the `.zip` to `.oramap`:
     ```
     map.yaml
     map.bin
     map.png
     rules.yaml
     map.lua
     campaign.lua
     utils.lua
     map.ftl
     ```
     > A complete, ready-to-package example is included in the manual repository at `build files/engine-tests/lua-mission/`.
2. **Validate the package:** run `OpenRA.Utility.exe ra --check-yaml` on the resulting `.oramap`. You should see `Testing map: Manual Test Mission` and exit code `0`.
3. **Play the mission:** start it from the Mission Selector. Confirm the objective appears, the attack wave arrives after the delay, and destroying (or selling) the factory wins the mission while losing the Construction Yard by destruction, sale, or capture loses it.

**Common pitfalls:**
- `InitObjectives` (from `campaign.lua`) and `AddPrimaryObjective` (from `utils.lua`) are shared-script helpers, not engine bindings. If you forget to list those scripts in `Scripts:` before `map.lua`, the calls raise a "nil value" error and the mission aborts on load.
- Objective descriptions passed to `AddPrimaryObjective` are **Fluent translation keys**, not raw text. They must be defined in a `.ftl` file and loaded via `FluentMessages:` in `map.yaml`; otherwise the escape menu shows the raw key string.
- Actor references in Lua must match the actor **keys** (names) in `map.yaml`. Typos fail silently (the variable becomes `nil`).
- `WorldLoaded` must be a global function; the engine calls it by name.
- `DateTime.Seconds(120)` is real seconds, not in-game seconds at high speed. Use `DateTime.Ticks(120)` for game ticks if you need speed-independent timing.
- Players with `Bot: campaign` require a `CampaignBot` or `ModularBot` definition in the mod's AI rules; otherwise the enemy will not do anything.
- Always guard against dead actors: `if not Actor3.IsDead then ... end` before using actor references in callbacks.

---

## Walkthrough 3 — Adding a Custom Crate Type

**Goal:** Add a new crate that gives a random unit or a lump of cash.

**What you need to know first:** [Part 2.4 — Rulesets, Actors, and Weapons](../chapters/Part_02_Chapter_04_Rules_Weapons.md) for actor rules and [Appendix B — Common YAML Patterns](Appendix_B_Common_YAML_Patterns.md) for trait inheritance.

**Files to edit:** `mods/ra/rules/misc.yaml` (or a new crate file loaded under `Rules:` in `mod.yaml`).

**Before:**

```yaml
CRATE:
    Inherits: ^Crate
    GiveCashCrateAction:
        Amount: 1000
        SelectionShares: 50
        UseCashTick: true
```

**After:**

```yaml
CRATE:
    Inherits: ^Crate
    GiveCashCrateAction:
        Amount: 1000
        SelectionShares: 30
        UseCashTick: true
    GiveCashCrateAction@BIGBONUS:
        Amount: 5000
        SelectionShares: 5
        UseCashTick: true
    GiveUnitCrateAction@RANDOMLIGHT:
        SelectionShares: 15
        Units: jeep, 1tnk, apc, ftrk
        ValidFactions: allies, england, france, germany, soviet, russia, ukraine
        Prerequisites: techlevel.low
    GiveUnitCrateAction@RANDOMHEAVY:
        SelectionShares: 8
        Units: 2tnk, 3tnk, v2rl, arty
        ValidFactions: allies, england, france, germany, soviet, russia, ukraine
        Prerequisites: techlevel.medium, fix
```

**How it works:**
- `CrateAction` is the base class. Every `GiveCashCrateAction` or `GiveUnitCrateAction` trait is a potential reward.
- `SelectionShares` is the weight used when the crate is collected. Higher shares means the action is more likely to be picked.
- `GiveCashCrateAction.Amount` is the cash value; `UseCashTick: true` displays a floating cash tick.
- `GiveUnitCrateAction.Units` is an immutable list of actor types. One is chosen randomly when collected, and the engine tries to place it on a nearby passable cell.
- `ValidFactions` restricts which faction can receive the action; `Prerequisites` gates it by the collector's tech state.
- `GetSelectionShares` returns zero if the action cannot be fulfilled (e.g. no space for the unit, wrong faction, or unmet prerequisites), so invalid actions are skipped automatically.

**How to verify it works:**
- Run `OpenRA.Utility.exe ra --check-yaml`.
- Start a skirmish with crates enabled and collect several crates. You should eventually see the new cash amounts and the listed units appear.

**Common pitfalls:**
- `GiveUnitCrateAction.Units` is plural and required. The field name changed from the older `Unit` to `Units` in recent engine versions.
- If no cell is suitable for the unit, the action silently fails and the crate is consumed. Add a variety of unit types to improve placement odds.
- `Prerequisites` are checked against the collector's tech tree, not the crate owner. A crate collected by a low-tech player will not pick a high-tech action.
- `SelectionShares` are summed across all actions; a value of 0 disables the action unless other conditions make it selectable.

---

## Walkthrough 4 — Adding a Custom Resource Type

**Goal:** Add a new resource type (e.g. "Gems" alongside "Ore") that harvesters can gather, refineries can accept, and the renderer can display.

**What you need to know first:** [Part 2.4 — Rulesets, Actors, and Weapons](../chapters/Part_02_Chapter_04_Rules_Weapons.md) for actor rules, [Part 7.7 — Resources and Actors](../chapters/Part_07_Chapter_07_Resources_Actors.md) for the resource pipeline, and [Appendix B — Common YAML Patterns](Appendix_B_Common_YAML_Patterns.md).

**Files to edit:**
- `mods/ra/rules/world.yaml` — `ResourceLayer`, `ResourceRenderer`, `EditorResourceLayer`
- `mods/ra/rules/defaults.yaml` — `Locomotor` terrain speeds for the new resource terrain
- `mods/ra/rules/vehicles.yaml` (or harvester actor) — `Harvester.Resources` and `StoresResources`
- `mods/ra/rules/structures.yaml` (or refinery/silo actors) — `StoresResources.Resources` and `Refinery`
- `mods/ra/rules/player.yaml` — `PlayerResources.ResourceValues`
- `mods/ra/sequences/misc.yaml` — new resource sequences
- `mods/ra/tilesets/*.yaml` — `TerrainType` entry for the new resource (if not already present)

**Complete example:**

`mods/ra/rules/world.yaml` — add `Gems` to the world resource layer:

```yaml
World:
    ...
    ResourceLayer:
        RecalculateResourceDensity: true
        ResourceTypes:
            Ore:
                ResourceIndex: 1
                TerrainType: Ore
                AllowedTerrainTypes: Clear, Road
                MaxDensity: 12
            Gems:
                ResourceIndex: 2
                TerrainType: Gems
                AllowedTerrainTypes: Clear, Road
                MaxDensity: 3
    ResourceRenderer:
        ResourceTypes:
            Ore:
                Sequences: gold01, gold02, gold03, gold04
                Palette: player
                Name: resource-minerals
            Gems:
                Sequences: gem01, gem02, gem03, gem04
                Palette: player
                Name: resource-gems
```

Also mirror the same `Gems` entry under `EditorWorld:` -> `EditorResourceLayer:` and `EditorWorld:` -> `ResourceRenderer:` so the map editor can paint and preview the resource.

`mods/ra/rules/defaults.yaml` — ensure locomotors can drive over the resource terrain:

```yaml
Locomotor@WHEELED:
    Name: wheeled
    TerrainSpeeds:
        Clear: 100
        Road: 125
        Ore: 88
        Gems: 88
```

`mods/ra/sequences/misc.yaml` — define the new sprites:

```yaml
resources:
    Defaults:
        Length: *
    gem01:
        Filename: gem01.tem
        TilesetFilenames:
            SNOW: gem01.sno
    gem02:
        Filename: gem02.tem
        TilesetFilenames:
            SNOW: gem02.sno
    gem03:
        Filename: gem03.tem
        TilesetFilenames:
            SNOW: gem03.sno
    gem04:
        Filename: gem04.tem
        TilesetFilenames:
            SNOW: gem04.sno
```

`mods/ra/rules/vehicles.yaml` (harvester `HARV`):

```yaml
HARV:
    ...
    Harvester:
        Resources: Ore, Gems
        ...
```

`mods/ra/rules/structures.yaml` (refinery `PROC` and silo `SILO`):

```yaml
PROC:
    ...
    StoresResources:
        Capacity: 2000
        Resources: Ore, Gems
    Refinery:
```

`mods/ra/rules/player.yaml`:

```yaml
Player:
    ...
    PlayerResources:
        ResourceValues:
            Ore: 25
            Gems: 50
```

`mods/ra/tilesets/temperat.yaml` (and other tilesets) — add the terrain type used by the resource:

```yaml
TerrainType@GEMS:
    Type: Gems
    Color: 00FF00
    TargetTypes: Ground
    MovementClass: 1
```

**How it works:**
- `ResourceLayer` is a world trait that stores the simulation-side resource grid. `ResourceTypes` maps the resource name to the index used in the binary map data, a terrain type, and placement rules.
- `ResourceRenderer` is a world trait that reads `ResourceLayer` and draws the matching sprite sequences. `Sequences` lists one or more image sequences that are randomly chosen per cell.
- `Harvester` can only gather resources listed in its `Resources` field, and only if the actor also has an `IStoresResources` trait (e.g. `StoresResources`) that accepts those types.
- `Refinery` accepts any resource the player owns a `StoresResources` trait for and converts it via `PlayerResources.ResourceValues` into cash.
- `PlayerResources.ResourceValues` defines the value per bale. The refinery applies `IResourceValueModifier` traits (e.g. ore refineries vs. gem refineries) to this base value.

**How to verify it works:**
- Run `OpenRA.Utility.exe ra --check-yaml`.
- Open the map editor and paint the new resource type. It should appear with the correct color and sprite.
- Start a skirmish, build a refinery and harvester, and order the harvester to gather the new resource. The cash counter should increase and the resource sprite should be removed from the cell.

**Common pitfalls:**
- There is no standalone `ResourceType` trait in the engine. Resource types are configured as nested dictionaries inside `ResourceLayer`, `EditorResourceLayer`, and `ResourceRenderer`.
- `ResourceIndex` must match the index used by the map binary data for that resource. In a custom mod, keep the same index across the layer, editor layer, and map files.
- `Harvester` validates its `Resources` list against `IStoresResourcesInfo.ResourceTypes` on the same actor. If the harvester does not have a `StoresResources` trait listing the resource, `--check-yaml` will throw an error.
- `Locomotor` must include the resource terrain type or harvesters will refuse to path over it.
- `PlayerResources.ResourceValues` must contain an entry for every resource type or refineries will refuse it.
- If you forget to add the resource to `EditorWorld:` -> `EditorResourceLayer:`, the map editor will not let you place it.

---

## Walkthrough 5 — Customizing Shroud and Fog of War

**Goal:** Change reveal ranges, disable fog globally, or grant/remove shroud sources per actor.

**What you need to know first:** [Part 1.1 — ECS, Actors, and Traits](../chapters/Part_01_Chapter_01_ECS.md) for the trait system, [Part 4.2 — WorldRenderer](../chapters/Part_04_Chapter_02_WorldRenderer.md) for rendering, and [Appendix B — Common YAML Patterns](Appendix_B_Common_YAML_Patterns.md).

**Files to edit:**
- `mods/ra/rules/player.yaml` — `Shroud` lobby options
- `mods/ra/rules/defaults.yaml` or actor rules — `RevealsShroud` and `CreatesShroud`
- `mods/ra/rules/world.yaml` — `ShroudRenderer`
- `mods/ra/sequences/misc.yaml` — `shroud` and `fog` sequences

**Complete example:**

`mods/ra/rules/player.yaml` — disable fog by default but keep shroud:

```yaml
Player:
    ...
    Shroud:
        FogCheckboxEnabled: false
        FogCheckboxLabel: checkbox-fog-of-war.label
        FogCheckboxDescription: checkbox-fog-of-war.description
```

`mods/ra/rules/defaults.yaml` — change default unit vision:

```yaml
^Vehicle:
    RevealsShroud:
        Range: 6c0
        MinRange: 0c0
        Type: GroundPosition
```

Per-actor example in `mods/ra/rules/vehicles.yaml` (a scout with a larger sight range):

```yaml
JEEP:
    ...
    RevealsShroud:
        Range: 10c0
        Type: GroundPosition
        RevealGeneratedShroud: true
```

An actor that generates shroud for enemies (e.g. a mobile gap generator):

```yaml
GAPV:
    ...
    CreatesShroud:
        Range: 8c0
        ValidRelationships: Neutral, Enemy
```

`mods/ra/rules/world.yaml` — configure the shroud/fog renderer:

```yaml
World:
    ...
    ShroudRenderer:
        Sequence: shroud
        ShroudVariants: shroud
        FogVariants: fog
        ShroudPalette: shroud
        FogPalette: fog
        Index: 12, 9, 8, 3, 1, 6, 4, 2, 13, 11, 7, 14
        UseExtendedIndex: false
```

**How it works:**
- `Shroud` is a player-actor trait. It stores the visibility grid and exposes the `FogEnabled` and `ExploreMapEnabled` options configured via `ILobbyOptions`.
- `RevealsShroud` is an actor trait that adds a visibility source to allied players. `Range` is a `WDist` (e.g. `6c0` = 6 cells). `RevealGeneratedShroud` controls whether it clears shroud created by `CreatesShroud`.
- `CreatesShroud` is an actor trait that adds a shroud source to neutral/enemy players, hiding the area around the actor.
- `ShroudRenderer` is a world trait that draws the shroud/fog overlay. It uses a single `Sequence` image with variant names for shroud and fog tiles, and an `Index` that maps neighbor visibility states to sprite frames.
- Both traits inherit from `AffectsShroud`, which recalculates projected cells when the actor moves, is created, or is disabled.

**How to verify it works:**
- Run `OpenRA.Utility.exe ra --check-yaml`.
- Start a skirmish. The scout should reveal farther than other units. If you place a `CreatesShroud` actor, enemy players should lose vision in the area until they have a `RevealsShroud` source with `RevealGeneratedShroud: true` nearby.
- Toggle the `Fog` checkbox in the lobby; with `FogCheckboxEnabled: false` the default should be off.

**Common pitfalls:**
- `Range` uses `WDist` syntax: `c0` means cells, `c512` means half a cell. `6c0` = 6 full cells.
- `RevealsShroud.ValidRelationships` defaults to `Ally`; `CreatesShroud.ValidRelationships` defaults to `Neutral | Enemy`. Changing these changes who is affected.
- `RevealGeneratedShroud: false` on a revealer means it will not clear shroud generated by `CreatesShroud`. This is why the Phase Transport in RA has `RevealGeneratedShroud: False` on its secondary mini-revealer.
- `ShroudRenderer.Index` must match the number of frames in the shroud/fog sequences. If the sequence has fewer frames than the index values, the renderer will crash or draw garbage.
- Disabling fog does not disable shroud. Players still need to explore the map; explored areas remain visible even without fog.

---

## Walkthrough 6 — Adding a Capture/Engineer Mechanic

**Goal:** Add an engineer infantry that can capture enemy structures.

**What you need to know first:** [Part 1.1 — ECS, Actors, and Traits](../chapters/Part_01_Chapter_01_ECS.md) for the condition and trait system, [Part 2.4 — Rulesets, Actors, and Weapons](../chapters/Part_02_Chapter_04_Rules_Weapons.md), and [Appendix E — Practical Modding Recipes](Appendix_E_Practical_Recipes.md).

**Files to edit:**
- `mods/ra/rules/infantry.yaml` — the engineer actor
- `mods/ra/rules/defaults.yaml` — base building capture support
- `mods/ra/rules/structures.yaml` — any building-specific capture overrides

**Complete example:**

`mods/ra/rules/infantry.yaml` — add or clone an engineer (based on RA's `E6`):

```yaml
E6:
    Inherits: ^Soldier
    Inherits@selection: ^SelectableSupportUnit
    Buildable:
        Queue: Infantry
        BuildAtProductionType: Soldier
        BuildPaletteOrder: 60
        Prerequisites: ~barracks, ~techlevel.infonly
        Description: actor-e6.description
    Valued:
        Cost: 400
    Tooltip:
        Name: actor-e6.name
    CaptureManager:
    Captures:
        CaptureTypes: building
        PlayerExperience: 10
        CaptureDelay: 200
        ConsumedByCapture: true
        SabotageThreshold: 0
        EnterCursor: enter
        EnterBlockedCursor: enter-blocked
    Voiced:
        VoiceSet: EngineerVoice
    -AttackFrontal:
```

`mods/ra/rules/defaults.yaml` — ensure buildings can be captured:

```yaml
^Building:
    ...
    CaptureManager:
        BeingCapturedCondition: being-captured
    Capturable:
        RequiresCondition: !build-incomplete
        Types: building
    CapturableProgressBar:
    CapturableProgressBlink:
```

A reusable engineer variant (does not die on capture):

```yaml
E6.REUSABLE:
    Inherits: E6
    Captures:
        CaptureTypes: building
        CaptureDelay: 375
        ConsumedByCapture: false
        PlayerExperience: 10
```

**How it works:**
- `CaptureManager` is required on both the capturer and the target. It coordinates the capture order and grants the `being-captured` condition while the capture is in progress.
- `Captures` defines what the engineer can capture via `CaptureTypes`. The target must have a `Capturable` trait with a matching `Types` entry.
- `CaptureDelay` is the number of ticks the engineer must stand next to the target before the capture completes. During this time the `CapturableProgressBar` and `CapturableProgressBlink` traits draw the progress indicator.
- `ConsumedByCapture: true` removes the engineer after a successful capture; `false` lets the engineer survive and capture again.
- `SabotageThreshold` allows the engineer to damage healthy targets instead of capturing them. Set to `0` to disable sabotage.
- There is no `ExternalCaptures` trait in the current engine. The capture mechanic is fully implemented by the `Captures` / `Capturable` / `CaptureManager` trio.

**How to verify it works:**
- Run `OpenRA.Utility.exe ra --check-yaml`.
- Train an engineer and order it onto an enemy building. The cursor should change to `enter`, a progress bar should appear, and after the delay the building should change ownership.
- If `ConsumedByCapture` is false, the engineer should remain selected and ready for another capture.

**Common pitfalls:**
- Both actors must have `CaptureManager`. Without it on the target, the engineer cannot issue a capture order; without it on the engineer, the order is rejected.
- `CaptureTypes` must match exactly between `Captures` and `Capturable`. If the engineer has `building` but the target has `structure`, capture will not work.
- `RequiresCondition: !build-incomplete` prevents capturing buildings that are still under construction. If the condition is omitted, engineers can capture unfinished foundations.
- `CaptureDelay` is in ticks. At normal speed, 25 ticks ≈ 1 second, so `CaptureDelay: 200` is about 8 seconds.
- A reusable engineer still needs a valid target after the first capture; if all nearby buildings are friendly, the cursor will show blocked.

---

## Walkthrough 7 — Adding a Cloak/Invisibility System

**Goal:** Add a stealth tank that cloaks when not attacking and is only revealed by detectors.

**What you need to know first:** [Part 1.1 — ECS, Actors, and Traits](../chapters/Part_01_Chapter_01_ECS.md) for conditions and the [trait](Appendix_A_Glossary.md) system, and [Part 2.4 — Rulesets, Actors, and Weapons](../chapters/Part_02_Chapter_04_Rules_Weapons.md).

**Files to edit:**
- `mods/ra/rules/vehicles.yaml` — the stealth tank actor
- `mods/ra/rules/defaults.yaml` — detector defaults

**Complete example:**

`mods/ra/rules/vehicles.yaml` — add a stealth tank based on the existing `stnk`:

```yaml
STNK:
    Inherits: ^Vehicle
    Inherits@selection: ^SelectableCombatUnit
    Inherits@GAP: ^DisableOnGroundShroud
    Buildable:
        Queue: Vehicle
        BuildPaletteOrder: 330
        Prerequisites: atek, ~vehicles.france, ~techlevel.high
        Description: actor-stnk.description
    Valued:
        Cost: 1000
    Tooltip:
        Name: actor-stnk.name
    Health:
        HP: 35000
    Armor:
        Type: Light
    Mobile:
        Speed: 128
        Locomotor: heavywheeled
        PauseOnCondition: notmobile || being-captured
    RevealsShroud:
        MinRange: 4c0
        Range: 7c0
        RevealGeneratedShroud: false
    AutoTarget:
        InitialStance: HoldFire
        InitialStanceAI: ReturnFire
    Armament:
        Weapon: APTusk.stnk
        LocalOffset: 192,0,176
    Turreted:
        TurnSpeed: 20
    AttackTurreted:
    WithSpriteTurret:
    Cloak:
        InitialDelay: 125
        CloakDelay: 175
        CloakSound: appear1.aud
        UncloakSound: appear1.aud
        PauseOnCondition: cloak-force-disabled
        UncloakOn: Attack, Load, Unload, Heal, Dock
    GrantConditionOnDamageState@UNCLOAK:
        Condition: cloak-force-disabled
        ValidDamageStates: Critical
    -MustBeDestroyed:
```

`mods/ra/rules/defaults.yaml` — make sure some actors can detect cloaked units:

```yaml
^Vehicle:
    ...
    DetectCloaked:
        DetectionTypes: Cloak
        Range: 6c0
```

**How it works:**
- `Cloak` is a `PausableConditionalTrait` that hides the actor from enemy players after an initial delay and a cloak delay.
- `UncloakOn` is a bitfield of events that force the actor to become visible temporarily. `Attack` is included by default, so the tank uncloaks when firing.
- `CloakedCondition` grants a named condition while cloaked, which can be used by other traits (e.g. to disable weapons or change the sprite).
- `DetectionTypes` defines which detector types can see this cloak. `DetectCloaked.DetectionTypes` on the observer must match.
- `CloakStyle` controls the visual effect: `Alpha` (partial transparency), `Color` (tint), `Palette` (swap palette), or `None` (fully invisible).
- `PauseOnCondition` can disable cloaking entirely, used here via `GrantConditionOnDamageState@UNCLOAK` to force the tank visible when critically damaged.

**How to verify it works:**
- Run `OpenRA.Utility.exe ra --check-yaml`.
- Build a stealth tank in a skirmish. Move it near an enemy. After a short delay it should fade or disappear from the enemy's view.
- Order it to attack; it should become visible while firing, then recloak after the cloak delay.
- Move a detector unit nearby; the enemy player should see the tank within the detector's range even while cloaked.

**Common pitfalls:**
- `UncloakOn` is a bitfield; the default already includes `Attack`, `Unload`, `Infiltrate`, `Demolish`, and `Dock`. To keep stealth while moving, do **not** add `Move` to the list.
- If the actor also has a passenger `Cargo` trait with `LoadingCondition: notmobile`, loading/unloading units will trigger the `Load`/`Unload` uncloak events.
- `CloakDelay` is the time after the last uncloak event before the actor can recloak. A very low value makes the unit flicker; a very high value makes it vulnerable.
- `DetectionTypes` must match exactly between `Cloak` and `DetectCloaked`. The default type is `Cloak`.
- `Cloak` does not make the actor immune to damage; area-of-effect weapons can still hit it. It only affects visibility and targeting.

---

## Walkthrough 8 — Adding a Voxel Unit (TS/RA2 Style)

**Goal:** Add a 3D voxel unit to a mod that already supports voxels (e.g. Tiberian Sun), including file placement, model sequences, rendering traits, and unit rules.

**What you need to know first:** [Part 6.5 — Asset Loaders](../chapters/Part_06_Chapter_05_Asset_Loaders.md) for asset loading, [Part 4.1 — Renderer](../chapters/Part_04_Chapter_01_Renderer.md) for rendering, and [Appendix H — Asset Visual Reference](Appendix_H_Asset_Visual_Reference.md).

**Files to edit:**
- `mods/ts/mod.yaml` — ensure `ModelSequences` is declared and `OpenRA.Mods.Cnc.dll` is loaded
- `mods/ts/sequences/voxels.yaml` — add model sequences
- `mods/ts/rules/defaults.yaml` — `^VoxelActor` template
- `mods/ts/rules/gdi-vehicles.yaml` (or your unit file) — the actor rules
- Package the `.vxl` (voxel model) and `.hva` (orientation/animation) files into a loaded asset package

**Complete example:**

`mods/ts/mod.yaml`:

```yaml
Assemblies: OpenRA.Mods.Common.dll, OpenRA.Mods.Cnc.dll

Sequences:
    ts|sequences/infantry.yaml
    ts|sequences/misc.yaml
    ts|sequences/vehicles.yaml
    ...

ModelSequences:
    ts|sequences/voxels.yaml
```

`mods/ts/sequences/voxels.yaml`:

```yaml
mmk2:
    idle:

mmk2tur:
    idle:

mmk2barl:
    idle:
```

`mods/ts/rules/defaults.yaml`:

```yaml
^VoxelActor:
    BodyOrientation:
        QuantizedFacings: 0
    RenderVoxels:
    WithVoxelBody:
```

`mods/ts/rules/gdi-vehicles.yaml`:

```yaml
MMK2:
    Inherits: ^Tank
    Inherits@VOXELS: ^VoxelActor
    Inherits@EXPERIENCE: ^GainsExperience
    Inherits@AUTOTARGET: ^AutoTargetGroundAssaultMove
    Buildable:
        Queue: Vehicle
        BuildPaletteOrder: 150
        Prerequisites: ~gaweap, gatech, ~techlevel.high
        Description: actor-mmk2.description
    Valued:
        Cost: 2500
    Tooltip:
        Name: actor-mmk2.name
    Mobile:
        TurnSpeed: 12
        Speed: 42
    Health:
        HP: 80000
    Armor:
        Type: Heavy
    RevealsShroud:
        Range: 8c0
        MaxHeightDelta: 3
    AttackFrontal:
        FacingTolerance: 0
    Armament:
        Weapon: MammothTusk
    RenderVoxels:
        Scale: 11.5
    WithVoxelTurret:
    WithVoxelBarrel:
        LocalOffset: 0,51,256
```

**How it works:**
- Voxel support lives in `OpenRA.Mods.Cnc.dll`, so the mod must load that assembly. The mod must also use an isometric map grid (TS/RA2 style) for the depth buffer to work correctly.
- `ModelSequences` is the YAML section that maps actor names (or `RenderVoxels.Image`) to named voxel sequences. The sequence names (`idle`, `turret`, `barrel`) are referenced by the rendering traits.
- `RenderVoxels` is the main rendering trait for voxel actors. It manages the model renderer, palette, lighting, and scale. `Image` defaults to the actor ID if omitted.
- `WithVoxelBody` draws the main body. `WithVoxelTurret` and `WithVoxelBarrel` draw turret and barrel components that rotate independently.
- `BodyOrientation` with `QuantizedFacings: 0` tells the engine to use smooth voxel rotations rather than quantized sprite facings.
- Voxel files are looked up by the actor/image name plus the sequence name. For `MMK2` with `idle`, the engine loads `voxels/mmk2.vxl` and `voxels/mmk2.hva` (or the appropriate package path). Turret/barrel sequences load their own files (`mmk2tur.vxl`, `mmk2barl.vxl`).

**How to verify it works:**
- Run `OpenRA.Utility.exe ts --check-yaml`.
- Ensure the `.vxl` and `.hva` files are in a package listed under `Packages:` in `mod.yaml`.
- Start a skirmish, build the unit, and confirm it renders as a voxel model, rotates smoothly, and the turret/barrel tracks targets.

**Common pitfalls:**
- `OpenRA.Mods.Cnc.dll` must be in the `Assemblies:` list. Without it, `RenderVoxels` and `WithVoxelBody` are unknown traits.
- The `ModelSequences` section is separate from `Sequences`. 2D sprite sequences and voxel model sequences cannot be mixed in the same section.
- Voxel files must be named to match the sequence lookup. If the actor is `MMK2` and the sequence is `idle`, the files are typically `mmk2.vxl` and `mmk2.hva` (case-insensitive on Windows but case-sensitive on some platforms—match the case exactly).
- `BodyOrientation.QuantizedFacings` must be `0` for voxel actors; otherwise the engine tries to quantize facings into a sprite-like set and the model will snap unnaturally.
- `Scale` on `RenderVoxels` adjusts the model size. Values around 10–12 are typical for TS units; experiment until the unit matches the cell footprint.
- If the unit does not appear, check the ingame asset browser to verify the voxel files are loaded and named correctly.

---

## Walkthrough 9 — Configuring a Custom AI Bot via YAML

**Goal:** Add a defensive "turtle" AI that focuses on base building, heavy defenses, and late-game units.

**What you need to know first:** [Part 8.1 — IBot](../chapters/Part_08_Chapter_01_IBot.md) for bot architecture, [Part 8.2 — Bot Modules](../chapters/Part_08_Chapter_02_Bot_Modules.md), and [Part 2.4 — Rulesets, Actors, and Weapons](../chapters/Part_02_Chapter_04_Rules_Weapons.md).

**Files to edit:**
- `mods/ra/rules/ai.yaml` — bot definitions and modules
- `mods/ra/mod.yaml` — ensure `ai.yaml` is loaded under `Rules:`
- `mods/ra/fluent/rules.ftl` (or similar) — bot name strings

**Complete example:**

`mods/ra/rules/ai.yaml` — add a new bot type:

```yaml
Player:
    ModularBot@TurtleAI:
        Name: bot-turtle-ai.name
        Type: turtle

    GrantConditionOnBotOwner@turtle:
        Condition: enable-turtle-ai
        Bots: turtle

    ResourceMapBotModule:
        RequiresCondition: enable-turtle-ai
        ResourceCreatorTypes: mine, gmine
        ValuableResourceTypes: Ore, Gems
        HarvesterTypes: harv
        RefineryTypes: proc
        EnemyBaseBuildingTypes: pbox,gun,ftur,tsla,agun,barr,tent,weap,afld,hpad,fact,powr,apwr,proc

    HarvesterBotModule@turtle:
        RequiresCondition: enable-turtle-ai
        HarvesterTypes: harv
        RefineryTypes: proc
        InitialHarvesters: 6

    BaseBuilderBotModule@turtle:
        RequiresCondition: enable-turtle-ai
        MinimumExcessPower: 0
        MaximumExcessPower: 250
        ExcessPowerIncrement: 80
        ExcessPowerIncreaseThreshold: 4
        ConstructionYardTypes: fact
        RefineryTypes: proc
        PowerTypes: powr,apwr
        TechTypes: mslo, dome, atek, stek, fix
        ProductionTypes: barr,tent,weap,afld,hpad
        NewProductionCashThreshold: 7000
        SiloTypes: silo
        DefenseTypes: hbox,pbox,gun,ftur,tsla,agun,sam
        BuildingLimits:
            barr: 5
            tent: 5
            kenn: 1
            dome: 1
            weap: 3
            afld: 2
            hpad: 2
            atek: 1
            stek: 1
            fix: 1
            powr: 8
            apwr: 8
            proc: 4
            pbox: 10
            gun: 10
            tsla: 6
            agun: 6
            sam: 6
        BuildingFractions:
            powr: 2
            apwr: 2
            proc: 4
            barr: 2
            tent: 2
            kenn: 1
            weap: 2
            afld: 1
            hpad: 1
            pbox: 8
            gun: 8
            tsla: 6
            agun: 6
            sam: 6
            dome: 4
            atek: 1
            stek: 1
            fix: 1
        BuildingDelays:
            pbox: 1000
            gun: 1500
            tsla: 2000

    SquadManagerBotModule@turtle:
        RequiresCondition: enable-turtle-ai
        SquadSize: 12
        SquadSizeRandomBonus: 4
        RushInterval: 6000
        MinimumAttackForceCount: 20
        ProtectUnitScanInterval: 50
        AssignRolesInterval: 100
        AttackForceInterval: 100
        UnitsToBuild:
            e1: 60
            e3: 40
            e4: 30
            e6: 1
            1tnk: 20
            2tnk: 30
            3tnk: 30
            v2rl: 20
            arty: 20
            yak: 10
            mig: 10

    SupportPowerBotModule:
        RequiresCondition: enable-turtle-ai
        Decisions:
            nukepower:
                OrderName: NukePowerInfoOrder
                MinimumAttractiveness: 3000
                Consideration@1:
                    Against: Enemy
                    Types: Structure
                    Attractiveness: 1
                    TargetMetric: Value
                    CheckRadius: 5c0
```

`mods/ra/fluent/rules.ftl`:

```yaml
bot-turtle-ai-name = Turtle AI
```

`mods/ra/mod.yaml` — ensure `ai.yaml` is loaded:

```yaml
Rules:
    ...
    ra|rules/ai.yaml
```

**How it works:**
- `ModularBot` is the player-actor trait that drives all YAML-configured bots. It delegates decisions to `IBotTick` and `IBotRespondToAttack` modules.
- `GrantConditionOnBotOwner` grants a condition when the player is using the specified bot type. Every module uses `RequiresCondition: enable-turtle-ai` so it only runs for that bot.
- `BaseBuilderBotModule` builds the base. `BuildingFractions` are relative weights; `BuildingLimits` cap the number of each building. `BuildingDelays` throttle how quickly the AI repeats a building type.
- `HarvesterBotModule` manages harvester production and assignment. `InitialHarvesters` controls how many harvesters the AI tries to keep alive.
- `ResourceMapBotModule` scouts and defends resource areas. `ValuableResourceTypes` tells the AI which resources are worth fighting over.
- `SquadManagerBotModule` manages attack forces and defensive rushes. `UnitsToBuild` maps actor types to desired counts.
- `SupportPowerBotModule` automatically fires support powers like nukes when the target attractiveness exceeds the threshold.

**How to verify it works:**
- Run `OpenRA.Utility.exe ra --check-yaml`.
- Start a skirmish and select the new bot from the AI dropdown.
- Observe that it builds many power plants, refineries, and defenses before attacking, and that harvesters are plentiful.
- Use the debug overlay (F9) to see the bot's squad assignments and building priorities.

**Common pitfalls:**
- The `Type` in `ModularBot` must match the `Bots:` list in `GrantConditionOnBotOwner`. A mismatch means the modules never activate.
- `BaseBuilderBotModule` requires `ConstructionYardTypes` to match the MCV/Construction Yard actor ID. If the AI has no construction yard, it cannot build anything.
- `BuildingFractions` are weights, not percentages. If `proc` has weight 4 and `pbox` has weight 8, the AI will build roughly twice as many pillboxes as refineries over time, subject to `BuildingLimits`.
- `MinimumAttackForceCount` and `SquadSize` must be set realistically. If the AI never builds enough units, it will never attack.
- The AI cannot use units that are not listed in `UnitsToBuild`. If you add a new unit, add it here or the AI will ignore it.
- Bot names must be defined in the mod's fluent files; otherwise the lobby will show a missing-text error.

---

## Summary

This appendix covered nine advanced modding topics that together fill the most common gaps between reading the engine docs and shipping a working mod feature:

1. **Custom Chrome UI panels** — `chrome.yaml`, Chrome layouts, `ChromeLogic` classes, hotkey wiring, and `mod.yaml` registration.
2. **Single-player Lua missions** — `map.yaml` structure, `WorldLoaded`/`Tick`, objectives, triggers, and reinforcements.
3. **Custom crate rewards** — `GiveCashCrateAction` and `GiveUnitCrateAction` with `SelectionShares`, prerequisites, and faction filters.
4. **Custom resources** — `ResourceLayer`, `ResourceRenderer`, `Harvester`, `StoresResources`, `Refinery`, and `PlayerResources.ResourceValues`.
5. **Shroud and fog customization** — `Shroud`, `RevealsShroud`, `CreatesShroud`, and `ShroudRenderer`.
6. **Capture mechanics** — `CaptureManager`, `Captures`, and `Capturable` for engineer-style capture (and reusable capture via `ConsumedByCapture: false`).
7. **Cloak/stealth** — the `Cloak` trait, `UncloakOn`, detection types, and `DetectCloaked`.
8. **Voxel units** — `ModelSequences`, `RenderVoxels`, `WithVoxelBody`, and TS-style actor rules.
9. **Custom AI bots** — `ModularBot` and the bot-module ecosystem configured in `ai.yaml`.

Each walkthrough is designed to be copied into a mod and iterated on, with verification steps and common pitfalls to speed up debugging.

## What to read next

- [Part 10.3 — Porting, Modding, and Developer Workflows](../chapters/Part_10_Chapter_03_Port_And_Modding.md) for the broader mod development workflow.
- [Appendix E — Practical Modding Recipes](Appendix_E_Practical_Recipes.md) for shorter, more focused recipes that complement these walkthroughs.
- [Appendix H — Asset Visual Reference](Appendix_H_Asset_Visual_Reference.md) for sprite, sequence, and voxel asset conventions.
- [Part 1.1 — ECS, Actors, and Traits](../chapters/Part_01_Chapter_01_ECS.md) for the fundamentals of OpenRA's trait system.
- [Part 2.4 — Rulesets, Actors, and Weapons](../chapters/Part_02_Chapter_04_Rules_Weapons.md) for YAML ruleset authoring.
- [Part 4.3 — Widgets and Chrome](../chapters/Part_04_Chapter_03_Widgets.md) for deeper Chrome UI internals.
- [Part 6.1 — Lua and Eluant](../chapters/Part_06_Chapter_01_Lua_Eluant.md) and [Part 6.2 — ScriptContext](../chapters/Part_06_Chapter_02_ScriptContext.md) for mission scripting internals.
- [Part 8.1 — IBot](../chapters/Part_08_Chapter_01_IBot.md) and [Part 8.2 — Bot Modules](../chapters/Part_08_Chapter_02_Bot_Modules.md) for AI architecture.