# Chapter 5.3 — Music

## Purpose

Music in OpenRA is driven by a world-level playlist trait that selects tracks, handles victory/defeat jingles, supports background music, and respects player settings such as shuffle and mute. The actual decoding and streaming is handled by the `Sound` layer described in [Part 5.1 — Audio Architecture](Part_05_Chapter_01_Audio_Architecture.md). This chapter focuses on the music metadata, the playlist state machine, and the configuration that controls it.

## Learning Objectives


After studying this chapter, you should be able to:

- Explain how MusicInfo tracks are loaded from the manifest and probed by the file system.
- Describe the [MusicPlaylist](../appendices/Appendix_A_Glossary.md) state machine and its handling of shuffle, repeat, and background music.
- Trace the music flow from map loading through playback, completion, and song advancement.
- Configure music tracks and the MusicPlaylist world trait in YAML.
- Explain the difference between streaming music and in-memory sound effects.
- Implement victory/defeat and background music transitions.

## Files

| File | Responsibility |
| :---- | :---- |
| `OpenRA.Game/GameRules/MusicInfo.cs` | Metadata for a single music track (title, filename, extension, volume, hidden, length). |
| `OpenRA.Mods.Common/Traits/World/MusicPlaylist.cs` | World trait that drives playback, playlist, background music, and game-over music. |
| `OpenRA.Game/Sound/Sound.cs` | `PlayMusic`, `PlayMusicThen`, `StopMusic`, `Tick`, music volume control. |
| `OpenRA.Game/Settings.cs` | `SoundSettings.MusicVolume`, `Repeat`, `Shuffle`, `MuteBackgroundMusic`. |
| `OpenRA.Game/Map/Map.cs` | Access to `Map.Rules.Music` and `InstalledMusic`. |
| `OpenRA.Game/Map/MapPreview.cs` | Uses `Ruleset.LoadDefaultsForTileSet` to pre-load music for the music preview. |
| `mods/*/audio/music.yaml` | Music track definitions for each mod. |

![Architecture diagram](images/Part_05_Chapter_03_Music-architecture-diagram-showing-the-main-classes-interfaces-and-9161e6.svg)

## Architecture


### MusicInfo as a lightweight ruleset entry

`MusicInfo` is created during ruleset loading from the manifest's `Music` files. It stores:

- `Title` — display name.
- `Filename` — actual file path computed as `<Filename or key>.<Extension>`.
- `VolumeModifier` — per-track volume scaling.
- `Hidden` — whether the track appears in the playlist UI.
- `Length` — duration in seconds, probed when the file is first loaded.
- `Exists` — whether the file was found in the mod's file system.

The `Load(IReadOnlyFileSystem)` method is called during map loading to probe the file and set `Exists` and `Length`. Tracks that cannot be found are skipped by the playlist.

### MusicPlaylist state machine

`MusicPlaylist` is a world trait that holds the current song and the background song. Its behavior is roughly:

1. On construction, build the `playlist` array from `InstalledMusic` excluding `Hidden` tracks.
2. Shuffle the playlist into `random` if shuffle is enabled.
3. Pick a starting song (either `StartingMusic`, `BackgroundMusic`, or a random track).
4. On `PostWorldLoaded`, play the current song.
5. When the song ends, `PlayNextSong` selects the next track and starts it.
6. On game over, switch to `VictoryMusic` or `DefeatMusic` as background.
7. When the player stops the music, fall back to `BackgroundMusic` if one is defined.

### Background music

`BackgroundMusic` is a track that plays when no other song is active and cannot be paused (but can be muted if `AllowMuteBackgroundMusic` is true). The `CurrentSongIsBackground` flag tracks whether the active track is the background track, so it is not advanced when it ends.

### Streaming vs in-memory

Music is streamed rather than loaded entirely into memory. `Sound.PlayMusic` calls `soundEngine.Play2DStream` with the decoded PCM stream, so large music files do not consume the source-memory cache.

![Data flow  code path diagram](images/Part_05_Chapter_03_Music-sequence-flow-diagram-tracing-the-execution-path-from-trigge-035864.svg)

## Data Flow / Code Path


### Loading music metadata

During `Ruleset.LoadDefaults`, the engine calls:

```csharp
var music = MergeOrDefault("Manifest,Music", fs, m.Music, null, null,
    k => new MusicInfo(k.Key, k.Value));
```

