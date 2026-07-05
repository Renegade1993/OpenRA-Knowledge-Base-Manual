# Appendix C — Debugging and Troubleshooting

This appendix is a practical guide for diagnosing problems in OpenRA. It covers the tools, log files, debug overlays, and systematic approaches that help you find and fix bugs in the engine, in a mod, or in a map.

## Logs

OpenRA writes logs to the `Logs/` directory under the engine folder (or the user data folder on some platforms). Important log channels:

| File | Contents |
| :---- | :---- |
| `debug.log` | General debug messages, warnings, and errors. |
| `server.log` | Dedicated server output and network events. |
| `lua.log` | Lua script output and errors. |
| `perf.log` | Performance timings and frame statistics. |
| `audio.log` | Audio initialization and playback issues. |
<!-- DEV-NOTE [tooling]: Khronos GLSL reference: https://www.khronos.org/opengl/wiki/OpenGL_Shading_Language — reference for the shader dialect used by the engine. -->
| `graphics.log` | Renderer and shader errors. |
| `sync.log` | Sync report data when sync reports are enabled. |

You can add custom log output from code:

```csharp
Log.Write("debug", "My debug message: {0}", value);
```

### Log file quick reference

Use the following channels to narrow down a problem quickly.

| Channel | What to look for | When to check |
| :---- | :---- | :---- |
| `debug` | Exception stack traces, [trait](Appendix_A_Glossary.md) load warnings, YAML parse errors, invalid trait/field names, and unhandled order strings. | Crashes on startup, trait misconfiguration, order resolution failures, or any unknown error. |
| `server` | Client connects/disconnects, malformed packets, ping spikes, order latency, and dropped frames. | Network stalls, [desyncs](Appendix_A_Glossary.md), or players dropping unexpectedly. |
| `lua` | `print()` output, "Fatal Lua Error" messages, script context disables, and stack traces from [Lua scripts](Appendix_A_Glossary.md). | Scripted missions that do not trigger, fail to spawn actors, or stop running. |
| `graphics` | Renderer initialization failures, missing shaders, texture upload errors, and sprite sheet problems. | Invisible sprites, black screens, palette errors, or GPU crashes. |
| `perf` | Frame timings, tick durations, and `PerfSample` markers for slow subsystems. | Frame drops, stuttering, or long simulation ticks. |
| `sync` | Per-actor and per-trait [sync hashes](Appendix_A_Glossary.md) when sync reports are enabled. | Multiplayer desyncs; compare reports from two clients to find the first diverging trait. |

## The in-game debug menu

Press **F12** in-game to open the debug menu. It can show:

- **Terrain grid** — outlines map cells.
- **Pathfinding cost field** — shows path costs and blocked cells.
- **Actor bounds** — shows selection and collision boxes.
- **Screen map partitions** — shows the spatial partitioning grid.
- **Render geometry** — shows sprite bounds and origins.
- **Depth buffer** — visualizes the depth buffer (isometric mods).

These overlays help you understand why a unit is pathing somewhere, why an actor is not visible, or why a sprite is drawn incorrectly.

### Debug overlays quick reference

| Overlay | What it shows | Use it when |
| :---- | :---- | :---- |
| **Terrain grid** | Map cell boundaries and cell coordinates. | A unit clips the wrong cell, a building footprint is misaligned, or path destinations look off by one cell. |
| **Pathfinding cost field** | Blocked cells, terrain costs, and reachable regions per locomotor. | A unit refuses to move, takes a strange route, or cannot reach a destination that looks open. |
| **Actor bounds** | Selection boxes, collision boxes, and targetable hit shapes. | An actor is hard to select, projectiles miss or hit unexpectedly, or crush rules behave oddly. |
| **Screen map partitions** | The spatial grid used to partition actors for rendering and queries. | Too many actors are being iterated, performance is poor, or effects are not visible at the edges of the screen. |
| **Render geometry** | Sprite bounds, origins, and Z-order offsets. | A sprite is invisible, drawn at the wrong scale, or layered behind terrain it should be in front of. |
| **Depth buffer** | Isometric depth values used by the renderer. | Depth fighting, sprites drawn on the wrong plane, or transparency ordering issues. |
| **Sync reports** | Live sync hashes for the world and selected actors when sync reports are enabled. | A multiplayer desync is suspected and you need to confirm which objects differ. |

