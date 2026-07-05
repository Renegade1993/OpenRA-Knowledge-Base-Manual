# Appendix E — Practical Modding Recipes

This appendix provides copy-paste-friendly recipes for the most common OpenRA [modding](Appendix_A_Glossary.md) tasks. They are intended as a practical complement to the architecture chapters ([Part 1.1 — ECS, Actors, and Traits](../chapters/Part_01_Chapter_01_ECS.md), [Part 2.4 — Rulesets, Actors, and Weapons](../chapters/Part_02_Chapter_04_Rules_Weapons.md), [Part 3.1 — Mod SDK and Project Structure](../chapters/Part_03_Chapter_01_Mod_SDK.md), [Part 4.3 — Widgets and Chrome](../chapters/Part_04_Chapter_03_Widgets.md), [Part 10.3 — Porting, Modding, and Developer Workflows](../chapters/Part_10_Chapter_03_Port_And_Modding.md)) and [Appendix B — Common YAML Patterns](Appendix_B_Common_YAML_Patterns.md).

> **Note:** All examples use the Red Alert mod as the baseline. File paths are relative to your mod folder, e.g. `mods/ra/` or `mods/my-mod/`.

---

## Recipe 1 — Add a New Weapon

**Goal:** Clone an existing rifle and increase its rate of fire.

**What you need to know first:** [Part 2.4 — Rulesets, Actors, and Weapons](../chapters/Part_02_Chapter_04_Rules_Weapons.md) and the weapon definition in [Appendix B — Common YAML Patterns](Appendix_B_Common_YAML_Patterns.md).

**Files to edit:** `mods/ra/weapons/smallcaliber.yaml` (or a new file loaded under `Weapons:` in `mod.yaml`).

**Before:**

```yaml
M1Carbine:
    Inherits: ^LightMG
    ReloadDelay: 20
    Range: 5c0
    Report: gun11.aud
```

**After:**

```yaml
M2Carbine:
    Inherits: M1Carbine
    ReloadDelay: 15
    Burst: 3
    BurstDelays: 3
    Warhead@1Dam: SpreadDamage
        Damage: 1200
        Versus:
            None: 150
            Wood: 40
            Light: 50
            Heavy: 25
            Concrete: 15
```

**How to verify it works:**
- Attach it to a unit: `Armament: Weapon: M2Carbine`.
- Run `OpenRA.Utility.exe ra --check-yaml` and test in a skirmish.

**Common pitfalls:**
- The weapon name in `Armament` must match the YAML key exactly.
- `ReloadDelay` is in ticks; lower is faster.

---

## Recipe 2 — Add a New Vehicle with Sequences and Voice

**Goal:** Add a fast scout vehicle with its own sprite, weapon, and voice set.

**What you need to know first:** [Part 2.4 — Rulesets, Actors, and Weapons](../chapters/Part_02_Chapter_04_Rules_Weapons.md), [Part 6.5 — Asset Loaders](../chapters/Part_06_Chapter_05_Asset_Loaders.md), and the inheritance/sequence examples in [Appendix B — Common YAML Patterns](Appendix_B_Common_YAML_Patterns.md).

**Files to edit:**
- `mods/ra/rules/vehicles.yaml`
- `mods/ra/sequences/vehicles.yaml`
- `mods/ra/audio/voices.yaml` (for a custom voice set)

**Before:**

```yaml
1TNK:
    Inherits: ^TrackedVehicle
    Inherits@GAINSEXPERIENCE: ^GainsExperience
    Buildable:
        Queue: Vehicle
        BuildPaletteOrder: 120
```

**After:**

`rules/vehicles.yaml`:

