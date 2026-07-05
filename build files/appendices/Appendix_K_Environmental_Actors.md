# Appendix K — Environmental Actor Reference

This appendix catalogs the **environmental actors** in the four official OpenRA mods: *Red Alert (RA)*, *Tiberian Dawn (C&C)*, *Dune 2000 (D2K)*, and *Tiberian Sun (TS)*. Environmental actors are map-placed objects that are not produced by a player's factory or construction yard in the normal tech tree—things like trees, rocks, civilian buildings, bridges, walls, gates, crates, resource spawns, and decorative props. Some of them (sandbags, concrete walls, gates) can also be built by players once the right prerequisites are met, but they still behave as world objects rather than as units.

They differ from buildable combat actors in a few key ways:

* Most inherit from templates such as `^Tree`, `^Rock`, `^CivBuilding`, `^Bridge`, `^Wall`, or `^Crate` rather than from `^Building` or `^Vehicle`.
* They are usually owned by `Neutral` (or `Creeps` for hostile wildlife) and placed in the map editor.
* They typically use `Building` for footprint, `Interactable` for selection bounds, `Tooltip` for display names, and `MapEditorData` for editor categorization.
* Many are invulnerable or have very high health, and some have special death behavior such as `SpawnActorOnDeath`, `FireWarheadsOnDeath`, `SeedsResource`, or `CashTrickler`.

The tables use the YAML data as it appears in the rules files. "Name/Tooltip" shows the in-game display name resolved from the mod's Fluent translation files. "Size" combines the `Dimensions` and `Footprint` values from the `Building` trait. "Key Traits" highlights the most important behavior traits. A "—" means the field is not explicitly set on that actor or its inherited template.

> **Generated, not hand-written.** This appendix is produced by `build files/generate_environmental_actor_reference.py`, which parses each mod's `rules/*.yaml` (resolving `Inherits:` chains) and `fluent/rules.ftl` (for display names). The preview column shows labelled placeholders by default; run `build files/extract_environmental_images.py` after installing the game content to render real sprites with the OpenRA Utility's `--export-sequence-frame` command.

> **A note on art.** OpenRA's own assets are openly licensed; the classic Westwood/EA unit art is distributed as freeware and remains its owners' property. Showing previews in a free, non-commercial, educational reference is a fair-use use, not an open-license grant. Attribute the art to its owners and include a "not endorsed by or affiliated with EA" notice when publishing.

> Cross-references: [Part 1.1 — ECS](../chapters/Part_01_Chapter_01_ECS.md), [Part 2.4 — Rulesets, Actors, and Weapons](../chapters/Part_02_Chapter_04_Rules_Weapons.md), [Part 7.7 — RMG Resources and Actors](../chapters/Part_07_Chapter_07_Resources_Actors.md), [Part 10.1 — Official Mods](../chapters/Part_10_Chapter_01_Official_Mods.md), [Appendix J — Terrain Tile Reference](Appendix_J_Terrain_Tiles.md)

---

## Red Alert
*135 environmental actors.*

### Vegetation (29)
| Preview | Actor | Name/Tooltip | Size | Key Traits | Notes |
| :---: | :--- | :--- | :--- | :--- | :--- |
| ![Tree preview](images/environmental/ra/t01.png) | `T01` | Tree | 2,2 `__ x_` | SpawnActorOnDeath | Exclude DESERT, INTERIOR |
| ![Tree preview](images/environmental/ra/t02.png) | `T02` | Tree | 2,2 `__ x_` | SpawnActorOnDeath | Exclude DESERT, INTERIOR |
| ![Tree preview](images/environmental/ra/t03.png) | `T03` | Tree | 2,2 `__ x_` | SpawnActorOnDeath | Exclude DESERT, INTERIOR |
| ![Tree preview](images/environmental/ra/t04.png) | `T04` | Tree | 2,2 `__ x_` | SpawnActorOnDeath | Exclude TEMPERAT, SNOW, INTERIOR |
| ![Tree preview](images/environmental/ra/t05.png) | `T05` | Tree | 2,2 `__ x_` | SpawnActorOnDeath | Exclude DESERT, INTERIOR |
| ![Tree preview](images/environmental/ra/t06.png) | `T06` | Tree | 2,2 `__ x_` | SpawnActorOnDeath | Exclude DESERT, INTERIOR |
| ![Tree preview](images/environmental/ra/t07.png) | `T07` | Tree | 2,2 `__ x_` | SpawnActorOnDeath | Exclude DESERT, INTERIOR |
| ![Tree preview](images/environmental/ra/t08.png) | `T08` | Tree | 2,1 `x_` | SpawnActorOnDeath | Exclude INTERIOR |
| ![Tree preview](images/environmental/ra/t09.png) | `T09` | Tree | 1,1 `x` | SpawnActorOnDeath | Exclude TEMPERAT, SNOW, INTERIOR |
| ![Tree preview](images/environmental/ra/t10.png) | `T10` | Tree | 2,2 `__ xx` | SpawnActorOnDeath | Exclude DESERT, INTERIOR |
| ![Tree preview](images/environmental/ra/t11.png) | `T11` | Tree | 2,2 `__ xx` | SpawnActorOnDeath | Exclude DESERT, INTERIOR |
| ![Tree preview](images/environmental/ra/t12.png) | `T12` | Tree | 2,2 `__ x_` | SpawnActorOnDeath | Exclude DESERT, INTERIOR |
| ![Tree preview](images/environmental/ra/t13.png) | `T13` | Tree | 2,2 `__ x_` | SpawnActorOnDeath | Exclude DESERT, INTERIOR |
| ![Tree preview](images/environmental/ra/t14.png) | `T14` | Tree | 3,2 `___ xx_` | SpawnActorOnDeath | Exclude DESERT, INTERIOR |
| ![Tree preview](images/environmental/ra/t15.png) | `T15` | Tree | 3,2 `___ xx_` | SpawnActorOnDeath | Exclude DESERT, INTERIOR |
| ![Tree preview](images/environmental/ra/t16.png) | `T16` | Tree | 2,2 `__ x_` | SpawnActorOnDeath | Exclude DESERT, INTERIOR |
| ![Tree preview](images/environmental/ra/t17.png) | `T17` | Tree | 2,2 `__ x_` | SpawnActorOnDeath | Exclude DESERT, INTERIOR |
| ![Tree preview](images/environmental/ra/tc01.png) | `TC01` | Tree | 3,2 `___ xx_` | SpawnActorOnDeath | Exclude INTERIOR |
| ![Tree preview](images/environmental/ra/tc02.png) | `TC02` | Tree | 3,2 `_x_ xx_` | SpawnActorOnDeath | Exclude DESERT, INTERIOR |
| ![Tree preview](images/environmental/ra/tc03.png) | `TC03` | Tree | 3,2 `xx_ xx_` | SpawnActorOnDeath | Exclude DESERT, INTERIOR |
| ![Tree preview](images/environmental/ra/tc04.png) | `TC04` | Tree | 4,3 `____ xxx_ x___` | SpawnActorOnDeath | Exclude DESERT, INTERIOR |
| ![Tree preview](images/environmental/ra/tc05.png) | `TC05` | Tree | 4,3 `__x_ xxx_ _xx_` | SpawnActorOnDeath | Exclude DESERT, INTERIOR |
| ![Ice Floe preview](images/environmental/ra/ice01.png) | `ICE01` | Ice Floe | 2,2 `xx xx` | — | Require SNOW; Exclude INTERIOR |
| ![Ice Floe preview](images/environmental/ra/ice02.png) | `ICE02` | Ice Floe | 1,2 `x x` | — | Require SNOW; Exclude INTERIOR |
| ![Ice Floe preview](images/environmental/ra/ice03.png) | `ICE03` | Ice Floe | 2,1 `xx` | — | Require SNOW; Exclude INTERIOR |
| ![Ice Floe preview](images/environmental/ra/ice04.png) | `ICE04` | Ice Floe | 1,1 `x` | — | Require SNOW; Exclude INTERIOR |
| ![Ice Floe preview](images/environmental/ra/ice05.png) | `ICE05` | Ice Floe | 1,1 `x` | — | Require SNOW; Exclude INTERIOR |
| ![Utility Pole preview](images/environmental/ra/utilpol1.png) | `UTILPOL1` | Utility Pole | 1,1 `x` | — | Exclude INTERIOR |
| ![Utility Pole preview](images/environmental/ra/utilpol2.png) | `UTILPOL2` | Utility Pole | 1,1 `x` | — | Exclude INTERIOR |

### Rocks and Cliffs (9)
| Preview | Actor | Name/Tooltip | Size | Key Traits | Notes |
| :---: | :--- | :--- | :--- | :--- | :--- |
| ![Rock preview](images/environmental/ra/rock1.png) | `ROCK1` | Rock | 3,2 `___ xx_` | — | Require DESERT |
| ![Rock preview](images/environmental/ra/rock2.png) | `ROCK2` | Rock | 3,1 `xx_` | — | Require DESERT |
| ![Rock preview](images/environmental/ra/rock3.png) | `ROCK3` | Rock | 3,2 `___ xx_` | — | Require DESERT |
| ![Rock preview](images/environmental/ra/rock4.png) | `ROCK4` | Rock | 2,1 `x_` | — | Require DESERT |
| ![Rock preview](images/environmental/ra/rock5.png) | `ROCK5` | Rock | 2,1 `x_` | — | Require DESERT |
| ![Rock preview](images/environmental/ra/rock6.png) | `ROCK6` | Rock | 3,2 `___ xxx` | — | Require DESERT |
| ![Rock preview](images/environmental/ra/rock7.png) | `ROCK7` | Rock | 5,1 `xxxx_` | — | Require DESERT |
| ![Tank Trap preview](images/environmental/ra/tanktrap1.png) | `TANKTRAP1` | Tank Trap | 1,1 `x` | — | Require TEMPERAT, SNOW, DESERT, INTERIOR |
| ![Tank Trap preview](images/environmental/ra/tanktrap2.png) | `TANKTRAP2` | Tank Trap | 1,1 `x` | — | Require TEMPERAT, SNOW, DESERT, INTERIOR |

