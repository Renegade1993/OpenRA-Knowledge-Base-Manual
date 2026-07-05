# Chapter 1.6 — Combat and Damage Resolution

## Purpose

This chapter traces the path from **"I want to attack that"** to **"the [target](../appendices/Appendix_A_Glossary.md)'s HP is reduced"** in OpenRA. It ties together the ECS [actor](../appendices/Appendix_A_Glossary.md) model from [Part 1.1 — Entity-Component-System (ECS) and Actor Lifecycle](Part_01_Chapter_01_ECS.md), the ruleset/weapon definitions from [Part 2.4 — Rulesets, Actors, and Weapons](Part_02_Chapter_04_Rules_Weapons.md), and the activity/order system from [Part 1.2 — Activities and the Game Loop](Part_01_Chapter_02_Activities.md) and [Part 1.3 — World, OrderManager, and Orders](Part_01_Chapter_03_World_Orders.md).

Combat internals are deliberately split across many small, single-purpose classes:

- `AttackBase` decides *when* and *what* to attack.
- `Armament` turns a weapon definition into a fired projectile.
- `WeaponInfo` owns the projectile and warheads.
- `IProjectile` implementations move the shot through the [world](../appendices/Appendix_A_Glossary.md).
- `IWarhead` implementations apply effects on impact.
- `Health` and `Armor` resolve the final numeric [damage](../appendices/Appendix_A_Glossary.md).

The goal is to show how those pieces cooperate without ever hard-coding a specific unit in the engine.

## Learning Objectives


After studying this chapter, you should be able to:

1. Trace a complete attack from an order through `AttackBase`, `Armament`, projectile creation, `Weapon.Impact`, warhead resolution, and `Health.InflictDamage`.
2. Explain the difference between weapon-level validation (`WeaponInfo.ValidTargets` / `InvalidTargets`) and warhead-level validation (`Warhead.ValidTargets` / `ValidRelationships`).
3. Describe how `DamageWarhead` combines firepower modifiers, armor `Versus` values, and `DamageTypes` into a final `Damage` instance.
4. Identify the role of `HitShape` in targeting and area-of-effect falloff calculations.
5. Add a new projectile, warhead, or damage modifier using the correct extension interfaces.
6. Diagnose common combat bugs such as "no damage dealt," "weapon won't fire," and "armor type is ignored."

![Practical example: a 120 mm shell versus a heavy tank diagram](images/Part_01_Chapter_06_Combat_Damage-end-to-end-worked-example-diagram-showing-the-inputs-interme-5fc6a2.svg)

## Practical Example: A 120 mm Shell versus a Heavy Tank


Imagine a tank firing a single shell at a heavy tank.

**Weapon definition**

```yaml
120mm:
    Range: 4c0
    ReloadDelay: 80
    ValidTargets: Ground, Water, GroundActor, WaterActor
    Projectile: Bullet
        Speed: 384
        Inaccuracy: 0
    Warhead@1Dam: SpreadDamage
        Spread: 128
        Damage: 4000
        ValidTargets: GroundActor, WaterActor
        Versus:
            None: 100
            Light: 60
            Heavy: 100
            Concrete: 30
        DamageTypes: ExplosionDeath
    Warhead@2Eff: CreateEffect
        Explosions: explosion
        ValidTargets: Ground, GroundActor, Water, WaterActor
```

**Target definition**

```yaml
HTNK:
    Inherits: ^Vehicle
    Health:
        HP: 50000
    Armor:
        Type: Heavy
    HitShape:
        Type: Circle
        Radius: 512
    Targetable:
        TargetTypes: GroundActor
```

**What happens at runtime**

