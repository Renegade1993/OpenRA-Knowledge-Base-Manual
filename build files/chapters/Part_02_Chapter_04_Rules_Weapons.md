# Chapter 2.4 — Rulesets, Actors, and Weapons

## Purpose

OpenRA is a data-driven engine.  Rather than hard-coding units, buildings, weapons, sounds, and music, the engine loads each of these definitions from MiniYaml files and turns them into immutable, fast runtime objects.  The ruleset subsystem is responsible for that transformation.

A **[ruleset](../appendices/Appendix_A_Glossary.md)** is the complete set of definitions that describe what can exist in a game session:

* **[Actors](../appendices/Appendix_A_Glossary.md)** (`ActorInfo`) — every unit, building, decoration, projectile, crate, player, world, and system actor.  An `ActorInfo` is a named collection of `[TraitInfo](../appendices/Appendix_A_Glossary.md)` objects, each configured with [YAML](../appendices/Appendix_A_Glossary.md) fields.
* **[Weapons](../appendices/Appendix_A_Glossary.md)** (`WeaponInfo`) — every weapon, including its projectile, warheads, range, burst, reload, firing sounds, and target validation rules.
* **Voices** and **Notifications** (`SoundInfo`) — spoken unit acknowledgments and UI/game notifications.
* **Music** (`MusicInfo`) — the soundtrack selection for the session.
* **Model sequences** (`MiniYamlNode`) — voxel/model animation data used by the D2k/Tiberian Sun style isometric assets.
* **Terrain info** (`ITerrainInfo`) — the tileset-specific terrain definition for the map being played.

`Ruleset`, `ActorInfo`, and `WeaponInfo` exist so that the engine can resolve all of this data once per map/session, produce a deterministic snapshot of the game world, and then hand immutable references to the runtime ECS ([Actor/Trait system](../appendices/Appendix_A_Glossary.md)), AI, network order validation, audio, and the renderer.  The ruleset is the boundary between YAML mod content and the C# simulation.

## Learning Objectives


After studying this chapter, you should be able to:

1. Define a ruleset and list the seven categories of data it stores.
2. Explain how `ActorInfo` turns a YAML actor block into a collection of `TraitInfo` instances.
3. Describe how `WeaponInfo` combines range, reload, projectile, and warheads into a runtime object.
4. Use inheritance (`Inherits:`), instance naming (`@`), and trait dependencies (`Requires<>`, `NotBefore<>`) when writing or reading rules.
5. Trace the complete load path from `mod.yaml` manifest lists to `ModData.DefaultRules` and map-specific rulesets.
6. Implement `IRulesetLoaded` or `IRulesetLoaded<T>` to validate cross-references after loading.
7. Diagnose common ruleset errors such as missing `^` parents, duplicate trait instances, and broken `Requires` dependencies.

![Practical example: adding a custom weapon to a tank diagram](images/Part_02_Chapter_04_Rules_Weapons-end-to-end-worked-example-diagram-showing-the-inputs-interme-5fc6a2.svg)

## Practical Example: Adding a Custom Weapon to a Tank


Suppose you want to give the Red Alert light tank a new secondary weapon that fires a short-range missile.

1. **Define the weapon.** Add a new top-level weapon block in `mods/ra/weapons/missiles.yaml`:
   ```yaml
   LightTankMissile:
       Range: 4c0
       ReloadDelay: 80
       Burst: 2
       Projectile: Missile
           Speed: 298
       Warhead: SpreadDamage
           Spread: 128
           Damage: 2500
           Versus:
               None: 25
               Wood: 35
               Light: 100
               Heavy: 100
   ```
2. **Add the armament to the actor.** In `mods/ra/rules/vehicles.yaml`, locate the `1TNK` (light tank) actor and add a second armament instance:
   ```yaml
   1TNK:
       Inherits: ^Tank
       Inherits@GAIN: ^GainsExperience
       Inherits@AUTOTARGET: ^AutoTargetGroundAssaultMove
       Mobile:
           Speed: 128
       Armament@PRIMARY:
           Weapon: 25mm
       Armament@SECONDARY:
           Weapon: LightTankMissile
           LocalOffset: 0,0,0
       AttackFrontal:
       ...
   ```
3. **Load into `Ruleset`.** When the game starts, `Ruleset.LoadDefaults` calls `MergeOrDefault` for the `Weapons` manifest list. It creates a `WeaponInfo` named `LightTankMissile` from the YAML block, with `FieldLoader` populating `Range`, `ReloadDelay`, `Burst`, `Projectile`, and `Warheads`.
4. **Bind to `Armament`.** `ActorInfo` parses the `1TNK` block and creates two `Armament` trait instances: `Armament@PRIMARY` (weapon `25mm`) and `Armament@SECONDARY` (weapon `LightTankMissile`). The `@SECONDARY` suffix is stored in `TraitInfo.InstanceName`.
5. **Fire during combat.** When the tank's `AttackFrontal` trait decides to attack, it asks the relevant `Armament` to fire. `Armament` checks the weapon's range, reload timer, and target validity, then creates the `Missile` projectile from `IProjectileInfo.Create` and dispatches the `SpreadDamage` warhead on impact.
6. **Validate.** Run `./utility.sh ra --check-yaml` to verify that the weapon and actor references are valid and that `Requires`/`NotBefore` dependencies are satisfied.

