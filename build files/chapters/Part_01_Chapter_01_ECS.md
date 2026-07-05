# Chapter 1.1 — Entity-Component-System (ECS) and Actor Lifecycle

## Purpose

This chapter explains the foundation of OpenRA's simulation architecture: every object in the game world is an [`Actor`](../appendices/Appendix_A_Glossary.md), and all behavior comes from detachable, data-driven **[Traits](../appendices/Appendix_A_Glossary.md)** that are attached to that actor. The goals are to show how an empty container (`Actor`) becomes a fully functional unit, building, or world system; how configuration (YAML) is separated from runtime state (C# trait instances); how the engine resolves trait dependencies, caches hot paths, and enforces single-instance invariants; and where mod authors can extend each stage of the lifecycle.

OpenRA's ECS differs from classical ECS frameworks. Instead of a dense array of homogeneous components queried by systems, OpenRA uses a **dictionary-of-traits** model: each actor owns a set of trait instances that implement marker interfaces, and the engine queries them via `Trait<T>`, `TraitOrDefault<T>`, or `TraitsImplementing<T>`. The split between [`TraitInfo`](../appendices/Appendix_A_Glossary.md) (immutable, shared, loaded from [YAML](../appendices/Appendix_A_Glossary.md)) and [`Trait`](../appendices/Appendix_A_Glossary.md) (mutable, per-actor, created at spawn time) is the key design that keeps the simulation [deterministic](../appendices/Appendix_A_Glossary.md) and cheap to replay.

## Learning Objectives


After studying this chapter, you should be able to:

1. Explain why OpenRA uses an Actor/Trait split rather than a classical object-oriented hierarchy.
2. Distinguish `TraitInfo` from `Trait` and describe their lifetimes and mutability rules.
3. Trace the path from a YAML actor definition to a fully constructed actor in the world.
4. Use `Trait<T>`, `TraitOrDefault<T>`, and `TraitsImplementing<T>` correctly in C# code.
5. Identify and resolve `Requires<T>` and `NotBefore<T>` dependency conflicts.
6. Understand why `Actor` caches hot interfaces and which interfaces are cached.
7. Explain how the condition system disables traits without removing them.

![Practical example: creating a simple unit diagram](images/Part_01_Chapter_01_ECS-end-to-end-worked-example-diagram-showing-the-inputs-interme-5fc6a2.svg)

## Practical Example: Creating a Simple Unit


Suppose you want to add a `Scout` unit to a mod. In YAML you would write:

```yaml
Scout:
    Inherits: ^Vehicle
    Mobile:
        Speed: 80
    RevealsShroud:
        Range: 10c0
    Health:
        HP: 2000
    Armor:
        Type: Light
```

When the map loads, the engine:

1. Loads `Scout` into an `ActorInfo` with `TraitInfo` instances for `Mobile`, `RevealsShroud`, `Health`, and `Armor`.
2. Resolves dependencies (e.g., `Mobile` requires `IOccupySpace`).
3. When the unit is built, creates a new `Actor` and runs `Create` on each `TraitInfo` to produce the runtime traits.
4. Caches interfaces like `IOccupySpace` so the renderer and pathfinder can query them quickly.
5. Ticks the actor and its traits every frame until the unit is destroyed.

This example shows how YAML configuration becomes C# runtime behavior through the ECS pipeline.

## Files

- `OpenRA.Game/Actor.cs` — The `Actor` class: construction, interface caching, tick/render/order hooks, condition system, and disposal.
- `OpenRA.Game/Traits/TraitsInterfaces.cs` — Shared trait interfaces (`IHealth`, `IOccupySpace`, `IFacing`, `ITargetable`, `ISync`, `INotifyIdle`, `IRulesetLoaded`, `Requires<T>`, `NotBefore<T>`, etc.).
- `OpenRA.Game/TraitDictionary.cs` — Per-actor trait storage, indexed by actor ID and interface, used by `World.TraitDict`.
- `OpenRA.Game/Primitives/TypeDictionary.cs` — Generic dictionary keyed by type, used by `ActorInfo` for `TraitInfo` collections and by `ActorInitializer` for init values.
- `OpenRA.Game/Map/ActorInitializer.cs` — Bridge between actor construction arguments (`ActorInit`) and the traits that consume them; supports named trait instances and `ISingleInstanceInit`.
- `OpenRA.Game/ObjectCreator.cs` — Reflection-based factory that maps YAML trait names (`"Health"`) to C# `TraitInfo` types (`"HealthInfo"`), loads mod assemblies, and caches constructors.
- `OpenRA.Game/FieldLoader.cs` — YAML-to-C# value deserializer; parses primitives, collections, world types, and custom loaders via `SerializeAttribute` / `LoadUsingAttribute`.
- `OpenRA.Game/GameRules/ActorInfo.cs` — The rules-definition of an actor: a `TypeDictionary` of `TraitInfo`s, dependency resolution, and construction ordering.
- `OpenRA.Game/GameRules/Ruleset.cs` — Loads default and map-specific rules, runs `IRulesetLoaded` hooks, and exposes `Rules.Actors`.