### Buildings and Structures (50)
| Preview | Actor | Name/Tooltip | Size | Key Traits | Notes |
| :---: | :--- | :--- | :--- | :--- | :--- |
| ![Forward Command preview](images/environmental/ra/fcom.png) | `FCOM` | Forward Command | 2,3 `xx xx ==` | FireWarheadsOnDeath, Capturable, InstantlyRepairable, RevealsShroud, BaseProvider, GivesBuildableArea, WithBuildingBib, Demolishable | — |
| ![Communications Center preview](images/environmental/ra/miss.png) | `MISS` | Communications Center | 3,3 `xxx xxx ===` | FireWarheadsOnDeath, Capturable, InstantlyRepairable, RevealsShroud, WithBuildingBib, Demolishable | — |
| ![Biological Lab preview](images/environmental/ra/bio.png) | `BIO` | Biological Lab | 2,2 `xx xx` | FireWarheadsOnDeath, Capturable, InstantlyRepairable, RevealsShroud, Demolishable | — |
| ![Hospital preview](images/environmental/ra/hosp.png) | `HOSP` | Hospital | 2,2 `xx xx` | FireWarheadsOnDeath, Capturable, InstantlyRepairable, RevealsShroud, WithBuildingBib, Demolishable | — |
| ![Church preview](images/environmental/ra/v01.png) | `V01` | Church | 2,2 `xx xx` | FireWarheadsOnDeath, RevealsShroud, Demolishable | Exclude DESERT, INTERIOR |
| ![Civilian Building preview](images/environmental/ra/v02.png) | `V02` | Civilian Building | 2,2 `xx xx` | FireWarheadsOnDeath, Demolishable | Exclude DESERT, INTERIOR |
| ![Civilian Building preview](images/environmental/ra/v03.png) | `V03` | Civilian Building | 2,2 `xx xx` | FireWarheadsOnDeath, Demolishable | Exclude DESERT, INTERIOR |
| ![Civilian Building preview](images/environmental/ra/v04.png) | `V04` | Civilian Building | 2,2 `xx xx` | FireWarheadsOnDeath, Demolishable | Exclude DESERT, INTERIOR |
| ![Civilian Building preview](images/environmental/ra/v05.png) | `V05` | Civilian Building | 2,1 `xx` | FireWarheadsOnDeath, Demolishable | Exclude DESERT, INTERIOR |
| ![Civilian Building preview](images/environmental/ra/v06.png) | `V06` | Civilian Building | 2,1 `xx` | FireWarheadsOnDeath, Demolishable | Exclude DESERT, INTERIOR |
| ![Civilian Building preview](images/environmental/ra/v07.png) | `V07` | Civilian Building | 2,1 `xx` | FireWarheadsOnDeath, Demolishable | Exclude DESERT, INTERIOR |
| ![Civilian Building preview](images/environmental/ra/v08.png) | `V08` | Civilian Building | 1,1 `x` | FireWarheadsOnDeath, Demolishable | Exclude DESERT, INTERIOR |
| ![Civilian Building preview](images/environmental/ra/v09.png) | `V09` | Civilian Building | 1,1 `x` | FireWarheadsOnDeath, Demolishable | Exclude DESERT, INTERIOR |
| ![Civilian Building preview](images/environmental/ra/v10.png) | `V10` | Civilian Building | 1,1 `x` | FireWarheadsOnDeath, Demolishable | Exclude DESERT, INTERIOR |
| ![Civilian Building preview](images/environmental/ra/v11.png) | `V11` | Civilian Building | 1,1 `x` | FireWarheadsOnDeath, Demolishable | Exclude DESERT, INTERIOR |
| ![— preview](images/environmental/ra/v12.png) | `V12` | — | 1,1 `x` | — | Exclude DESERT, INTERIOR; Non-interactive field |
| ![— preview](images/environmental/ra/v13.png) | `V13` | — | 1,1 `x` | — | Exclude DESERT, INTERIOR; Non-interactive field |
| ![Field preview](images/environmental/ra/v14.png) | `V14` | Field | 1,1 `x` | — | Exclude DESERT, INTERIOR; Non-interactive field |
| ![Field preview](images/environmental/ra/v15.png) | `V15` | Field | 1,1 `x` | — | Exclude DESERT, INTERIOR; Non-interactive field |
| ![Field preview](images/environmental/ra/v16.png) | `V16` | Field | 1,1 `x` | — | Exclude DESERT, INTERIOR; Non-interactive field |
| ![Field preview](images/environmental/ra/v17.png) | `V17` | Field | 1,1 `x` | — | Exclude DESERT, INTERIOR; Non-interactive field |
| ![Field preview](images/environmental/ra/v18.png) | `V18` | Field | 1,1 `x` | — | Exclude DESERT, INTERIOR; Non-interactive field |
| ![Oil Pump preview](images/environmental/ra/v19.png) | `V19` | Oil Pump | 1,1 `x` | SpawnActorOnDeath, FireWarheadsOnDeath, Demolishable | Exclude INTERIOR |
| ![Explosive Barrel preview](images/environmental/ra/barl.png) | `BARL` | Explosive Barrel | 1,1 `x` | FireWarheadsOnDeath | — |
| ![Explosive Barrel preview](images/environmental/ra/brl3.png) | `BRL3` | Explosive Barrel | 1,1 `x` | FireWarheadsOnDeath | — |
| ![Oil Derrick preview](images/environmental/ra/oilb.png) | `OILB` | Oil Derrick | 2,2 `xx xx` | FireWarheadsOnDeath, CashTrickler, Capturable, InstantlyRepairable, RevealsShroud, Demolishable | — |
| ![Civilian Building preview](images/environmental/ra/v20.png) | `V20` | Civilian Building | 2,2 `xx xx` | FireWarheadsOnDeath, Demolishable | Require DESERT; Exclude INTERIOR; Desert building |
| ![Civilian Building preview](images/environmental/ra/v21.png) | `V21` | Civilian Building | 2,2 `xx xx` | FireWarheadsOnDeath, Demolishable | Require DESERT; Exclude INTERIOR; Desert building |
| ![Civilian Building preview](images/environmental/ra/v22.png) | `V22` | Civilian Building | 2,1 `xx` | FireWarheadsOnDeath, Demolishable | Require DESERT; Exclude INTERIOR; Desert building |
| ![Civilian Building preview](images/environmental/ra/v23.png) | `V23` | Civilian Building | 1,1 `x` | FireWarheadsOnDeath, Demolishable | Require DESERT; Exclude INTERIOR; Desert building |
| ![Civilian Building preview](images/environmental/ra/v24.png) | `V24` | Civilian Building | 2,2 `xx xx` | FireWarheadsOnDeath, Demolishable | Require DESERT; Exclude INTERIOR; Desert building |
| ![Church preview](images/environmental/ra/v25.png) | `V25` | Church | 2,2 `xx xx` | FireWarheadsOnDeath, RevealsShroud, Demolishable | Require DESERT; Exclude INTERIOR; Desert building |
| ![Civilian Building preview](images/environmental/ra/v26.png) | `V26` | Civilian Building | 2,1 `xx` | FireWarheadsOnDeath, Demolishable | Require DESERT; Exclude INTERIOR; Desert building |
| ![Civilian Building preview](images/environmental/ra/v27.png) | `V27` | Civilian Building | 1,1 `x` | FireWarheadsOnDeath, Demolishable | Require DESERT; Exclude INTERIOR; Desert building |
| ![Civilian Building preview](images/environmental/ra/v28.png) | `V28` | Civilian Building | 1,1 `x` | FireWarheadsOnDeath, Demolishable | Require DESERT; Exclude INTERIOR; Desert building |
| ![Civilian Building preview](images/environmental/ra/v29.png) | `V29` | Civilian Building | 1,1 `x` | FireWarheadsOnDeath, Demolishable | Require DESERT; Exclude INTERIOR; Desert building |
| ![Civilian Building preview](images/environmental/ra/v30.png) | `V30` | Civilian Building | 2,1 `xx` | FireWarheadsOnDeath, Demolishable | Require DESERT; Exclude INTERIOR; Desert building |
| ![Civilian Building preview](images/environmental/ra/v31.png) | `V31` | Civilian Building | 2,1 `xx` | FireWarheadsOnDeath, Demolishable | Require DESERT; Exclude INTERIOR; Desert building |
| ![Civilian Building preview](images/environmental/ra/v32.png) | `V32` | Civilian Building | 2,1 `xx` | FireWarheadsOnDeath, Demolishable | Require DESERT; Exclude INTERIOR; Desert building |
| ![Civilian Building preview](images/environmental/ra/v33.png) | `V33` | Civilian Building | 2,1 `xx` | FireWarheadsOnDeath, Demolishable | Require DESERT; Exclude INTERIOR; Desert building |
| ![Civilian Building preview](images/environmental/ra/v34.png) | `V34` | Civilian Building | 1,1 `x` | FireWarheadsOnDeath, Demolishable | Require DESERT; Exclude INTERIOR; Desert building |
| ![Civilian Building preview](images/environmental/ra/v35.png) | `V35` | Civilian Building | 1,1 `x` | FireWarheadsOnDeath, Demolishable | Require DESERT; Exclude INTERIOR; Desert building |
| ![Civilian Building preview](images/environmental/ra/v36.png) | `V36` | Civilian Building | 1,1 `x` | FireWarheadsOnDeath, Demolishable | Require DESERT; Exclude INTERIOR; Desert building |
| ![Civilian Building preview](images/environmental/ra/v37.png) | `V37` | Civilian Building | 5,2 `__xx_ ___xx` | FireWarheadsOnDeath, Demolishable | Require DESERT; Exclude INTERIOR; Desert building |
| ![Field preview](images/environmental/ra/rice.png) | `RICE` | Field | 1,1 `x` | — | Require TEMPERAT; Exclude INTERIOR; Non-interactive field |
| ![Civilian Building preview](images/environmental/ra/rushouse.png) | `RUSHOUSE` | Civilian Building | 1,2 `x x` | FireWarheadsOnDeath, Demolishable | Require TEMPERAT; Exclude INTERIOR |
| ![Civilian Building preview](images/environmental/ra/asianhut.png) | `ASIANHUT` | Civilian Building | 1,1 `x` | FireWarheadsOnDeath, Demolishable | Require TEMPERAT; Exclude INTERIOR |
| ![Civilian Building preview](images/environmental/ra/snowhut.png) | `SNOWHUT` | Civilian Building | 1,2 `x x` | FireWarheadsOnDeath, Demolishable | Require SNOW; Exclude INTERIOR |
| ![Lighthouse preview](images/environmental/ra/lhus.png) | `LHUS` | Lighthouse | 1,1 `x` | FireWarheadsOnDeath, Demolishable | Require TEMPERAT; Exclude INTERIOR |
| ![Windmill preview](images/environmental/ra/windmill.png) | `WINDMILL` | Windmill | 1,1 `x` | FireWarheadsOnDeath, Demolishable | Require TEMPERAT; Exclude INTERIOR |

### Walls and Fences (6)
| Preview | Actor | Name/Tooltip | Size | Key Traits | Notes |
| :---: | :--- | :--- | :--- | :--- | :--- |
| ![Sandbag Wall preview](images/environmental/ra/sbag.png) | `SBAG` | Sandbag Wall | 1,1 `x` | Crushable | — |
| ![Wire Fence preview](images/environmental/ra/fenc.png) | `FENC` | Wire Fence | 1,1 `x` | Crushable | — |
| ![Concrete Wall preview](images/environmental/ra/brik.png) | `BRIK` | Concrete Wall | 1,1 `x` | Crushable | — |
| ![Chain-Link Barrier preview](images/environmental/ra/cycl.png) | `CYCL` | Chain-Link Barrier | 1,1 `x` | Crushable | — |
| ![Barbed-Wire Fence preview](images/environmental/ra/barb.png) | `BARB` | Barbed-Wire Fence | 1,1 `x` | Crushable | — |
| ![Wooden Fence preview](images/environmental/ra/wood.png) | `WOOD` | Wooden Fence | 1,1 `x` | Crushable | — |

### Bridges (12)
| Preview | Actor | Name/Tooltip | Size | Key Traits | Notes |
| :---: | :--- | :--- | :--- | :--- | :--- |
| ![Bridge preview](images/environmental/ra/br1.png) | `BR1` | Bridge | 4,2 `____ ____` | — | — |
| ![Bridge preview](images/environmental/ra/br2.png) | `BR2` | Bridge | 4,2 `____ ____` | — | — |
| ![Bridge preview](images/environmental/ra/br3.png) | `BR3` | Bridge | 4,2 `____ ____` | — | — |
| ![Bridge preview](images/environmental/ra/bridge1.png) | `BRIDGE1` | Bridge | 5,3 `_____ _____ _____` | — | — |
| ![Bridge preview](images/environmental/ra/bridge2.png) | `BRIDGE2` | Bridge | 5,2 `_____ _____` | — | — |
| ![Bridge preview](images/environmental/ra/bridge3.png) | `BRIDGE3` | Bridge | 4,2 `____ ____` | — | — |
| ![Bridge preview](images/environmental/ra/bridge4.png) | `BRIDGE4` | Bridge | 4,2 `____ ____` | — | — |
| ![Bridge preview](images/environmental/ra/sbridge1.png) | `SBRIDGE1` | Bridge | 3,2 `___ ___` | — | — |
| ![Bridge preview](images/environmental/ra/sbridge2.png) | `SBRIDGE2` | Bridge | 2,3 `__ __ __` | — | — |
| ![Bridge preview](images/environmental/ra/sbridge3.png) | `SBRIDGE3` | Bridge | 4,2 `____ ____` | — | — |
| ![Bridge preview](images/environmental/ra/sbridge4.png) | `SBRIDGE4` | Bridge | 4,2 `____ ____` | — | — |
| ![— preview](images/environmental/ra/bridgehut.png) | `BRIDGEHUT` | — | 2,2 `__ __` | — | — |