This example shows how a single YAML change flows through the ruleset system into runtime combat behavior.

## Files

| File | Responsibility |
| :---- | :---- |
| `OpenRA.Game/GameRules/Ruleset.cs` | Loads, merges, and stores the complete set of actors, weapons, voices, notifications, music, model sequences, and terrain info. Fires `IRulesetLoaded` callbacks. |
| `OpenRA.Game/GameRules/ActorInfo.cs` | Parses a single actor block from YAML into a collection of `TraitInfo` instances. Resolves trait dependencies and build order. Filters abstract `^` actors. |
| `OpenRA.Game/GameRules/WeaponInfo.cs` | Parses a single weapon block from YAML into range, burst, reload, sounds, a projectile, and a list of warheads. Implements target validation and impact dispatch. |
| `OpenRA.Game/Primitives/ActorInfoDictionary.cs` | Read-only dictionary wrapper over `ActorInfo`s. Guarantees entries for `SystemActors` even if YAML does not define them. |
| `OpenRA.Game/Primitives/TypeDictionary.cs` | Stores `TraitInfo` instances indexed by runtime type, base types, and interfaces. Enables `TraitInfo<T>`, `TraitInfos<T>`, and fast lookup by trait interface. |
| `OpenRA.Game/Traits/TraitsInterfaces.cs` | Defines `TraitInfo`, `IRulesetLoaded`, `IRulesetLoaded<T>`, `Requires<>`, `NotBefore<>`, and `ILobbyCustomRulesIgnore`. |
| `OpenRA.Game/FieldLoader.cs` | Reflection-based YAML-to-C# loader. Parses primitive fields, arrays, dictionaries, and generic collections; supports `[FieldLoader.Require]` and `[FieldLoader.LoadUsing]`. |
| `OpenRA.Game/MiniYaml.cs` | YAML parsing, inheritance resolution (`Inherits:`), node removal (`-Node`), and multi-source merging (mod files + map overrides). |
| `OpenRA.Mods.Common/Traits/Armament.cs` | The trait that attaches a `WeaponInfo` to an actor and drives firing, reloading, modifiers, and muzzle effects. |
| `OpenRA.Mods.Common/Projectiles/Bullet.cs` | A common projectile implementation (straight-line/arc travel with sprite, shadow, trail, contrail, and bouncing). |
| `OpenRA.Mods.Common/Projectiles/InstantHit.cs` | Invisible direct-hit projectile used by many small arms and beams. |
| `OpenRA.Mods.Common/Warheads/Warhead.cs` | Abstract base for warheads; defines target relationships, valid/invalid target types, and `AirThreshold`. |
| `OpenRA.Mods.Common/Warheads/DamageWarhead.cs` | Adds raw damage, damage types, and armor `Versus` handling. |
| `OpenRA.Mods.Common/Warheads/SpreadDamageWarhead.cs` | Area-of-effect damage with falloff; implements `IRulesetLoaded<WeaponInfo>` to validate its range table. |
| `mods/ra/mod.yaml` | Manifest that lists the rules, weapons, voices, notifications, music, and model-sequence files for the Red Alert mod. |
| `mods/ra/rules/defaults.yaml` | Abstract `^` actors (`^Infantry`, `^Soldier`, `^Vehicle`, `^ExistsInWorld`, etc.) that are inherited by concrete units and structures. |
| `mods/ra/rules/infantry.yaml` | Concrete infantry actors such as `E1`, `E2`, `DOG`, `SPY`, `E6`. |
| `mods/ra/weapons/smallcaliber.yaml` | Concrete and abstract weapons (`M1Carbine`, `Vulcan`, `^HeavyMG`, `^LightMG`, `^AACannon`). |

![Architecture diagram](images/Part_02_Chapter_04_Rules_Weapons-architecture-diagram-showing-the-main-classes-interfaces-and-9161e6.svg)

## Architecture


The ruleset architecture is a thin layer of immutable runtime objects sitting on top of the YAML pipeline described in [Part 2.1 — MiniYaml and the Rules File Format](Part_02_Chapter_01_MiniYaml.md) and [Part 2.3 — FieldLoader and Type Conversions](Part_02_Chapter_03_FieldLoader.md).  The flow is: Manifest file lists -> `MiniYaml.Load/Merge` -> `MergeOrDefault<T>` -> dictionaries of `ActorInfo`, `WeaponInfo`, `SoundInfo`, `MusicInfo`, and model sequences -> `new Ruleset(...)` -> `IRulesetLoaded` callbacks -> `ModData.DefaultRules` / map-specific ruleset -> consumed by the Actor ECS, `Armament`, `AttackBase`, AI, audio, and world systems.

### Key classes and interfaces