```yaml
RAIDR:
    Inherits: ^Vehicle
    Inherits@GAINSEXPERIENCE: ^GainsExperience
    Inherits@AUTOTARGET: ^AutoTargetGroundAssaultMove
    Buildable:
        Queue: Vehicle
        BuildPaletteOrder: 330
        Prerequisites: ~vehicles.allies, ~techlevel.low
        Description: actor-raidr.description
    Valued:
        Cost: 600
    Tooltip:
        Name: actor-raidr.name
    Health:
        HP: 15000
    Armor:
        Type: Light
    Mobile:
        Speed: 160
        Locomotor: wheeled
    RevealsShroud:
        Range: 7c0
    Armament:
        Weapon: M2Carbine
        LocalOffset: 0,0,128
    AttackFrontal:
        FacingTolerance: 0
    WithFacingSpriteBody:
    AutoTarget:
        ScanRadius: 7
    RenderSprites:
        Image: raidr
    Voiced:
        VoiceSet: RaiderVoice
```

`sequences/vehicles.yaml`:

```yaml
raidr:
    Defaults:
        Filename: raidr.shp
    idle:
        Facings: 32
        UseClassicFacings: True
    icon:
        Filename: raidricon.shp
```

`audio/voices.yaml`:

```yaml
RaiderVoice:
    Inherits: VehicleVoice
    Voices:
        Select: vehic1,report1
        Action: ackno,affirm1
```

**How to verify it works:**
- Ensure the `raidr.shp` and `raidricon.shp` assets are in a loaded package.
- Run `--check-yaml` and start a skirmish; confirm the unit moves, fires, and speaks.

**Common pitfalls:**
- The sequence key must match the `RenderSprites.Image` value (or the actor ID if `RenderSprites` is omitted).
- `BuildPaletteOrder` must be unique within the same queue.

---

## Recipe 3 — Add a New Building with Production

**Goal:** Add a factory that produces units from the existing Vehicle queue.

**What you need to know first:** [Part 2.4 — Rulesets, Actors, and Weapons](../chapters/Part_02_Chapter_04_Rules_Weapons.md) and the building/production [traits](Appendix_A_Glossary.md) in [Part 3.1 — Mod SDK and Project Structure](../chapters/Part_03_Chapter_01_Mod_SDK.md). Review `SPEN` or `WEAP` in `rules/structures.yaml`.

**Files to edit:**
- `mods/ra/rules/structures.yaml`
- `mods/ra/sequences/structures.yaml`

**Before:**

```yaml
SPEN:
    Inherits: ^Building
    Inherits@PRIMARY: ^PrimaryBuilding
    Production:
        Produces: Ship, Submarine
    ProductionBar:
        ProductionType: Ship
    RallyPoint:
```

**After:**

`rules/structures.yaml`:

```yaml
AFA:
    Inherits: ^Building
    Inherits@PRIMARY: ^PrimaryBuilding
    Inherits@IDISABLE: ^DisableOnLowPowerOrPowerDown
    Buildable:
        Queue: Building
        BuildPaletteOrder: 200
        Prerequisites: fix, anypower, ~vehicles.allies, ~techlevel.medium
        Description: actor-afa.description
    Valued:
        Cost: 1200
    Tooltip:
        Name: actor-afa.name
    Building:
        Footprint: xxx xxx
        Dimensions: 3,2
    Health:
        HP: 90000
    Armor:
        Type: Wood
    RevealsShroud:
        Range: 5c0
    Exit@1:
        SpawnOffset: 0,0,0
        ExitCell: 0,2
        ProductionTypes: Vehicle
    Production:
        Produces: Vehicle
    ProductionBar:
        ProductionType: Vehicle
    RallyPoint:
    Power:
        Amount: -30
    WithIdleOverlay@DOOR:
        Sequence: idle
        RequiresCondition: !build-incomplete
```

`sequences/structures.yaml`:

```yaml
afa:
    Defaults:
        Filename: afa.shp
    idle:
        Length: 16
        Tick: 120
    make:
        Filename: afamake.shp
        Length: *
    icon:
        Filename: afaicon.shp
```

**How to verify it works:**
- Ensure the `afa.shp` and `afaicon.shp` assets are in a loaded package.
- Run `--check-yaml` and start a skirmish; confirm the AFA can produce vehicles.

**Common pitfalls:**
- `Footprint` must match `Building.Dimensions` exactly; each character is one cell.
- `ExitCell` must be a clear, passable cell or units will get stuck.
- `Production.Produces` and `ProductionBar.ProductionType` must match a `ClassicProductionQueue` `Type` in `rules/player.yaml`.