![Architecture diagram](images/Part_01_Chapter_01_ECS-architecture-diagram-showing-the-main-classes-interfaces-and-9161e6.svg)

## Architecture


![The openra ecs shape diagram](images/Part_01_Chapter_01_ECS-two-tier-diagram-traitinfo-immutable-shared-and-trait-mutabl-66a487.svg)

### The OpenRA ECS Shape


OpenRA's ECS is a **two-tier info/instance pattern**.

| Tier | Class | Lifetime | Source | Role |
|------|-------|----------|--------|------|
| Info | `TraitInfo` (and `TraitInfo<T>`) | One per actor definition | YAML rules, loaded once per `Ruleset` | Immutable configuration, dependency graph, ruleset-wide cross references |
| Instance | The trait class `T` | One per spawned actor | Created by `TraitInfo.Create(ActorInitializer)` | Mutable runtime state, receives tick/order/render events |

- An `Actor` is an **empty container**. Its public members (`[World](../appendices/Appendix_A_Glossary.md)`, `ActorID`, `Owner`, `Info`, `IsInWorld`, etc.) exist only to wire traits together. The actor itself has no unit-specific logic.
- A `Trait` is any C# object attached to the actor. Traits implement one or more interfaces from `TraitsInterfaces.cs`. There is no base class requirement; a trait can be as small as a single data holder or as large as a full subsystem.
- `ITraitInfo` is not a single interface; it is a family of two things: the empty marker `ITraitInfoInterface`, and the abstract `TraitInfo` class that adds `InstanceName` and `abstract object Create(ActorInitializer init)`. Most trait definitions use `class MyTraitInfo : TraitInfo<MyTrait>, ...` to implement `Create` with `new T()`.
- `ActorInfo` is the rules-level definition of an actor. It contains a `TypeDictionary` of `TraitInfo` objects and knows how to order them by `Requires<T>` and `NotBefore<T>` dependencies.
- `World.TraitDict` is a `TraitDictionary` (per-world, not per-actor) that stores every trait instance of every actor, indexed by interface. This lets global queries like `World.ActorsWithTrait<MyInterface>()` run efficiently.
- `ActorInitializer` is the construction-time argument bag. It wraps a `TypeDictionary` of `ActorInit` objects and lets each `TraitInfo` pull `LocationInit`, `OwnerInit`, `HealthInit`, etc., in a named-trait-aware way.

### Why the Info/Trait Split Preserves Determinism

1. **Shared, immutable data** — `TraitInfo` objects are created once per `Ruleset` and reused by every actor of that type. Mutating one instance's fields would affect every actor, so `TraitInfo` fields are expected to be `readonly` or loaded only from YAML.
2. **Runtime state is per-actor** — Health, position, activity queues, condition tokens, and cached renderables live in the trait instance, not in the `Info`.
3. **Construction order is fixed** — `ActorInfo.TraitsInConstructOrder()` resolves dependencies before any actor is created, so all actors of the same type build their trait instances in the same deterministic order.
4. **Ruleset-level linking happens once** — `IRulesetLoaded.RulesetLoaded(Ruleset, ActorInfo)` lets trait infos cache references to other actors, weapons, or locomotors during ruleset construction, avoiding runtime reflection or string lookups during simulation.

![Key cached interfaces and why they are cached diagram](images/Part_01_Chapter_01_ECS-actor-object-diagram-showing-the-cached-interface-fields-and-9ccb9a.svg)

### Key Cached Interfaces and Why They Are Cached


Inside `Actor` constructor the engine eagerly resolves specific interfaces and stores them in private fields. This is the most performance-critical code path of the whole engine: every actor pays this cost once, then gets fast access for the rest of its life.