* **`Ruleset`** — `OpenRA.Game/GameRules/Ruleset.cs`.  Holds seven read-only dictionaries/objects and runs the post-load callback phase.
* **`ActorInfo`** — `OpenRA.Game/GameRules/ActorInfo.cs`.  A named collection of `TraitInfo` plus a computed topological construction order.
* **`ActorInfoDictionary`** — `OpenRA.Game/Primitives/ActorInfoDictionary.cs`.  Wraps the dictionary and injects empty entries for `SystemActors`.
* **`TraitInfo`** / **`TraitInfo<T>`** — `OpenRA.Game/Traits/TraitsInterfaces.cs`.  Base class for every trait info; `InstanceName` is set by reflection when the YAML key contains `@`.
* **`TypeDictionary`** — `OpenRA.Game/Primitives/TypeDictionary.cs`.  Indexes trait info objects by concrete type, base types, and interfaces, enabling fast `TraitInfo<T>` and `TraitInfos<T>` lookups.
* **`WeaponInfo`** — `OpenRA.Game/GameRules/WeaponInfo.cs`.  Holds weapon fields plus `Projectile` (`IProjectileInfo`) and `Warheads` (`ImmutableArray<IWarhead>`), loaded by `FieldLoader.LoadUsing`.
* **`IProjectileInfo`** / **`IProjectile`** — `OpenRA.Game/GameRules/WeaponInfo.cs`.  `IProjectileInfo.Create(ProjectileArgs)` returns a runtime projectile effect.
* **`IWarhead`** — `OpenRA.Game/Traits/TraitsInterfaces.cs`.  Warheads implement `IsValidAgainst` and `DoImpact`.
* **`IRulesetLoaded`** / **`IRulesetLoaded<TInfo>`** — `OpenRA.Game/Traits/TraitsInterfaces.cs`.  Implemented by trait info and weapon/warhead classes for post-load cross-reference validation and derived state.
* **`Requires<T>`** / **`NotBefore<T>`** — `OpenRA.Game/Traits/TraitsInterfaces.cs`.  Generic marker interfaces declaring trait construction dependencies (required presence vs. required ordering).
* **`ILobbyCustomRulesIgnore`** — `OpenRA.Game/Traits/TraitsInterfaces.cs`.  Marker interface for trait info classes safe to override in map rules without flagging the map as "unsafe".

### Inheritance and instance naming

* **`Inherits:`** — Resolves a parent block and merges its children into the child block.
* **`Inherits@SOMETHING:`** — Multiple inheritance with a unique key, e.g. `Inherits@AUTOTARGET: ^AutoTargetGroundAssaultMove`.
* **`^` abstract actor prefix** — `ActorInfo.AbstractActorPrefix = '^'`.  `^` actors are filtered from the runtime dictionary but can be inherited.
* **`-TraitName:`** — Removes an inherited trait, e.g. `-AttackFrontal:` on the Dog.
* **`TraitName@INSTANCE:`** — Creates a second instance of the same trait info on one actor, e.g. `Armament@PRIMARY`, `WithInfantryBody@RUN`.  The instance name is stored in `TraitInfo.InstanceName`.

![Data flow  code path diagram](images/Part_02_Chapter_04_Rules_Weapons-sequence-flow-diagram-tracing-the-execution-path-from-trigge-035864.svg)

## Data Flow / Code Path


### 1. Loading the default ruleset (`Ruleset.LoadDefaults`)

`OpenRA.Game/GameRules/Ruleset.cs` build the default ruleset once per mod at startup.  It calls `MergeOrDefault` for each manifest list:

```csharp
var actors = MergeOrDefault("Manifest,Rules", fs, m.Rules, null, null,
    k => new ActorInfo(modData.ObjectCreator, k.Key.ToLowerInvariant(), k.Value),
    filterNode: n => n.Key.StartsWith(ActorInfo.AbstractActorPrefix));

var weapons = MergeOrDefault("Manifest,Weapons", fs, m.Weapons, null, null,
    k => new WeaponInfo(k.Value));

// voices, notifications, music, modelSequences constructed similarly

ruleset = new Ruleset(actors, weapons, voices, notifications, music, null, modelSequences);
```

The default ruleset is stored in `ModData.DefaultRules` and has no terrain tileset.

### 2. Binding a tileset (`Ruleset.LoadDefaultsForTileSet`)

`OpenRA.Game/GameRules/Ruleset.cs`:

```csharp
var dr = modData.DefaultRules;
var terrainInfo = modData.DefaultTerrainInfo[tileSet];
return new Ruleset(dr.Actors, dr.Weapons, dr.Voices, dr.Notifications, dr.Music, terrainInfo, dr.ModelSequences);
```

This reuses the immutable default dictionaries and only adds the tileset-specific terrain info.

### 3. Map-specific rules (`Ruleset.Load`)

`OpenRA.Game/GameRules/Ruleset.cs` are called when a map is selected.  They pass the default dictionaries into `MergeOrDefault` as the `defaults` argument and apply map overrides on top:

```csharp
var actors = MergeOrDefault("Rules", fileSystem, m.Rules, mapRules, dr.Actors,
    k => new ActorInfo(modData.ObjectCreator, k.Key.ToLowerInvariant(), k.Value),
    filterNode: n => n.Key.StartsWith(ActorInfo.AbstractActorPrefix));

var weapons = MergeOrDefault("Weapons", fileSystem, m.Weapons, mapWeapons, dr.Weapons,
    k => new WeaponInfo(k.Value));

ruleset = new Ruleset(actors, weapons, voices, notifications, music, terrainInfo, modelSequences);
```

