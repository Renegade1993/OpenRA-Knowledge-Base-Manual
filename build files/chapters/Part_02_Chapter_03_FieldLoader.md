# Chapter 2.3 — FieldLoader and ObjectCreator

## Purpose

`FieldLoader` and `ObjectCreator` are the two halves of OpenRA's runtime bridge between [YAML](../appendices/Appendix_A_Glossary.md) rule files and the C# object model. `ObjectCreator` turns a textual type name (e.g., `Mobile`, `Health`, `WeaponInfo`) into a living C# instance. `FieldLoader` then takes the YAML key/value pairs under that node and assigns them to the matching fields of the instance. Together they make it possible for a modder to declare an actor such as:

```yaml
3tnk:
    Health:
        HP: 50000
    Armor:
        Type: Heavy
```

…and have the engine instantiate `HealthInfo` and `ArmorInfo`, populate their `HP` and `Type` fields, and add them to the actor's [`TypeDictionary`](../appendices/Appendix_A_Glossary.md) of [traits](../appendices/Appendix_A_Glossary.md). The same machinery is reused for weapon info, settings modules, map rules, and any other YAML-backed configuration object.

## Learning Objectives


After studying this chapter, you should be able to:

- Explain how ObjectCreator resolves YAML type names to C# instances.
- Describe how FieldLoader maps YAML key-value pairs to C# fields.
- Use [Require], [LoadUsing], and [Ignore] attributes to control YAML loading.
- Trace the data flow from a [MiniYaml](../appendices/Appendix_A_Glossary.md) actor node to a populated [`TraitInfo`](../appendices/Appendix_A_Glossary.md).
- Identify the built-in scalar and generic collection parsers in FieldLoader.
- Debug common FieldLoader errors such as missing required fields.

## Files

| File | Responsibility |
| :---- | :---- |
| `OpenRA.Game/ObjectCreator.cs` | Resolves type names to .NET `Type` objects, picks constructors, and instantiates objects. It also manages the assembly list supplied by the mod manifest and caches `Type` → `ConstructorInfo` lookups. |
| `OpenRA.Game/FieldLoader.cs` | Deserializes YAML scalar and node data into C# fields. Maintains hard-coded scalar parsers (`TypeParsers`), generic collection parsers (`GenericTypeParsers`), expression caches, and the `[Require]` / `[LoadUsing]` / `[Ignore]` attribute logic. |
| `OpenRA.Game/GameRules/ActorInfo.cs` | Consumer of both systems: iterates the trait nodes of an actor definition, calls `ObjectCreator` to create the `TraitInfo`, then calls `FieldLoader.Load` to fill it. |
| `OpenRA.Game/Traits/TraitsInterfaces.cs` | Defines `TraitInfo`, `TraitInfo<T>`, and the dependency interfaces (`Requires<>`, `NotBefore<>`) that `ActorInfo` uses after loading. |

![Architecture diagram](images/Part_02_Chapter_03_FieldLoader-architecture-diagram-showing-the-main-classes-interfaces-and-9161e6.svg)

## Architecture


```
[MiniYaml rules] --parsed by--> [ActorInfo / Ruleset / Settings]
     |
     v
[ObjectCreator] --FindType--> [TypeCache]
     |
     v
[Constructor with UseCtor] or [parameterless ctor]
     |
     v
[TraitInfo instance] --FieldLoader.Load--> [FieldLoadInfo[]]
     |
     v
[TypeParsers / GenericTypeParsers / TypeDescriptor]
     |
     v
[Populated C# object]
```

### ObjectCreator

`ObjectCreator` is a disposable, mod-scoped service constructed from the active `Manifest` and the installed mods list.

- **Assembly list** (`assemblies`): It always starts with `typeof(Game).Assembly` (the core engine). Then it loads every additional DLL named in the mod's `Assemblies` manifest entry, placing them next to the game executable (`Platform.BinDir`). Because .NET cannot unload assemblies, it hashes each file with SHA-1 and stores the loaded `Assembly` in a static `ResolvedAssemblies` dictionary so the same physical DLL is never loaded twice across mod changes.
- **Type cache** (`typeCache`): Maps a bare class name like `HealthInfo` to a `Type` by scanning every namespace of every loaded assembly (`FindType`). The first match wins.
- **Constructor cache** (`ctorCache`): Maps a `Type` to the single constructor decorated with `[ObjectCreator.UseCtor]`, or `null` if the type should be created with its parameterless constructor.
- **Assembly resolve hook**: It subscribes to `AppDomain.CurrentDomain.AssemblyResolve` so that dependencies of mod assemblies can be found at runtime.