1. The player issues an **Attack** [order](../appendices/Appendix_A_Glossary.md). `AttackBase` resolves it and starts an attack [activity](../appendices/Appendix_A_Glossary.md).
2. `AttackBase.DoAttack` finds the `Armament` whose `Name` matches the weapon slot.
3. `Armament.CheckFire` checks range, reload, target validity, and facing/turret alignment, then calls `FireBarrel`.
4. `FireBarrel` builds a `ProjectileArgs` and creates a `Bullet` via `BulletInfo.Create`.
5. The `Bullet` travels one tick at a time. When it reaches the target position, it builds a `WarheadArgs` and calls `WeaponInfo.Impact`.
6. `WeaponInfo.Impact` iterates its warheads. `Warhead@1Dam` is a `SpreadDamageWarhead`, so it runs `SpreadDamageWarhead.DoImpact`.
7. The warhead searches actors in the outer `Spread` radius, finds `HTNK`, validates target type and relationship, and selects the nearest `HitShape`.
8. `DamageVersus` sees the `Armor.Type: Heavy` and the warhead's `Versus: Heavy: 100`, so no armor reduction applies.
9. `DamageWarhead.InflictDamage` builds a `Damage` instance with `Value = 4000` and `DamageTypes = ExplosionDeath`.
10. `Actor.InflictDamage` forwards the call to `Health.InflictDamage`, which applies any `IDamageModifier` traits, clamps HP to `[0, MaxHP]`, and fires `INotifyDamage` / `INotifyDamageStateChanged` callbacks. If HP reaches 0, `INotifyKilled` callbacks run and the actor is disposed.

The final HP reduction is `50000 -> 46000` (assuming no external damage modifiers). The same pipeline is used for machine-gun bullets, missiles, explosions, and even bridge demolition.

## Files

| File | Responsibility |
| :---- | :---- |
| `OpenRA.Game/GameRules/WeaponInfo.cs` | Parses a weapon from YAML into range, reload, burst, projectile, and warheads. Implements `IsValidAgainst` target validation and `Impact` dispatch. |
| `OpenRA.Game/GameRules/DamageTypes.cs` | **Does not exist.** The `DamageType` type tag lives in `OpenRA.Game/Traits/TraitsInterfaces.cs` as a sealed class used by `BitSet<DamageType>`. |
| `OpenRA.Game/Traits/TraitsInterfaces.cs` | Defines `IHealth`, `IHealthInfo`, `DamageType`, `Damage`, `AttackInfo`, and notification interfaces used during combat. |
| `OpenRA.Game/Actor.cs` | Provides the `InflictDamage` and `Kill` convenience wrappers that forward to the cached `IHealth` trait. |
| `OpenRA.Mods.Common/Traits/Armament.cs` | Attaches a weapon to an actor, handles reload/burst timing, muzzle offsets, and creates projectiles via `IProjectileInfo.Create`. |
| `OpenRA.Mods.Common/Traits/Attack/AttackBase.cs` | Abstract base for attack logic: order resolution, target validity, and driving attached armaments. |
| `OpenRA.Mods.Common/Traits/Attack/AttackFrontal.cs` | Requires the actor to face the target before firing. |
| `OpenRA.Mods.Common/Traits/Attack/AttackTurreted.cs` | Requires a turret to align before `AttackBase` fires. |
| `OpenRA.Mods.Common/Traits/Health.cs` | Stores HP, applies damage modifiers, clamps HP, and dispatches damage/kill notifications. |
| `OpenRA.Mods.Common/Traits/Armor.cs` | A simple type-tag trait used by damage warheads to select `Versus` modifiers. |
| `OpenRA.Mods.Common/Traits/HitShape.cs` | Defines the actor's physical shape, targetable positions, and which armor types apply to that shape. |
| `OpenRA.Mods.Common/Traits/Buildings/Bridge.cs` | Example of a destructible actor with `Health` that changes terrain templates on death. |
| `OpenRA.Mods.Common/Projectiles/Bullet.cs` | Straight-line or arcing projectile with optional bounce, trail, and contrail. |
| `OpenRA.Mods.Common/Projectiles/Missile.cs` | Homing missile with fuel, turn rates, and jamming support. |
| `OpenRA.Mods.Common/Projectiles/InstantHit.cs` | Direct, invisible projectile used by beams and small-arms. |
| `OpenRA.Mods.Common/Warheads/Warhead.cs` | Base class for warheads: target validation, delay support, and `DoImpact` hook. |
| `OpenRA.Mods.Common/Warheads/DamageWarhead.cs` | Base class for warheads that deal HP damage; applies `Versus` and `DamageModifiers`. |
| `OpenRA.Mods.Common/Warheads/SpreadDamageWarhead.cs` | Area-of-effect damage with distance falloff and multiple damage-calculation modes. |
| `OpenRA.Mods.Common/Warheads/CreateEffectWarhead.cs` | Spawns explosion sprite and sound effects on impact. |
| `OpenRA.Mods.Common/Warheads/FireClusterWarhead.cs` | Fires a secondary weapon from the impact point using a footprint pattern. |

