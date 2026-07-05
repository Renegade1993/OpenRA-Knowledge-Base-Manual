# OpenRA Source-to-Manual Coverage Matrix

This matrix maps directories and files in the cloned OpenRA engine to the Parts and Chapters of the Knowledge Base Manual. It is used to ensure every subsystem is documented and to track progress.

## Part 1 — Core Engine Architecture

| Chapter | Source Directory / Files | Status |
| :---- | :---- | :---- |
| 1.1 ECS | `OpenRA.Game\Actor.cs`, `OpenRA.Game\Traits\ITraitInfo.cs`, `OpenRA.Game\Traits\TraitsInterfaces.cs`, `OpenRA.Game\Traits\TraitDictionary.cs`, `OpenRA.Game\Traits\TypeDictionary.cs`, `OpenRA.Game\Traits\ActorInitializer.cs`, `OpenRA.Game\ObjectCreator.cs`, `OpenRA.Game\FieldLoader.cs` | Complete |
| 1.2 Activities | `OpenRA.Game\Activities\Activity.cs`, `OpenRA.Game\Activities\ActivityUtils.cs`, `OpenRA.Game\Activities\ActionQueue.cs` | Complete |
| 1.3 World, Orders | `OpenRA.Game\World.cs`, `OpenRA.Game\GameRules\ActorInfo.cs`, `OpenRA.Game\Network\OrderManager.cs`, `OpenRA.Game\Orders\Order.cs`, `OpenRA.Game\Orders\UnitOrders.cs`, `OpenRA.Game\Sync.cs` | Complete |
| 1.4 Deterministic Math | `OpenRA.Game\Primitives\WPos.cs`, `WDist.cs`, `WAngle.cs`, `WVec.cs`, `CPos.cs`, `MPos.cs`, `OpenRA.Game\Map\MapGrid.cs`, `OpenRA.Game\MathUtils.cs`, `OpenRA.Game\Exts.cs` | Complete |

## Part 2 — Data and Configuration

| Chapter | Source Directory / Files | Status |
| :---- | :---- | :---- |
| 2.1 MiniYaml | `OpenRA.Game\MiniYaml.cs`, `OpenRA.Game\MiniYamlNode.cs`, `OpenRA.Game\MiniYamlExtensions.cs` | Complete |
| 2.2 Manifest, ModData, Ruleset | `OpenRA.Game\Manifest.cs`, `OpenRA.Game\ModData.cs`, `OpenRA.Game\GameRules\Ruleset.cs`, `OpenRA.Game\Map\Map.cs` (rules) | Complete |
| 2.3 FieldLoader, ObjectCreator | `OpenRA.Game\FieldLoader.cs`, `OpenRA.Game\ObjectCreator.cs` | Complete |
| 2.4 Rules, Weapons, Warheads, Projectiles | `OpenRA.Game\GameRules\ActorInfo.cs`, `OpenRA.Game\GameRules\WeaponInfo.cs`, `OpenRA.Mods.Common\Weapons\*`, `OpenRA.Mods.Common\Warheads\*`, `OpenRA.Mods.Common\Projectiles\*` | Complete |

## Part 3 — Mod SDK, Build, Deployment