### FieldLoader

`FieldLoader` is a static utility class. Its central job is `Load(object self, MiniYaml my)`, which walks the cached metadata for the target type and assigns values from the YAML.

Key caches:

- `TypeLoadInfo` — a `ConcurrentCache<Type, FieldLoadInfo[]>` built once per type by `BuildTypeLoadInfo`. It inspects every instance field (public or non-public) and decides whether to serialize it based on `SerializeAttribute`. The result is an array of `FieldLoadInfo` containing the `FieldInfo`, the `SerializeAttribute`, and an optional `Func<MiniYaml, object>` loader.
- `BooleanExpressionCache` — caches parsed `BooleanExpression` objects by string.
- `IntegerExpressionCache` — caches parsed `IntegerExpression` objects by string.

### FieldLoadInfo

`FieldLoadInfo` is the metadata token for one YAML-bound field. It contains:

- `Field` — the `FieldInfo` to set.
- `Attribute` — the `SerializeAttribute` derived from `[Require]`, `[LoadUsing]`, `[Ignore]`, or the default.
- `Loader` — an optional delegate created from a `[LoadUsing("MethodName")]` static method.
- `YamlName` — always the C# field name; YAML keys must match it exactly.

### Parser dictionaries

`TypeParsers` is a `FrozenDictionary<Type, Func<string, Type, string, object>>` keyed by exact scalar types: `int`, `ushort`, `float`, `bool`, `string`, `Color`, `Hotkey`, `WDist`, `WVec`, `WPos`, `WAngle`, `WRot`, `CPos`, `CVec`, `BooleanExpression`, `IntegerExpression`, `DateTime`, and several fixed-size vector/array types.

`GenericTypeParsers` is a `FrozenDictionary<Type, Func<string, Type, string, MiniYaml, object>>` keyed by open generic definitions: `HashSet<>`, `List<>`, `Dictionary<,>`, `ImmutableArray<>`, `FrozenSet<>`, `FrozenDictionary<,>`, `BitSet<>`, and `Nullable<>`.

Both are static and intentionally read-only; they cannot be mutated at runtime. This is a deliberate performance choice: frozen dictionaries provide fast lookup and the parser table is compiled into the engine.

![Data flow  code path diagram](images/Part_02_Chapter_03_FieldLoader-sequence-flow-diagram-tracing-the-execution-path-from-trigge-035864.svg)

## Data Flow / Code Path


### 1. From a YAML actor to a trait instance

The canonical path is `ActorInfo` construction in `ActorInfo.cs`.

1. The constructor receives a `MiniYaml` node representing one actor definition.
2. For each child node (`node.Nodes`), it calls `LoadTraitInfo(creator, t.Key, t.Value)`.
3. `LoadTraitInfo` first rejects a non-empty scalar value on the trait node itself — a trait must be a mapping, not a string.
4. It strips any `@InstanceName` suffix using `TraitInstanceSeparator` (`'@'`), so `Mobile@CampaignOnly` becomes `Mobile`.
5. It asks `ObjectCreator` for `creator.CreateObject<TraitInfo>(traitName + "Info")`. This is the name convention: a YAML trait `Health` maps to the C# info class `HealthInfo`.
6. `CreateObject<TraitInfo>` looks up the type in `typeCache` and either:
   - throws `InvalidOperationException` if the type cannot be found (unless `ObjectCreator.MissingTypeAction` is set for the linter), or
   - finds the `[UseCtor]` constructor (or the parameterless constructor) and creates the instance.
7. If an instance name was present, it is written via reflection into the `TraitInfo.InstanceName` field.
8. `FieldLoader.Load(info, my)` is called.

### 2. FieldLoader.Load

`FieldLoader.Load(object self, MiniYaml my)` performs the population.

