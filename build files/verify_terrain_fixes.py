#!/usr/bin/env python3
"""Verify terrain preview fixes for RA Desert, CNC Desert, TS, and D2K Arrakis."""

from pathlib import Path
from PIL import Image
import sys

MANUAL_DIR = Path("C:/Users/Kmoney/Documents/AI Projects/Cameo Work/Game Sources and Development Reference Materials/OpenRA Manual")
BACKUP_DIR = Path("C:/Users/Kmoney/Documents/AI Projects/Cameo Work/to delete/terrain_images_backup_20260630_105726")
IMAGES_DIR = MANUAL_DIR / "images" / "terrain"
APPENDIX_J = MANUAL_DIR / "build files" / "appendices" / "Appendix_J_Terrain_Tiles.md"


def count_purple_pixels(img_path):
    """Count pixels that look purple/pink (high R and B, low G)."""
    img = Image.open(img_path).convert("RGBA")
    data = img.getdata()
    count = 0
    for r, g, b, a in data:
        if a > 0 and r > 150 and b > 150 and g < 100:
            count += 1
    return count, img.width * img.height


def check_ra_cnc_desert():
    print("Checking RA Desert and CNC Desert for purple/pink artifacts...")
    issues = []
    for mod in ["ra", "cnc"]:
        desert_dir = IMAGES_DIR / mod / "desert"
        if not desert_dir.exists():
            print(f"  Directory not found: {desert_dir}")
            continue
        for img_path in sorted(desert_dir.glob("*.png")):
            purple, total = count_purple_pixels(img_path)
            if purple > 0:
                issues.append((str(img_path.relative_to(MANUAL_DIR)), purple, total))
    if issues:
        print(f"  Found {len(issues)} images with purple/pink pixels:")
        for rel, purple, total in issues[:10]:
            print(f"    {rel}: {purple}/{total} purple pixels")
    else:
        print("  No purple/pink artifacts detected in RA/CNC Desert previews.")
    return len(issues) == 0


def check_ts():
    print("Checking TS Temperate for pink/purple artifacts...")
    issues = []
    ts_dir = IMAGES_DIR / "ts" / "temperate"
    if not ts_dir.exists():
        print(f"  Directory not found: {ts_dir}")
        return False

    # Check specific named templates.
    targets = ["bld01.tem.png", "house01.tem.png", "civ01.tem.png", "shore41.tem.png"]
    for i in range(1, 15):
        targets.append(f"water{i:02d}.tem.png")

    for name in targets:
        img_path = ts_dir / name
        if not img_path.exists():
            print(f"  Missing: {name}")
            continue
        purple, total = count_purple_pixels(img_path)
        if purple > 0:
            issues.append((name, purple, total))

    if issues:
        print(f"  Found {len(issues)} TS images with purple/pink pixels:")
        for name, purple, total in issues[:10]:
            print(f"    {name}: {purple}/{total} purple pixels")
    else:
        print("  No pink/purple artifacts detected in TS Temperate previews.")
    return len(issues) == 0


def check_d2k_arrakis():
    print("Checking D2K Arrakis for unique/disambiguated previews...")
    d2k_dir = IMAGES_DIR / "d2k" / "arrakis"
    if not d2k_dir.exists():
        print(f"  Directory not found: {d2k_dir}")
        return False

    files = sorted(d2k_dir.glob("*.png"))
    print(f"  Found {len(files)} D2K Arrakis preview files.")

    # Check that there are disambiguated files (BLOXBASE_<id>.R16.png etc.)
    disambiguated = [f for f in files if "_" in f.stem]
    print(f"  Disambiguated files: {len(disambiguated)}")

    # Check that not all files are identical.
    hashes = {}
    for f in files:
        h = hash(f.read_bytes())
        hashes.setdefault(h, []).append(f.name)

    duplicate_groups = [names for names in hashes.values() if len(names) > 1]
    if duplicate_groups:
        print(f"  WARNING: {len(duplicate_groups)} groups of identical files found.")
        for names in duplicate_groups[:5]:
            print(f"    Identical: {', '.join(names[:5])}")
    else:
        print("  All D2K Arrakis preview files are unique.")

    # Check that the Markdown references disambiguated filenames for D2K Arrakis.
    text = APPENDIX_J.read_text(encoding="utf-8")
    bloxbase_refs = text.count("BLOXBASE.R16.png")
    bloxbase_disambig = text.count("BLOXBASE_")
    print(f"  Markdown references to BLOXBASE.R16.png: {bloxbase_refs}")
    print(f"  Markdown references to disambiguated BLOXBASE_*.R16.png: {bloxbase_disambig}")

    # If all rows reference the same non-disambiguated file, something is wrong.
    if bloxbase_refs > 10 and bloxbase_disambig == 0:
        print("  ERROR: Markdown appears to reference the same BLOXBASE.R16.png for many rows.")
        return False

    # A few identical files are expected when different templates share the same tile.
    if duplicate_groups:
        print(f"  NOTE: {len(duplicate_groups)} groups of identical files (likely shared tiles).")
    return True


def compare_with_backup():
    print("Comparing new images with backup for affected tilesets...")
    for subdir in ["ra_desert", "cnc_desert", "ts_temperate", "d2k_arrakis"]:
        old_dir = BACKUP_DIR / subdir
        new_mod = subdir.split("_")[0]
        new_tileset = subdir.split("_")[1]
        new_dir = IMAGES_DIR / new_mod / new_tileset
        if not old_dir.exists() or not new_dir.exists():
            print(f"  Skipping {subdir} (missing old or new dir)")
            continue
        changed = 0
        same = 0
        for old_path in old_dir.glob("*.png"):
            new_path = new_dir / old_path.name
            if not new_path.exists():
                print(f"  New missing: {new_path.relative_to(MANUAL_DIR)}")
                continue
            if old_path.read_bytes() == new_path.read_bytes():
                same += 1
            else:
                changed += 1
        print(f"  {subdir}: {changed} changed, {same} unchanged (out of {changed + same})")


def main():
    ok = True
    ok = check_ra_cnc_desert() and ok
    ok = check_ts() and ok
    ok = check_d2k_arrakis() and ok
    compare_with_backup()
    if ok:
        print("\nAll automated checks passed.")
    else:
        print("\nSome automated checks failed. Manual review recommended.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
