# Chapter 5.4 — Sound Triggers

## Purpose

Sound triggers are the [traits](../appendices/Appendix_A_Glossary.md) and [activities](../appendices/Appendix_A_Glossary.md) that call `Game.Sound.Play` or `Game.Sound.PlayNotification` in response to game events. They are the bridge between the simulation and the audio system. This chapter covers the common trigger traits, the voice/notification resolution pipeline, and how modders can add new audio feedback.

## Learning Objectives


After studying this chapter, you should be able to:

- Explain the difference between [world](../appendices/Appendix_A_Glossary.md) sounds and UI/notification sounds.
- Describe the voice and notification resolution pipeline through PlayPredefined.
- Use SoundPool interrupt types (DoNotPlay, Interrupt, Overlap) to prevent audio spam.
- Configure voice sets, notifications, and weapon reports in YAML.
- Implement common sound trigger traits such as Voiced, AttackSounds, and SoundOnDamageTransition.
- Add custom sound triggers that respond to game events.

## Files

| File | Responsibility |
| :---- | :---- |
| `OpenRA.Mods.Common/Traits/Voiced.cs` | Plays voice phrases for a selected actor (Select, Move, Attack, etc.). |
| `OpenRA.Mods.Common/Traits/Sound/VoiceAnnouncement.cs` | Plays a voice clip when the trait is enabled. |
| `OpenRA.Mods.Common/Traits/Sound/AttackSounds.cs` | Plays a sound when an actor attacks or prepares an attack. |
| `OpenRA.Mods.Common/Traits/Sound/SoundOnDamageTransition.cs` | Plays sounds when damage state crosses Heavy or Dead. |
| `OpenRA.Mods.Common/Traits/Sound/DeathSounds.cs` | Plays a death sound when an actor is killed. |
| `OpenRA.Mods.Common/Traits/Sound/AmbientSound.cs` | Plays a continuous looped sound attached to an actor. |
| `OpenRA.Mods.Common/Traits/Sound/AnnounceOnSeen.cs` | Plays a notification when an actor is first spotted. |
| `OpenRA.Mods.Common/Traits/Sound/AnnounceOnKill.cs` | Plays a notification when an actor scores a kill. |
| `OpenRA.Mods.Common/Traits/Sound/CaptureNotification.cs` | Plays a notification when an actor is captured. |
| `OpenRA.Mods.Common/Traits/Sound/ActorLostNotification.cs` | Plays a notification when an actor is lost. |
| `OpenRA.Mods.Common/Traits/Player/ProductionQueue.cs` | Plays construction-started and unit-ready notifications. |
| `OpenRA.Mods.Common/Traits/Player/PlaceBuilding.cs` | Plays building placement and cancellation sounds. |
| `OpenRA.Mods.Common/Traits/Player/PlaceBeacon.cs` | Plays a beacon placement sound. |
| `OpenRA.Mods.Common/Traits/SupportPowers/SupportPower.cs` | Plays support-power charging and activation sounds. |
| `OpenRA.Game/Sound/Sound.cs` | `PlayPredefined`, `PlayNotification`, `Play`, and sound pools. |
| `OpenRA.Game/GameRules/SoundInfo.cs` | `SoundPool` and interrupt behavior. |

![Architecture diagram](images/Part_05_Chapter_04_Sound_Triggers-architecture-diagram-showing-the-main-classes-interfaces-and-9161e6.svg)

## Architecture


### Two main trigger families

Sound triggers fall into two categories:

1. **World sounds** — positional, played at an [actor](../appendices/Appendix_A_Glossary.md)'s `CenterPosition` and attenuated by the camera. Examples: gunshots, explosions, voices, ambient loops.
2. **UI/Notification sounds** — head-relative, played at zero volume attenuation. Examples: "Building complete", "Low power", "Unit ready".

### Voice vs notification resolution

`Sound.PlayPredefined` is the central dispatcher. It takes a `type` (voice set or notification type), a `definition` (phrase name such as "Select" or "Attack"), and an optional `variant` (faction or actor variant). It then:

1. Looks up the `SoundInfo` for the voice set or notification type.
2. Finds the matching `SoundPool` for the definition.
3. Picks the next clip from the pool.
4. Applies variant-specific suffix/prefix from `SoundInfo.Variants` and `Prefixes`.
5. Plays the clip through the sound engine.

For voices, the pool is keyed by actor ID so that each actor can have its own active voice. For notifications, the pool is keyed by the resolved clip name, so the same notification cannot overlap itself unless configured to.