1. It looks up the cached `FieldLoadInfo[]` for `self.GetType()`.
2. It lazily converts the YAML node into a `Dictionary<string, MiniYaml>` for key lookup.
3. For each `FieldLoadInfo`:
   - If a custom `Loader` exists, it checks whether the field is `[Require]` and whether the YAML key is present. If required and missing, the YAML name is added to a `missing` list; otherwise the loader is invoked with the original `MiniYaml`.
   - If no custom loader exists, it calls `TryGetValueFromYaml`. If the key is absent and the field is `[Require]`, it is recorded as missing; otherwise the field is skipped and its default value remains.
   - If a value is produced, `fli.Field.SetValue(self, val)` is called.
4. After all fields are processed, if any required fields were missing, a `FieldLoader.MissingFieldsException` is thrown.

### 3. Converting a YAML value to a C# value

`TryGetValueFromYaml` calls `GetValue(field.Name, field.FieldType, yaml)`, which dispatches to the most specific overload: `GetValue(string fieldName, Type fieldType, string value, MiniYaml yaml)`.

1. The scalar value is trimmed.
2. If the type is a generic type, it looks up the open generic definition in `GenericTypeParsers`.
3. Otherwise it checks `TypeParsers` by exact type.
4. If neither matched, it checks for one-dimensional arrays and enums.
5. If still unmatched, it falls back to `TypeDescriptor.GetConverter(fieldType)`. If the converter can convert from `string`, it is used; otherwise `UnknownFieldAction` is invoked.

The parser itself returns an object. Scalar value types are boxed on return; the dictionary/array parsers return already-allocated objects. `Field.SetValue` then performs the final unboxing or reference assignment.

![Configuration (yaml) diagram](images/Part_02_Chapter_03_FieldLoader-annotated-yaml-snippet-diagram-showing-the-key-fields-and-ho-6a1b98.svg)

## Configuration (YAML)


### Trait names → Info class names

YAML uses the trait name without the `Info` suffix. The engine appends `Info` internally. Examples from the Red Alert mod:

```yaml
3tnk:
    Mobile:
        Speed: 85
    Health:
        HP: 50000
    Armor:
        Type: Heavy
```

These map to `MobileInfo`, `HealthInfo`, and `ArmorInfo` respectively.

### Trait instance suffix

To use a trait multiple times on the same actor, add `@Name`:

```yaml
someactor:
    Armament@Primary:
        Weapon: 25mm
    Armament@Secondary:
        Weapon: 50mm
```

The `ObjectCreator` still resolves `ArmamentInfo`, but the post-creation reflection step sets `InstanceName` to `Primary` and `Secondary` in `ActorInfo.cs`.

### Field names → YAML keys

YAML keys are matched against C# field names case-sensitively. The default `SerializeAttribute` means public and non-public instance fields are eligible unless marked `[Ignore]`. Properties are **not** loaded by `FieldLoader.Load` — only fields. `FieldLoader.LoadFieldOrProperty` can load both fields and properties, but it is used only for ad-hoc overrides such as command-line settings.

### Value formats

- Numeric scalars are parsed with invariant culture. `float` and `decimal` accept an optional trailing `%` (e.g., `Speed: 50%` becomes `0.5`).
- Vector types use comma-separated components: `WVec: 0,0,1` is `WVec(0, 0, 1)`.
- Arrays and lists use comma-separated scalar values: `Offsets: 1,2,3,4` becomes a collection of ints.
- Dictionary and `FrozenDictionary` types consume the child YAML nodes: each child node becomes one key/value pair.
- `BooleanExpression` and `IntegerExpression` store the raw string but parse it once and cache the compiled expression.
- `Nullable<T>` accepts an empty or missing value as `null`.

## Interconnectivity

### Depends on

- **MiniYaml parser** (`OpenRA.Game/MiniYaml.cs`) — supplies the `MiniYaml` and `MiniYamlNode` structures that `FieldLoader` consumes.
- **Manifest / AssemblyLoader** (`OpenRA.Game/Manifest.cs`, `OpenRA.Game/Support/AssemblyLoader.cs`) — tell `ObjectCreator` which mod assemblies to load.
- **TypeDescriptor / .NET converters** — the fallback path for types not explicitly handled by `TypeParsers`.
- **CryptoUtil** (`OpenRA.Primitives/CryptoUtil.cs`) — used to hash assemblies before loading them.
- **Cache / ConcurrentCache** (`OpenRA.Primitives/Cache.cs`) — provides the memoization used by `ObjectCreator` and `FieldLoader`.

