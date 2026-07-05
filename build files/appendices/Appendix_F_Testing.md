# Appendix F — Testing Strategies

OpenRA is a [deterministic](Appendix_A_Glossary.md), [lockstep](Appendix_A_Glossary.md) real-time strategy engine. That means the simulation must produce exactly the same result on every client when given the same initial state and the same stream of [orders](Appendix_A_Glossary.md). Testing is therefore not only about catching crashes; it is about proving that the engine, an official mod, or a custom mod stays deterministic across hardware, platforms, and game versions. This appendix covers the testing layers used to protect that determinism: unit tests, YAML validation, replay testing, sync testing, performance testing, and practical checklists.

## Overview

Why does deterministic testing matter? In a lockstep architecture the server only forwards player [orders](Appendix_A_Glossary.md); each client runs the full simulation locally. If two clients ever compute a different [world](Appendix_A_Glossary.md) state, the game has **[desynced](Appendix_A_Glossary.md)** and cannot be trusted to continue. Replays rely on the same property: a replay file stores only the initial settings and the order stream, so playback must reproduce the original simulation frame-for-frame.

A bug can be completely invisible in single-player or skirmish mode yet break multiplayer immediately. Common examples include:

- A [trait](Appendix_A_Glossary.md) using a random number generator that is not shared between clients.
- A trait iterating over an unordered collection without a stable sort key.
- A rule change that makes an old replay compute a different battle outcome.

Testing should happen at every layer: code, YAML, recorded gameplay, live multiplayer sync, and performance.

![Unit tests diagram](images/Appendix_F_Testing-diagram-of-the-openra-test-project-layout-mapped-to-the-engi-3a5642.svg)

## Unit tests


<!-- DEV-NOTE [tooling]: NUnit: https://nunit.org — the testing framework used by the OpenRA.Test project. -->
OpenRA's unit tests live in the `OpenRA.Test` project. They use **NUnit** and target the same engine and mod assemblies the game runs. The project is split into the same namespaces as the engine, so tests for `OpenRA.Game` live under `OpenRA.Test/OpenRA.Game/`, tests for `OpenRA.Mods.Common` under `OpenRA.Test/OpenRA.Mods.Common/`, and so on.

### Layout

| Location | Typical contents |
| :---- | :---- |
| `OpenRA.Test/OpenRA.Game/` | Tests for core types such as `CPos`, `WPos`, `MiniYaml`, `Order`, and `Sync` helpers. |
| `OpenRA.Test/OpenRA.Mods.Common/` | Tests for traits, activities, weapons, pathfinding, and utility commands. |
| `OpenRA.Test/OpenRA.Mods.Cnc/` | Tests specific to the Tiberian Dawn mod. |
| `OpenRA.Test/OpenRA.Mods.Ra/` | Tests specific to the Red Alert mod. |

### Adding a test for a trait

A trait test usually constructs a small world or uses helper methods that create a map with the actor and rules needed. Keep the test focused on the trait's behavior rather than the whole game loop. Here is a minimal pattern:

```csharp
[Test]
public void MyTraitDoesX()
{
    // Arrange: create a map and ruleset that include the [actor](Appendix_A_Glossary.md).
    var map = new Map(...);
    var rules = map.Rules; // or a custom Ruleset loaded from [MiniYaml](Appendix_A_Glossary.md)
    var actor = CreateActor(map, rules, "my-actor");

    // Act: tick the trait or call its public method directly.
    actor.Tick();

    // Assert: verify the trait state or the actor's state changed as expected.
    Assert.That(SomeState, Is.EqualTo(expectedValue));
}
```

Many existing tests create actors through `World` helpers or set up `TraitData` directly. Look at `OpenRA.Test/OpenRA.Mods.Common/Traits/` for existing examples when adding a new trait test.

### Adding a test for an activity

Activity tests are similar, but they usually queue the activity on an actor and tick it until completion:

```csharp
[Test]
public void MyActivityCompletes()
{
    var actor = CreateActor(...);
    var activity = new MyActivity(Target.FromActor(other));
    actor.QueueActivity(activity);

    // Tick until the activity finishes or a safety limit is reached.
    for (var i = 0; i < 100 && !actor.IsIdle; i++)
        actor.Tick();

    Assert.That(actor.IsIdle, Is.True);
}
```

