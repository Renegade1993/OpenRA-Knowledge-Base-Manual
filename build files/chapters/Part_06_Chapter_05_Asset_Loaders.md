# Chapter 6.5 — Asset Loaders

## Purpose

OpenRA assets come in many formats: legacy Westwood [sprites](../appendices/Appendix_A_Glossary.md) (SHP/TMP), audio (AUD/VOC/WAV/OGG/MP3), video (VQA), and modern formats (PNG). The engine uses a plugin-style loader system so each format can be parsed independently. This chapter covers the loader interfaces for sprites, [sequences](../appendices/Appendix_A_Glossary.md), audio, and video, and how they are registered and invoked.

## Learning Objectives


After studying this chapter, you should be able to:

- Explain the loader chain architecture for sprites, sequences, audio, and video.
- Describe the interfaces ISpriteLoader, ISpriteSequenceLoader, ISoundLoader, and IVideoLoader.
- Trace the sprite pipeline from raw file to GPU sheet.
- Configure asset loaders in the mod manifest.
- Implement a new loader for a custom asset format.
- Explain how sprite sequences and sheet packing work.

## Files

| File | Responsibility |
| :---- | :---- |
| `OpenRA.Game/Graphics/SpriteLoader.cs` | `ISpriteLoader`, `ISpriteFrame`, `FrameCache`, `FrameLoader`, `SpriteFrameType`. |
| `OpenRA.Game/Graphics/SequenceSet.cs` | `ISpriteSequence`, `ISpriteSequenceLoader`, `SequenceSet`. |
| `OpenRA.Game/Graphics/SpriteCache.cs` | Caches sprite frames and packs them into GPU sheets. |
| `OpenRA.Game/Sound/Sound.cs` | `ISoundLoader`, `ISoundFormat`. |
| `OpenRA.Game/Graphics/VideoLoader.cs` | `IVideoLoader`, `IVideo`. |
| `OpenRA.Game/ModData.cs` | Holds `SpriteLoaders`, `SpriteSequenceLoader`, `SoundLoaders`, `VideoLoaders`, and `PackageLoaders`. |
| `OpenRA.Mods.Common/SpriteLoaders/*.cs` | Common sprite loaders (Png, Shp, ShpTS, Tmp, etc.). |
| `OpenRA.Mods.Common/AudioLoaders/*.cs` | Common audio loaders (Wav, Ogg, Mp3). |
| `OpenRA.Mods.Cnc/AudioLoaders/VocLoader.cs` | Westwood VOC loader. |
| `OpenRA.Mods.Cnc/VideoLoaders/VqaLoader.cs` | Westwood VQA video loader. |
| `OpenRA.Game/Graphics/Sprite.cs` | In-memory sprite reference. |
| `OpenRA.Game/Graphics/Sheet.cs` | GPU texture sheet. |

![Architecture diagram](images/Part_06_Chapter_05_Asset_Loaders-architecture-diagram-showing-the-main-classes-interfaces-and-9161e6.svg)

## Architecture


### Loader chains

Each asset category has a loader chain:

```
[File request] -> [FrameLoader/SoundLoader/VideoLoader] -> tries each ISpriteLoader/ISoundLoader/IVideoLoader -> returns parsed asset
```

`ModData` stores the arrays of loaders discovered from the mod manifest. When an asset is requested, the engine tries each loader in order until one succeeds.

### Sprite pipeline

```
[Sprite file] -> [ISpriteLoader] -> [ISpriteFrame[]] -> [SpriteCache] -> [Sheet] -> [Sprite]
```

A sprite loader reads the raw file and produces one or more `ISpriteFrame` objects. The `SpriteCache` reserves space on GPU sheets and, when `LoadSprites` is called, uploads the frames and creates `Sprite` objects.

### Sequence pipeline

```
[sequences/*.yaml] -> [ISpriteSequenceLoader] -> [ISpriteSequence dictionary] -> [SpriteCache] -> resolved sprites
```

Sequences are YAML definitions that describe how a sprite file is sliced into frames, facings, and animations. The `ISpriteSequenceLoader` parses the YAML and creates `ISpriteSequence` objects. Sequences are resolved lazily through the `SpriteCache`.

### Audio pipeline

```
[audio file] -> [ISoundLoader] -> [ISoundFormat] -> [ISoundEngine] -> [ISoundSource]
```

Audio loaders parse the file and expose a PCM stream. The sound engine then creates a source from the PCM data.

### Video pipeline

```
[video file] -> [IVideoLoader] -> [IVideo] -> [renderer] + [sound engine]
```

Video loaders decode frames and audio. The renderer displays frames, and the sound engine plays the audio track.

![Data flow  code path diagram](images/Part_06_Chapter_05_Asset_Loaders-sequence-flow-diagram-tracing-the-execution-path-from-trigge-035864.svg)

## Data Flow / Code Path


### Loading sprite frames

```csharp
public static ISpriteFrame[] GetFrames(Stream stream, ISpriteLoader[] loaders, string filename, out TypeDictionary metadata)
{
    metadata = null;
    foreach (var loader in loaders)
        if (loader.TryParseSprite(stream, filename, out var frames, out metadata))
            return frames;

    return null;
}
```