![Architecture diagram](images/Part_01_Chapter_06_Combat_Damage-architecture-diagram-showing-the-main-classes-interfaces-and-9161e6.svg)

## Architecture


### The combat pipeline

![The combat pipeline](images/Part_01_Chapter_06_Combat_Damage-The_combat_pipeline.svg)
### Key classes and interfaces

- **`WeaponInfo`** — The immutable runtime definition of a weapon. It stores one `IProjectileInfo` and an ordered list of `IWarhead`s. Its `Impact` method is the entry point for warhead application.
- **`ProjectileArgs`** and **`WarheadArgs`** — Lightweight data bags that carry the source actor, target, muzzle facing, and accumulated damage modifiers from the armament to the projectile and from the projectile to the warheads.
- **`IProjectile` / `IProjectileInfo`** — Every projectile must implement `IProjectileInfo.Create` to produce a projectile instance, and `IProjectile` to receive per-tick `Tick` and `Render` calls.
- **`IWarhead`** — Implemented by all warheads. The base `Warhead` class provides target validation; derived classes implement `DoImpact`.
- **`AttackBase`** — An abstract ECS trait. It owns the **attack order**, the **target-line cursor**, and the loop that asks each `Armament` to fire. Concrete variants (`AttackFrontal`, `AttackTurreted`, `AttackFollow`) only change *when* the actor is considered ready to fire.
- **`Armament`** — The bridge between an actor and a weapon. It is responsible for reload timing, muzzle position, recoil, and notifying `INotifyAttack` listeners.
- **`Health`** / **`IHealth`** — The only place where an actor's HP is reduced. It also dispatches the entire damage notification graph.
- **`Armor`** — Has no behavior of its own. It is a typed marker queried by `DamageWarhead.DamageVersus`.
- **`HitShape`** — Provides the physical shape and targetable positions for targeting, falloff, and armor-type scoping.

### Why the pipeline is split this way

- **Reusability**: The same `WeaponInfo` can be mounted on infantry, vehicles, or turrets via different `Armament`/`AttackBase` combinations.
- **Data separation**: YAML decides *what* the weapon does; C# decides *how* to do it. No unit-specific code lives in the engine.
- **Determinism**: All randomness (inaccuracy, falloff scatter, effect selection) uses the shared world RNG or the local RNG consistently, which is important for replay and network sync.

![Data flow  code path diagram](images/Part_01_Chapter_06_Combat_Damage-sequence-flow-diagram-tracing-the-execution-path-from-trigge-035864.svg)

## Data Flow / Code Path


The following is the complete flow for a normal ranged attack.

### 1. Order and attack activity

The player issues an `Attack` order. `AttackBase` implements `IResolveOrder` and `IIssueOrder`, so it creates an `Order` with the target. In `AttackBase.ResolveOrder`, the order is converted into an attack activity by calling `GetAttackActivity`, which is overridden by each attack type (e.g., `AttackFrontal` returns an `Attack` activity). The activity then runs each tick and repeatedly calls `AttackBase.DoAttack` when the target is reachable.

### 2. `AttackBase` chooses an armament

`DoAttack` first checks `CanAttack`, which verifies:

- The actor is in the world.
- The trait is not paused or disabled.
- The target is still valid for the attacker.
- At least one attached armament has a valid weapon (via `HasAnyValidWeapons`).
- The actor can interact with the ground layer if it is mobile.

It then loops over its `Armaments` and calls `Armament.CheckFire` for each.

### 3. `Armament` validates and fires

`Armament.CheckFire` runs `CanFire`, which checks:

- `FireDelay` / reload state (`IsReloading`).
- Turret alignment (`Turreted.HasAchievedDesiredFacing`).
- Range (`MaxRange()` and `Weapon.MinRange`).
- Weapon target validity (`WeaponInfo.IsValidAgainst`).

If everything passes, it constructs a `ProjectileArgs` containing:

- `Weapon` — the `WeaponInfo` from the armament.
- `DamageModifiers`, `InaccuracyModifiers`, `RangeModifiers` — arrays of percentages collected from traits such as `IFirepowerModifier`, `IInaccuracyModifier`, and `IRangeModifier`.
- `Source`, `CurrentSource`, `Facing`, `CurrentMuzzleFacing` — derived from the muzzle position and orientation.
- `PassiveTarget` — the aim point computed from the target's positions, burst offsets, and `TargetActorCenter`.
- `GuidedTarget` — the original `Target` for homing missiles.

`FireBarrel` schedules the actual projectile creation through `ScheduleDelayedAction` so that `FireDelay` and burst timing are honored. When the delay expires, `IProjectileInfo.Create` is called and the projectile is added to the world.

### 4. The projectile travels

Different projectiles behave differently:

- **`InstantHit`** — In its first `Tick`, it checks blocking actors if `Blockable` is true, builds a `WarheadArgs`, calls `WeaponInfo.Impact`, and removes itself.
- **`Bullet`** — Travels in a straight line or arc. It applies inaccuracy on creation, advances position each tick, supports bouncing, and calls `WeaponInfo.Impact` when its flight length is reached or it collides.
- **`Missile`** — Enters a homing state, updates velocity toward the guided target, and explodes when within `CloseEnough` distance or when it runs out of fuel.

All of them end with the same call: `args.Weapon.Impact(target, warheadArgs)`.

### 5. `WeaponInfo.Impact` dispatches warheads

```
foreach warhead in WeaponInfo.Warheads
    if warhead.Delay > 0
        schedule DelayedImpact
    else
        warhead.DoImpact(target, args)
```

Delayed warheads are wrapped in a `DelayedImpact` effect that calls `DoImpact` after the configured number of ticks. This is how time-delayed explosions work.

### 6. Warhead applies its effect

Every warhead inherits `Warhead.IsValidAgainst`, which checks:

- `AffectsParent` — can the weapon hit the attacker?
- `ValidRelationships` — is the target an ally, neutral, or enemy?
- `ValidTargets` / `InvalidTargets` — does the target's `BitSet<TargetableType>` overlap correctly?

Damage-dealing warheads (`DamageWarhead`) add an extra check: the target must have an `IHealthInfo` and an active `HitShape`.

For a single actor target, `DamageWarhead.DoImpact` finds the closest active `HitShape` and calls `InflictDamage(victim, firedBy, shape, args)`.

For a position target, `SpreadDamageWarhead.DoImpact` scans all actors within the outer radius, computes falloff distance from each actor's nearest `HitShape`, and calls `InflictDamage` per actor with a `DamageModifiers` array that includes the falloff percentage.

### 7. `DamageWarhead` calculates final damage

`DamageVersus` selects the armor values that apply:

```
for each enabled Armor trait on the victim
    if Versus contains the armor type
    and (HitShape has no ArmorTypes or ArmorTypes contains the armor type)
        include Versus[armor type]

final armor modifier = ApplyPercentageModifiers(100, selected values)
```

`InflictDamage` then combines firepower modifiers and armor modifiers:

```
damage = ApplyPercentageModifiers(Damage, DamageModifiers + DamageVersus)
```

and constructs `new Damage(damage, DamageTypes)`.

### 8. `Health` applies the result

`Actor.InflictDamage` simply calls `Health.InflictDamage` unless the actor is already disposed or has no health. `Health.InflictDamage` does the following:

1. If already dead, ignore the hit (overkill protection).
2. If `ignoreModifiers` is false and the damage is positive, apply every `IDamageModifier` on the actor and on the owning player's `PlayerActor`.
3. Subtract the final value from `HP` and clamp to `[0, MaxHP]`.
4. Build an `AttackInfo` and notify `INotifyDamage` and `INotifyDamageStateChanged` listeners.
5. If the attacker is alive and `NotifyAppliedDamage` is enabled, notify `INotifyAppliedDamage` listeners on the attacker.
6. If `HP` is now 0, notify `INotifyKilled` listeners and dispose the actor if `RemoveOnDeath` is true.

### 9. Death and side effects