### 4. `MergeOrDefault<T>`

`OpenRA.Game/GameRules/Ruleset.cs`:

```csharp
static IReadOnlyDictionary<string, T> MergeOrDefault<T>(string name,
    IReadOnlyFileSystem fileSystem, IEnumerable<string> files, MiniYaml additional,
    IReadOnlyDictionary<string, T> defaults, Func<MiniYamlNode, T> makeObject,
    Func<MiniYamlNode, bool> filterNode = null)
{
    if (additional == null && defaults != null)
        return defaults;

    IEnumerable<MiniYamlNode> yamlNodes = MiniYaml.Load(fileSystem, files, additional);

    if (filterNode != null)
        yamlNodes = yamlNodes.Where(k => !filterNode(k));

    return yamlNodes.ToDictionaryWithConflictLog(k => k.Key.ToLowerInvariant(), makeObject, "LoadFromManifest<" + name + ">");
}
```

The `additional == null && defaults != null` short-circuit returns the existing defaults dictionary unchanged when no map override exists, keeping mod-only games fast.  Otherwise `MiniYaml.Load` merges the manifest files with any map files and the override tree.

### 5. MiniYaml inheritance and merge

`OpenRA.Game/MiniYaml.cs` implement the core merge.  `MiniYaml.Merge` performs three stages:

1. **MergeSelfPartial** — merges duplicate keys within each source list.
2. **MergePartial** — merges all sources left-to-right, overriding values recursively.  `-Key` removals are preserved.
3. **ResolveInherits** — expands `Inherits:` and `Inherits@` parents, applies `-Key` removals, and detects inheritance cycles.

`ToDictionaryWithConflictLog` throws a `YamlException` when duplicate keys cannot be merged.

### 6. Actor parsing (`ActorInfo` constructor)

`OpenRA.Game/GameRules/ActorInfo.cs` iterate each child node of the actor, call `LoadTraitInfo`, and add the resulting `TraitInfo` to a `TypeDictionary`.  `LoadTraitInfo` splits the key on `ActorInfo.TraitInstanceSeparator`, appends `Info` to the trait name, instantiates the class via `ObjectCreator`, sets `InstanceName` by reflection, and loads fields via `FieldLoader.Load`:

```csharp
var traitInstance = traitName.Split(TraitInstanceSeparator);
var info = creator.CreateObject<TraitInfo>(traitInstance[0] + "Info");
if (traitInstance.Length > 1)
    info.GetType().GetField(nameof(info.InstanceName)).SetValue(info, traitInstance[1]);

FieldLoader.Load(info, my);
```

`LoadTraitInfo` returns `null` only when the linter is running and the trait name is unknown; in normal gameplay, a missing trait throws.

### 7. Weapon parsing (`WeaponInfo` constructor)

`OpenRA.Game/GameRules/WeaponInfo.cs`:

```csharp
public WeaponInfo(MiniYaml content)
{
    content = content.WithNodes(MiniYaml.Merge([content.Nodes]));
    FieldLoader.Load(this, content);
}

static object LoadProjectile(MiniYaml yaml)
{
    var proj = yaml.NodeWithKeyOrDefault("Projectile")?.Value;
    if (proj == null) return null;
    var ret = Game.CreateObject<IProjectileInfo>(proj.Value + "Info");
    FieldLoader.Load(ret, proj);
    return ret;
}

static object LoadWarheads(MiniYaml yaml)
{
    var retList = new List<IWarhead>();
    foreach (var node in yaml.Nodes.Where(n => n.Key.StartsWith("Warhead", StringComparison.Ordinal)))
    {
        var ret = Game.CreateObject<IWarhead>(node.Value.Value + "Warhead");
        FieldLoader.Load(ret, node.Value);
        retList.Add(ret);
    }

    return retList.ToImmutableArray();
}
```

The `Projectile` node value names the projectile class with `Info` appended.  Every child node starting with `Warhead` names a warhead class with `Warhead` appended.

### 8. `IRulesetLoaded` callbacks

`OpenRA.Game/GameRules/Ruleset.cs` fire post-load callbacks after the dictionaries are built.  It iterates every actor's `IRulesetLoaded` trait infos and every weapon's `IRulesetLoaded<WeaponInfo>` projectile and warheads.  Callbacks are the correct place to resolve cross-references (e.g. `ArmamentInfo` looks up `Weapon` in `rules.Weapons`), validate invariants (e.g. `HealthInfo` checks `HitShapeInfo`), and cache derived values (e.g. `SpreadDamageWarhead` computes `effectiveRange`).  Exceptions are wrapped with the actor or weapon name.

### 9. Weapon attachment at runtime

`OpenRA.Mods.Common/Traits/Armament.cs`.  `ArmamentInfo` declares `Requires<AttackBaseInfo>` and uses `[FieldLoader.Require]` on `Weapon`.  Its `RulesetLoaded` resolves the string reference into a `WeaponInfo`, validates `BurstDelays` and `ReloadDelay`, and caches `ModifiedRange` from range-modifier traits.  The runtime `Armament` trait then fires, reloads, and applies modifiers using the cached `WeaponInfo`.

