# Appendix B — Common YAML Patterns

This appendix collects the [MiniYaml](Appendix_A_Glossary.md) patterns you will encounter most often when reading or writing OpenRA rules. It is designed as a quick reference and a learning aid: each pattern shows a concrete example, explains why it works, and points to the relevant chapter.

## Abstract actors and inheritance

[Abstract Actor](Appendix_A_Glossary.md)s start with `^` and are never spawned directly. They exist to be inherited by concrete actors.

```yaml
^Infantry:
    Inherits@1: ^ExistsInWorld
    Inherits@2: ^SpriteActor
    Health:
        HP: 5000
    Mobile:
        Speed: 40
    AttackFrontal:
        FacingTolerance: 0

E1:
    Inherits: ^Infantry
    Buildable:
        Queue: Infantry
        Cost: 100
    Mobile:
        Speed: 50
```

**Why this works:** `[ActorInfo](Appendix_A_Glossary.md)` merges the inherited nodes before creating the `[TraitInfo](Appendix_A_Glossary.md)` collection. The concrete actor (`E1`) inherits `Health` and `Mobile` from `^Infantry`, then overrides `Mobile.Speed`. This keeps common defaults in one place.

**See:** [Part 2.4 — Rulesets, Actors, and Weapons](../chapters/Part_02_Chapter_04_Rules_Weapons.md).

## Multiple inheritance with keyed inherits

When an actor inherits from several abstract actors, use keyed inherits to avoid node-name collisions.

```yaml
E1:
    Inherits@1: ^Infantry
    Inherits@2: ^AutoTargetGround
    Inherits@3: ^ProducibleWithQueue
```

**Why this works:** The merge algorithm treats each `[Inherits](Appendix_A_Glossary.md)@N` as a separate merge source. Without the `@N` suffix, later `Inherits` keys would overwrite earlier ones.

## Trait instances

Multiple instances of the same [trait](Appendix_A_Glossary.md) can be attached to one actor using the `@Name` suffix.

```yaml
E1:
    Armament@PRIMARY:
        Name: primary
        Weapon: M1Carbine
        LocalOffset: 0,0,171
    Armament@SECONDARY:
        Name: secondary
        Weapon: Grenade
        LocalOffset: 0,0,171
```

**Why this works:** `TraitInfo.[InstanceName](Appendix_A_Glossary.md)` stores the suffix. Traits that reference armaments (e.g., `AttackFrontal`) use the `Name` field to select which one to fire.

**See:** [Part 1.1 — ECS, Actors, and Traits](../chapters/Part_01_Chapter_01_ECS.md) and [Part 2.4 — Rulesets, Actors, and Weapons](../chapters/Part_02_Chapter_04_Rules_Weapons.md).

## Removing inherited traits

Prefix a trait name with `-` to remove an inherited trait.

```yaml
DOG:
    Inherits: ^Infantry
    -AttackFrontal:
    -Armament:
    AttackLeap:
        ...
```

**Why this works:** The merge pass treats `-TraitName` as a removal instruction before the final `TraitInfo` collection is built.

## Conditional trait interfaces

Some traits can be disabled by conditions (e.g., `Disabled`, `Parking`, `Emp`). This is controlled by `RequiresCondition` and `PauseOnCondition`.

```yaml
E1:
    Mobile:
        Speed: 50
        PauseOnCondition: disabled || emp
    WithInfantryBody:
        RequiresCondition: !disabled
```

**Why this works:** The condition system evaluates tokens like `disabled` and `emp`. `PauseOnCondition` stops the trait from ticking; `RequiresCondition` hides it from interface queries.

**See:** [Part 1.1 — ECS, Actors, and Traits](../chapters/Part_01_Chapter_01_ECS.md) for condition tokens.

## Weapon definition

```yaml
M1Carbine:
    Range: 4c0
    ReloadDelay: 20
    Burst: 3
    BurstDelay: 5
    Report: gun11.aud
    Projectile: Bullet
        Speed: 1c682
    Warhead@1Dam: SpreadDamage
        Spread: 0c256
        Damage: 1500
        Versus:
            None: 100
            Wood: 60
            Light: 40
            Heavy: 25
            Concrete: 10
    Warhead@2Eff: CreateEffect
        Explosions: piff
```