### Adding a test for a utility command

Utility commands implement `IUtilityCommand`. You can test them by invoking `Run` with a `Utility` instance and the arguments you would pass on the command line:

```csharp
[Test]
public void MyUtilityCommandRuns()
{
    var utility = new Utility("ra", new string[0]);
    var command = new MyUtilityCommand();

    var args = new[] { "my-utility-command", "some-arg" };
    command.Run(utility, args);

    // Assert the expected output files, console output, or return state.
}
```

### Running the tests

<!-- DEV-NOTE [tooling]: Microsoft .NET SDK: https://dotnet.microsoft.com — required to build the OpenRA engine and mod projects. -->
Use `dotnet test` directly:

```bash
dotnet test OpenRA.Test/OpenRA.Test.csproj
```

Run a single test or namespace with the `--filter` option:

```bash
dotnet test OpenRA.Test/OpenRA.Test.csproj --filter "FullyQualifiedName~MyTrait"
```

The OpenRA build scripts also expose a convenient target:

```bash
make test
```

On Windows the equivalent is usually `make.cmd test` or `dotnet test` from the solution root. CI runs the full suite on every pull request, so adding a test for new engine behavior is the best way to prevent regressions.

## YAML validation

A large part of OpenRA is data-driven. Mods, maps, weapons, sequences, chrome layouts, and audio definitions are all written in [MiniYaml](Appendix_A_Glossary.md). The engine provides a family of utility commands that parse and validate this data without launching the game. Running these commands is the cheapest way to catch errors before a human player sees them.

### `--check-yaml`

`--check-yaml` loads the full mod ruleset and reports syntax errors, inheritance problems, missing trait fields, invalid trait references, and duplicate keys. It is the first command to run after any non-trivial YAML change.

```bash
./utility.sh ra --check-yaml
```

Common issues it catches:

| Error type | Example | What to do |
| :---- | :---- | :---- |
| Parse error | Misaligned indentation or a missing colon. | Fix indentation and MiniYaml syntax. |
| Invalid trait name | `Helth:` instead of `Health:`. | Correct the trait or field name. |
| Missing required field | `Mobile:` with no `Locomotor` defined. | Add the required field or inherit from a template that provides it. |
| Inheritance loop | `A inherits: B` and `B inherits: A`. | Remove the circular `Inherits` reference. |
| Duplicate key | Two `Armament` nodes without `@` instance names. | Key them (`Armament@PRIMARY`, `Armament@SECONDARY`). |

### `--check-sequences` and related commands

`--check-sequences` validates sequence definitions, image references, and frame ranges. Other useful commands include:

| Command | Purpose |
| :---- | :---- |
| `--check-sequences` | Validate sequence YAML and image references. |
| `--check-missing-sprites` | Report sprites referenced by sequences but not present in the VFS. |
| `--check-missing-sequences` | Report actors that reference sequences that do not exist. |
| `--check-referenced-sequences` | Verify that every `RenderSprites` or sequence trait uses a defined sequence. |
| `--check-explicit-interfaces` | Verify that traits correctly implement required interfaces. |
| `--check-conditional-trait-interface-overrides` | Validate conditional trait interface overrides. |

Typical validation workflow after adding art:

```bash
./utility.sh ra --check-yaml
./utility.sh ra --check-sequences
./utility.sh ra --check-missing-sprites
./utility.sh ra --check-missing-sequences
```

If `--check-yaml` passes, the mod is likely syntactically valid. Passing the sequence checks means the artwork is wired correctly. These commands do not verify gameplay balance or logic, but they eliminate the most common startup crashes.

![Replay testing diagram](images/Appendix_F_Testing-testing-workflow-diagram-showing-the-layers-unit-test-yaml-c-3f7681.svg)

## Replay testing


A [replay](Appendix_A_Glossary.md) is a deterministic recording of a game. It stores the initial map, lobby settings, random seed, and the complete order stream from every player. It does **not** store the [world](Appendix_A_Glossary.md) state, so every frame must be recomputed during playback. If the simulation is not deterministic, the replay will desync from the original game.

### Recording and playback