### Crates and Pickups (3)
| Preview | Actor | Name/Tooltip | Size | Key Traits | Notes |
| :---: | :--- | :--- | :--- | :--- | :--- |
| ![Ammo Box preview](images/environmental/ra/ammobox1.png) | `AMMOBOX1` | Ammo Box | 1,1 `x` | FireWarheadsOnDeath, Demolishable | — |
| ![Ammo Box preview](images/environmental/ra/ammobox2.png) | `AMMOBOX2` | Ammo Box | 1,1 `x` | FireWarheadsOnDeath, Demolishable | — |
| ![Ammo Box preview](images/environmental/ra/ammobox3.png) | `AMMOBOX3` | Ammo Box | 1,1 `x` | FireWarheadsOnDeath, Demolishable | — |

### Civilians (17)
| Preview | Actor | Name/Tooltip | Size | Key Traits | Notes |
| :---: | :--- | :--- | :--- | :--- | :--- |
| ![Civilian preview](images/environmental/ra/c1.png) | `C1` | Civilian | — | RevealsShroud, Crushable | — |
| ![Civilian preview](images/environmental/ra/c2.png) | `C2` | Civilian | — | RevealsShroud, Crushable | — |
| ![Civilian preview](images/environmental/ra/c3.png) | `C3` | Civilian | — | RevealsShroud, Crushable | — |
| ![Civilian preview](images/environmental/ra/c4.png) | `C4` | Civilian | — | RevealsShroud, Crushable | — |
| ![Civilian preview](images/environmental/ra/c5.png) | `C5` | Civilian | — | RevealsShroud, Crushable | — |
| ![Civilian preview](images/environmental/ra/c6.png) | `C6` | Civilian | — | RevealsShroud, Crushable | — |
| ![Civilian preview](images/environmental/ra/c7.png) | `C7` | Civilian | — | RevealsShroud, Crushable | — |
| ![Civilian preview](images/environmental/ra/c8.png) | `C8` | Civilian | — | RevealsShroud, Crushable | — |
| ![Civilian preview](images/environmental/ra/c9.png) | `C9` | Civilian | — | RevealsShroud, Crushable | — |
| ![Scientist preview](images/environmental/ra/c10.png) | `C10` | Scientist | — | RevealsShroud, Crushable | — |
| ![Civilian preview](images/environmental/ra/c11.png) | `C11` | Civilian | — | RevealsShroud, Crushable | — |
| ![Technician preview](images/environmental/ra/tecn.png) | `TECN` | Technician | — | RevealsShroud, Crushable | — |
| ![Technician preview](images/environmental/ra/tecn2.png) | `TECN2` | Technician | — | RevealsShroud, Crushable | — |
| ![Prof. Einstein preview](images/environmental/ra/einstein.png) | `EINSTEIN` | Prof. Einstein | — | RevealsShroud, Crushable | — |
| ![Agent Delphi preview](images/environmental/ra/delphi.png) | `DELPHI` | Agent Delphi | — | RevealsShroud, Crushable | — |
| ![Scientist preview](images/environmental/ra/chan.png) | `CHAN` | Scientist | — | RevealsShroud, Crushable | — |
| ![General preview](images/environmental/ra/gnrl.png) | `GNRL` | General | — | RevealsShroud, Crushable | — |

### Decorative Props (9)
| Preview | Actor | Name/Tooltip | Size | Key Traits | Notes |
| :---: | :--- | :--- | :--- | :--- | :--- |
| ![Boxes preview](images/environmental/ra/boxes01.png) | `BOXES01` | Boxes | 1,1 `x` | — | Exclude INTERIOR |
| ![Boxes preview](images/environmental/ra/boxes02.png) | `BOXES02` | Boxes | 1,1 `x` | — | Exclude INTERIOR |
| ![Boxes preview](images/environmental/ra/boxes03.png) | `BOXES03` | Boxes | 1,1 `x` | — | Exclude INTERIOR |
| ![Boxes preview](images/environmental/ra/boxes04.png) | `BOXES04` | Boxes | 1,1 `x` | — | Exclude INTERIOR |
| ![Boxes preview](images/environmental/ra/boxes05.png) | `BOXES05` | Boxes | 1,1 `x` | — | Exclude INTERIOR |
| ![Boxes preview](images/environmental/ra/boxes06.png) | `BOXES06` | Boxes | 1,1 `x` | — | Exclude INTERIOR |
| ![Boxes preview](images/environmental/ra/boxes07.png) | `BOXES07` | Boxes | 1,1 `x` | — | Exclude INTERIOR |
| ![Boxes preview](images/environmental/ra/boxes08.png) | `BOXES08` | Boxes | 1,1 `x` | — | Exclude INTERIOR |
| ![Boxes preview](images/environmental/ra/boxes09.png) | `BOXES09` | Boxes | 1,1 `x` | — | Exclude INTERIOR |

## Tiberian Dawn
*103 environmental actors.*

### Vegetation (23)
| Preview | Actor | Name/Tooltip | Size | Key Traits | Notes |
| :---: | :--- | :--- | :--- | :--- | :--- |
| ![Tree preview](images/environmental/cnc/t01.png) | `T01` | Tree | 2,2 `__ x_` | SpawnActorOnDeath | Exclude DESERT |
| ![Tree preview](images/environmental/cnc/t02.png) | `T02` | Tree | 2,2 `__ x_` | SpawnActorOnDeath | Exclude DESERT |
| ![Tree preview](images/environmental/cnc/t03.png) | `T03` | Tree | 2,2 `__ x_` | SpawnActorOnDeath | Exclude DESERT |
| ![Tree preview](images/environmental/cnc/t04.png) | `T04` | Tree | 2,2 `__ x_` | SpawnActorOnDeath | Require DESERT |
| ![Tree preview](images/environmental/cnc/t05.png) | `T05` | Tree | 2,2 `__ x_` | SpawnActorOnDeath | Exclude DESERT |
| ![Tree preview](images/environmental/cnc/t06.png) | `T06` | Tree | 2,2 `__ x_` | SpawnActorOnDeath | Exclude DESERT |
| ![Tree preview](images/environmental/cnc/t07.png) | `T07` | Tree | 2,2 `__ x_` | SpawnActorOnDeath | Exclude DESERT |
| ![Tree preview](images/environmental/cnc/t08.png) | `T08` | Tree | 2,1 `x_` | SpawnActorOnDeath | — |
| ![Tree preview](images/environmental/cnc/t09.png) | `T09` | Tree | 2,1 `x_` | SpawnActorOnDeath | Require DESERT |
| ![Tree preview](images/environmental/cnc/t10.png) | `T10` | Tree | 2,2 `__ xx` | SpawnActorOnDeath | Exclude DESERT |
| ![Tree preview](images/environmental/cnc/t11.png) | `T11` | Tree | 2,2 `__ xx` | SpawnActorOnDeath | Exclude DESERT |
| ![Tree preview](images/environmental/cnc/t12.png) | `T12` | Tree | 2,2 `__ x_` | SpawnActorOnDeath | Exclude DESERT |
| ![Tree preview](images/environmental/cnc/t13.png) | `T13` | Tree | 2,2 `__ x_` | SpawnActorOnDeath | Exclude DESERT |
| ![Tree preview](images/environmental/cnc/t14.png) | `T14` | Tree | 2,2 `__ x_` | SpawnActorOnDeath | Exclude DESERT |
| ![Tree preview](images/environmental/cnc/t15.png) | `T15` | Tree | 3,2 `___ xx_` | SpawnActorOnDeath | Exclude DESERT |
| ![Tree preview](images/environmental/cnc/t16.png) | `T16` | Tree | 2,2 `__ x_` | SpawnActorOnDeath | Exclude DESERT |
| ![Tree preview](images/environmental/cnc/t17.png) | `T17` | Tree | 2,2 `__ x_` | SpawnActorOnDeath | Exclude DESERT |
| ![Tree preview](images/environmental/cnc/t18.png) | `T18` | Tree | 2,2 `__ x_` | SpawnActorOnDeath | Require DESERT |
| ![Tree preview](images/environmental/cnc/tc01.png) | `TC01` | Tree | 3,2 `___ xx_` | SpawnActorOnDeath | Exclude DESERT |
| ![Tree preview](images/environmental/cnc/tc02.png) | `TC02` | Tree | 3,2 `_x_ xx_` | SpawnActorOnDeath | Exclude DESERT |
| ![Tree preview](images/environmental/cnc/tc03.png) | `TC03` | Tree | 3,2 `_x_ xx_` | SpawnActorOnDeath | Exclude DESERT |
| ![Tree preview](images/environmental/cnc/tc04.png) | `TC04` | Tree | 4,3 `____ xxx_ x___` | SpawnActorOnDeath | Exclude DESERT |
| ![Tree preview](images/environmental/cnc/tc05.png) | `TC05` | Tree | 4,3 `__x_ xxx_ _xx_` | SpawnActorOnDeath | Exclude DESERT |

### Rocks and Cliffs (7)
| Preview | Actor | Name/Tooltip | Size | Key Traits | Notes |
| :---: | :--- | :--- | :--- | :--- | :--- |
| ![Rock preview](images/environmental/cnc/rock1.png) | `ROCK1` | Rock | 2,2 `__ xx` | — | Require DESERT |
| ![Rock preview](images/environmental/cnc/rock2.png) | `ROCK2` | Rock | 3,1 `xx_` | — | Require DESERT |
| ![Rock preview](images/environmental/cnc/rock3.png) | `ROCK3` | Rock | 2,2 `__ x_` | — | Require DESERT |
| ![Rock preview](images/environmental/cnc/rock4.png) | `ROCK4` | Rock | 1,1 `x` | — | Require DESERT |
| ![Rock preview](images/environmental/cnc/rock5.png) | `ROCK5` | Rock | 2,1 `x_` | — | Require DESERT |
| ![Rock preview](images/environmental/cnc/rock6.png) | `ROCK6` | Rock | 3,2 `___ xxx` | — | Require DESERT |
| ![Rock preview](images/environmental/cnc/rock7.png) | `ROCK7` | Rock | 4,1 `xxxx` | — | Require DESERT |