**Why this works:** `[WeaponInfo](Appendix_A_Glossary.md)` loads the projectile and [warhead](Appendix_A_Glossary.md) nodes. Multiple warheads are allowed. `Versus` modifies damage based on the target's armor type.

**See:** [Part 2.4 — Rulesets, Actors, and Weapons](../chapters/Part_02_Chapter_04_Rules_Weapons.md).

## Sequence definition

```yaml
e1:
    idle:
        Start: 0
        Facings: 8
    run:
        Start: 8
        Length: 6
        Facings: 8
        Tick: 120
    die:
        Start: 134
        Length: 8
        Facings: 8
        Tick: 80
```

**Why this works:** The image key (`e1`) matches the sprite file. The [sequence](Appendix_A_Glossary.md) name (`idle`) is referenced by render traits. `Facings` duplicates the frames for each orientation.

**See:** [Part 6.5 — Asset Loaders](../chapters/Part_06_Chapter_05_Asset_Loaders.md) and [Part 4.1 — Renderer, Sheet, and Sprite](../chapters/Part_04_Chapter_01_Renderer.md).

![Chrome widget definition diagram](images/Appendix_B_Common_YAML_Patterns-widget-tree-diagram-showing-parent-child-nesting-focus-path-3925dd.svg)

## Chrome widget definition


```yaml
MainMenu:
    Container:
        Logic: MainMenuLogic
        X: (WINDOW_RIGHT - WIDTH)/2
        Y: (WINDOW_BOTTOM - HEIGHT)/2
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
```

**Why this works:** `WidgetLoader` instantiates the [widget](Appendix_A_Glossary.md) class named by the node key (`Container`, `Label`, `Button`). The `@ID` suffix sets the widget ID. The `Logic` class receives the widget and drives its behavior.

**See:** [Part 4.3 — Widgets and Chrome](../chapters/Part_04_Chapter_03_Widgets.md).

## Map generator definition

```yaml
World:
    ClassicMapGenerator:
        TerrainDensity: 0x40
        Water: 0.2
        WaterDepth: 3
        TerrainFeatures: 0.3
        ResourceSpawn: 0.1
```

**Why this works:** The `World` actor is the root for map-level systems. The `ClassicMapGenerator` trait is registered as a map generator and appears in the skirmish lobby.

**See:** [Part 7.6 — Mod-Specific Generators](../chapters/Part_07_Chapter_06_Mod_Generators.md).

## Bot module configuration

```yaml
Player:
    ModularBot:
        Type: rush
    BaseBuilderBotModule:
        MinimumExcessPower: 15
        MaximumExcessPower: 150
        ConstructionYardTypes: fact
        McvTypes: mcv
    UnitBuilderBotModule:
        UnitQueues: Infantry, Vehicle
        UnitsToBuild:
            e1: 50
            e2: 25
            jeep: 25
            tank: 50
    SquadManagerBotModule:
        SquadSize: 10
        IdleScanRadius: 10
        AttackScanRadius: 12
```

**Why this works:** `[ModularBot](Appendix_A_Glossary.md)` is the coordinator. The other [bot modules](Appendix_A_Glossary.md) are independent traits that each implement a slice of AI behavior. They all read the same `Player` actor.

**See:** [Part 8.2 — Bot Modules](../chapters/Part_08_Chapter_02_Bot_Modules.md).

## Conditions

Conditions are boolean flags that traits expose to each other.

```yaml
^Vehicle:
    GrantConditionOnDamageState@CRITICAL:
        Condition: critical
        ValidDamageState: Critical
    WithDamageOverlay:
        Image: fire
        RequiresCondition: critical
```

**Why this works:** `GrantConditionOnDamageState` sets `critical` when the actor enters the critical damage state. `WithDamageOverlay` only renders the fire overlay while the condition is active.

## Global mod data

Custom mod-wide data can be declared in `mod.yaml` under the mod ID.

```yaml
my-mod:
    MyGlobalData:
        Foo: 123
        Bar: hello
```

