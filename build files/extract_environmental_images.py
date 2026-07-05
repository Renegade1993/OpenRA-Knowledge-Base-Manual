#!/usr/bin/env python3
"""Extract real environmental-actor sprites from the installed OpenRA game content.

Reads the environmental actor manifest produced by
`generate_environmental_actor_reference.py`, tries to render each actor's world
sprite with `OpenRA.Utility.exe --export-sequence-frame`, and overwrites the
placeholder PNGs under `images/environmental/<mod>/`. Actors whose
content is missing or whose sequence cannot be resolved keep their placeholder.

Run after `generate_environmental_actor_reference.py`.
"""
import os, json, subprocess, sys
from pathlib import Path
from collections import defaultdict
from PIL import Image

ENGINE_DIR = Path("C:/Users/Kmoney/Documents/AI Projects/Cameo Work/Game Sources and Development Reference Materials/OpenRA GitHub Repositories/OpenRA")
MANUAL_DIR = Path("C:/Users/Kmoney/Documents/AI Projects/Cameo Work/Game Sources and Development Reference Materials/OpenRA Manual")
BUILD = MANUAL_DIR / "build files"
MANIFEST = BUILD / "environmental_actor_manifest.json"
IMAGES = MANUAL_DIR / "images" / "environmental"
UTILITY = ENGINE_DIR / "bin" / "OpenRA.Utility.exe"
FORCE = "--force" in sys.argv

# Maximum size for a preview image; larger sprites (e.g. bridge terrain templates) are
# downscaled so the reference table stays compact.
PREVIEW_MAX_SIZE = 128

# Palette used for sidebar/cameo icon sequences when an actor has no in-world sprite.
CHROME_PALETTE = "chrome"

DEFAULT_TILESET = {
    "ra": "TEMPERAT",
    "cnc": "TEMPERAT",
    "d2k": "ARRAKIS",
    "ts": "TEMPERATE",
}

# Known tilesets for each mod, used to pick a fallback when the default is excluded.
MOD_TILESETS = {
    "ra": ["TEMPERAT", "SNOW", "DESERT", "INTERIOR"],
    "cnc": ["TEMPERAT", "SNOW", "DESERT", "WINTER"],
    "d2k": ["ARRAKIS"],
    "ts": ["TEMPERATE", "SNOW"],
}

# Derived palette names that are not backed by PaletteFromFile and should be mapped to their base palette.
DERIVED_PALETTE_FALLBACK = {
    "greentiberium": "player",
    "bluetiberium": "player",
    "civilian2": "player",
    "civilian4": "player",
    "civilian5": "player",
    "civilian6": "player",
    "civilian7": "player",
    "civilian8": "player",
    "civilian9": "player",
    "civilian10": "player",
    "player-nomuzzle": "player",
    "player-nobright": "player",
}

# Some mods define the player palette as a derived palette without a PaletteFromFile entry.
# In those mods we must pass the base palette name to the utility.
PLAYER_PALETTE_FALLBACK = {
    "ra": "player",      # PaletteFromFile@player exists
    "cnc": "terrain",    # player is a PlayerColorPalette derived from terrain
    "d2k": "d2k",        # player is a PlayerColorPalette derived from d2k
    "ts": "player",      # PaletteFromFile@playertem/playersno exist
}

# Body traits that can override the palette used by RenderSprites.
BODY_PALETTE_TRAITS = {
    "WithInfantryBody": "Palette",
    "WithSplitAttackPaletteInfantryBody": "Palette",
    "WithSpriteBody": "Palette",
    "WithFacingSpriteBody": "Palette",
    "WithVoxelBody": "Palette",
}

# D2K uses non-standard sequence names for some environmental actors.
D2K_SEQUENCE_OVERRIDES = {
    "spicebloom": "grow0",
    "sandworm": "mouth",
}

# Rules that indicate an infantry-style actor should use the "stand" sequence.
INFANTRY_TRAITS = {"WithInfantryBody", "TakeCover"}


def tileset_for_actor(mod, code, resolved):
    """Pick the best tileset for this actor from its MapEditorData restrictions."""
    med = resolved.get("MapEditorData", {})
    if not isinstance(med, dict):
        med = {}

    req = med.get("RequireTilesets", "")
    if req:
        return req.split(",")[0].strip().upper()

    excl = med.get("ExcludeTilesets", "")
    default = DEFAULT_TILESET[mod]
    if excl:
        excluded = {x.strip().upper() for x in excl.split(",") if x.strip()}
        if default not in excluded:
            return default
        for tileset in MOD_TILESETS.get(mod, []):
            if tileset not in excluded:
                return tileset

    return default


def is_unit_actor(resolved):
    """Return True if the actor is mobile infantry/vehicle/aircraft (uses player palette)."""
    return any(t in resolved for t in ("Mobile", "Aircraft", "WithInfantryBody"))


