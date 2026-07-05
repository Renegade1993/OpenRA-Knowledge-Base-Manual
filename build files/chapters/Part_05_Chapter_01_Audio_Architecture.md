# Chapter 5.1 — Audio Architecture

## Purpose

OpenRA's audio system bridges game events (unit voices, UI feedback, music, weapon reports) to a low-level sound engine. The architecture is deliberately layered: the engine defines a small, backend-agnostic interface (`ISoundEngine`), the `Sound` class manages samples, voices, notifications, and music, and a platform-specific implementation (OpenAL) handles device management, source pooling, and 3D spatialization. This chapter explains the layers, the data flow, and the configuration that ties them together.

## Learning Objectives


After studying this chapter, you should be able to:

- Explain the layered audio architecture from game code through [ISoundEngine](../appendices/Appendix_A_Glossary.md) to the OpenAL backend.
- Describe the roles of ISoundEngine, [ISoundSource](../appendices/Appendix_A_Glossary.md), [ISound](../appendices/Appendix_A_Glossary.md), and the Sound class.
- Trace how a sound file is loaded, cached, and played through the audio pipeline.
- Configure audio loaders and sound [manifests](../appendices/Appendix_A_Glossary.md) in mod.yaml.
- Explain the difference between UI sounds and world sounds, including player filtering.
- Describe source pooling and per-frame capping in OpenAlSoundEngine.

## Files

| File | Responsibility |
| :---- | :---- |
| `OpenRA.Game/Sound/SoundDevice.cs` | `ISoundEngine`, `ISound`, `ISoundSource`, and `SoundDevice` records. |
| `OpenRA.Game/Sound/Sound.cs` | Main API: sample caching, playback, music, video audio, and listener position. |
| `OpenRA.Game/GameRules/SoundInfo.cs` | Ruleset sound configuration (variants, prefixes, voice pools, notification pools). |
| `OpenRA.Game/GameRules/MusicInfo.cs` | Music track metadata (filename, title, hidden, volume modifier, length). |
| `OpenRA.Platforms.Default/OpenAlSoundEngine.cs` | OpenAL backend implementation: device enumeration, source pool, spatial attenuation. |
| `OpenRA.Mods.Common/FileFormats/ImaAdpcmReader.cs` | IMA ADPCM format reader. |
| `OpenRA.Mods.Common/AudioLoaders/WavLoader.cs` | WAV format loader. |
| `OpenRA.Mods.Common/AudioLoaders/OggLoader.cs` | Ogg Vorbis loader. |
| `OpenRA.Mods.Common/AudioLoaders/Mp3Loader.cs` | MP3 loader. |
| `OpenRA.Mods.Cnc/AudioLoaders/VocLoader.cs` | Westwood VOC format loader. |
| `OpenRA.Mods.Cnc/VideoLoaders/VqaLoader.cs` | VQA video loader (also produces audio). |
| `OpenRA.Mods.Common/Traits/World/MusicPlaylist.cs` | World trait that drives the music playlist, victory/defeat music, and background music. |
| `OpenRA.Game/Settings.cs` | `SoundSettings` for volume, device, mute, shuffle, etc. |
| `OpenRA.Game/ModData.cs` | Holds `SoundLoaders` and exposes them to `Sound.Initialize`. |

![Architecture diagram](images/Part_05_Chapter_01_Audio_Architecture-architecture-diagram-showing-the-main-classes-interfaces-and-9161e6.svg)

## Architecture


### Layered audio stack

```
[Game / Traits] -> [Sound] -> [ISoundEngine] -> [OpenAlSoundEngine] -> [OpenAL device]
```

The `Sound` class is the single point of contact for the rest of the game. It never talks to OpenAL directly. Instead it calls methods on the `ISoundEngine` interface, which is provided by `IPlatform.CreateSound(...)`. The only shipped implementation is `OpenAlSoundEngine` in `OpenRA.Platforms.Default`.

### Key abstractions

- `ISoundEngine` — backend contract: create sources, play sounds, pause/stop, set listener position, manage volume.
- `ISoundSource` — a loaded audio buffer (e.g., an OpenAL buffer). Created once and reused for many plays.
- `ISound` — an active playing instance (e.g., an OpenAL source). Tracks completion and position.
- `Sound` — high-level cache and playback API exposed as `Game.Sound`.

### Sound object lifetime

At startup, `Sound` receives a `SoundSettings` object and asks the platform to create an engine. It then loads audio files on demand through a `Cache<string, ISoundSource>` keyed by filename. When a game mod is loaded, `Sound.Initialize` is called with the mod's `SoundLoaders` and `IReadOnlyFileSystem`. This stops all current sounds, disposes cached sources, and rebuilds the cache for the new mod.