**Why this works:** `ModData` creates an instance of `MyGlobalData` (which must implement `IGlobalModData`) and loads it with `[FieldLoader](Appendix_A_Glossary.md)`. It can be accessed anywhere via `modData.GetOrCreate<MyGlobalData>()`.

**See:** [Part 3.1 — Mod SDK and Project Structure](../chapters/Part_03_Chapter_01_Mod_SDK.md).

## Good vs. bad patterns

The best way to avoid MiniYaml errors is to compare a broken snippet with the corrected version. Each pair below shows the mistake first, then the fix, and explains why the engine rejects or misinterprets the bad version.

### 1. Wrong indentation / mixing tabs and spaces

OpenRA's parser counts one indentation level per tab or per four spaces. Mixing them silently changes the parent/child relationship.

**Bad:**

```yaml
E1:
    Inherits: ^Infantry
  Health:
      HP: 5000
```

**Good:**

```yaml
E1:
    Inherits: ^Infantry
    Health:
        HP: 5000
```

**Why it matters:** The bad version places `Health` at the wrong level, so the parser treats it as a sibling of `E1` instead of a child. This usually produces a "Sequence contains no matching element" or unexpected node error during `Ruleset.LoadDefaults`.

**See:** [Part 2.1 — MiniYaml Parser](../chapters/Part_02_Chapter_01_MiniYaml.md).

### 2. Missing `Inherits:` or misspelled parent name

Templates are referenced by exact name. A typo or missing line leaves the actor without its default traits.

**Bad:**

```yaml
E1:
    Inherits: ^Infentry
    Health:
        HP: 5000
```

**Good:**

```yaml
E1:
    Inherits: ^Infantry
    Health:
        HP: 5000
```

**Why it matters:** `^Infentry` does not exist, so the inheritance resolver fails with a "Missing parent" error. The actor also loses the `Mobile`, `RevealsShroud`, and other traits defined in `^Infantry`.

### 3. Duplicate `BuildPaletteOrder` in the same queue

Two actors in the same production queue cannot share the same palette order. The second one may hide or displace the first.

**Bad:**

```yaml
E1:
    Buildable:
        Queue: Infantry
        BuildPaletteOrder: 10

E2:
    Buildable:
        Queue: Infantry
        BuildPaletteOrder: 10
```

**Good:**

```yaml
E1:
    Buildable:
        Queue: Infantry
        BuildPaletteOrder: 10

E2:
    Buildable:
        Queue: Infantry
        BuildPaletteOrder: 20
```

**Why it matters:** `BuildPaletteOrder` is the sort key in the production palette. Duplicates are accepted by the parser but cause layout conflicts in the UI and make one icon unclickable.

### 4. Condition name mismatch across traits

A condition granted by one trait must be spelled exactly the same in every trait that reacts to it.

**Bad:**

```yaml
E1:
    GrantConditionOnDamageState@CRITICAL:
        Condition: critical
    WithDamageOverlay:
        Image: fire
        RequiresCondition: critcal
```

**Good:**

```yaml
E1:
    GrantConditionOnDamageState@CRITICAL:
        Condition: critical
    WithDamageOverlay:
        Image: fire
        RequiresCondition: critical
```

**Why it matters:** `critcal` is never granted, so `WithDamageOverlay` never activates. The actor will not show the fire overlay even when heavily damaged. Condition tokens are literal strings, not inferred.

**See:** [Part 1.1 — ECS, Actors, and Traits](../chapters/Part_01_Chapter_01_ECS.md) and the "Conditions" section earlier in this appendix.

### 5. Forgetting the `@` instance suffix when adding multiple instances of the same trait

Without the suffix, the second trait definition overwrites the first.

**Bad:**

```yaml
E1:
    Armament:
        Weapon: M1Carbine
    Armament:
        Weapon: Grenade
```

**Good:**

```yaml
E1:
    Armament@PRIMARY:
        Weapon: M1Carbine
    Armament@SECONDARY:
        Weapon: Grenade
```

**Why it matters:** The bad version leaves `E1` with only the Grenade armament. The `AttackFrontal` trait will fire only that weapon, and the rifle will be missing entirely. The suffix is stored in `TraitInfo.InstanceName` and lets the engine keep both instances.

