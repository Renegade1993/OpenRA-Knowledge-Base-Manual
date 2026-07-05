# Chapter 2.1 — MiniYaml Parser and Inheritance

## Purpose

OpenRA stores almost all of its mod data in a custom [YAML](../appendices/Appendix_A_Glossary.md) dialect called **[MiniYaml](../appendices/Appendix_A_Glossary.md)**. It is *not* a general-purpose YAML 1.1/1.2 parser: it is a small, deterministic, streaming parser tuned for the engine's specific needs. It loads rules, sequences, weapons, voices, notifications, chrome, settings, and map overrides; it resolves template inheritance across multiple files; and it merges map-defined overrides into mod defaults. This chapter explains the grammar, the AST, the parser's data path, the merge/inheritance algorithms, and the error cases that mod authors and engine developers hit in practice.

## Learning Objectives


After studying this chapter, you should be able to:

1. Explain why OpenRA uses a custom [YAML](../appendices/Appendix_A_Glossary.md) dialect instead of a standard YAML parser.
2. Describe the immutable `MiniYamlNode` / `MiniYaml` AST and the mutable `MiniYamlNodeBuilder` / `MiniYamlBuilder` variants.
3. Trace the parsing pipeline from `MiniYaml.FromFile` through `FromLines` to a tree of nodes.
4. Understand inheritance (`Inherits:`), multiple inheritance (`Inherits@NAME:`), and [trait](../appendices/Appendix_A_Glossary.md)/[actor](../appendices/Appendix_A_Glossary.md) removal (`-TraitName:`).
5. Predict how duplicate keys within a file and later files in a manifest list override earlier definitions.
6. Read and write MiniYaml for actors, traits, weapons, and sequences.
7. Use `SourceLocation` to diagnose parse errors, merge conflicts, and missing parents.

![Practical example: defining a custom infantry unit diagram](images/Part_02_Chapter_01_MiniYaml-end-to-end-worked-example-diagram-showing-the-inputs-interme-5fc6a2.svg)

## Practical Example: Defining a Custom Infantry Unit


Suppose you want to add a new commando infantry unit named `e9` to the Red Alert mod. You can do this entirely with MiniYaml inheritance and overrides:

1. **Open the template.** In `mods/ra/rules/infantry.yaml`, most infantry inherit from `^Infantry` (defined in `mods/ra/rules/defaults.yaml`). The template already provides `Health`, `Mobile`, `RevealsShroud`, and other common traits.
2. **Create the concrete actor.** Add a new top-level node:
   ```yaml
   E9:
       Inherits: ^Infantry
       Inherits@AUTOTARGET: ^AutoTargetGroundAssaultMove
       Buildable:
           Queue: Infantry
           BuildPaletteOrder: 120
           Cost: 1000
       Valued:
           Cost: 1000
       Tooltip:
           Name: Commando
       Health:
           HP: 20000
       Mobile:
           Speed: 71
       Armament:
           Weapon: E9Rifle
       -TakeCover:
   ```
3. **Explain the inheritance.** `Inherits: ^Infantry` copies all of the template's children into `E9`. `Inherits@AUTOTARGET: ^AutoTargetGroundAssaultMove` adds a second inherited block without name collisions.
4. **Override fields.** `Health.HP: 20000` and `Mobile.Speed: 71` replace the inherited values. The parser merges these keys during `MergeSelfPartial`.
5. **Add a new trait.** `Armament:` adds a weapon slot that the template did not have.
6. **Remove an inherited trait.** `-TakeCover:` removes the prone/cover behavior that `^Infantry` included, so the commando never takes cover.
7. **Load and validate.** `Ruleset.LoadDefaults` calls `MiniYaml.Load`, which merges `defaults.yaml`, `infantry.yaml`, and any map overrides, resolves `Inherits`, then filters out `^` prefixed templates. The result is an [`ActorInfo`](../appendices/Appendix_A_Glossary.md) named `e9` containing the merged [`TraitInfo`](../appendices/Appendix_A_Glossary.md) collection.