![Data flow  code path diagram](images/Part_05_Chapter_01_Audio_Architecture-sequence-flow-diagram-tracing-the-execution-path-from-trigge-035864.svg)

## Data Flow / Code Path


### Engine creation and initialization

```csharp
soundEngine = platform.CreateSound(soundSettings.Device);
```

`IPlatform.CreateSound` is implemented by `OpenRA.Platforms.Default` and returns an `OpenAlSoundEngine` (or a dummy engine if sound is disabled). The device string comes from the `SoundSettings.Device` field. If `soundSettings.Mute` is true, `Sound.MuteAudio()` is called immediately.

### Loading a sample

```csharp
ISoundSource LoadIntoMemory(ISoundFormat soundFormat) => soundEngine.AddSoundSourceFromMemory(
    soundFormat.GetPCMInputStream().ReadAllBytes(), soundFormat.Channels, soundFormat.SampleBits, soundFormat.SampleRate);

sounds = new Cache<string, ISoundSource>(filename => LoadSound(filename, LoadIntoMemory));
```

When `Sound.Play` is called with a filename, the cache resolves the filename, opens the file via the mod file system, tries each `ISoundLoader` until one parses the format, and then asks the engine to create a source from the decoded PCM.

### Playing a sound

The central `Play` method is:

```csharp
ISound Play(SoundType type, Player player, string name, bool headRelative, WPos pos, float volumeModifier = 1f, bool loop = false)
{
    if (string.IsNullOrEmpty(name) || DisableAllSounds || (DisableWorldSounds && type == SoundType.World))
        return null;

    if (player != null && player != player.World.LocalPlayer)
        return null;

    return soundEngine.Play2D(sounds[name],
        loop, headRelative, pos,
        InternalSoundVolume * volumeModifier, true);
}
```

`SoundType` is either `UI` or `World`. UI sounds are always head-relative and unattenuated. World sounds are placed at a `WPos` and are attenuated by distance and the listener position.

### Player filtering

`PlayToPlayer` plays a sound only for a specific player. If `player` is not the local player, the call returns null immediately. This is used for per-player notifications such as "Building complete" or "Unit ready".

### Listener position

The camera/controller sets the listener position:

```csharp
public void SetListenerPosition(WPos position)
{
    soundEngine.SetListenerPosition(position);
}
```

World sounds are attenuated relative to this listener. UI sounds are relative to the listener (head-relative) so they are not attenuated.

### Source pooling

`OpenAlSoundEngine` pre-creates a pool of 256 OpenAL sources. When a sound is played, the engine allocates an idle source, or reclaims one whose sound has completed. If the pool is exhausted and no completed sounds are reclaimable, the play request returns null.

The engine also implements per-frame capping: if more than `MaxInstancesPerFrame` (3) instances of the same sound source start within 5 frames and within `GroupDistance` (2730 world units) of each other, additional plays are dropped to prevent audio spam.

### Music and video audio

Music is loaded via `Sound.PlayMusic(MusicInfo, bool looped)` and streamed through `ISoundEngine.Play2DStream`. The `Sound.Tick` method monitors the music `ISound.Complete` flag and invokes the `onMusicComplete` callback to advance the playlist.

Video audio is decoded by the video loader and passed directly as raw PCM to `soundEngine.AddSoundSourceFromMemory` and `soundEngine.Play2D`.

![Configuration (yaml) diagram](images/Part_05_Chapter_01_Audio_Architecture-annotated-yaml-snippet-diagram-showing-the-key-fields-and-ho-6a1b98.svg)

## Configuration (YAML)


### Sound manifest

The mod manifest lists the audio file loaders:

```yaml
Loaders:
    Sound:
        - OpenRA.Mods.Common.AudioLoaders.WavLoader
        - OpenRA.Mods.Common.AudioLoaders.OggLoader
        - OpenRA.Mods.Common.AudioLoaders.Mp3Loader
```

The order matters: `Sound.LoadSound` tries each loader in order until one succeeds.

### Voices and notifications

`SoundInfo` is loaded from the manifest's `Voices` and `Notifications` files. It defines:

- `Variants` — per-actor sound file extensions (e.g., `.aud`, `.ogg`).
- `Prefixes` — per-actor path prefixes.
- `Voices` — named voice sets mapped to arrays of sound files.
- `Notifications` — named notification sets mapped to sound pools with volume modifiers and interrupt types.

Example:

```yaml
Sounds:
    Voices:
        e1:
            Select: e1sel1, e1sel2, e1sel3
            Move: e1mov1, e1mov2, e1mov3
            Attack: e1atk1, e1atk2
    Notifications:
        Building:
            VolumeModifier: 0.9
            InterruptType: Overlap
            Notifications: build1, build2
```