Replays are recorded automatically during normal games. They are written to the `Replays/` folder under the user data directory. To play a replay back, select it from the replay browser in the main menu, or launch it directly from the command line with the appropriate replay path.

```bash
./launch-game.sh "Game.Replay=<path-to-replay>"
```

During playback the game feeds the stored orders into the same simulation loop used for live games. Any divergence between the recorded [sync hash](Appendix_A_Glossary.md) and the computed hash indicates a [desync](Appendix_A_Glossary.md).

### What a replay regression tells you

If a replay that worked on a previous engine version desyncs on the new version, the simulation has changed. This is expected when gameplay rules change intentionally, but it is a bug when the engine itself was supposed to stay compatible. Investigate the same way you would a multiplayer desync:

1. Enable sync reports if possible.
2. Find the first frame where the sync hash differs.
3. Identify the actor or trait that changed.
4. Look for unordered collections, random sources, floating-point math, or missing `[VerifySync]` fields.

Because replay compatibility is fragile, official mods keep a set of reference replays and replay them in CI. Mods should also re-test important replays after rule changes. See [Part 9.3 — Sync Hashing and Determinism](../chapters/Part_09_Chapter_03_Sync_Hashing.md) for how the sync hash is computed and compared.

![Sync testing diagram](images/Appendix_F_Testing-testing-workflow-diagram-showing-the-layers-unit-test-yaml-c-3f7681.svg)

## Sync testing


Sync testing is multiplayer testing. Its goal is to prove that every client reaches the same world state after every frame. The primary tool is the **sync report**, which dumps the per-actor, per-trait hash contributions when a desync is detected.

### Enabling sync reports

Sync reports are enabled in the lobby before the game starts:

```yaml
GlobalSettings:
    EnableSyncReports: true
```

You can also enable extra guards in `settings.yaml` for development:

```yaml
Debug:
    SyncCheckUnsyncedCode: true
    SyncCheckBotModuleCode: true
```

- `SyncCheckUnsyncedCode`: wraps `Sync.RunUnsynced` calls with a before/after sync hash comparison, catching code that accidentally mutates world state while claiming to be unsynced.
- `SyncCheckBotModuleCode`: runs bot module ticks inside a sync check so that AI decisions that differ between clients are caught early.

### Comparing sync reports

When a desync occurs, each client writes a `sync.log` file to the `Logs/` directory. The log contains one line per synced object with its hash and the values of its `[VerifySync]` fields. To find the cause:

1. Collect `sync.log` from two clients that desynced on the same frame.
2. Compare the reports line by line from the top.
3. The first object whose hash differs is the most likely culprit.
4. Once the actor/trait is known, inspect the trait code for determinism violations.

### Isolating a desyncing trait

Use this decision tree when a sync report points to a specific trait:

1. Does the trait use `world.SharedRandom` for any simulation-affecting decision?
   - **No.** Use `world.SharedRandom` for combat, movement, spawning, and any other gameplay outcome. `world.LocalRandom` and `Game.CosmeticRandom` are only for client-side or cosmetic effects.
2. Does the trait iterate over dictionaries, hash sets, or other unordered collections?
   - **Yes.** Sort the collection by a stable key such as `ActorID` or use an ordered list.
3. Does the trait run inside `Sync.RunUnsynced` but change world state or synced fields?
   - **Yes.** Move the mutation out of `RunUnsynced` and add `[VerifySync]` to the fields it changes.
4. Does the trait use `float` or `double` math in the simulation path?
   - **Yes.** Replace with fixed-point types (`WPos`, `WDist`, `WAngle`, `WVec`, `int`) or isolate the math and prove it is deterministic across platforms.
5. Does the trait read client-only state such as camera position, selection, or UI settings?
   - **Yes.** Gate the code behind client-only logic and never let it affect the simulation.

See [Appendix C — Debugging and Troubleshooting](Appendix_C_Debugging.md) for a full decision tree and the top ten desync causes, and [Part 9.3 — Sync Hashing and Determinism](../chapters/Part_09_Chapter_03_Sync_Hashing.md) for the sync hashing contract.

![Performance testing diagram](images/Appendix_F_Testing-testing-workflow-diagram-showing-the-layers-unit-test-yaml-c-3f7681.svg)

