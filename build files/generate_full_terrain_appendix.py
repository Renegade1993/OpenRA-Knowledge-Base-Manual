#!/usr/bin/env python3
"""Generate the complete Appendix J Terrain Tiles reference.

For every official mod tileset, dumps all templates via the OpenRA Utility,
writes a Markdown appendix with Preview first, then renders every template.
"""

import json
import subprocess
from pathlib import Path

ENGINE_DIR = Path("C:/Users/Kmoney/Documents/AI Projects/Cameo Work/Game Sources and Development Reference Materials/OpenRA GitHub Repositories/OpenRA")
MANUAL_DIR = Path("C:/Users/Kmoney/Documents/AI Projects/Cameo Work/Game Sources and Development Reference Materials/OpenRA Manual")
APPENDIX_J = MANUAL_DIR / "build files" / "appendices" / "Appendix_J_Terrain_Tiles.md"
UTILITY = ENGINE_DIR / "bin" / "OpenRA.Utility.exe"

# (mod, tileset_id, tileset_file_stem, display_name)
TILESETS = [
    ("ra", "TEMPERAT", "temperat", "Temperate"),
    ("ra", "SNOW", "snow", "Snow"),
    ("ra", "DESERT", "desert", "Desert"),
    ("ra", "INTERIOR", "interior", "Interior"),
    ("cnc", "TEMPERAT", "temperat", "Temperate"),
    ("cnc", "SNOW", "snow", "Snow"),
    ("cnc", "DESERT", "desert", "Desert"),
    ("cnc", "WINTER", "winter", "Winter"),
    ("d2k", "ARRAKIS", "arrakis", "Arrakis"),
    ("ts", "TEMPERATE", "temperate", "Temperate"),
    ("ts", "SNOW", "snow", "Snow"),
]


def run_dump(mod, tileset_id):
    """Run the OpenRA utility to dump all templates for a tileset."""
    env = {
        "ENGINE_DIR": str(ENGINE_DIR),
        "MOD_SEARCH_PATHS": str(ENGINE_DIR / "mods"),
    }
    cmd = [str(UTILITY), mod, "--dump-terrain-templates", tileset_id]
    result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def get_image_stem_ext(image_name):
    """Split an image name like 'clear1.tem' or 'BLOXBASE.R16' into (stem, ext)."""
    if "." in image_name:
        stem, ext = image_name.rsplit(".", 1)
        return stem, ext
    return image_name, ""


def make_preview_filename(mod, tileset, template_id, image_name, used_names):
    """Return a unique preview filename for this template.

    Uses the image name directly when possible; appends the template ID if the
    same image name is already used by a different template ID.
    """
    key = (mod, tileset, image_name)
    if key not in used_names:
        used_names[key] = template_id
        return f"{image_name}.png"

    if used_names[key] == template_id:
        # Same template ID (duplicate row) -> reuse the same file.
        return f"{image_name}.png"

    # Different template IDs share the same image -> disambiguate with the ID.
    stem, ext = get_image_stem_ext(image_name)
    return f"{stem}_{template_id}.{ext}.png"


def make_preview_path(mod, tileset_stem, image_name, template_id, used_names):
    """Return the relative Markdown image path for a preview."""
    preview_file = make_preview_filename(mod, tileset_stem, template_id, image_name, used_names)
    return f"images/terrain/{mod}/{tileset_stem}/{preview_file}"


def build_notes(template):
    """Build a notes string from template metadata.
    
    For large templates, summarize mixed terrain as counts instead of a full
    cell-by-cell mapping so the table row stays compact.
    """
    parts = []
    if template.get("PickAny"):
        parts.append("PickAny")
    categories = template.get("Categories", [])
    if categories:
        parts.append(f"Category: {', '.join(categories)}")
    tile_types = template.get("TileTerrainTypes", {})
    if len(set(tile_types.values())) > 1:
        size = template.get("Size", "")
        try:
            cells = 1
            sep = "x" if "x" in size else ","
            w, h = size.split(sep)
            cells = int(w) * int(h)
        except Exception:
            cells = len(tile_types)
        # For templates with more than 20 cells, summarize terrain counts.
        if cells > 20:
            from collections import Counter
            counts = Counter(tile_types.values())
            summary = ", ".join(f"{k} ({v})" for k, v in sorted(counts.items()))
            parts.append(f"Mixed terrain: {summary}")
        else:
            parts.append(f"Mixed terrain: {tile_types}")
    return "; ".join(parts) if parts else ""


def generate_appendix():
    """Generate the full Appendix J markdown."""
    lines = [
        "# Appendix J — Terrain Tile Reference",
        "",
        "This appendix catalogs every terrain template in every official OpenRA mod tileset.",
        "Each row shows a rendered preview, the template ID, the source image file(s), the grid size,",
        "the primary terrain type, and notes about the template.",
        "",
    ]

    for mod, tileset_id, tileset_stem, display_name in TILESETS:
        lines.append(f"## {mod.upper()} — {display_name}")
        lines.append("")
        lines.append(f"### `mods/{mod}/tilesets/{tileset_stem}.yaml`")
        lines.append("")
        lines.append("#### All Templates")
        lines.append("")
        lines.append("| Preview | Id | Image(s) | Size | Primary Terrain | Notes |")
        lines.append("| :-- | ---: | :--- | :--- | :--- | :--- |")

        templates = run_dump(mod, tileset_id)
        used_names = {}
        for t in templates:
            tid = t["Id"]
            images = ", ".join(t.get("Images", []))
            size = t.get("Size", "")
            primary = t.get("PrimaryTerrain", "")
            notes = build_notes(t)
            # Use the first image for the preview filename; disambiguate when the
            # same image name is shared by multiple template IDs.
            image_name = t["Images"][0] if t.get("Images") else ""
            preview = f"![{image_name} preview]({make_preview_path(mod, tileset_stem, image_name, tid, used_names)})" if image_name else ""
            lines.append(f"| {preview} | {tid} | {images} | {size} | {primary} | {notes} |")

        lines.append("")

    APPENDIX_J.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {APPENDIX_J}")


if __name__ == "__main__":
    generate_appendix()