### Music

Music tracks are defined in the manifest's `Music` files:

```yaml
Music:
    intro:
        Title: Act on Instinct
        Filename: intro
        Extension: aud
        VolumeModifier: 1.0
        Hidden: false
```

`MusicInfo` computes the actual filename as `<Filename or key>.<Extension>` and lazily probes its length and existence through the file system.

### MusicPlaylist

The world actor carries a `MusicPlaylist` trait:

```yaml
World:
    MusicPlaylist:
        StartingMusic: intro
        VictoryMusic: win1
        DefeatMusic: lose1
        BackgroundMusic: map1
        DisableWorldSounds: false
```

## Interconnectivity

- **Depends on:** [Part 2.1 — MiniYaml Parser](Part_02_Chapter_01_MiniYaml.md), [Part 2.3 — FieldLoader](Part_02_Chapter_03_FieldLoader.md), [Part 3.1 — Mod SDK and Project Structure](Part_03_Chapter_01_Mod_SDK.md), [Part 6.3 — Virtual File System](Part_06_Chapter_03_VFS.md), [Part 4.2 — WorldRenderer](Part_04_Chapter_02_WorldRenderer.md).
- **Used by:** [Part 5.2 — Spatial Attenuation](Part_05_Chapter_02_Spatial_Attenuation.md), [Part 5.3 — Music](Part_05_Chapter_03_Music.md), [Part 5.4 — Sound Triggers](Part_05_Chapter_04_Sound_Triggers.md), Part 1 (Actor/World traits), Part 8 (AI notifications), Part 9 (network/local determinism boundary).

![Algorithms diagram](images/Part_05_Chapter_01_Audio_Architecture-algorithm-diagram-or-pseudocode-flowchart-for-the-non-trivia-5983ed.svg)

## Algorithms


### Sound loader selection

`Sound.LoadSound<T>` iterates through `loaders` and rewinds the stream to position 0 for each attempt. The first loader that returns `true` from `TryParseSound` wins. If none succeed, an `InvalidDataException` is thrown.

### Per-player sound filtering

The filter `if (player != null && player != player.World.LocalPlayer) return null;` guarantees that `PlayToPlayer` sounds are only audible for the owning player. This is the boundary between the authoritative simulation and the local-only audio presentation.

### Source pool reclamation

In `OpenAlSoundEngine.Play2D`, if no idle source is available, the engine scans the pool for slots whose `ISound.Complete` flag is true. It rewinds the OpenAL source, detaches its buffer, unbinds the sound, and reactivates the slot. This lets a 256-source pool handle a large number of short, overlapping sounds.

### Instance throttling

```csharp
if (++instances == MaxInstancesPerFrame)
    return null;
```

The same sound starting too many times in a small area within a few frames is dropped. This is a presentation-layer optimization, not a simulation-layer change, so it does not affect gameplay determinism.

![Extension points diagram](images/Part_05_Chapter_01_Audio_Architecture-extension-hook-diagram-showing-the-interface-s-to-implement-b4a27b.svg)

## Extension Points


### Add a new audio format

Implement `ISoundLoader` and `ISoundFormat` in a mod. Register the loader in the manifest's `Loaders: Sound:` list. The loader must parse the file from a `Stream`, expose `Channels`, `SampleBits`, `SampleRate`, and `LengthInSeconds`, and return a PCM stream via `GetPCMInputStream()`.

### Add a custom sound engine

Implement `ISoundEngine` and create a new platform assembly that provides it via `IPlatform.CreateSound`. This is how alternative backends (e.g., a WASAPI or SDL backend) could be integrated.

### Add new voice or notification pools

Define them in the mod's `SoundInfo` YAML. The keys are arbitrary and are looked up by traits such as `Voiced` and `AnnounceOnBuild`.

### Override music behavior

Subclass `MusicPlaylist` or add a new world trait that calls `Game.Sound.PlayMusic(...)` directly. The playlist trait is only one possible driver; music can be triggered from any world trait.

### Disable world audio per map

Set `MusicPlaylist.DisableWorldSounds: true` to silence combat and ambient world sounds while keeping UI sounds and music.

## Practical Example

This section ties the YAML actor definition, the trait trigger, and the `Game.Sound` API together with a concrete example.

![Practical example: playing a sound from a trait diagram](images/Part_05_Chapter_01_Audio_Architecture-signal-flow-diagram-from-yaml-actor-trait-event-soundengine-8f354b.svg)

### Practical Example: Playing a Sound from a Trait