### Interrupt types

Every `SoundPool` has an `InterruptType`:

- `DoNotPlay` — if the same sound is already playing, the new request is dropped.
- `Interrupt` — the old sound is stopped and the new one plays.
- `Overlap` — the new sound is allowed to play over the old one.

This is configured per notification in YAML and is the primary tool for preventing audio spam.

![Data flow  code path diagram](images/Part_05_Chapter_04_Sound_Triggers-sequence-flow-diagram-tracing-the-execution-path-from-trigge-035864.svg)

## Data Flow / Code Path


### Voice trigger

When the player clicks a unit, the selection logic calls `self.PlayVoice("Select")`, which resolves to `IVoiced.PlayVoice(...)` in `Voiced.cs`:

```csharp
bool IVoiced.PlayVoice(Actor self, string phrase, string variant)
{
    ...
    return Game.Sound.PlayPredefined(SoundType.World, self.World.Map.Rules, null, self, type, phrase, variant, true, WPos.Zero, volume, true);
}
```

`PlayVoice` is head-relative (used for UI feedback when the actor is selected). `PlayVoiceLocal` is positional and uses the actor's `CenterPosition`.

### Notification trigger

Player-level traits call `Game.Sound.PlayNotification(rules, player, type, notification, variant)`:

```csharp
public bool PlayNotification(Ruleset rules, Player player, string type, string notification, string variant)
{
    return PlayPredefined(SoundType.UI, rules, player, null, type.ToLowerInvariant(), notification, variant, true, WPos.Zero, 1f, false);
}
```

The player filter ensures that only the local player hears notifications meant for them.

### Attack sound trigger

`AttackSounds` implements `INotifyAttack` and `ITick`. When the actor fires or prepares to fire, it schedules a delayed sound or plays it immediately:

```csharp
void INotifyAttack.Attacking(Actor self, in Target target, Armament a, Barrel barrel)
{
    if (info.DelayRelativeTo == AttackDelayType.Attack)
    {
        if (info.Delay > 0)
            tick = info.Delay;
        else
            PlaySound(self);
    }
}

void PlaySound(Actor self)
{
    if (info.Sounds.Length > 0)
        Game.Sound.Play(SoundType.World, info.Sounds, self.World, self.CenterPosition);
}
```

### Damage sound trigger

`SoundOnDamageTransition` implements `INotifyDamageStateChanged`:

```csharp
void INotifyDamageStateChanged.DamageStateChanged(Actor self, AttackInfo e)
{
    if (!info.DamageTypes.IsEmpty && !e.Damage.DamageTypes.Overlaps(info.DamageTypes))
        return;

    var rand = Game.CosmeticRandom;

    if (e.DamageState == DamageState.Dead)
    {
        var sound = info.DestroyedSounds.RandomOrDefault(rand);
        Game.Sound.Play(SoundType.World, sound, self.CenterPosition);
    }
    else if (e.DamageState >= DamageState.Heavy && e.PreviousDamageState < DamageState.Heavy)
    {
        var sound = info.DamagedSounds.RandomOrDefault(rand);
        Game.Sound.Play(SoundType.World, sound, self.CenterPosition);
    }
}
```

![Configuration (yaml) diagram](images/Part_05_Chapter_04_Sound_Triggers-annotated-yaml-snippet-diagram-showing-the-key-fields-and-ho-6a1b98.svg)

## Configuration (YAML)


### Voice set

A voice set is a named collection of phrases mapped to arrays of sound files:

```yaml
Sounds:
    Voices:
        e1:
            Select: e1sel1, e1sel2, e1sel3
            Move: e1mov1, e1mov2, e1mov3
            Attack: e1atk1, e1atk2
```

An actor that uses the voice set declares:

```yaml
E1:
    Voiced:
        VoiceSet: e1
        Volume: 1
```

The standard phrase names used by the engine and activities are:

- `Select` — played when the actor is selected.
- `Move` — played when the actor is ordered to move.
- `Attack` — played when the actor is ordered to attack.
- `Guard` — played when the actor is ordered to guard.
- `Build` — played when the actor is produced.
- `Die` — played when the actor is killed.
- `Capture` — played when the actor captures a building.
- `Enter` — played when the actor enters a transport or structure.

### Notifications

Notifications are defined per notification type (usually `Speech` or `Sounds`):

