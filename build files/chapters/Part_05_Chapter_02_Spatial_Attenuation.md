# Chapter 5.2 — Spatial Sound Attenuation

## Purpose

[Spatial attenuation](../appendices/Appendix_A_Glossary.md) makes world sounds feel as if they originate from places on the battlefield. A tank firing near the camera is loud; a distant explosion is quiet. OpenRA delegates this to OpenAL, feeding it source positions and a listener position that tracks the camera. This chapter explains how positions flow from the simulation to OpenAL, the OpenAL attenuation model, and the tuning constants OpenRA uses.

## Learning Objectives


After studying this chapter, you should be able to:

- Explain how spatial attenuation makes world sounds feel positioned in the battlefield.
- Describe how the listener position follows the camera and how source positions are set.
- Trace the data flow from a WPos to an OpenAL source position.
- Interpret OpenRA's OpenAL constants (reference distance, max distance, listener Z offset).
- Explain the inverse-distance attenuation model used by OpenAL.
- Implement moving sounds and per-sound volume modifiers correctly.

## Files

| File | Responsibility |
| :---- | :---- |
| `OpenRA.Game/Game.cs` | Calls `Sound.SetListenerPosition(worldRenderer.Viewport.CenterPosition)` once per render frame. |
| `OpenRA.Game/Sound/Sound.cs` | `SetListenerPosition`, `Play(..., WPos pos)`, `SetPosition(ISound, WPos)`. |
| `OpenRA.Game/Sound/SoundDevice.cs` | `ISoundEngine` interface methods for listener position and source position. |
| `OpenRA.Platforms.Default/OpenAlSoundEngine.cs` | OpenAL implementation: `SetListenerPosition`, `OpenAlSound` constructor, `SetSoundPosition`. |
| `OpenRA.Game/Graphics/WorldRenderer.cs` | Provides `Viewport.CenterPosition` for the listener. |

![Architecture diagram](images/Part_05_Chapter_02_Spatial_Attenuation-architecture-diagram-showing-the-main-classes-interfaces-and-9161e6.svg)

## Architecture


### Listener follows the camera

```
[Game loop] -> [WorldRenderer.Viewport.CenterPosition] -> [Sound.SetListenerPosition] -> [OpenAL listener]
```

Once per frame, the main loop in `OpenRA.Game/Game.cs` sets the listener to the center of the [viewport](../appendices/Appendix_A_Glossary.md):

```csharp
Sound.SetListenerPosition(worldRenderer.Viewport.CenterPosition);
```

World sounds that are played with a `WPos` argument are automatically placed at their source position. OpenAL then computes the gain based on the distance between the source and the listener.

### UI sounds vs world sounds

UI sounds are played with `headRelative: true`. OpenAL treats them as attached to the listener, so they are not attenuated by distance. World sounds use `headRelative: false` and are positioned in the world. The `SoundType` enum (`UI` or `World`) is used by `Sound.Play` to suppress world sounds when the user disables them, but it does not affect attenuation directly.

### Moving sounds

A sound that has already started can be moved by calling `Sound.SetPosition(ISound, WPos)`. This updates the source's OpenAL `AL_POSITION` while the sound is playing. This is used for continuous sounds attached to moving actors, such as sirens or long-running ambient loops.

![Data flow  code path diagram](images/Part_05_Chapter_02_Spatial_Attenuation-sequence-flow-diagram-tracing-the-execution-path-from-trigge-035864.svg)

## Data Flow / Code Path


### Playing a positioned sound

```csharp
public ISound Play(SoundType type, string name, WPos pos) { return Play(type, null, name, false, pos, 1f); }
```

The public overload passes `headRelative: false` and the world position to the internal `Play` method, which calls `soundEngine.Play2D(sounds[name], loop, headRelative, pos, volume, attenuateVolume: true)`.

### Inside OpenAL

`OpenAlSoundEngine.Play2D` obtains a source from the pool, fills a `PoolSlot` with position and metadata, and constructs an `OpenAlSound`:

```csharp
slot.Sound = new OpenAlSound(source, loop, relative, pos, volume * atten, alSoundSource.SampleRate, alSoundSource.Buffer);
```

The `OpenAlSound` constructor sets the OpenAL source parameters:

```csharp
AL10.alSourcef(source, AL10.AL_PITCH, 1f);
AL10.alSource3f(source, AL10.AL_POSITION, pos.X, pos.Y, pos.Z);
AL10.alSource3f(source, AL10.AL_VELOCITY, 0f, 0f, 0f);
AL10.alSourcei(source, AL10.AL_LOOPING, looping ? 1 : 0);
AL10.alSourcei(source, AL10.AL_SOURCE_RELATIVE, relative ? 1 : 0);
AL10.alSourcef(source, AL10.AL_REFERENCE_DISTANCE, 6826);
AL10.alSourcef(source, AL10.AL_MAX_DISTANCE, 136533);
```