---

## Recipe 4 — Add a Support Power

**Goal:** Add a single-target invulnerability power to a new building.

**What you need to know first:** [Part 3.1 — Mod SDK and Project Structure](../chapters/Part_03_Chapter_01_Mod_SDK.md) for support powers and [Part 1.1 — ECS, Actors, and Traits](../chapters/Part_01_Chapter_01_ECS.md) for the [condition](Appendix_A_Glossary.md) system. The Iron Curtain in `rules/structures.yaml` is the canonical example.

**Files to edit:**
- `mods/ra/rules/structures.yaml`
- `mods/ra/sequences/structures.yaml` (for the icon and building artwork)
- `mods/ra/audio/notifications.yaml` (optional, for charging/ready speech)

**Before:**

```yaml
GrantExternalConditionPower@IRONCURTAIN:
    Icon: invuln
    ChargeInterval: 3000
    Duration: 400
    Condition: invulnerability
    SupportPowerPaletteOrder: 10
```

**After:**

```yaml
SHIELD:
    Inherits: ^ScienceBuilding
    Inherits@IDISABLE: ^DisableOnLowPowerOrPowerDown
    Inherits@shape: ^2x2Shape
    Buildable:
        Queue: Defense
        BuildPaletteOrder: 150
        Prerequisites: atek, ~structures.allies, ~techlevel.high
        BuildLimit: 1
        Description: actor-shield.description
    Valued:
        Cost: 1500
    Tooltip:
        Name: actor-shield.name
    Building:
        Footprint: xx xx
        Dimensions: 2,2
    Health:
        HP: 60000
    Armor:
        Type: Heavy
    RevealsShroud:
        Range: 6c0
    GrantExternalConditionPower@SHIELD:
        Icon: shield
        ChargeInterval: 6000
        Duration: 300
        Name: actor-shield.shield-name
        Description: actor-shield.shield-description
        Condition: invulnerability
        OnFireSound: ironcur9.aud
        SelectTargetSpeechNotification: SelectTarget
        EndChargeSpeechNotification: IronCurtainReady
        SupportPowerPaletteOrder: 80
        DisplayRadarPing: True
    SupportPowerChargeBar:
    Power:
        Amount: -100
    WithIdleOverlay:
        Sequence: idle
        RequiresCondition: !build-incomplete
```

**How to verify it works:**
- Ensure the `shield` icon is defined in a sequence or chrome image set.
- Run `--check-yaml` and test in a skirmish; the target should gain the Iron Curtain overlay and become invulnerable.

**Common pitfalls:**
- The target actor must accept the condition. In RA, all units and buildings inherit `^IronCurtainable`, which defines `ExternalCondition@INVULNERABILITY` with the condition `invulnerability`.
- `SupportPowerPaletteOrder` must be unique across all support powers for that player.
- `Duration` is in ticks; `300` ticks is about 7.5 seconds at default speed.

---

## Recipe 5 — Add a Status Effect with a Condition

**Goal:** Make a vehicle move faster when it is heavily damaged.

**What you need to know first:** [Part 1.1 — ECS, Actors, and Traits](../chapters/Part_01_Chapter_01_ECS.md) for condition tokens and the `GrantConditionOnDamageState` / `SpeedMultiplier` [traits](Appendix_A_Glossary.md) in `defaults.yaml` and `rules/vehicles.yaml`.

**Files to edit:** `mods/ra/rules/vehicles.yaml` (or any actor file).

**Before:**

```yaml
^Vehicle:
    GrantConditionOnDamageState@DAMAGED:
        Condition: damaged
        ValidDamageStates: Light, Medium, Heavy, Critical
```

**After:**