This example shows how MiniYaml inheritance lets mod authors compose new units from shared templates without duplicating YAML or editing C#.

### Full Minimal Actor Example: A RECON Vehicle

The infantry example above showed inheritance and overrides in a single file. A complete, copy-pasteable vehicle also needs a sequence file and a `mod.yaml` manifest entry. This example assumes a small mod that inherits from the `common` mod (see [Part 10.3 — Porting, Modding, and Developer Workflows](Part_10_Chapter_03_Port_And_Modding.md)).

1. **Actor definition.** In `my-mod/rules/vehicles.yaml`:
   ```yaml
   RECON:
       Inherits: ^Vehicle
       Inherits@GAIN: ^GainsExperience
       Inherits@AUTOTARGET: ^AutoTargetGroundAssaultMove
       Buildable:
           Queue: Vehicle
           BuildPaletteOrder: 330
           Prerequisites: ~vehicles.allies, ~techlevel.low
       Valued:
           Cost: 600
       Tooltip:
           Name: Recon Buggy
       Health:
           HP: 15000
       Armor:
           Type: Light
       Mobile:
           Speed: 160
           Locomotor: wheeled
       RevealsShroud:
           Range: 7c0
       Armament@PRIMARY:
           Weapon: M1Carbine
           LocalOffset: 0,0,128
       AttackFrontal:
           FacingTolerance: 0
       WithFacingSpriteBody:
       RenderSprites:
           Image: recon
       Voiced:
           VoiceSet: VehicleVoice
   ```

2. **Sequence definition.** In `my-mod/sequences/vehicles.yaml`:
   ```yaml
   recon:
       Defaults:
           Filename: recon.shp
       idle:
           Facings: 32
           UseClassicFacings: True
       icon:
           Filename: reconicon.shp
   ```

3. **Manifest entries.** Add the files to `my-mod/mod.yaml`:
   ```yaml
   Rules:
       my-mod|rules/vehicles.yaml
   Sequences:
       my-mod|sequences/vehicles.yaml
   ```

4. **Key points.**
   - `Inherits` plus `Inherits@GAIN` and `Inherits@AUTOTARGET` show multiple inheritance without key collisions.
   - `Armament@PRIMARY` is a named trait instance; `Armament` and `AttackFrontal` add behavior the `^Vehicle` template does not provide.
   - `Health`, `Armor`, `Mobile`, `Tooltip`, `Valued`, and `Buildable` override or fill values inherited from `^Vehicle`.
   - The sequence key `recon` must match `RenderSprites.Image`.
   - The weapon name in `Armament@PRIMARY.Weapon` must exist in a loaded `Weapons:` file (e.g., `M1Carbine` from the inherited mod).

For a full recipe covering weapons, buildings, and support powers, see [Appendix E -- Practical Modding Recipes](../appendices/Appendix_E_Practical_Recipes.md).

## Files

| File | Responsibility |
| :---- | :---- |
| `OpenRA.Game/MiniYaml.cs` | **Single source of truth for the entire MiniYaml stack.** Contains `MiniYamlExts` (serialization), `MiniYamlNode` / `MiniYaml` (immutable AST), `MiniYamlNodeBuilder` / `MiniYamlBuilder` (mutable AST), `YamlException`, and all parse/merge/inheritance logic. |
| `OpenRA.Game/Exts.cs` | Extension helpers used by the parser: `HashSet<T>.GetOrAdd(...)` (string-pool helper), `IntoDictionaryWithConflictLog(...)` (duplicate-key conflict reporting). |
| `OpenRA.Game/StreamExts.cs` | `ReadAllLinesAsMemory(Stream)` — low-allocation line streaming that backs `MiniYaml.FromStream`. |
| `OpenRA.Game/GameRules/ActorInfo.cs` | Defines `AbstractActorPrefix` (`'^'`) and `TraitInstanceSeparator` (`'@'`), and documents the `^`/`@` conventions. |
| `OpenRA.Game/GameRules/Ruleset.cs` | Loads rules and filters out `^` prefixed abstract actors after inheritance resolution. |
| `OpenRA.Game/Graphics/SequenceSet.cs` | Filters out `^` prefixed abstract actors when loading sequences. |
| `OpenRA.Game/Settings.cs` | Uses `MiniYamlNodeBuilder` / `MiniYamlBuilder` for editable settings YAML. |
| `OpenRA.Test/OpenRA.Game/MiniYamlTest.cs` | Exhaustive behavioral tests for parsing, merging, inheritance, removals, comments, whitespace, and round-trips. |

