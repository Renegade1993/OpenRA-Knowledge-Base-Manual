#!/usr/bin/env python3
"""Render terrain template previews in parallel.

Reads Appendix J, finds every template row, and renders the preview PNG if it
does not already exist. Uses a process pool to run OpenRA.Utility.exe commands
in parallel.
"""

import json
import os
import re
import subprocess
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

ENGINE_DIR = Path("C:/Users/Kmoney/Documents/AI Projects/Cameo Work/Game Sources and Development Reference Materials/OpenRA GitHub Repositories/OpenRA")
MANUAL_DIR = Path("C:/Users/Kmoney/Documents/AI Projects/Cameo Work/Game Sources and Development Reference Materials/OpenRA Manual")
APPENDIX_J = MANUAL_DIR / "build files" / "appendices" / "Appendix_J_Terrain_Tiles.md"
IMAGES_DIR = MANUAL_DIR / "images" / "terrain"
UTILITY = ENGINE_DIR / "bin" / "OpenRA.Utility.exe"

SECTION_RE = re.compile(r"^### `mods/(?P<mod>[a-z0-9]+)/tilesets/(?P<tileset>[a-z0-9_]+)\.yaml`")

ENV = {
    "ENGINE_DIR": str(ENGINE_DIR),
    "MOD_SEARCH_PATHS": str(ENGINE_DIR / "mods"),
}


def parse_appendix(path):
    """Yield (mod, tileset, template_id, image_name) for each template row."""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    current_mod = None
    current_tileset = None
    id_col = None
    images_col = None
    in_table = False

    for line in lines:
        m = SECTION_RE.match(line)
        if m:
            current_mod = m.group("mod")
            current_tileset = m.group("tileset")
            id_col = None
            images_col = None
            in_table = False
            continue

        if line.strip() in ("#### Representative Templates", "#### All Templates"):
            id_col = None
            images_col = None
            in_table = False
            continue

        if not in_table and line.startswith("|") and "Id" in line and "Image(s)" in line:
            cols = [c.strip() for c in line.split("|")]
            try:
                id_col = cols.index("Id")
                images_col = cols.index("Image(s)")
                in_table = True
            except ValueError:
                pass
            continue

        if in_table:
            if line.startswith("|---"):
                continue
            if not line.startswith("|") or line.strip() == "":
                in_table = False
                id_col = None
                images_col = None
                continue
            cols = [c.strip() for c in line.split("|")]
            if id_col < len(cols) and images_col < len(cols):
                tid = cols[id_col]
                images = cols[images_col]
                if tid.isdigit() and images:
                    yield current_mod, current_tileset, int(tid), images.split(",")[0].strip()


def render_one(args):
    mod, tileset, template_id, image_name = args
    tileset_dir = IMAGES_DIR / mod / tileset
    tileset_dir.mkdir(parents=True, exist_ok=True)
    outfile = tileset_dir / f"{image_name}.png"
    if outfile.exists():
        return (mod, tileset, template_id, image_name, "exists")

    cmd = [str(UTILITY), mod, "--export-terrain-template", tileset.upper(), str(template_id), str(outfile)]
    try:
        result = subprocess.run(cmd, env=ENV, capture_output=True, text=True, check=True, timeout=60)
        return (mod, tileset, template_id, image_name, "ok")
    except subprocess.CalledProcessError as e:
        return (mod, tileset, template_id, image_name, f"error: {e.stdout} {e.stderr}")
    except subprocess.TimeoutExpired:
        return (mod, tileset, template_id, image_name, "timeout")


if __name__ == "__main__":
    tasks = list(parse_appendix(APPENDIX_J))
    print(f"Total tasks: {len(tasks)}")

    generated = 0
    failed = 0
    exists = 0
    with ProcessPoolExecutor(max_workers=8) as executor:
        future_to_task = {executor.submit(render_one, t): t for t in tasks}
        for future in as_completed(future_to_task):
            mod, tileset, tid, img, status = future.result()
            if status == "ok":
                generated += 1
            elif status == "exists":
                exists += 1
            else:
                failed += 1
                print(f"FAIL {mod}/{tileset} #{tid} {img}: {status}")
            if (generated + exists + failed) % 100 == 0:
                print(f"progress: ok={generated} exists={exists} failed={failed}")

    print(f"Done: ok={generated} exists={exists} failed={failed}")