![Decision trees for common problems diagram](images/Appendix_C_Debugging-debugging-decision-tree-or-flowchart-for-the-most-common-fai-8aeea8.svg)

## Decision trees for common problems


Decision trees help you isolate a bug by following a short series of yes/no checks. Each path ends in the most likely cause.

### My unit won't move

1. Does the actor have a `Mobile` trait?
   - **No.** Add `Mobile` and link it to a valid `Locomotor` name.
   - **Yes.** Continue.
2. Does the actor's `Locomotor` have `TerrainSpeeds` entries for the terrain it is on?
   - **No.** Add `TerrainSpeeds` for that terrain type in `OpenRA.Mods.Common/Traits/World/Locomotor.cs` rules or YAML, or move the actor to valid terrain.
   - **Yes.** Continue.
3. Is the destination on the same pathfinding domain and not blocked by immovable actors or terrain?
   - **No.** Use the terrain grid and pathfinding cost field overlays to see blocked cells; check that the destination is reachable by that locomotor.
   - **Yes.** Continue.
4. Is the actor currently disabled by a status condition, loaded into cargo, or falling from a parachute?
   - **Yes.** Wait for the condition to clear, or check the condition granting logic in the actor's rules.
   - **No.** Continue.
5. Is the actor already running an [activity](Appendix_A_Glossary.md) that prevents movement, such as an attack-chase loop or a `Turn` activity?
   - **Yes.** Inspect the activity queue and the order that started it.
   - **No.** Continue.
6. Is the destination inside unrevealed shroud and the locomotor does not allow `MoveIntoShroud`?
   - **Yes.** Reveal the area or set `MoveIntoShroud: true` on the locomotor if appropriate.
   - **No.** Look at `debug.log` for path errors, then step through `Move` in `OpenRA.Mods.Common/Activities/Move/Move.cs`.

### My weapon doesn't fire

1. Does the actor have an `Armament` and an attack trait such as `AttackFrontal` or `AttackTurreted`?
   - **No.** Add the missing trait and ensure the armament `Name` matches the attack trait's weapon slot.
   - **Yes.** Continue.
2. Does the weapon's `ValidTargets` include at least one of the target's `Targetable` target types?
   - **No.** Adjust `ValidTargets` on the weapon or the target's `Targetable` types.
   - **Yes.** Continue.
3. Is the target within the weapon's `Range`?
   - **No.** Move the attacker closer, or increase the weapon range if the design requires it.
   - **Yes.** Continue.
4. Does the armament have a `ReloadDelay` or burst cooldown that has not elapsed?
   - **Yes.** Wait for the reload; verify the timing in the weapon definition.
   - **No.** Continue.
5. For `AttackFrontal` or `AttackTurreted`, is the actor or turret facing the target?
   - **No.** Check `TurnSpeed` and `IdleTurnSpeed`; the actor may be stuck turning.
   - **Yes.** Continue.
6. Does the warhead's `ValidTargets` or `ValidRelationships` exclude the target?
   - **Yes.** Update the warhead in `OpenRA.Mods.Common/Warheads/Warhead.cs` or derived types.
   - **No.** Continue.
7. Is the target visible to the owning player, or does the weapon allow firing into shroud?
   - **No.** Reveal the target or adjust the weapon/attack traits.
   - **Yes.** Set a breakpoint in `Armament.CheckFire` in `OpenRA.Mods.Common/Traits/Armament.cs` and trace the failure.

### My trait isn't loading

1. Is the trait name spelled exactly as it appears in the C# class name (without the `Info` suffix) or in the YAML name mapping?
   - **No.** Fix the typo in the actor or world rules.
   - **Yes.** Continue.
2. If the trait is custom, is the mod assembly listed in `mod.yaml` `Assemblies` and is the class public?
   - **No.** Register the assembly or make the trait class public.
   - **Yes.** Continue.