`Bridge` is a useful example of a non-unit that uses the same pipeline. It has `Health`, reacts to `INotifyDamageStateChanged` in `Bridge.UpdateState`, and can call `Actor.Kill` on units standing on it when it collapses. `Actor.Kill` bypasses normal modifiers and inflicts exactly `MaxHP` damage with the given `DamageTypes`.

![Configuration (yaml) diagram](images/Part_01_Chapter_06_Combat_Damage-annotated-yaml-snippet-diagram-showing-the-key-fields-and-ho-6a1b98.svg)

## Configuration (YAML)


### Weapon-level keys

| YAML key | C# field | Meaning |
| :---- | :---- | :---- |
| `Range` | `WeaponInfo.Range` | Maximum firing distance. |
| `MinRange` | `WeaponInfo.MinRange` | Minimum firing distance (used by `Armament.CanFire`). |
| `ReloadDelay` | `WeaponInfo.ReloadDelay` | Ticks between magazines. |
| `Burst` | `WeaponInfo.Burst` | Shots per magazine. |
| `BurstDelays` | `WeaponInfo.BurstDelays` | Ticks between shots in a burst. |
| `ValidTargets` | `WeaponInfo.ValidTargets` | BitSet of targetable types the weapon can aim at. |
| `InvalidTargets` | `WeaponInfo.InvalidTargets` | Overrides `ValidTargets`. |
| `TargetActorCenter` | `WeaponInfo.TargetActorCenter` | If true, aim at the actor's center instead of closest targetable position. |
| `Projectile` | `WeaponInfo.Projectile` | A nested `IProjectileInfo` block (e.g., `Bullet`, `Missile`, `InstantHit`). |
| `Warhead@Name` | `WeaponInfo.Warheads` | One or more warhead blocks. The suffix (`@1Dam`) is just for readability and YAML merging. |

### Projectile keys

- `Bullet` — `Speed`, `Inaccuracy`, `LaunchAngle`, `BounceCount`, `Blockable`, `Width`, `ContrailLength`, `Shadow`.
- `Missile` — `Speed`, `Acceleration`, `HorizontalRateOfTurn`, `VerticalRateOfTurn`, `RangeLimit`, `CloseEnough`, `Jammable`, `TrailImage`.
- `InstantHit` — `Inaccuracy`, `Blockable`, `Width`.

### Warhead keys (damage)

| YAML key | C# field | Meaning |
| :---- | :---- | :---- |
| `Spread` | `SpreadDamageWarhead.Spread` | Distance between falloff steps. |
| `Falloff` | `SpreadDamageWarhead.Falloff` | Damage percentage at each step. Defaults to `100, 37, 14, 5, 0`. |
| `Damage` | `DamageWarhead.Damage` | Base damage before modifiers. |
| `Versus` | `DamageWarhead.Versus` | Dictionary of `Armor.Type` to percentage. |
| `DamageTypes` | `DamageWarhead.DamageTypes` | BitSet of tags such as `ExplosionDeath`, `BulletDeath`, `FireDeath`. |
| `ValidTargets` | `Warhead.ValidTargets` | Targetable types this warhead can affect. |
| `ValidRelationships` | `Warhead.ValidRelationships` | `Enemy`, `Neutral`, `Ally`, or combinations. |
| `AffectsParent` | `Warhead.AffectsParent` | Can the warhead hit the attacker? |
| `Delay` | `Warhead.Delay` | Ticks before the warhead applies. |

### Armor and target type keys

```yaml
SomeUnit:
    Health:
        HP: 10000
    Armor:
        Type: Light
    HitShape:
        Type: Circle
        Radius: 256
        ArmorTypes: Light    # optional: only these armors apply to this shape
    Targetable:
        TargetTypes: GroundActor
```

- `Armor.Type` is an arbitrary string. It only matters if a warhead has a matching `Versus` entry.
- `HitShape.ArmorTypes` is optional. If specified, only those armor types are considered by `DamageVersus` for hits against this shape.
- `DamageTypes` are arbitrary string tags. Other traits (e.g., death animations, veterancy, crate effects) inspect them via `INotifyKilled` or `INotifyDamage`.

## Interconnectivity

### Depends on

