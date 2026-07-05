# Part 0 — Foundations: How to Use This Manual

## What OpenRA is

OpenRA is a real-time strategy (RTS) game engine that recreates and extends the classic Westwood/EA RTS games—Command & Conquer, Red Alert, Dune 2000, and Tiberian Sun—using modern, open-source technology. It is also a moddable engine: the same codebase that powers the official mods can be used to build entirely new RTS games.

OpenRA is not a monolithic game with hard-coded units. It is a **data-driven simulation engine**:

- The core engine is written in C# (.NET).
- Gameplay rules, units, weapons, maps, UI, and audio are defined in **[MiniYaml](../appendices/Appendix_A_Glossary.md)** files.
- Custom behavior is added through C# **traits** (plug-in components) that can be combined in YAML.
- Single-player missions and custom game modes are scripted in **Lua**.
- Multiplayer is deterministic and **lockstepped**: every client runs the same simulation and only player orders cross the network.

This architecture means that much of what looks like "game-specific code" is actually reusable engine machinery. A modder can change how a tank behaves without recompiling the engine, while an engine developer can add a new rendering feature that all mods inherit.

> **Version note:** This manual is current as of 2026-06-24 and reflects the OpenRA engine source at tag `playtest-20260222-76-g972c10ec80`. File paths and class names may change in newer engine versions, so always cross-check with the source tree or the official OpenRA docs.

![Learning objectives diagram](images/Part_00_Foundations-learning-objectives-summary-diagram-or-concept-map-showing-h-fe332a.svg)

## Learning Objectives


After studying this chapter, you should be able to:

- Explain what OpenRA is and how its data-driven engine architecture differs from a monolithic RTS.
- Identify the core technologies used by OpenRA (C#, MiniYaml, traits, Lua, lockstep networking).
- Match your goals to the recommended learning paths in the manual.
- Describe the foundational concepts of actors, traits, activities, orders, rulesets, determinism, and MiniYaml.
- Set up the recommended workflow for reading source code alongside the manual.
- Use the built-in tests, launch commands, and debug tools to verify changes.

## Who this manual is for

This manual has three audiences in mind:

1. **New contributors** who want to understand the engine before they open their first pull request.
2. **Modders** who want to go beyond tweaking YAML and understand *why* traits behave the way they do.
3. **Engine maintainers** who need a concise, source-grounded reference to subsystem architecture and extension points.

You do not need to read every chapter. The manual is organized so you can study it cover-to-cover or dip into specific subsystems.

![How to read this manual diagram](images/Part_00_Foundations-visual-learner-guide-showing-the-recommended-reading-paths-n-8e427b.svg)

## How to read this manual


### Chapter template

Every chapter follows the same structure:

| Section | Why it exists |
| :---- | :---- |
| **Purpose** | Tells you what the subsystem does and why it matters. |
| **Files** | Lists the key source files so you can read the code alongside the chapter. |
| **Architecture** | Explains the classes, interfaces, and relationships. |
| **Data Flow / Code Path** | Walks through the execution path from trigger to output. |
| **Configuration (YAML)** | Shows how MiniYaml controls the subsystem. |
| **Interconnectivity** | Points to upstream and downstream chapters. |
| **Algorithms** | Describes non-trivial logic in plain language. |
| **Extension Points** | Explains how to extend or override the subsystem. |
| **Common Pitfalls / Guardrails** | Lists mistakes, determinism rules, and performance constraints. |
| **References** | Source paths and related chapters. |

In addition to the chapters, the manual includes reference appendices you can dip into at any time:

- [Appendix A — Glossary](../appendices/Appendix_A_Glossary.md) — definitions of OpenRA terms.
- [Appendix B — Common YAML Patterns](../appendices/Appendix_B_Common_YAML_Patterns.md) — reusable MiniYaml snippets.
- [Appendix E — Practical Modding Recipes](../appendices/Appendix_E_Practical_Recipes.md) — copy-paste recipes for units, weapons, buildings, and support powers.
- [Appendix F — Testing Strategies](../appendices/Appendix_F_Testing.md) — unit tests, YAML validation, replay/sync testing, and performance testing.
- [Appendix H — Asset Visual Reference](../appendices/Appendix_H_Asset_Visual_Reference.md) — a categorical lookup of file formats, YAML definitions, and engine classes for every asset type.

The [Master Index](../MASTER_INDEX.md) provides a single-page overview of every chapter and appendix.

![Architecture at a glance diagram](images/Part_00_Foundations-layered-architecture-diagram-engine-mods-content-map-game-se-247021.svg)

## Architecture at a Glance


OpenRA is built as a stack of layers. The engine code is shared by every mod; each mod layers its own assets, rules, and missions on top; and a running game session is the combination of a selected mod, a loaded map, and the live simulation state.

![Architecture at a Glance](images/Part_00_Foundations-Architecture_at_a_Glance-1.svg)
One simulation step follows a simple pipeline. Input is turned into orders, orders are applied on the next lockstep frame, the world ticks every actor and trait, and the renderer draws the resulting world state. The full order lockstep path is covered in [Part 1.3 — World, OrderManager, and Orders](Part_01_Chapter_03_World_Orders.md) and [Part 9.1 — OrderManager and Lockstep Foundation](Part_09_Chapter_01_OrderManager.md); the rendering frame is covered in [Part 4.1 — Renderer, Sheet, and Sprite](Part_04_Chapter_01_Renderer.md).

![Architecture at a Glance](images/Part_00_Foundations-Architecture_at_a_Glance-2.svg)
## Your first 30 minutes with OpenRA

If you are new to OpenRA, do not start by reading the whole manual. Start with this 30-minute loop:

1. **Get a working mod.** Follow [Part 3.2 — Mod SDK Bootstrapping](Part_03_Chapter_02_SDK_Bootstrap.md) to clone the Mod SDK and launch the default mod.
2. **Open one actor YAML file.** In your mod's `rules/` or `mods/ra/rules/` folder, open `infantry.yaml` or `vehicles.yaml` and find a unit you recognize (e.g., `RIFLE` or `1TNK`).
3. **Change one number.** Double the `Speed` of a vehicle, or increase the `Range` of a weapon. Save the file.
4. **Run the game.** Use `./launch-game.sh` or `make run` and check your change in-game.
5. **Undo the change** (or keep it) and try a different trait name from the Traits reference in the official OpenRA docs.

This loop—read a rule, make a tiny change, see it in-game—is the fastest way to build intuition. The rest of the manual explains *why* each rule behaves the way it does, but the *what* and *how* come from hands-on experimentation.

For the SDK setup, see [Part 3.2 — Mod SDK Bootstrapping](Part_03_Chapter_02_SDK_Bootstrap.md); for trait definitions, see the [OpenRA Traits reference](https://docs.openra.net/en/release/traits/).

### Recommended tooling

A good editor and the right supporting tools make the first 30 minutes much smoother:

- **Visual Studio / VS Code:** Use the [C# Dev Kit](https://marketplace.visualstudio.com/items?itemName=ms-dotnettools.csdevkit) and the OpenRA extension for C# editing, and the [community Lua tutorial setup page](https://steamsdev.github.io/content/openratut/luaintro.html) for Lua mission work.
- **JetBrains Rider:** A fully featured alternative C# IDE available at https://www.jetbrains.com/rider/.
- **OpenRA map editor:** Launched from the game client; use it for basic map creation and editing.
- **Official docs:** Keep the [OpenRA playtest docs](https://docs.openra.net/en/playtest/) and the [Traits reference](https://docs.openra.net/en/release/traits/) open while you work.

![Your first custom trait (the 5-minute version) diagram](images/Part_00_Foundations-extension-hook-diagram-showing-the-interface-s-to-implement-b4a27b.svg)

## Your first custom trait (the 5-minute version)


A custom trait is the smallest C# change you can make to OpenRA. Here is a complete, minimal example that adds a condition when an actor's health drops below 50%. You can copy this pattern for almost any simple trait.

### The C# code

Create a new file in your mod project (e.g., `MyMod/Traits/GrantConditionOnLowHealth.cs`):

```csharp
using OpenRA.Mods.Common.Traits;
using OpenRA.Traits;

namespace MyMod.Traits
{
    [Desc("Grants a condition while the actor's health is below a threshold.")]
    public class GrantConditionOnLowHealthInfo : TraitInfo, Requires<IHealthInfo>
    {
        [FieldLoader.Require]
        [GrantedConditionReference]
        [Desc("Condition to grant when health is below the threshold.")]
        public readonly string Condition = null;

        [Desc("Health threshold, as a fraction of total HP (0-1).")]
        public readonly float Threshold = 0.5f;

        public override object Create(ActorInitializer init) { return new GrantConditionOnLowHealth(init.Self, this); }
    }

    public class GrantConditionOnLowHealth : INotifyCreated, INotifyDamage
    {
        readonly GrantConditionOnLowHealthInfo info;
        readonly IHealth health;

        int conditionToken = Actor.InvalidConditionToken;

        public GrantConditionOnLowHealth(Actor self, GrantConditionOnLowHealthInfo info)
        {
            this.info = info;
            health = self.Trait<IHealth>();
        }

        void INotifyCreated.Created(Actor self)
        {
            UpdateCondition(self);
        }

        void INotifyDamage.Damaged(Actor self, AttackInfo e)
        {
            UpdateCondition(self);
        }

        void UpdateCondition(Actor self)
        {
            var lowHealth = health.HP < health.MaxHP * info.Threshold;
            var granted = conditionToken != Actor.InvalidConditionToken;

            if (lowHealth && !granted)
                conditionToken = self.GrantCondition(info.Condition);
            else if (!lowHealth && granted)
                conditionToken = self.RevokeCondition(conditionToken);
        }
    }
}
```

### The YAML registration

Add the trait to an actor definition:

```yaml
MyUnit:
    Inherits: ^Infantry
    Health:
        HP: 5000
    GrantConditionOnLowHealth:
        Condition: damaged
        Threshold: 0.5
    # ... other traits can now react to the `damaged` condition, e.g.:
    # SpeedMultiplier@DAMAGED:
    #     Modifier: 75
    #     RequiresCondition: damaged
```

### Build and test

1. Make sure your mod project file includes the new `.cs` file.
<!-- DEV-NOTE [tooling]: Microsoft .NET SDK: https://dotnet.microsoft.com — required to build the OpenRA engine and mod projects. -->
2. Run `make` or `dotnet build` to compile the mod assembly.
3. Launch the game with your mod and spawn the unit.
4. Attack the unit until its health drops below 50%; the `damaged` condition should now be active.

For a full walkthrough with debugging tips, see [Appendix E — Practical Modding Recipes](../appendices/Appendix_E_Practical_Recipes.md). For a deeper explanation of the trait lifecycle, see [Part 1.1 — Entity-Component-System (ECS) and Actor Lifecycle](Part_01_Chapter_01_ECS.md).

### Suggested learning paths

**If you want to make a new unit or modify weapons (start here):**
- [Part 0 — Foundations: How to Use This Manual](Part_00_Foundations.md) → [Part 2.1 — MiniYaml Parser and Inheritance](Part_02_Chapter_01_MiniYaml.md) → [Part 2.4 — Rulesets, Actors, and Weapons](Part_02_Chapter_04_Rules_Weapons.md) → [Part 1.1 — Entity-Component-System (ECS) and Actor Lifecycle](Part_01_Chapter_01_ECS.md) → [Part 1.5 — Pathfinding and Movement](Part_01_Chapter_05_Pathfinding_Movement.md) → [Part 1.6 — Combat and Damage Resolution](Part_01_Chapter_06_Combat_Damage.md) → [Part 10.3 — Porting, Modding, and Developer Workflows](Part_10_Chapter_03_Port_And_Modding.md) → [Appendix E — Practical Modding Recipes](../appendices/Appendix_E_Practical_Recipes.md).

**If you want to add AI behavior:**
- [Part 1.1 — Entity-Component-System (ECS) and Actor Lifecycle](Part_01_Chapter_01_ECS.md) → [Part 1.3 — World, OrderManager, and Orders](Part_01_Chapter_03_World_Orders.md) → [Part 8.1 — IBot and ModularBot](Part_08_Chapter_01_IBot.md) → [Part 8.2 — Bot Modules](Part_08_Chapter_02_Bot_Modules.md) → [Part 8.3 — Bot Squads and Combat Heuristics](Part_08_Chapter_03_Squads.md) → [Part 8.4 — Bot Order Flow](Part_08_Chapter_04_Order_Flow.md).

**If you want to work on graphics or UI:**
- [Part 4.1 — Renderer, Sheet, and Sprite](Part_04_Chapter_01_Renderer.md) → [Part 4.2 — WorldRenderer](Part_04_Chapter_02_WorldRenderer.md) → [Part 4.3 — Widgets and Chrome](Part_04_Chapter_03_Widgets.md) → [Part 4.4 — Viewport and Input](Part_04_Chapter_04_Viewport_Input.md).

**If you want to work on multiplayer/networking:**
- [Part 1.3 — World, OrderManager, and Orders](Part_01_Chapter_03_World_Orders.md) → [Part 9.1 — OrderManager and Lockstep Foundation](Part_09_Chapter_01_OrderManager.md) → [Part 9.2 — Server and Connection Layer](Part_09_Chapter_02_Server_Connection.md) → [Part 9.3 — Sync Hashing and Determinism](Part_09_Chapter_03_Sync_Hashing.md).

**If you want to create missions or scripted game modes:**
- [Part 6.1 — Lua Scripting and Eluant](Part_06_Chapter_01_Lua_Eluant.md) → [Part 6.2 — ScriptContext Lifecycle and Bindings](Part_06_Chapter_02_ScriptContext.md) → [Part 6.3 — Virtual File System](Part_06_Chapter_03_VFS.md) → [Part 10.3 — Porting, Modding, and Developer Workflows](Part_10_Chapter_03_Port_And_Modding.md).

**If you want to create a new mod:**
- [Part 3.1 — Mod SDK and Project Structure](Part_03_Chapter_01_Mod_SDK.md) → [Part 3.2 — Mod SDK Bootstrapping](Part_03_Chapter_02_SDK_Bootstrap.md) → [Part 3.3 — Build Pipeline and Packaging](Part_03_Chapter_03_Build_Packaging.md) → [Part 10.1 — Official Mods](Part_10_Chapter_01_Official_Mods.md) → [Part 10.3 — Porting, Modding, and Developer Workflows](Part_10_Chapter_03_Port_And_Modding.md).

## Key concepts you should know first

### Actors and Traits

An **[Actor](../appendices/Appendix_A_Glossary.md)** is an object in the game world: a tank, a building, a projectile, a crate, a player, or the world itself. An actor by itself is empty. All behavior comes from **[Traits](../appendices/Appendix_A_Glossary.md)** attached to it.

A **Trait** is a C# class instance that lives on the actor. Traits implement marker interfaces (e.g., `ITick`, `IResolveOrder`, `IRender`) so the engine can call them at the right time.

Each trait has a **[TraitInfo](../appendices/Appendix_A_Glossary.md)** counterpart: an immutable configuration object loaded from YAML. `HealthInfo` becomes `Health` on every spawned actor.

See [Part 1.1 — Entity-Component-System (ECS) and Actor Lifecycle](Part_01_Chapter_01_ECS.md) for the full explanation.

### Activities

An **[Activity](../appendices/Appendix_A_Glossary.md)** is a queued task for an actor: move to a cell, attack a target, play a death animation, wait, etc. Activities form a stack. The actor ticks the topmost activity each frame.

See [Part 1.2 — Activities and the Game Loop](Part_01_Chapter_02_Activities.md) for details.

### Orders

An **[Order](../appendices/Appendix_A_Glossary.md)** is the only thing that crosses from the unsynced world (UI, AI, input) into the deterministic simulation. Every player action and bot action is packaged as an `Order` and executed on the next lockstep frame.

See [Part 1.3 — World, OrderManager, and Orders](Part_01_Chapter_03_World_Orders.md) and [Part 9.1 — OrderManager and Lockstep Foundation](Part_09_Chapter_01_OrderManager.md)

### Rulesets

A **[Ruleset](../appendices/Appendix_A_Glossary.md)** is the immutable set of actor definitions, weapons, voices, notifications, music, and terrain info loaded for a map. It is the boundary between YAML content and the C# simulation.

See [Part 2.4 — Rulesets, Actors, and Weapons](Part_02_Chapter_04_Rules_Weapons.md).

### Determinism and sync

Because OpenRA uses lockstep multiplayer, the simulation must produce exactly the same result on every client. Anything that affects gameplay must be deterministic and must be included in the **sync hash**.

See [Part 9.3 — Sync Hashing and Determinism](Part_09_Chapter_03_Sync_Hashing.md).

### MiniYaml

MiniYaml is OpenRA's configuration format. It is a simplified, indented markup used for rules, weapons, sequences, UI layouts, and more. It supports inheritance, overrides, and node removal.

See [Part 2.1 — MiniYaml Parser and Inheritance](Part_02_Chapter_01_MiniYaml.md).

## How to use the source code alongside this manual

Every chapter lists the files it discusses. You should open those files in your editor and read them as you go. The manual is designed to be a **guided tour** of the source, not a replacement for it.

Recommended setup:

1. Clone the OpenRA repository.
2. Open the solution in your IDE.
3. When a chapter mentions a file, jump to it and read the relevant lines.
4. Use the search terms in the chapter to find related code.

## How to verify your understanding

- Run `make test` or `./utility.sh <mod> --check-yaml` after changing YAML.
- Launch the game with a specific mod: `./launch-game.sh Game.Mod=ra`.
- Use the in-game debug menu (F12) to visualize terrain grids, paths, actor bounds, and screen partitions.
- Read the unit tests in `OpenRA.Test` for examples of how engine systems are validated.
- Try small exercises: create a custom unit, add a trait, modify a sequence, or write a tiny Lua script.

## Conventions used in this manual

- Code paths are written as `Project/Directory/File.cs` relative to the repository root.
- Line references are approximate; they may shift between engine versions.
- `YAML` examples are illustrative; always check the official mods for exact syntax.
- `Part X.Y` refers to chapter `Y` of part `X`.

## Where to go next

**If you have never modified OpenRA before**, start with **Your first 30 minutes with OpenRA** above, then read **[Part 1.1 — Entity-Component-System (ECS) and Actor Lifecycle](Part_01_Chapter_01_ECS.md)**. That chapter is the foundation for everything else.

**If you want to change units or weapons quickly**, read **[Part 2.4 — Rulesets, Actors, and Weapons](Part_02_Chapter_04_Rules_Weapons.md)**, then **[Appendix E — Practical Modding Recipes](../appendices/Appendix_E_Practical_Recipes.md)**.

**If you want to write a custom trait in C#**, read **[Part 1.1 — Entity-Component-System (ECS) and Actor Lifecycle](Part_01_Chapter_01_ECS.md)**, then **[Appendix E — Practical Modding Recipes](../appendices/Appendix_E_Practical_Recipes.md)** for the full recipe, and **[Part 3.1 — Mod SDK and Project Structure](Part_03_Chapter_01_Mod_SDK.md)**/**[Part 3.2 — Mod SDK Bootstrapping](Part_03_Chapter_02_SDK_Bootstrap.md)** for SDK setup.

**If you are returning to look up a specific subsystem**, use the **Master Index** in `build files/MASTER_INDEX.md` or the **Chapter Index** in `build files/README.md`.

## Summary

- This manual is a source-grounded tour of the OpenRA engine. It is meant to be read alongside the pinned engine source at tag `playtest-20260222-76-g972c10ec80`.
- OpenRA is an actor/trait ECS. Every game object is an `Actor`; all behavior comes from `Trait` instances configured by immutable `TraitInfo` objects loaded from MiniYaml.
- Activities queue deterministic work, Orders are the only cross from the unsynced UI/AI world into the lockstep simulation, and Rulesets are the immutable boundary between YAML content and the C# engine.
- The manual is organized into Parts 0–10 plus appendices. Suggested learning paths are provided above for new modders, AI authors, graphics/UI contributors, networking developers, and mission scripters.
- When you want to go deeper, open the source files listed in each chapter and read them alongside the chapter text.

## What to read next

- If you want to understand how actors and traits are constructed, read [Part 1.1 — Entity-Component-System (ECS) and Actor Lifecycle](Part_01_Chapter_01_ECS.md).
- If you want to learn how OpenRA parses MiniYaml rules, read [Part 2.1 — MiniYaml Parser and Inheritance](Part_02_Chapter_01_MiniYaml.md).
- If you want to set up a standalone mod project, read [Part 3.1 — Mod SDK and Project Structure](Part_03_Chapter_01_Mod_SDK.md).