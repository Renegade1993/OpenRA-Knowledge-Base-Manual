# Appendix H — Asset Visual Reference

This appendix is a categorical field guide to every asset type that OpenRA loads, renders, plays, or simulates. For each category it shows the raw file format, the YAML file that wires the asset into the engine, the C# class or loader that owns it, a plain-text visual placeholder, and any special notes. Use it when you need to answer "what kind of asset is this and where is it defined?".

> **Visual note:** All previews in this appendix are placeholder descriptions or diagrams. No copyrighted game art is embedded.

## How to read the tables

Each table uses the same columns:

| Column | Meaning |
| :---- | :---- |
| **Asset** | The name of the asset type in modding terms. |
| **File Format(s)** | The raw file extension(s) the engine reads. |
| **Definition YAML** | The YAML file(s) and manifest key that tell the engine how to use the asset. |
| **Engine Loader / Class** | The C# class, interface, or loader responsible for the asset. |
| **Visual Preview** | A description of what the asset looks like in-game. |
| **Notes** | Anything special: palette usage, tileset rules, spatial audio, etc. |

---

## Sprites / Sprite Sequences

Sprites are the 2D bitmaps that actors, projectiles, effects, and overlays draw on screen. A *sequence* is a named animation that maps frames from a sprite file to an actor state.

| Asset | File Format(s) | Definition YAML | Engine Loader / Class | Visual Preview | Notes |
| :---- | :---- | :---- | :---- | :---- | :---- |
| Unit / vehicle sprite | `.shp`, `.shp(TS)`, `.png` | `sequences/*.yaml`, `mod.yaml` → `Sequences` | `DefaultSpriteSequence`, `ClassicSpriteSequence`, `ISpriteSequence` (`OpenRA.Game/Graphics/SequenceSet.cs`), `SpriteCache` (`OpenRA.Game/Graphics/SpriteCache.cs`), `SheetBuilder` (`OpenRA.Game/Graphics/SheetBuilder.cs`) | A rectangular sprite sheet; each cell is one frame of the unit viewed from a fixed angle. | `Facings` duplicates frames for 8 or 32 orientations. `DepthSprite` can give per-pixel depth. |
| Infantry sprite | `.shp`, `.png` | `sequences/infantry.yaml` | same as above | A strip of walking frames, repeated for 8 facing directions. | Uses `Tick` for gait timing and `Transpose` or `Facings` for orientation. `WithInfantryBody` selects the sequence. |
| Structure sprite | `.shp`, `.png` | `sequences/structures.yaml` | same as above | A large base frame plus optional build, idle, and damaged frames. | `Make:` is the construction animation; `WithIdleOverlay` adds independent overlays. |
| Projectile / effect sprite | `.shp`, `.png` | `sequences/misc.yaml`, `weapons.yaml` `Image` / `Palette` | same as above | A small 16×16 to 48×48 burst, bullet, or explosion frame. | Usually short `Length` and no facings; referenced by `Projectile` or `CreateEffect` warhead. |
| Raw sprite sheet | `.shp`, `.png`, `.tmp` | `mod.yaml` → `SpriteFormats` / `Loaders` → `Sprite` | `ISpriteLoader` (`OpenRA.Game/Graphics/SpriteLoader.cs`), `SpriteCache`, `SheetBuilder`, `Sprite` (`OpenRA.Game/Graphics/Sprite.cs`) | A large GPU texture packed with many individual frames. | `SpriteCache` packs frames into `Sheet` objects to reduce draw calls. |

---

## Terrain / Tilesets

Tilesets define the visual and gameplay properties of every cell on a map. A tileset YAML file contains the tile size, terrain types, and a library of templates that the map editor and renderer use.

| Asset | File Format(s) | Definition YAML | Engine Loader / Class | Visual Preview | Notes |
| :---- | :---- | :---- | :---- | :---- | :---- |
| Tile template | `.shp`, `.tmp`, `.png` | `tilesets/*.yaml`, `mod.yaml` → `TileSets` | `ITerrainInfo` / `DefaultTerrainInfo` (`OpenRA.Mods.Common/Terrain/DefaultTerrain.cs`), `TerrainTemplateInfo` (`OpenRA.Mods.Common/Terrain/TerrainInfo.cs`), `TerrainRenderer` (`OpenRA.Mods.Common/Traits/World/TerrainRenderer.cs`) | A square tile grid showing a single terrain template (e.g., a 2×2 cliff or road piece). | `PickAny` lets the engine pick a random variation; `Riser` defines height transitions between cells. |
| Terrain type | `.yaml` (inside tileset) | `tilesets/*.yaml` | `TerrainTypeInfo` (`OpenRA.Game/Map/TerrainInfo.cs`), `ITerrainInfo` | A colored cell representing a movement/terrain class. | Defines speed, minimap color, and restricted player color rules. |
| Rendered terrain layer | `.bin` (inside map) | `map.yaml`, `tilesets/*.yaml` | `TerrainRenderer`, `Map` (`OpenRA.Game/Map/Map.cs`) | A top-down isometric battlefield of connected tiles. | Each map cell stores a template index + frame; the renderer draws only the visible tiles. |