- **[Part 1.1 — Entity-Component-System (ECS) and Actor Lifecycle](Part_01_Chapter_01_ECS.md)** — All combat classes are traits attached to actors. `Armament`, `AttackBase`, `Health`, and `Armor` are created from `TraitInfo` and queried via `Trait`, `TraitOrDefault`, and `TraitsImplementing`.
- **[Part 1.2 — Activities and the Game Loop](Part_01_Chapter_02_Activities.md)** — `AttackBase` returns an activity (`Attack`, `AttackFollow`) that manages movement and firing timing.
- **[Part 1.3 — World, OrderManager, and Orders](Part_01_Chapter_03_World_Orders.md)** — Attack orders are issued, queued, and resolved through the world order system before reaching `AttackBase`.
- **[Part 1.5 — Pathfinding and Movement](Part_01_Chapter_05_Pathfinding_Movement.md)** — `AttackMove` and `AttackFollow` rely on pathfinding to bring the attacker into range and to re-acquire targets.
- **[Part 2.4 — Rulesets, Actors, and Weapons](Part_02_Chapter_04_Rules_Weapons.md)** — `WeaponInfo`, `ArmamentInfo`, and `ActorInfo` are built from YAML by the ruleset loader. `IRulesetLoaded` validates weapon references and warhead ranges.
- **[Part 8.3 — Bot Squads and Combat Heuristics](Part_08_Chapter_03_Squads.md)** — AI squad modules issue attack orders and target selection decisions that feed into this same pipeline.

### Used by

- AI bot modules and [Part 6.1 — Lua Scripting and Eluant](Part_06_Chapter_01_Lua_Eluant.md) — trigger attacks, check `IsDead`, and react to damage states.
- [Part 5.1 — Audio Architecture](Part_05_Chapter_01_Audio_Architecture.md) — plays `Report`, `StartBurstReport`, and impact sounds.
- Renderer — muzzle flashes, projectile sprites, explosion effects, and debug overlays (`WarheadDebugOverlay`).
- Score/statistics traits — listen to `INotifyKilled` and `INotifyAppliedDamage`.

![Algorithms diagram](images/Part_01_Chapter_06_Combat_Damage-algorithm-diagram-or-pseudocode-flowchart-for-the-non-trivia-5983ed.svg)

## Algorithms


### Damage modifier composition

OpenRA stores modifiers as integer percentages (e.g., `50` means half damage, `200` means double). The helper `Util.ApplyPercentageModifiers` multiplies them together in sequence:

```
result = baseValue
for each modifier in modifiers
    result = result * modifier / 100
```

`DamageModifiers` are collected from `IFirepowerModifier` on the attacker. `Armor` values come from `Versus`. `SpreadDamageWarhead` also appends a falloff percentage. The order is important only in that all percentages are multiplicative; the final result is the same regardless of sequence.

### Armor selection (`DamageVersus`)

```
selected = empty list
foreach Armor a on victim (not disabled)
    if a.Type is in Versus
        and (HitShape.ArmorTypes is empty or HitShape.ArmorTypes contains a.Type)
            selected.Add(Versus[a.Type])

if selected is empty
    return 100
else
    return ApplyPercentageModifiers(100, selected)
```

### Area-of-effect falloff

`SpreadDamageWarhead.GetDamageFalloff` walks the `effectiveRange` array built from `Spread` or `Range`:

```
inner = 0
for i = 1 to effectiveRange.Length - 1
    outer = effectiveRange[i]
    if distance < outer
        return Lerp(Falloff[i-1], Falloff[i], distance - inner, outer - inner)
    inner = outer
return 0
```

`int2.Lerp` is a linear interpolation clamped to the range. This is why units at the edge of an explosion take far less damage.

### Target validity

Both `WeaponInfo` and `Warhead` use the same pattern:

```
isValid = ValidTargets.Overlaps(targetTypes) && !InvalidTargets.Overlaps(targetTypes)
```

`BitSet<TargetableType>` makes this a fast bit-mask operation.

![Extension points diagram](images/Part_01_Chapter_06_Combat_Damage-extension-hook-diagram-showing-the-interface-s-to-implement-b4a27b.svg)

## Extension Points