```yaml
Sounds:
    Notifications:
        Speech:
            Building:
                VolumeModifier: 1
                InterruptType: DoNotPlay
                Notifications: bldgin1
            UnitReady:
                InterruptType: Interrupt
                Notifications: unitredy1
```

Traits call `Game.Sound.PlayNotification(rules, player, "Speech", "Building", null)`.

### Weapon reports

Weapons declare their own sounds in `WeaponInfo`:

```yaml
M1Carbine:
    Report: gun11
    StartBurstReport: gun11
    AfterFireSound: reload
```

These are triggered by the `Armament` trait when the weapon fires.

### Trigger traits

Most sound trigger traits can be added directly to an actor:

```yaml
E1:
    AttackSounds:
        Sounds: gun11
        Delay: 0
    SoundOnDamageTransition:
        DamagedSounds: unitdie1
        DestroyedSounds: unitdie1
    AmbientSound:
        SoundFile: tesla
        Interval: 30
        Delay: 0
```

## Interconnectivity

- **Depends on:** [Part 5.1 — Audio Architecture](Part_05_Chapter_01_Audio_Architecture.md), [Part 5.2 — Spatial Attenuation](Part_05_Chapter_02_Spatial_Attenuation.md), [Part 2.4 — Rulesets, Actors, and Weapons](Part_02_Chapter_04_Rules_Weapons.md), [Part 1.1 — ECS, Actors, and Traits](Part_01_Chapter_01_ECS.md).
- **Used by:** Part 8 (AI notifications), [Part 4.3 — Widgets and Chrome](Part_04_Chapter_03_Widgets.md), Part 9 ([order](../appendices/Appendix_A_Glossary.md) handling that triggers voices), [Part 2.4 — Rulesets, Actors, and Weapons](Part_02_Chapter_04_Rules_Weapons.md).

![Algorithms diagram](images/Part_05_Chapter_04_Sound_Triggers-algorithm-diagram-or-pseudocode-flowchart-for-the-non-trivia-5983ed.svg)

## Algorithms


### SoundPool clip selection

`SoundPool.GetNext()` maintains a `liveclips` list. When the list is empty, it refills from the original `clips` array and then randomly removes one entry to play. This guarantees that every clip in a pool is played before any clip repeats, preventing the same voice line from being selected twice in a row.

```csharp
public string GetNext()
{
    if (liveclips.Count == 0)
        liveclips.AddRange(clips);

    if (liveclips.Count == 0)
        return null;

    var i = Game.CosmeticRandom.Next(liveclips.Count);
    var s = liveclips[i];
    liveclips.RemoveAt(i);
    return s;
}
```

### Variant suffix/prefix selection

```csharp
if (variant != null)
{
    if (rules.Variants.TryGetValue(variant, out var v) && !rules.DisableVariants.Contains(definition))
        suffix = v[(int)(id % v.Length)];
    if (rules.Prefixes.TryGetValue(variant, out var p) && !rules.DisablePrefixes.Contains(definition))
        prefix = p[(int)(id % v.Length)];
}
```

The actor ID is used to deterministically pick a variant suffix/prefix so the same actor always uses the same voice variant across the game session.

### Actor selection muting

```csharp
var actorId = voicedActor != null && voicedActor.World.Selection.Contains(voicedActor) ? 0 : id;
```

Selected actors share `actorId = 0`, so only one selected actor can speak at a time. This prevents the cacophony of selecting multiple units and giving them an order.

### Interrupt handling

For notifications, `currentNotifications` tracks active sounds by name. If the same notification is requested again, the engine either drops the new request, stops the old one, or overlaps based on the pool's `InterruptType`.

For actor voices, `currentSounds` tracks active sounds by actor ID. This prevents a single actor from stacking voice lines and respects the same interrupt behavior.

![Extension points diagram](images/Part_05_Chapter_04_Sound_Triggers-extension-hook-diagram-showing-the-interface-s-to-implement-b4a27b.svg)

## Extension Points


### Add a new sound trigger trait

Create a trait that implements the appropriate notification interface (e.g., `INotifyAttack`, `INotifyDamageStateChanged`, `INotifyKilled`, `INotifyCreated`, `INotifyCapture`, `INotifyDiscovered`) and call `Game.Sound.Play` or `Game.Sound.PlayNotification` at the right moment.

### Add a new voice phrase

Add a new entry under the actor's voice set in `SoundInfo.Voices`, then call `self.PlayVoice("MyPhrase")` from an activity or trait. The phrase name is arbitrary as long as it is defined in the voice set.