| Cached field | Interface | Why it is cached |
|--------------|-----------|----------------|
| `OccupiesSpace` | `IOccupySpace` | Pathfinding, collision, shroud, rendering, and target queries all need `CenterPosition` / `TopLeft` / `OccupiedCells`. |
| `facing` | `IFacing` | Orientation, turret aiming, movement facing, and many renderables need `Facing`/`Orientation`. |
| `health` | `IHealth` | Damage, death, and selection status require fast `IsDead` / `DamageState` checks. |
| `EffectiveOwner` | `IEffectiveOwner` | Disguise/owner-spoofing logic is evaluated frequently by targeting and visibility. |
| `Targetables` | `ITargetable[]` | Combat, orders, and auto-target scan all targetable types. |
| `EnabledTargetablePositions` | `ITargetablePositions` | Provides world-space aim points; cached with `Exts.IsTraitEnabled` filtering. |
| `crushables` | `ICrushable[]` | Movement/ crushing logic checks these on every collision. |
| `resolveOrders` | `IResolveOrder[]` | Orders are dispatched to every resolver in a hot loop. |
| `renders` | `IRender[]` | Render frame. |
| `renderModifiers` | `IRenderModifier[]` | Frame. |
| `mouseBounds` | `IMouseBounds[]` | Input/selection. |
| `visibilityModifiers` | `IVisibilityModifier[]` | Shroud/visibility. |
| `defaultVisibility` | `IDefaultVisibility` | Shroud/visibility. |
| `becomingIdles` | `INotifyBecomingIdle[]` | Activity state transitions. |
| `tickIdles` | `INotifyIdle[]` | Called when idle. |
| `SyncHashes` | `ISync[]` | Network sync hashing walks this array every sync tick. |

Caching these at construction avoids per-frame reflection or `TraitsImplementing<T>` lookups in tight loops. The comments in `Actor.cs` explicitly call this out: the one-off cost is accepted because it speeds up pathfinding, visibility, rendering, and combat.

`ISync` is special: the `SyncHash` struct wraps each `ISync` trait with a precompiled hash function (`Sync.GetHashFunction`), so the network sync loop can call `Hash()` without reflection.

<!-- DEV-NOTE [visual-aid]: Actor lifecycle diagram showing the flow from YAML actor definition → ActorInfo → TraitInfo[] → new Actor() → TraitsInConstructOrder() → per-actor Trait instances → INotifyCreated hooks → World.Add() → Tick/Render/Order processing → World.Remove()/Disposal. Emphasise the immutable info/instance split and the deterministic creation order. -->

## Actor Lifecycle Diagram

The path from a YAML actor definition to a live unit in the world is a straight pipeline. First the ruleset creates immutable `TraitInfo` objects in `OpenRA.Game/GameRules/ActorInfo.cs`; later, spawning in `OpenRA.Game/World.cs` creates per-actor `Trait` instances through `TraitInfo.Create()` and runs the creation hooks.

![Actor Lifecycle Diagram](images/Part_01_Chapter_01_ECS-Actor_Lifecycle_Diagram.svg)
The `Actor` class itself is an empty container; it delegates the actual work to its traits by iterating over the interface arrays that were cached at construction time in `OpenRA.Game/Actor.cs`.

![Actor Tick/Render Delegation](images/Part_01_Chapter_01_ECS-Actor_TickRender_Diagram.svg)
![Data flow  code path diagram](images/Part_01_Chapter_01_ECS-sequence-flow-diagram-tracing-the-execution-path-from-trigge-035864.svg)

## Data Flow / Code Path


### 1. Ruleset Construction (once per map / mod change)

```
Ruleset.LoadDefaults(modData)                [Ruleset.cs]
  MergeOrDefault("Manifest,Rules", ...,
    k => new ActorInfo(modData.ObjectCreator, k.Key.ToLowerInvariant(), k.Value))

ActorInfo constructor                         [ActorInfo.cs]
  foreach (traitNode in yaml)
    trait = LoadTraitInfo(creator, traitName, traitNode.Value)
    traits.Add(trait)
  traits.TrimExcess()

LoadTraitInfo                                 [ActorInfo.cs]
  info = creator.CreateObject<TraitInfo>(traitName + "Info")
  FieldLoader.Load(info, yaml)
  return info

Ruleset constructor                           [Ruleset.cs]
  foreach (ActorInfo a)
    foreach (IRulesetLoaded t in a)
      t.RulesetLoaded(this, a)
```

At this point every actor definition has a fully populated `TypeDictionary` of `TraitInfo` objects. No actual actor exists yet.

### 2. Actor Instantiation and Trait Creation