1. **New projectile** — Implement `IProjectileInfo` and `IProjectile`. Register the class in the mod assembly; YAML then uses `Projectile: MyProjectile`. Implement `ISync` if the projectile needs to participate in network sync.
2. **New warhead** — Inherit `Warhead` (or `DamageWarhead` for HP damage). Implement `IRulesetLoaded<WeaponInfo>` to validate cross-references. YAML uses `Warhead@Name: MyWarhead`.
3. **New attack behavior** — Inherit `AttackBase` and override `CanAttack` and `GetAttackActivity`. Use `Requires<T>` in the `*Info` class to demand prerequisites such as `IFacingInfo` or `TurretedInfo`.
4. **Damage modifiers** — Implement `IDamageModifier` on the victim or on the `PlayerActor` to reduce or increase incoming damage. Implement `IFirepowerModifier` on the attacker to increase outgoing damage. Implement `IRangeModifier` or `IInaccuracyModifier` to change weapon range or projectile spread.
5. **Custom armor behavior** — The `Armor` trait itself is just a tag, but a custom `IDamageModifier` can read `DamageTypes` or `Armor.Type` to implement special rules (e.g., directional armor, shields).
6. **Damage/death notifications** — Implement `INotifyDamage`, `INotifyDamageStateChanged`, `INotifyKilled`, or `INotifyAppliedDamage` to react to combat events (veterancy, score, death animation, etc.).
7. **Combat debug overlay** — The engine can draw `Warhead` impact ranges and shapes via `WarheadDebugOverlay` when the `DebugVisualizations.CombatGeometry` flag is enabled.

![Common pitfalls  guardrails diagram](images/Part_01_Chapter_06_Combat_Damage-checklist-infographic-style-diagram-summarizing-the-top-pitf-fb069e.svg)

## Common Pitfalls / Guardrails


- **No `DamageTypes.cs` file.** The `DamageType` tag is defined in `OpenRA.Game/Traits/TraitsInterfaces.cs`. Damage type strings are arbitrary and only meaningful to traits that consume them.
- **Health requires a `HitShape`.** `HealthInfo.RulesetLoaded` throws if the actor has no `HitShapeInfo`. Without a shape, the actor cannot be targeted or damaged by warheads.
- **Armor strings must match exactly.** If a warhead's `Versus` has `Heavy` but the actor's `Armor.Type` is `Hevy` (typo), the default 100% modifier is used silently.
- **Weapon `ValidTargets` vs. warhead `ValidTargets`.** The weapon controls whether the cursor/activity can target something. The warhead controls what actually happens on impact. It is common to have a weapon valid against `Ground` and a damage warhead valid only against `GroundActor`.
- **Damage modifiers apply only to positive damage.** `Health.InflictDamage` skips `IDamageModifier` when `damage.Value <= 0` or when `ignoreModifiers` is true. This is why healing or self-damage can be made unmodified.
- **Delayed warheads can hit disposed actors.** If the target is destroyed before a delayed warhead fires, the warhead should re-validate the target in `DoImpact`. The built-in damage warheads already do this.
- **`Actor.InflictDamage` is not the final authority.** The `Actor` wrapper simply forwards to `Health`. For special logic, call `IHealth.InflictDamage` directly or use `Actor.Kill`.
- **`InstantHit` is not free.** It still runs world queries for blocking actors when `Blockable` is true, which can be expensive with many shots.
- **Projectile randomness must be deterministic.** Use `World.SharedRandom` for gameplay-affecting randomness (inaccuracy, missile jitter) and `World.LocalRandom` for purely visual effects (explosion sprite selection, sound choice). This preserves replay/sync.
- **Do not mutate `WeaponInfo` at runtime.** `WeaponInfo` objects are shared across all actors. Runtime state belongs in the projectile, warhead args, or actor traits.
- **Bursts and `BurstDelays` length.** If you supply more than one `BurstDelays` value, the count must equal `Burst - 1`. `ArmamentInfo.RulesetLoaded` validates this.
- **ReloadDelay must be > 0.** `ArmamentInfo.RulesetLoaded` rejects `ReloadDelay <= 0`.
- **Bridge `RemoveOnDeath`.** `Bridge` sets `health.RemoveOnDeath = false` because the actor must survive to be repaired. Most units leave `RemoveOnDeath = true` so they are removed from the world on death.

## Summary

