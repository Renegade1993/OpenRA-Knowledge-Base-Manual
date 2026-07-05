# Next-Session Handoff — OpenRA Manual v1.0

> **Read this one file to resume. You do NOT need to re-investigate anything below.**
> Full detail lives in `DEVELOPMENT_LOG.md` (top entry) and `PRODUCTION_HANDOFF.md` (top session-log entry). Read those only if you need specifics.

---

## 1. Where things stand (one paragraph)

The manual's **text is technically verified (statically) and proofread.** A prior session (Claude #1, 2026-06-25) pinned the engine version, verified every priority code snippet against the real engine source, fixed several real bugs, and proofread structure. **What's left = (a) a short list of engine-execution checks that need a Windows + .NET machine, and (b) the entire visual-asset + export pass (Claude #2).** No further deep static verification is needed.

## 2. Pinned version (use this exact checkout)

- **OpenRA `bleed` @ `972c10ec80f90a30a4fa80abfebc633af3365847`** — the **playtest** line (matches the manual's Part 0 note `playtest-20260222-76-g972c10ec80`).
- Source clone: `...\Game Sources and Development Reference Materials\OpenRA GitHub Repositories\OpenRA`
- **Open question for the user:** confirm playtest is the intended v1.0 target (vs a tagged release). If they want release, every snippet must be re-checked against a release checkout.

## 3. Environment gotchas (important, saves you hours)

- **No .NET / mono / msbuild** in the work sandbox → you **cannot** run `OpenRA.Utility.exe`, compile C#, or launch a mission here. Those are the deferred Windows steps in §5.
- **The OpenRA source clone IS readable via the file tools** (Read/Grep/Glob) even though it's not a "selected folder." Use file tools for it.
- **Cowork bash file-cache bug is real and active here.** The Linux shell silently served a *stale/truncated* copy of an edited file this session (`Part_09_Chapter_02_Server_Connection.md`) and would not refresh. **Rule: trust the file tools (Read/Write/Edit/Grep) as ground truth; use bash only to RUN scripts, and re-verify any edited file's effect via the file tools or on Windows.** Don't waste a session re-diagnosing this.

## 4. What Claude #1 already changed (do NOT redo)

All in `build files/`. Source files on disk are correct.

- **`chapters/Part_09_Chapter_02_Server_Connection.md`** — fixed server-trait paths (`OpenRA.Game/Server/TraitInterfaces.cs`, `OpenRA.Mods.Common/ServerTraits/*.cs`, `OpenRA.Game/Server/`); rewrote the `Slot`/`Client` field model (`Race`→`Faction`, removed bogus `Slot.ClientIndex`); removed nonexistent `IClientDisconnected`; minor wording.
- **`chapters/Part_08_Chapter_02_Bot_Modules.md`** — removed nonexistent `ExternalCaptures` (now "the `Captures` trait").
- **`appendices/Appendix_H_Advanced_Modding_Walkthroughs.md`** — **Walkthrough 2 Lua mission:** fixed `LuaScript` block to `Scripts: campaign.lua, utils.lua, map.lua` (was `Script: map.lua`, a mission-breaking error); added explanation + pitfall.
- **Logs updated:** `DEVELOPMENT_LOG.md` and `PRODUCTION_HANDOFF.md`.

Snippets confirmed **correct, no change**: Part 0 C# trait, Appendix E Recipe 6 C#, Appendix H Chrome UI C#, Appendix H crate/capture/resource YAML, Part 2.4 weapon/actor YAML, full trait-name scan.

## 5. Remaining technical work — RUNBOOK (Windows + .NET, ~30–60 min)

Optional confidence pass. None of this blocks publishing a v1.0 of a living document — it upgrades the snippet checks from "statically verified" to "engine-confirmed."

**Prerequisites (one time):**
- Install the **.NET 8 SDK** (the engine targets `net8.0`; there is no `global.json` pinning a patch version).
- Open a terminal in the source clone: `...\OpenRA GitHub Repositories\OpenRA`.
- Build once: `make.cmd all` (or `.\make.ps1 all`). The utility/launcher scripts call `bin\OpenRA.Utility.exe` after this builds.

**Step A — YAML snippets (`--check-yaml`):**
1. Create a throwaway test map: `mods\ra\maps\manual-test\`.
2. Add a minimal `map.yaml` (copy any existing small map's header) plus `rules.yaml` / `weapons.yaml` and paste the snippets you want to validate (Appendix E recipes, Appendix H walkthroughs, Part 2.4, Part 10.3).
3. Run: `utility.cmd ra --check-yaml`  (this validates the `ra` mod **and** its installed maps). Fix any reported field/trait errors. Delete the test map when done.

**Step B — C# custom traits (compile = API confirmation):**
- Quick path: drop each of the 3 snippets (Part 0 `GrantConditionOnLowHealth`, Appendix E Recipe 6 `CashOnCreated`, Appendix H Chrome UI `MyPanelLogic`/`MyPanelHotkeyLogic`) into `OpenRA.Mods.Common\Traits\` (or `...\Widgets\Logic\`), adjust the namespace to `OpenRA.Mods.Common.*`, then run `make.cmd all`. If it compiles, the APIs are valid. Remove the files afterward.
- Clean path: scaffold a real mod with the **OpenRA Mod SDK** (https://github.com/OpenRA/OpenRAModSDK), put the traits in its assembly, list it under `Assemblies:` in `mod.yaml`, and build. (This is what the manual's Part 3 documents.)

**Step C — Lua mission (load + play):**
1. Make `mods\ra\maps\manual-mission\` with the Appendix H Walkthrough 2 `map.yaml`, the `rules.yaml` containing `World: LuaScript: Scripts: campaign.lua, utils.lua, map.lua`, and `map.lua`.
2. `utility.cmd ra --check-yaml` to validate, then `launch-game.cmd` → Maps → start it. Confirm `WorldLoaded` runs, the objective appears, the attack wave arrives after the delay, and win/lose triggers fire. (Should load now that the `Scripts:` field is fixed.)

**Note for balance drift over time (you flagged this):** balance updates change YAML *values* (cost, damage, reload), not trait/field *names* or APIs — which is what this manual documents and which are far more stable. Re-running Step A periodically against a newer checkout is enough to catch the rare structural rename; you don't need a full re-verification each time.

## 6. Verification commands + expected output

```powershell
cd "...\OpenRA Manual\build files"
python assemble_manual.py
python verify_paths.py
python verify_internal_links.py
```
Expect on Windows (now that **Appendix I** is wired in): **56 chapters; ~1,38x,xxx bytes (CRLF); ~1,739 links / 0 broken; ~275–276 paths / 0 missing.**
Notes:
- Link count jumps because Appendix I adds **190 cameo image links + 3 cross-refs** (1,546 → ~1,739). All were verified to resolve in isolation (placeholders exist).
- Path count may shift ±1–2 vs the old 275 because of the Part 9.2 path corrections; the key is **0 missing / 0 broken**. The old "1 missing" `ServerTraits/...` artifact is gone.
- **In-sandbox full re-assembly is blocked** by the file-cache bug (bash sees a truncated copy of files edited via the file tools, including `assemble_manual.py`). The host files are correct; just run the three commands on Windows. Appendix I itself was written via the shell and verified clean.
- Before/after the cameo extraction the counts are identical — placeholders and real cameos live at the same paths.

## 7. Optional / low-priority leftovers

- **118 bare ASCII-diagram code fences** could be tagged ` ```text ` for consistency (cosmetic; they render fine bare). Deferred deliberately.
- **Glossary completeness (P2):** linking is maintained from prior sessions; a deeper term-by-term pass is optional.
- **Self-assessment prompts (P3):** still absent; optional for learners.

## 7b. Actor Reference (Appendix I) — BUILT and in v1.0 (cameos pending one Windows run)

This is now a real appendix: **`appendices/Appendix_I_Actor_Reference.md`** — auto-generated deep tables (cameo, codename, name, faction, cost, HP, armor, speed, sight, weapons, notable traits) for every buildable actor in the three bundled mods (**ra 91, cnc 54, d2k 45 = 190 actors**). Wired into `assemble_manual.py` (now 56 files) and `MASTER_INDEX.md`. Independently verified link-valid (190 cameo links + cross-refs, 0 broken).

**Pipeline (all in `build files/`):**
- `generate_actor_reference.py` — re-runnable generator. Parses each mod's `rules/*.yaml` (resolves `Inherits:`) + `fluent/rules.ftl`, rewrites the appendix, regenerates the placeholder cameos, and writes `actor_manifest.json`. Set `OPENRA_SRC` to the engine source path.
- `actor_manifest.json` — the actor code list per mod (input to the extractor).
- `extract_cameos.ps1` — **the one Windows step that makes sprites real.** Uses `OpenRA.Utility.exe <mod> --resolved-sequences <code>` to find each actor's `icon` sequence, then `--png <file> <palette>` to export it to `images/actors/<mod>/<code>.png`, overwriting placeholders. Palettes: ra/cnc `temperat.pal`, d2k `PALETTE.BIN` (d2k cameos are frames in a shared `DATA.R16` container — the script prints the frame index to pick).

**Current state of the cameos:** every slot holds a **faction-tinted placeholder PNG** (labelled box) so the manual renders and verifies now. Run `extract_cameos.ps1` once on a machine with the ra/cnc/d2k content installed to replace all 190 with real cameos. **This is the remaining step to fully satisfy "sprites in v1.0."**

**Licensing (settled, not legal advice):** OpenRA's own art is openly licensed; the classic Westwood/EA cameos are freeware game content, not open-licensed — using them in this free, non-commercial, educational manual is a fair-use call. Keep the appendix's built-in "attribute to owners + not endorsed by EA" note. The user has accepted this and wants the cameos in.

**Possible v1.1 extensions:** per-actor weapon stat expansion (damage/range/ROF pulled from `weapons/*.yaml`), tech-tree/prerequisite graphs, and a later *separate* Cameo-mod "layered" edition (explicitly out of scope for this OpenRA-only manual).

## 8. Then: Claude #2 — Visual assets & export (the big remaining phase)

Not started. See `PRODUCTION_HANDOFF.md` → "Claude #2" table: audit/replace 340 SVG diagrams, add screenshots + accent art, standardize diagram style, verify alt text, then choose output format and export (Markdown/DOCX/PDF/web), license + README, distribution. **Do the visual pass only after the §5 engine checks pass.** Do not embed copyrighted Westwood/EA art.