---

## Palettes

Palettes are 256-color lookup tables used by 8-bit indexed sprites. The engine can load a palette from disk, derive one from another palette, or extract one from a sprite file.

| Asset | File Format(s) | Definition YAML | Engine Loader / Class | Visual Preview | Notes |
| :---- | :---- | :---- | :---- | :---- | :---- |
| Palette from file | `.pal` | `rules/palettes.yaml` | `PaletteFromFile` (`OpenRA.Mods.Common/Traits/Palettes/PaletteFromFile.cs`), `IPalette` (`OpenRA.Game/Graphics/Palette.cs`) | A horizontal strip of 256 indexed colors numbered 0–255. | 8-bit sprites reference a named palette at render time; a `.pal` can be 6-bit Westwood or 8-bit. |
| Derived palette | `.yaml` only | `rules/palettes.yaml` | `PaletteFromPaletteWithAlpha` (`OpenRA.Mods.Common/Traits/Palettes/PaletteFromPaletteWithAlpha.cs`), `PaletteFromPlayerPalette*` (common palettes), `IPalette` | Same color strip but with a translucent or player-tint overlay. | Used for remap colors, shadows, and faction tints. |
| Embedded palette | inside `.shp` | `rules/palettes.yaml` | `PaletteFromEmbeddedSpritePalette` (`OpenRA.Mods.Common/Traits/Palettes/PaletteFromEmbeddedSpritePalette.cs`) | A tiny palette extracted from a sprite file. | Some SHP files carry their own palette; OpenRA can expose it via a palette trait. |

---

## Cursors

Cursors are small animated sprites that follow the mouse pointer. OpenRA prefers hardware cursors but falls back to software rendering when necessary.

| Asset | File Format(s) | Definition YAML | Engine Loader / Class | Visual Preview | Notes |
| :---- | :---- | :---- | :---- | :---- | :---- |
| Mouse cursor | `.shp`, `.png` | `cursors.yaml`, `mod.yaml` → `Cursors` | `CursorManager` (`OpenRA.Game/Graphics/CursorManager.cs`), `IHardwareCursor` / `ISoftwareCursor` (`OpenRA.Game/Graphics/PlatformInterfaces.cs`) | A small pointer (e.g., 32×32) with an active hot spot. | Hardware cursors are preferred; software fallback is used when disabled. |
| Animated cursor | `.shp`, `.png` | `cursors.yaml` | `CursorManager` | A 4–8 frame animation loop (e.g., a loading spinner). | `Start` / `Length` selects frames from the source sprite; packed onto a cursor sheet. |

---

## Chrome / UI

Chrome is OpenRA's UI system. It combines skin images (chrome collections) with widget layout YAML and C# logic classes to build menus, HUDs, and in-game interfaces.

| Asset | File Format(s) | Definition YAML | Engine Loader / Class | Visual Preview | Notes |
| :---- | :---- | :---- | :---- | :---- | :---- |
| UI panel / button skin | `.png` (1×, 2×, 3×) | `chrome.yaml`, `mod.yaml` → `Chrome` | `ChromeProvider` (`OpenRA.Game/Graphics/ChromeProvider.cs`) | A 9-slice panel: corners, edges, and a stretchable center. | `PanelRegion` and `PanelSides` define the slices; `Collection` maps names to regions. |
| Widget layout | `.yaml` | `chrome/*.yaml`, `mod.yaml` → `ChromeLayout` | `WidgetLoader`, `Widget` (`OpenRA.Game/Widgets/Widget.cs`), `ChromeLogic` | A tree diagram of nested UI containers, labels, and buttons. | The `Logic` key names the C# class that drives the widget. |
| UI icon | `.png` | `chrome.yaml` | `ChromeProvider` | A small 24×24 icon inside a named collection region. | Referenced by chrome widgets via `Image` / `ImageCollection`. |

---

## Audio / Sounds