![Configuration (yaml) diagram](images/Part_02_Chapter_04_Rules_Weapons-annotated-yaml-snippet-diagram-showing-the-key-fields-and-ho-6a1b98.svg)

## Configuration (YAML)


### Manifest entries

A mod's `mod.yaml` declares the file lists for the ruleset.  `mods/ra/mod.yaml` lists `Rules`, `Weapons`, `Voices`, `Notifications`, `Music`, and `ModelSequences` entries; the `Rules` and `Weapons` lists are the most important for modders.  Example:

```yaml
Rules:
    ra|rules/defaults.yaml
    ra|rules/infantry.yaml
    ra|rules/vehicles.yaml
    ra|rules/structures.yaml
    ...

Weapons:
    ra|weapons/smallcaliber.yaml
    ra|weapons/missiles.yaml
    ...
```

### Actor YAML syntax

A concrete actor block inherits from one or more abstract actors and then adds, overrides, or removes traits.

From `mods/ra/rules/infantry.yaml`, the `E1` (Rifle Infantry) actor:

```yaml
E1:
    Inherits: ^Soldier
    Inherits@AUTOTARGET: ^AutoTargetGroundAssaultMove
    Buildable:
        Queue: Infantry
        BuildAtProductionType: Soldier
        BuildPaletteOrder: 10
        Prerequisites: ~barracks, ~techlevel.infonly
    Valued:
        Cost: 100
    Health:
        HP: 5000
    Armament@PRIMARY:
        Weapon: M1Carbine
    Armament@GARRISONED:
        Name: garrisoned
        Weapon: Vulcan
    WithInfantryBody:
        DefaultAttackSequence: shoot
        RequiresCondition: !parachute
    WithInfantryBody@PARACHUTE:
        StandSequences: parachute
        RequiresCondition: parachute
```

Key points:

* `Inherits: ^Soldier` pulls in the entire `^Soldier` abstract block.
* `Inherits@AUTOTARGET: ^AutoTargetGroundAssaultMove` is a second inheritance line.  The `@AUTOTARGET` suffix is only a YAML key; it lets the same actor have multiple `Inherits` entries.
* `Armament@PRIMARY` and `Armament@GARRISONED` are two distinct instances of `ArmamentInfo`.  The instance names are stored in `TraitInfo.InstanceName`.
* `WithInfantryBody@PARACHUTE` is a second `WithInfantryBody` instance active only when the `parachute` condition is granted.

Removing inherited traits is done with a leading `-`; the `DOG` actor in `mods/ra/rules/infantry.yaml` removes inherited `AttackFrontal` and `TakeCover` with `-AttackFrontal:` and `-TakeCover:`.

### Weapon YAML syntax

Weapons are configured as a top-level block per weapon.  A common pattern is to define an abstract base weapon and inherit concrete weapons from it.

From `mods/ra/weapons/smallcaliber.yaml`, the abstract `^HeavyMG`:

```yaml
^HeavyMG:
    ReloadDelay: 35
    Range: 6c0
    Report: gun13.aud
    ValidTargets: Ground, Water, GroundActor, WaterActor
    Projectile: InstantHit
        Blockable: true
    Warhead@1Dam: SpreadDamage
        Spread: 128
        Damage: 2500
        ValidTargets: GroundActor, WaterActor
        Versus:
            None: 120
            Wood: 60
            Light: 72
            Heavy: 28
            Concrete: 28
        DamageTypes: Prone50Percent, TriggerProne, BulletDeath
    Warhead@2Eff: CreateEffect
        Explosions: piffs
        ValidTargets: Ground, GroundActor, Air, AirborneActor, WaterActor, Trees
    Warhead@3EffWater: CreateEffect
        Explosions: water_piffs
        ValidTargets: Water, Underwater
        InvalidTargets: Bridge
```

A concrete weapon such as `M1Carbine` inherits from `^LightMG` and overrides `ReloadDelay`, `Range`, `Report`, and individual warheads.

Key weapon fields:

* `ReloadDelay` — ticks between magazine reloads.
* `Burst` — shots per magazine.
* `BurstDelays` — ticks between shots in a burst; single value or `Burst - 1` entries.
* `Range` / `MinRange` — maximum and minimum firing range.
* `ValidTargets` / `InvalidTargets` — `BitSet<TargetableType>` controlling what the weapon can fire at.
* `CanTargetSelf` — whether the weapon can hit the firer.
* `Report` — sound played each time the weapon fires.
* `StartBurstReport` — sound played only on the first shot of a burst.
* `AfterFireSound` — sound played when the magazine reloads.
* `Projectile` — names the projectile class (e.g. `InstantHit`, `Bullet`, `Missile`).
* `Warhead@Name` — one or more warhead instances; each key must start with `Warhead`.

The `Projectile` block's child fields are loaded into the projectile's `*Info` class.  The `Warhead@Name` node's value is the warhead class name and its children are loaded into the warhead's `*Warhead` class.

## Interconnectivity

