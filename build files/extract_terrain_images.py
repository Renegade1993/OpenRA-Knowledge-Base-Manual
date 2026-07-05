#!/usr/bin/env python3
"""Render terrain template previews for Appendix J and update the tables.

Reads the Appendix J markdown, identifies each referenced template, renders it
via the OpenRA Utility's custom --export-terrain-template command, and updates
the "Representative Templates" tables with a Preview column.

Run from the Manual/build files directory or pass paths explicitly.
"""

import os
import re
import subprocess
import sys
from pathlib import Path
from collections import defaultdict

ENGINE_DIR = Path("C:/Users/Kmoney/Documents/AI Projects/Cameo Work/Game Sources and Development Reference Materials/OpenRA GitHub Repositories/OpenRA")
MANUAL_DIR = Path("C:/Users/Kmoney/Documents/AI Projects/Cameo Work/Game Sources and Development Reference Materials/OpenRA Manual")
APPENDIX_J = MANUAL_DIR / "build files" / "appendices" / "Appendix_J_Terrain_Tiles.md"
IMAGES_DIR = MANUAL_DIR / "images" / "terrain"
UTILITY = ENGINE_DIR / "bin" / "OpenRA.Utility.exe"
FORCE = "--force" in sys.argv

# Template section headers look like:
# ### `mods/ra/tilesets/temperat.yaml`
SECTION_RE = re.compile(r"^### `mods/(?P<mod>[a-z0-9]+)/tilesets/(?P<tileset>[a-z0-9_]+)\.yaml`")

# Table rows under "Representative Templates" or "All Templates".
# Columns: Id | Image(s) | Size | Primary Terrain | Notes | (optional Preview at end)
# or: Preview | Id | Image(s) | Size | Primary Terrain | Notes
ROW_RE = re.compile(r"^\|\s*(?P<id>\d+)\s*\|\s*(?P<images>[^|]+?)\s*\|\s*(?P<size>[^|]+?)\s*\|\s*(?P<terrain>[^|]+?)\s*\|\s*(?P<notes>[^|]*?)\s*\|(?:[^|]*\|)?\s*$")


def make_preview_markdown(image_name, preview_path):
    """Markdown image tag for the preview."""
    label = f"{image_name} preview"
    return f"![{label}]({preview_path})"


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


def run_utility(mod, tileset_id, template_id, outfile):
    """Run the OpenRA utility to render a single template."""
    env = os.environ.copy()
    env["ENGINE_DIR"] = str(ENGINE_DIR)
    cmd = [
        str(UTILITY),
        mod,
        "--export-terrain-template",
        tileset_id,
        str(template_id),
        str(outfile),
    ]
    try:
        result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=True)
        return True, result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return False, e.stdout.strip() + " " + e.stderr.strip()


def parse_appendix(path):
    """Yield (mod, tileset, table_start_line, rows) for each templates table."""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    current_mod = None
    current_tileset = None
    pending_heading = False
    in_table = False
    table_start = None
    rows = []
    id_col = None
    images_col = None
    preview_col = None

    def parse_header(header_line):
        cols = [c.strip() for c in header_line.split("|")]
        try:
            return (
                cols.index("Id"),
                cols.index("Image(s)"),
                cols.index("Size"),
                cols.index("Primary Terrain"),
                cols.index("Notes"),
                cols.index("Preview") if "Preview" in cols else None,
            )
        except ValueError:
            return None, None, None, None, None, None

    def parse_row(line, id_col, images_col, size_col, terrain_col, notes_col, preview_col):
        cols = [c.strip() for c in line.split("|")]
        if id_col >= len(cols) or images_col >= len(cols):
            return None
        preview = cols[preview_col] if preview_col is not None and preview_col < len(cols) else ""
        # Extract the image path from a markdown image tag like ![alt](path)
        m = re.search(r"!\[.*?\]\((.*?)\)", preview)
        preview_path = m.group(1) if m else ""
        return {
            "id": cols[id_col],
            "images": cols[images_col],
            "size": cols[size_col] if size_col is not None and size_col < len(cols) else "",
            "terrain": cols[terrain_col] if terrain_col is not None and terrain_col < len(cols) else "",
            "notes": cols[notes_col] if notes_col is not None and notes_col < len(cols) else "",
            "preview_path": preview_path,
        }

    for i, line in enumerate(lines):
        m = SECTION_RE.match(line)
        if m:
            current_mod = m.group("mod")
            current_tileset = m.group("tileset")
            pending_heading = False
            in_table = False
            table_start = None
            rows = []
            id_col = None
            images_col = None
            size_col = None
            terrain_col = None
            notes_col = None
            preview_col = None
            continue

        if line.strip() in ("#### Representative Templates", "#### All Templates"):
            if rows and table_start is not None:
                yield current_mod, current_tileset, table_start, rows
            pending_heading = True
            in_table = False
            table_start = None
            rows = []
            id_col = None
            images_col = None
            size_col = None
            terrain_col = None
            notes_col = None
            preview_col = None
            continue

        if pending_heading:
            if line.startswith("|") and "Id" in line and "Image(s)" in line:
                table_start = i
                id_col, images_col, size_col, terrain_col, notes_col, preview_col = parse_header(line)
                in_table = id_col is not None and images_col is not None
                pending_heading = False
                continue
            if line.strip() == "":
                continue
            pending_heading = False

        if in_table:
            if line.startswith("|---"):
                continue
            row = parse_row(line, id_col, images_col, size_col, terrain_col, notes_col, preview_col)
            if row and row["id"].isdigit():
                rows.append(row)
                continue
            if line.strip() == "" or not line.startswith("|"):
                # End of table
                if rows and table_start is not None:
                    yield current_mod, current_tileset, table_start, rows
                in_table = False
                table_start = None
                rows = []
                id_col = None
                images_col = None
                size_col = None
                terrain_col = None
                notes_col = None
                preview_col = None
                continue

    if in_table and rows and table_start is not None:
        yield current_mod, current_tileset, table_start, rows