Sound effects are short positional or global samples triggered by weapons, traits, and UI events. The engine tries each registered `ISoundLoader` until one parses the file.

| Asset | File Format(s) | Definition YAML | Engine Loader / Class | Visual Preview | Notes |
| :---- | :---- | :---- | :---- | :---- | :---- |
| Sound effect | `.aud`, `.wav`, `.ogg`, `.mp3` | `weapons.yaml` `Report`, trait `Sound:` fields, `mod.yaml` → `SoundFormats` | `ISoundLoader` (`OpenRA.Game/Sound/Sound.cs`), `Sound` (Game.Sound) | A short waveform or a single "pop" in a sound-field. | Spatial attenuation; random pitch via `Pitch` modifiers; can be positional. |
| Ambient sound | `.wav`, `.ogg` | `AmbientSound` trait in map / rules | `Sound`, `AmbientSound` trait | A looping waveform that fills an area. | Optional `Interval` and `RequiredCondition` control when it plays. |

---

## Voices

Voices are phrases spoken by units when selected, ordered, or killed. They are grouped into sets and referenced by the `Voiced` trait.

| Asset | File Format(s) | Definition YAML | Engine Loader / Class | Visual Preview | Notes |
| :---- | :---- | :---- | :---- | :---- | :---- |
| Voice set | `.aud`, `.wav`, `.ogg` | `voices.yaml`, `mod.yaml` → `Voices` | `SoundInfo` (`OpenRA.Game/GameRules/Ruleset.cs`), `Sound` | A speaker icon with a unit silhouette and phrases like "Select", "Move", "Attack". | `Voiced` trait selects the set; the engine picks a phrase matching the action. |

---

## Notifications

Notifications are global speech events such as "Construction complete" or "Unit ready". They are not positional and are played per-player through the central sound system.

| Asset | File Format(s) | Definition YAML | Engine Loader / Class | Visual Preview | Notes |
| :---- | :---- | :---- | :---- | :---- | :---- |
| Game notification | `.aud`, `.wav`, `.ogg` | `notifications.yaml`, `mod.yaml` → `Notifications` | `SoundInfo` (`OpenRA.Game/GameRules/Ruleset.cs`), `Sound` | A warning triangle with a speech bubble (e.g., "Construction complete"). | Played via `Game.Sound.PlayNotification`; global per-player, not positional. |

---

## Music

Music tracks are background songs played by the `MusicPlaylist` trait. The mod manifest lists the available tracks and the ruleset loads them as `MusicInfo` objects.

| Asset | File Format(s) | Definition YAML | Engine Loader / Class | Visual Preview | Notes |
| :---- | :---- | :---- | :---- | :---- | :---- |
| Music track | `.ogg`, `.mp3`, `.wav` | `music.yaml`, `mod.yaml` → `Music` | `MusicInfo` (`OpenRA.Game/GameRules/Ruleset.cs`), `MusicPlaylist` (`OpenRA.Mods.Common/Traits/World/MusicPlaylist.cs`) | A musical note with a track title and progress bar. | `MusicPlaylist` selects tracks, honors `Hidden`, and pauses for in-game speech. |

---

## Maps

Maps are self-contained packages that include terrain, actor placement, rules overrides, and a preview image. They can be packaged as `.oramap` (a ZIP file) or as a directory.

| Asset | File Format(s) | Definition YAML | Engine Loader / Class | Visual Preview | Notes |
| :---- | :---- | :---- | :---- | :---- | :---- |
| Map package | `.oramap` (zip), directory | `map.yaml`, `map.bin`, `map.png` | `Map` (`OpenRA.Game/Map/Map.cs`), `MapPreview` (`OpenRA.Game/Map/MapPreview.cs`) | A minimap thumbnail with colored terrain and numbered spawn points. | `map.bin` is the binary tile layer; `map.yaml` holds rules, actors, and metadata. |
| Map preview image | `.png` | `map.png` | `MapPreview` | A 256×256 top-down overview of the map. | Auto-generated by the editor; used by the map browser. |

---

## Fonts

Fonts are TrueType files declared in `mod.yaml`. The engine rasterizes glyphs into a sprite sheet via `SpriteFont` so text can be drawn efficiently with the rest of the UI.

| Asset | File Format(s) | Definition YAML | Engine Loader / Class | Visual Preview | Notes |
| :---- | :---- | :---- | :---- | :---- | :---- |
| UI font | `.ttf` | `mod.yaml` → `Fonts` | `SpriteFont` (`OpenRA.Game/Graphics/SpriteFont.cs`), `IFont` (`OpenRA.Game/Graphics/PlatformInterfaces.cs`) | The text "ABC" rendered as a crisp bitmap glyph strip. | Rasterized into a sprite sheet at load time; multiple named sizes can use the same `.ttf`. |