def is_terrain_actor(resolved, templates):
    """Return True for terrain/destructible/building decorations (trees, rocks, ice, walls, civilian buildings, etc.)."""
    if is_unit_actor(resolved):
        return False
    if "Terrain" in resolved:
        return True
    if templates:
        terrain_templates = {
            "^Tree", "^Rock", "^Wall", "^DestroyableTile", "^DestroyedTile", "^TreeHusk", "^TibTree",
            "^CivBuilding", "^CivBuildingHusk", "^TechBuilding", "^BasicBuilding", "^Building",
        }
        if terrain_templates & set(templates):
            return True
    return False


def palette_for_actor(mod, code, resolved, templates):
    """Pick the palette that this actor's body sequence is rendered with.

    OpenRA's RenderSprites trait defaults to the player palette when no explicit
    Palette is set. Most environmental actors override this to terrain,
    terraindecoration, desert, etc., so we read the resolved actor rules.
    Body traits such as WithInfantryBody can also override the palette.

    Terrain-like environmental actors (trees, rocks, ice, tank traps, walls,
    destructible tiles) must use the tileset terrain palette rather than the
    player/chrome palette, which gives them a blueish tint.
    """
    palettes = []
    rs = resolved.get("RenderSprites", {})
    if isinstance(rs, dict):
        p = rs.get("Palette")
        if p:
            palettes.append(p)

    for trait, key in BODY_PALETTE_TRAITS.items():
        t = resolved.get(trait, {})
        if isinstance(t, dict):
            p = t.get(key)
            if p:
                palettes.append(p)

    if palettes:
        # Use the first explicit palette found.
        p = palettes[0]
        p = DERIVED_PALETTE_FALLBACK.get(p, p)
    else:
        # RenderSprites default is player palette; some mods need the base palette name.
        p = PLAYER_PALETTE_FALLBACK.get(mod, "player")

    # Force terrain palette for terrain/destructible actors that would otherwise
    # render with a unit/chrome palette (causes blueish tint in the PDF).
    if is_terrain_actor(resolved, templates) and (p == "player" or p == "chrome" or p.startswith("player-")):
        return "d2k" if mod == "d2k" else "terrain"

    return p


def sequence_for(mod, code, resolved):
    """Pick the best sequence name to export for this actor.

    The OpenRA Utility's `@unit` auto-mode picks the in-world body sequence
    (idle/stand), composites building roof/tower overlays, and drops shadow
    pixels to transparent.  This is almost always what we want for the
    preview matrix.  D2K spicebloom/sandworm need explicit sequences because
    their real animation names are not in the auto-pick list.
    """
    lower = code.lower()
    if mod == "d2k" and lower in D2K_SEQUENCE_OVERRIDES:
        return D2K_SEQUENCE_OVERRIDES[lower]
    return "@unit"


def image_name(code, resolved):
    """Return the sprite image name for the actor.

    Sequence image keys are case-insensitive in the engine but the utility's
    lookup is case-sensitive, so we always return a lowercase name.
    """
    rs = resolved.get("RenderSprites", {})
    if isinstance(rs, dict) and rs.get("Image"):
        return rs["Image"].lower()
    return code.lower()


def run_utility(mod, image, sequence, outfile, tileset, palette):
    """Invoke OpenRA.Utility.exe --export-sequence-frame."""
    env = os.environ.copy()
    env["ENGINE_DIR"] = str(ENGINE_DIR)
    env["MOD_SEARCH_PATHS"] = str(ENGINE_DIR / "mods")
    cmd = [str(UTILITY), mod, "--export-sequence-frame", image, sequence, str(outfile), tileset, palette]
    try:
        result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=30, check=True)
        return True, result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return False, (e.stdout.strip() + " " + e.stderr.strip()).strip()
    except subprocess.TimeoutExpired:
        return False, "timeout"


def run_utility_terrain_template(mod, tileset, template_id, outfile):
    """Invoke OpenRA.Utility.exe --export-terrain-template for a bridge template."""
    env = os.environ.copy()
    env["ENGINE_DIR"] = str(ENGINE_DIR)
    env["MOD_SEARCH_PATHS"] = str(ENGINE_DIR / "mods")
    cmd = [str(UTILITY), mod, "--export-terrain-template", tileset, str(template_id), str(outfile)]
    try:
        result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=30, check=True)
        return True, result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return False, (e.stdout.strip() + " " + e.stderr.strip()).strip()
    except subprocess.TimeoutExpired:
        return False, "timeout"


def resize_to_preview(path, max_size=PREVIEW_MAX_SIZE):
    """Resize an image so its longest side is at most max_size, preserving aspect ratio."""
    try:
        img = Image.open(path)
        if img.width == 0 or img.height == 0:
            return False
        max_dim = max(img.width, img.height)
        if max_dim <= max_size:
            return False
        scale = max_size / max_dim
        new_size = (int(img.width * scale), int(img.height * scale))
        if img.mode == "P":
            img = img.convert("RGBA")
        img = img.resize(new_size, Image.NEAREST)
        img.save(path)
        return True
    except Exception:
        return False