3. Is the trait placed on the right kind of actor? Some traits must be on the world actor, on a player actor, or on a regular actor.
   - **No.** Move the trait to the correct actor type.
   - **Yes.** Continue.
4. Does the trait depend on another trait that is missing? For example, `Mobile` requires a `Locomotor` and `AttackFrontal` requires an `Armament`.
   - **Yes.** Add the prerequisite trait or check that it was not removed by an earlier rule.
   - **No.** Continue.
5. Is the trait explicitly removed by a `-TraitName` rule before it is redefined?
   - **Yes.** Reorder or simplify the inheritance chain; removals must happen before the trait is added again.
   - **No.** Continue.
6. Does running `--check-yaml` report a field error or missing interface?
   - **Yes.** Fix the reported YAML or C# interface mismatch.
   - **No.** Check `debug.log` for an exception during trait creation and inspect the trait constructor in the source.

### I'm investigating a desync

1. Did the out-of-sync message appear during a multiplayer game?
   - **No.** A single-player crash is not a desync; treat it as a normal exception.
   - **Yes.** Continue.
2. Are all clients running the same engine, mod, and map versions with no local file edits?
   - **No.** Synchronize versions and restart.
   - **Yes.** Continue.
3. Was `EnableSyncReports` enabled in the lobby *before* the desync happened?
   - **No.** Enable it, reproduce the desync, and compare the resulting `sync.log` files.
   - **Yes.** Continue.
4. Do the `sync.log` files from both clients diverge at a specific actor or trait?
   - **No.** The desync may be in the world hash, settings, or mod data; check the earliest hash difference.
   - **Yes.** Continue.
5. Does the diverging trait use `world.LocalRandom` instead of `world.SharedRandom`?
   - **Yes.** Replace `LocalRandom` with `SharedRandom` for any simulation-affecting decision.
   - **No.** Continue.
6. Does the trait iterate over dictionaries, hash sets, or other unordered collections without sorting?
   - **Yes.** Sort the collection by a stable key, or iterate over an ordered structure such as a list.
   - **No.** Continue.
7. Does the trait run inside `Sync.RunUnsynced` but change world state, actor state, or synced fields?
   - **Yes.** Move the mutation out of `RunUnsynced` and mark the changed fields with `[VerifySync]` if they affect gameplay.
   - **No.** Continue.
8. Does the trait use `float` or `double` math in the simulation path?
   - **Yes.** Convert to fixed-point math (`WPos`, `WDist`, `WAngle`, `WVec`, `int`) or ensure the result is fully deterministic across platforms.
   - **No.** Continue.
9. Does the trait read client-only state such as camera position, selection, or UI settings?
   - **Yes.** Gate that code behind client-only logic and never let it affect the simulation.
   - **No.** Continue to the Top 10 desync causes list and review each item.

![Timeline/frame diagram of the lockstep order/sync path, showing order ](images/Appendix_C_Debugging-timeline-frame-diagram-of-the-lockstep-order-sync-path-showi-a5bb06.svg)

## Top 10 desync causes


Most multiplayer desyncs come from a small set of mistakes. Work through this list when the decision tree above does not immediately point to the cause.

| # | Cause | What to do |
| :---- | :---- | :---- |
| 1 | Using `world.LocalRandom` for gameplay-affecting decisions. | Use `world.SharedRandom` anywhere the result changes simulation state. |
| 2 | Iterating over dictionaries or hash sets without deterministic ordering. | Sort by a stable key, or use ordered collections in synced code paths. |
| 3 | Modifying simulation state from UI or unsynced code. | Keep world mutations inside simulation ticks; use `Sync.RunUnsynced` only for read-only or client-side effects. |
| 4 | Missing `[VerifySync]` on gameplay fields that affect the outcome. | Implement `ISync` and mark fields that must be identical on every client. |
| 5 | Floating-point math (`float`/`double`) in simulation code. | Prefer fixed-point types and integer math; isolate any floats and test across CPUs. |
| 6 | Bot logic or AI modules that differ between clients or read client-only state. | Run bot decisions in `RunUnsynced` only if they do not mutate state; keep bot state synced if it matters. |
| 7 | Reading client-only state such as camera, selection, or settings in simulation code. | Pass simulation-relevant data through orders or synced fields, not from client state. |
| 8 | Culture-dependent parsing of strings or numbers. | Use `CultureInfo.InvariantCulture` or OpenRA's parse helpers for any string-to-number conversion. |
| 9 | Different mod/map versions or modified data files across clients. | Verify checksums and ensure every client uses the same release. |
| 10 | Race conditions between simulation and rendering, or unguarded shared state. | Mutate state only on the simulation thread; protect shared state with locks if it is truly shared. |

