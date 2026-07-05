# Appendix I — Actor Reference

This appendix consolidates, in one place, every **buildable actor** in the four mods that ship with OpenRA — *Red Alert*, *Tiberian Dawn*, *Dune 2000*, and *Tiberian Sun* — with its cameo, codename, faction, role, and core combat statistics. The goal is the thing that exists nowhere else: the sprite, the internal codename you write in YAML, and the numbers that define the unit, all next to each other, so a new modder can see at a glance what a unit *is* and what rules drive it.

This is engine-data reference, not balance commentary. Every value here is read directly from the mod's own rules YAML, so it always reflects the pinned engine rather than a hand-maintained copy that can drift.

> **Generated, not hand-written.** This appendix is produced by `build files/generate_actor_reference.py`, which parses each mod's `rules/*.yaml` (resolving `Inherits:` chains) and `fluent/rules.ftl` (for display names).

## How to read these tables

Each mod is split into **Infantry, Vehicles, Aircraft, Naval, and Buildings**. Columns:

- **Preview** — the build-palette cameo and the in-world battlefield sprite stacked in one cell. The cameo is the icon shown in the production sidebar; the unit is the idle/stand frame rendered with the same palette the engine uses in-game. (See the note on the images below.)
- **Code** — the actor's internal name; this is the key you use in `rules/*.yaml`, map actor definitions, and Lua (`Actor.Create("e1", ...)`).
- **Name** — the in-game display name, resolved from the mod's Fluent (`.ftl`) strings.
- **Faction** — derived from the build `Prerequisites`/`Queue` (e.g. `~vehicles.soviet`). A dash means shared or not faction-restricted.
- **Cost** — `Valued.Cost` (credits).
- **HP** — `Health.HP`, in raw engine health units (OpenRA's RA mod uses a ~100x scale, so `60000` is the classic "600").
- **Armor** — `Armor.Type` (matched against weapon `Versus` tables).
- **Speed** — `Mobile.Speed` (ground) or `Aircraft.Speed` (air), in engine units.
- **Sight** — `RevealsShroud.Range`, in cells (`WDist`, e.g. `6c0` = 6 cells).
- **Weapon(s)** — the weapon name(s) from each `Armament`; look these up in the mod's `weapons/*.yaml`.
- **Notable traits** — a curated set of standout abilities present on the actor (cloak, capture, deploy, support powers, self-heal, etc.).

> **About the images.** Each actor shows a **Preview** cell containing both the build-palette cameo (sidebar/construction-menu icon) and the in-world battlefield sprite. Both are rendered from the original game art, which lives only where you have installed the OpenRA game content — it is not in the engine source, so it cannot be bundled. Until the extraction script (below) is run on a machine with the content installed, the cell shows two labelled faction-tinted **placeholders** (the cameo box is grey; the unit box is blue-grey). A handful of actors have no art for one of the two slots (e.g. fake structures, or units with no separate sidebar icon) and keep its placeholder there. The manual is fully laid out and link-valid in the meantime.

> **A note on art.** OpenRA's own assets are openly licensed; the classic Westwood/EA unit art is distributed as freeware and remains its owners' property. Showing cameos in a free, non-commercial, educational reference is a fair-use use, not an open-license grant. Attribute the art to its owners and include a "not endorsed by or affiliated with EA" notice when publishing.

## Red Alert

*90 buildable actors.*

### Red Alert — Infantry (15)

| Preview | Code | Name | Faction | Cost | HP | Armor | Speed | Sight | Weapon(s) | Notable traits |
| :---: | :--- | :--- | :--- | ---: | ---: | :--- | ---: | ---: | :--- | :--- |
| ![Tanya cameo](images/actors/ra/e7.png) ![Tanya unit](images/actors/ra/e7_unit.png) | `E7` | Tanya | Allied | 1800 | 10000 | None | 68 | 6c0 | Colt45, Colt45 | Demolition, DetectCloaked, Parachutable, ProducibleWithLevel |
| ![Giant Ant cameo](images/actors/ra/ant.png) ![Giant Ant unit](images/actors/ra/ant_unit.png) | `Ant` | Giant Ant | — | 300 | 75000 | None | 92 | 4c0 | mandible | DetectCloaked, Parachutable |
| ![Zombie cameo](images/actors/ra/zombie.png) ![Zombie unit](images/actors/ra/zombie_unit.png) | `Zombie` | Zombie | — | 100 | 25000 | None | 39 | 4c0 | claw | DetectCloaked, Parachutable |
| ![Engineer cameo](images/actors/ra/e6.png) ![Engineer unit](images/actors/ra/e6_unit.png) | `E6` | Engineer | — | 400 | 2500 | None | 54 | 4c0 | — | Captures, DetectCloaked, Parachutable |
| ![Thief cameo](images/actors/ra/thf.png) ![Thief unit](images/actors/ra/thf_unit.png) | `THF` | Thief | Soviet | 500 | 8000 | None | 72 | 5c0 | — | Captures, Cloak, DetectCloaked, Parachutable |
| ![Attack Dog cameo](images/actors/ra/dog.png) ![Attack Dog unit](images/actors/ra/dog_unit.png) | `DOG` | Attack Dog | Soviet | 200 | 1800 | None | 100 | 5c512 | DogJaw | DetectCloaked, Parachutable |
| ![Rifle Infantry cameo](images/actors/ra/e1.png) ![Rifle Infantry unit](images/actors/ra/e1_unit.png) | `E1` | Rifle Infantry | — | 100 | 5000 | None | 54 | 4c0 | M1Carbine, Vulcan | DetectCloaked, Parachutable, ProducibleWithLevel |
| ![Grenadier cameo](images/actors/ra/e2.png) ![Grenadier unit](images/actors/ra/e2_unit.png) | `E2` | Grenadier | Soviet | 150 | 5000 | None | 68 | 4c0 | Grenade, Grenade | DetectCloaked, Parachutable, ProducibleWithLevel |
| ![Rocket Soldier cameo](images/actors/ra/e3.png) ![Rocket Soldier unit](images/actors/ra/e3_unit.png) | `E3` | Rocket Soldier | — | 300 | 4500 | None | 54 | 4c0 | RedEye, Dragon, RedEye, Dragon | DetectCloaked, Parachutable, ProducibleWithLevel |
| ![Flame Infantry cameo](images/actors/ra/e4.png) ![Flame Infantry unit](images/actors/ra/e4_unit.png) | `E4` | Flame Infantry | Soviet | 300 | 4000 | None | 54 | 4c0 | Flamer, Flamer | DetectCloaked, Parachutable, ProducibleWithLevel |
| ![Medic cameo](images/actors/ra/medi.png) ![Medic unit](images/actors/ra/medi_unit.png) | `MEDI` | Medic | Allied | 200 | 6000 | None | 49 | 3c0 | Heal | DetectCloaked, Parachutable |
| ![Mechanic cameo](images/actors/ra/mech.png) ![Mechanic unit](images/actors/ra/mech_unit.png) | `MECH` | Mechanic | Allied | 500 | 8000 | None | 49 | 3c0 | Repair | Captures, DetectCloaked, Parachutable |
| ![Shock Trooper cameo](images/actors/ra/shok.png) ![Shock Trooper unit](images/actors/ra/shok_unit.png) | `SHOK` | Shock Trooper | Soviet | 350 | 5000 | None | 54 | 5c0 | PortaTesla, PortaTesla | DetectCloaked, Parachutable, ProducibleWithLevel |
| ![Fire Ant cameo](images/actors/ra/fireant.png) ![Fire Ant unit](images/actors/ra/fireant_unit.png) | `FireAnt` | Fire Ant | — | 300 | 7500 | Heavy | 68 | 4c0 | AntFireball | DetectCloaked, Parachutable |
| ![Scout Ant cameo](images/actors/ra/scoutant.png) ![Scout Ant unit](images/actors/ra/scoutant_unit.png) | `ScoutAnt` | Scout Ant | — | 300 | 8500 | Light | 92 | 4c0 | mandible | DetectCloaked, Parachutable |

### Red Alert — Vehicle (21)

| Preview | Code | Name | Faction | Cost | HP | Armor | Speed | Sight | Weapon(s) | Notable traits |
| :---: | :--- | :--- | :--- | ---: | ---: | :--- | ---: | ---: | :--- | :--- |
| ![Ore Truck cameo](images/actors/ra/harv.png) ![Ore Truck unit](images/actors/ra/harv_unit.png) | `HARV` | Ore Truck | — | 1100 | 60000 | Heavy | 72 | 4c0 | — | Chronoshiftable, Parachutable, Repairable |
| ![Supply Truck cameo](images/actors/ra/truk.png) ![Supply Truck unit](images/actors/ra/truk_unit.png) | `TRUK` | Supply Truck | — | 500 | 11000 | Light | 113 | 4c0 | — | Chronoshiftable, Parachutable, Repairable |
| ![Transport cameo](images/actors/ra/lst.png) ![Transport unit](images/actors/ra/lst_unit.png) | `LST` | Transport | — | 500 | 40000 | Heavy | 115 | 6c0 | — | — |
| ![V2 Rocket Launcher cameo](images/actors/ra/v2rl.png) ![V2 Rocket Launcher unit](images/actors/ra/v2rl_unit.png) | `V2RL` | V2 Rocket Launcher | Soviet | 900 | 20000 | Light | 72 | 5c0 | SCUD | Chronoshiftable, Parachutable, ProducibleWithLevel, Repairable |
| ![Light Tank cameo](images/actors/ra/1tnk.png) ![Light Tank unit](images/actors/ra/1tnk_unit.png) | `1TNK` | Light Tank | Allied | 700 | 23000 | Heavy | 113 | 5c0 | 25mm | Chronoshiftable, Parachutable, ProducibleWithLevel, Repairable |
| ![Medium Tank cameo](images/actors/ra/2tnk.png) ![Medium Tank unit](images/actors/ra/2tnk_unit.png) | `2TNK` | Medium Tank | Allied | 850 | 46000 | Heavy | 72 | 6c0 | 90mm | Chronoshiftable, Parachutable, ProducibleWithLevel, Repairable |
| ![Heavy Tank cameo](images/actors/ra/3tnk.png) ![Heavy Tank unit](images/actors/ra/3tnk_unit.png) | `3TNK` | Heavy Tank | Soviet | 1150 | 60000 | Heavy | 64 | 6c0 | 105mm | Chronoshiftable, Parachutable, ProducibleWithLevel, Repairable |
| ![Mammoth Tank cameo](images/actors/ra/4tnk.png) ![Mammoth Tank unit](images/actors/ra/4tnk_unit.png) | `4TNK` | Mammoth Tank | Soviet | 2000 | 90000 | Heavy | 43 | 6c0 | 120mm, MammothTusk | Chronoshiftable, Parachutable, ProducibleWithLevel, Repairable |
| ![Artillery cameo](images/actors/ra/arty.png) ![Artillery unit](images/actors/ra/arty_unit.png) | `ARTY` | Artillery | Allied | 850 | 10000 | Light | 72 | 5c0 | 155mm | Chronoshiftable, Parachutable, ProducibleWithLevel, Repairable |
| ![Mobile Construction Vehicle cameo](images/actors/ra/mcv.png) ![Mobile Construction Vehicle unit](images/actors/ra/mcv_unit.png) | `MCV` | Mobile Construction Vehicle | — | 2000 | 60000 | Light | 60 | 4c0 | — | Chronoshiftable, Parachutable, Repairable, Transforms |
| ![Ranger cameo](images/actors/ra/jeep.png) ![Ranger unit](images/actors/ra/jeep_unit.png) | `JEEP` | Ranger | Allied | 500 | 15000 | Light | 164 | 7c0 | M60mg | Chronoshiftable, Parachutable, ProducibleWithLevel, Repairable |
| ![Armored Personnel Carrier cameo](images/actors/ra/apc.png) ![Armored Personnel Carrier unit](images/actors/ra/apc_unit.png) | `APC` | Armored Personnel Carrier | Soviet | 850 | 35000 | Heavy | 128 | 5c0 | M60mg | Chronoshiftable, Parachutable, ProducibleWithLevel, Repairable |
| ![Minelayer cameo](images/actors/ra/mnly.png) ![Minelayer unit](images/actors/ra/mnly_unit.png) | `MNLY` | Minelayer | — | 800 | 30000 | Heavy | 113 | 5c0 | — | Chronoshiftable, DetectCloaked, Minelayer, Parachutable, Repairable |
| ![Mobile Gap Generator cameo](images/actors/ra/mgg.png) ![Mobile Gap Generator unit](images/actors/ra/mgg_unit.png) | `MGG` | Mobile Gap Generator | Allied | 1000 | 22000 | Heavy | 72 | 6c0 | — | Chronoshiftable, Parachutable, Repairable |
| ![Mobile Radar Jammer cameo](images/actors/ra/mrj.png) ![Mobile Radar Jammer unit](images/actors/ra/mrj_unit.png) | `MRJ` | Mobile Radar Jammer | Allied | 1000 | 22000 | Heavy | 68 | 7c0 | — | Chronoshiftable, Parachutable, Repairable |
| ![Tesla Tank cameo](images/actors/ra/ttnk.png) ![Tesla Tank unit](images/actors/ra/ttnk_unit.png) | `TTNK` | Tesla Tank | Soviet | 1350 | 40000 | Light | 92 | 7c0 | TTankZap | Chronoshiftable, Parachutable, ProducibleWithLevel, Repairable |
| ![Mobile Flak cameo](images/actors/ra/ftrk.png) ![Mobile Flak unit](images/actors/ra/ftrk_unit.png) | `FTRK` | Mobile Flak | Soviet | 600 | 15000 | Light | 113 | 6c0 | FLAK-23-AA, FLAK-23-AG | Chronoshiftable, Parachutable, ProducibleWithLevel, Repairable |
| ![Demolition Truck cameo](images/actors/ra/dtrk.png) ![Demolition Truck unit](images/actors/ra/dtrk_unit.png) | `DTRK` | Demolition Truck | Soviet | 2500 | 2800 | Light | 67 | 4c0 | DemoTruckTargeting | Chronoshiftable, GrantConditionOnDeploy, Parachutable, Repairable |
| ![Chrono Tank cameo](images/actors/ra/ctnk.png) ![Chrono Tank unit](images/actors/ra/ctnk_unit.png) | `CTNK` | Chrono Tank | Allied | 1350 | 40000 | Light | 86 | 6c0 | APTusk | Chronoshiftable, Parachutable, ProducibleWithLevel, Repairable |
| ![MAD Tank cameo](images/actors/ra/qtnk.png) ![MAD Tank unit](images/actors/ra/qtnk_unit.png) | `QTNK` | MAD Tank | Soviet | 2000 | 90000 | Heavy | 46 | 6c0 | — | Chronoshiftable, Parachutable, Repairable |
| ![Phase Transport cameo](images/actors/ra/stnk.png) ![Phase Transport unit](images/actors/ra/stnk_unit.png) | `STNK` | Phase Transport | Allied | 1000 | 35000 | Light | 128 | 7c0 | APTusk.stnk | Chronoshiftable, Cloak, Parachutable, ProducibleWithLevel, Repairable |

### Red Alert — Aircraft (6)

| Preview | Code | Name | Faction | Cost | HP | Armor | Speed | Sight | Weapon(s) | Notable traits |
| :---: | :--- | :--- | :--- | ---: | ---: | :--- | ---: | ---: | :--- | :--- |
| ![MiG Attack Plane cameo](images/actors/ra/mig.png) ![MiG Attack Plane unit](images/actors/ra/mig_unit.png) | `MIG` | MiG Attack Plane | Soviet | 2000 | 8000 | Light | 223 | 13c0 | Maverick | ProducibleWithLevel, Repairable |
| ![Yak Attack Plane cameo](images/actors/ra/yak.png) ![Yak Attack Plane unit](images/actors/ra/yak_unit.png) | `YAK` | Yak Attack Plane | Soviet | 1350 | 6000 | Light | 178 | 11c0 | ChainGun.Yak | ProducibleWithLevel, Repairable |
| ![Chinook cameo](images/actors/ra/tran.png) ![Chinook unit](images/actors/ra/tran_unit.png) | `TRAN` | Chinook | Allied | 900 | 14000 | Light | 128 | 8c0 | — | Repairable |
| ![Longbow cameo](images/actors/ra/heli.png) ![Longbow unit](images/actors/ra/heli_unit.png) | `HELI` | Longbow | Allied | 2000 | 12000 | Light | 149 | 12c0 | HellfireAA, HellfireAG | ProducibleWithLevel, Repairable |
| ![Hind cameo](images/actors/ra/hind.png) ![Hind unit](images/actors/ra/hind_unit.png) | `HIND` | Hind | Allied | 1500 | 10000 | Light | 112 | 10c0 | ChainGun | ProducibleWithLevel, Repairable |
| ![Black Hawk cameo](images/actors/ra/mh60.png) ![Black Hawk unit](images/actors/ra/mh60_unit.png) | `MH60` | Black Hawk | Allied | 1500 | 10000 | Light | 112 | 10c0 | ChainGun | ProducibleWithLevel, Repairable |

### Red Alert — Naval (5)

| Preview | Code | Name | Faction | Cost | HP | Armor | Speed | Sight | Weapon(s) | Notable traits |
| :---: | :--- | :--- | :--- | ---: | ---: | :--- | ---: | ---: | :--- | :--- |
| ![Submarine cameo](images/actors/ra/ss.png) ![Submarine unit](images/actors/ra/ss_unit.png) | `SS` | Submarine | Soviet | 950 | 25000 | Light | 78 | 8c0 | TorpTube | Chronoshiftable, Cloak, DetectCloaked |
| ![Missile Submarine cameo](images/actors/ra/msub.png) ![Missile Submarine unit](images/actors/ra/msub_unit.png) | `MSUB` | Missile Submarine | Soviet | 2000 | 40000 | Light | 44 | 8c0 | SubMissile, SubMissileAA | Chronoshiftable, Cloak, DetectCloaked |
| ![Destroyer cameo](images/actors/ra/dd.png) ![Destroyer unit](images/actors/ra/dd_unit.png) | `DD` | Destroyer | Soviet | 1000 | 40000 | Heavy | 92 | 5c0 | Stinger, DepthCharge, StingerAA | Chronoshiftable, DetectCloaked |
| ![Cruiser cameo](images/actors/ra/ca.png) ![Cruiser unit](images/actors/ra/ca_unit.png) | `CA` | Cruiser | Soviet / Allied | 2400 | 80000 | Heavy | 44 | 7c0 | 8Inch, 8Inch | Chronoshiftable |
| ![Gunboat cameo](images/actors/ra/pt.png) ![Gunboat unit](images/actors/ra/pt_unit.png) | `PT` | Gunboat | Soviet | 500 | 20000 | Heavy | 142 | 8c0 | 2Inch, DepthCharge | Chronoshiftable, DetectCloaked |

### Red Alert — Building (43)

| Preview | Code | Name | Faction | Cost | HP | Armor | Speed | Sight | Weapon(s) | Notable traits |
| :---: | :--- | :--- | :--- | ---: | ---: | :--- | ---: | ---: | :--- | :--- |
| ![Sub Pen cameo](images/actors/ra/spen.png) ![Sub Pen unit](images/actors/ra/spen_unit.png) | `SPEN` | Sub Pen | Soviet | 800 | 100000 | Wood | — | 5c0 | — | DetectCloaked |
| ![Naval Yard cameo](images/actors/ra/syrd.png) ![Naval Yard unit](images/actors/ra/syrd_unit.png) | `SYRD` | Naval Yard | Allied | 1000 | 100000 | Wood | — | 5c0 | — | DetectCloaked |
| ![Service Depot cameo](images/actors/ra/fix.png) ![Service Depot unit](images/actors/ra/fix_unit.png) | `FIX` | Service Depot | — | 1200 | 80000 | Wood | — | 5c0 | — | — |
| ![Missile Silo cameo](images/actors/ra/mslo.png) ![Missile Silo unit](images/actors/ra/mslo_unit.png) | `MSLO` | Missile Silo | — | 2500 | 100000 | Wood | — | 6c0 | — | NukePower |
| ![Iron Curtain cameo](images/actors/ra/iron.png) ![Iron Curtain unit](images/actors/ra/iron_unit.png) | `IRON` | Iron Curtain | Soviet | 2000 | 100000 | Wood | — | 6c0 | — | — |
| ![Radar Dome cameo](images/actors/ra/dome.png) ![Radar Dome unit](images/actors/ra/dome_unit.png) | `DOME` | Radar Dome | — | 1500 | 100000 | Wood | — | 10c0 | — | ProvidesRadar |
| ![Allied Tech Center cameo](images/actors/ra/atek.png) ![Allied Tech Center unit](images/actors/ra/atek_unit.png) | `ATEK` | Allied Tech Center | Allied | 1500 | 60000 | Wood | — | 5c0 | — | — |
| ![War Factory cameo](images/actors/ra/weap.png) ![War Factory unit](images/actors/ra/weap_unit.png) | `WEAP` | War Factory | — | 2000 | 150000 | Wood | — | 5c0 | — | — |
| ![Ore Refinery cameo](images/actors/ra/proc.png) ![Ore Refinery unit](images/actors/ra/proc_unit.png) | `PROC` | Ore Refinery | — | 1400 | 90000 | Wood | — | 5c0 | — | — |
| ![Helipad cameo](images/actors/ra/hpad.png) ![Helipad unit](images/actors/ra/hpad_unit.png) | `HPAD` | Helipad | Allied | 500 | 80000 | Wood | — | 5c0 | — | — |
| ![Airfield cameo](images/actors/ra/afld.png) ![Airfield unit](images/actors/ra/afld_unit.png) | `AFLD` | Airfield | Soviet | 500 | 100000 | Wood | — | 5c0 | — | AirstrikePower, ParatroopersPower |
| ![Power Plant cameo](images/actors/ra/powr.png) ![Power Plant unit](images/actors/ra/powr_unit.png) | `POWR` | Power Plant | — | 300 | 40000 | Wood | — | 4c0 | — | — |
| ![Advanced Power Plant cameo](images/actors/ra/apwr.png) ![Advanced Power Plant unit](images/actors/ra/apwr_unit.png) | `APWR` | Advanced Power Plant | — | 500 | 70000 | Wood | — | 5c0 | — | — |
| ![Soviet Barracks cameo](images/actors/ra/barr.png) ![Soviet Barracks unit](images/actors/ra/barr_unit.png) | `BARR` | Soviet Barracks | Soviet | 500 | 60000 | Wood | — | 5c0 | — | — |
| ![Allied Barracks cameo](images/actors/ra/tent.png) ![Allied Barracks unit](images/actors/ra/tent_unit.png) | `TENT` | Allied Barracks | Allied | 500 | 60000 | Wood | — | 5c0 | — | — |
| ![Fake Power Plant cameo](images/actors/ra/fpwr.png) ![Fake Power Plant unit](images/actors/ra/fpwr_unit.png) | `FPWR` | Fake Power Plant | — | 30 | 40000 | Wood | — | 1c0 | — | — |
| ![Fake Allied Barracks cameo](images/actors/ra/tenf.png) ![Fake Allied Barracks unit](images/actors/ra/tenf_unit.png) | `TENF` | Fake Allied Barracks | — | 50 | 60000 | Wood | — | 1c0 | — | — |
| ![Fake Naval Yard cameo](images/actors/ra/syrf.png) ![Fake Naval Yard unit](images/actors/ra/syrf_unit.png) | `SYRF` | Fake Naval Yard | — | 100 | 100000 | Light | — | 1c0 | — | — |
| ![Fake Sub Pen cameo](images/actors/ra/spef.png) ![Fake Sub Pen unit](images/actors/ra/spef_unit.png) | `SPEF` | Fake Sub Pen | — | 80 | 100000 | Light | — | 1c0 | — | — |
| ![Fake War Factory cameo](images/actors/ra/weaf.png) ![Fake War Factory unit](images/actors/ra/weaf_unit.png) | `WEAF` | Fake War Factory | — | 200 | 150000 | Wood | — | 1c0 | — | — |
| ![Fake Radar Dome cameo](images/actors/ra/domf.png) ![Fake Radar Dome unit](images/actors/ra/domf_unit.png) | `DOMF` | Fake Radar Dome | — | 180 | 100000 | Wood | — | 1c0 | — | — |
| ![Fake Service Depot cameo](images/actors/ra/fixf.png) ![Fake Service Depot unit](images/actors/ra/fixf_unit.png) | `FIXF` | Fake Service Depot | — | 120 | 80000 | Wood | — | 1c0 | — | — |
| ![Fake Advanced Power Plant cameo](images/actors/ra/fapw.png) ![Fake Advanced Power Plant unit](images/actors/ra/fapw_unit.png) | `FAPW` | Fake Advanced Power Plant | — | 50 | 70000 | Wood | — | 1c0 | — | — |
| ![Fake Allied Tech Center cameo](images/actors/ra/atef.png) ![Fake Allied Tech Center unit](images/actors/ra/atef_unit.png) | `ATEF` | Fake Allied Tech Center | — | 150 | 40000 | Wood | — | 1c0 | — | — |
| ![Fake Chronosphere cameo](images/actors/ra/pdof.png) ![Fake Chronosphere unit](images/actors/ra/pdof_unit.png) | `PDOF` | Fake Chronosphere | — | 150 | 100000 | Wood | — | 1c0 | — | — |
| ![Fake Missile Silo cameo](images/actors/ra/mslf.png) ![Fake Missile Silo unit](images/actors/ra/mslf_unit.png) | `MSLF` | Fake Missile Silo | — | 250 | 100000 | Wood | — | 1c0 | — | — |
| ![Fake Construction Yard cameo](images/actors/ra/facf.png) ![Fake Construction Yard unit](images/actors/ra/facf_unit.png) | `FACF` | Fake Construction Yard | — | 200 | 150000 | Wood | — | 1c0 | — | — |
| ![Gap Generator cameo](images/actors/ra/gap.png) ![Gap Generator unit](images/actors/ra/gap_unit.png) | `GAP` | Gap Generator | Allied | 800 | 50000 | Heavy | — | 6c0 | — | — |
| ![Chronosphere cameo](images/actors/ra/pdox.png) ![Chronosphere unit](images/actors/ra/pdox_unit.png) | `PDOX` | Chronosphere | Allied | 1500 | 100000 | Wood | — | 6c0 | — | — |
| ![Tesla Coil cameo](images/actors/ra/tsla.png) ![Tesla Coil unit](images/actors/ra/tsla_unit.png) | `TSLA` | Tesla Coil | Soviet | 1200 | 40000 | Heavy | — | 7c0 | TeslaZap | DetectCloaked |
| ![AA Gun cameo](images/actors/ra/agun.png) ![AA Gun unit](images/actors/ra/agun_unit.png) | `AGUN` | AA Gun | Allied | 800 | 40000 | Heavy | — | 6c0 | ZSU-23 | — |
| ![Pillbox cameo](images/actors/ra/pbox.png) ![Pillbox unit](images/actors/ra/pbox_unit.png) | `PBOX` | Pillbox | Allied | 600 | 40000 | Heavy | — | 6c0 | — | DetectCloaked |
| ![Camo Pillbox cameo](images/actors/ra/hbox.png) ![Camo Pillbox unit](images/actors/ra/hbox_unit.png) | `HBOX` | Camo Pillbox | Allied | 750 | 40000 | Heavy | — | 6c0 | — | Cloak, DetectCloaked |
| ![Turret cameo](images/actors/ra/gun.png) ![Turret unit](images/actors/ra/gun_unit.png) | `GUN` | Turret | Allied | 800 | 40000 | Heavy | — | 6c512 | TurretGun | DetectCloaked |
| ![Flame Tower cameo](images/actors/ra/ftur.png) ![Flame Tower unit](images/actors/ra/ftur_unit.png) | `FTUR` | Flame Tower | Soviet | 600 | 40000 | Heavy | — | 6c0 | FireballLauncher | DetectCloaked |
| ![SAM Site cameo](images/actors/ra/sam.png) ![SAM Site unit](images/actors/ra/sam_unit.png) | `SAM` | SAM Site | Soviet | 700 | 40000 | Heavy | — | 8c0 | Nike | — |
| ![Construction Yard cameo](images/actors/ra/fact.png) ![Construction Yard unit](images/actors/ra/fact_unit.png) | `FACT` | Construction Yard | — | 2000 | 150000 | Wood | — | 5c0 | — | BaseProvider, Transforms |
| ![Silo cameo](images/actors/ra/silo.png) ![Silo unit](images/actors/ra/silo_unit.png) | `SILO` | Silo | — | 150 | 30000 | Wood | — | 4c0 | — | — |
| ![Soviet Tech Center cameo](images/actors/ra/stek.png) ![Soviet Tech Center unit](images/actors/ra/stek_unit.png) | `STEK` | Soviet Tech Center | Soviet | 1500 | 80000 | Wood | — | 5c0 | — | — |
| ![Kennel cameo](images/actors/ra/kenn.png) ![Kennel unit](images/actors/ra/kenn_unit.png) | `KENN` | Kennel | Soviet | 200 | 30000 | Wood | — | 4c0 | — | — |
| ![Sandbag Wall cameo](images/actors/ra/sbag.png) ![Sandbag Wall unit](images/actors/ra/sbag_unit.png) | `SBAG` | Sandbag Wall | Allied | 30 | 15000 | Wood | — | — | — | — |
| ![Wire Fence cameo](images/actors/ra/fenc.png) ![Wire Fence unit](images/actors/ra/fenc_unit.png) | `FENC` | Wire Fence | Soviet | 30 | 15000 | Wood | — | — | — | — |
| ![Concrete Wall cameo](images/actors/ra/brik.png) ![Concrete Wall unit](images/actors/ra/brik_unit.png) | `BRIK` | Concrete Wall | — | 200 | 40000 | Concrete | — | — | — | — |

## Tiberian Dawn

*54 buildable actors.*

### Tiberian Dawn — Infantry (11)

| Preview | Code | Name | Faction | Cost | HP | Armor | Speed | Sight | Weapon(s) | Notable traits |
| :---: | :--- | :--- | :--- | ---: | ---: | :--- | ---: | ---: | :--- | :--- |
| ![Engineer cameo](images/actors/cnc/e6.png) ![Engineer unit](images/actors/cnc/e6_unit.png) | `E6` | Engineer | GDI / Nod | 500 | 3000 | None | 46 | 5c0 | — | Captures, DetectCloaked |
| ![Minigunner cameo](images/actors/cnc/e1.png) ![Minigunner unit](images/actors/cnc/e1_unit.png) | `E1` | Minigunner | GDI / Nod | 100 | 5000 | None | 54 | 5c0 | M16 | DetectCloaked |
| ![Grenadier cameo](images/actors/cnc/e2.png) ![Grenadier unit](images/actors/cnc/e2_unit.png) | `E2` | Grenadier | GDI | 160 | 5000 | None | 68 | 5c0 | Grenade | DetectCloaked |
| ![Rocket Soldier cameo](images/actors/cnc/e3.png) ![Rocket Soldier unit](images/actors/cnc/e3_unit.png) | `E3` | Rocket Soldier | GDI / Nod | 300 | 4500 | None | 39 | 5c0 | Rockets | DetectCloaked |
| ![Flamethrower cameo](images/actors/cnc/e4.png) ![Flamethrower unit](images/actors/cnc/e4_unit.png) | `E4` | Flamethrower | Nod | 200 | 9000 | None | 54 | 5c0 | Flamethrower | DetectCloaked |
| ![Chemical Warrior cameo](images/actors/cnc/e5.png) ![Chemical Warrior unit](images/actors/cnc/e5_unit.png) | `E5` | Chemical Warrior | Nod | 300 | 9000 | None | 54 | 5c0 | Chemspray | DetectCloaked |
| ![Commando cameo](images/actors/cnc/rmbo.png) ![Commando unit](images/actors/cnc/rmbo_unit.png) | `RMBO` | Commando | GDI | 1500 | 15000 | None | 68 | 6c0 | Sniper | Demolition, DetectCloaked |
| ![Stegosaurus cameo](images/actors/cnc/steg.png) ![Stegosaurus unit](images/actors/cnc/steg_unit.png) | `STEG` | Stegosaurus | GDI / Nod | 1000 | 100000 | Wood | 113 | 6c0 | tail | — |
| ![Tyrannosaurus rex cameo](images/actors/cnc/trex.png) ![Tyrannosaurus rex unit](images/actors/cnc/trex_unit.png) | `TREX` | Tyrannosaurus rex | GDI / Nod | 1000 | 100000 | Wood | 113 | 6c0 | teeth | — |
| ![Triceratops cameo](images/actors/cnc/tric.png) ![Triceratops unit](images/actors/cnc/tric_unit.png) | `TRIC` | Triceratops | GDI / Nod | 1000 | 100000 | Wood | 113 | 6c0 | horn | — |
| ![Velociraptor cameo](images/actors/cnc/rapt.png) ![Velociraptor unit](images/actors/cnc/rapt_unit.png) | `RAPT` | Velociraptor | GDI / Nod | 1000 | 100000 | Wood | 113 | 6c0 | claw | — |

### Tiberian Dawn — Vehicle (17)

| Preview | Code | Name | Faction | Cost | HP | Armor | Speed | Sight | Weapon(s) | Notable traits |
| :---: | :--- | :--- | :--- | ---: | ---: | :--- | ---: | ---: | :--- | :--- |
| ![Supply Truck cameo](images/actors/cnc/truck.png) ![Supply Truck unit](images/actors/cnc/truck_unit.png) | `TRUCK` | Supply Truck | GDI / Nod | 1000 | 11000 | Light | 113 | 4c0 | — | Repairable |
| ![Harvester cameo](images/actors/cnc/harv.png) ![Harvester unit](images/actors/cnc/harv_unit.png) | `HARV` | Harvester | GDI / Nod | 1100 | 62500 | Heavy | 72 | 4c0 | — | Cloak, Repairable |
| ![Mobile Construction Vehicle cameo](images/actors/cnc/mcv.png) ![Mobile Construction Vehicle unit](images/actors/cnc/mcv_unit.png) | `MCV` | Mobile Construction Vehicle | GDI / Nod | 3000 | 120000 | Heavy | 60 | 8c0 | — | Repairable, Transforms |
| ![Visceroid cameo](images/actors/cnc/pvice.png) ![Visceroid unit](images/actors/cnc/pvice_unit.png) | `PVICE` | Visceroid | GDI / Nod | 700 | 30000 | Light | 68 | 6c0 | Chemspray | — |
| ![APC cameo](images/actors/cnc/apc.png) ![APC unit](images/actors/cnc/apc_unit.png) | `APC` | APC | GDI | 600 | 19000 | Heavy | 128 | 7c0 | APCGun, APCGun.AA | Cloak, Repairable |
| ![Artillery cameo](images/actors/cnc/arty.png) ![Artillery unit](images/actors/cnc/arty_unit.png) | `ARTY` | Artillery | Nod | 600 | 7500 | Light | 72 | 5c0 | ArtilleryShell | Cloak, Repairable |
| ![Flame Tank cameo](images/actors/cnc/ftnk.png) ![Flame Tank unit](images/actors/cnc/ftnk_unit.png) | `FTNK` | Flame Tank | Nod | 600 | 27000 | Heavy | 92 | 6c0 | BigFlamer | Cloak, Repairable |
| ![Nod Buggy cameo](images/actors/cnc/bggy.png) ![Nod Buggy unit](images/actors/cnc/bggy_unit.png) | `BGGY` | Nod Buggy | Nod | 300 | 12000 | Light | 170 | 8c0 | MachineGun | Cloak, Repairable |
| ![Recon Bike cameo](images/actors/cnc/bike.png) ![Recon Bike unit](images/actors/cnc/bike_unit.png) | `BIKE` | Recon Bike | Nod | 500 | 11000 | Light | 192 | 8c0 | BikeRockets | Cloak, Repairable |
| ![Hum-vee cameo](images/actors/cnc/jeep.png) ![Hum-vee unit](images/actors/cnc/jeep_unit.png) | `JEEP` | Hum-vee | GDI | 400 | 16000 | Light | 145 | 8c0 | MachineGunH | Cloak, Repairable |
| ![Light Tank cameo](images/actors/cnc/ltnk.png) ![Light Tank unit](images/actors/cnc/ltnk_unit.png) | `LTNK` | Light Tank | Nod | 750 | 32000 | Heavy | 102 | 6c0 | 70mm | Cloak, Repairable |
| ![Medium Tank cameo](images/actors/cnc/mtnk.png) ![Medium Tank unit](images/actors/cnc/mtnk_unit.png) | `MTNK` | Medium Tank | GDI | 900 | 45000 | Heavy | 72 | 6c0 | 120mm | Cloak, Repairable |
| ![Mammoth Tank cameo](images/actors/cnc/htnk.png) ![Mammoth Tank unit](images/actors/cnc/htnk_unit.png) | `HTNK` | Mammoth Tank | GDI | 1800 | 87000 | Heavy | 46 | 6c0 | 120mmDual, MammothMissiles | Cloak, Repairable |
| ![Rocket Launcher cameo](images/actors/cnc/msam.png) ![Rocket Launcher unit](images/actors/cnc/msam_unit.png) | `MSAM` | Rocket Launcher | GDI | 900 | 12000 | Light | 72 | 6c0 | 227mm, 227mm | Cloak, Repairable |
| ![Mobile SAM cameo](images/actors/cnc/mlrs.png) ![Mobile SAM unit](images/actors/cnc/mlrs_unit.png) | `MLRS` | Mobile SAM | Nod | 600 | 18000 | Light | 92 | 8c0 | Patriot | Cloak, Repairable |
| ![Stealth Tank cameo](images/actors/cnc/stnk.png) ![Stealth Tank unit](images/actors/cnc/stnk_unit.png) | `STNK` | Stealth Tank | Nod | 900 | 15000 | Light | 127 | 7c0 | 227mm.stnk, 227mm.stnkAA | Cloak, Repairable |
| ![Mobile HQ cameo](images/actors/cnc/mhq.png) ![Mobile HQ unit](images/actors/cnc/mhq_unit.png) | `MHQ` | Mobile HQ | — | 1000 | 20000 | Light | 72 | 6c0 | — | Repairable |

### Tiberian Dawn — Aircraft (3)

| Preview | Code | Name | Faction | Cost | HP | Armor | Speed | Sight | Weapon(s) | Notable traits |
| :---: | :--- | :--- | :--- | ---: | ---: | :--- | ---: | ---: | :--- | :--- |
| ![Chinook Transport cameo](images/actors/cnc/tran.png) ![Chinook Transport unit](images/actors/cnc/tran_unit.png) | `TRAN` | Chinook Transport | GDI / Nod | 750 | 12500 | Light | 150 | 10c0 | — | Repairable |
| ![Apache Longbow cameo](images/actors/cnc/heli.png) ![Apache Longbow unit](images/actors/cnc/heli_unit.png) | `HELI` | Apache Longbow | Nod | 1200 | 12500 | Light | 180 | 10c0 | HeliAGGun, HeliAAGun | Repairable |
| ![Orca cameo](images/actors/cnc/orca.png) ![Orca unit](images/actors/cnc/orca_unit.png) | `ORCA` | Orca | GDI | 1200 | 10000 | Light | 186 | 10c0 | OrcaAGMissiles, OrcaAAMissiles | Repairable |

### Tiberian Dawn — Building (23)

| Preview | Code | Name | Faction | Cost | HP | Armor | Speed | Sight | Weapon(s) | Notable traits |
| :---: | :--- | :--- | :--- | ---: | ---: | :--- | ---: | ---: | :--- | :--- |
| ![Tech Center cameo](images/actors/cnc/miss.png) ![Tech Center unit](images/actors/cnc/miss_unit.png) | `MISS` | Tech Center | — | 0 | 80000 | Wood | — | 13c0 | — | — |
| ![Helipad cameo](images/actors/cnc/hpad.png) ![Helipad unit](images/actors/cnc/hpad_unit.png) | `HPAD` | Helipad | GDI / Nod | 1000 | 60000 | Wood | — | 5c0 | — | — |
| ![Repair Facility cameo](images/actors/cnc/fix.png) ![Repair Facility unit](images/actors/cnc/fix_unit.png) | `FIX` | Repair Facility | GDI / Nod | 500 | 80000 | Wood | — | 5c0 | — | — |
| ![Construction Yard cameo](images/actors/cnc/fact.png) ![Construction Yard unit](images/actors/cnc/fact_unit.png) | `FACT` | Construction Yard | — | 3000 | 210000 | Wood | — | 10c0 | — | BaseProvider, Transforms |
| ![Power Plant cameo](images/actors/cnc/nuke.png) ![Power Plant unit](images/actors/cnc/nuke_unit.png) | `NUKE` | Power Plant | GDI / Nod | 500 | 55000 | Wood | — | 4c0 | — | — |
| ![Advanced Power Plant cameo](images/actors/cnc/nuk2.png) ![Advanced Power Plant unit](images/actors/cnc/nuk2_unit.png) | `NUK2` | Advanced Power Plant | GDI / Nod | 800 | 70000 | Wood | — | 4c0 | — | — |
| ![Tiberium Refinery cameo](images/actors/cnc/proc.png) ![Tiberium Refinery unit](images/actors/cnc/proc_unit.png) | `PROC` | Tiberium Refinery | GDI / Nod | 1500 | 100000 | Wood | — | 6c0 | — | — |
| ![Tiberium Silo cameo](images/actors/cnc/silo.png) ![Tiberium Silo unit](images/actors/cnc/silo_unit.png) | `SILO` | Tiberium Silo | GDI / Nod | 100 | 50000 | Wood | — | 4c0 | — | — |
| ![Barracks cameo](images/actors/cnc/pyle.png) ![Barracks unit](images/actors/cnc/pyle_unit.png) | `PYLE` | Barracks | GDI | 500 | 60000 | Wood | — | 5c0 | — | — |
| ![Hand of Nod cameo](images/actors/cnc/hand.png) ![Hand of Nod unit](images/actors/cnc/hand_unit.png) | `HAND` | Hand of Nod | Nod | 500 | 60000 | Wood | — | 5c0 | — | — |
| ![Airstrip cameo](images/actors/cnc/afld.png) ![Airstrip unit](images/actors/cnc/afld_unit.png) | `AFLD` | Airstrip | Nod | 2000 | 110000 | Wood | — | 7c0 | — | — |
| ![Weapons Factory cameo](images/actors/cnc/weap.png) ![Weapons Factory unit](images/actors/cnc/weap_unit.png) | `WEAP` | Weapons Factory | GDI | 2000 | 110000 | Wood | — | 4c0 | — | — |
| ![Communications Center cameo](images/actors/cnc/hq.png) ![Communications Center unit](images/actors/cnc/hq_unit.png) | `HQ` | Communications Center | GDI / Nod | 1000 | 80000 | Wood | — | 10c0 | — | AirstrikePower, DetectCloaked, ProvidesRadar |
| ![Advanced Communications Center cameo](images/actors/cnc/eye.png) ![Advanced Communications Center unit](images/actors/cnc/eye_unit.png) | `EYE` | Advanced Communications Center | GDI | 1800 | 130000 | Wood | — | 10c0 | — | DetectCloaked, IonCannonPower, ProvidesRadar |
| ![Temple of Nod cameo](images/actors/cnc/tmpl.png) ![Temple of Nod unit](images/actors/cnc/tmpl_unit.png) | `TMPL` | Temple of Nod | Nod | 2000 | 210000 | Wood | — | 6c0 | — | DetectCloaked, NukePower |
| ![Turret cameo](images/actors/cnc/gun.png) ![Turret unit](images/actors/cnc/gun_unit.png) | `GUN` | Turret | GDI / Nod | 600 | 41000 | Concrete | — | 6c0 | TurretGun | DetectCloaked |
| ![SAM Site cameo](images/actors/cnc/sam.png) ![SAM Site unit](images/actors/cnc/sam_unit.png) | `SAM` | SAM Site | Nod | 650 | 40000 | Concrete | — | 8c0 | Dragon | — |
| ![Obelisk of Light cameo](images/actors/cnc/obli.png) ![Obelisk of Light unit](images/actors/cnc/obli_unit.png) | `OBLI` | Obelisk of Light | Nod | 1500 | 75000 | Concrete | — | 8c0 | Laser | DetectCloaked |
| ![Guard Tower cameo](images/actors/cnc/gtwr.png) ![Guard Tower unit](images/actors/cnc/gtwr_unit.png) | `GTWR` | Guard Tower | GDI / Nod | 600 | 40000 | Concrete | — | 7c0 | HighV | DetectCloaked |
| ![Advanced Guard Tower cameo](images/actors/cnc/atwr.png) ![Advanced Guard Tower unit](images/actors/cnc/atwr_unit.png) | `ATWR` | Advanced Guard Tower | GDI | 1000 | 55000 | Concrete | — | 8c0 | TowerMissile, TowerAAMissile | DetectCloaked |
| ![Sandbag Barrier cameo](images/actors/cnc/sbag.png) ![Sandbag Barrier unit](images/actors/cnc/sbag_unit.png) | `SBAG` | Sandbag Barrier | GDI | 25 | 10000 | Light | — | — | — | — |
| ![Chain Link Barrier cameo](images/actors/cnc/cycl.png) ![Chain Link Barrier unit](images/actors/cnc/cycl_unit.png) | `CYCL` | Chain Link Barrier | Nod | 25 | 10000 | Light | — | — | — | — |
| ![Concrete Barrier cameo](images/actors/cnc/brik.png) ![Concrete Barrier unit](images/actors/cnc/brik_unit.png) | `BRIK` | Concrete Barrier | GDI / Nod | 150 | 20000 | Concrete | — | — | — | — |

## Dune 2000

*45 buildable actors.*

### Dune 2000 — Infantry (10)

| Preview | Code | Name | Faction | Cost | HP | Armor | Speed | Sight | Weapon(s) | Notable traits |
| :---: | :--- | :--- | :--- | ---: | ---: | :--- | ---: | ---: | :--- | :--- |
| ![Saboteur cameo](images/actors/d2k/saboteur.png) ![Saboteur unit](images/actors/d2k/saboteur_unit.png) | `saboteur` | Saboteur | — | 300 ## actually 0, but spawns from support power at Palace | 5000 | None | 43 | 4c768 | — | Cloak, Demolition, DetectCloaked, GrantConditionOnDeploy |
| ![Engineer cameo](images/actors/d2k/engineer.png) ![Engineer unit](images/actors/d2k/engineer_unit.png) | `engineer` | Engineer | — | 400 | 5000 | None | 31 | 2c768 | — | Captures, DetectCloaked |
| ![Light Infantry cameo](images/actors/d2k/light_inf.png) ![Light Infantry unit](images/actors/d2k/light_inf_unit.png) | `light_inf` | Light Infantry | — | 50 | 6000 | None | 43 | 3c768 | LMG | DetectCloaked |
| ![Trooper cameo](images/actors/d2k/trooper.png) ![Trooper unit](images/actors/d2k/trooper_unit.png) | `trooper` | Trooper | — | 100 | 7000 | None | 31 | 4c768 | Bazooka | DetectCloaked |
| ![Thumper Infantry cameo](images/actors/d2k/thumper.png) ![Thumper Infantry unit](images/actors/d2k/thumper_unit.png) | `thumper` | Thumper Infantry | — | 200 | 3750 | None | 43 | 2c768 | — | DetectCloaked, GrantConditionOnDeploy |
| ![Fremen cameo](images/actors/d2k/fremen.png) ![Fremen unit](images/actors/d2k/fremen_unit.png) | `fremen` | Fremen | — | 200 ## actually 0, but spawns from support power at Palace | 7000 | None | 43 | 4c768 | Fremen_S, Fremen_L | Cloak, DetectCloaked |
| ![Grenadier cameo](images/actors/d2k/grenadier.png) ![Grenadier unit](images/actors/d2k/grenadier_unit.png) | `grenadier` | Grenadier | Atreides | 80 | 6000 | None | 43 | 3c768 | grenade | DetectCloaked |
| ![Sardaukar cameo](images/actors/d2k/sardaukar.png) ![Sardaukar unit](images/actors/d2k/sardaukar_unit.png) | `sardaukar` | Sardaukar | — | 120 | 10000 | None | 31 | 4c768 | M_LMG, M_HMG | DetectCloaked |
| ![Sardaukar cameo](images/actors/d2k/mpsardaukar.png) ![Sardaukar unit](images/actors/d2k/mpsardaukar_unit.png) | `mpsardaukar` | Sardaukar | Harkonnen | 200 | 10000 | None | 31 | 4c768 | M_LMG_H, M_HMG_H | DetectCloaked |
| ![Fremen cameo](images/actors/d2k/nsfremen.png) ![Fremen unit](images/actors/d2k/nsfremen_unit.png) | `nsfremen` | Fremen | — | 200 ## actually 0, but spawns from support power at Palace | 7000 | None | 43 | 4c768 | Fremen_S, Fremen_L | DetectCloaked |

### Dune 2000 — Vehicle (14)

| Preview | Code | Name | Faction | Cost | HP | Armor | Speed | Sight | Weapon(s) | Notable traits |
| :---: | :--- | :--- | :--- | ---: | ---: | :--- | ---: | ---: | :--- | :--- |
| ![Spice Harvester cameo](images/actors/d2k/harvester.png) ![Spice Harvester unit](images/actors/d2k/harvester_unit.png) | `harvester` | Spice Harvester | — | 1200 | 45000 | Harvester | 43 | 3c768 | — | Repairable |
| ![Mobile Construction Vehicle cameo](images/actors/d2k/mcv.png) ![Mobile Construction Vehicle unit](images/actors/d2k/mcv_unit.png) | `mcv` | Mobile Construction Vehicle | — | 2000 | 45000 | Light | 31 | 2c768 | — | Repairable, Transforms |
| ![Trike cameo](images/actors/d2k/trike.png) ![Trike unit](images/actors/d2k/trike_unit.png) | `trike` | Trike | — | 300 | 9000 | Wood | 128 | 5c512 | HMG | Repairable |
| ![Missile Quad cameo](images/actors/d2k/quad.png) ![Missile Quad unit](images/actors/d2k/quad_unit.png) | `quad` | Missile Quad | — | 400 | 11000 | Light | 96 | 4c768 | Rocket | Repairable |
| ![Siege Tank cameo](images/actors/d2k/siege_tank.png) ![Siege Tank unit](images/actors/d2k/siege_tank_unit.png) | `siege_tank` | Siege Tank | — | 800 | 11500 | Light | 40 | 6c768 | 155mm | Repairable |
| ![Missile Tank cameo](images/actors/d2k/missile_tank.png) ![Missile Tank unit](images/actors/d2k/missile_tank_unit.png) | `missile_tank` | Missile Tank | — | 900 | 13000 | Wood | 60 | 6c768 | mtank_pri | Repairable |
| ![Sonic Tank cameo](images/actors/d2k/sonic_tank.png) ![Sonic Tank unit](images/actors/d2k/sonic_tank_unit.png) | `sonic_tank` | Sonic Tank | Atreides | 1100 | 30000 | Light | 31 | 5c768 | Sound | Repairable |
| ![Devastator cameo](images/actors/d2k/devastator.png) ![Devastator unit](images/actors/d2k/devastator_unit.png) | `devastator` | Devastator | Harkonnen | 1200 | 50000 | Heavy | 31 | 5c512 | DevBullet | GrantConditionOnDeploy, Repairable |
| ![Raider Trike cameo](images/actors/d2k/raider.png) ![Raider Trike unit](images/actors/d2k/raider_unit.png) | `raider` | Raider Trike | — | 330 | 9200 | Wood | 140 | 4c768 | HMGo | Repairable |
| ![Stealth Raider Trike cameo](images/actors/d2k/stealth_raider.png) ![Stealth Raider Trike unit](images/actors/d2k/stealth_raider_unit.png) | `stealth_raider` | Stealth Raider Trike | Ordos | 400 | 10000 | Wood | 140 | 4c768 | HMGo | Cloak, Repairable |
| ![Deviator cameo](images/actors/d2k/deviator.png) ![Deviator unit](images/actors/d2k/deviator_unit.png) | `deviator` | Deviator | Ordos | 1000 | 12500 | Wood | 53 | 6c0 | DeviatorMissile | Repairable |
| ![Atreides Combat Tank cameo](images/actors/d2k/combat_tank_a.png) ![Atreides Combat Tank unit](images/actors/d2k/combat_tank_a_unit.png) | `combat_tank_a` | Atreides Combat Tank | — | 700 | 22000 | Heavy | 75 | 5c768 | 80mm_A | Repairable |
| ![Harkonnen Combat Tank cameo](images/actors/d2k/combat_tank_h.png) ![Harkonnen Combat Tank unit](images/actors/d2k/combat_tank_h_unit.png) | `combat_tank_h` | Harkonnen Combat Tank | — | 700 | 28500 | Heavy | 64 | 5c768 | 80mm_H | Repairable |
| ![Ordos Combat Tank cameo](images/actors/d2k/combat_tank_o.png) ![Ordos Combat Tank unit](images/actors/d2k/combat_tank_o_unit.png) | `combat_tank_o` | Ordos Combat Tank | — | 700 | 19000 | Heavy | 85 | 5c768 | 80mm_O | Repairable |

### Dune 2000 — Aircraft (2)

| Preview | Code | Name | Faction | Cost | HP | Armor | Speed | Sight | Weapon(s) | Notable traits |
| :---: | :--- | :--- | :--- | ---: | ---: | :--- | ---: | ---: | :--- | :--- |
| ![Carryall cameo](images/actors/d2k/carryall.png) ![Carryall unit](images/actors/d2k/carryall_unit.png) | `carryall` | Carryall | — | 1000 | 20000 | Light | 170 | — | — | — |
| ![Ornithopter cameo](images/actors/d2k/ornithopter.png) ![Ornithopter unit](images/actors/d2k/ornithopter_unit.png) | `ornithopter` | Ornithopter | — | — | 8000 | Light | 224 | — | OrniBomb | — |

### Dune 2000 — Building (19)

| Preview | Code | Name | Faction | Cost | HP | Armor | Speed | Sight | Weapon(s) | Notable traits |
| :---: | :--- | :--- | :--- | ---: | ---: | :--- | ---: | ---: | :--- | :--- |
| ![Silo cameo](images/actors/d2k/silo.png) ![Silo unit](images/actors/d2k/silo_unit.png) | `silo` | Silo | — | 120 | 15000 | Building | — | 2c768 | — | — |
| ![Concrete Wall cameo](images/actors/d2k/wall.png) ![Concrete Wall unit](images/actors/d2k/wall_unit.png) | `wall` | Concrete Wall | — | 100 | 20000 | Wall | — | 1c768 | — | — |
| ![Repair Pad cameo](images/actors/d2k/repair_pad.png) ![Repair Pad unit](images/actors/d2k/repair_pad_unit.png) | `repair_pad` | Repair Pad | — | 800 | 30000 | Building | — | 3c768 | — | — |
| ![Death Hand cameo](images/actors/d2k/deathhand.png) ![Death Hand unit](images/actors/d2k/deathhand_unit.png) | `deathhand` | Death Hand | — | — | — | — | — | — | — | — |
| ![Concrete Slab cameo](images/actors/d2k/concretea.png) ![Concrete Slab unit](images/actors/d2k/concretea_unit.png) | `concretea` | Concrete Slab | — | 20 | — | — | — | — | — | — |
| ![Large Concrete Slab cameo](images/actors/d2k/concreteb.png) ![Large Concrete Slab unit](images/actors/d2k/concreteb_unit.png) | `concreteb` | Large Concrete Slab | — | 50 | — | — | — | — | — | — |
| ![Construction Yard cameo](images/actors/d2k/construction_yard.png) ![Construction Yard unit](images/actors/d2k/construction_yard_unit.png) | `construction_yard` | Construction Yard | — | 2000 | 30000 | Cy | — | 5c768 | — | — |
| ![Wind Trap cameo](images/actors/d2k/wind_trap.png) ![Wind Trap unit](images/actors/d2k/wind_trap_unit.png) | `wind_trap` | Wind Trap | — | 225 | 28000 | Building | — | 3c768 | — | — |
| ![Barracks cameo](images/actors/d2k/barracks.png) ![Barracks unit](images/actors/d2k/barracks_unit.png) | `barracks` | Barracks | — | 300 | 32000 | Building | — | 3c768 | — | — |
| ![Spice Refinery cameo](images/actors/d2k/refinery.png) ![Spice Refinery unit](images/actors/d2k/refinery_unit.png) | `refinery` | Spice Refinery | — | 1500 | 30000 | Building | — | 3c768 | — | — |
| ![Light Factory cameo](images/actors/d2k/light_factory.png) ![Light Factory unit](images/actors/d2k/light_factory_unit.png) | `light_factory` | Light Factory | — | 600 | 33000 | Building | — | 5c768 | — | — |
| ![Heavy Factory cameo](images/actors/d2k/heavy_factory.png) ![Heavy Factory unit](images/actors/d2k/heavy_factory_unit.png) | `heavy_factory` | Heavy Factory | — | 1200 | 35000 | Building | — | 4c768 | — | — |
| ![Outpost cameo](images/actors/d2k/outpost.png) ![Outpost unit](images/actors/d2k/outpost_unit.png) | `outpost` | Outpost | — | 750 | 35000 | Building | — | 11c0 | — | DetectCloaked, ProvidesRadar |
| ![Starport cameo](images/actors/d2k/starport.png) ![Starport unit](images/actors/d2k/starport_unit.png) | `starport` | Starport | — | 1500 | 35000 | Heavy | — | 3c768 | — | — |
| ![Gun Turret cameo](images/actors/d2k/medium_gun_turret.png) ![Gun Turret unit](images/actors/d2k/medium_gun_turret_unit.png) | `medium_gun_turret` | Gun Turret | — | 550 | 24000 | Wall | — | 5c0 | 110mm_Gun | DetectCloaked |
| ![Rocket Turret cameo](images/actors/d2k/large_gun_turret.png) ![Rocket Turret unit](images/actors/d2k/large_gun_turret_unit.png) | `large_gun_turret` | Rocket Turret | — | 750 | 27000 | Wall | — | 6c0 | TowerMissile | DetectCloaked |
| ![High Tech Factory cameo](images/actors/d2k/high_tech_factory.png) ![High Tech Factory unit](images/actors/d2k/high_tech_factory_unit.png) | `high_tech_factory` | High Tech Factory | — | 1150 | 35000 | Building | — | 4c768 | — | AirstrikePower |
| ![IX Research Center cameo](images/actors/d2k/research_centre.png) ![IX Research Center unit](images/actors/d2k/research_centre_unit.png) | `research_centre` | IX Research Center | — | 1000 | 25000 | Building | — | 4c768 | — | — |
| ![Palace cameo](images/actors/d2k/palace.png) ![Palace unit](images/actors/d2k/palace_unit.png) | `palace` | Palace | — | 1600 | 40000 | Heavy | — | 4c768 | — | NukePower |

## Tiberian Sun

*80 buildable actors.*

### Tiberian Sun — Infantry (10)

| Preview | Code | Name | Faction | Cost | HP | Armor | Speed | Sight | Weapon(s) | Notable traits |
| :---: | :--- | :--- | :--- | ---: | ---: | :--- | ---: | ---: | :--- | :--- |
| ![Disc Thrower cameo](images/actors/ts/e2.png) ![Disc Thrower unit](images/actors/ts/e2_unit.png) | `E2` | Disc Thrower | — | 200 | 15000 | None | 56 | 7c0 | Grenade | Cloak, ProducibleWithLevel |
| ![Medic cameo](images/actors/ts/medic.png) ![Medic unit](images/actors/ts/medic_unit.png) | `MEDIC` | Medic | — | 600 | 12500 | None | 56 | 6c0 | Heal | Cloak |
| ![Ghost Stalker cameo](images/actors/ts/ghost.png) ![Ghost Stalker unit](images/actors/ts/ghost_unit.png) | `GHOST` | Ghost Stalker | — | 1750 | 20000 | Light | 56 | 6c0 | LtRail | Cloak, Demolition, ProducibleWithLevel |
| ![Wolverine cameo](images/actors/ts/smech.png) ![Wolverine unit](images/actors/ts/smech_unit.png) | `SMECH` | Wolverine | — | 500 | 17500 | Light | 99 | 6c0 | AssaultCannon | Cloak, Repairable |
| ![Rocket Infantry cameo](images/actors/ts/e3.png) ![Rocket Infantry unit](images/actors/ts/e3_unit.png) | `E3` | Rocket Infantry | — | 250 | 10000 | None | 56 | 7c0 | Bazooka | Cloak, ProducibleWithLevel |
| ![Cyborg Infantry cameo](images/actors/ts/cyborg.png) ![Cyborg Infantry unit](images/actors/ts/cyborg_unit.png) | `CYBORG` | Cyborg Infantry | — | 650 | 30000 | Light | 56 | 5c0 | Vulcan3 | Cloak, ProducibleWithLevel |
| ![Cyborg Commando cameo](images/actors/ts/cyc2.png) ![Cyborg Commando unit](images/actors/ts/cyc2_unit.png) | `CYC2` | Cyborg Commando | — | 2000 | 50000 | Heavy | 56 | 7c0 | CyCannon | Cloak, ProducibleWithLevel |
| ![Mutant Hijacker cameo](images/actors/ts/mhijack.png) ![Mutant Hijacker unit](images/actors/ts/mhijack_unit.png) | `MHIJACK` | Mutant Hijacker | — | 1850 | 30000 | None | 99 | 6c0 | — | Captures, Cloak |
| ![Light Infantry cameo](images/actors/ts/e1.png) ![Light Infantry unit](images/actors/ts/e1_unit.png) | `E1` | Light Infantry | — | 120 | 12500 | None | 71 | 5c0 | Minigun, M1Carbine | Cloak, ProducibleWithLevel |
| ![Engineer cameo](images/actors/ts/engineer.png) ![Engineer unit](images/actors/ts/engineer_unit.png) | `ENGINEER` | Engineer | — | 500 | 10000 | None | 56 | 4c0 | — | Captures, Cloak |

### Tiberian Sun — Vehicle (20)

| Preview | Code | Name | Faction | Cost | HP | Armor | Speed | Sight | Weapon(s) | Notable traits |
| :---: | :--- | :--- | :--- | ---: | ---: | :--- | ---: | ---: | :--- | :--- |
| ![Jump Jet Infantry cameo](images/actors/ts/jumpjet.png) ![Jump Jet Infantry unit](images/actors/ts/jumpjet_unit.png) | `JUMPJET` | Jump Jet Infantry | — | 600 | 12000 | Light | 71 | 6c0 | JumpCannon | Cloak, ProducibleWithLevel |
| ![Amphibious APC cameo](images/actors/ts/apc.png) ![Amphibious APC unit](images/actors/ts/apc_unit.png) | `APC` | Amphibious APC | — | 800 | 20000 | Heavy | 113 | 5c0 | — | Cloak, Repairable |
| ![Titan cameo](images/actors/ts/mmch.png) ![Titan unit](images/actors/ts/mmch_unit.png) | `MMCH` | Titan | — | 800 | 40000 | Heavy | 56 | 8c0 | 120mm | Cloak, DetectCloaked, Repairable |
| ![Mammoth Mk. II cameo](images/actors/ts/hmec.png) ![Mammoth Mk. II unit](images/actors/ts/hmec_unit.png) | `HMEC` | Mammoth Mk. II | — | 3000 | 80000 | Heavy | 42 | 8c0 | MammothTusk, MechRailgun | Cloak, Repairable |
| ![Disruptor cameo](images/actors/ts/sonic.png) ![Disruptor unit](images/actors/ts/sonic_unit.png) | `SONIC` | Disruptor | — | 1300 | 50000 | Heavy | 56 | 7c0 | SonicZap | Cloak, Repairable |
| ![Juggernaut cameo](images/actors/ts/jugg.png) ![Juggernaut unit](images/actors/ts/jugg_unit.png) | `JUGG` | Juggernaut | — | 950 | 35000 | Light | 71 | 9c0 | Jugg90mm | Cloak, GrantConditionOnDeploy, Repairable |
| ![Mobile EMP Cannon cameo](images/actors/ts/mobilemp.png) ![Mobile EMP Cannon unit](images/actors/ts/mobilemp_unit.png) | `MOBILEMP` | Mobile EMP Cannon | — | 1000 | 80000 | Heavy | 85 | 6c0 | — | Cloak, Repairable |
| ![Attack Buggy cameo](images/actors/ts/bggy.png) ![Attack Buggy unit](images/actors/ts/bggy_unit.png) | `BGGY` | Attack Buggy | — | 500 | 22000 | Light | 142 | 6c0 | RaiderCannon | Cloak, Repairable |
| ![Attack Cycle cameo](images/actors/ts/bike.png) ![Attack Cycle unit](images/actors/ts/bike_unit.png) | `BIKE` | Attack Cycle | — | 600 | 15000 | Wood | 170 | 5c0 | BikeMissile, HoverMissile | Cloak, Repairable |
| ![Tick Tank cameo](images/actors/ts/ttnk.png) ![Tick Tank unit](images/actors/ts/ttnk_unit.png) | `TTNK` | Tick Tank | — | 800 | 35000 | Light | 85 | 5c0 | 90mm, 120mmx, 90mm, 120mmx | Cloak, DetectCloaked, GrantConditionOnDeploy, Repairable |
| ![Artillery cameo](images/actors/ts/art2.png) ![Artillery unit](images/actors/ts/art2_unit.png) | `ART2` | Artillery | — | 975 | 30000 | Light | 71 | 9c0 | 155mm | Cloak, GrantConditionOnDeploy, Repairable |
| ![Mobile Repair Vehicle cameo](images/actors/ts/repair.png) ![Mobile Repair Vehicle unit](images/actors/ts/repair_unit.png) | `REPAIR` | Mobile Repair Vehicle | — | 1000 | 20000 | — | 85 | 5c0 | Repair | Cloak, Repairable |
| ![Weed Eater cameo](images/actors/ts/weed.png) ![Weed Eater unit](images/actors/ts/weed_unit.png) | `WEED` | Weed Eater | — | 1400 | 60000 | Heavy | 71 | 4c0 | — | Cloak, Repairable |
| ![Subterranean APC cameo](images/actors/ts/sapc.png) ![Subterranean APC unit](images/actors/ts/sapc_unit.png) | `SAPC` | Subterranean APC | — | 800 | 17500 | Heavy | 71 | 5c0 | — | Cloak, Repairable |
| ![Devil's Tongue cameo](images/actors/ts/subtank.png) ![Devil's Tongue unit](images/actors/ts/subtank_unit.png) | `SUBTANK` | Devil's Tongue | — | 750 | 30000 | Light | 71 | 5c0 | FireballLauncher | Cloak, Repairable |
| ![Stealth Tank cameo](images/actors/ts/stnk.png) ![Stealth Tank unit](images/actors/ts/stnk_unit.png) | `STNK` | Stealth Tank | — | 1100 | 18000 | Light | 85 | 5c0 | Dragon | Cloak, Repairable |
| ![Mobile Stealth Generator cameo](images/actors/ts/sgen.png) ![Mobile Stealth Generator unit](images/actors/ts/sgen_unit.png) | `SGEN` | Mobile Stealth Generator | — | 1600 | 20000 | Light | 85 | 5c0 | — | Cloak, GrantConditionOnDeploy, Repairable |
| ![Mobile Construction Vehicle cameo](images/actors/ts/mcv.png) ![Mobile Construction Vehicle unit](images/actors/ts/mcv_unit.png) | `MCV` | Mobile Construction Vehicle | — | 2500 | 100000 | Heavy | 42 | 6c0 | — | Cloak, Repairable, Transforms |
| ![Harvester cameo](images/actors/ts/harv.png) ![Harvester unit](images/actors/ts/harv_unit.png) | `HARV` | Harvester | — | 1400 | 100000 | Heavy | 71 | 4c0 | — | Cloak, Repairable |
| ![Mobile Sensor Array cameo](images/actors/ts/lpst.png) ![Mobile Sensor Array unit](images/actors/ts/lpst_unit.png) | `LPST` | Mobile Sensor Array | — | 950 | 60000 | Wood | 85 | 10c0 | — | Cloak, DetectCloaked, GrantConditionOnDeploy, Repairable |

### Tiberian Sun — Aircraft (6)

| Preview | Code | Name | Faction | Cost | HP | Armor | Speed | Sight | Weapon(s) | Notable traits |
| :---: | :--- | :--- | :--- | ---: | ---: | :--- | ---: | ---: | :--- | :--- |
| ![Orca Fighter cameo](images/actors/ts/orca.png) ![Orca Fighter unit](images/actors/ts/orca_unit.png) | `ORCA` | Orca Fighter | — | 1000 | 20000 | Light | 186 | 2c0 | Hellfire | Cloak, Repairable |
| ![Orca Bomber cameo](images/actors/ts/orcab.png) ![Orca Bomber unit](images/actors/ts/orcab_unit.png) | `ORCAB` | Orca Bomber | — | 1600 | 26000 | Light | 96 | 2c0 | Bomb | Cloak, Repairable |
| ![Orca Transport cameo](images/actors/ts/orcatran.png) ![Orca Transport unit](images/actors/ts/orcatran_unit.png) | `ORCATRAN` | Orca Transport | — | 1200 | 20000 | Light | 84 | 2c0 | — | Cloak, Repairable |
| ![Carryall cameo](images/actors/ts/trnsport.png) ![Carryall unit](images/actors/ts/trnsport_unit.png) | `TRNSPORT` | Carryall | — | 750 | 17500 | Light | 149 | 2c0 | — | Carryall, Cloak, Repairable |
| ![Banshee Fighter cameo](images/actors/ts/scrin.png) ![Banshee Fighter unit](images/actors/ts/scrin_unit.png) | `SCRIN` | Banshee Fighter | — | 1500 | 28000 | Light | 200 | 2c0 | Proton | Cloak, Repairable |
| ![Harpy cameo](images/actors/ts/apache.png) ![Harpy unit](images/actors/ts/apache_unit.png) | `APACHE` | Harpy | — | 1000 | 22500 | Light | 130 | 2c0 | HarpyClaw | Cloak, Repairable |

### Tiberian Sun — Naval (1)

| Preview | Code | Name | Faction | Cost | HP | Armor | Speed | Sight | Weapon(s) | Notable traits |
| :---: | :--- | :--- | :--- | ---: | ---: | :--- | ---: | ---: | :--- | :--- |
| ![Hover MLRS cameo](images/actors/ts/hvr.png) ![Hover MLRS unit](images/actors/ts/hvr_unit.png) | `HVR` | Hover MLRS | — | 900 | 23000 | Wood | 99 | 7c0 | HoverMissile | Cloak, Repairable |

### Tiberian Sun — Building (43)

| Preview | Code | Name | Faction | Cost | HP | Armor | Speed | Sight | Weapon(s) | Notable traits |
| :---: | :--- | :--- | :--- | ---: | ---: | :--- | ---: | ---: | :--- | :--- |
| ![Sandbags cameo](images/actors/ts/gasand.png) ![Sandbags unit](images/actors/ts/gasand_unit.png) | `GASAND` | Sandbags | — | 25 | 25000 | Light | — | — | — | Cloak |
| ![GDI Power Plant cameo](images/actors/ts/gapowr.png) ![GDI Power Plant unit](images/actors/ts/gapowr_unit.png) | `GAPOWR` | GDI Power Plant | GDI | 300 | 75000 | Wood | — | 4c0 | — | Cloak |
| ![Power Turbine cameo](images/actors/ts/gapowrup.png) ![Power Turbine unit](images/actors/ts/gapowrup_unit.png) | `GAPOWRUP` | Power Turbine | GDI | 150 | — | — | — | — | — | — |
| ![GDI Barracks cameo](images/actors/ts/gapile.png) ![GDI Barracks unit](images/actors/ts/gapile_unit.png) | `GAPILE` | GDI Barracks | GDI | 300 | 80000 | Wood | — | 5c0 | — | Cloak |
| ![GDI War Factory cameo](images/actors/ts/gaweap.png) ![GDI War Factory unit](images/actors/ts/gaweap_unit.png) | `GAWEAP` | GDI War Factory | GDI | 2000 | 100000 | Heavy | — | 4c0 | — | Cloak |
| ![Helipad cameo](images/actors/ts/gahpad.png) ![Helipad unit](images/actors/ts/gahpad_unit.png) | `GAHPAD` | Helipad | GDI | 500 | 60000 | — | — | 5c0 | — | Cloak |
| ![Service Depot cameo](images/actors/ts/gadept.png) ![Service Depot unit](images/actors/ts/gadept_unit.png) | `GADEPT` | Service Depot | GDI | 1200 | 110000 | — | — | 5c0 | — | Cloak |
| ![GDI Radar cameo](images/actors/ts/garadr.png) ![GDI Radar unit](images/actors/ts/garadr_unit.png) | `GARADR` | GDI Radar | GDI | 1000 | 100000 | Wood | — | 10c0 | — | Cloak, DetectCloaked, ProvidesRadar |
| ![GDI Tech Center cameo](images/actors/ts/gatech.png) ![GDI Tech Center unit](images/actors/ts/gatech_unit.png) | `GATECH` | GDI Tech Center | GDI | 1500 | 50000 | Wood | — | 4c0 | — | Cloak |
| ![GDI Upgrade Center cameo](images/actors/ts/gaplug.png) ![GDI Upgrade Center unit](images/actors/ts/gaplug_unit.png) | `GAPLUG` | GDI Upgrade Center | GDI | 1000 | 100000 | Wood | — | 6c0 | — | Cloak, IonCannonPower |
| ![Seeker Control cameo](images/actors/ts/gaplug2.png) ![Seeker Control unit](images/actors/ts/gaplug2_unit.png) | `GAPLUG2` | Seeker Control | GDI | 1000 | — | — | — | — | — | — |
| ![Ion Cannon Uplink cameo](images/actors/ts/gaplug3.png) ![Ion Cannon Uplink unit](images/actors/ts/gaplug3_unit.png) | `GAPLUG3` | Ion Cannon Uplink | GDI | 1500 | — | — | — | — | — | — |
| ![Drop Pod Node cameo](images/actors/ts/gaplug4.png) ![Drop Pod Node unit](images/actors/ts/gaplug4_unit.png) | `GAPLUG4` | Drop Pod Node | GDI | 1000 | — | — | — | — | — | — |
| ![Firestorm Generator cameo](images/actors/ts/gafire.png) ![Firestorm Generator unit](images/actors/ts/gafire_unit.png) | `GAFIRE` | Firestorm Generator | GDI | 1500 | 100000 | — | — | 6c0 | — | Cloak |
| ![Concrete Wall cameo](images/actors/ts/gawall.png) ![Concrete Wall unit](images/actors/ts/gawall_unit.png) | `GAWALL` | Concrete Wall | GDI | 50 | 22500 | Concrete | — | — | — | Cloak |
| ![GDI Gate cameo](images/actors/ts/gagate_a.png) ![GDI Gate unit](images/actors/ts/gagate_a_unit.png) | `GAGATE_A` | GDI Gate | GDI | 250 | 35000 | Heavy | — | — | — | Cloak |
| ![GDI Gate cameo](images/actors/ts/gagate_b.png) ![GDI Gate unit](images/actors/ts/gagate_b_unit.png) | `GAGATE_B` | GDI Gate | GDI | 250 | 35000 | Heavy | — | — | — | Cloak |
| ![Component Tower cameo](images/actors/ts/gactwr.png) ![Component Tower unit](images/actors/ts/gactwr_unit.png) | `GACTWR` | Component Tower | GDI | 200 | 50000 | Light | — | 6c0 | VulcanTower, RPGTower, RedEye2 | Cloak, DetectCloaked |
| ![Vulcan Tower cameo](images/actors/ts/gavulc.png) ![Vulcan Tower unit](images/actors/ts/gavulc_unit.png) | `GAVULC` | Vulcan Tower | GDI | 150 | — | — | — | — | — | — |
| ![RPG Upgrade cameo](images/actors/ts/garock.png) ![RPG Upgrade unit](images/actors/ts/garock_unit.png) | `GAROCK` | RPG Upgrade | GDI | 600 | — | — | — | — | — | — |
| ![SAM Upgrade cameo](images/actors/ts/gacsam.png) ![SAM Upgrade unit](images/actors/ts/gacsam_unit.png) | `GACSAM` | SAM Upgrade | GDI | 300 | — | — | — | — | — | — |
| ![Nod Power Plant cameo](images/actors/ts/napowr.png) ![Nod Power Plant unit](images/actors/ts/napowr_unit.png) | `NAPOWR` | Nod Power Plant | Nod | 300 | 75000 | Wood | — | 4c0 | — | Cloak |
| ![Nod Advanced Power Plant cameo](images/actors/ts/naapwr.png) ![Nod Advanced Power Plant unit](images/actors/ts/naapwr_unit.png) | `NAAPWR` | Nod Advanced Power Plant | Nod | 500 | 75000 | Wood | — | 4c0 | — | Cloak |
| ![Hand of Nod cameo](images/actors/ts/nahand.png) ![Hand of Nod unit](images/actors/ts/nahand_unit.png) | `NAHAND` | Hand of Nod | Nod | 300 | 80000 | Wood | — | 5c0 | — | Cloak |
| ![Nod War Factory cameo](images/actors/ts/naweap.png) ![Nod War Factory unit](images/actors/ts/naweap_unit.png) | `NAWEAP` | Nod War Factory | Nod | 2000 | 100000 | Heavy | — | 4c0 | — | Cloak |
| ![Helipad cameo](images/actors/ts/nahpad.png) ![Helipad unit](images/actors/ts/nahpad_unit.png) | `NAHPAD` | Helipad | Nod | 500 | 60000 | — | — | 5c0 | — | Cloak |
| ![Nod Radar cameo](images/actors/ts/naradr.png) ![Nod Radar unit](images/actors/ts/naradr_unit.png) | `NARADR` | Nod Radar | Nod | 1000 | 100000 | Wood | — | 10c0 | — | Cloak, DetectCloaked, ProvidesRadar |
| ![Nod Tech Center cameo](images/actors/ts/natech.png) ![Nod Tech Center unit](images/actors/ts/natech_unit.png) | `NATECH` | Nod Tech Center | Nod | 1500 | 50000 | Wood | — | 4c0 | — | Cloak |
| ![Stealth Generator cameo](images/actors/ts/nastlh.png) ![Stealth Generator unit](images/actors/ts/nastlh_unit.png) | `NASTLH` | Stealth Generator | Nod | 2500 | 60000 | Wood | — | 6c0 | — | Cloak |
| ![Temple of Nod cameo](images/actors/ts/natmpl.png) ![Temple of Nod unit](images/actors/ts/natmpl_unit.png) | `NATMPL` | Temple of Nod | Nod | 2000 | 100000 | Wood | — | 6c0 | — | Cloak |
| ![Nod Missile Silo cameo](images/actors/ts/namisl.png) ![Nod Missile Silo unit](images/actors/ts/namisl_unit.png) | `NAMISL` | Nod Missile Silo | Nod | 1300 | 100000 | Wood | — | 4c0 | — | Cloak, NukePower |
| ![Waste Refinery cameo](images/actors/ts/nawast.png) ![Waste Refinery unit](images/actors/ts/nawast_unit.png) | `NAWAST` | Waste Refinery | Nod | 1600 | 40000 | — | — | 6c0 | — | Cloak |
| ![Concrete Wall cameo](images/actors/ts/nawall.png) ![Concrete Wall unit](images/actors/ts/nawall_unit.png) | `NAWALL` | Concrete Wall | Nod | 50 | 22500 | Concrete | — | — | — | Cloak |
| ![Nod Gate cameo](images/actors/ts/nagate_a.png) ![Nod Gate unit](images/actors/ts/nagate_a_unit.png) | `NAGATE_A` | Nod Gate | Nod | 250 | 35000 | Heavy | — | — | — | Cloak |
| ![Nod Gate cameo](images/actors/ts/nagate_b.png) ![Nod Gate unit](images/actors/ts/nagate_b_unit.png) | `NAGATE_B` | Nod Gate | Nod | 250 | 35000 | Heavy | — | — | — | Cloak |
| ![Laser Fence cameo](images/actors/ts/napost.png) ![Laser Fence unit](images/actors/ts/napost_unit.png) | `NAPOST` | Laser Fence | Nod | 200 | 30000 | Concrete | — | 4c0 | — | Cloak |
| ![Laser Turret cameo](images/actors/ts/nalasr.png) ![Laser Turret unit](images/actors/ts/nalasr_unit.png) | `NALASR` | Laser Turret | Nod | 300 | 50000 | Wood | — | 7c0 | TurretLaserFire | Cloak, DetectCloaked |
| ![Obelisk of Light cameo](images/actors/ts/naobel.png) ![Obelisk of Light unit](images/actors/ts/naobel_unit.png) | `NAOBEL` | Obelisk of Light | Nod | 1500 | 72500 | Wood | — | 8c0 | ObeliskLaserFire | Cloak, DetectCloaked |
| ![S.A.M. Site cameo](images/actors/ts/nasam.png) ![S.A.M. Site unit](images/actors/ts/nasam_unit.png) | `NASAM` | S.A.M. Site | Nod | 500 | 60000 | Wood | — | 6c0 | RedEye2 | Cloak, DetectCloaked |
| ![Construction Yard cameo](images/actors/ts/gacnst.png) ![Construction Yard unit](images/actors/ts/gacnst_unit.png) | `GACNST` | Construction Yard | — | 2500 | 150000 | Wood | — | 5c0 | — | Cloak, Transforms |
| ![Tiberium Refinery cameo](images/actors/ts/proc.png) ![Tiberium Refinery unit](images/actors/ts/proc_unit.png) | `PROC` | Tiberium Refinery | — | 2000 | 90000 | — | — | 6c0 | — | Cloak |
| ![Silo cameo](images/actors/ts/gasilo.png) ![Silo unit](images/actors/ts/gasilo_unit.png) | `GASILO` | Silo | — | 150 | 30000 | Wood | — | 4c0 | — | Cloak |
| ![EMP Cannon cameo](images/actors/ts/napuls.png) ![EMP Cannon unit](images/actors/ts/napuls_unit.png) | `NAPULS` | EMP Cannon | — | 1000 | 50000 | Heavy | — | 8c0 | EMPulseCannon | Cloak, DetectCloaked |

## Summary

This appendix is a single-source, auto-generated reference to every buildable actor in OpenRA's four bundled mods, pairing each unit's cameo and internal codename with its faction, role, and core statistics drawn straight from the engine's own rules. It lowers the barrier to entry for new modders by putting the sprite, the YAML codename, and the numbers in one place, and it stays accurate over time because it is regenerated from the pinned source rather than maintained by hand.

## What to read next

- [Part 2.4 — Rules and Weapons](../chapters/Part_02_Chapter_04_Rules_Weapons.md) — how the actor and weapon YAML in these tables is defined.
- [Appendix H — Asset Visual Reference](Appendix_H_Asset_Visual_Reference.md) — the file formats and engine classes behind cameos, sprites, and other assets.
- [Part 10.3 — Porting and Modding](../chapters/Part_10_Chapter_03_Port_And_Modding.md) — creating your own actor from scratch.