```
World.CreateActor(bool addToWorld, string name, TypeDictionary initDict)
  var a = new Actor(this, name, initDict)    [World.cs]
  a.Initialize(addToWorld)

Actor constructor                             [Actor.cs]
  Validate: no duplicate ISingleInstanceInit inits
  init = new ActorInitializer(this, initDict)
  ActorID = world.NextAID()
  Owner = ownerInit.Value(world)
  Info = world.Map.Rules.Actors[name]

  foreach (TraitInfo in Info.TraitsInConstructOrder())
    var trait = traitInfo.Create(init)       // usually new T()
    AddTrait(trait)                          // World.TraitDict.AddTrait
    // cache hot interfaces
  }
```

`Info.TraitsInConstructOrder()` returns a topologically sorted array of `TraitInfo`s based on `Requires<T>` and `NotBefore<T>`. Traits are created in that order, and each `TraitInfo.Create` receives the `ActorInitializer` so it can pull map-spawn arguments such as `LocationInit` or `HealthInit`.

### 3. Post-Construction: `Actor.Initialize`

```
Actor.Initialize(bool addToWorld = true)      [Actor.cs]
  created = true
  foreach (INotifyCreated t)
    t.Created(this)

  foreach (IObservesVariables t)
    foreach (VariableObserver v in t.GetVariableObservers())
      register notifier with condition state

  foreach (VariableObserverNotifier n)
    n(this, readOnlyConditionCache)            // initial condition state

  foreach (ICreationActivity t where enabled)
    if activity != null
      throw (only one ICreationActivity allowed)
    CurrentActivity = t.GetCreationActivity()

  if (addToWorld)
    World.Add(this)
```

`INotifyCreated` is the first place a trait can safely interact with other traits. Before this point the actor is still being assembled; after this point the actor is considered "created" and can queue activities. `ICreationActivity` is the only trait that may inject the actor's initial activity, and `Actor.QueueActivity` throws if called before `created` is true.

### 4. World Add / Tick / Render

- `World.Add(this)` adds the actor to the world spatial index and calls `INotifyAddedToWorld` for each trait.
- `Actor.Tick()` runs the current activity, then `INotifyBecomingIdle` or `INotifyIdle.TickIdle` depending on the activity transition.
- `Actor.Render()` applies `IRenderModifier`s over the output of `IRender` traits.
- `Actor.ResolveOrder()` broadcasts `Order` objects to every `IResolveOrder` trait.

### 5. Disposal

```
Actor.Dispose()                               [Actor.cs]
  CurrentActivity?.OnActorDisposeOuter(this)
  WillDispose = true
  World.AddFrameEndTask(_ =>
  {
    if (IsInWorld) World.Remove(this)
    foreach (INotifyActorDisposing t)
      t.Disposing(this)
    World.TraitDict.RemoveActor(this)
    Disposed = true
  })
```

Disposal is deferred to the end of the frame so that other traits do not access a partially-destroyed actor during a tick.

![Configuration (yaml) diagram](images/Part_01_Chapter_01_ECS-annotated-yaml-snippet-diagram-showing-the-key-fields-and-ho-6a1b98.svg)

## Configuration (YAML)


### Actor Definition

```yaml
# mod/rules/infantry.yaml
E1:
    Inherits: ^Infantry
    Buildable:
        Queue: Infantry
        BuildPaletteOrder: 10
    Mobile:
        Speed: 50
    Health:
        HP: 5000
    RevealsShroud:
        Range: 5c0
    WithInfantryBody:
    TakeCover:
```

Each top-level node under an actor name is a trait name. The trait name maps to a C# class by adding the suffix `Info`:

- `Health:` → `HealthInfo`
- `Mobile:` → `MobileInfo`
- `RevealsShroud:` → `RevealsShroudInfo`

### Named Trait Instances

Traits can be duplicated with an `@` suffix:

```yaml
DOME:
    RevealsShroud:
        Range: 10c0
    RevealsShroud@GAP:
        Range: 20c0
        RequiresCondition: gap-generator
```

`ActorInfo.TraitInstanceSeparator` is `'@'`. The base name becomes the trait type; the part after `@` becomes the `InstanceName`. `ActorInitializer.GetOrDefault<T>(TraitInfo)` will prefer an init whose `InstanceName` matches the trait's instance name, falling back to an unnamed init.

### FieldLoader Mapping

Fields in a `TraitInfo` are populated by `FieldLoader.Load`. The default behavior is:

- Public fields are serialized by default.
- Private fields are ignored unless marked with `[FieldLoader.Serialize]` or `[FieldLoader.LoadUsing]`.
- `[FieldLoader.Ignore]` excludes a field from YAML loading.
- `[FieldLoader.Require]` marks a field as required; missing fields raise `MissingFieldsException`.
- `[FieldLoader.LoadUsing("LoaderMethod")]` delegates YAML parsing to a static method on the info class.

Example trait info:

```csharp
public class MyTraitInfo : TraitInfo<MyTrait>
{
    [FieldLoader.Require]
    public readonly int Range = 0;

    [FieldLoader.Ignore]
    public readonly int RuntimeCache = 0;

    [FieldLoader.LoadUsing("LoadOffsets")]
    public readonly WVec[] Offsets = null;

    static WVec[] LoadOffsets(MiniYaml yaml) { ... }
}
```

`FieldLoader` uses a frozen dictionary of primitive parsers (`TypeParsers`) and generic parsers (`GenericTypeParsers`) for `HashSet<>`, `List<>`, `Dictionary<,>`, `ImmutableArray<>`, `FrozenSet<>`, `FrozenDictionary<,>`, `BitSet<>`, and `Nullable<>`. World types like `WPos`, `WVec`, `WDist`, `CPos`, `WRot`, `Color`, and `Hotkey` have dedicated parsers.

### `IRulesetLoaded` — Post-Load Linking

Trait infos that implement `IRulesetLoaded` receive `RulesetLoaded(Ruleset, ActorInfo)` after all rules are loaded. This is the correct place to:

- Resolve references to other actor types (e.g., `world.Map.Rules.Actors["mcv"]`).
- Cache the result of cross-trait info lookups (e.g., `LocomotorInfo` references by name).
- Validate that required trait infos are present.

It is **not** the place to mutate runtime actor state — no actors exist yet.

## Interconnectivity

### How `Actor`, `ActorInfo`, `ActorInitializer`, `TraitInfo`, and `Trait` Relate

- `Actor` holds a reference to its `ActorInfo` (`Info`).
- `ActorInfo` holds a `TypeDictionary` of `TraitInfo` objects and exposes `TraitInfo<T>()`, `TraitInfos<T>()`, `HasTraitInfo<T>()`.
- When `Actor` is constructed, it iterates `Info.TraitsInConstructOrder()` and calls `TraitInfo.Create(init)` for each.
- `TraitInfo.Create` receives an `ActorInitializer`, which wraps the `TypeDictionary` of `ActorInit` objects passed by the map or by `World.CreateActor`.
- The returned trait instance is added to `World.TraitDict` via `Actor.AddTrait(object)`.
- After construction, `Actor` exposes `Trait<T>()` and `TraitsImplementing<T>()` which query `World.TraitDict`.

### `TraitDictionary` vs `TypeDictionary`

- `TypeDictionary` (in `OpenRA.Primitives`) is a simple type-keyed dictionary. It is used for the `ActorInfo.traits` collection and for `ActorInitializer`'s init bag. `Get<T>()` throws if more than one instance of `T` exists.
- `TraitDictionary` (in `OpenRA.Game`) is the global world index. It stores `(Actor, trait)` pairs per interface, sorted by `ActorID`, and supports `ActorsWithTrait<T>`, `ActorsHavingTrait<T>`, and `WithInterface<T>` per actor. `Get<T>` throws if an actor has more than one trait of type `T`.

Both use the same pattern: a generic inner container is created at runtime via `MakeGenericType`, and a value is registered under every interface and base class of the concrete type.

### ObjectCreator and FieldLoader

- `ObjectCreator` is a reflection factory. Its constructor loads the game assembly and any mod assemblies listed in `Manifest.Assemblies`. It caches types by name and constructors decorated with `[ObjectCreator.UseCtorAttribute]`.
- `ObjectCreator.CreateObject<T>(className, args)` resolves the type, picks the `[UseCtor]` constructor if present, and maps the `args` dictionary to constructor parameter names.
- For traits, `ObjectCreator` is used as `creator.CreateObject<TraitInfo>(traitName + "Info")`. The linter can set `ObjectCreator.MissingTypeAction` to avoid crashing when a trait is missing.
- `FieldLoader` then populates the public fields of the newly created `TraitInfo` from the YAML subtree.

### `Requires<T>` and `NotBefore<T>`

Dependencies are declared as interface implementations on the `TraitInfo` class:

```csharp
public class MobileInfo : TraitInfo<Mobile>, Requires<IOccupySpaceInfo>
public class MyInfo : TraitInfo<My>, Requires<HealthInfo>, NotBefore<MobileInfo>
```