Each entry becomes a `MusicInfo` keyed by its YAML node name. Later, when a map is loaded, `MusicInfo.Load(fileSystem)` probes the file.

### Starting playback

The playlist starts music in `PostWorldLoaded`:

```csharp
void IPostWorldLoaded.PostWorldLoaded(World world, WorldRenderer wr)
{
    Game.Sound.DisableWorldSounds = info.DisableWorldSounds;

    if (!world.IsLoadingGameSave)
        Play();
}
```

`Play()` calls `Game.Sound.PlayMusicThen(currentSong, PlayNextSong)`.

### Advancing songs

`Sound.Tick` checks whether the music instance is complete:

```csharp
public void Tick()
{
    if (MusicPlaying && music.Complete)
    {
        StopMusic();
        onMusicComplete();
    }
}
```

When complete, `PlayNextSong` is invoked. It picks the next song from the shuffled or ordered playlist and calls `Play()` again.

### Resuming the same song

`PlayMusicThen` first checks if the requested song is already loaded:

```csharp
if (m == CurrentMusic && music != null)
{
    soundEngine.PauseSound(music, false);
    MusicPlaying = true;
    return;
}
```

This avoids restarting the file when the music volume is toggled or the playlist is paused and resumed.

### Game-over music

`MusicPlaylist` implements `IGameOver`. On game over it sets the background song to the victory or defeat track and calls `Stop()`, which immediately transitions to the new background music:

```csharp
if (SongExists(info.VictoryMusic))
{
    currentBackgroundSong = world.Map.Rules.Music[info.VictoryMusic];
    Stop();
}
```

![Configuration (yaml) diagram](images/Part_05_Chapter_03_Music-annotated-yaml-snippet-diagram-showing-the-key-fields-and-ho-6a1b98.svg)

## Configuration (YAML)


### Music manifest

Music tracks are declared in the mod manifest:

```yaml
Music:
    mods/ra/audio/music.yaml
```

### Track definition

```yaml
intro:
    Title: Act on Instinct
    Filename: intro
    Extension: aud
    VolumeModifier: 1.0

map1:
    Title: Map Theme
    Filename: map1
    Extension: aud
    Hidden: false
```

If `Filename` is omitted, the YAML key is used as the base filename. The default extension is `aud` if `Extension` is omitted.

### Playlist trait

The world actor carries the playlist:

```yaml
World:
    MusicPlaylist:
        StartingMusic: intro
        VictoryMusic: win1
        DefeatMusic: lose1
        BackgroundMusic: map1
        AllowMuteBackgroundMusic: false
        DisableWorldSounds: false
```

### Player settings

In `settings.yaml` or the in-game settings panel:

- `MusicVolume` — global music gain.
- `Repeat` — loop the current track.
- `Shuffle` — randomize the playlist order.
- `MuteBackgroundMusic` — silence the background track (if `AllowMuteBackgroundMusic` is true).

## Interconnectivity

- **Depends on:** [Part 2.1 — MiniYaml Parser](Part_02_Chapter_01_MiniYaml.md), [Part 2.4 — Rulesets, Actors, and Weapons](Part_02_Chapter_04_Rules_Weapons.md), [Part 3.1 — Mod SDK and Project Structure](Part_03_Chapter_01_Mod_SDK.md), [Part 5.1 — Audio Architecture](Part_05_Chapter_01_Audio_Architecture.md), [Part 6.3 — Virtual File System](Part_06_Chapter_03_VFS.md).
- **Used by:** Part 10 (official mods that ship music packs), UI music browser widgets, and the end-game screen.

![Algorithms diagram](images/Part_05_Chapter_03_Music-algorithm-diagram-or-pseudocode-flowchart-for-the-non-trivia-5983ed.svg)

## Algorithms


### Playlist selection

```csharp
var songs = Game.Settings.Sound.Shuffle ? random : playlist;

var next = reverse
    ? songs.Reverse().SkipWhile(m => m != currentSong).Skip(1).FirstOrDefault() ?? songs.Reverse().FirstOrDefault()
    : songs.SkipWhile(m => m != currentSong).Skip(1).FirstOrDefault() ?? songs.FirstOrDefault();
```

When shuffle is on, the playlist walks through the pre-shuffled `random` array. When shuffle is off, it walks through the original `playlist` array. In either case, it wraps around to the first track when it reaches the end.

### Background/foreground priority

