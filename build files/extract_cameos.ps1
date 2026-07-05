<#
  extract_cameos.ps1 — render real actor cameos for Appendix I.

  Replaces the faction-tinted PLACEHOLDER images under images/actors/<mod>/<code>.png
  with the real build-palette cameos rendered from the installed game content.

  WHY THIS RUNS ON WINDOWS (not in the doc sandbox): cameos are rendered from the original
  game art, which is downloaded/installed with the OpenRA content — it is not in the engine
  source, so it cannot be bundled with the manual.

  PREREQUISITES
    * .NET 8 SDK, and a built OpenRA engine  (run  make.cmd all  in the engine source once).
    * The ra, cnc, and d2k content installed (launch each mod once so OpenRA fetches it).
    * Run from the engine source root, or pass -EngineDir pointing to the folder with bin\OpenRA.Utility.exe.
    * For D2K, the engine must include the custom `--export-sequence-frame` utility command
      (provided by `OpenRA.Mods.Common/UtilityCommands/ExportSequenceFrameCommand.cs` in this
      repository's pinned engine source).

  USAGE
    powershell -ExecutionPolicy Bypass -File extract_cameos.ps1 `
        -EngineDir "C:\...\OpenRA GitHub Repositories\OpenRA" `
        -ManualDir "C:\...\OpenRA Manual"

  HOW IT WORKS
    For each actor code in actor_manifest.json it exports TWO images via the custom
    `--export-sequence-frame` utility command:
      1. The `icon` sequence -> images\actors\<mod>\<code>.png       (sidebar / construction-menu cameo)
      2. The `@unit` auto-pick  -> images\actors\<mod>\<code>_unit.png (in-world battlefield sprite:
         first available of idle / stand / ... )

    Tileset per mod: ra=TEMPERAT, cnc=TEMPERAT, d2k=ARRAKIS.
    Palette per mod (indexed SHP frames only): ra=temperat.pal, cnc=temperat.pal, d2k=PALETTE.BIN.

  NOTE ON RENDERING
    The custom `--export-sequence-frame` command reads the raw sprite frame DIRECTLY (no texture-sheet
    round trip), so colours are exact and nothing is cropped. Indexed SHP frames (RA/CNC) are coloured
    with the supplied palette; truecolour D2K R16 frames carry their own colour already (this is what
    fixed the earlier purple/blue D2K cameos, which were a red<->blue channel swap from the sheet path).

  NOTE ON ART/LICENSING
    The classic Westwood/EA cameos are freeware game content, not openly licensed. Use them in
    this free, non-commercial, educational manual as fair-use reference; attribute to their
    owners and include a "not endorsed by or affiliated with EA" notice when publishing.
#>

param(
  [string]$EngineDir = (Get-Location).Path,
  [string]$ManualDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
)

$ErrorActionPreference = "Stop"
$utilityExe = Join-Path $EngineDir "bin\OpenRA.Utility.exe"
$manifest = Join-Path $PSScriptRoot "actor_manifest.json"
$iconPalettes = @{ ra = "chrome"; cnc = "chrome"; d2k = "chrome"; ts = "chrome" }
$unitPalettes = @{ ra = "player"; cnc = "terrain"; d2k = "d2k"; ts = "player" }
# CNC's TRUCK uses a custom SHP icon (truckicon.shp) instead of the usual *.icnh.tem
# chrome icons.  Render it with the terrain unit palette: the chrome palette renders
# the icon's transparent pixels as opaque white, which leaves heavy white haloing
# around the truck in the manual.  Terrain gives the same icon with a transparent
# background.
$iconPaletteOverrides = @{ "cnc" = @{ "truck" = "terrain" } }

if (-not (Test-Path $utilityExe)) { throw "OpenRA.Utility.exe not found in $EngineDir\bin. Build the engine (make.cmd all) and pass -EngineDir." }
$env:ENGINE_DIR = $EngineDir
if (-not (Test-Path $manifest)) { throw "actor_manifest.json not found next to this script." }

$data = Get-Content $manifest -Raw | ConvertFrom-Json

# D2K actor names often do not match the sequence image (e.g. construction_yard -> conyard.ordos),
# so for D2K we try the actor name first, then this known fallback mapping.
$d2kImageMap = @{
  "construction_yard" = "conyard.ordos"
  "wind_trap"         = "power.ordos"
  "barracks"          = "barracks.ordos"
  "refinery"          = "refinery.ordos"
  "silo"              = "silo.ordos"
  "light_factory"     = "light.ordos"
  "heavy_factory"     = "heavy.ordos"
  "outpost"           = "outpost.ordos"
  "starport"          = "starport.ordos"
  "repair_pad"        = "repair_pad.ordos"
  "high_tech_factory" = "hightech.ordos"
  "research_centre"   = "research.ordos"
  "palace"            = "palace.ordos"
  "mpsardaukar"       = "sardaukar"
  "nsfremen"          = "fremen"
}

# RA fake buildings share their in-world sprite with the real building but use a separate fake-icon
# cameo sequence defined on the real building's image. Map the fake actor code to the real image.
$raFakeImageMap = @{
  "fpwr" = "powr"
  "tenf" = "tent"
  "syrf" = "syrd"
  "spef" = "spen"
  "weaf" = "weap"
  "domf" = "dome"
  "fixf" = "fix"
  "fapw" = "apwr"
  "atef" = "atek"
  "pdof" = "pdox"
  "mslf" = "mslo"
  "facf" = "fact"
}

# Export one frame; try the primary image name then the fallback. Returns $true on success.
function Export-Frame($mod, $primary, $fallback, $sequence, $outFile, $tileset, $pal) {
  try {
    & $utilityExe $mod --export-sequence-frame $primary $sequence $outFile $tileset $pal 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Utility exited with code $LASTEXITCODE" }
    return $true
  } catch {
    if ($fallback) {
      try {
        & $utilityExe $mod --export-sequence-frame $fallback $sequence $outFile $tileset $pal 2>$null | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "Utility exited with code $LASTEXITCODE" }
        return $true
      } catch { return $false }
    }
    return $false
  }
}