Note: The requested files `MiniYamlNode.cs` and `MiniYamlExtensions.cs` do not exist as separate files in this repository; their contents are folded into `OpenRA.Game/MiniYaml.cs`.

![Architecture diagram](images/Part_02_Chapter_01_MiniYaml-architecture-diagram-showing-the-main-classes-interfaces-and-9161e6.svg)

## Architecture


### The Two AST Shapes

MiniYaml has two parallel representations:

![The Two AST Shapes](images/Part_02_Chapter_01_MiniYaml-Two_AST_Shapes.svg)

Immutable nodes are preferred for loaded rules because they are safe to share, cache, and compare by reference. `MiniYamlNodeBuilder` / `MiniYamlBuilder` exist only when the engine needs to mutate YAML in memory (e.g., `Settings.Commit`). Both shapes share the same line-oriented serialization in `MiniYamlExts.ToLines` and `MiniYaml.ToLines`.

### The Core Value Types

- `MiniYamlNode.SourceLocation` (`MiniYaml.cs`) is a small `readonly struct` holding the source file name and the 1-based line number. It is embedded in every node so diagnostics can report exactly where a conflict or missing parent originated.
- `MiniYaml.Value` (`MiniYaml.cs`) is the scalar after the colon. It is `null` for empty or whitespace-only values, not the empty string.
- `MiniYaml.Nodes` (`MiniYaml.cs`) is an `ImmutableArray<MiniYamlNode>`. Empty children use `ImmutableArray<MiniYamlNode>.Empty`.
- `MiniYaml` itself can be used as a synthetic root node: `new MiniYaml("", nodes)`.

### How OpenRA Uses the AST

- `Ruleset.LoadDefaults` / `Ruleset.Load` call `MiniYaml.Load(...)` to merge rule files and map overrides, then filter out `^` abstract templates.
- `ActorInfo` walks each actor's `MiniYaml` children and treats each child node as a trait instantiation (key = trait name, possibly with `@` suffix for a named instance).
- `FieldLoader` consumes individual `MiniYaml` subtrees to populate `TraitInfo` fields.

![Data flow  code path diagram](images/Part_02_Chapter_01_MiniYaml-sequence-flow-diagram-tracing-the-execution-path-from-trigge-035864.svg)

## Data Flow / Code Path


### 1. Parsing a Single File

```
MiniYaml.FromFile(path, discardCommentsAndWhitespace, stringPool)          [MiniYaml.cs]
  -> MiniYaml.FromStream(stream, name, ...)                               [MiniYaml.cs]
       -> StreamExts.ReadAllLinesAsMemory(stream)                         [StreamExts.cs]
       -> MiniYaml.FromLines(lines, name, discardCommentsAndWhitespace, stringPool)
            [MiniYaml.cs]
```

`FromLines` is the heart of the parser. It performs one pass over the input:

1. **Indentation scan** (`MiniYaml.cs`). Each line is scanned from the left. A space advances a counter; every 4 spaces increments one nesting level. A tab increments one level immediately. This means **tab and space indentation are not equivalent** — a tab is treated as a full indent level.
2. **Key / value / comment extraction** (`MiniYaml.cs`). The line is treated as `<key>: <value>#<comment>`. The first unescaped `:` separates key and value; the first unescaped `#` starts a comment. The `#` character is allowed in values if escaped as `\#`. Keys are always trimmed. Values are trimmed unless they start/end with a backslash followed by whitespace, which acts as a whitespace guard.
3. **String pooling** (`MiniYaml.cs`). Extracted key, value, and comment strings are canonicalized through a `HashSet<string>` via `GetOrAdd`, so identical strings share one instance.
4. **Node building** (`MiniYaml.cs`). Parsed lines are kept in a stack (`parsedLines`). When a line is less indented than the previous one, the parser closes the deeper node and attaches its children. Children are stored in a `result[level]` list, so parent/child relationships are resolved without recursion or lookahead. Top-level nodes are yielded as soon as they are completed.

### 2. Loading and Merging Multiple Files

```
MiniYaml.Load(fileSystem, files, mapRules)                                [MiniYaml.cs]
  -> Create a single string pool                                            [MiniYaml.cs]
  -> For each file: MiniYaml.FromStream(..., stringPool)                    [MiniYaml.cs]
  -> Append mapRules.Nodes if present                                       [MiniYaml.cs]
  -> MiniYaml.Merge(yaml)                                                   [MiniYaml.cs]
```

`Merge` (`MiniYaml.cs`) orchestrates the entire multi-file merge:

1. **Self-merge each source** (`MergeSelfPartial`, `MiniYaml.cs`). Within each file, duplicate keys are merged into a single node. This is what allows a file to define `Test:` twice and have the second occurrence extend the first.
2. **Partial merge across sources** (`MergePartial`, `MiniYaml.cs`). The self-merged sources are merged left-to-right using `MergePartial`. Later files override earlier files.
3. **Inheritance resolution** (`ResolveInherits`, `MiniYaml.cs`). The merged tree is walked; every `Inherits` or `Inherits@...` key is replaced by the resolved children of the named parent.
4. **Top-level removal resolution** (`ResolveInherits` on a synthetic root, `MiniYaml.cs`). This handles removing whole top-level nodes (e.g., removing an actor definition in a map override).

### 3. Converting YAML to Rules

```
Ruleset.LoadDefaults(modData)                                            [Ruleset.cs]
  -> MergeOrDefault("Manifest,Rules", fs, m.Rules, null, null,
       k => new ActorInfo(..., k.Value),
       filterNode: n => n.Key.StartsWith(ActorInfo.AbstractActorPrefix))
                                                                   [Ruleset.cs]
```

After `MiniYaml.Merge` resolves inheritance, the `^` prefixed abstract templates are still present in the tree. `Ruleset` (and `SequenceSet`) filters them out before instantiating `ActorInfo` objects. This is why `^` templates are visible to inheritance but are not themselves real actors.

![Configuration (yaml) diagram](images/Part_02_Chapter_01_MiniYaml-annotated-yaml-snippet-diagram-showing-the-key-fields-and-ho-6a1b98.svg)

## Configuration (YAML)


### MiniYaml Grammar vs. Standard YAML

MiniYaml is a deliberately small subset of YAML:

- Only **block-style** mapping nodes are supported. There are no flow collections (`[...]`, `{...}`), no anchors/aliases, no tags, and no multi-line literal/folded scalars.
- Indentation is **significant**. A child is indented by one level more than its parent. The parser accepts either 4 spaces or one tab per level, but it does not enforce consistency between adjacent lines.
- A node is one line: `key: value # comment`. The colon is required. A line with only a key and a colon is valid and has a `null` value.
- Empty lines are ignored for structure but **count for line numbers** (`MiniYamlTest.cs`).
- Comments are preserved only when `discardCommentsAndWhitespace` is `false`.

### Example of a Simple Tree