The first loader that recognizes the file wins. `metadata` can contain format-specific data (e.g., embedded palettes).`

### Sprite cache

`SpriteCache` reserves sprite slots on GPU sheets. It is created during `SequenceSet` construction and loaded after the world is ready:

```csharp
public void LoadSprites()
{
    SpriteCache.LoadReservations(modData);
    foreach (var sequences in images.Values)
        foreach (var sequence in sequences)
            sequence.Value.ResolveSprites(SpriteCache);
}
```

### Loading sequences

```csharp
IReadOnlyDictionary<string, IReadOnlyDictionary<string, ISpriteSequence>> Load(...)
{
    var nodes = MiniYaml.Load(fileSystem, modData.Manifest.Sequences, additionalSequences);
    var images = new Dictionary<string, IReadOnlyDictionary<string, ISpriteSequence>>();
    foreach (var node in nodes)
    {
        if (node.Key.StartsWith(ActorInfo.AbstractActorPrefix))
            continue;

        images[node.Key] = modData.SpriteSequenceLoader.ParseSequences(modData, TileSet, SpriteCache, node);
    }

    return images;
}
```

Each top-level YAML node is an "image" (e.g., `e1`, `tank`) that contains multiple named sequences (e.g., `idle`, `run`, `die`).

### Loading audio

```csharp
T LoadSound<T>(string filename, Func<ISoundFormat, T> loadFormat)
{
    using (var stream = fileSystem.Open(filename))
    {
        foreach (var loader in loaders)
        {
            stream.Position = 0;
            if (loader.TryParseSound(stream, out var soundFormat))
            {
                var source = loadFormat(soundFormat);
                soundFormat.Dispose();
                return source;
            }
        }
    }

    throw new InvalidDataException(filename + " is not a valid sound file!");
}
```

### Loading video

```csharp
public static IVideo GetVideo(Stream stream, bool useFramePadding, IVideoLoader[] loaders)
{
    foreach (var loader in loaders)
        if (loader.TryParseVideo(stream, useFramePadding, out var video))
            return video;

    return null;
}
```

![Configuration (yaml) diagram](images/Part_06_Chapter_05_Asset_Loaders-annotated-yaml-snippet-diagram-showing-the-key-fields-and-ho-6a1b98.svg)

## Configuration (YAML)


### Loader registration

The mod manifest declares loaders for each asset type:

```yaml
Loaders:
    Sprite:
        - OpenRA.Mods.Common.SpriteLoaders.PngLoader
        - OpenRA.Mods.Common.SpriteLoaders.ShpLoader
        - OpenRA.Mods.Common.SpriteLoaders.ShpTSLoader
        - OpenRA.Mods.Common.SpriteLoaders.TmpLoader
    SpriteSequence:
        - OpenRA.Mods.Common.SpriteLoaders.DefaultSpriteSequenceLoader
    Sound:
        - OpenRA.Mods.Common.AudioLoaders.AudLoader
        - OpenRA.Mods.Common.AudioLoaders.WavLoader
        - OpenRA.Mods.Common.AudioLoaders.OggLoader
        - OpenRA.Mods.Common.AudioLoaders.Mp3Loader
    Video:
        - OpenRA.Mods.Cnc.VideoLoaders.VqaLoader
    Package:
        - OpenRA.Mods.Common.FileSystem.MixFileLoader
```

### Sequence definitions

Sequences are defined in YAML files listed under `Sequences` in the manifest:

```yaml
Sequences:
    mods/ra/sequences/infantry.yaml
```

Example sequence:

```yaml
e1:
    idle:
        Start: 0
        Facings: 8
    die:
        Start: 8
        Length: 8
```

## Interconnectivity

- **Depends on:** [Part 2.1 — MiniYaml Parser](Part_02_Chapter_01_MiniYaml.md), [Part 3.1 — Mod SDK and Project Structure](Part_03_Chapter_01_Mod_SDK.md), [Part 6.3 — Virtual File System](Part_06_Chapter_03_VFS.md), [Part 4.1 — Renderer, Sheet, and Sprite](Part_04_Chapter_01_Renderer.md), [Part 5.1 — Audio Architecture](Part_05_Chapter_01_Audio_Architecture.md).
- **Used by:** [Part 4.2 — WorldRenderer](Part_04_Chapter_02_WorldRenderer.md), [Part 5.4 — Sound Triggers](Part_05_Chapter_04_Sound_Triggers.md), Part 10 (mods define their assets).

For a quick reference of sprite, audio, and video asset formats and their engine loaders, see [Appendix H — Asset Visual Reference](../appendices/Appendix_H_Asset_Visual_Reference.md).

![Algorithms diagram](images/Part_06_Chapter_05_Asset_Loaders-algorithm-diagram-or-pseudocode-flowchart-for-the-non-trivia-5983ed.svg)

## Algorithms


### Sprite frame types

`SpriteFrameType` defines the pixel format:

- `Indexed8` — 8-bit palette index.
- `Bgra32` — 32-bit BGRA.
- `Bgr24` — 24-bit BGR.
- `Rgba32` — 32-bit RGBA.
- `Rgb24` — 24-bit RGB.

The renderer uses the type to decide whether to apply a palette or upload directly.

### Sprite sheet packing

`SpriteCache` packs multiple frames into larger GPU sheets based on the frame type (indexed vs. BGRA) and size. The size of the sheets is controlled by `RendererConstants` in the manifest:

```yaml
RendererConstants:
    SequenceBgraSheetSize: 2048
    SequenceIndexedSheetSize: 2048
