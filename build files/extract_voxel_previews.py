#!/usr/bin/env python3
"""Render previews for Tiberian Sun voxel-only units.

OpenRA's TS voxel actors (ICBM, BUS, PICK, CAR, WINI, TRUCKA, TRUCKB, 4TNK) have no SHP
sprite sequences, so the normal --export-sequence-frame utility can't produce a preview.
This script calls the custom --export-voxel-frame utility command, which reads the
original .vxl/.hva files and renders a simple orthographic projection.

Run after extract_environmental_images.py. It only overwrites placeholder PNGs for the
listed TS voxel units.
"""
import os, subprocess, sys
from pathlib import Path
from PIL import Image

ENGINE_DIR = Path("C:/Users/Kmoney/Documents/AI Projects/Cameo Work/Game Sources and Development Reference Materials/OpenRA GitHub Repositories/OpenRA")
MANUAL_DIR = Path("C:/Users/Kmoney/Documents/AI Projects/Cameo Work/Game Sources and Development Reference Materials/OpenRA Manual")
OUT_DIR = MANUAL_DIR / "images" / "environmental" / "ts"
UTILITY = ENGINE_DIR / "bin" / "OpenRA.Utility.exe"
PREVIEW_MAX_SIZE = 64

# TS units that are voxel-only (no SHP sequences) and need a VXL render.
TS_VOXEL_UNITS = ["icbm", "bus", "pick", "car", "wini", "trucka", "truckb", "4tnk"]

# Default tileset palette mapping for TS voxel color indices.
PALETTE_FOR_TILESET = {
    "TEMPERATE": "unittem.pal",
    "SNOW": "unitsno.pal",
}


def resize_to_preview(path, max_size=PREVIEW_MAX_SIZE):
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


def render_voxel_unit(code, tileset, out_dir):
    outfile = out_dir / f"{code}.png"
    palette = PALETTE_FOR_TILESET.get(tileset, "unittem.pal")
    env = os.environ.copy()
    env["ENGINE_DIR"] = str(ENGINE_DIR)
    env["MOD_SEARCH_PATHS"] = str(ENGINE_DIR / "mods")
    cmd = [str(UTILITY), "ts", "--export-voxel-frame", code, str(outfile), palette]
    try:
        result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=60, check=True)
        resize_to_preview(outfile, PREVIEW_MAX_SIZE)
        return True, result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return False, (e.stdout.strip() + " " + e.stderr.strip()).strip()
    except subprocess.TimeoutExpired:
        return False, "timeout"


def main():
    if not UTILITY.exists():
        print(f"OpenRA.Utility.exe not found: {UTILITY}")
        sys.exit(1)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    generated = []
    failed = []
    for code in TS_VOXEL_UNITS:
        ok, msg = render_voxel_unit(code, "TEMPERATE", OUT_DIR)
        if ok:
            generated.append(code)
        else:
            failed.append((code, msg))
            print(f"  {code}: failed ({msg[:120]})")

    print(f"Voxel previews: {len(generated)}/{len(TS_VOXEL_UNITS)} rendered")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