```yaml
Actor:
    Trait:
        Field: value
```

Parses as:
- `MiniYamlNode` `Actor`
  - `Value.Value = null`
  - `Value.Nodes` contains one node `Trait`
    - `Value.Value = null`
    - `Value.Nodes` contains one node `Field`
      - `Value.Value = "value"`

### The `@` Separator — Trait Instances

`@` is defined as `ActorInfo.TraitInstanceSeparator` (`ActorInfo.cs`). It is **not parsed specially** by MiniYaml; it is just a character in the key. The semantic meaning is enforced by the consumers:

```yaml
Armament@PRIMARY:
    Weapon: M1Carbine
Armament@GARRISONED:
    Name: garrisoned
    Weapon: Vulcan
```

`ActorInfo.LoadTraitInfo` splits the key at `@`, takes the left part as the trait class name (`ArmamentInfo`), and assigns the right part as the trait instance name (`InstanceName`). This allows multiple instances of the same trait class on one actor. MiniYaml treats `Armament@PRIMARY` and `Armament@GARRISONED` as unrelated keys.

### The `^` Prefix — Abstract Templates

`^` is defined as `ActorInfo.AbstractActorPrefix` (`ActorInfo.cs`). It is also **not parsed specially** by MiniYaml; it is a naming convention. Nodes whose key starts with `^` are intended to be inherited but never instantiated directly:

```yaml
^Soldier:
    Inherits: ^ExistsInWorld
    Health:
        HP: 5000

E1:
    Inherits: ^Soldier
    Buildable:
        Queue: Infantry
```

`Ruleset` and `SequenceSet` skip `^` prefixed nodes after inheritance has been resolved. If you forget to filter them, the engine would try to create `ActorInfo("^soldier", ...)` which is not a real unit.

### The `Inherits` / `Inherits@...` Key

The only real inheritance operator in MiniYaml is the key `Inherits` or `Inherits@<label>` (`MiniYaml.cs`):

```yaml
E1:
    Inherits: ^Soldier
    Inherits@AUTOTARGET: ^AutoTargetGroundAssaultMove
```

- `Inherits:` is a single inheritance parent.
- `Inherits@<label>` allows multiple inheritance parents. The label is arbitrary and only exists to keep the key unique within the node's children so MiniYaml does not see it as a duplicate key.
- The value of the node is the **parent name** (e.g., `^Soldier`). It is looked up by name in the merged tree.

Note: In `ActorInfo` comments, the convention is described as `Inherits:` and `-TraitName:` for removal. The actual parsing of `Inherits` is done by `MiniYaml.ResolveInherits`, not by `ActorInfo`.

### The `-` Prefix — Removal Nodes

A node whose key starts with `-` removes a previously defined node. It is used at two different stages:

```yaml
E1:
    Inherits: ^Soldier
    -TakeCover:
    Buildable:
        Queue: Infantry
```

- During `WeakResolveRemovals` (`MiniYaml.cs`) within a single node list, a removal node removes a matching plain node.
- During `ResolveInherits` (`MiniYaml.cs`), a removal node in the child list removes a matching inherited node.
- `MergeNode` (`MiniYaml.cs`) appends removal nodes to the result rather than merging them, so removals can act as boundaries between duplicate plain nodes.

## Interconnectivity

- **Depends on:**
  - `OpenRA.Game/StreamExts.cs` for line streaming (`ReadAllLinesAsMemory`).
  - `OpenRA.Game/Exts.cs` for `GetOrAdd` and conflict logging (`IntoDictionaryWithConflictLog`).
- **Used by:**
  - `OpenRA.Game/GameRules/Ruleset.cs` and `ActorInfo.cs` for loading actor definitions.
  - `OpenRA.Game/Graphics/SequenceSet.cs` for loading sequences.
  - `OpenRA.Game/FieldLoader.cs` for deserializing YAML values into C# [trait](../appendices/Appendix_A_Glossary.md) fields.
  - `OpenRA.Game/Settings.cs` for persisting user settings.
  - `OpenRA.Game/Widgets/WidgetLoader.cs`, `ChromeMetrics.cs`, `ChromeProvider.cs`, and network/session code for chrome and network configuration.