**See:** [Part 2.4 — Rulesets, Actors, and Weapons](../chapters/Part_02_Chapter_04_Rules_Weapons.md) and the "Trait instances" section earlier in this appendix.

### 6. Referencing a sequence key that does not match `RenderSprites.Image` or the actor ID

Render traits look up sequences by image name, not by actor name, unless the actor name is used as the default image.

**Bad:**

```yaml
E1:
    RenderSprites:
        Image: e1
    WithInfantryBody:
        Sequence: runn
```

**Good:**

```yaml
E1:
    RenderSprites:
        Image: e1
    WithInfantryBody:
        Sequence: run
```

**Why it matters:** The sequence block in `mods/ra/sequences/infantry.yaml` defines `run`, not `runn`. A missing sequence causes the renderer to throw a `SequenceNotFoundException` or display a blank sprite.

**See:** [Part 6.5 — Asset Loaders](../chapters/Part_06_Chapter_05_Asset_Loaders.md) and [Part 4.1 — Renderer, Sheet, and Sprite](../chapters/Part_04_Chapter_01_Renderer.md).

### 7. Forgetting to list a new file in `mod.yaml`

A YAML file that is not listed in the manifest is never loaded, no matter how correct its contents are.

**Bad:**

```yaml
Rules:
    mods/ra/rules/defaults.yaml
    mods/ra/rules/infantry.yaml
    # vehicles.yaml is missing
```

**Good:**

```yaml
Rules:
    mods/ra/rules/defaults.yaml
    mods/ra/rules/infantry.yaml
    mods/ra/rules/vehicles.yaml
```

**Why it matters:** `mod.yaml` is the entry point for `MiniYaml.Load`. If `vehicles.yaml` is omitted, any actor defined in it is invisible to the ruleset and the game cannot spawn it.

**See:** [Part 2.4 — Rulesets, Actors, and Weapons](../chapters/Part_02_Chapter_04_Rules_Weapons.md) and [Part 3.1 — Mod SDK and Project Structure](../chapters/Part_03_Chapter_01_Mod_SDK.md).

## Complete minimal actor examples

The blocks below are intentionally small but complete: each one contains the minimum set of traits needed for the actor to be spawned, rendered, and functional. They are useful as starting points for new units.

### Minimal infantry actor

```yaml
RIFLE:
    Inherits: ^Infantry
    Health:
        HP: 10000
    Mobile:
        Speed: 50
    RevealsShroud:
        Range: 5c0
    RenderSprites:
        Image: rifle
    WithInfantryBody:
    Armament:
        Weapon: M1Carbine
    AttackFrontal:
        FacingTolerance: 0
```

**Why it works:** `^Infantry` supplies the base interface, selection, and selection-box traits. `Health`, `Mobile`, and `RevealsShroud` make the actor spawn and move. `RenderSprites` plus `WithInfantryBody` provide the sprite animation, `Armament` attaches a weapon, and `AttackFrontal` lets the player issue attack orders.

**See:** `mods/ra/rules/infantry.yaml` and `mods/ra/sequences/infantry.yaml`.

### Minimal vehicle actor

```yaml
JEEP:
    Inherits: ^Vehicle
    Mobile:
        Speed: 120
        Locomotor: wheeled
    Health:
        HP: 15000
    Armor:
        Type: Light
    RevealsShroud:
        Range: 6c0
    RenderSprites:
        Image: jeep
    WithFacingSpriteBody:
    Armament:
        Weapon: M1Carbine
    AttackFrontal:
        FacingTolerance: 0
```

**Why it works:** `^Vehicle` provides the default vehicle behavior and selection logic. `Mobile` with a `Locomotor` references the movement class defined in `mods/ra/rules/defaults.yaml`. `Armor` assigns a type that warheads use for `Versus` calculations. `WithFacingSpriteBody` renders the chassis with directional facings, while `Armament` and `AttackFrontal` handle combat.

**See:** `mods/ra/rules/vehicles.yaml` and `mods/ra/sequences/vehicles.yaml`.

### Minimal building actor

