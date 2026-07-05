# Engine-Execution Runbook — OpenRA Manual v1.0

**Why you're running this and not Claude:** the work sandbox has no .NET / mono / msbuild, so the
engine can't be built or run there. These four parts confirm the manual's code snippets actually
compile and load against the pinned engine. Run on Windows, then paste the output back to Claude to verify.

**Pinned engine (already checked out):**
`...\OpenRA GitHub Repositories\OpenRA` @ `972c10ec80f90a30a4fa80abfebc633af3365847`
(`playtest-20260222-76-g972c10ec80`). Don't change the checkout.

**Time:** ~30–60 min total. Parts 1–3 are the high-value checks; Part 4 (C# compile) is optional confidence.

> Tip: copy each block of commands into **PowerShell**. Paste me the **last ~30 lines** of each part's
> output (especially anything containing `Error`, `Exception`, `Warning`, or `Failed`).

---

## Part 0 — One-time prerequisites

1. Install the **.NET 8 SDK** (https://dotnet.microsoft.com/download/dotnet/8.0). Verify:

   ```powershell
   dotnet --list-sdks      # expect at least one 8.x.x entry
   ```

2. Build the engine once:

   ```powershell
   cd "C:\Users\Kmoney\Documents\AI Projects\Cameo Work\Game Sources and Development Reference Materials\OpenRA GitHub Repositories\OpenRA"
   .\make.cmd all
   ```

   **Expected:** ends with `Build succeeded` and no errors. `bin\OpenRA.Utility.exe` now exists.
   **Paste me:** the final 15–20 lines (the success/failure summary).

3. (Needed only for Part 3 play-test and later cameo extraction) Launch RA once so OpenRA downloads
   the original game content: `.\launch-game.cmd` → let it fetch content → quit. For cnc/d2k later,
   launch those mods once too.

---

## Part 1 — Baseline YAML validation (highest value, ~5 min)

Validates that the engine parses each mod's full ruleset **and all bundled maps** at this commit. This
is the single strongest signal that the trait/field names the manual documents are valid here.

```powershell
cd "C:\Users\Kmoney\Documents\AI Projects\Cameo Work\Game Sources and Development Reference Materials\OpenRA GitHub Repositories\OpenRA"
.\utility.cmd ra  --check-yaml
.\utility.cmd cnc --check-yaml
.\utility.cmd d2k --check-yaml
```

**Expected:** each command prints validation progress and returns with **no `Error`/`Exception`** lines.
**Paste me:** the tail of each, or just confirm "all three clean."

---

## Part 2 — Snippet-specific YAML validation (~15 min)

Confirms the manual's *custom* YAML examples (crates, resources, cloak, capture, AI, etc.) parse, not
just the shipping rules. Easiest reliable method uses a throwaway map per mod.

1. Launch RA (`.\launch-game.cmd`) → **Map Editor** → **New Map** → Tileset **TEMPERAT**, size
   **96 x 96** → Save as `manual-test`. (This creates a valid map with the binary data the validator needs.)
2. Open the new map folder:
   `C:\Users\Kmoney\AppData\Roaming\OpenRA\maps\ra\manual-test\` and create/append a `rules.yaml`.
3. Paste the snippet blocks you want to check from **`yaml-snippets.md`** (next to this file) into that
   `rules.yaml` (and `weapons.yaml` for the weapon block). Make sure `map.yaml` lists them under
   `Rules:` / `Weapons:` — the editor usually adds `Rules: rules.yaml` automatically; if not, add it.
4. Validate:

   ```powershell
   cd "C:\Users\Kmoney\Documents\AI Projects\Cameo Work\Game Sources and Development Reference Materials\OpenRA GitHub Repositories\OpenRA"
   .\utility.cmd ra --check-yaml
   ```

   (`--check-yaml` validates the mod **and** its installed maps, so it picks up `manual-test`.)
5. Delete the `manual-test` map when done.

**Expected:** no errors referencing `manual-test`.
**Paste me:** any error lines mentioning the test map (or "clean").

> If hand-building the test map is too fiddly, **Part 1 alone is acceptable** for v1.0 — it already
> proves every trait/field name in the snippets exists in this engine, since the snippets are built
> from these same rules. Part 2 only adds "these exact example blocks parse as written."

---

## Part 3 — Lua mission load + play (~10 min)

Confirms the Appendix G Walkthrough 2 mission (whose `Scripts:` field was bug-fixed last session) loads
and runs. Files are prepared in **`lua-mission\`** next to this runbook.

1. In the Map Editor, **New Map** → TEMPERAT, **96 x 96**, save as `manual-mission`.
2. Go to `C:\Users\Kmoney\AppData\Roaming\OpenRA\maps\ra\manual-mission\` and copy in:
   - `lua-mission\map.yaml` (replace the generated one). It loads the campaign rules (`campaign-rules.yaml`, `campaign-tooltips.yaml`, `campaign-palettes.yaml`) plus the map's own `rules.yaml`.
   - `lua-mission\rules.yaml`,
   - `lua-mission\map.lua`,
   - `lua-mission\map.ftl` (required for the objective text and mission briefing to display correctly).
   - Optional: also copy `lua-mission\campaign.lua` and `lua-mission\utils.lua` if you want the test pack to be self-contained; otherwise the engine loads them from the RA mod's scripts.
3. Validate, then launch:

   ```powershell
   cd "C:\Users\Kmoney\Documents\AI Projects\Cameo Work\Game Sources and Development Reference Materials\OpenRA GitHub Repositories\OpenRA"
   .\utility.cmd ra --check-yaml
   .\launch-game.cmd
   ```

4. In game: **Single Player → Missions** (or Skirmish → select `manual-mission`). Confirm:
   - the map loads with **no Lua "nil value" error** (this is the fix being verified),
   - the **mission briefing** reads "Destroy the German weapons factory to win the mission..." (not a briefing from another mission),
   - the **objective** reads "Destroy the German weapons factory." (not the raw key `destroy-enemy-factory`),
   - after ~2 min an **attack wave** (e1 e1 e3 2tnk) arrives from the NE corner,
   - destroying the German `weap` **wins**; losing your `fact` **loses**.

**Paste me:** "loads clean + objective shows" at minimum. If it errors on load, paste the exact Lua error
and the game log at `C:\Users\Kmoney\AppData\Roaming\OpenRA\Logs\` (`lua.log` / `exception.log`).

> Geometry caveat: the prepared `map.yaml` places actors at fixed cells on a 96x96/Bounds 16,16,64,64
> map. If the editor map differs, nudge MapSize/Bounds to match or move an actor that landed off-bounds.
> The *load + objective + Scripts:* check is the real goal; the full play-through is a bonus.

---

## Part 4 — C# custom-trait compile (optional, ~15 min)

Compiling = proof the C# APIs in the manual exist at this commit. Quick path drops the snippets into the
engine's own assembly. Files are prepared in **`csharp\`** with namespaces already adjusted.

1. Copy into the engine source:
   - `csharp\GrantConditionOnLowHealth.cs`  →  `OpenRA.Mods.Common\Traits\`
   - `csharp\CashOnCreated.cs`               →  `OpenRA.Mods.Common\Traits\`
   - `csharp\MyPanelLogic.cs`                →  `OpenRA.Mods.Common\Widgets\Logic\`
   - `csharp\MyPanelHotkeyLogic.cs`          →  `OpenRA.Mods.Common\Widgets\Logic\`
2. Rebuild:

   ```powershell
   cd "C:\Users\Kmoney\Documents\AI Projects\Cameo Work\Game Sources and Development Reference Materials\OpenRA GitHub Repositories\OpenRA"
   .\make.cmd all
   ```

3. **Delete all four files** from the engine source afterward (keep the checkout clean).

**Expected:** `Build succeeded`. If it compiles, the trait/widget APIs are confirmed.
**Paste me:** `Build succeeded`, or the exact compiler errors (`CSxxxx`) — those tell me precisely which
API in a snippet is wrong so I can fix the manual.

---

## After all parts

Paste the outputs here. Claude will confirm each check and update `DEVELOPMENT_LOG.md` /
`PRODUCTION_HANDOFF.md`. Once green, the next step is the **cameo extraction** (`extract_cameos.ps1`,
which also needs this built engine) and then the Claude #2 visual/export pass.