* **Depends on:**
  * **[Part 2.1 — MiniYaml and the Rules File Format](Part_02_Chapter_01_MiniYaml.md)** for parsing, inheritance, and merging.
  * **[Part 2.2 — Manifest, ModData, Ruleset, and RulesetCache](Part_02_Chapter_02_Manifest.md)** for `DefaultTerrainInfo` and the tileset-specific ruleset.
  * **[Part 2.3 — FieldLoader and Type Conversions](Part_02_Chapter_03_FieldLoader.md)** for converting YAML values into C# fields.
  * **[Part 3.1 — ModData, the Mod SDK, and the Manifest](Part_03_Chapter_01_Mod_SDK.md)** for the file lists, the `ObjectCreator`, and the `DefaultFileSystem`.
  * **[Part 5.1 — Audio Architecture](Part_05_Chapter_01_Audio_Architecture.md)** for `SoundInfo` and `MusicInfo`.

* **Used by:**
  * **[Part 1.1 — Entity-Component-System (ECS) and Actor Lifecycle](Part_01_Chapter_01_ECS.md)** because `ActorInfo` is the blueprint from which every `Actor` is instantiated.
  * **[Part 1.3 — World, OrderManager, and Orders](Part_01_Chapter_03_World_Orders.md)** because `IValidateOrder` and `IResolveOrder` traits are discovered from `ActorInfo`.
  * **[Part 4.3 — Widgets and Chrome](Part_04_Chapter_03_Widgets.md)** for production queues, tooltips, and palettes.
  * **[Part 5.1 — Audio Architecture](Part_05_Chapter_01_Audio_Architecture.md)** for voices and notifications.
  * **[Part 6.5 — Asset Loaders](Part_06_Chapter_05_Asset_Loaders.md)** for model sequences.
  * **[Part 8.1 — IBot and the AI Foundation](Part_08_Chapter_01_IBot.md)** because the AI queries the ruleset to know which units exist, what they cost, and what weapons they carry.
  * **[Part 9.1 — OrderManager and Lockstep Foundation](Part_09_Chapter_01_OrderManager.md)** because order validation and creation use the trait interfaces found in `ActorInfo`.

![Algorithms diagram](images/Part_02_Chapter_04_Rules_Weapons-algorithm-diagram-or-pseudocode-flowchart-for-the-non-trivia-5983ed.svg)

## Algorithms


### 1. Trait construction order (`TraitsInConstructOrder`)

`OpenRA.Game/GameRules/ActorInfo.cs`.  Every actor must create its runtime traits in a deterministic order that respects `Requires<T>` and `NotBefore<T>` dependencies.

Plain-language algorithm:

```
source = every TraitInfo in this actor, with:
    Type = its runtime type
    Dependencies = types from Requires<T> interfaces
    OptionalDependencies = types from NotBefore<T> interfaces

resolved = all traits with no dependencies and no optional dependencies
unresolved = all remaining traits

repeat:
    ready = every unresolved trait where:
        every dependency d is satisfied by a resolved trait, AND
        no unresolved trait also satisfies d, AND
        every optional dependency d is not satisfied by any unresolved trait
    add ready to resolved
    remove ready from unresolved
until ready is empty

if unresolved is not empty:
    throw a detailed YamlException listing missing and unresolved dependencies

cache and return resolved order
```

The key predicate `AreResolvable(a, b)` is `a.IsAssignableFrom(b)`.  This means a dependency on `HealthInfo` can be satisfied by any `HealthInfo` or subclass.  The loop is repeated until no more traits can be resolved; if any remain, the actor has an unsatisfiable or circular dependency graph.

### 2. MiniYaml merge (`MergeOrDefault` and `MiniYaml.Merge`)

Plain-language algorithm:

```
MergeOrDefault(name, files, mapOverrides, defaults, makeObject, filter):
    if mapOverrides is null and defaults is not null:
        return defaults                           // fast path

    yamlNodes = MiniYaml.Load(fileSystem, files, mapOverrides)
    if filter is not null:
        yamlNodes = yamlNodes where not filter(node)

    return yamlNodes.ToDictionaryWithConflictLog(
        key = node.Key.ToLowerInvariant(),
        value = makeObject(node),
        logName = "LoadFromManifest<" + name + ">")

MiniYaml.Load(files, mapOverrides):
    if mapOverrides.Value is a list of file paths:
        files = files + those map file paths
    parsed = read and parse each file
    return Merge(parsed)

MiniYaml.Merge(sources):
    for each source list:
        merge duplicate keys within the source (MergeSelfPartial)
    merge all sources left-to-right (MergePartial)
    build a dictionary keyed by top-level node name
    for each top-level node:
        recursively resolve Inherits: and Inherits@ parents
    return the resolved tree
```

Conflict log: `ToDictionaryWithConflictLog` and `IntoDictionaryWithConflictLog` are used at multiple stages.  They produce a `YamlException` if the same key appears twice and cannot be merged into a single entry.  The exception message includes the conflicting keys and their source locations.

### 3. Weapon target validation (`WeaponInfo.IsValidAgainst`)

`OpenRA.Game/GameRules/WeaponInfo.cs`.