First, define the actor in the mod's rules YAML and add the trait that will react when the unit is created:

```yaml
myunit:
    Inherits: ^Vehicle
    Buildable:
        Queue: Vehicle
        BuildPaletteOrder: 10
    AnnounceOnCreated:
    Valued:
        Cost: 500
```

The trait is a minimal C# class that implements `INotifyCreated` and calls the sound API:

```csharp
using OpenRA.Traits;

class AnnounceOnCreatedInfo : TraitInfo<AnnounceOnCreated> { }

class AnnounceOnCreated : INotifyCreated
{
    public void Created(Actor self)
    {
        // Positional world sound played at the actor's location.
        Game.Sound.Play(SoundType.World, "unit-online", self.CenterPosition);

        // Per-player notification, filtered to the owning player.
        Game.Sound.PlayNotification(self.World, self.Owner, "Speech", "UnitReady", self.Owner.Faction.InternalName);
    }
}
```

When the actor defined in YAML is created, the `AnnounceOnCreated` trait receives the `Created` event. The YAML rule selects which actor gets the behavior; the trait decides when the trigger fires; the C# code calls `Game.Sound` to enqueue the sound; and the `SoundEngine` resolves the asset through the mod file system, loads the decoded PCM into an `ISoundSource`, and asks the OpenAL backend for a source to play it.

![Common pitfalls  guardrails diagram](images/Part_05_Chapter_01_Audio_Architecture-checklist-infographic-style-diagram-summarizing-the-top-pitf-fb069e.svg)

## Common Pitfalls / Guardrails


- **Determinism:** audio playback is client-side. `Sound` is not part of the lockstep simulation, and all randomness used for voice lines uses `Game.CosmeticRandom` (or `world.LocalRandom`), not the world sync random.
- **Missing files:** `Sound.LoadSound<T>` returns `default` if the file does not exist. Callers that ignore null checks may crash when a sound file is absent.
- **Format support:** not every mod ships every loader. A mod that uses MP3 music must include `Mp3Loader` in its manifest.
- **Volume hierarchy:** the final volume is a product of the engine `Volume`, the `InternalSoundVolume` multiplier, the per-call `volumeModifier`, and the `MusicInfo.VolumeModifier` (for music).
- **Source exhaustion:** a busy battlefield can exhaust the 256-source pool. The engine drops new sounds rather than crashing; the throttling heuristic reduces this risk.
- **Listener position:** world sounds must have the listener updated by the camera or they will be attenuated relative to the default origin.

## What to read next

- [Part 5.2 — Spatial Attenuation](Part_05_Chapter_02_Spatial_Attenuation.md) for how world sounds are positioned in 3D space.
- [Part 5.3 — Music](Part_05_Chapter_03_Music.md) for the music playlist and streaming logic that runs on top of the sound engine.
- [Part 5.4 — Sound Triggers](Part_05_Chapter_04_Sound_Triggers.md) for the traits and activities that call into the audio API.

## Summary

This chapter explains the layered audio architecture that drives OpenRA's sound engine, from the backend-agnostic `ISoundEngine` interface through the OpenAL backend to the `Sound` API that game code and traits consume.

If any of the concepts above feel unclear, review the relevant section before continuing. For source files and further reading, see the References section.


## References

- `OpenRA.Game/Sound/SoundDevice.cs` — backend interface.
- `OpenRA.Game/Sound/Sound.cs` — high-level audio API.
- `OpenRA.Platforms.Default/OpenAlSoundEngine.cs` — OpenAL backend.
- `OpenRA.Game/GameRules/SoundInfo.cs` — ruleset sound configuration.
- `OpenRA.Game/GameRules/MusicInfo.cs` — music metadata.
- `OpenRA.Mods.Common/Traits/World/MusicPlaylist.cs` — music playlist driver.
- `OpenRA.Mods.Common/AudioLoaders/*.cs` — format loaders.
- `OpenRA.Game/Settings.cs` — sound settings.
- `OpenRA.Game/ModData.cs` — loader registration and sound initialization.
- [OpenRA sound notification docs](https://docs.openra.net/en/release/traits/)

### External resources

- [OpenAL Soft](https://openal-soft.org) — the open-source implementation of the spatial audio API used by OpenRA.

## What to read next

- [Part 5.3 — Music](Part_05_Chapter_03_Music.md) for the music playlist and track selection.
- [Part 5.4 — Sound Triggers](Part_05_Chapter_04_Sound_Triggers.md) for voice and notification triggers.
- [Appendix H — Asset Visual Reference](../appendices/Appendix_H_Asset_Visual_Reference.md) for a categorical lookup of audio file formats, YAML definitions, and engine classes.