## Utility commands for validation

```bash
./utility.sh ra --check-yaml
./utility.sh ra --check-missing-sprites
./utility.sh ra --check-missing-sequences
./utility.sh all --check-explicit-interfaces
./utility.sh all --check-conditional-trait-interface-overrides
./utility.sh all --check-referenced-sequences
```

Run these after changing YAML, sequences, or traits. They catch many errors before launch.

## Common problem: crash on startup

1. Check `debug.log` for the exception stack trace.
2. Identify whether the crash is in engine code, mod YAML, or a custom assembly.
3. If the crash mentions a trait name, check the actor's YAML for malformed fields.
4. If the crash is in a custom assembly, ensure it is built against the correct engine version.
5. Run `--check-yaml` to validate the mod.

![Timeline/frame diagram of the lockstep order/sync path, showing order ](images/Appendix_C_Debugging-timeline-frame-diagram-of-the-lockstep-order-sync-path-showi-a5bb06.svg)

## Common problem: desync in multiplayer


1. Enable `EnableSyncReports` in the lobby settings.
2. Reproduce the desync.
3. Compare `sync.log` files from both clients.
4. Find the first actor/trait whose hash differs.
5. Investigate the trait for:
   - Use of `world.LocalRandom` instead of `world.SharedRandom`.
   - Floating-point math (`float`/`double`).
   - Non-deterministic iteration order (e.g., over dictionaries).
   - Culture-dependent string parsing.
   - Code that runs in a `RunUnsynced` block but mutates state.

**See:** [Part 9.3 — Sync Hashing and Determinism](../chapters/Part_09_Chapter_03_Sync_Hashing.md) and the "I'm investigating a desync" decision tree and Top 10 desync causes above.

## Common problem: unit does not move or attack

1. Check that the actor has `Mobile` and `AttackFrontal` (or equivalent) traits.
2. Check that the `RevealsShroud` or `RevealsFog` trait covers the target area.
3. Check that the weapon's `ValidTargets` includes the target's target type.
4. Check that the locomotor's `TerrainSpeeds` allows movement on the terrain.
5. Use the pathfinding debug overlay to see if the destination is reachable.

**See:** [Part 1.5 — Pathfinding and Movement](../chapters/Part_01_Chapter_05_Pathfinding_Movement.md) and [Part 1.6 — Combat and Damage Resolution](../chapters/Part_01_Chapter_06_Combat_Damage.md).

## Common problem: sprite is invisible or wrong

1. Check that the sequence name is correct and the sprite file is loaded.
2. Check the `ZOffset` and `RenderSprites` settings.
3. Check the palette name for indexed sprites.
4. Use the render geometry debug overlay to see if the sprite is off-screen or scaled incorrectly.
5. Check `graphics.log` for texture upload errors.

## Common problem: bot does nothing

1. Check that the `Player` actor has `ModularBot` and the desired bot modules.
2. Check that the AI's `BuildingFractions` or `UnitsToBuild` reference valid actor names.
3. Check that the bot has a valid construction yard or factory.
4. Check `lua.log` if the map uses custom scripts that override bot behavior.
5. Enable debug logs for the bot modules.

## Common problem: YAML not applied as expected

1. Check inheritance order. Later files override earlier files.
2. Check that `Inherits` keys are keyed (`Inherits@1`) when using multiple inheritance.
3. Check that `-TraitName` removals are applied before the trait is redefined.
4. Check for typos in trait or field names.
5. Run `--check-yaml` to see the merged result.

