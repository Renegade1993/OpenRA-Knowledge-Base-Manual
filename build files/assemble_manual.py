#!/usr/bin/env python3
"""Assemble the OpenRA Knowledge Base Manual into a single Markdown file.

Run from the project root or from the directory containing this script.
"""

import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_FILE = BASE_DIR.parent / "OpenRA_Knowledge_Base_Manual.md"

MANUAL_VERSION = "v.5"
VERSION_TAG = "playtest-20260222-76-g972c10ec80"
VERSION_DATE = "2026-06-24"

FILES = [
    "MASTER_INDEX.md",
    "chapters/Part_00_Foundations.md",
    "chapters/Part_01_Chapter_01_ECS.md",
    "chapters/Part_01_Chapter_02_Activities.md",
    "chapters/Part_01_Chapter_03_World_Orders.md",
    "chapters/Part_01_Chapter_04_Math.md",
    "chapters/Part_01_Chapter_05_Pathfinding_Movement.md",
    "chapters/Part_01_Chapter_06_Combat_Damage.md",
    "chapters/Part_02_Chapter_01_MiniYaml.md",
    "chapters/Part_02_Chapter_02_Manifest.md",
    "chapters/Part_02_Chapter_03_FieldLoader.md",
    "chapters/Part_02_Chapter_04_Rules_Weapons.md",
    "chapters/Part_03_Chapter_01_Mod_SDK.md",
    "chapters/Part_03_Chapter_02_SDK_Bootstrap.md",
    "chapters/Part_03_Chapter_03_Build_Packaging.md",
    "chapters/Part_04_Chapter_01_Renderer.md",
    "chapters/Part_04_Chapter_02_WorldRenderer.md",
    "chapters/Part_04_Chapter_03_Widgets.md",
    "chapters/Part_04_Chapter_04_Viewport_Input.md",
    "chapters/Part_05_Chapter_01_Audio_Architecture.md",
    "chapters/Part_05_Chapter_02_Spatial_Attenuation.md",
    "chapters/Part_05_Chapter_03_Music.md",
    "chapters/Part_05_Chapter_04_Sound_Triggers.md",
    "chapters/Part_06_Chapter_01_Lua_Eluant.md",
    "chapters/Part_06_Chapter_02_ScriptContext.md",
    "chapters/Part_06_Chapter_03_VFS.md",
    "chapters/Part_06_Chapter_04_Crypto.md",
    "chapters/Part_06_Chapter_05_Asset_Loaders.md",
    "chapters/Part_07_Chapter_01_Pipeline.md",
    "chapters/Part_07_Chapter_02_Data_Structures.md",
    "chapters/Part_07_Chapter_03_Algorithms.md",
    "chapters/Part_07_Chapter_04_Terraformer.md",
    "chapters/Part_07_Chapter_05_MultiBrush.md",
    "chapters/Part_07_Chapter_06_Mod_Generators.md",
    "chapters/Part_07_Chapter_07_Resources_Actors.md",
    "chapters/Part_07_Chapter_08_Extension_Points.md",
    "chapters/Part_07_Chapter_09_File_Index.md",
    "chapters/Part_08_Chapter_01_IBot.md",
    "chapters/Part_08_Chapter_02_Bot_Modules.md",
    "chapters/Part_08_Chapter_03_Squads.md",
    "chapters/Part_08_Chapter_04_Order_Flow.md",
    "chapters/Part_09_Chapter_01_OrderManager.md",
    "chapters/Part_09_Chapter_02_Server_Connection.md",
    "chapters/Part_09_Chapter_03_Sync_Hashing.md",
    "chapters/Part_10_Chapter_01_Official_Mods.md",
    "chapters/Part_10_Chapter_02_Online_References.md",
    "chapters/Part_10_Chapter_03_Port_And_Modding.md",
    "appendices/Appendix_A_Glossary.md",
    "appendices/Appendix_B_Common_YAML_Patterns.md",
    "appendices/Appendix_C_Debugging.md",
    "appendices/Appendix_D_Engine_Conventions.md",
    "appendices/Appendix_E_Practical_Recipes.md",
    "appendices/Appendix_F_Testing.md",
    "appendices/Appendix_G_Advanced_Modding_Walkthroughs.md",
    "appendices/Appendix_H_Asset_Visual_Reference.md",
    "appendices/Appendix_I_Actor_Reference.md",
    "appendices/Appendix_J_Terrain_Tiles.md",
    "appendices/Appendix_K_Environmental_Actors.md",
]

VALID_FILES = set(FILES)


def anchor_id(filename):
    return "file-" + filename.replace("/", "-").replace(".md", "")


def rewrite_links(text, current_file):
    """Rewrite relative markdown links so they point to anchors in the combined manual."""
    current_dir = BASE_DIR / Path(current_file).parent
    link_re = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

    def replace(match):
        label, target = match.group(1), match.group(2)

        # Leave external links, anchors, and non-markdown links unchanged.
        if target.startswith(("http://", "https://", "mailto:", "#")):
            return match.group(0)
        if target.startswith("/") or not target.endswith(".md"):
            return match.group(0)

        resolved = (current_dir / target).resolve()
        try:
            relative = resolved.relative_to(BASE_DIR)
        except ValueError:
            return match.group(0)

        key = str(relative).replace("\\", "/")
        if key in VALID_FILES:
            return f"[{label}](#{anchor_id(key)})"
        return match.group(0)

    return link_re.sub(replace, text)


def first_heading(path):
    text = path.read_text(encoding="utf-8")
    for line in text.splitlines():
        if line.startswith("# "):
            return line.lstrip("# ").strip()
    return path.name


def make_header(toc):
    return f"""# OpenRA Knowledge Base Manual {MANUAL_VERSION}

> **Version note:** Manual {MANUAL_VERSION} — this edition reflects the OpenRA engine source at tag `{VERSION_TAG}` and is current as of {VERSION_DATE}. File paths and class names may change in newer engine versions.

This single-file edition combines the OpenRA Knowledge Base Manual chapters into one document. It is the canonical version for reading, printing, or feeding to an AI for review.

## Table of Contents

{toc}

---

"""


def assemble():
    toc_lines = []
    for filename in FILES:
        path = BASE_DIR / filename
        title = first_heading(path)
        toc_lines.append(f"- [{title}](#{anchor_id(filename)})")

    with OUTPUT_FILE.open("w", encoding="utf-8") as out:
        out.write(make_header("\n".join(toc_lines)))
        for i, filename in enumerate(FILES):
            path = BASE_DIR / filename
            if not path.exists():
                raise FileNotFoundError(f"Missing chapter file: {path}")
            text = path.read_text(encoding="utf-8")
            text = rewrite_links(text, filename)
            # Add a Pandoc-native header ID to the first top-level heading so PDF
            # internal links resolve to a real \label instead of an HTML anchor.
            text = re.sub(r"^(# .+)$", lambda m: f"{m.group(1)} {{#{anchor_id(filename)}}}", text, count=1, flags=re.MULTILINE)
            out.write(f'<a id="{anchor_id(filename)}"></a>\n\n')
            out.write(f"<!-- --- FILE: {filename} --- -->\n\n")
            out.write(text)
            out.write("\n\n")
            if i < len(FILES) - 1:
                out.write("\n---\n\n")

    print(f"Generated: {OUTPUT_FILE}")
    print(f"Chapters: {len(FILES)}")
    print(f"Size: {OUTPUT_FILE.stat().st_size:,} bytes")


if __name__ == "__main__":
    assemble()