# Export a voxel frame for Tiberian Sun voxel-only actors (no SHP @unit sequence).
# IMAGE OUTFILE [PALETTE-FILE] ; default palette is unittem.pal.
function Export-VoxelFrame($mod, $primary, $outFile, $paletteFile = "unittem.pal") {
  try {
    & $utilityExe $mod --export-voxel-frame $primary $outFile $paletteFile 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Utility exited with code $LASTEXITCODE" }
    return $true
  } catch { return $false }
}

foreach ($mod in @("ra","cnc","d2k","ts")) {
  $entries = $data.$mod
  if (-not $entries) { continue }
  $codes = @($entries.PSObject.Properties | ForEach-Object { $_.Name })
  $outDir = Join-Path $ManualDir "images\actors\$mod"
  New-Item -ItemType Directory -Force -Path $outDir | Out-Null
  $iconPal = $iconPalettes[$mod]
  $unitPal = $unitPalettes[$mod]
  $tileset = if ($mod -eq "d2k") { "ARRAKIS" } elseif ($mod -eq "ts") { "TEMPERATE" } else { "TEMPERAT" }
  Write-Host "`n=== $mod : $($codes.Count) actors (tileset $tileset, icon-palette $iconPal, unit-palette $unitPal) ==="

  foreach ($code in $codes) {
    $img = $entries.$code

    # Fake buildings: use the real building's image for both cameo (real icon sequence) and unit (@unit).
    # The in-game fake-icon SHPs are lower-quality recolours; for the manual we render the real cameo,
    # which is the asset the fake building is meant to impersonate.
    if ($mod -eq "ra" -and $raFakeImageMap.ContainsKey($code.ToLower())) {
      $realImg = $raFakeImageMap[$code.ToLower()]
      $iconOk = Export-Frame $mod $realImg $null "icon" (Join-Path $outDir "$($code.ToLower()).png")      $tileset $iconPal
      $unitOk = Export-Frame $mod $realImg $null '@unit' (Join-Path $outDir "$($code.ToLower())_unit.png") $tileset $unitPal
    } else {
      $fallback = if ($mod -eq "d2k") { $d2kImageMap[$code.ToLower()] } else { $null }
      $unitFile = Join-Path $outDir "$($code.ToLower())_unit.png"
      $effectiveIconPal = if ($iconPaletteOverrides.ContainsKey($mod) -and $iconPaletteOverrides[$mod].ContainsKey($code.ToLower())) { $iconPaletteOverrides[$mod][$code.ToLower()] } else { $iconPal }
      if ($code.ToLower() -eq "truck") { Write-Host "DEBUG truck effectiveIconPal=$effectiveIconPal iconPal=$iconPal" }
      $iconOk = Export-Frame $mod $img $fallback "icon"  (Join-Path $outDir "$($code.ToLower()).png")      $tileset $effectiveIconPal

      # Tiberian Sun units are almost all voxel-based; prefer the orthographic voxel renderer
      # (which auto-composites turrets/barrels) and only fall back to the SHP @unit path when
      # no voxel model exists. This avoids showing the flat SHP fallback without its turret.
      if ($mod -eq "ts") {
        $voxelPalette = if ($tileset -eq "TEMPERATE") { "unittem.pal" } else { "unitsno.pal" }
        # Faction-specific SHP icons use names like mcv.gdi, but the shared voxel model is mcv.
        $voxelImg = $img -replace '\.(gdi|nod)$', ''
        $unitOk = Export-VoxelFrame $mod $voxelImg $unitFile $voxelPalette
        if (-not $unitOk) {
          $unitOk = Export-Frame $mod $img $fallback '@unit' $unitFile $tileset $unitPal
        }
      }
      else {
        $unitOk = Export-Frame $mod $img $fallback '@unit' $unitFile $tileset $unitPal
      }
    }

    $iconTag = if ($iconOk) { "icon" } else { "icon:--" }
    $unitTag = if ($unitOk) { "unit" } else { "unit:--" }
    Write-Host ("  {0,-18} {1,-8} {2,-8}" -f $code,$iconTag,$unitTag)
  }
}

# Rescale the extracted battlefield sprites so they stay readable after Pandoc's figure shrink.
$rescalingScript = Join-Path $PSScriptRoot "rescale_actor_unit_images.py"
if (Test-Path $rescalingScript) {
  py `"$rescalingScript`"
}

Write-Host "`nDone. Re-run the verification commands (assemble_manual.py, verify_paths.py, verify_internal_links.py)."
Write-Host "Slots with no art (printed as icon:-- / unit:--) keep their faction-tinted placeholder and stay link-valid."