![Debugging with an ide diagram](images/Appendix_C_Debugging-debugging-decision-tree-or-flowchart-for-the-most-common-fai-8aeea8.svg)

## Debugging with an IDE


<!-- DEV-NOTE [tooling]: Microsoft .NET SDK: https://dotnet.microsoft.com — required to build the OpenRA engine and mod projects. -->
1. Open the OpenRA solution in Visual Studio, Rider, or VS Code.
2. Set a breakpoint in the relevant trait or world code.
3. Launch the game in debug mode.
4. Reproduce the issue.
5. Inspect the call stack, variables, and trait state.

![Debugging lua scripts diagram](images/Appendix_C_Debugging-debugging-decision-tree-or-flowchart-for-the-most-common-fai-8aeea8.svg)

## Debugging Lua scripts


1. Use `print("message")` in the script.
2. Check `lua.log` for output.
3. Watch for "Fatal Lua Error" messages that disable the script context.
4. Use the `World` and `Map` globals to inspect state.
5. Test scripts incrementally; Lua errors are fatal to the script context.

## Performance profiling

1. Enable `PerfGraph` in settings if available.
2. Check `perf.log` for frame timings.
3. Use `PerfSample` in code to measure sections:

```csharp
using (new PerfSample("my section"))
{
    // code to measure
}
```

4. Common slow paths:
   - Pathfinding on large maps.
   - Too many actors or effects.
   - Inefficient trait queries in tight loops.
   - Large Lua scripts or frequent Lua calls.

![Network debugging diagram](images/Appendix_C_Debugging-debugging-decision-tree-or-flowchart-for-the-most-common-fai-8aeea8.svg)

## Network debugging


1. Enable `EnableSyncReports` in the lobby.
2. Check `server.log` for disconnects, malformed packets, or ping failures.
3. Use `OrderManager.IsReadyForNextFrame` to diagnose stalls.
4. Verify that all clients have the same mod and map versions.

![Useful debugging tips diagram](images/Appendix_C_Debugging-debugging-decision-tree-or-flowchart-for-the-most-common-fai-8aeea8.svg)

## Useful debugging tips


- **Start small:** when testing a new trait or weapon, create a minimal actor that uses only that feature.
- **Use the mod chooser:** run `./launch-game.sh` without arguments to choose the mod and map.
- **Isolate maps:** copy a map to a test directory and edit it without affecting the main mod.
- **Read the stack trace:** OpenRA's logs usually include enough context to pinpoint the subsystem.
- **Check official mods:** compare your YAML to the official mods. They are the reference implementation.
- **Use `git diff`:** if you modified the engine, review your changes for unintended side effects.

## Where to get help

- OpenRA GitHub issues and discussions.
- OpenRA Discord/IRC community.
- The source code itself — the engine is well-organized and heavily commented.

## Summary

This appendix is a practical guide for diagnosing problems in OpenRA. It covers the log files, the in-game debug menu, decision trees for common failures, network debugging, and general troubleshooting tips. Use it as a first stop when a mod, map, or engine change does not behave as expected.

## What to read next

- **If you are stuck on a YAML error:** [Appendix B — Common YAML Patterns](Appendix_B_Common_YAML_Patterns.md)
- **If a unit will not move or an activity is stuck:** [Part 1.2 — Activities and the Game Loop](../chapters/Part_01_Chapter_02_Activities.md) for the activity queue, and [Part 1.1 — Entity-Component-System (ECS) and Actor Lifecycle](../chapters/Part_01_Chapter_01_ECS.md) for trait/condition interactions.
- **If the issue is a desync or network stall:** [Part 9.3 — Sync Hashing and Determinism](../chapters/Part_09_Chapter_03_Sync_Hashing.md)
- **If you are investigating performance problems:** [Appendix D — Engine Conventions](Appendix_D_Engine_Conventions.md) and [Appendix E — Practical Recipes](Appendix_E_Practical_Recipes.md)
- **If you want to set up automated reproduction checks:** [Appendix F — Testing](Appendix_F_Testing.md)