```yaml
RAIDR:
    Inherits: ^Vehicle
    ...
    GrantConditionOnDamageState@DESPERATE:
        Condition: desperate
        ValidDamageStates: Heavy, Critical
        GrantPermanently: false
    SpeedMultiplier@DESPERATE:
        Modifier: 125
        RequiresCondition: desperate
    WithDecoration@DESPERATE:
        Image: pips
        Sequence: tag
        RequiresCondition: desperate
        Position: TopRight
        Margin: 5, 5
```

**How to verify it works:**
- Run `--check-yaml` and start a skirmish.
- Let the RAIDR take heavy damage; its speed should increase and the decoration should appear.

**Common pitfalls:**
- The condition name (`desperate`) must match exactly in every trait that references it.
- Damage states are percentages of max HP, not absolute values.
- Multiple `SpeedMultiplier` modifiers stack multiplicatively.

---

![Recipe 6  add a custom c trait diagram](images/Appendix_E_Practical_Recipes-extension-hook-diagram-showing-the-interface-s-to-implement-b4a27b.svg)

## Recipe 6 — Add a Custom C# Trait


**Goal:** Give the player a cash bonus every time a specific actor is built.

**What you need to know first:** [Part 1.1 — ECS, Actors, and Traits](../chapters/Part_01_Chapter_01_ECS.md), [Appendix D — Engine Conventions and Style](Appendix_D_Engine_Conventions.md), and the `PlayerResources` [trait](Appendix_A_Glossary.md) in `OpenRA.Mods.Common/Traits/Player/PlayerResources.cs`.

**Files to edit:**
- A new C# file in your custom mod assembly, e.g. `OpenRA.Mods.MyMod/Traits/CashOnCreated.cs`
- `mods/ra/mod.yaml` (add the assembly to `Assemblies:`)
- The actor YAML where you want to use the trait

**C# snippet:**

```csharp
using OpenRA.Traits;
using OpenRA.Mods.Common.Traits;

namespace OpenRA.Mods.MyMod.Traits
{
    [Desc("Grants a cash bonus to the owner when this actor is created.")]
    public class CashOnCreatedInfo : TraitInfo
    {
        [FieldLoader.Require]
        [Desc("Cash amount to grant when the actor is created.")]
        public readonly int Amount = 0;

        public override object Create(ActorInitializer init) { return new CashOnCreated(init, this); }
    }

    public class CashOnCreated : INotifyCreated
    {
        readonly CashOnCreatedInfo info;

        public CashOnCreated(ActorInitializer init, CashOnCreatedInfo info)
        {
            this.info = info;
        }

        void INotifyCreated.Created(Actor self)
        {
            // PlayerResources lives on the player actor, not on the unit itself.
            var playerResources = self.Owner.PlayerActor.Trait<PlayerResources>();
            playerResources.GiveCash(info.Amount);
        }
    }
}
```

**After:**

`mod.yaml`:

```yaml
Assemblies:
    OpenRA.Mods.Common.dll
    OpenRA.Mods.Cnc.dll
    OpenRA.Mods.MyMod.dll
```

`rules/structures.yaml`:

```yaml
AFA:
    ...
    CashOnCreated:
        Amount: 500
```

**How to verify it works:**
- Build the custom mod assembly and ensure the DLL is next to the game executable.
- Run `--check-yaml` and start a skirmish; build the AFA and confirm the cash increases by 500.

**Common pitfalls:**
- The YAML trait name is the class name without the `Info` suffix (`CashOnCreated`).
- The custom assembly must be listed in `mod.yaml` and built against the same engine version.
- `GiveCash` affects the simulation; if you add randomness, use `world.SharedRandom`, not `Game.CosmeticRandom`.

---

## Recipe 7 — Add a New Production Queue and Build Tab

**Goal:** Add a new "Superweapon" production queue and a matching sidebar tab.

**What you need to know first:** [Part 4.3 — Widgets and Chrome](../chapters/Part_04_Chapter_03_Widgets.md) and the production-queue definitions in `rules/player.yaml`.

**Files to edit:**
- `mods/ra/rules/player.yaml`
- `mods/ra/chrome/ingame-player.yaml`
- `mods/ra/chrome.yaml`
- `mods/ra/fluent/chrome.ftl` (for the tooltip text)

**Before:**