`ActorInfo.PrerequisitesOf` extracts `Requires<T>` and `ActorInfo.OptionalPrerequisitesOf` extracts `NotBefore<T>`. The topological sort in `TraitsInConstructOrder()` guarantees that every `Requires<T>` dependency is instantiated before the trait that depends on it, and every `NotBefore<T>` is instantiated after the referenced type if present.

![Algorithms diagram](images/Part_01_Chapter_01_ECS-algorithm-diagram-or-pseudocode-flowchart-for-the-non-trivia-5983ed.svg)

## Algorithms


### Trait Construction Order Resolution

Source: `ActorInfo.TraitsInConstructOrder()`.

1. Build a work item for each `TraitInfo`:
   - `Type` = its concrete type.
   - `Dependencies` = `PrerequisitesOf(info)` (direct, hard requirements).
   - `OptionalDependencies` = `OptionalPrerequisitesOf(info)` (only affects ordering, not presence).
2. Seed `resolved` with traits that have no dependencies at all.
3. Move traits from `unresolved` to `resolved` when:
   - All `Dependencies` are satisfied by already-resolved traits, **and** no unresolved trait still provides a matching dependency.
   - All `OptionalDependencies` are either already resolved or absent.
4. Repeat until no more traits can be resolved.
5. If any trait remains unresolved, throw a `YamlException` listing missing dependencies and unresolved types with their unmet prerequisites.

This is a dependency-graph ordering with a specific tie-breaking rule: even if a dependency is already resolved, an unresolved trait that also implements the dependency blocks the dependent trait until the dependency-only trait is resolved. This prevents ordering races between multiple traits that implement the same interface.

### `TraitDictionary` Storage and Lookup

Source: `TraitDictionary` / `TraitContainer<T>`.

- Each interface/base-class `T` gets a `TraitContainer<T>` holding two parallel `List<T>`s: one of `Actor`, one of `T`.
- Insertion uses a custom binary search on `Actor.ActorID` to keep the list sorted by ID.
- `Get<T>(Actor)` returns the single trait for that actor; it throws if there are multiple.
- `WithInterface<T>(Actor)` returns a custom `IEnumerable<T>` enumerator that scans the contiguous block of entries for that actor ID.
- `ActorsWithTrait<T>()` returns `(Actor, trait)` pairs for every actor in the world.
- `RemoveActor(uint actorID)` removes all contiguous entries for that actor ID from every container.

The binary search is implemented as `SpanExts.BinarySearchMany`, which returns the first index where the actor ID is >= the searched ID. This supports both insertion and lookup.

### `TypeDictionary` Duplicate Detection

Source: `TypeDictionary.Get<T>()`.

- When `Get<T>()` is called, it returns the single object of type `T`.
- If the container holds more than one object of type `T`, it throws `InvalidOperationException`: `"TypeDictionary contains multiple instances of type 'T'"`.

This is how `ActorInfo.TraitInfo<T>()` enforces that only one trait info of a given type exists per actor definition. Traits that are expected to be unique (e.g., one `HealthInfo`) are retrieved via `TraitInfo<T>()`, while repeatable traits are retrieved via `TraitInfos<T>()` (which returns `IReadOnlyCollection<T>`).

### Actor Init Single-Instance Enforcement

Source: `Actor` constructor.

```csharp
var duplicateInit = initDict.WithInterface<ISingleInstanceInit>().GroupBy(i => i.GetType())
    .FirstOrDefault(i => i.Count() > 1);
if (duplicateInit != null)
    throw new InvalidDataException($"Duplicate initializer '{duplicateInit.Key.Name}'");
```

Any `ActorInit` that implements `ISingleInstanceInit` (e.g., `LocationInit`, `OwnerInit`) may appear at most once in an actor's init dictionary. `TypeDictionary` also enforces this when `ActorInitializer.Get<T>()` is called.

### Only-One-Enabled `ICreationActivity`

Source: `Actor.Initialize`.

```csharp
ICreationActivity creationActivity = null;
foreach (var ica in TraitsImplementing<ICreationActivity>())
{
    if (!ica.IsTraitEnabled())
        continue;
    if (creationActivity != null)
        throw new InvalidOperationException($"More than one enabled ICreationActivity trait: ...");
    ...
}
```

This is another single-instance guard: only one enabled trait may provide the actor's initial activity.

![Extension points diagram](images/Part_01_Chapter_01_ECS-extension-hook-diagram-showing-the-interface-s-to-implement-b4a27b.svg)