### Used by

- **ActorInfo** (`OpenRA.Game/GameRules/ActorInfo.cs`) — loads trait info from actor rules.
- **WeaponInfo** (`OpenRA.Game/GameRules/WeaponInfo.cs`) — loads weapon definitions.
- **Ruleset** (`OpenRA.Game/GameRules/Ruleset.cs`) — orchestrates the loading of actor, weapon, voice, music, and condition rules.
- **Settings** (`OpenRA.Game/Settings.cs`) — loads and merges user settings from YAML and command-line overrides.
- **MapGenerator / MultiBrush** (`OpenRA.Mods.Common/MapGenerator/MultiBrush.cs`) — invokes `FieldLoader.InvalidValueAction` manually for custom validation.
- **CheckYaml linter** (`OpenRA.Mods.Common/UtilityCommands/CheckYaml.cs`) — replaces `ObjectCreator.MissingTypeAction` and `FieldLoader.UnknownFieldAction` to emit non-fatal errors.

![Algorithms diagram](images/Part_02_Chapter_03_FieldLoader-algorithm-diagram-or-pseudocode-flowchart-for-the-non-trivia-5983ed.svg)

## Algorithms


### Type resolution in ObjectCreator

```
function FindType(className):
    for each (assembly, namespace) in assemblies:
        type = assembly.GetType(namespace + "." + className, false)
        if type != null:
            return type
    return null
```

The `assemblies` array is built once during construction and is the Cartesian product of every loaded assembly and every namespace declared inside that assembly. This means a bare name like `HealthInfo` can live in any namespace of any loaded assembly, but the first matching namespace wins. Modders should avoid duplicate type names across namespaces.

### Constructor selection

```
function GetCtor(type):
    ctors = type.GetConstructors(all instance flags) where HasAttribute<UseCtor>()
    if count > 1: throw
    return first or null
```

If a `[UseCtor]` constructor is found, `CreateUsingArgs` is used. It builds an argument array by matching constructor parameter names to keys in the `args` dictionary passed to `CreateObject`. If no `[UseCtor]` constructor is found, the parameterless constructor is invoked via `CreateBasic`.

### Field metadata construction

```
function BuildTypeLoadInfo(type):
    result = []
    for each instance field in type (public or non-public):
        attr = custom SerializeAttribute or Default
        if not attr.Serialize: continue
        loader = attr.GetLoader(type)
        result.add(new FieldLoadInfo(field, attr, loader))
    return result
```

Only instance fields are considered. Static fields and properties are ignored by `FieldLoader.Load`.

### Parser dispatch

```
function GetValue(fieldName, fieldType, value, yaml):
    value = value.Trim()
    if fieldType.IsGenericType:
        if GenericTypeParsers.TryGetValue(fieldType.GetGenericTypeDefinition()):
            return parser(fieldName, fieldType, value, yaml)
    else:
        if TypeParsers.TryGetValue(fieldType):
            return parser(fieldName, fieldType, value)
        if fieldType.IsArray and rank == 1:
            return ParseArray(...)
        if fieldType.IsEnum:
            return ParseEnum(...)
    converter = TypeDescriptor.GetConverter(fieldType)
    if converter.CanConvertFrom(string):
        try convert; on error call InvalidValueAction
    else:
        UnknownFieldAction(...)
```

This order matters: generic types are handled before exact-type fallback, and the `TypeDescriptor` fallback is the last resort.

### BooleanExpression / IntegerExpression caching

Both expression types are parsed via static `ConcurrentCache` instances. The cache key is the raw expression string. The first parse compiles the expression; subsequent identical strings reuse the same object. This is important because conditions and integer expressions are used heavily in trait definitions and would otherwise be parsed repeatedly during every rule load.

![Extension points diagram](images/Part_02_Chapter_03_FieldLoader-extension-hook-diagram-showing-the-interface-s-to-implement-b4a27b.svg)

## Extension Points


### 1. TypeConverter fallback

For types that are not in `TypeParsers` or `GenericTypeParsers`, `FieldLoader` asks the .NET `TypeDescriptor` for a converter. The standard library provides converters for `sbyte`, `byte`, `short`, `double`, `TimeSpan`, `Guid`, and many other primitive and struct types. Modders can write their own by subclassing `System.ComponentModel.TypeConverter` and applying `[TypeConverter(typeof(MyConverter))]` to their custom type. `OpenRA.Mods.Common/ActorInitializer.cs` does exactly this with `ActorInitLoader` for `ActorInitActorReference`.