def render_all():
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    used_names = {}
    generated = []
    skipped = []
    failed = []
    processed_files = set()
    table_rows = []

    for mod, tileset, table_start, rows in parse_appendix(APPENDIX_J):
        tileset_dir = IMAGES_DIR / mod / tileset
        tileset_dir.mkdir(parents=True, exist_ok=True)
        tileset_id = tileset.upper()

        for row in rows:
            template_id = int(row["id"])
            images = [img.strip() for img in row["images"].split(",")]
            images = [img for img in images if img]
            if not images:
                failed.append((mod, tileset, template_id, "No image name in row"))
                table_rows.append((mod, tileset, table_start, row, None))
                continue

            image_name = images[0]
            preview_file = make_preview_filename(mod, tileset, template_id, image_name, used_names)
            outfile = tileset_dir / preview_file
            preview_path = f"images/terrain/{mod}/{tileset}/{preview_file}"

            if FORCE or outfile not in processed_files:
                processed_files.add(outfile)
                if not FORCE and outfile.exists():
                    skipped.append((mod, tileset, template_id, image_name, preview_path))
                else:
                    ok, msg = run_utility(mod, tileset_id, template_id, outfile)
                    if ok:
                        generated.append((mod, tileset, template_id, image_name, preview_path))
                    else:
                        failed.append((mod, tileset, template_id, image_name, msg))
                        preview_path = None

            table_rows.append((mod, tileset, table_start, row, preview_path))

    return generated, skipped, failed, table_rows


def update_markdown(path, table_rows):
    """Insert or refresh a Preview column in every Representative Templates table."""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    # Group rows by their table_start line.
    rows_by_table = defaultdict(list)
    for mod, tileset, table_start, row, preview_path in table_rows:
        rows_by_table[table_start].append((row, preview_path))

    # Process tables in reverse order so line indices remain valid.
    for table_start in sorted(rows_by_table.keys(), reverse=True):
        rows = rows_by_table[table_start]
        header_line = table_start
        align_line = table_start + 1

        # Update header and alignment rows.
        header = lines[header_line]
        align = lines[align_line]
        cols = [c.strip() for c in header.split("|")]
        try:
            preview_col = cols.index("Preview")
        except ValueError:
            preview_col = -1

        if not header.endswith(" |"):
            continue

        if preview_col == -1:
            # No Preview column yet; add one at the end.
            lines[header_line] = header[:-1] + "| Preview |"
            lines[align_line] = align[:-1] + "| :-- |"
            preview_col = len(cols) - 1

        for row, preview_path in rows:
            # Find the row by matching the non-preview columns.
            row_core = f"| {row['id']} | {row['images']} | {row['size']} | {row['terrain']} | {row['notes']} |"
            for j in range(table_start + 2, len(lines)):
                if row_core in lines[j]:
                    if preview_path:
                        preview = make_preview_markdown(row['images'].split(",")[0].strip(), preview_path)
                        cell_content = f" {preview} "
                    else:
                        cell_content = " "

                    # Replace the Preview cell, wherever it is in the row.
                    parts = lines[j].split("|")
                    if preview_col < len(parts):
                        parts[preview_col] = cell_content
                        lines[j] = "|".join(parts)
                    break

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    generated, skipped, failed, table_rows = render_all()
    print(f"Generated: {len(generated)}")
    print(f"Skipped (already exist): {len(skipped)}")
    print(f"Failed: {len(failed)}")
    for g in generated:
        print("  OK", g)
    for f in failed:
        print("  FAIL", f)

    if table_rows:
        update_markdown(APPENDIX_J, table_rows)
        print("Updated Appendix J tables.")