```yaml
TENT:
    Inherits: ^Building
    Building:
        Footprint: xx xx
        Dimensions: 2,2
    Health:
        HP: 60000
    Armor:
        Type: Wood
    RevealsShroud:
        Range: 5c0
    RenderSprites:
        Image: tent
    WithIdleOverlay:
        Sequence: idle
    Power:
        Amount: -30
    Exit@1:
        ExitCell: 0,2
        ProductionTypes: Infantry
    Production:
        Produces: Infantry
    RallyPoint:
```

**Why it works:** `^Building` supplies placement, selection, and damage-state logic. `Building` defines the footprint and dimensions. `WithIdleOverlay` renders the idle animation. `Power` makes the structure require a power plant. `Exit`, `Production`, and `RallyPoint` allow the building to create units and send them to a rally point.

**See:** `mods/ra/rules/structures.yaml`, `mods/ra/rules/defaults.yaml`, and `mods/ra/sequences/structures.yaml`.

### Minimal weapon definition

```yaml
M1Carbine:
    ReloadDelay: 20
    Range: 4c0
    ValidTargets: Ground, Water
    Projectile: InstantHit
    Warhead: SpreadDamage
        Spread: 0c256
        Damage: 1500
        ValidTargets: Ground, Water
```

**Why it works:** `ReloadDelay` sets the fire interval in ticks. `Range` defines the maximum attack distance. `ValidTargets` restricts what the weapon can aim at. `Projectile: InstantHit` means the shot reaches the target immediately with no visible projectile. `Warhead: SpreadDamage` applies area damage when the shot lands. Every weapon must have at least one projectile and one warhead.

**See:** `mods/ra/weapons/smallcaliber.yaml` and [Part 2.4 — Rulesets, Actors, and Weapons](../chapters/Part_02_Chapter_04_Rules_Weapons.md).

## Common mistakes in YAML

- **Forgetting the `^` prefix on abstract actors.** If `^Infantry` is defined without `^`, it will appear as a spawnable unit.
- **Using `Inherits:` without keyed names when inheriting multiple blocks.** Later `Inherits` keys overwrite earlier ones.
- **Forgetting that `TraitInfo` fields are case-sensitive.** `Speed` and `speed` are different fields.
- **Removing a trait that is required by another trait.** `Requires<T>` dependencies will throw an error during ruleset construction.
- **Referencing a sequence that does not exist.** The renderer will crash or show a missing sprite.
- **Using `world.LocalRandom` in YAML-driven logic.** YAML configuration itself does not run code; randomness comes from traits that call `world.SharedRandom`.

## Where to find more examples

The official mods are the definitive reference. Browse:

- `mods/ra/rules/defaults.yaml` — abstract actor patterns.
- `mods/ra/weapons/smallcaliber.yaml` — weapon patterns.
- `mods/ra/sequences/infantry.yaml` — sequence patterns.
- `mods/common/chrome/ingame.yaml` — UI patterns.

## Summary

This appendix collects the most common MiniYaml patterns you will encounter when writing or reading OpenRA rules: inheritance, trait instances, conditions, weapons, sequences, chrome widgets, and more. It is intended as a quick reference to complement the architecture chapters and the official mod rules.

## What to read next

- [Part 2.1 — MiniYaml Parser](../chapters/Part_02_Chapter_01_MiniYaml.md) for the parser rules that make these patterns work.
- [Part 2.4 — Rulesets, Actors, and Weapons](../chapters/Part_02_Chapter_04_Rules_Weapons.md) for the actor and weapon loading pipeline.
- [Part 1.1 — Entity-Component-System (ECS) and Actor Lifecycle](../chapters/Part_01_Chapter_01_ECS.md) for how the trait and instance-name patterns in YAML map to C# runtime behavior.
- [Part 6.3 — Virtual File System](../chapters/Part_06_Chapter_03_VFS.md) for how the `Package` and `Loader` patterns in `mod.yaml` mount asset sources.
- [Appendix E — Practical Modding Recipes](Appendix_E_Practical_Recipes.md) for ready-to-use YAML snippets that build on these patterns.
- [Appendix H — Asset Visual Reference](Appendix_H_Asset_Visual_Reference.md) for a categorical lookup of the asset types (sprites, audio, maps, chrome, etc.) behind these patterns.