## Performance testing


Performance testing makes sure the game stays responsive as the world grows. OpenRA provides two simple in-code tools: `PerfSample` and `PerfTimer`. Both write timings to `perf.log` so you can see where the simulation or renderer spends its time.

### Using `PerfSample`

`PerfSample` measures a block of code with a `using` statement. The sample name appears in `perf.log` and can be aggregated across frames.

```csharp
using (new PerfSample("my trait tick"))
{
    // Work to measure
}
```

### Using `PerfTimer`

`PerfTimer` is useful when you need to measure several named sub-sections manually or when the work is not naturally scoped to a single `using` block.

```csharp
using (var timer = new PerfTimer("pathfinding"))
{
    timer.StartSection("build graph");
    BuildGraph();

    timer.StartSection("search");
    Search();
}
```

### Reading `perf.log`

`perf.log` contains frame timings, tick durations, and custom `PerfSample` markers. Look for:

| Marker | What it tells you |
| :---- | :---- |
| Frame time | Total time to render and simulate one frame. Spikes here cause stutter. |
| Tick time | Time spent inside the simulation tick. Long ticks delay the lockstep frame. |
| `PerfSample` names | Custom sections you added; compare before/after to measure optimizations. |

Common hotspots to measure and optimize:

- Pathfinding on large maps with many actors.
- Trait queries inside tight loops, especially `World.ActorsWithTrait<T>` or `World.ActorsHavingTrait<T>`.
- Heavy effects and projectile counts.
- Lua scripts that run frequently or allocate many objects.
- Rendering many actors without effective spatial partitioning.

In-game performance graphs can be enabled in settings when available. Use them alongside `perf.log` to confirm that an optimization actually improves the worst-case frame time, not just the average.

## Writing a test plan for a new feature

Before committing a new trait, weapon, activity, or utility command, work through this short checklist. It catches the determinism, data, and performance problems that are easiest to introduce and hardest to debug later.

- [ ] **Unit tests.** Add NUnit tests for the new logic. If the feature is a trait, test it in a small world. If it is a utility command, test `Run` directly.
- [ ] **YAML coverage.** Add or update a test map or test actor that exercises the new YAML fields. Run `--check-yaml` and any sequence or sprite checks.
- [ ] **Explicit interface checks.** Run `--check-explicit-interfaces` and `--check-conditional-trait-interface-overrides` when the trait implements conditional interfaces.
- [ ] **Replay regression.** Record a replay with the feature active and ensure it plays back without desyncing. Re-test after every rule change.
- [ ] **Sync safety.** If the feature changes world state, implement `ISync` and mark relevant fields with `[VerifySync]`. Use `world.SharedRandom` for randomness.
- [ ] **Unsynced code guard.** If the feature reads world state but should not change it, wrap it in `Sync.RunUnsynced` and enable `SyncCheckUnsyncedCode` during testing.
- [ ] **Bot/[AI](Appendix_A_Glossary.md) safety.** If the feature is touched by bot modules, enable `SyncCheckBotModuleCode` and test with at least one bot player in a local multiplayer game.
- [ ] **Performance baseline.** Add `PerfSample` markers around expensive work and check `perf.log` under worst-case conditions (many actors, large map, many effects).
- [ ] **Documentation.** Update trait `[Desc]` attributes, YAML comments, and manual references so other developers know how to test the feature.
- [ ] **Manual QA.** Run the feature in a real skirmish or mission, including edge cases such as the actor dying mid-action, the player being defeated, and the game being saved/loaded if applicable.

## Common testing pitfalls

These are the mistakes that most often slip through single-player testing and surface only in multiplayer or replay playback. Most of them are also listed in the Top 10 desync causes in [Appendix C — Debugging and Troubleshooting](Appendix_C_Debugging.md).