![Algorithms diagram](images/Part_02_Chapter_01_MiniYaml-algorithm-diagram-or-pseudocode-flowchart-for-the-non-trivia-5983ed.svg)

## Algorithms


### MergeNode — Merging One Node into a List

`MergeNode` (`MiniYaml.cs`) is the rule for how a single node is incorporated into an output list:

1. If the node is a removal node (`key.StartsWith('-')`), append it unchanged.
2. If the key has not been seen before, append it unchanged.
3. If the key has been seen before, look for the most recent plain node and the most recent removal node for that key.
   - If a removal node is closer (higher index) than the plain node, append the new node instead of merging. This preserves the sequence: old node applied, then removed, then new node applied.
   - Otherwise, merge the new node into the existing plain node in place: `existing.Value = MergePartial(existing.Value, new.Value)`.

### MergePartial — Merging Two Subtrees

`MergePartial` (`MiniYaml.cs`) combines two `MiniYaml` values:

1. Run `WeakResolveRemovals` on both node lists.
2. Check for duplicate keys inside each list using `IntoDictionaryWithConflictLog` with the shared `ConflictScratch` dictionary. If duplicates remain, throw `YamlException`.
3. If either side is null, return the other side.
4. The scalar value comes from the override: `overrideNodes.Value ?? existingNodes.Value`.
5. The child nodes come from the node-level `MergePartial`.

### WeakResolveRemovals

`WeakResolveRemovals` (`MiniYaml.cs`) scans a single node list and removes any plain node that is preceded by a matching `-Key` node. It is "weak" because it does not throw if the target is missing; it simply removes whatever it finds. This is used inside `MergePartial` to clean up the operands before merging, and also during inheritance resolution.

### MergeSelfPartial

`MergeSelfPartial` (`MiniYaml.cs`) merges duplicate keys within a single source. This is the first stage of `Merge` and is what allows a single YAML file to define the same top-level actor multiple times:

```yaml
Test:
    A: 1
Test:
    B: 2
```

becomes one `Test` node with both `A` and `B`.

### ResolveInherits — Recursive Inheritance

`ResolveInherits` (`MiniYaml.cs`) recursively expands `Inherits` directives:

1. For each child node:
   - If the key is `Inherits` or starts with `Inherits@`, look up the parent name in the merged tree.
   - If the parent is missing, throw `YamlException`.
   - If the parent has already been inherited in the current chain, throw `YamlException` with the previous location.
   - Recursively resolve the parent's children, then merge each resolved child into the current output using `MergeIntoResolved`.
   - The inherited parent's children are placed *before* the child's own explicit nodes (so explicit nodes override inherited ones).
2. If a child key starts with `-`, remove a matching node from the current output list.
3. Otherwise, merge the child into the output list.

The `inherited` dictionary is an `ImmutableDictionary<string, SourceLocation>` so each recursion gets an immutable copy of the inheritance chain.

### String Pooling

`FromLines` accepts a `HashSet<string> stringPool` (`MiniYaml.cs`). If null, a local pool is created. Every key, value, and comment string is passed through `stringPool.GetOrAdd(...)` (`Exts.cs`). Because the pool is shared across an entire `MiniYaml.Load` call, the same string appearing in many files (e.g., `Health`, `Inherits`, `true`, `0`) is allocated only once. This is critical because parsed YAML values stay resident for the lifetime of the `Ruleset`.

### Top-Level Removal

`MiniYaml.Merge` wraps the fully merged tree in a synthetic `MiniYaml` root (`MiniYaml.cs`) and runs `ResolveInherits` on it. This allows a map override to remove a whole actor definition defined in the mod:

```yaml
- ActorThatShouldNotExist:
```

![Extension points diagram](images/Part_02_Chapter_01_MiniYaml-extension-hook-diagram-showing-the-interface-s-to-implement-b4a27b.svg)

## Extension Points


- **Custom file formats:** `MiniYaml.FromLines` accepts any `IEnumerable<ReadOnlyMemory<char>>`, so you can feed it pre-processed text without writing to disk.
- **Map overrides:** A map can supply `MiniYaml mapRules` and `MiniYaml mapSequences` to `MiniYaml.Load`. These are merged after the mod files, so map YAML wins.
- **Mutable editing:** Use `MiniYamlNodeBuilder` / `MiniYamlBuilder` to construct or edit YAML programmatically, then call `Build()` to obtain the immutable form.
- **Custom consumers:** The inheritance system is generic; any subsystem can call `MiniYaml.Merge` and then use `ToDictionary()` or `NodeWithKey()` to interpret the result.

![Common pitfalls  guardrails diagram](images/Part_02_Chapter_01_MiniYaml-checklist-infographic-style-diagram-summarizing-the-top-pitf-fb069e.svg)

## Common Pitfalls / Guardrails


### Indentation

- The parser uses `SpacesPerLevel = 4` (`MiniYaml.cs`) but a tab counts as one full level. Mixing tabs and spaces can produce surprising nesting if the counts do not align.
- A line that is indented more than one level deeper than the previous line causes `YamlException("Bad indent in miniyaml at ...")` (`MiniYaml.cs`).
- Empty lines are allowed between nodes and do not reset nesting.

### Duplicates and Merging

- Duplicates **within a single file** are allowed if the file is self-merged: `MergeSelfPartial` merges them.
- Duplicates **within a single node list that is not being merged with another list** cause a `YamlException` because `MergePartial` runs the conflict check. For example, two sibling nodes with the same key under the same parent that are not split by a removal will fail.
- Duplicates **across different files** are merged safely; later files override earlier files.
- Interleaving duplicate keys and removal nodes can suppress the duplicate error. See the test cases in `MiniYamlTest.cs`.

### Inheritance

- A parent referenced by `Inherits` must exist in the merged tree. If it is missing, the parser throws `YamlException` with the source location.
- Cyclic inheritance is detected by the `inherited` dictionary. The error message includes the previous location where the parent was inherited.
- Multiple inheritance is allowed via `Inherits@<label>`. Each label must be unique within the actor.
- Removals apply to inherited nodes as well as explicitly defined nodes, but the order matters. `ResolveInherits` processes children in order, so a removal node only removes nodes that have already been added to the output list.

### Comments and Whitespace