### Add a new notification type

Define a new notification entry under `SoundInfo.Notifications`, then call `Game.Sound.PlayNotification(rules, player, "MyType", "MyNotification", variant)`.

### Customize interrupt behavior

Set `InterruptType` per notification pool to control overlap. Use `DoNotPlay` for infrequent announcements (e.g., "Low power"), `Interrupt` for critical state changes (e.g., "Unit ready"), and `Overlap` for ambient or layered effects.

### Add ambient sounds

Use `AmbientSound` to attach a continuous or looping sound to an actor. The sound is played at the actor's position and can be moved with `Sound.SetPosition` if the actor moves.

![Common pitfalls  guardrails diagram](images/Part_05_Chapter_04_Sound_Triggers-checklist-infographic-style-diagram-summarizing-the-top-pitf-fb069e.svg)

## Common Pitfalls / Guardrails


- **Client-side only:** all sound triggers are client-side. Do not use audio playback for gameplay logic or determinism.
- **Random source:** triggers use `Game.CosmeticRandom`, not `world.LocalRandom` or `world.SharedRandom`. This ensures voice line selection does not affect the simulation.
- **Player filtering:** `PlayNotification` filters by `player == localPlayer`. If you call it with the wrong player, no one will hear it.
- **Missing pools:** `PlayPredefined` throws if the requested `definition` is not present in the voice or notification pool. Ensure YAML definitions match the phrase names used in code.
- **Spatial attenuation:** world sounds must be passed a valid `WPos` or they will be attenuated relative to the origin. UI sounds must be played with `headRelative: true`.
- **Pool exhaustion:** if too many sounds overlap, new ones are dropped. Use `InterruptType.Overlap` sparingly for loud sounds.
- **Variant arrays:** if `Variants` or `Prefixes` have fewer entries than the actor ID modulo, the lookup will index out of bounds. Keep variant arrays consistent across all voice sets.

## What to read next

- [Part 5.1 — Audio Architecture](Part_05_Chapter_01_Audio_Architecture.md) for the ISoundEngine, ISoundSource, and ISound playback pipeline.
- [Part 5.2 — Spatial Attenuation](Part_05_Chapter_02_Spatial_Attenuation.md) for how world-sound triggers are attenuated by distance.
- [Part 1.1 — ECS, Actors, and Traits](Part_01_Chapter_01_ECS.md) for the actor/trait model that hosts sound trigger traits.
- [Appendix H — Asset Visual Reference](../appendices/Appendix_H_Asset_Visual_Reference.md) for a reference of voice, notification, and music asset definitions and engine classes.

## Summary

This chapter explains how sound triggers are implemented by [traits](../appendices/Appendix_A_Glossary.md) and [activities](../appendices/Appendix_A_Glossary.md) that call `Game.Sound.Play` or `Game.Sound.PlayNotification` in response to game events.

After reading this chapter, you should be able to:

- **World sounds** — positional, played at an [actor](../appendices/Appendix_A_Glossary.md)'s `CenterPosition` and attenuated by the camera. Examples: gunshots, explosions, voices, ambient loops.
- **UI/Notification sounds** — head-relative, played at zero volume attenuation. Examples: "Building complete", "Low power", "Unit ready".

If any of the concepts above feel unclear, review the relevant section before continuing. For source files and further reading, see the References section.


## References

- `OpenRA.Mods.Common/Traits/Voiced.cs` — voice playback.
- `OpenRA.Mods.Common/Traits/Sound/VoiceAnnouncement.cs` — voice announcement trigger.
- `OpenRA.Mods.Common/Traits/Sound/AttackSounds.cs` — attack sounds.
- `OpenRA.Mods.Common/Traits/Sound/SoundOnDamageTransition.cs` — damage state sounds.
- `OpenRA.Mods.Common/Traits/Sound/DeathSounds.cs` — death sounds.
- `OpenRA.Mods.Common/Traits/Sound/AmbientSound.cs` — ambient sounds.
- `OpenRA.Mods.Common/Traits/Player/ProductionQueue.cs` — production notifications.
- `OpenRA.Mods.Common/Traits/SupportPowers/SupportPower.cs` — support power sounds.
- `OpenRA.Game/Sound/Sound.cs` — `PlayPredefined` and `PlayNotification`.
- `OpenRA.Game/GameRules/SoundInfo.cs` — `SoundPool` and interrupt types.