```
IsValidAgainst(target, world, firedBy):
    if target is Actor:
        return IsValidAgainst(actor, firedBy)
    if target is FrozenActor:
        return IsValidAgainst(frozenActor, firedBy)
    if target is Terrain:
        altitude = distance above terrain at target position
        if altitude > AirThreshold:
            return IsValidTarget(Air)               // only air target type
        cell = map cell containing target position
        if cell not in map:
            return false
        return IsValidTarget(cell.TerrainInfo.TargetTypes)
    return false

IsValidAgainst(actor, firedBy):
    if not CanTargetSelf and actor == firedBy:
        return false
    return IsValidTarget(actor.GetEnabledTargetTypes())

IsValidTarget(targetTypes):
    return ValidTargets.Overlaps(targetTypes) and not InvalidTargets.Overlaps(targetTypes)
```

`ValidTargets` and `InvalidTargets` are `BitSet<TargetableType>`.  The weapon is valid against a target only if the target shares at least one valid target type and shares none of the invalid ones.  `InvalidTargets` overrides `ValidTargets`.  For terrain targets above the `AirThreshold`, the weapon ignores all terrain types and only checks whether `Air` is valid.

![Extension points diagram](images/Part_02_Chapter_04_Rules_Weapons-extension-hook-diagram-showing-the-interface-s-to-implement-b4a27b.svg)

## Extension Points


### 1. Adding new actor types

Create a new top-level YAML block in a rules file, inherit from an abstract actor such as `^Vehicle`, `^Soldier`, or `^Infantry`, and add or override traits.  No C# is required unless the new behavior needs a new trait.

### 2. Adding new weapons

Create a new top-level YAML block in a weapons file and define a `Projectile` and one or more `Warhead@` entries.  The node values name the C# class (`Bullet`, `SpreadDamage`, `CreateEffect`, etc.) with `Info` or `Warhead` appended during load.

### 3. Adding new projectiles and warheads

Implement a new `IProjectileInfo` class (and matching `IProjectile`) or derive from `Warhead` / `DamageWarhead` in a mod assembly, then reference them by name in YAML:

```yaml
Projectile: MyProjectile
    Speed: 200
Warhead@1My: MyWarhead
    SomeField: 42
```

### 4. Implementing `IRulesetLoaded<>`

Use this when a trait or weapon component needs to validate cross-references or compute derived values after the whole ruleset is built.  `HealthInfo` uses it to assert that an actor with `Health` also has `HitShapeInfo`; `SpreadDamageWarhead` uses `IRulesetLoaded<WeaponInfo>` to validate and cache its range/falloff table.

### 5. Adding custom trait dependencies

Declare `Requires<T>` when a trait cannot exist without another trait, and `NotBefore<T>` when it must be constructed after another trait if present:

```csharp
public class MyTraitInfo : TraitInfo, Requires<HealthInfo>, NotBefore<SomeOtherInfo>
{
    public override object Create(ActorInitializer init) { return new MyTrait(init, this); }
}
```

`Requires<T>` and `NotBefore<T>` are generic marker interfaces; `ActorInfo.PrerequisitesOf` and `ActorInfo.OptionalPrerequisitesOf` discover them via reflection.

![Common pitfalls  guardrails diagram](images/Part_02_Chapter_04_Rules_Weapons-checklist-infographic-style-diagram-summarizing-the-top-pitf-fb069e.svg)

## Common Pitfalls / Guardrails


### 1. Determinism and load frequency

Rulesets are loaded once per map/session.  `ModData.DefaultRules` is loaded at mod startup.  `Ruleset.Load` is called when a map is selected, and the resulting ruleset is stored on the `World` or `Map`.  Do not create or modify `ActorInfo` / `WeaponInfo` objects at runtime; they must be immutable for deterministic simulation and replay correctness.

### 2. Linter `LoadTraitInfo` null-return behavior

`ActorInfo.LoadTraitInfo` returns `null` only when the linter is running and a trait name cannot be resolved.  In normal gameplay, an unknown trait name throws from `ObjectCreator.CreateObject`.  Do not rely on `null` return for normal flow; treat it as a lint-only convenience.

### 3. Abstract actor prefix (`^`) filtering

`ActorInfo.AbstractActorPrefix = '^'`.  `Ruleset.LoadDefaults` and `Ruleset.Load` filter out any top-level actor node whose key starts with `^`.  This means abstract actors cannot be spawned directly, but they can be inherited.  If you accidentally name a concrete actor `^MyActor`, it will silently disappear from the ruleset.

### 4. `YamlException` wrapping

Both `ActorInfo` and `Ruleset` catch `YamlException` and rethrow with a prefix identifying the actor or weapon.  Always throw `YamlException` from `IRulesetLoaded` callbacks, not generic exceptions, so users get clean YAML error messages.

### 5. `ILobbyCustomRulesIgnore` and unsafe map rules

`OpenRA.Game/Traits/TraitsInterfaces.cs` defines the `ILobbyCustomRulesIgnore` marker interface.  `Ruleset.DefinesUnsafeCustomRules` flags maps with custom weapon, voice, notification, or sequence overrides as unsafe, and calls `AnyFlaggedTraits` to check every map trait override.  If a trait's `*Info` class does **not** implement `ILobbyCustomRulesIgnore`, the map is flagged as unsafe for multiplayer.  Any trait intended to be safely overridable by map authors must implement this marker.

### 6. Weapon validation

`ArmamentInfo.RulesetLoaded` validates that `BurstDelays` is either a single value or exactly `Burst - 1` entries when `Burst > 1`, and that `ReloadDelay` is greater than zero.

