# Appendix D — Engine Conventions and Style

This appendix documents the coding, naming, and architectural conventions used in the OpenRA engine. Following these conventions makes your code consistent with the rest of the codebase and easier to review.

## C# style

OpenRA uses a standard C# style with a few project-specific conventions:

- **Braces** on the same line for methods and control structures.
- **Indentation** with tabs.
- **Naming:**
  - `PascalCase` for classes, methods, properties, and public fields.
  - `camelCase` for local variables and private fields.
  - `ALL_CAPS` for constants.
  - `[TraitInfo](Appendix_A_Glossary.md)` classes are named `MyTraitInfo` and the runtime trait is `MyTrait`.
- **Avoid LINQ in tight loops.** The codebase explicitly calls this out for performance-critical paths.
- **Use `var`** when the type is obvious.
- **Prefer readonly fields** on `TraitInfo` classes.

## Trait conventions

### TraitInfo class

```csharp
public class MyTraitInfo : TraitInfo<MyTrait>, Requires<SomeOtherTraitInfo>
{
    [Desc("Description of this field for modders.")]
    public readonly int MyField = 10;

    public override object Create(ActorInitializer init) { return new MyTrait(init, this); }
}
```

### Trait class

```csharp
public class MyTrait : INotifyCreated, ITick
{
    readonly MyTraitInfo info;

    public MyTrait(ActorInitializer init, MyTraitInfo info)
    {
        this.info = info;
    }

    void INotifyCreated.Created(Actor self)
    {
        // Post-creation setup
    }

    void ITick.Tick(Actor self)
    {
        // Per-frame logic
    }
}
```

### Use `Requires<T>` and `NotBefore<T>` correctly

- `Requires<T>` means the [actor](Appendix_A_Glossary.md) must have [trait](Appendix_A_Glossary.md) `T`.
- `NotBefore<T>` means this trait must be created after trait `T`.
- Use `TraitOrDefault<T>` if the trait may be absent.
- Use `TraitsImplementing<T>()` to iterate over multiple instances.

## Sync safety

- Mark gameplay-relevant fields with `[Sync]` or `[VerifySync]`.
- Use `world.SharedRandom` inside the simulation.
- Use `world.LocalRandom` only for UI, AI, or cosmetic effects.
- Never use `float`/`double` for synced state.
- Never iterate over non-deterministic collections (e.g., `Dictionary.Values`) in simulation code unless order is guaranteed not to matter.
- Wrap unsynced code in `Sync.RunUnsynced` if it reads world state.

## Order handling

- [Orders](Appendix_A_Glossary.md) are the only way to change the [world](Appendix_A_Glossary.md) state from the UI or [AI](Appendix_A_Glossary.md).
- Order handlers implement `IResolveOrder` or are handled in `UnitOrders`.
- Use `Order` with `SuppressVisualFeedback = true` for bot orders.
- Validate targets before acting; invalid targets are common in multiplayer due to latency.

## YAML conventions

- Use spaces for indentation in [MiniYaml](Appendix_A_Glossary.md) (not tabs).
- Use lowercase for actor keys and trait names.
- Use `^` for abstract actors.
- Use `@N` keyed inherits for multiple inheritance.
- Use `@INSTANCE` for multiple trait instances.
- Keep abstract actors in `defaults.yaml` or `shared.yaml`.
- Group related rules in separate files.

## Error handling

- Use exceptions for programming errors (e.g., missing required trait).
- Use `Log.Write` for recoverable runtime issues.
- Validate assumptions in `IRulesetLoaded` or `Created` hooks rather than silently failing.
- Do not catch exceptions that hide logic errors unless you are handling a specific expected case.

## Performance considerations

- Cache trait lookups in the actor constructor.
- Avoid `foreach` over large collections in tight loops.
- Use `World.ScreenMap` for spatial queries instead of scanning all actors.
- Batch rendering and avoid per-sprite draw calls.
- Use `PerfSample` to measure suspected slow paths.
- Profile before optimizing.

## Documentation conventions

- Use `[Desc("...")]` on public `TraitInfo` fields so the field is documented in YAML.
- Add XML comments to public APIs when the behavior is non-obvious.
- Keep comments focused on *why*, not *what*.
- Update this manual when adding significant new subsystems.

## File organization

- Engine code is in `OpenRA.Game/`.
- Common mod code is in `OpenRA.Mods.Common/`.
- Mod-specific code is in `OpenRA.Mods.<Mod>/`.
- YAML rules are in `mods/<mod>/rules/`.
- Sequences are in `mods/<mod>/sequences/`.
- Chrome layouts are in `mods/<mod>/chrome/`.

## Testing conventions

- Unit tests are in `OpenRA.Test/`.
- Name test classes after the class under test.
- Run `make tests` before submitting changes.
- For gameplay changes, test in multiplayer to ensure sync safety.

## Versioning

- Mods declare `RequiresMods` with the exact engine version.
- Use `make version` to update version strings before release.
- Keep the `VERSION` file and `mod.yaml` metadata in sync.

## Pull request etiquette

- Keep changes focused on one subsystem.
- Include tests when possible.
- Run `make check` and `make test` before submitting.
- Explain the motivation, not just the mechanics.
- Reference related issues or chapters in the manual.

## Summary

This appendix documents the coding, naming, and architectural conventions used in the OpenRA engine. Following these conventions — C# style, trait design, sync safety, YAML structure, error handling, and performance — keeps custom code and mods consistent with the rest of the codebase and easier to review.

## What to read next

- **For trait and actor lifecycle basics:** [Part 1.1 — ECS, Actors, and Traits](../chapters/Part_01_Chapter_01_ECS.md)
- **For the activity system and tick conventions:** [Part 1.2 — Activities and the Game Loop](../chapters/Part_01_Chapter_02_Activities.md)
- **For order and sync safety details:** [Part 9.1 — OrderManager and Networked Orders](../chapters/Part_09_Chapter_01_OrderManager.md) and [Part 9.3 — Sync Hashing and Determinism](../chapters/Part_09_Chapter_03_Sync_Hashing.md)
- **For YAML pattern examples:** [Appendix B — Common YAML Patterns](Appendix_B_Common_YAML_Patterns.md)
- **For debugging recipes that apply these conventions:** [Appendix C — Debugging and Troubleshooting](Appendix_C_Debugging.md)
- **For testing practices:** [Appendix F — Testing](Appendix_F_Testing.md)