After the source is configured, `AL10.alSourcePlay(source)` starts playback.

### Listener setup

`OpenAlSoundEngine.SetListenerPosition` moves the listener slightly above the ground plane and sets the world-to-meter scale:

```csharp
public void SetListenerPosition(WPos position)
{
    AL10.alListener3f(AL10.AL_POSITION, position.X, position.Y, position.Z + 2133);

    var orientation = new[] { 0f, 0f, 1f, 0f, -1f, 0f };
    AL10.alListenerfv(AL10.AL_ORIENTATION, orientation);
    AL10.alListenerf(EFX.AL_METERS_PER_UNIT, .01f);
}
```

The `+2133` on the Z axis pulls the listener out of the isometric plane so that sounds directly under the camera center are not panned too sharply. The orientation vector is a fixed "look down, Y up" orientation. The scale `0.01` means one world unit is treated as one centimeter by OpenAL's distance model.

![Configuration (yaml) diagram](images/Part_05_Chapter_02_Spatial_Attenuation-annotated-yaml-snippet-diagram-showing-the-key-fields-and-ho-6a1b98.svg)

## Configuration (YAML)


Spatial attenuation is driven entirely by C# constants and OpenAL defaults; there are no mod-facing YAML knobs for the reference distance or max distance. However, the effective loudness of a sound is controlled by two YAML-level values:

- `VolumeModifier` on a `MusicInfo` or `SoundPool` entry.
- The `volumeModifier` argument passed by traits when they call `Game.Sound.Play`.

For example:

```yaml
Notifications:
    Explosion:
        VolumeModifier: 0.7
        Notifications: expl1, expl2
```

A trait can then call `Game.Sound.Play(SoundType.World, "Explosion", self.CenterPosition, volumeModifier)` to further scale the sound.

## Interconnectivity

- **Depends on:** [Part 5.1 — Audio Architecture](Part_05_Chapter_01_Audio_Architecture.md), [Part 4.2 — WorldRenderer](Part_04_Chapter_02_WorldRenderer.md), [Part 1.4 — Math, Coordinates, and Determinism](Part_01_Chapter_04_Math.md).
- **Used by:** [Part 5.4 — Sound Triggers](Part_05_Chapter_04_Sound_Triggers.md), Part 8 (bot notifications), and any trait that plays a world sound.

![Algorithms diagram](images/Part_05_Chapter_02_Spatial_Attenuation-algorithm-diagram-or-pseudocode-flowchart-for-the-non-trivia-5983ed.svg)

## Algorithms


### OpenAL inverse-distance attenuation

With the default OpenAL distance model (inverse distance clamped), source gain is:

```
gain = clamp(distance / referenceDistance, 0, 1)  // inverted
actual gain = volume * (1 - clampedFactor)
```

More precisely, OpenAL computes:

```
distance = max(distance, AL_REFERENCE_DISTANCE)
gain = AL_REFERENCE_DISTANCE / (AL_REFERENCE_DISTANCE + AL_ROLLOFF_FACTOR * (distance - AL_REFERENCE_DISTANCE))
gain = clamp(gain, 0.0, 1.0)
```

OpenRA does not set `AL_ROLLOFF_FACTOR`, so it defaults to `1.0`, producing standard inverse-distance rolloff. The gain is clamped so that sounds beyond `AL_MAX_DISTANCE` become silent and sounds at or within `AL_REFERENCE_DISTANCE` are at full volume.

### OpenRA constants in world units

Because `AL_METERS_PER_UNIT = 0.01`, the OpenAL constants translate to world units as follows:

- `AL_REFERENCE_DISTANCE = 6826` world units (~68.3 meters).
- `AL_MAX_DISTANCE = 136533` world units (~1365 meters).
- Listener Z offset = 2133 world units (~21 meters above the ground plane).
- `GroupDistance = 2730` world units used for the instance-throttling heuristic.

These values were chosen so that the isometric camera (typically looking down at an angle) hears nearby combat clearly and distant combat fades naturally.

### Instance throttling and volume

Before the source is allocated, `OpenAlSoundEngine.Play2D` computes an additional attenuation factor based on how many sources are currently active:

```csharp
atten = 0.66f * ((PoolSize - activeCount * 0.5f) / PoolSize);
```

This is multiplied by the requested volume. As the pool fills, all new sounds become slightly quieter to reduce the overall perceived volume and prevent clipping. This is independent of spatial distance attenuation.

### Per-frame capping

The same sound source starting too many times within 5 frames and within `GroupDistanceSqr` (2730 world units) is dropped entirely:

```csharp
if (++instances == MaxInstancesPerFrame)
    return null;
```

This prevents rapid-fire sounds (e.g., many machine guns from a cluster of infantry) from overwhelming the audio pipeline.

### Moving a playing sound

`OpenAlSound.SetPosition` updates `AL_POSITION` directly:

```csharp
public void SetPosition(WPos pos)
{
    if (done)
        return;

    AL10.alSource3f(Source, AL10.AL_POSITION, pos.X, pos.Y, pos.Z);
}
```

This is the only way to keep a long sound spatially accurate as its source actor moves.

![Extension points diagram](images/Part_05_Chapter_02_Spatial_Attenuation-extension-hook-diagram-showing-the-interface-s-to-implement-b4a27b.svg)

## Extension Points


### Change attenuation constants

The only way to alter reference distance, max distance, or the listener Z offset is to modify `OpenAlSoundEngine` or provide a custom `ISoundEngine` implementation. These are not exposed through YAML because OpenRA's camera and world scale are fixed.

### Per-sound volume scaling

Mods can use the `volumeModifier` argument in `Game.Sound.Play` calls to make certain sounds louder or quieter relative to their spatial distance. This is the recommended way to balance combat audio without touching the engine.

### Custom distance model

A custom `ISoundEngine` could ignore OpenAL's built-in attenuation and compute gain itself based on the source/listener distance, then set `AL_GAIN` directly. This would allow nonlinear rolloff curves, but it would require re-implementing the rest of the source management.

### Head-relative sounds

Sounds that should always be full volume regardless of camera position should be played with `headRelative: true` (or the `Play(SoundType, string name)` overload that defaults to it). This is the right choice for UI feedback, music, and per-player announcements.

![Common pitfalls  guardrails diagram](images/Part_05_Chapter_02_Spatial_Attenuation-checklist-infographic-style-diagram-summarizing-the-top-pitf-fb069e.svg)

## Common Pitfalls / Guardrails


- **Listener Z offset:** the `+2133` offset means sounds very far above or below the listener plane can behave unexpectedly. Always pass a grounded `WPos` (e.g., `self.CenterPosition` or `self.World.Map.CenterOfCell(cell)`) for world sounds.
- **Source-relative flag:** `headRelative: true` disables spatialization entirely. Do not accidentally pass `false` for UI sounds.
- **Max distance:** sounds beyond 136533 world units will be silent. This is rarely hit on typical maps, but very large custom maps should keep this in mind.
- **Pool exhaustion:** if the source pool is exhausted, the sound is simply dropped. There is no queue; the gameplay is unaffected.
- **Determinism:** attenuation is client-side. The simulation does not know whether a sound was played or how loud it was. Never use audio state for gameplay logic.
- **Volume hierarchy:** the final gain is the product of the source volume, the `volumeModifier`, the OpenAL distance gain, and the global `AL_GAIN` listener gain. Changing any one changes the final loudness.

## What to read next

- [Part 5.1 — Audio Architecture](Part_05_Chapter_01_Audio_Architecture.md) for the ISoundEngine, ISoundSource, and ISound abstractions.
- [Part 5.4 — Sound Triggers](Part_05_Chapter_04_Sound_Triggers.md) for the traits that trigger the positional sounds attenuated here.
- [Part 4.4 — Viewport and Input](Part_04_Chapter_04_Viewport_Input.md) for the camera viewport that provides the listener position.

## Summary

This chapter explains how OpenRA positions world sounds in 3D space through OpenAL spatial attenuation, from source and listener positions to the inverse-distance model and tuning constants.

If any of the concepts above feel unclear, review the relevant section before continuing. For source files and further reading, see the References section.


## References

- `OpenRA.Game/Game.cs` — listener position update in the main loop.
- `OpenRA.Game/Sound/Sound.cs` — `SetListenerPosition`, `Play` with position, `SetPosition`.
- `OpenRA.Game/Sound/SoundDevice.cs` — `ISoundEngine` interface.
- `OpenRA.Platforms.Default/OpenAlSoundEngine.cs` — `SetListenerPosition`, `Play2D`, `OpenAlSound`, source pool.
- `OpenRA.Platforms.Default/DummySoundEngine.cs` — no-op backend for headless/muted mode.
- `OpenRA.Game/Graphics/WorldRenderer.cs` — viewport and camera position.
- OpenAL Soft documentation: `AL_REFERENCE_DISTANCE`, `AL_MAX_DISTANCE`, `AL_SOURCE_RELATIVE`, `AL_METERS_PER_UNIT`.

### External resources

- [OpenAL Soft](https://openal-soft.org) — the open-source implementation of the spatial audio API used by OpenRA.