- A `#` in a value must be escaped as `\#` if it is not intended to start a comment. The parser replaces `\#` with `#` in the final value (`MiniYaml.cs`).
- When `discardCommentsAndWhitespace` is `true` (the default for most loads), comment lines and top-level comment-only nodes are dropped. The source line numbers of subsequent nodes are still correct because the parser counts every line.
- Whitespace at the start or end of a value can be preserved by placing a backslash before it: `key: \  value  \`. The backslash and the adjacent whitespace marker are stripped.
- Empty keys (` : value`) are allowed and result in `Key = null`. The node is ignored by `MergeSelfPartial` and `MergeNode` because they skip null keys.

### Performance

- `ConflictScratch` is a static `Dictionary<string, MiniYamlNode>` reused under a `lock` (`MiniYaml.cs`, `564-579`). This avoids allocating conflict dictionaries during merges, but it means `MergePartial` is not re-entrant.
- `NodeWithKeyOrDefault` and `IndexOfKey` / `LastIndexOfKey` avoid LINQ to keep hot paths fast.
- `ImmutableArray` is used for node storage because rules are read-mostly.
- Do not mutate `MiniYaml` or `MiniYamlNode` after creation; use the `With*` helpers or the mutable builders.

### The `^` Prefix is Not Magic to the Parser

MiniYaml does not treat `^` specially. `^Soldier` is just another key. If you forget to filter abstract nodes in your own loader, you will end up instantiating them. `Ruleset` and `SequenceSet` perform the filtering; custom loaders must do it themselves if needed.

### The `@` Separator is Not Magic to the Parser

`Armament@PRIMARY` is just a key. The parser does not know about traits. The split is done later by `ActorInfo.LoadTraitInfo` (`ActorInfo.cs`). This means `Merge` and inheritance operate on the full string, so two different `@` instances of the same trait are independent nodes.

## Summary

This chapter explains how OpenRA stores mod data in **[MiniYaml](../appendices/Appendix_A_Glossary.md)**, the custom YAML dialect that drives rules, sequences, weapons, and UI definitions.

After reading this chapter, you should be able to:

- Explain why OpenRA uses a custom [YAML](../appendices/Appendix_A_Glossary.md) dialect instead of a standard YAML parser.
- Describe the immutable `MiniYamlNode` / `MiniYaml` AST and the mutable `MiniYamlNodeBuilder` / `MiniYamlBuilder` variants.
- Trace the parsing pipeline from `MiniYaml.FromFile` through `FromLines` to a tree of nodes.
- Understand inheritance (`Inherits:`), multiple inheritance (`Inherits@NAME:`), and [trait](../appendices/Appendix_A_Glossary.md)/[actor](../appendices/Appendix_A_Glossary.md) removal (`-TraitName:`).
- Predict how duplicate keys within a file and later files in a manifest list override earlier definitions.
- Read and write MiniYaml for actors, traits, weapons, and sequences.
- Use `SourceLocation` to diagnose parse errors, merge conflicts, and missing parents.

If any of the concepts above feel unclear, review the relevant section before continuing. For source files and further reading, see the References section.


## References

- `OpenRA.Game/MiniYaml.cs` — Complete parser, AST, and merge/inheritance implementation.
- `OpenRA.Game/Exts.cs` — `GetOrAdd` and `IntoDictionaryWithConflictLog` helpers.
- `OpenRA.Game/StreamExts.cs` — `ReadAllLinesAsMemory` line streaming.
- `OpenRA.Game/GameRules/ActorInfo.cs` — `^` and `@` conventions, trait instantiation.
- `OpenRA.Game/GameRules/Ruleset.cs` — Rule loading and abstract-actor filtering.
- `OpenRA.Game/Graphics/SequenceSet.cs` — Sequence loading and abstract-actor filtering.
- `OpenRA.Game/Settings.cs` — Mutable `MiniYamlBuilder` usage for settings.
- `OpenRA.Test/OpenRA.Game/MiniYamlTest.cs` — Authoritative behavioral tests for edge cases.
- Online MiniYaml documentation: `https://github.com/OpenRA/OpenRA/wiki/MiniYAML` (engine wiki, verify for current edition).



### External resources

- [OpenRA traits reference](https://docs.openra.net/en/release/traits/)
## What to read next

- Now that you understand the MiniYaml grammar, AST, and inheritance rules, read [Part 2.2 — Manifest, ModData, Ruleset, and RulesetCache](Part_02_Chapter_02_Manifest.md) to learn how the engine uses MiniYaml files to assemble a complete mod.
- For the next step in the data pipeline, read [Part 2.3 — FieldLoader and Type Conversions](Part_02_Chapter_03_FieldLoader.md) to see how MiniYaml values are converted into C# trait and weapon fields.
- Now that you can read and write MiniYaml for actors and weapons, read [Part 2.4 — Rulesets, Actors, and Weapons](Part_02_Chapter_04_Rules_Weapons.md) to learn how `ActorInfo` and `WeaponInfo` are produced from the parsed YAML.