| Chapter | Source Directory / Files | Status |
| :---- | :---- | :---- |
| 3.1 Mod SDK and Project Structure | `OpenRA.Game\Manifest.cs`, `OpenRA.Game\ModData.cs`, `OpenRA.Game\ObjectCreator.cs`, `OpenRA.Game\Game.Initialize` (mod assembly loading) | Complete |
| 3.2 SDK Bootstrap | `OpenRA-Mod-SDK\launch-game.sh`, `mod.config`, `fetch-engine.sh`, `make.cmd`, `make.ps1` | Complete |
| 3.3 Build and Packaging | `OpenRA-Mod-SDK\Makefile`, `OpenRA-Mod-SDK\packaging\`, `OpenRA\packaging\` | Complete |

## Part 4 — Rendering and UI

| Chapter | Source Directory / Files | Status |
| :---- | :---- | :---- |
| 4.1 Asset Pipeline | `OpenRA.Game\Graphics\SpriteLoader.cs`, `OpenRA.Game\Graphics\SheetBuilder.cs`, `OpenRA.Game\Graphics\Sprite.cs`, `OpenRA.Game\Graphics\SequenceProvider.cs`, `OpenRA.Mods.Common\Graphics\*` | Complete |
| 4.2 World Renderer | `OpenRA.Game\Graphics\WorldRenderer.cs`, `OpenRA.Game\Graphics\Viewport.cs`, `OpenRA.Game\Graphics\TerrainRenderer.cs`, `OpenRA\glsl\*` | Complete |
| 4.3 Chrome UI | `OpenRA.Game\Widgets\Widget.cs`, `OpenRA.Game\Widgets\WidgetLoader.cs`, `OpenRA.Mods.Common\Widgets\*`, `OpenRA.Mods.Common\Widgets\Logic\*` | Complete |
| 4.4 DPI / FBO | `OpenRA.Game\Graphics\WorldRenderer.cs`, `OpenRA.Game\Widgets\*`, `OpenRA.Platforms.Default\*` | Complete |

## Part 5 — Audio

| Chapter | Source Directory / Files | Status |
| :---- | :---- | :---- |
| 5.1 Audio Architecture | `OpenRA.Game\Sound\SoundDevice.cs`, `OpenRA.Game\Sound\Sound.cs`, `OpenRA.Platforms.Default\OpenAlSoundEngine.cs`, `OpenRA.Platforms.Default\DummySoundEngine.cs` | Complete |
| 5.2 Spatial Attenuation | `OpenRA.Platforms.Default\OpenAlSoundEngine.cs` | Complete |
| 5.3 Music | `OpenRA.Mods.Common\Traits\World\MusicPlaylist.cs`, `OpenRA.Game\GameRules\MusicInfo.cs`, `OpenRA.Game\Sound\Sound.cs` | Complete |
| 5.4 Sound Triggers | `OpenRA.Mods.Common\Traits\Sound\AttackSounds.cs`, `DeathSounds.cs`, `AmbientSound.cs`, `Voiced.cs`, `OpenRA.Game\GameRules\SoundInfo.cs` | Complete |

## Part 6 — Scripting and VFS

| Chapter | Source Directory / Files | Status |
| :---- | :---- | :---- |
| 6.1 Lua / Eluant | `OpenRA.Mods.Common\Scripting\*`, `OpenRA.Game\Scripting\ScriptContext.cs`, `OpenRA.Game\Scripting\LuaScript.cs` | Complete |
| 6.2 ScriptContext | `OpenRA.Game\Scripting\ScriptContext.cs` | Complete |
| 6.3 VFS | `OpenRA.Game\FileSystem\*`, `OpenRA.Game\FileSystem\IPackage.cs`, `Folder.cs`, `MixFile.cs`, `InstallShieldPackage.cs`, `Pak.cs`, `BigFile.cs`, `ZipFile.cs` | Complete |
| 6.4 Cryptography | `OpenRA.Mods.Common\FileFormats\Blowfish.cs`, `OpenRA.Game\FileSystem\MixFile.cs`, `OpenRA.Mods.Common\FileSystem\BlowfishKeyProvider.cs` | Complete |
| 6.5 Asset Loaders | `OpenRA.Game\FileFormats\AudLoader.cs`, `WavLoader.cs`, `ImaAdpcmLoader.cs`, `OpenRA.Mods.Common\FileFormats\*` | Complete |

## Part 7 — Random / Procedural Map Generator (Deep Dive)

| Chapter | Source Directory / Files | Status |
| :---- | :---- | :---- |
| 7.1 Pipeline Overview | `OpenRA.Mods.Common\Traits\World\MapGeneratorLogic.cs`, `MapGeneratorToolLogic.cs`, `OpenRA.Mods.Common\MapGenerator\IEditorMapGeneratorInfo.cs` | Complete |
| 7.2 Data Structures | `OpenRA.Game\Map\CellLayer.cs`, `CellLayerBase.cs`, `OpenRA.Mods.Common\MapGenerator\Matrix.cs`, `OpenRA.Game\Map\MapGrid.cs` | Complete |
| 7.3 Algorithms | `OpenRA.Mods.Common\MapGenerator\NoiseUtils.cs`, `MatrixUtils.cs`, `Symmetry.cs` | Complete |
| 7.4 Terraformer | `OpenRA.Mods.Common\MapGenerator\Terraformer.cs` | Complete |
| 7.5 MultiBrush | `OpenRA.Mods.Common\MapGenerator\MultiBrush.cs` | Complete |
| 7.6 Mod Generators | `OpenRA.Mods.D2k\Traits\World\D2kMapGenerator.cs`, `OpenRA.Mods.Cnc\Traits\World\TSMapGenerator.cs`, `OpenRA.Mods.Common\Traits\World\ClassicMapGenerator.cs` | Complete |
| 7.7 Resources / Actors | `OpenRA.Mods.Common\MapGenerator\Terraformer.cs` (PlanResources), `OpenRA.Mods.Common\MapGenerator\Symmetry.cs` | Complete |
| 7.8 Extension Points | `OpenRA.Mods.Common\MapGenerator\*` | Complete |
| 7.9 File-by-File Index | `OpenRA.Mods.Common\MapGenerator\*`, `OpenRA.Mods.D2k\*`, `OpenRA.Mods.Cnc\*` | Complete |

## Part 8 — AI and Bot Framework

| Chapter | Source Directory / Files | Status |
| :---- | :---- | :---- |
| 8.1 IBot / ModularBot | `OpenRA.Game\Traits\TraitsInterfaces.cs`, `OpenRA.Mods.Common\Traits\Player\ModularBot.cs`, `DummyBot.cs` | Complete |
| 8.2 Bot Modules | `OpenRA.Mods.Common\Traits\BotModules\*BotModule.cs` | Complete |
| 8.3 Squads / Fuzzy | `OpenRA.Mods.Common\Traits\BotModules\Squads\*.cs`, `AttackOrFleeFuzzy.cs` | Complete |
| 8.4 Order Flow | `OpenRA.Game\World.cs`, `OpenRA.Game\Network\OrderManager.cs` | Complete |

## Part 9 — Network and Lockstep

| Chapter | Source Directory / Files | Status |
| :---- | :---- | :---- |
| 9.1 OrderManager | `OpenRA.Game\Network\OrderManager.cs` | Complete |
| 9.2 Server / Connection | `OpenRA.Game\Server\Server.cs`, `OpenRA.Game\Network\Connection.cs`, `OpenRA.Server\Program.cs` | Complete |
| 9.3 Sync Hashing | `OpenRA.Game\Network\SyncReport.cs`, `OpenRA.Game\Sync.cs` | Complete |

## Part 10 — Official Mods and Online References

| Chapter | Source Directory / Files | Status |
| :---- | :---- | :---- |
| 10.1 Official Mods | `OpenRA\mods\*` | Complete |
| 10.2 Online Docs | `docs.openra.net`, `openra.net/book` | Complete |
| 10.3 Community | `OpenRA-Resources`, `OpenRAWeb`, tutorials | Complete |