## Extension Points


### Adding a New Trait

1. Define a `MyTraitInfo : TraitInfo<MyTrait>` class (or implement `TraitInfo.Create` manually).
2. Add public fields; decorate with `[FieldLoader.Require]`, `[FieldLoader.LoadUsing]`, `[FieldLoader.Ignore]`, etc., as needed.
3. Implement `MyTrait` as the runtime class.
4. Implement one or more interfaces from `TraitsInterfaces.cs` to receive events:
   - `ITick` — called every tick.
   - `INotifyCreated` — called after construction, before world add.
   - `INotifyAddedToWorld` / `INotifyRemovedFromWorld` — world membership changes.
   - `INotifyIdle` / `INotifyBecomingIdle` — activity state.
   - `IResolveOrder` — receive player/AI orders.
   - `IIssueOrder` — provide order targeters.
   - `IRender` / `IRenderModifier` / `IRenderAboveShroud` / `IRenderAnnotations` — render hooks.
   - `IOccupySpace` / `IFacing` / `IHealth` / `ITargetable` — core actor state.
   - `ISync` — include trait in network sync hash.
   - `IObservesVariables` / `IConditionConsumer` — react to condition changes.
   - `IRulesetLoaded` — link against other rules during ruleset load.
   - `IGameSaveTraitData` — save/load persistent data.
5. Add `Requires<T>` / `NotBefore<T>` interfaces to the `Info` class to enforce construction order.
6. Add the trait to the actor YAML definition.

### `ConditionalTrait<T>`

Although not in the files requested, most traits in OpenRA.Mods.Common derive from `ConditionalTrait<T>`. This base class implements `IDisabledTrait` and integrates with the condition system. Traits that may be disabled by conditions should implement `IDisabledTrait` and check `IsTraitDisabled` / `IsTraitEnabled` in their hot paths. The actor's cached interface lists (e.g., `Targetables`, `EnabledTargetablePositions`) do not automatically filter by enabled state; consumers must call `IsTraitEnabled()` when it matters.

### `RequiresExplicitImplementationAttribute`

Several interfaces are marked with `[RequireExplicitImplementation]`. This is an engine-level marker that downstream tools (e.g., the lint pass, script interface generation) use to enforce that the interface is implemented directly rather than inherited implicitly. As a trait author, you should implement these interfaces explicitly if your trait exposes their members.

![Common pitfalls  guardrails diagram](images/Part_01_Chapter_01_ECS-checklist-infographic-style-diagram-summarizing-the-top-pitf-fb069e.svg)

## Common Pitfalls / Guardrails


### Do not call `QueueActivity` before `INotifyCreated`

`Actor.QueueActivity` checks `if (!created)` and throws `"An activity was queued before the actor was created. Queue it inside the INotifyCreated.Created callback instead."`. The constructor runs before `created` is set; any per-actor setup that needs activities must happen in `INotifyCreated.Created`.

### Do not assume traits are available during `TraitInfo.Create`

The trait instance is created, but it is not yet added to `World.TraitDict` and other traits on the same actor may not be created yet. Use `INotifyCreated` for cross-trait initialization. `Requires<T>` ensures creation order but not access to the actual trait instance.

### `TraitInfo` fields must be immutable

Because `TraitInfo` instances are shared across all actors of the same type, mutating a `TraitInfo` field at runtime will corrupt every actor of that type. Keep fields `readonly` and perform runtime mutation in the trait instance.

### Missing required fields produce clear errors

`FieldLoader.MissingFieldsException` is caught by `ActorInfo.LoadTraitInfo` and rethrown as `YamlException` with the trait name prefix, so modders see messages like `Actor type e1: Trait name Health: Required property missing: HP`.

### Duplicate `ISingleInstanceInit` inits are rejected early

The actor constructor validates the init dictionary before creating any trait. Passing two `LocationInit` or `OwnerInit` values will throw before the actor is fully built.

### Duplicate trait instances of a non-repeatable type are rejected at lookup time

If a YAML definition accidentally contains two `Health:` nodes (or two `Health@A:` and `Health@B:` nodes that both resolve to `HealthInfo`), `TypeDictionary.Get<HealthInfo>()` will throw at runtime when code asks for `actor.Info.TraitInfo<HealthInfo>()`. The engine does not explicitly pre-validate that only one `HealthInfo` exists; it relies on the lookup semantics. If you need multiple similar behaviors, use distinct `InstanceName`s and query with `TraitInfos<T>()`.

### `ICreationActivity` conflicts are runtime-only