| # | Pitfall | Why it breaks tests | What to do |
| :---- | :---- | :---- | :---- |
| 1 | Non-deterministic RNG | Using `world.LocalRandom` or `Game.CosmeticRandom` for a gameplay outcome means different clients roll different numbers. | Use `world.SharedRandom` for simulation. |
| 2 | Relying on client-only state | Camera position, selection, UI settings, and local player preferences differ across clients. | Pass simulation-relevant data through orders or synced fields. |
| 3 | Unordered collections | `Dictionary`, `HashSet`, and some LINQ queries have non-deterministic iteration order. | Sort by `ActorID`, `PlayerName`, or another stable key before iterating. |
| 4 | Using `DateTime.Now` or wall-clock time | Wall-clock time differs on every client and depends on the local system. | Use game ticks, frame numbers, or `World.WorldTick` for timing. |
| 5 | Uninitialized static fields | Static state can persist between tests or game runs and leak from one test into another. | Initialize static state explicitly or avoid static mutable state in tests. |
| 6 | Missing `[VerifySync]` | Gameplay state that is not hashed will silently diverge between clients. | Implement `ISync` and mark every field that affects outcomes. |
| 7 | Floating-point math | `float` and `double` can produce slightly different results across CPUs and compilers. | Use fixed-point math (`WPos`, `WDist`, `WAngle`, `WVec`) or integers. |
| 8 | Culture-dependent parsing | `float.Parse` or string formatting can vary by locale and change parsed values. | Use `CultureInfo.InvariantCulture` or OpenRA's parsing helpers. |
| 9 | Mutating state from `RunUnsynced` | Code marked as unsynced is not allowed to change the world. | Move mutations into the simulation tick and sync them. |
| 10 | Assuming file-system order | Directory enumeration order is not guaranteed across platforms. | Sort file lists before using them in simulation or deterministic loading. |

If a multiplayer bug is hard to reproduce, add a small test that calls the same code path twice with the same inputs and asserts the outputs are identical. Deterministic functions should always produce the same result on the same input, and this property is much easier to test in isolation than in a live game.

## Summary

This section recaps the key points, definitions, and recipes presented above. Use it as a quick reference before moving to the next chapter or before returning to this material later.


## References

- [Part 9.3 — Sync Hashing and Determinism](../chapters/Part_09_Chapter_03_Sync_Hashing.md): the sync hash contract, `ISync`, `VerifySync`, and the `RunUnsynced` guard.
- [Part 10.3 — Porting, Modding, and Developer Workflows](../chapters/Part_10_Chapter_03_Port_And_Modding.md): developer workflow, utility commands, and the trait/sequence checklists.
- [Appendix C — Debugging and Troubleshooting](Appendix_C_Debugging.md): log channels, debug overlays, decision trees for desyncs, and the Top 10 desync causes.
- [Appendix A — Glossary](Appendix_A_Glossary.md): definitions for actor, trait, order, sync hash, desync, and other terms used in this appendix.

Key files to explore while writing tests:

- `OpenRA.Test/OpenRA.Test.csproj` — NUnit test project.
- `OpenRA.Game/Sync.cs` — sync hash generation and `RunUnsynced`.
- `OpenRA.Game/Network/SyncReport.cs` — sync report generation.
- `OpenRA.Game/Traits/TraitsInterfaces.cs` — `ISync` and other trait interfaces.
- `OpenRA.Mods.Common/UtilityCommands/` — utility command implementations and tests.
- `OpenRA.Mods.Common/Traits/` — reference trait implementations.
- `OpenRA.Game/Support/PerfSample.cs` and `OpenRA.Game/Support/PerfTimer.cs` — performance measurement helpers.



### External resources

- [OpenRA playtest docs](https://docs.openra.net/en/playtest/)
- [OpenRA main site](https://www.openra.net)
## What to read next

- **For the sync hashing and determinism contract:** [Part 9.3 — Sync Hashing and Determinism](../chapters/Part_09_Chapter_03_Sync_Hashing.md)
- **For debugging desyncs and testing failures:** [Appendix C — Debugging and Troubleshooting](Appendix_C_Debugging.md)
- **For engine conventions when writing testable traits:** [Appendix D — Engine Conventions and Style](Appendix_D_Engine_Conventions.md)
- **For practical modding recipes to test against:** [Appendix E — Practical Modding Recipes](Appendix_E_Practical_Recipes.md)
- **For developer workflows and utility commands:** [Part 10.3 — Porting, Modding, and Developer Workflows](../chapters/Part_10_Chapter_03_Port_And_Modding.md)