```

### Sequence parsing

`DefaultSpriteSequenceLoader` parses sequence YAML and creates `SpriteSequence` objects. Each sequence specifies:

- `Start` / `Length` / `Stride` — frame indices.
- `Facings` — number of orientations.
- `Tick` — animation interval.
- `ZOffset` / `ShadowZOffset` — draw depth.
- `Offset` / `FlipX` / `FlipY` — transform.
- `Transpose` / `ReverseFacings` — orientation mapping.

### Audio format detection

Each `ISoundLoader` inspects the stream's header. The `WavLoader` checks for RIFF/WAVE, `OggLoader` checks for Ogg pages, `AudLoader` checks for Westwood AUD magic, etc.

### Video frame padding

Some video formats need frame padding to be uploaded as textures. The `useFramePadding` flag is passed to the loader so it can add the necessary padding.

![Extension points diagram](images/Part_06_Chapter_05_Asset_Loaders-extension-hook-diagram-showing-the-interface-s-to-implement-b4a27b.svg)

## Extension Points


### Add a new sprite loader

Implement `ISpriteLoader` and register it in the manifest. The loader should:

- Recognize the file format from the stream.
- Return `ISpriteFrame[]` with the correct `SpriteFrameType`.
- Optionally return metadata via `TypeDictionary`.

### Add a new sequence loader

Implement `ISpriteSequenceLoader` and register it. The loader parses MiniYaml and returns `ISpriteSequence` objects. This is useful for custom animation systems.

### Add a new audio format

Implement `ISoundLoader` and `ISoundFormat`. The loader must expose the number of channels, sample bits, sample rate, and a PCM stream.

### Add a new video format

Implement `IVideoLoader` and `IVideo`. The loader must expose frame count, dimensions, BGRA frame data, and optionally audio.

### Add custom metadata

A sprite loader can return arbitrary metadata in a `TypeDictionary`. Downstream code can read this metadata (e.g., a palette override) from the cache.

![Common pitfalls  guardrails diagram](images/Part_06_Chapter_05_Asset_Loaders-checklist-infographic-style-diagram-summarizing-the-top-pitf-fb069e.svg)

## Common Pitfalls / Guardrails


- **Stream position:** loaders must reset the stream position if they fail, so the next loader can read from the beginning.
- **Frame type:** returning the wrong `SpriteFrameType` will cause visual corruption or palette errors.
- **Sheet size:** very large frames may exceed the configured sheet size. Increase `SequenceBgraSheetSize` or split the asset.
- **Audio format:** the sound engine supports common channel/sample/rate combinations. Unusual formats may not play.
- **Video audio:** video audio must be decoded to PCM before being passed to the sound engine. The loader is responsible for decompression.
- **Loader order:** put the most common or specific loaders first to reduce the number of failed parse attempts.
- **Caching:** `FrameCache` and `SpriteCache` cache assets by filename. Mods that dynamically swap assets should understand the cache invalidation model.

## What to read next

- [Part 4.1 — Renderer, Sheet, and Sprite](Part_04_Chapter_01_Renderer.md) for how loaded sprites and sequences are packed into sheets.
- [Part 5.1 — Audio Architecture](Part_05_Chapter_01_Audio_Architecture.md) for the sound engine that consumes audio loaders.
- [Part 6.3 — Virtual File System](Part_06_Chapter_03_VFS.md) for the package layer that asset loaders read from.

## Summary

This chapter explains how OpenRA loads legacy and modern asset formats through its sprite, sequence, audio, and video loaders.

If any of the concepts above feel unclear, review the relevant section before continuing. For source files and further reading, see the References section.


## References

- `OpenRA.Game/Graphics/SpriteLoader.cs` — sprite loader interface.
- `OpenRA.Game/Graphics/SequenceSet.cs` — sequence loader interface.
- `OpenRA.Game/Graphics/SpriteCache.cs` — sprite cache and sheet packing.
- `OpenRA.Game/Sound/Sound.cs` — audio loader interface.
- `OpenRA.Game/Graphics/VideoLoader.cs` — video loader interface.
- `OpenRA.Game/Graphics/Video.cs` — video interface.
- `OpenRA.Game/ModData.cs` — loader registration.
- `OpenRA.Mods.Common/SpriteLoaders/*.cs` — sprite loader implementations.
- `OpenRA.Mods.Common/AudioLoaders/*.cs` — audio loader implementations.
- `OpenRA.Mods.Cnc/VideoLoaders/VqaLoader.cs` — VQA loader.
- `OpenRA.Mods.Cnc/AudioLoaders/VocLoader.cs` — VOC loader.