### 7. Warhead target relationships and armor

`Warhead.IsValidAgainst` checks `ValidRelationships` against the owner relationship.  `ValidRelationships: Ally` is useful for healing or buffing; `ValidRelationships: Enemy` is the default for damage.  `DamageWarhead.DamageVersus` requires an `Armor` trait whose type matches the `HitShape` `ArmorTypes`; otherwise the warhead defaults to 100% damage.

## Summary

This chapter explains how OpenRA turns MiniYaml actor and weapon definitions into immutable runtime rulesets.

After reading this chapter, you should be able to:

- Define a ruleset and list the seven categories of data it stores.
- Explain how `ActorInfo` turns a YAML actor block into a collection of `TraitInfo` instances.
- Describe how `WeaponInfo` combines range, reload, projectile, and warheads into a runtime object.
- Use inheritance (`Inherits:`), instance naming (`@`), and trait dependencies (`Requires<>`, `NotBefore<>`) when writing or reading rules.
- Trace the complete load path from `mod.yaml` manifest lists to `ModData.DefaultRules` and map-specific rulesets.
- Implement `IRulesetLoaded` or `IRulesetLoaded<T>` to validate cross-references after loading.
- Diagnose common ruleset errors such as missing `^` parents, duplicate trait instances, and broken `Requires` dependencies.

If any of the concepts above feel unclear, review the relevant section before continuing. For source files and further reading, see the References section.


## References

* Internal chapters:
  * [Part 1.1 — Entity-Component-System (ECS) and Actor Lifecycle](Part_01_Chapter_01_ECS.md)
  * [Part 1.3 — World, OrderManager, and Orders](Part_01_Chapter_03_World_Orders.md)
  * [Part 2.1 — MiniYaml and the Rules File Format](Part_02_Chapter_01_MiniYaml.md)
  * [Part 2.2 — Manifest, ModData, Ruleset, and RulesetCache](Part_02_Chapter_02_Manifest.md)
  * [Part 2.3 — FieldLoader and Type Conversions](Part_02_Chapter_03_FieldLoader.md)
  * [Part 3.1 — ModData, the Mod SDK, and the Manifest](Part_03_Chapter_01_Mod_SDK.md)
  * [Part 4.3 — Widgets and Chrome](Part_04_Chapter_03_Widgets.md)
  * [Part 5.1 — Audio Architecture](Part_05_Chapter_01_Audio_Architecture.md)
  * [Part 6.5 — Asset Loaders](Part_06_Chapter_05_Asset_Loaders.md)
  * [Part 8.1 — IBot and the AI Foundation](Part_08_Chapter_01_IBot.md)
  * [Part 9.1 — OrderManager and Lockstep Foundation](Part_09_Chapter_01_OrderManager.md)

* Source files:
  * `OpenRA.Game/GameRules/Ruleset.cs`
  * `OpenRA.Game/GameRules/ActorInfo.cs`
  * `OpenRA.Game/GameRules/WeaponInfo.cs`
  * `OpenRA.Game/Primitives/ActorInfoDictionary.cs`
  * `OpenRA.Game/Primitives/TypeDictionary.cs`
  * `OpenRA.Game/Traits/TraitsInterfaces.cs`
  * `OpenRA.Game/FieldLoader.cs`
  * `OpenRA.Game/MiniYaml.cs`
  * `OpenRA.Mods.Common/Traits/Armament.cs`
  * `OpenRA.Mods.Common/Traits/Health.cs`
  * `OpenRA.Mods.Common/Projectiles/Bullet.cs`
  * `OpenRA.Mods.Common/Projectiles/InstantHit.cs`
  * `OpenRA.Mods.Common/Warheads/Warhead.cs`
  * `OpenRA.Mods.Common/Warheads/DamageWarhead.cs`
  * `OpenRA.Mods.Common/Warheads/SpreadDamageWarhead.cs`
  * `mods/ra/mod.yaml`
  * `mods/ra/rules/defaults.yaml`
  * `mods/ra/rules/infantry.yaml`
  * `mods/ra/weapons/smallcaliber.yaml`

* Official documentation:
  * OpenRA modding wiki: https://wiki.openra.net/
  * GitHub repository: https://github.com/OpenRA/OpenRA



### External resources

- [OpenRA traits reference](https://docs.openra.net/en/release/traits/)
- [OpenRA weapons reference](https://docs.openra.net/en/release/weapons/)
## What to read next

- Now that you know how `ActorInfo` and `TraitInfo` are built from YAML, read [Part 1.1 — Entity-Component-System (ECS) and Actor Lifecycle](Part_01_Chapter_01_ECS.md) to learn how the engine turns those static definitions into live actors and traits.
- Now that you understand how `WeaponInfo`, projectiles, and warheads are loaded, read [Part 1.6 — Combat and Damage Resolution](Part_01_Chapter_06_Combat_Damage.md) to see how they actually fire and resolve damage in the simulation.
- If you want to apply these rules to a real mod, read [Part 3.1 — ModData, the Mod SDK, and the Manifest](Part_03_Chapter_01_Mod_SDK.md) to learn how the manifest, `ModData`, and the SDK bootstrap create the environment in which the ruleset is loaded.