- `CurrentSongIsBackground == true` means the active track is the background music. When it ends, the playlist does not advance it; it simply re-evaluates whether the background music should resume.
- `CurrentSongIsBackground == false` means the active track is a normal playlist song. When it ends, the playlist advances to the next song.

### Music file probing

`MusicInfo.Load` opens the file once, tries every registered sound loader, and records the first successful duration. If no loader can parse the file, `Exists` remains false and the track is skipped. This is why a mod that ships music in a new format must register the loader in the manifest.

![Extension points diagram](images/Part_05_Chapter_03_Music-extension-hook-diagram-showing-the-interface-s-to-implement-b4a27b.svg)

## Extension Points


### Add new music tracks

Add entries to the mod's music YAML and ensure the files are packaged in the mod's [VFS](../appendices/Appendix_A_Glossary.md) paths. No code changes are needed.

### Change playlist behavior

`MusicPlaylist` is a world trait. A mod can replace it with a custom trait that drives `Game.Sound.PlayMusic` directly. For example, a campaign could add a trait that plays specific tracks based on scripted objectives.

### Add a new music format

Register a new `ISoundLoader` as described in [Part 5.1 — Audio Architecture](Part_05_Chapter_01_Audio_Architecture.md). Music files are decoded through the same loader pipeline as sound effects.

### Volume and muting

Mods can expose `MusicInfo.VolumeModifier` per track and `SoundSettings.MusicVolume` globally. A custom UI widget can change these at runtime without restarting the game.

### Victory/defeat music

Set `VictoryMusic` and `DefeatMusic` in the `MusicPlaylist` trait to play jingles on game over. If a map should not play a jingle, leave these fields null.

![Common pitfalls  guardrails diagram](images/Part_05_Chapter_03_Music-checklist-infographic-style-diagram-summarizing-the-top-pitf-fb069e.svg)

## Common Pitfalls / Guardrails


- **File existence:** if a music file is missing, `MusicInfo.Exists` is false and the track is silently skipped. The playlist will still work, but the missing track will never play.
- **Format loaders:** `MusicInfo.Load` tries every sound loader. If a mod uses MP3 or OGG, the corresponding loader must be registered in the manifest's `Loaders: Sound:` list.
- **Determinism:** music playback is client-side. The `random` playlist order uses `Game.CosmeticRandom`, not the world sync random.
- **Background music loop:** background music is not advanced by `PlayNextSong`. If it stops, it will restart automatically unless muted.
- **Save/load:** `MusicPlaylist` implements `INotifyGameLoaded` and resumes playback after a savegame is loaded.
- **Length probing:** `MusicInfo.Length` is set only when the file is probed. Code that reads `Length` before `Load` is called may see zero.

## What to read next

- [Part 5.1 — Audio Architecture](Part_05_Chapter_01_Audio_Architecture.md) for the sound engine that decodes and streams music tracks.
- [Part 5.4 — Sound Triggers](Part_05_Chapter_04_Sound_Triggers.md) for how the audio system is used from traits and activities.
- [Part 6.5 — Asset Loaders](Part_06_Chapter_05_Asset_Loaders.md) for the sound loaders that parse music file formats.

## Summary

This chapter explains how music in OpenRA is driven by a world-level playlist trait that selects tracks, handles victory/defeat jingles, supports background music, and respects player settings such as shuffle and mute.

After reading this chapter, you should be able to:

- On construction, build the `playlist` array from `InstalledMusic` excluding `Hidden` tracks.
- Shuffle the playlist into `random` if shuffle is enabled.
- Pick a starting song (either `StartingMusic`, `BackgroundMusic`, or a random track).
- On `PostWorldLoaded`, play the current song.
- When the song ends, `PlayNextSong` selects the next track and starts it.
- On game over, switch to `VictoryMusic` or `DefeatMusic` as background.
- When the player stops the music, fall back to `BackgroundMusic` if one is defined.

If any of the concepts above feel unclear, review the relevant section before continuing. For source files and further reading, see the References section.


## References

- `OpenRA.Game/GameRules/MusicInfo.cs` — music track metadata.
- `OpenRA.Mods.Common/Traits/World/MusicPlaylist.cs` — playlist driver.
- `OpenRA.Game/Sound/Sound.cs` — music playback and `Tick`.
- `OpenRA.Game/Settings.cs` — sound settings.
- `OpenRA.Game/Map/Map.cs` — map rules and `InstalledMusic`.
- `mods/ra/audio/music.yaml` — example music definitions.