Two enabled traits implementing `ICreationActivity` will throw during `Actor.Initialize`. This is checked at runtime rather than lint time because it depends on condition state.

### `ObjectCreator` cannot unload assemblies

The comment in `ObjectCreator.cs` notes that .NET does not support unloading assemblies, so mod libraries leak across mod changes. `ResolvedAssemblies` uses a SHA1 hash to avoid loading the same assembly twice, but changing mods still leaks memory. Mod switchers should be aware of this limitation.

### `FieldLoader` value parsing is culture-invariant

Numeric parsers use `InvariantInfo`. Percent values and world coordinates (e.g., `5c0`, `0,0,0`) have dedicated parsers. Do not rely on locale-specific formatting.

### `TraitInfo` type names must match the YAML name

The convention is strict: YAML `Health:` maps to `HealthInfo`. The engine builds the type name by concatenation (`traitName + "Info"`). A mismatch results in `Cannot locate type: HealthInfo` (or a linter message if `MissingTypeAction` is set).

## Summary

This chapter explains the foundation of OpenRA's simulation architecture: every object in the game world is an [`Actor`](../appendices/Appendix_A_Glossary.md), and all behavior comes from detachable, data-driven **[Traits](../appendices/Appendix_A_Glossary.md)** that are attached to that actor.

After reading this chapter, you should be able to:

- Explain why OpenRA uses an Actor/Trait split rather than a classical object-oriented hierarchy.
- Distinguish `TraitInfo` from `Trait` and describe their lifetimes and mutability rules.
- Trace the path from a YAML actor definition to a fully constructed actor in the world.
- Use `Trait<T>`, `TraitOrDefault<T>`, and `TraitsImplementing<T>` correctly in C# code.
- Identify and resolve `Requires<T>` and `NotBefore<T>` dependency conflicts.
- Understand why `Actor` caches hot interfaces and which interfaces are cached.
- Explain how the condition system disables traits without removing them.

If any of the concepts above feel unclear, review the relevant section before continuing. For source files and further reading, see the References section.


## References

- `OpenRA.Game/Actor.cs` (`Actor` class, lifecycle, interface caching, conditions, disposal).
- `OpenRA.Game/Traits/TraitsInterfaces.cs` (core trait interfaces, `TraitInfo`, `Requires<T>`, `NotBefore<T>`, `RequireExplicitImplementationAttribute`).
- `OpenRA.Game/GameRules/ActorInfo.cs` (trait info loading, `TraitsInConstructOrder`, dependency resolution).
- `OpenRA.Game/GameRules/Ruleset.cs` (ruleset loading, `IRulesetLoaded` hook, default/map rule merging).
- `OpenRA.Game/TraitDictionary.cs` (global trait storage, per-actor lookup, `TraitContainer<T>` binary search).
- `OpenRA.Game/Primitives/TypeDictionary.cs` (type-keyed dictionary, duplicate-instance enforcement).
- `OpenRA.Game/Map/ActorInitializer.cs` (actor init bag, `ISingleInstanceInit`, named-instance lookup).
- `OpenRA.Game/ObjectCreator.cs` (reflection factory, mod assembly loading, constructor caching).
- `OpenRA.Game/FieldLoader.cs` (YAML deserialization, primitive/generic parsers, `SerializeAttribute`/`LoadUsingAttribute`).
- `OpenRA.Game/Primitives/ActorInfoDictionary.cs` (system actor fallback entries).



### External resources

- [OpenRA traits reference](https://docs.openra.net/en/release/traits/)
## What to read next

- [Part 1.2 — Activities and the Game Loop](Part_01_Chapter_02_Activities.md): the actor lifecycle connects directly to the activity queue; learn how activities drive actor behavior each tick.
- [Part 2.4 — Rulesets, Actors, and Weapons](Part_02_Chapter_04_Rules_Weapons.md): dive into how `ActorInfo` and `TraitInfo` are created from YAML rulesets.
- [Part 1.3 — World, OrderManager, and Orders](Part_01_Chapter_03_World_Orders.md): see how the `World` container, actors, and orders interact at runtime.
- [Appendix B — Common YAML Patterns](../appendices/Appendix_B_Common_YAML_Patterns.md): for concrete examples of the actor/trait definitions that feed into the ECS lifecycle.
- [Appendix D — Engine Conventions and Style](../appendices/Appendix_D_Engine_Conventions.md): for the trait naming, `Requires<T>`/`NotBefore<T>`, and sync conventions you will use when adding new traits.