Limitations:

- The fallback only receives a trimmed string; it cannot inspect child YAML nodes.
- It is invoked only after the built-in parser dictionaries fail.

### 2. `[LoadUsing]` custom loader

For cases where the built-in parser machinery is insufficient, a field can request a custom static loader method:

```csharp
public class MyTraitInfo : TraitInfo<MyTrait>
{
    [FieldLoader.LoadUsing(nameof(LoadCustomData))]
    public CustomType Data;

    static CustomType LoadCustomData(MiniYaml yaml)
    {
        // Full access to the MiniYaml node
        return ...;
    }
}
```

The loader method must be static, accept `MiniYaml`, and return `object`. It is looked up with `BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Static | BindingFlags.FlattenHierarchy`, so it can be private or inherited. The returned value is assigned directly to the field via reflection.

### 3. Custom mod assemblies

New types are discovered by listing their assembly in the mod's `mod.yaml`:

```yaml
Assemblies:
    common|OpenRA.Mods.Common.dll
    mymod|MyMod.dll
```

`ObjectCreator` loads the DLL and scans its namespaces. Any `TraitInfo` class following the naming convention `MyTraitInfo` can then be referenced from YAML as `MyTrait`.

### 4. Error-action overrides

`ObjectCreator.MissingTypeAction`, `FieldLoader.UnknownFieldAction`, and `FieldLoader.InvalidValueAction` are public static delegates. They can be replaced to change failure behavior. The linter uses this to turn exceptions into logged errors in `CheckYaml.cs`, and the settings loader uses it to substitute default values instead of crashing in `Settings.cs`.

Because these are global static fields, callers should always save the previous value and restore it in a `finally` block.

### 5. Adding new "first-class" types

Engine developers can extend `TypeParsers` or `GenericTypeParsers` by editing `FieldLoader.cs` and adding a new `case` to the static initialization. This is not a runtime extension point, but it is the standard way to add high-performance parsing for a new scalar or collection type that is used by many traits. The convention is to add a `ParseXxx` static method and register it in the appropriate frozen dictionary.

![Common pitfalls  guardrails diagram](images/Part_02_Chapter_03_FieldLoader-checklist-infographic-style-diagram-summarizing-the-top-pitf-fb069e.svg)

## Common Pitfalls / Guardrails


### Assembly lifetime

`ObjectCreator` comments explicitly note that .NET does not support unloading assemblies. The static `ResolvedAssemblies` dictionary prevents duplicate loads, but once a mod DLL is loaded it stays in memory until the process exits. This is why mod changes require a game restart.

### TypeParsers are frozen

`TypeParsers` and `GenericTypeParsers` are built as `FrozenDictionary` objects. They cannot be modified at runtime. Modders cannot "register" a new parser without recompiling the engine. Use `[LoadUsing]` or `TypeConverter` instead.

### BoxedInt cache only covers 0–32

`BoxedInts` is initialized as `Exts.MakeArray(33, i => (object)i)`. When `ParseInt` returns an integer in the range `0` to `32` inclusive, it returns the cached boxed object instead of allocating a new box. This is a micro-optimization for very common small values (facing angles, tile offsets, counts). Values outside this range are boxed normally. Relying on reference equality of boxed ints is a bug; only value equality is guaranteed.

### BooleanExpression and IntegerExpression caches are unbounded

They cache by raw string, so every unique expression string lives in the cache for the process lifetime. This is fine because rule sets use a finite set of expressions, but dynamically generated expressions with unique keys could grow memory. Expression parse errors are caught and rethrown as `YamlException` with the original expression text preserved.

### `[Require]` does not apply to default values

A field marked `[FieldLoader.Require]` must be present in the YAML node. If the key is missing, `FieldLoader.Load` collects the name and throws a single `MissingFieldsException` at the end. The exception message is decorated by `ActorInfo.LoadTraitInfo` to include the trait name. `LoadUsing` fields also honor `[Require]`.

### Properties are not auto-loaded