def bridge_template_for_actor(resolved):
    """Return the bridge terrain template id if the actor is a classic bridge."""
    bridge = resolved.get("Bridge")
    if not isinstance(bridge, dict):
        return None
    return bridge.get("Template")


def try_bridge_template(mod, code, resolved, outfile):
    """Try to export a classic bridge actor using the terrain template command.

    Some bridge templates are only defined for a specific tileset (e.g. RA/CnC
    desert bridges), so we try the actor's preferred tileset first and then
    fall back to every other tileset known for the mod.
    """
    template_id = bridge_template_for_actor(resolved)
    if template_id is None:
        return False, "not a bridge"

    preferred = tileset_for_actor(mod, code, resolved)
    candidates = [preferred] + [t for t in MOD_TILESETS.get(mod, []) if t != preferred]
    last_msg = ""
    for tileset in candidates:
        ok, last_msg = run_utility_terrain_template(mod, tileset, template_id, outfile)
        if ok:
            resize_to_preview(outfile, PREVIEW_MAX_SIZE)
            return True, last_msg
    return False, last_msg


def load_resolved_mod(mod):
    """Load rules and return a dict of resolved actors and inherited templates."""
    sys.path.insert(0, str(BUILD))
    from generate_environmental_actor_reference import load_mod, resolve, inherited_templates
    actors, _ = load_mod(mod)
    resolved = {n: resolve(n, actors) for n in actors}
    templates = {n: inherited_templates(n, actors) for n in actors}
    return resolved, templates


def main():
    if not MANIFEST.exists():
        print(f"Manifest not found: {MANIFEST}")
        print("Run generate_environmental_actor_reference.py first.")
        raise SystemExit(1)

    with open(MANIFEST, encoding="utf-8") as f:
        manifest = json.load(f)

    resolved_mods = {}
    templates_mods = {}
    for mod in manifest:
        resolved_mods[mod], templates_mods[mod] = load_resolved_mod(mod)

    generated = defaultdict(list)
    failed = defaultdict(list)
    skipped = 0

    for mod, codes in manifest.items():
        mod_dir = IMAGES / mod
        mod_dir.mkdir(parents=True, exist_ok=True)
        resolved_actors = resolved_mods[mod]
        templates_actors = templates_mods[mod]

        for code in codes:
            outfile = mod_dir / f"{code.lower()}.png"
            if not FORCE and outfile.exists():
                # Don't re-render if a real sprite already exists (bigger than the 48x48 placeholder).
                size = outfile.stat().st_size
                if size > 5000:
                    skipped += 1
                    continue

            resolved = resolved_actors.get(code, {})
            templates = templates_actors.get(code, set())
            image = image_name(code, resolved)
            sequence = sequence_for(mod, code, resolved)
            tileset = tileset_for_actor(mod, code, resolved)
            palette = palette_for_actor(mod, code, resolved, templates)

            ok = False
            msg = ""

            # Classic bridges (RA/CnC) are rendered as terrain templates, not sequences.
            ok, msg = try_bridge_template(mod, code, resolved, outfile)

            if not ok:
                ok, msg = run_utility(mod, image, sequence, outfile, tileset, palette)

            if not ok:
                # Fallback sequences for actors without a usable body frame:
                # - editor (TS bridge placeholders)
                # - icon (sidebar cameo for voxel-only units)
                for fb_seq, fb_pal in (("editor", palette), ("icon", CHROME_PALETTE)):
                    ok, msg = run_utility(mod, image, fb_seq, outfile, tileset, fb_pal)
                    if ok:
                        break

            if ok:
                resize_to_preview(outfile, PREVIEW_MAX_SIZE)
                generated[mod].append(code)
            else:
                failed[mod].append((code, image, sequence, tileset, palette, msg))

    print("Extraction complete.")
    total_gen = sum(len(v) for v in generated.values())
    total_fail = sum(len(v) for v in failed.values())
    print(f"Generated: {total_gen}  Failed: {total_fail}  Skipped: {skipped}")
    for mod in manifest:
        print(f"  {mod}: generated={len(generated.get(mod, []))} failed={len(failed.get(mod, []))}")
    if failed:
        print("\nSample failures:")
        for mod, items in failed.items():
            for code, image, sequence, tileset, palette, msg in items[:3]:
                print(f"  {mod}/{code} ({image}/{sequence} ts={tileset} pal={palette}): {msg[:120]}")

    # Upscale small environmental sprites so they remain visible in the PDF.
    rescale_script = BUILD / "rescale_environmental_images.py"
    if rescale_script.exists():
        print("\nRescaling environmental previews...")
        subprocess.run([sys.executable, str(rescale_script)], check=False)


if __name__ == "__main__":
    main()