### Buildings and Structures (41)
| Preview | Actor | Name/Tooltip | Size | Key Traits | Notes |
| :---: | :--- | :--- | :--- | :--- | :--- |
| ![Tech Center preview](images/environmental/cnc/miss.png) | `MISS` | Tech Center | 3,2 `xxx xxx` | FireWarheadsOnDeath, Capturable, InstantlyRepairable, RevealsShroud, WithBuildingBib, Demolishable | — |
| ![Biological Lab preview](images/environmental/cnc/bio.png) | `BIO` | Biological Lab | 2,2 `xx xx` | SpawnActorOnDeath, FireWarheadsOnDeath, Capturable, InstantlyRepairable, RevealsShroud, Demolishable | — |
| ![Oil Pump preview](images/environmental/cnc/arco.png) | `ARCO` | Oil Pump | 2,1 `xx` | SpawnActorOnDeath, FireWarheadsOnDeath, Demolishable | — |
| ![Sala's House preview](images/environmental/cnc/v20.png) | `V20` | Sala's House | 2,2 `xx xx` | SpawnActorOnDeath, FireWarheadsOnDeath, Demolishable | Require DESERT |
| ![Abdul's House preview](images/environmental/cnc/v21.png) | `V21` | Abdul's House | 2,2 `xx xx` | SpawnActorOnDeath, FireWarheadsOnDeath, Demolishable | Require DESERT |
| ![Pablo's Wicked Pub preview](images/environmental/cnc/v22.png) | `V22` | Pablo's Wicked Pub | 2,1 `xx` | SpawnActorOnDeath, FireWarheadsOnDeath, Demolishable | Require DESERT |
| ![Village Well preview](images/environmental/cnc/v23.png) | `V23` | Village Well | 1,1 `x` | SpawnActorOnDeath, FireWarheadsOnDeath, Demolishable | Require DESERT |
| ![Camel Trader preview](images/environmental/cnc/v24.png) | `V24` | Camel Trader | 2,2 `xx xx` | SpawnActorOnDeath, FireWarheadsOnDeath, Demolishable | Require DESERT |
| ![Church preview](images/environmental/cnc/v25.png) | `V25` | Church | 2,2 `xx xx` | SpawnActorOnDeath, FireWarheadsOnDeath, Demolishable | Require DESERT |
| ![Ali's House preview](images/environmental/cnc/v26.png) | `V26` | Ali's House | 2,1 `xx` | SpawnActorOnDeath, FireWarheadsOnDeath, Demolishable | Require DESERT |
| ![Trader Ted's preview](images/environmental/cnc/v27.png) | `V27` | Trader Ted's | 1,1 `x` | SpawnActorOnDeath, FireWarheadsOnDeath, Demolishable | Require DESERT |
| ![Menelik's House preview](images/environmental/cnc/v28.png) | `V28` | Menelik's House | 1,1 `x` | SpawnActorOnDeath, FireWarheadsOnDeath, Demolishable | Require DESERT |
| ![Prestor John's House preview](images/environmental/cnc/v29.png) | `V29` | Prestor John's House | 1,1 `x` | SpawnActorOnDeath, FireWarheadsOnDeath, Demolishable | Require DESERT |
| ![Village Well preview](images/environmental/cnc/v30.png) | `V30` | Village Well | 2,1 `xx` | SpawnActorOnDeath, FireWarheadsOnDeath, Demolishable | Require DESERT |
| ![Witch Doctor's Hut preview](images/environmental/cnc/v31.png) | `V31` | Witch Doctor's Hut | 2,1 `xx` | SpawnActorOnDeath, FireWarheadsOnDeath, Demolishable | Require DESERT |
| ![Rikitikitembo's Hut preview](images/environmental/cnc/v32.png) | `V32` | Rikitikitembo's Hut | 2,1 `xx` | SpawnActorOnDeath, FireWarheadsOnDeath, Demolishable | Require DESERT |
| ![Roarke's Hut preview](images/environmental/cnc/v33.png) | `V33` | Roarke's Hut | 2,1 `xx` | SpawnActorOnDeath, FireWarheadsOnDeath, Demolishable | Require DESERT |
| ![Mubasa's Hut preview](images/environmental/cnc/v34.png) | `V34` | Mubasa's Hut | 1,1 `x` | SpawnActorOnDeath, FireWarheadsOnDeath, Demolishable | Require DESERT |
| ![Aksum's Hut preview](images/environmental/cnc/v35.png) | `V35` | Aksum's Hut | 1,1 `x` | SpawnActorOnDeath, FireWarheadsOnDeath, Demolishable | Require DESERT |
| ![Mambo's Hut preview](images/environmental/cnc/v36.png) | `V36` | Mambo's Hut | 1,1 `x` | SpawnActorOnDeath, FireWarheadsOnDeath, Demolishable | Require DESERT |
| ![The Studio preview](images/environmental/cnc/v37.png) | `V37` | The Studio | 5,2 `__xx_ ___xx` | SpawnActorOnDeath, FireWarheadsOnDeath, Demolishable | Require DESERT |
| ![Church preview](images/environmental/cnc/v01.png) | `V01` | Church | 2,2 `xx xx` | SpawnActorOnDeath, FireWarheadsOnDeath, Demolishable | Exclude DESERT |
| ![Hans and Gretel's House preview](images/environmental/cnc/v02.png) | `V02` | Hans and Gretel's House | 2,2 `xx xx` | SpawnActorOnDeath, FireWarheadsOnDeath, Demolishable | Exclude DESERT |
| ![Hewitt's House preview](images/environmental/cnc/v03.png) | `V03` | Hewitt's House | 2,2 `xx xx` | SpawnActorOnDeath, FireWarheadsOnDeath, Demolishable | Exclude DESERT |
| ![Ricktor's House preview](images/environmental/cnc/v04.png) | `V04` | Ricktor's House | 2,2 `xx xx` | SpawnActorOnDeath, FireWarheadsOnDeath, Demolishable | Exclude DESERT |
| ![Gretchkin's House preview](images/environmental/cnc/v05.png) | `V05` | Gretchkin's House | 2,1 `xx` | SpawnActorOnDeath, FireWarheadsOnDeath, Demolishable | Exclude DESERT |
| ![The Barn preview](images/environmental/cnc/v06.png) | `V06` | The Barn | 2,1 `xx` | SpawnActorOnDeath, FireWarheadsOnDeath, Demolishable | Exclude DESERT |
| ![Damon's Pub preview](images/environmental/cnc/v07.png) | `V07` | Damon's Pub | 2,1 `xx` | SpawnActorOnDeath, FireWarheadsOnDeath, Demolishable | Exclude DESERT |
| ![Fran's House preview](images/environmental/cnc/v08.png) | `V08` | Fran's House | 1,1 `x` | SpawnActorOnDeath, FireWarheadsOnDeath, Demolishable | Exclude DESERT |
| ![Music Factory preview](images/environmental/cnc/v09.png) | `V09` | Music Factory | 1,1 `x` | SpawnActorOnDeath, FireWarheadsOnDeath, Demolishable | Exclude DESERT |
| ![Toymaker's preview](images/environmental/cnc/v10.png) | `V10` | Toymaker's | 1,1 `x` | SpawnActorOnDeath, FireWarheadsOnDeath, Demolishable | Exclude DESERT |
| ![Ludwig's House preview](images/environmental/cnc/v11.png) | `V11` | Ludwig's House | 1,1 `x` | SpawnActorOnDeath, FireWarheadsOnDeath, Demolishable | Exclude DESERT |
| ![— preview](images/environmental/cnc/v12.png) | `V12` | — | 1,1 `x` | SpawnActorOnDeath | Exclude DESERT; Non-interactive field |
| ![— preview](images/environmental/cnc/v13.png) | `V13` | — | 1,1 `x` | SpawnActorOnDeath | Exclude DESERT; Non-interactive field |
| ![Wheat Field preview](images/environmental/cnc/v14.png) | `V14` | Wheat Field | 1,1 `x` | SpawnActorOnDeath | Exclude DESERT; Non-interactive field |
| ![Fallow Field preview](images/environmental/cnc/v15.png) | `V15` | Fallow Field | 1,1 `x` | SpawnActorOnDeath | Exclude DESERT; Non-interactive field |
| ![Corn Field preview](images/environmental/cnc/v16.png) | `V16` | Corn Field | 1,1 `x` | SpawnActorOnDeath | Exclude DESERT; Non-interactive field |
| ![Celery Field preview](images/environmental/cnc/v17.png) | `V17` | Celery Field | 1,1 `x` | SpawnActorOnDeath | Exclude DESERT; Non-interactive field |
| ![Potato Field preview](images/environmental/cnc/v18.png) | `V18` | Potato Field | 1,1 `x` | SpawnActorOnDeath | Exclude DESERT; Non-interactive field |
| ![Oil Derrick preview](images/environmental/cnc/v19.png) | `V19` | Oil Derrick | 1,1 `x` | SpawnActorOnDeath, FireWarheadsOnDeath, CashTrickler, Capturable, InstantlyRepairable, RevealsShroud, Demolishable | — |
| ![Hospital preview](images/environmental/cnc/hosp.png) | `HOSP` | Hospital | 2,2 `xx xx` | SpawnActorOnDeath, FireWarheadsOnDeath, Capturable, InstantlyRepairable, RevealsShroud, WithBuildingBib, Demolishable | — |

### Walls and Fences (5)
| Preview | Actor | Name/Tooltip | Size | Key Traits | Notes |
| :---: | :--- | :--- | :--- | :--- | :--- |
| ![Barbwire Fence preview](images/environmental/cnc/barb.png) | `BARB` | Barbwire Fence | 1,1 `x` | Crushable | — |
| ![Wooden Fence preview](images/environmental/cnc/wood.png) | `WOOD` | Wooden Fence | 1,1 `x` | Crushable | — |
| ![Sandbag Barrier preview](images/environmental/cnc/sbag.png) | `SBAG` | Sandbag Barrier | 1,1 `x` | Crushable | — |
| ![Chain Link Barrier preview](images/environmental/cnc/cycl.png) | `CYCL` | Chain Link Barrier | 1,1 `x` | Crushable | — |
| ![Concrete Barrier preview](images/environmental/cnc/brik.png) | `BRIK` | Concrete Barrier | 1,1 `x` | Crushable | — |

### Bridges (5)
| Preview | Actor | Name/Tooltip | Size | Key Traits | Notes |
| :---: | :--- | :--- | :--- | :--- | :--- |
| ![Bridge preview](images/environmental/cnc/bridge1.png) | `BRIDGE1` | Bridge | 4,4 `____ ____ ____ ____` | — | — |
| ![Bridge preview](images/environmental/cnc/bridge2.png) | `BRIDGE2` | Bridge | 5,5 `_____ _____ _____ _____ _____` | — | — |
| ![Bridge preview](images/environmental/cnc/bridge3.png) | `BRIDGE3` | Bridge | 6,5 `______ ______ ______ ______ ______` | — | — |
| ![Bridge preview](images/environmental/cnc/bridge4.png) | `BRIDGE4` | Bridge | 6,4 `______ ______ ______ ______` | — | — |
| ![— preview](images/environmental/cnc/bridgehut.png) | `BRIDGEHUT` | — | 2,2 `__ __` | — | — |

### Resource Spawns (3)
| Preview | Actor | Name/Tooltip | Size | Key Traits | Notes |
| :---: | :--- | :--- | :--- | :--- | :--- |
| ![Blossom Tree preview](images/environmental/cnc/split2.png) | `SPLIT2` | Blossom Tree | 1,1 `x` | SeedsResource | — |
| ![Blossom Tree preview](images/environmental/cnc/split3.png) | `SPLIT3` | Blossom Tree | 1,1 `x` | SeedsResource | — |
| ![Blue Blossom Tree preview](images/environmental/cnc/splitblue.png) | `SPLITBLUE` | Blue Blossom Tree | 1,1 `x` | SeedsResource | — |

### Civilians (13)
| Preview | Actor | Name/Tooltip | Size | Key Traits | Notes |
| :---: | :--- | :--- | :--- | :--- | :--- |
| ![Civilian preview](images/environmental/cnc/c1.png) | `C1` | Civilian | — | SpawnActorOnDeath, RevealsShroud, Crushable | — |
| ![Civilian preview](images/environmental/cnc/c2.png) | `C2` | Civilian | — | SpawnActorOnDeath, RevealsShroud, Crushable | — |
| ![Civilian preview](images/environmental/cnc/c3.png) | `C3` | Civilian | — | SpawnActorOnDeath, RevealsShroud, Crushable | — |
| ![Civilian preview](images/environmental/cnc/c4.png) | `C4` | Civilian | — | SpawnActorOnDeath, RevealsShroud, Crushable | — |
| ![Civilian preview](images/environmental/cnc/c5.png) | `C5` | Civilian | — | SpawnActorOnDeath, RevealsShroud, Crushable | — |
| ![Civilian preview](images/environmental/cnc/c6.png) | `C6` | Civilian | — | SpawnActorOnDeath, RevealsShroud, Crushable | — |
| ![Civilian preview](images/environmental/cnc/c7.png) | `C7` | Civilian | — | SpawnActorOnDeath, RevealsShroud, Crushable | — |
| ![Civilian preview](images/environmental/cnc/c8.png) | `C8` | Civilian | — | SpawnActorOnDeath, RevealsShroud, Crushable | — |
| ![Civilian preview](images/environmental/cnc/c9.png) | `C9` | Civilian | — | SpawnActorOnDeath, RevealsShroud, Crushable | — |
| ![Civilian preview](images/environmental/cnc/c10.png) | `C10` | Civilian | — | SpawnActorOnDeath, RevealsShroud, Crushable | — |
| ![Agent Delphi preview](images/environmental/cnc/delphi.png) | `DELPHI` | Agent Delphi | — | SpawnActorOnDeath, RevealsShroud, Crushable | — |
| ![Dr. Chan preview](images/environmental/cnc/chan.png) | `CHAN` | Dr. Chan | — | SpawnActorOnDeath, RevealsShroud, Crushable | — |
| ![Dr. Moebius preview](images/environmental/cnc/moebius.png) | `MOEBIUS` | Dr. Moebius | — | SpawnActorOnDeath, RevealsShroud, Crushable | — |

### Critters and Wildlife (6)
| Preview | Actor | Name/Tooltip | Size | Key Traits | Notes |
| :---: | :--- | :--- | :--- | :--- | :--- |
| ![Visceroid preview](images/environmental/cnc/vice.png) | `VICE` | Visceroid | — | RevealsShroud | — |
| ![Visceroid preview](images/environmental/cnc/pvice.png) | `PVICE` | Visceroid | — | RevealsShroud | — |
| ![Stegosaurus preview](images/environmental/cnc/steg.png) | `STEG` | Stegosaurus | — | RevealsShroud | — |
| ![Tyrannosaurus rex preview](images/environmental/cnc/trex.png) | `TREX` | Tyrannosaurus rex | — | RevealsShroud | — |
| ![Triceratops preview](images/environmental/cnc/tric.png) | `TRIC` | Triceratops | — | RevealsShroud | — |
| ![Velociraptor preview](images/environmental/cnc/rapt.png) | `RAPT` | Velociraptor | — | RevealsShroud | — |

## Dune 2000
*12 environmental actors.*

### Buildings and Structures (1)
| Preview | Actor | Name/Tooltip | Size | Key Traits | Notes |
| :---: | :--- | :--- | :--- | :--- | :--- |
| ![Fremen Sietch preview](images/environmental/d2k/sietch.png) | `sietch` | Fremen Sietch | 2,2 `xx xx` | FireWarheadsOnDeath, RevealsShroud, Demolishable | — |

### Crates and Pickups (1)
| Preview | Actor | Name/Tooltip | Size | Key Traits | Notes |
| :---: | :--- | :--- | :--- | :--- | :--- |
| ![Crate preview](images/environmental/d2k/crate.png) | `crate` | Crate | — | — | — |

### Resource Spawns (1)
| Preview | Actor | Name/Tooltip | Size | Key Traits | Notes |
| :---: | :--- | :--- | :--- | :--- | :--- |
| ![Spice Bloom preview](images/environmental/d2k/spicebloom.png) | `spicebloom` | Spice Bloom | — | SpawnActorOnDeath, FireWarheadsOnDeath, SpiceBloom, Crushable | — |

### Critters and Wildlife (1)
| Preview | Actor | Name/Tooltip | Size | Key Traits | Notes |
| :---: | :--- | :--- | :--- | :--- | :--- |
| ![Sandworm preview](images/environmental/d2k/sandworm.png) | `sandworm` | Sandworm | — | RevealsShroud, AttackSwallow, Sandworm | — |

### Destructible Terrain (8)
| Preview | Actor | Name/Tooltip | Size | Key Traits | Notes |
| :---: | :--- | :--- | :--- | :--- | :--- |
| ![Passage (destroyable) preview](images/environmental/d2k/pass01_destroyable_bottom.png) | `pass01_destroyable_bottom` | Passage (destroyable) | 3,3 `=== X=X X=X` | SpawnActorOnDeath, FireWarheadsOnDeath | — |
| ![Passage (repairable) preview](images/environmental/d2k/pass01_destroyed_bottom.png) | `pass01_destroyed_bottom` | Passage (repairable) | 3,3 `=== xxx xxx` | Capturable, TransformOnCapture | — |
| ![Passage (destroyable) preview](images/environmental/d2k/pass01_destroyable_left.png) | `pass01_destroyable_left` | Passage (destroyable) | 3,3 `XX= === XX=` | SpawnActorOnDeath, FireWarheadsOnDeath | — |
| ![Passage (repairable) preview](images/environmental/d2k/pass01_destroyed_left.png) | `pass01_destroyed_left` | Passage (repairable) | 3,3 `xx= xx= xx=` | Capturable, TransformOnCapture | — |
| ![Passage (destroyable) preview](images/environmental/d2k/pass01_destroyable_right.png) | `pass01_destroyable_right` | Passage (destroyable) | 3,3 `=XX === =XX` | SpawnActorOnDeath, FireWarheadsOnDeath | — |
| ![Passage (repairable) preview](images/environmental/d2k/pass01_destroyed_right.png) | `pass01_destroyed_right` | Passage (repairable) | 3,3 `=xx =xx =xx` | Capturable, TransformOnCapture | — |
| ![Passage (destroyable) preview](images/environmental/d2k/pass01_destroyable_top.png) | `pass01_destroyable_top` | Passage (destroyable) | 3,3 `X=X X=X ===` | SpawnActorOnDeath, FireWarheadsOnDeath | — |
| ![Passage (repairable) preview](images/environmental/d2k/pass01_destroyed_top.png) | `pass01_destroyed_top` | Passage (repairable) | 3,3 `XxX xxx xxx` | Capturable, TransformOnCapture | — |

## Tiberian Sun
*231 environmental actors.*

### Vegetation (40)
| Preview | Actor | Name/Tooltip | Size | Key Traits | Notes |
| :---: | :--- | :--- | :--- | :--- | :--- |
| ![Tree preview](images/environmental/ts/tree01.png) | `TREE01` | Tree | 1, 1 `x` | — | — |
| ![Tree preview](images/environmental/ts/tree02.png) | `TREE02` | Tree | 1, 1 `x` | — | — |
| ![Tree preview](images/environmental/ts/tree03.png) | `TREE03` | Tree | 1, 1 `x` | — | — |
| ![Tree preview](images/environmental/ts/tree04.png) | `TREE04` | Tree | 1, 1 `x` | — | — |
| ![Tree preview](images/environmental/ts/tree05.png) | `TREE05` | Tree | 1, 1 `x` | — | — |
| ![Tree preview](images/environmental/ts/tree06.png) | `TREE06` | Tree | 1, 1 `x` | — | — |
| ![Tree preview](images/environmental/ts/tree07.png) | `TREE07` | Tree | 1, 1 `x` | — | — |
| ![Tree preview](images/environmental/ts/tree08.png) | `TREE08` | Tree | 1, 1 `x` | — | — |
| ![Tree preview](images/environmental/ts/tree09.png) | `TREE09` | Tree | 1, 1 `x` | — | — |
| ![Tree preview](images/environmental/ts/tree10.png) | `TREE10` | Tree | 1, 1 `x` | — | — |
| ![Tree preview](images/environmental/ts/tree11.png) | `TREE11` | Tree | 1, 1 `x` | — | — |
| ![Tree preview](images/environmental/ts/tree12.png) | `TREE12` | Tree | 1, 1 `x` | — | — |
| ![Tree preview](images/environmental/ts/tree13.png) | `TREE13` | Tree | 1, 1 `x` | — | — |
| ![Tree preview](images/environmental/ts/tree14.png) | `TREE14` | Tree | 1, 1 `x` | — | — |
| ![Tree preview](images/environmental/ts/tree15.png) | `TREE15` | Tree | 1, 1 `x` | — | — |
| ![Tree preview](images/environmental/ts/tree16.png) | `TREE16` | Tree | 1, 1 `x` | — | — |
| ![Tree preview](images/environmental/ts/tree17.png) | `TREE17` | Tree | 1, 1 `x` | — | — |
| ![Tree preview](images/environmental/ts/tree18.png) | `TREE18` | Tree | 1, 1 `x` | — | — |
| ![Tree preview](images/environmental/ts/tree19.png) | `TREE19` | Tree | 1, 1 `x` | — | — |
| ![Tree preview](images/environmental/ts/tree20.png) | `TREE20` | Tree | 1, 1 `x` | — | — |
| ![Tree preview](images/environmental/ts/tree21.png) | `TREE21` | Tree | 1, 1 `x` | — | — |
| ![Tree preview](images/environmental/ts/tree22.png) | `TREE22` | Tree | 1, 1 `x` | — | — |
| ![Tree preview](images/environmental/ts/tree23.png) | `TREE23` | Tree | 1, 1 `x` | — | — |
| ![Tree preview](images/environmental/ts/tree24.png) | `TREE24` | Tree | 1, 1 `x` | — | — |
| ![Tree preview](images/environmental/ts/tree25.png) | `TREE25` | Tree | 1, 1 `x` | — | — |
| ![Tiberian Flora preview](images/environmental/ts/fona01.png) | `FONA01` | Tiberian Flora | 1, 1 `x` | — | Require TEMPERATE |
| ![Tiberian Flora preview](images/environmental/ts/fona02.png) | `FONA02` | Tiberian Flora | 1, 1 `x` | — | Require TEMPERATE |
| ![Tiberian Flora preview](images/environmental/ts/fona03.png) | `FONA03` | Tiberian Flora | 1, 1 `x` | — | Require TEMPERATE |
| ![Tiberian Flora preview](images/environmental/ts/fona04.png) | `FONA04` | Tiberian Flora | 1, 1 `x` | — | Require TEMPERATE |
| ![Tiberian Flora preview](images/environmental/ts/fona05.png) | `FONA05` | Tiberian Flora | 1, 1 `x` | — | Require TEMPERATE |
| ![Tiberian Flora preview](images/environmental/ts/fona06.png) | `FONA06` | Tiberian Flora | 1, 1 `x` | — | Require TEMPERATE |
| ![Tiberian Flora preview](images/environmental/ts/fona07.png) | `FONA07` | Tiberian Flora | 1, 1 `x` | — | Require TEMPERATE |
| ![Tiberian Flora preview](images/environmental/ts/fona08.png) | `FONA08` | Tiberian Flora | 1, 1 `x` | — | Require TEMPERATE |
| ![Tiberian Flora preview](images/environmental/ts/fona09.png) | `FONA09` | Tiberian Flora | 1, 1 `x` | — | Require TEMPERATE |
| ![Tiberian Flora preview](images/environmental/ts/fona10.png) | `FONA10` | Tiberian Flora | 1, 1 `x` | — | Require TEMPERATE |
| ![Tiberian Flora preview](images/environmental/ts/fona11.png) | `FONA11` | Tiberian Flora | 1, 1 `x` | — | Require TEMPERATE |
| ![Tiberian Flora preview](images/environmental/ts/fona12.png) | `FONA12` | Tiberian Flora | 1, 1 `x` | — | Require TEMPERATE |
| ![Tiberian Flora preview](images/environmental/ts/fona13.png) | `FONA13` | Tiberian Flora | 1, 1 `x` | — | Require TEMPERATE |
| ![Tiberian Flora preview](images/environmental/ts/fona14.png) | `FONA14` | Tiberian Flora | 1, 1 `x` | — | Require TEMPERATE |
| ![Tiberian Flora preview](images/environmental/ts/fona15.png) | `FONA15` | Tiberian Flora | 1, 1 `x` | — | Require TEMPERATE |

### Rocks and Cliffs (10)
| Preview | Actor | Name/Tooltip | Size | Key Traits | Notes |
| :---: | :--- | :--- | :--- | :--- | :--- |
| ![Rock preview](images/environmental/ts/srock01.png) | `SROCK01` | Rock | 1, 1 `x` | — | — |
| ![Rock preview](images/environmental/ts/srock02.png) | `SROCK02` | Rock | 1, 1 `x` | — | — |
| ![Rock preview](images/environmental/ts/srock03.png) | `SROCK03` | Rock | 1, 1 `x` | — | — |
| ![Rock preview](images/environmental/ts/srock04.png) | `SROCK04` | Rock | 1, 1 `x` | — | — |
| ![Rock preview](images/environmental/ts/srock05.png) | `SROCK05` | Rock | 1, 1 `x` | — | — |
| ![Rock preview](images/environmental/ts/trock01.png) | `TROCK01` | Rock | 1, 1 `x` | — | — |
| ![Rock preview](images/environmental/ts/trock02.png) | `TROCK02` | Rock | 1, 1 `x` | — | — |
| ![Rock preview](images/environmental/ts/trock03.png) | `TROCK03` | Rock | 1, 1 `x` | — | — |
| ![Rock preview](images/environmental/ts/trock04.png) | `TROCK04` | Rock | 1, 1 `x` | — | — |
| ![Rock preview](images/environmental/ts/trock05.png) | `TROCK05` | Rock | 1, 1 `x` | — | — |

### Buildings and Structures (79)
| Preview | Actor | Name/Tooltip | Size | Key Traits | Notes |
| :---: | :--- | :--- | :--- | :--- | :--- |
| ![WS Logging Company preview](images/environmental/ts/aban01.png) | `ABAN01` | WS Logging Company | 2, 6 `xx xx xx xx xx XX` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | Exclude TEMPERATE |
| ![Panullo Hacienda preview](images/environmental/ts/aban02.png) | `ABAN02` | Panullo Hacienda | 5, 3 `xxxxx xxxxx XXXxX` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | Exclude TEMPERATE |
| ![Abandoned Factory preview](images/environmental/ts/aban03.png) | `ABAN03` | Abandoned Factory | 2, 5 `xx xx xx xx XX` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | Exclude TEMPERATE |
| ![City Hall preview](images/environmental/ts/aban04.png) | `ABAN04` | City Hall | 4, 2 `xxxX xxxX` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | Exclude TEMPERATE |
| ![Hunting Lodge preview](images/environmental/ts/aban05.png) | `ABAN05` | Hunting Lodge | 3, 2 `xxX xxX` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | Exclude TEMPERATE |
| ![Local Inn & Lodging preview](images/environmental/ts/aban06.png) | `ABAN06` | Local Inn & Lodging | 2, 2 `xx xx` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | Exclude TEMPERATE |
| ![Church preview](images/environmental/ts/aban07.png) | `ABAN07` | Church | 2, 2 `xx xx` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | Exclude TEMPERATE |
| ![Abandoned Warehouse preview](images/environmental/ts/aban08.png) | `ABAN08` | Abandoned Warehouse | 2, 2 `xx xx` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | Exclude TEMPERATE |
| ![Tall's Residence preview](images/environmental/ts/aban09.png) | `ABAN09` | Tall's Residence | 2, 2 `xx xx` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | Exclude TEMPERATE |
| ![Denzil's Last Chance Motel preview](images/environmental/ts/aban10.png) | `ABAN10` | Denzil's Last Chance Motel | 2, 2 `xx xx` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | Exclude TEMPERATE |
| ![Miele Manor preview](images/environmental/ts/aban11.png) | `ABAN11` | Miele Manor | 2, 2 `xx xx` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | Exclude TEMPERATE |
| ![Kettler's Place preview](images/environmental/ts/aban12.png) | `ABAN12` | Kettler's Place | 2, 2 `xx xx` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | Exclude TEMPERATE |
| ![Long's Home preview](images/environmental/ts/aban13.png) | `ABAN13` | Long's Home | 1, 1 `x` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | Exclude TEMPERATE |
| ![Local Store preview](images/environmental/ts/aban14.png) | `ABAN14` | Local Store | 1, 1 `x` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | Exclude TEMPERATE |
| ![Adam's House preview](images/environmental/ts/aban15.png) | `ABAN15` | Adam's House | 1, 1 `x` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | Exclude TEMPERATE |
| ![Gas Station preview](images/environmental/ts/aban16.png) | `ABAN16` | Gas Station | 2, 2 `xx xX` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | Exclude TEMPERATE |
| ![Gas Pumps preview](images/environmental/ts/aban17.png) | `ABAN17` | Gas Pumps | 1, 1 `x` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | Exclude TEMPERATE |
| ![Gas Station Sign preview](images/environmental/ts/aban18.png) | `ABAN18` | Gas Station Sign | 1, 1 `x` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | Exclude TEMPERATE |
| ![Ammo Crates preview](images/environmental/ts/ammocrat.png) | `AMMOCRAT` | Ammo Crates | 1, 1 `x` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | — |
| ![Rade's Roadhouse preview](images/environmental/ts/ca0001.png) | `CA0001` | Rade's Roadhouse | 3, 3 `xxX xxX XXX` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | — |
| ![Sandberg and Son's preview](images/environmental/ts/ca0002.png) | `CA0002` | Sandberg and Son's | 3, 3 `xxX xxx Xxx` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | — |
| ![Temp Housing preview](images/environmental/ts/ca0003.png) | `CA0003` | Temp Housing | 2, 2 `xx xx` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | — |
| ![Waystation preview](images/environmental/ts/ca0004.png) | `CA0004` | Waystation | 2, 2 `xx xX` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | — |
| ![Ferbie's 4 Sale preview](images/environmental/ts/ca0005.png) | `CA0005` | Ferbie's 4 Sale | 1, 2 `x x` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | — |
| ![Deluxe Accomodations preview](images/environmental/ts/ca0006.png) | `CA0006` | Deluxe Accomodations | 1, 2 `x x` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | — |
| ![Field Generator preview](images/environmental/ts/ca0007.png) | `CA0007` | Field Generator | 1, 2 `x x` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | — |
| ![Subterranean Dwelling preview](images/environmental/ts/ca0008.png) | `CA0008` | Subterranean Dwelling | 2, 3 `xX xX xx` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | — |
| ![Subterranean Dwelling preview](images/environmental/ts/ca0009.png) | `CA0009` | Subterranean Dwelling | 2, 3 `xX xx xX` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | — |
| ![Leary Traveller Inn preview](images/environmental/ts/ca0010.png) | `CA0010` | Leary Traveller Inn | 2, 2 `xx xx` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | — |
| ![Water Tank preview](images/environmental/ts/ca0011.png) | `CA0011` | Water Tank | 1, 2 `x x` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | — |
| ![Greenhouse preview](images/environmental/ts/ca0012.png) | `CA0012` | Greenhouse | 1, 2 `x x` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | — |
| ![Water Purifier preview](images/environmental/ts/ca0013.png) | `CA0013` | Water Purifier | 2, 1 `xx` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | — |
| ![Observation Tower preview](images/environmental/ts/ca0014.png) | `CA0014` | Observation Tower | 1, 1 `x` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | — |
| ![Port-A-Shack preview](images/environmental/ts/ca0015.png) | `CA0015` | Port-A-Shack | 1, 1 `x` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | — |
| ![Port-A-Shack Deluxe preview](images/environmental/ts/ca0016.png) | `CA0016` | Port-A-Shack Deluxe | 1, 1 `x` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | — |
| ![Energy Transformer preview](images/environmental/ts/ca0017.png) | `CA0017` | Energy Transformer | 1, 1 `x` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | — |
| ![Solar Panel preview](images/environmental/ts/ca0018.png) | `CA0018` | Solar Panel | 1, 2 `x x` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | — |
| ![Solar Panel preview](images/environmental/ts/ca0019.png) | `CA0019` | Solar Panel | 1, 2 `x x` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | — |
| ![Solar Panel preview](images/environmental/ts/ca0020.png) | `CA0020` | Solar Panel | 1, 2 `x x` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | — |
| ![Solar Panel preview](images/environmental/ts/ca0021.png) | `CA0021` | Solar Panel | 1, 2 `x x` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | — |
| ![Civilian Array preview](images/environmental/ts/caaray.png) | `CAARAY` | Civilian Array | 2, 2 `xx xx` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | — |
| ![Civilian Armory preview](images/environmental/ts/caarmr.png) | `CAARMR` | Civilian Armory | 4, 4 `xxxx xxxx xxxx xxxx` | FireWarheadsOnDeath, Capturable, InstantlyRepairable, RevealsShroud, ProvidesPrerequisite, Demolishable | — |
| ![Pyramid preview](images/environmental/ts/capyr01.png) | `CAPYR01` | Pyramid | 2, 2 `xx xx` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | Exclude SNOW |
| ![Pyramid preview](images/environmental/ts/capyr02.png) | `CAPYR02` | Pyramid | 4, 4 `xxxx xxxx xxxx xxxx` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | Exclude SNOW |
| ![Pyramid preview](images/environmental/ts/capyr03.png) | `CAPYR03` | Pyramid | 4, 4 `xxxx xxxx xxxx xxxx` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | Exclude SNOW |
| ![Connelly Court Apts preview](images/environmental/ts/city01.png) | `CITY01` | Connelly Court Apts | 4, 2 `xxxX XxxX` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | Require TEMPERATE |
| ![Lightner's Luxury Suites preview](images/environmental/ts/city02.png) | `CITY02` | Lightner's Luxury Suites | 2, 3 `xx xx xx` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | Require TEMPERATE |
| ![Office Building preview](images/environmental/ts/city03.png) | `CITY03` | Office Building | 3, 2 `xxx xxx` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | Require TEMPERATE |
| ![Westwood Stock Exchange preview](images/environmental/ts/city04.png) | `CITY04` | Westwood Stock Exchange | 3, 2 `xxx xxx` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | Require TEMPERATE |
| ![Daily Sun Times preview](images/environmental/ts/city05.png) | `CITY05` | Daily Sun Times | 3, 2 `xxx xxx` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | Require TEMPERATE |
| ![YEO-CA Cola Corp. preview](images/environmental/ts/city06.png) | `CITY06` | YEO-CA Cola Corp. | 4, 2 `xxxx XxxX` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | Require TEMPERATE |
| ![Urban Housing preview](images/environmental/ts/city07.png) | `CITY07` | Urban Housing | 4, 2 `xxxx xxxx` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | Require TEMPERATE |
| ![Yee's Discount Liquor preview](images/environmental/ts/city08.png) | `CITY08` | Yee's Discount Liquor | 2, 2 `xx xx` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | Require TEMPERATE |
| ![Abandoned Warehouse preview](images/environmental/ts/city09.png) | `CITY09` | Abandoned Warehouse | 2, 2 `xx xx` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | Require TEMPERATE |
| ![Urban Storefront preview](images/environmental/ts/city10.png) | `CITY10` | Urban Storefront | 2, 2 `xx xx` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | Require TEMPERATE |
| ![Ambrose Lounge preview](images/environmental/ts/city11.png) | `CITY11` | Ambrose Lounge | 2, 2 `xx xx` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | Require TEMPERATE |
| ![Bostic Tower preview](images/environmental/ts/city12.png) | `CITY12` | Bostic Tower | 2, 2 `xX xx` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | Require TEMPERATE |
| ![Hewitt Hair Salon preview](images/environmental/ts/city13.png) | `CITY13` | Hewitt Hair Salon | 2, 2 `xX Xx` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | Require TEMPERATE |
| ![Business Offices preview](images/environmental/ts/city14.png) | `CITY14` | Business Offices | 1, 1 `x` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | Require TEMPERATE |
| ![2nd National Bank preview](images/environmental/ts/city15.png) | `CITY15` | 2nd National Bank | 4, 2 `xxxX xxxX` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | Require TEMPERATE |
| ![Highrise Hotel preview](images/environmental/ts/city16.png) | `CITY16` | Highrise Hotel | 4, 2 `xxxx xxxx` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | Require TEMPERATE |
| ![The Projects preview](images/environmental/ts/city17.png) | `CITY17` | The Projects | 4, 3 `XxxX xxxx xxxX` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | Require TEMPERATE |
| ![Archer Asylum preview](images/environmental/ts/city18.png) | `CITY18` | Archer Asylum | 3, 5 `xxx xxx xxx xxx xxX` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | Require TEMPERATE |
| ![Fill'er Up-Pump'N'Go preview](images/environmental/ts/city19.png) | `CITY19` | Fill'er Up-Pump'N'Go | 2, 2 `xx xX` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | Require TEMPERATE |
| ![Gas Pump preview](images/environmental/ts/city20.png) | `CITY20` | Gas Pump | 1, 1 `x` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | Require TEMPERATE |
| ![Gas Station Sign preview](images/environmental/ts/city21.png) | `CITY21` | Gas Station Sign | 1, 1 `x` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | Require TEMPERATE |
| ![Church preview](images/environmental/ts/city22.png) | `CITY22` | Church | 2, 2 `xx xx` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | Require TEMPERATE |
| ![Hydroelectric Dam preview](images/environmental/ts/ctdam.png) | `CTDAM` | Hydroelectric Dam | 2, 5 `xx xx xx xx xx` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, ProvidesPrerequisite, Demolishable | Exclude SNOW |
| ![Vega's Pyramid preview](images/environmental/ts/ctvega.png) | `CTVEGA` | Vega's Pyramid | 4, 4 `xxxx xxxx xxxx xxxx` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | Exclude SNOW |
| ![GDI Kodiak preview](images/environmental/ts/gakodk.png) | `GAKODK` | GDI Kodiak | 4, 2 `xxXX xxXX` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | — |
| ![Old Construction Yard preview](images/environmental/ts/gaoldcc1.png) | `GAOLDCC1` | Old Construction Yard | 2, 2 `xx xx` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | — |
| ![Old Temple preview](images/environmental/ts/gaoldcc2.png) | `GAOLDCC2` | Old Temple | 2, 2 `xx xX` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | — |
| ![Old Weapons Factory preview](images/environmental/ts/gaoldcc3.png) | `GAOLDCC3` | Old Weapons Factory | 2, 2 `xx xx` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | — |
| ![Old Refinery preview](images/environmental/ts/gaoldcc4.png) | `GAOLDCC4` | Old Refinery | 2, 2 `xx xx` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | — |
| ![Old Advanced Power Plant preview](images/environmental/ts/gaoldcc5.png) | `GAOLDCC5` | Old Advanced Power Plant | 2, 2 `xx xx` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | — |
| ![Old Silos preview](images/environmental/ts/gaoldcc6.png) | `GAOLDCC6` | Old Silos | 2, 2 `xX Xx` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | — |
| ![Nod Montauk preview](images/environmental/ts/namntk.png) | `NAMNTK` | Nod Montauk | 1, 3 `x x x` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | — |
| ![Nod Pyramid preview](images/environmental/ts/ntpyra.png) | `NTPYRA` | Nod Pyramid | 4, 4 `xxxx xxxx xxxx xxxx` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | — |
| ![Scrin Ship preview](images/environmental/ts/ufo.png) | `UFO` | Scrin Ship | 6, 4 `xxxxxx xxxxxx xxxxxx xxxxxx` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | Require TEMPERATE |

### Walls and Fences (8)
| Preview | Actor | Name/Tooltip | Size | Key Traits | Notes |
| :---: | :--- | :--- | :--- | :--- | :--- |
| ![Sandbags preview](images/environmental/ts/gasand.png) | `GASAND` | Sandbags | 1,1 `x` | Crushable, Demolishable | — |
| ![Concrete Wall preview](images/environmental/ts/gawall.png) | `GAWALL` | Concrete Wall | 1,1 `x` | Crushable, Demolishable | — |
| ![GDI Gate preview](images/environmental/ts/gagate_a.png) | `GAGATE_A` | GDI Gate | 3,1 `xxx` | FireWarheadsOnDeath, InstantlyRepairable, Demolishable | — |
| ![GDI Gate preview](images/environmental/ts/gagate_b.png) | `GAGATE_B` | GDI Gate | 1,3 `x x x` | FireWarheadsOnDeath, InstantlyRepairable, Demolishable | — |
| ![Concrete Wall preview](images/environmental/ts/nawall.png) | `NAWALL` | Concrete Wall | 1,1 `x` | Crushable, Demolishable | — |
| ![Nod Gate preview](images/environmental/ts/nagate_a.png) | `NAGATE_A` | Nod Gate | 3,1 `xxx` | FireWarheadsOnDeath, InstantlyRepairable, Demolishable | — |
| ![Nod Gate preview](images/environmental/ts/nagate_b.png) | `NAGATE_B` | Nod Gate | 1,3 `x x x` | FireWarheadsOnDeath, InstantlyRepairable, Demolishable | — |
| ![Laser Fence preview](images/environmental/ts/nafnce.png) | `NAFNCE` | Laser Fence | — | FireWarheadsOnDeath, Demolishable | — |

### Bridges (13)
| Preview | Actor | Name/Tooltip | Size | Key Traits | Notes |
| :---: | :--- | :--- | :--- | :--- | :--- |
| ![Bridge repair hut preview](images/environmental/ts/cabhut.png) | `CABHUT` | Bridge repair hut | 1, 1 `x` | InstantlyRepairable | — |
| ![Bridge preview](images/environmental/ts/lobrdg_a.png) | `LOBRDG_A` | Bridge | 3, 1 `___` | SpawnActorOnDeath | — |
| ![Bridge preview](images/environmental/ts/lobrdg_a_d.png) | `LOBRDG_A_D` | Bridge | 3, 1 `___` | SpawnActorOnDeath | — |
| ![Bridge preview](images/environmental/ts/lobrdg_b.png) | `LOBRDG_B` | Bridge | 1, 3 `_ _ _` | SpawnActorOnDeath | — |
| ![Bridge preview](images/environmental/ts/lobrdg_b_d.png) | `LOBRDG_B_D` | Bridge | 1, 3 `_ _ _` | SpawnActorOnDeath | — |
| ![Bridge preview](images/environmental/ts/lobrdg_r_se.png) | `LOBRDG_R_SE` | Bridge | 1, 3 `_ _ _` | — | — |
| ![Bridge preview](images/environmental/ts/lobrdg_r_nw.png) | `LOBRDG_R_NW` | Bridge | 1, 3 `_ _ _` | — | — |
| ![Bridge preview](images/environmental/ts/lobrdg_r_ne.png) | `LOBRDG_R_NE` | Bridge | 3, 1 `___` | — | — |
| ![Bridge preview](images/environmental/ts/lobrdg_r_sw.png) | `LOBRDG_R_SW` | Bridge | 3, 1 `___` | — | — |
| ![Bridge preview](images/environmental/ts/bridge1.png) | `BRIDGE1` | Bridge | — | — | — |
| ![Bridge preview](images/environmental/ts/bridge2.png) | `BRIDGE2` | Bridge | — | — | — |
| ![Bridge preview](images/environmental/ts/railbrdg1.png) | `RAILBRDG1` | Bridge | — | — | — |
| ![Bridge preview](images/environmental/ts/railbrdg2.png) | `RAILBRDG2` | Bridge | — | — | — |

### Resource Spawns (6)
| Preview | Actor | Name/Tooltip | Size | Key Traits | Notes |
| :---: | :--- | :--- | :--- | :--- | :--- |
| ![Blossom Tree preview](images/environmental/ts/tibtre01.png) | `TIBTRE01` | Blossom Tree | 1,1 `x` | SeedsResource | — |
| ![Blossom Tree preview](images/environmental/ts/tibtre02.png) | `TIBTRE02` | Blossom Tree | 1,1 `x` | SeedsResource | — |
| ![Blossom Tree preview](images/environmental/ts/tibtre03.png) | `TIBTRE03` | Blossom Tree | 1,1 `x` | SeedsResource | — |
| ![Large Blue Tiberium Crystal preview](images/environmental/ts/bigblue.png) | `BIGBLUE` | Large Blue Tiberium Crystal | 1,1 `x` | SeedsResource | — |
| ![Large Blue Tiberium Crystal preview](images/environmental/ts/bigblue3.png) | `BIGBLUE3` | Large Blue Tiberium Crystal | 1,1 `x` | SeedsResource | — |
| ![Veinhole preview](images/environmental/ts/veinhole.png) | `VEINHOLE` | Veinhole | 3, 3 `xxx xxx xxx` | — | — |

### Civilians (4)
| Preview | Actor | Name/Tooltip | Size | Key Traits | Notes |
| :---: | :--- | :--- | :--- | :--- | :--- |
| ![Civilian preview](images/environmental/ts/civ1.png) | `CIV1` | Civilian | — | SpawnActorOnDeath, RevealsShroud, Crushable | — |
| ![Civilian preview](images/environmental/ts/civ2.png) | `CIV2` | Civilian | — | SpawnActorOnDeath, RevealsShroud, Crushable | — |
| ![Civilian preview](images/environmental/ts/civ3.png) | `CIV3` | Civilian | — | SpawnActorOnDeath, RevealsShroud, Crushable | — |
| ![Civilian preview](images/environmental/ts/ctech.png) | `CTECH` | Civilian | — | SpawnActorOnDeath, RevealsShroud, Crushable | — |

### Critters and Wildlife (4)
| Preview | Actor | Name/Tooltip | Size | Key Traits | Notes |
| :---: | :--- | :--- | :--- | :--- | :--- |
| ![Tiberian Fiend preview](images/environmental/ts/doggie.png) | `DOGGIE` | Tiberian Fiend | — | SpawnActorOnDeath, RevealsShroud, Crushable | — |
| ![Baby Visceroid preview](images/environmental/ts/visc_sml.png) | `VISC_SML` | Baby Visceroid | — | Crushable | — |
| ![Adult Visceroid preview](images/environmental/ts/visc_lrg.png) | `VISC_LRG` | Adult Visceroid | — | RevealsShroud | — |
| ![Tiberium Floater preview](images/environmental/ts/jfish.png) | `JFISH` | Tiberium Floater | — | RevealsShroud | — |

### Railway (19)
| Preview | Actor | Name/Tooltip | Size | Key Traits | Notes |
| :---: | :--- | :--- | :--- | :--- | :--- |
| ![Train Locomotive preview](images/environmental/ts/locomotive.png) | `LOCOMOTIVE` | Train Locomotive | — | FireWarheadsOnDeath, RevealsShroud | — |
| ![Passenger Car preview](images/environmental/ts/traincar.png) | `TRAINCAR` | Passenger Car | — | FireWarheadsOnDeath, RevealsShroud | — |
| ![Cargo Car preview](images/environmental/ts/cargocar.png) | `CARGOCAR` | Cargo Car | — | FireWarheadsOnDeath, RevealsShroud | — |
| ![Railway preview](images/environmental/ts/tracks01.png) | `TRACKS01` | Railway | — | — | — |
| ![Railway preview](images/environmental/ts/tracks02.png) | `TRACKS02` | Railway | — | — | — |
| ![Railway preview](images/environmental/ts/tracks03.png) | `TRACKS03` | Railway | — | — | — |
| ![Railway preview](images/environmental/ts/tracks04.png) | `TRACKS04` | Railway | — | — | — |
| ![Railway preview](images/environmental/ts/tracks05.png) | `TRACKS05` | Railway | — | — | — |
| ![Railway preview](images/environmental/ts/tracks06.png) | `TRACKS06` | Railway | — | — | — |
| ![Railway preview](images/environmental/ts/tracks07.png) | `TRACKS07` | Railway | — | — | — |
| ![Railway preview](images/environmental/ts/tracks08.png) | `TRACKS08` | Railway | — | — | — |
| ![Railway preview](images/environmental/ts/tracks09.png) | `TRACKS09` | Railway | — | — | — |
| ![Railway preview](images/environmental/ts/tracks10.png) | `TRACKS10` | Railway | — | — | — |
| ![Railway preview](images/environmental/ts/tracks11.png) | `TRACKS11` | Railway | — | — | — |
| ![Railway preview](images/environmental/ts/tracks12.png) | `TRACKS12` | Railway | — | — | — |
| ![Railway preview](images/environmental/ts/tracks13.png) | `TRACKS13` | Railway | — | — | — |
| ![Railway preview](images/environmental/ts/tracks14.png) | `TRACKS14` | Railway | — | — | — |
| ![Railway preview](images/environmental/ts/tracks15.png) | `TRACKS15` | Railway | — | — | — |
| ![Railway preview](images/environmental/ts/tracks16.png) | `TRACKS16` | Railway | — | — | — |

### Billboards (16)
| Preview | Actor | Name/Tooltip | Size | Key Traits | Notes |
| :---: | :--- | :--- | :--- | :--- | :--- |
| ![Eat at Rade's Roadhouse preview](images/environmental/ts/bboard01.png) | `BBOARD01` | Eat at Rade's Roadhouse | 1, 1 `x` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | — |
| ![Drink YEO-CA Cola! preview](images/environmental/ts/bboard02.png) | `BBOARD02` | Drink YEO-CA Cola! | 1, 1 `x` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | — |
| ![Hamburgers $.99 preview](images/environmental/ts/bboard03.png) | `BBOARD03` | Hamburgers $.99 | 1, 1 `x` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | — |
| ![Visit Scenic Las Vegas preview](images/environmental/ts/bboard04.png) | `BBOARD04` | Visit Scenic Las Vegas | 1, 1 `x` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | — |
| ![Rooms $29 a nite preview](images/environmental/ts/bboard05.png) | `BBOARD05` | Rooms $29 a nite | 1, 1 `x` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | — |
| ![Kaspm's Tiberium Warhouse preview](images/environmental/ts/bboard06.png) | `BBOARD06` | Kaspm's Tiberium Warhouse | 1, 2 `x x` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | — |
| ![Alkaline's Battery Superstore preview](images/environmental/ts/bboard07.png) | `BBOARD07` | Alkaline's Battery Superstore | 1, 2 `x x` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | — |
| ![Alex-Gator's Petshop just ahead! preview](images/environmental/ts/bboard08.png) | `BBOARD08` | Alex-Gator's Petshop just ahead! | 1, 2 `x x` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | — |
| ![TacticX Games rock! preview](images/environmental/ts/bboard09.png) | `BBOARD09` | TacticX Games rock! | 1, 1 `x` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | — |
| ![WW Surf and Turf hits the spot! preview](images/environmental/ts/bboard10.png) | `BBOARD10` | WW Surf and Turf hits the spot! | 1, 1 `x` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | — |
| ![Only 11 miles to Zydeko's cafe! preview](images/environmental/ts/bboard11.png) | `BBOARD11` | Only 11 miles to Zydeko's cafe! | 1, 1 `x` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | — |
| ![No escape from Archer's Asylum! preview](images/environmental/ts/bboard12.png) | `BBOARD12` | No escape from Archer's Asylum! | 1, 1 `x` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | — |
| ![Stop in at Hewitt's hair salon preview](images/environmental/ts/bboard13.png) | `BBOARD13` | Stop in at Hewitt's hair salon | 1, 1 `x` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | — |
| ![Billy Bob's Harvester School preview](images/environmental/ts/bboard14.png) | `BBOARD14` | Billy Bob's Harvester School | 2, 1 `xx` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | — |
| ![Pannullo's hacienda es bueno preview](images/environmental/ts/bboard15.png) | `BBOARD15` | Pannullo's hacienda es bueno | 2, 1 `xx` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | — |
| ![Join GDI: We save lives. preview](images/environmental/ts/bboard16.png) | `BBOARD16` | Join GDI: We save lives. | 2, 1 `xx` | FireWarheadsOnDeath, InstantlyRepairable, RevealsShroud, Demolishable | — |

### Tunnels (4)
| Preview | Actor | Name/Tooltip | Size | Key Traits | Notes |
| :---: | :--- | :--- | :--- | :--- | :--- |
| ![— preview](images/environmental/ts/tuntop01.png) | `TUNTOP01` | — | 3, 3 `___ ___ ___` | — | — |
| ![— preview](images/environmental/ts/tuntop02.png) | `TUNTOP02` | — | 3, 3 `___ ___ ___` | — | — |
| ![— preview](images/environmental/ts/tuntop03.png) | `TUNTOP03` | — | 3, 3 `___ ___ ___` | — | — |
| ![— preview](images/environmental/ts/tuntop04.png) | `TUNTOP04` | — | 3, 3 `___ ___ ___` | — | — |

### Decorative Props (18)
| Preview | Actor | Name/Tooltip | Size | Key Traits | Notes |
| :---: | :--- | :--- | :--- | :--- | :--- |
| ![Crash Site preview](images/environmental/ts/cacrsh01.png) | `CACRSH01` | Crash Site | 1, 1 `x` | — | — |
| ![Crash Site preview](images/environmental/ts/cacrsh02.png) | `CACRSH02` | Crash Site | 1, 1 `x` | — | — |
| ![Crash Site preview](images/environmental/ts/cacrsh03.png) | `CACRSH03` | Crash Site | 1, 1 `x` | — | — |
| ![Crash Site preview](images/environmental/ts/cacrsh04.png) | `CACRSH04` | Crash Site | 1, 1 `x` | — | — |
| ![Crash Site preview](images/environmental/ts/cacrsh05.png) | `CACRSH05` | Crash Site | 1, 1 `x` | — | — |
| ![Box preview](images/environmental/ts/crat01.png) | `CRAT01` | Box | 1, 1 `x` | — | — |
| ![Box preview](images/environmental/ts/crat02.png) | `CRAT02` | Box | 1, 1 `x` | — | — |
| ![Box preview](images/environmental/ts/crat03.png) | `CRAT03` | Box | 1, 1 `x` | — | — |
| ![Box preview](images/environmental/ts/crat04.png) | `CRAT04` | Box | 1, 1 `x` | — | — |
| ![Box preview](images/environmental/ts/crat0a.png) | `CRAT0A` | Box | 1, 1 `x` | — | — |
| ![Box preview](images/environmental/ts/crat0b.png) | `CRAT0B` | Box | 1, 1 `x` | — | — |
| ![Box preview](images/environmental/ts/crat0c.png) | `CRAT0C` | Box | 1, 1 `x` | — | — |
| ![Drum preview](images/environmental/ts/drum01.png) | `DRUM01` | Drum | 1, 1 `x` | — | — |
| ![Drum preview](images/environmental/ts/drum02.png) | `DRUM02` | Drum | 1, 1 `x` | — | — |
| ![Pallet preview](images/environmental/ts/palet01.png) | `PALET01` | Pallet | 1, 1 `x` | — | — |
| ![Pallet preview](images/environmental/ts/palet02.png) | `PALET02` | Pallet | 1, 1 `x` | — | — |
| ![Pallet preview](images/environmental/ts/palet03.png) | `PALET03` | Pallet | 1, 1 `x` | — | — |
| ![Pallet preview](images/environmental/ts/palet04.png) | `PALET04` | Pallet | 1, 1 `x` | — | — |

### Other Environmental Actors (10)
| Preview | Actor | Name/Tooltip | Size | Key Traits | Notes |
| :---: | :--- | :--- | :--- | :--- | :--- |
| ![Civilian Hospital preview](images/environmental/ts/cahosp.png) | `CAHOSP` | Civilian Hospital | 3, 4 `XxX xxx xxx xxx` | FireWarheadsOnDeath, Capturable, InstantlyRepairable, Demolishable | — |
| ![Light Tower preview](images/environmental/ts/gaspot.png) | `GASPOT` | Light Tower | 1, 1 `x` | FireWarheadsOnDeath, Capturable, InstantlyRepairable, RevealsShroud, GivesBuildableArea, Demolishable | — |
| ![Light Post preview](images/environmental/ts/galite.png) | `GALITE` | Light Post | 1,1 `x` | FireWarheadsOnDeath, Capturable, InstantlyRepairable, RevealsShroud, GivesBuildableArea, Demolishable | — |
| ![Red Light Post preview](images/environmental/ts/redlamp.png) | `REDLAMP` | Red Light Post | 1,1 `x` | FireWarheadsOnDeath, Capturable, InstantlyRepairable, RevealsShroud, GivesBuildableArea, Demolishable | — |
| ![Negative Red Light Post preview](images/environmental/ts/negred.png) | `NEGRED` | Negative Red Light Post | 1,1 `x` | FireWarheadsOnDeath, Capturable, InstantlyRepairable, RevealsShroud, GivesBuildableArea, Demolishable | — |
| ![Green Light Post preview](images/environmental/ts/grenlamp.png) | `GRENLAMP` | Green Light Post | 1,1 `x` | FireWarheadsOnDeath, Capturable, InstantlyRepairable, RevealsShroud, GivesBuildableArea, Demolishable | — |
| ![Blue Light Post preview](images/environmental/ts/bluelamp.png) | `BLUELAMP` | Blue Light Post | 1,1 `x` | FireWarheadsOnDeath, Capturable, InstantlyRepairable, RevealsShroud, GivesBuildableArea, Demolishable | — |
| ![Yellow Light Post preview](images/environmental/ts/yelwlamp.png) | `YELWLAMP` | Yellow Light Post | 1,1 `x` | FireWarheadsOnDeath, Capturable, InstantlyRepairable, RevealsShroud, GivesBuildableArea, Demolishable | — |
| ![Purple Light Post preview](images/environmental/ts/purplamp.png) | `PURPLAMP` | Purple Light Post | 1,1 `x` | FireWarheadsOnDeath, Capturable, InstantlyRepairable, RevealsShroud, GivesBuildableArea, Demolishable | — |
| ![Light Post preview](images/environmental/ts/tstlamp.png) | `TSTLAMP` | Light Post | 1,1 `x` | FireWarheadsOnDeath, Capturable, InstantlyRepairable, RevealsShroud, GivesBuildableArea, Demolishable | — |

## Summary

This appendix is a single-source, auto-generated reference to the environmental actors in OpenRA's four bundled mods. It pairs each object's internal codename with its editor category, footprint, key traits, and a preview slot, all drawn from the engine's own rules so the reference stays in sync with the pinned source.

## What to read next

- [Part 2.4 — Rules and Weapons](../chapters/Part_02_Chapter_04_Rules_Weapons.md) — how the actor and weapon YAML in these tables is defined.
- [Appendix J — Terrain Tile Reference](Appendix_J_Terrain_Tiles.md) — the terrain tiles these objects sit on.
- [Part 10.3 — Porting and Modding](../chapters/Part_10_Chapter_03_Port_And_Modding.md) — creating your own environmental actor from scratch.