`BuildTypeLoadInfo` only enumerates `GetFields`, not `GetProperties`. If you add a property, it will not be populated by YAML unless you explicitly call `FieldLoader.LoadFieldOrProperty`.

### LoadUsing method signature

The loader must be `static object MethodName(MiniYaml yaml)`. If the method signature is wrong, `Delegate.CreateDelegate` will throw at metadata-build time. The method name is given as a string, so renaming the method without updating the attribute will cause a runtime `InvalidOperationException`.

### Trait nodes must not carry scalar values

`LoadTraitInfo` throws `YamlException` if the trait node has a non-empty `Value`. A trait is always a mapping; its data lives in child nodes.

### Unknown fields throw by default

If a YAML file contains a key that does not match any serializable field on the target type, the default `UnknownFieldAction` throws a `NotImplementedException`. The linter swaps this to a logged error. The same action is also used when the `TypeDescriptor` fallback cannot find a converter for a type.

### Type name collisions

Because `FindType` scans every namespace of every loaded assembly, two different assemblies defining the same bare class name (e.g., `HealthInfo`) will collide. The first namespace in the `assemblies` array wins. The array order is deterministic: core engine first, then manifest assemblies in the order declared.

## Summary

This chapter explains how `FieldLoader` and `ObjectCreator` turn MiniYaml rule files into runtime C# objects.

After reading this chapter, you should be able to:

- The constructor receives a `MiniYaml` node representing one actor definition.
- For each child node (`node.Nodes`), it calls `LoadTraitInfo(creator, t.Key, t.Value)`.
- `LoadTraitInfo` first rejects a non-empty scalar value on the trait node itself — a trait must be a mapping, not a string.
- It strips any `@InstanceName` suffix using `TraitInstanceSeparator` (`'@'`), so `Mobile@CampaignOnly` becomes `Mobile`.
- It asks `ObjectCreator` for `creator.CreateObject<TraitInfo>(traitName + "Info")`. This is the name convention: a YAML trait `Health` maps to the C# info class `HealthInfo`.
- `CreateObject<TraitInfo>` looks up the type in `typeCache` and either:

If any of the concepts above feel unclear, review the relevant section before continuing. For source files and further reading, see the References section.


## References

- `OpenRA.Game/FieldLoader.cs` — source for `FieldLoader`, `FieldLoadInfo`, `SerializeAttribute`, `RequireAttribute`, `LoadUsingAttribute`, `IgnoreAttribute`, and all parser methods.
- `OpenRA.Game/ObjectCreator.cs` — source for type resolution, constructor selection, and object instantiation.
- `OpenRA.Game/GameRules/ActorInfo.cs` — primary caller demonstrating the trait-name → `Info` convention and the use of `FieldLoader.Load`.
- `OpenRA.Game/Traits/TraitsInterfaces.cs` — definition of `TraitInfo` and `TraitInfo<T>`.
- `OpenRA.Game/Settings.cs` — example of swapping `InvalidValueAction` and `UnknownFieldAction` for non-fatal settings loading.
- `OpenRA.Mods.Common/UtilityCommands/CheckYaml.cs` — example of swapping error actions for linting.
- `OpenRA.Mods.Common/ActorInitializer.cs` — example of a custom `TypeConverter` for `ActorInitActorReference`.
- `OpenRA.Test/OpenRA.Game/FieldLoaderTest.cs` — exhaustive test cases covering every parser, `[Require]`, `[LoadUsing]`, `[Ignore]`, `LoadFieldOrProperty`, nested collections, and `TypeConverter` fallback.
- Online: .NET `TypeDescriptor` and `TypeConverter` documentation for implementing custom converters.

## What to read next

- [Part 2.4 — Rulesets, Actors, and Weapons](Part_02_Chapter_04_Rules_Weapons.md): FieldLoader and ObjectCreator are the bridge that produces the `ActorInfo` and `WeaponInfo` objects stored in the ruleset.
- [Part 2.1 — MiniYaml Parser and Inheritance](Part_02_Chapter_01_MiniYaml.md): the AST and merge/inheritance algorithms that supply the `MiniYaml` nodes consumed by `FieldLoader`.
- [Part 2.2 — Manifest, ModData, Ruleset, and RulesetCache](Part_02_Chapter_02_Manifest.md): learn how `ModData` creates the `ObjectCreator` and invokes the ruleset load that uses FieldLoader.