```yaml
ClassicProductionQueue@Vehicle:
    Type: Vehicle
    DisplayOrder: 3
    ...
```

```yaml
ProductionTypeButton@VEHICLE:
    Y: 93
    ProductionGroup: Vehicle
```

**After:**

`rules/player.yaml`:

```yaml
ClassicProductionQueue@Super:
    Type: Super
    DisplayOrder: 6
    LowPowerModifier: 300
    ReadyAudio: UnitReady
    ReadyTextNotification: notification-unit-ready
    BlockedAudio: NoBuild
    BlockedTextNotification: notification-unable-to-build-more
    LimitedAudio: BuildingInProgress
    LimitedTextNotification: notification-unable-to-comply-building-in-progress
    QueuedAudio: Building
    OnHoldAudio: OnHold
    CancelledAudio: Cancelled
    SpeedUp: True
```

`chrome/ingame-player.yaml` (inside `Container@PRODUCTION_TYPES`):

```yaml
ProductionTypeButton@SUPER:
    Logic: AddFactionSuffixLogic
    Y: 186
    Width: 28
    Height: 28
    VisualHeight: 0
    Background: sidebar-button
    TooltipText: button-production-types-super-tooltip
    TooltipContainer: TOOLTIP_CONTAINER
    ProductionGroup: Super
    Key: ProductionTypeSuper
    Children:
        Image@ICON:
            X: 6
            Y: 6
            ImageCollection: production-icons
            ImageName: super
```

`chrome.yaml`:

```yaml
production-icons:
    Inherits: ^Glyphs
    Regions:
        ...
        super: 204, 68, 16, 16
        super-disabled: 204, 85, 16, 16
        super-alert: 204, 102, 16, 16
```

`fluent/chrome.ftl`:

```ftl
button-production-types-super-tooltip = Superweapon
```

Finally, assign a building to the new queue (for example, the SHIELD from Recipe 4):

```yaml
SHIELD:
    Buildable:
        Queue: Super
        BuildPaletteOrder: 10
```

**How to verify it works:**
- Run `--check-yaml` and start a skirmish.
- Build the SHIELD prerequisites; a new "Superweapon" tab should appear in the sidebar.

**Common pitfalls:**
- `ProductionGroup` in the button must exactly match the `Type` field of the `ClassicProductionQueue`.
- `DisplayOrder` controls the queue order in the UI; do not reuse an existing value.
- The `Key` field must be defined in the hotkey file if you want a keyboard shortcut.

## Summary

This appendix provides copy-paste-friendly recipes for the most common OpenRA modding tasks: adding weapons, vehicles, buildings, support powers, production queues, and more. Each recipe explains the goal, the files to edit, the before/after YAML, how to verify it works, and the pitfalls to avoid.

## What to read next

- **For the architecture behind actors and traits:** [Part 1.1 — ECS, Actors, and Traits](../chapters/Part_01_Chapter_01_ECS.md)
- **For weapon and ruleset design:** [Part 2.4 — Rulesets, Actors, and Weapons](../chapters/Part_02_Chapter_04_Rules_Weapons.md)
- **For YAML pattern snippets and syntax:** [Appendix B — Common YAML Patterns](Appendix_B_Common_YAML_Patterns.md)
- **For engine conventions when writing custom C# traits:** [Appendix D — Engine Conventions and Style](Appendix_D_Engine_Conventions.md)
- **For debugging recipes that do not work:** [Appendix C — Debugging and Troubleshooting](Appendix_C_Debugging.md)
- **For custom asset packages and VFS mounting:** [Part 6.3 — Virtual File System](../chapters/Part_06_Chapter_03_VFS.md)
- **For random map generator recipes:** [Part 7.1 — Map Generation Pipeline Overview](../chapters/Part_07_Chapter_01_Pipeline.md)
- **For testing your changes:** [Appendix F — Testing](Appendix_F_Testing.md)
- **For longer advanced walkthroughs:** [Appendix G — Advanced Modding Walkthroughs](Appendix_G_Advanced_Modding_Walkthroughs.md)