---

## Translations

Translations use Project Fluent `.ftl` files. The engine loads a mod-level bundle and an optional map-level bundle, then resolves strings by key at runtime.

| Asset | File Format(s) | Definition YAML | Engine Loader / Class | Visual Preview | Notes |
| :---- | :---- | :---- | :---- | :---- | :---- |
| Fluent string | `.ftl` | `mod.yaml` → `Translations`, map `FluentMessageDefinitions` | `FluentProvider` (`OpenRA.Game/FluentProvider.cs`), `FluentBundle` | A label shown in two languages side by side. | Supports variables, pluralization, and map-level overrides. |

---

## Videos

Full-motion videos are loaded through the `IVideoLoader` interface. The Tiberian Dawn mod provides a Westwood VQA loader.

| Asset | File Format(s) | Definition YAML | Engine Loader / Class | Visual Preview | Notes |
| :---- | :---- | :---- | :---- | :---- | :---- |
| FMV / cutscene | `.vqa`, `.ogv` | `mod.yaml` → `Movies` | `IVideoLoader` (`OpenRA.Game/Graphics/VideoLoader.cs`), `VqaLoader` (`OpenRA.Mods.Cnc/VideoLoaders/VqaLoader.cs`), `IVideo` | A filmstrip frame with a play button and subtitle area. | The sound engine plays the audio track; optional subtitle support. |

---

## Voxels (TS/RA2)

Voxels are 3D models used by Tiberian Sun and Red Alert 2 style mods. They are stored as a `.vxl` volume plus an `.hva` animation/position file.

| Asset | File Format(s) | Definition YAML | Engine Loader / Class | Visual Preview | Notes |
| :---- | :---- | :---- | :---- | :---- | :---- |
| Voxel model | `.vxl` + `.hva` | `mod.yaml` → `ModelSequences` | `VoxelLoader` (`OpenRA.Mods.Cnc/Graphics/VoxelLoader.cs`), `Voxel` (`OpenRA.Mods.Cnc/Graphics/Voxel.cs`), `IModel` | A blocky 3D object (e.g., a turret) viewed from a rotating angle. | `.hva` holds the limb transforms; TS/RA2-style mods use these for units and projectiles. |

---

## MIX / Package archives

OpenRA mounts archives and directories through a layered virtual file system. MIX files are the classic Westwood archive format; ZIP files and loose folders are also supported.

| Asset | File Format(s) | Definition YAML | Engine Loader / Class | Visual Preview | Notes |
| :---- | :---- | :---- | :---- | :---- | :---- |
| MIX archive | `.mix` | `mod.yaml` → `PackageFormats` / `Packages` / `FileSystem` | `MixFile` (`OpenRA.Mods.Cnc/FileSystem/MixFile.cs`), `IPackage` (`OpenRA.Game/FileSystem/IPackage.cs`), `FileSystem` | A closed box labeled `.mix` containing many small asset icons. | Westwood archive format; mounted by the VFS so files are addressed by name. |
| ZIP / loose package | `.zip`, folder | `mod.yaml` → `Packages` | `ZipFile` (`OpenRA.Game/FileSystem/ZipFile.cs`), `IPackage` | A folder or zip icon at the bottom of a layered stack. | The VFS layers packages in mount order; later mounts override earlier ones. |

---

## Summary

This appendix catalogued OpenRA's asset types: sprites, terrain, palettes, cursors, chrome, audio, voices, notifications, music, maps, fonts, translations, videos, voxels, and MIX archives. Each entry showed the raw file format, the YAML definition, the engine loader or class, and any special rendering or playback notes. It is intended as a quick reference while reading the rest of the manual or while working in a mod's asset tree.

## What to read next

- [Part 4.1 — Renderer, Sheet, and Sprite](../chapters/Part_04_Chapter_01_Renderer.md) for sprite sheet and palette details.
- [Part 6.5 — Asset Loaders](../chapters/Part_06_Chapter_05_Asset_Loaders.md) for the loader chain architecture.
- [Part 6.3 — Virtual File System](../chapters/Part_06_Chapter_03_VFS.md) for package mounting and file lookup.
- [Appendix B — Common YAML Patterns](Appendix_B_Common_YAML_Patterns.md) for reusable MiniYaml snippets that wire many of these assets together.