This chapter traces the path from **"I want to attack that"** to **"the [target](../appendices/Appendix_A_Glossary.md)'s HP is reduced"** in OpenRA.

After reading this chapter, you should be able to:

- Trace a complete attack from an order through `AttackBase`, `Armament`, projectile creation, `Weapon.Impact`, warhead resolution, and `Health.InflictDamage`.
- Explain the difference between weapon-level validation (`WeaponInfo.ValidTargets` / `InvalidTargets`) and warhead-level validation (`Warhead.ValidTargets` / `ValidRelationships`).
- Describe how `DamageWarhead` combines firepower modifiers, armor `Versus` values, and `DamageTypes` into a final `Damage` instance.
- Identify the role of `HitShape` in targeting and area-of-effect falloff calculations.
- Add a new projectile, warhead, or damage modifier using the correct extension interfaces.
- Diagnose common combat bugs such as "no damage dealt," "weapon won't fire," and "armor type is ignored."

If any of the concepts above feel unclear, review the relevant section before continuing. For source files and further reading, see the References section.


## References

### Internal chapters

- [Part 1.1 — Entity-Component-System (ECS) and Actor Lifecycle](Part_01_Chapter_01_ECS.md)
- [Part 1.2 — Activities and the Game Loop](Part_01_Chapter_02_Activities.md)
- [Part 1.3 — World, OrderManager, and Orders](Part_01_Chapter_03_World_Orders.md)
- [Part 1.4 — Deterministic Math and Coordinate Systems](Part_01_Chapter_04_Math.md)
- [Part 1.5 — Pathfinding and Movement](Part_01_Chapter_05_Pathfinding_Movement.md)
- [Part 2.4 — Rulesets, Actors, and Weapons](Part_02_Chapter_04_Rules_Weapons.md)
- [Part 8.3 — Bot Squads and Combat Heuristics](Part_08_Chapter_03_Squads.md)

### Source files

- `OpenRA.Game/GameRules/WeaponInfo.cs`
- `OpenRA.Game/Traits/TraitsInterfaces.cs`
- `OpenRA.Game/Actor.cs`
- `OpenRA.Mods.Common/Traits/Armament.cs`
- `OpenRA.Mods.Common/Traits/Attack/AttackBase.cs`
- `OpenRA.Mods.Common/Traits/Attack/AttackFrontal.cs`
- `OpenRA.Mods.Common/Traits/Attack/AttackTurreted.cs`
- `OpenRA.Mods.Common/Traits/Health.cs`
- `OpenRA.Mods.Common/Traits/Armor.cs`
- `OpenRA.Mods.Common/Traits/HitShape.cs`
- `OpenRA.Mods.Common/Traits/Buildings/Bridge.cs`
- `OpenRA.Mods.Common/Projectiles/Bullet.cs`
- `OpenRA.Mods.Common/Projectiles/Missile.cs`
- `OpenRA.Mods.Common/Projectiles/InstantHit.cs`
- `OpenRA.Mods.Common/Warheads/Warhead.cs`
- `OpenRA.Mods.Common/Warheads/DamageWarhead.cs`
- `OpenRA.Mods.Common/Warheads/SpreadDamageWarhead.cs`
- `OpenRA.Mods.Common/Warheads/CreateEffectWarhead.cs`
- `OpenRA.Mods.Common/Warheads/FireClusterWarhead.cs`

### Online resources

- OpenRA wiki — "Weapons" and "Traits" modding guides: <https://wiki.openra.net/>
- OpenRA source repository — `OpenRA.Mods.Common/Traits` and `OpenRA.Mods.Common/Warheads`: <https://github.com/OpenRA/OpenRA>

## What to read next

- [Part 2.4 — Rulesets, Actors, and Weapons](Part_02_Chapter_04_Rules_Weapons.md): combat classes and YAML are defined in the ruleset; this chapter explains how `WeaponInfo`, `ArmamentInfo`, and actor traits are loaded.
- [Part 8.3 — Bot Squads and Combat Heuristics](Part_08_Chapter_03_Squads.md): see how AI squads and bot modules use the same attack pipeline to decide targets and issue orders.
- [Part 5.1 — Audio Architecture](Part_05_Chapter_01_Audio_Architecture.md): continue from weapon reports and impact sounds into the audio subsystem that plays them.