#!/usr/bin/env python3
"""generate_environmental_actor_reference.py — build Appendix K (Environmental
Actor Reference) for the OpenRA Knowledge Base Manual from the bundled mods'
rules YAML + Fluent strings.

It parses each mod's rules/*.yaml (resolving Inherits: chains) and
fluent/rules.ftl (for display names), extracts map-editor-placed environmental
actors, and writes:
  appendices/Appendix_K_Environmental_Actors.md
and regenerates neutral placeholder previews under
  ../images/environmental/<mod>/<code>.png
  ../images/environmental/<mod>/<code>_unit.png

Real sprites are produced separately by engine/asset extraction tools; the
generators are kept optional because the original game art lives outside the
engine source. The placeholders keep the manual layout and link-valid without it.

Point at the engine source with the OPENRA_SRC environment variable, e.g.:
  set OPENRA_SRC=C:\\...\\OpenRA GitHub Repositories\\OpenRA   (Windows)
  OPENRA_SRC=/path/to/OpenRA python generate_environmental_actor_reference.py  (Unix)

Requires Pillow (pip install pillow) for placeholder generation.
"""
import os, re, glob, json
from collections import OrderedDict, defaultdict

BUILD = os.path.dirname(os.path.abspath(__file__))
MANUAL_DIR = os.path.dirname(BUILD)
APPENDIX = os.path.join(BUILD, "appendices", "Appendix_K_Environmental_Actors.md")
IMAGES = os.path.join(MANUAL_DIR, "images", "environmental")
SRC = os.environ.get(
    "OPENRA_SRC",
    r"C:\Users\Kmoney\Documents\AI Projects\Cameo Work\Game Sources and Development Reference Materials\OpenRA GitHub Repositories\OpenRA",
)

MODS = [("ra", "Red Alert"), ("cnc", "Tiberian Dawn"), ("d2k", "Dune 2000"), ("ts", "Tiberian Sun")]

# Editor categories that identify environmental / map-placed actors.
ENV_CATEGORIES = {
    "Tree", "Decoration", "Civilian building", "Tech building", "Wall", "Bridge",
    "Crate", "Resource spawn", "Husk", "Civilian infantry", "Civilian vehicle",
    "Critter", "Railway", "Billboard", "Tunnel", "Destroable Tiles", "Destroyed Tiles", "Debris",
}

# Editor categories that identify player-produced units/structures.
EXCLUDE_CATEGORIES = {
    "Building", "Defense", "Support", "Vehicle", "Infantry", "Naval", "Aircraft", "Fake", "System",
}

# Some mods put environmental actors in the System category; include them explicitly.
EXPLICIT_INCLUDE = {
    ("d2k", "crate"),
    ("d2k", "spicebloom"),
    ("d2k", "spicebloom.spawnpoint"),
    ("d2k", "sandworm"),
    ("d2k", "sietch"),
}

# Map markers / system actors that should never appear in the reference.
EXPLICIT_EXCLUDE = {
    ("ra", "camera"), ("ra", "flare"), ("ra", "mine"), ("ra", "minp"), ("ra", "minv"),
    ("ra", "railmine"), ("ra", "gmine"), ("ra", "lar1"), ("ra", "lar2"),
    ("ra", "quee"), ("ra", "sonar"), ("ra", "ctflag"), ("ra", "moneycrate"),
    ("ra", "healcrate"), ("ra", "scrate"), ("ra", "crate"),
    ("cnc", "camera"), ("cnc", "flare"), ("cnc", "moneycrate"), ("cnc", "scrate"), ("cnc", "crate"),
    ("d2k", "camera"), ("d2k", "deathhand"), ("d2k", "mpspawn"), ("d2k", "waypoint"),
    ("d2k", "wormspawner"), ("d2k", "crate_explosion"), ("d2k", "crate_reveal"), ("d2k", "crate_script"),
    ("ts", "camera"),
}

# Source files that are allowed to contribute actors even if their inherited
# category is not recognized (e.g. D2K arrakis.yaml).
ENV_SOURCE_FILES = {
    "ra": ["civilian.yaml", "decoration.yaml", "misc.yaml"],
    "cnc": ["civilian.yaml", "civilian-desert.yaml", "trees.yaml", "misc.yaml"],
    "d2k": ["arrakis.yaml", "misc.yaml"],
    "ts": ["civilian-structures.yaml", "civilian-infantry.yaml", "civilian-vehicles.yaml",
            "critters.yaml", "bridges.yaml", "trees.yaml", "misc.yaml"],
}

# Order of category sections and a human-readable title for each.
SECTION_ORDER = [
    ("Vegetation", "Tree"),
    ("Rocks and Cliffs", "Rock"),
    ("Buildings and Structures", "Building"),
    ("Walls and Fences", "Wall"),
    ("Bridges", "Bridge"),
    ("Crates and Pickups", "Crate"),
    ("Resource Spawns", "Resource"),
    ("Civilians", "Civilian"),
    ("Critters and Wildlife", "Critter"),
    ("Railway", "Railway"),
    ("Billboards", "Billboard"),
    ("Tunnels", "Tunnel"),
    ("Destructible Terrain", "Destructible"),
    ("Decorative Props", "Decoration"),
    ("Other Environmental Actors", "Other"),
]

SECTION_MAP = {label: title for title, label in SECTION_ORDER}


def parse_miniyaml(path):
    """Simple tab-aware MiniYAML parser matching generate_actor_reference.py."""
    a = OrderedDict(); cur = None; ct = None
    for raw in open(path, encoding="utf-8"):
        l = raw.rstrip("\n")
        if not l.strip() or l.strip().startswith("#"):
            continue
        ind = len(l) - len(l.lstrip("\t")); c = l.strip()
        if ind == 0:
            k = c.split(":", 1)[0].strip(); a[k] = OrderedDict(); cur = a[k]; ct = None
        elif ind == 1 and cur is not None:
            k, v = (c.split(":", 1) + [""])[:2]
            cur[k.strip()] = OrderedDict(); cur[k.strip()]["_v"] = v.strip(); ct = cur[k.strip()]
        elif ind >= 2 and ct is not None and ":" in c:
            k, v = c.split(":", 1); ct[k.strip()] = v.strip()
    return a


def load_mod(mod):
    """Load all rules for a mod and remember which file each actor came from."""
    actors = OrderedDict()
    sources = defaultdict(list)
    for f in sorted(glob.glob(os.path.join(SRC, "mods", mod, "rules", "*.yaml"))):
        fname = os.path.basename(f)
        for n, nd in parse_miniyaml(f).items():
            if n in actors:
                for tk, tv in nd.items():
                    actors[n][tk] = tv
            else:
                actors[n] = nd
            sources[n].append(fname)
    return actors, sources


def resolve(name, actors, seen=None):
    """Resolve an actor's inheritance chain into a flat trait dict."""
    if seen is None:
        seen = set()
    if name not in actors or name in seen:
        return OrderedDict()
    seen = seen | {name}; nd = actors[name]; m = OrderedDict()
    for k, tv in nd.items():
        if k.split("@")[0] == "Inherits":
            for ptk, ptv in resolve(tv.get("_v", "").strip(), actors, seen).items():
                m[ptk] = OrderedDict(ptv)
    for k, tv in nd.items():
        if k.split("@")[0] == "Inherits":
            continue
        if k.startswith("-"):
            m.pop(k[1:], None); continue
        if k in m:
            for fk, fv in tv.items():
                m[k][fk] = fv
        else:
            m[k] = OrderedDict(tv)
    return m


def inherited_templates(name, actors, seen=None):
    """Return the set of template names this actor inherits from."""
    if seen is None:
        seen = set()
    if name not in actors or name in seen:
        return set()
    seen = seen | {name}
    result = set()
    for k, tv in actors[name].items():
        if k.split("@")[0] == "Inherits":
            parent = tv.get("_v", "").strip()
            result.add(parent)
            result.update(inherited_templates(parent, actors, seen))
    return result


def parse_fluent(path):
    """Parse a simple Fluent key/value file."""
    msgs = {}; cur = None
    if not os.path.exists(path):
        return msgs
    for raw in open(path, encoding="utf-8"):
        l = raw.rstrip("\n")
        if not l.strip() or l.lstrip().startswith("#"):
            continue
        m = re.match(r'^([A-Za-z0-9_-]+)\s*=(.*)$', l)
        if m and l[0] not in ' \t':
            cur = m.group(1); msgs.setdefault(cur, {"_v": m.group(2).strip()})
        else:
            am = re.match(r'^\s+\.([A-Za-z0-9_-]+)\s*=(.*)$', l)
            if am and cur:
                msgs[cur][am.group(1)] = am.group(2).strip()
    return msgs


def fl(key, fn):
    """Resolve a Fluent key, supporting dotted attribute lookups."""
    if not key:
        return None
    if "." in key:
        msg, attr = key.rsplit(".", 1)
        return fn.get(msg, {}).get(attr) or fn.get(key, {}).get("_v")
    return fn.get(key, {}).get("_v")


def editor_category(resolved):
    """Return the resolved MapEditorData category, if any."""
    med = resolved.get("MapEditorData", {})
    if not isinstance(med, dict):
        return ""
    return med.get("Categories", "")


def environmental_section(resolved, templates, mod, name):
    """Pick a markdown section for this actor based on category/template."""
    cat = editor_category(resolved)
    lower = name.lower()

    # Explicit category mappings
    # D2K puts many environmental actors in the System category; map by name.
    if lower in ("spicebloom", "spicebloom.spawnpoint"):
        return SECTION_MAP["Resource"]
    if lower == "sandworm":
        return SECTION_MAP["Critter"]
    if lower == "crate":
        return SECTION_MAP["Crate"]
    if lower == "sietch":
        return SECTION_MAP["Building"]

    if cat == "Tree":
        return SECTION_MAP["Tree"]
    if cat == "Wall":
        return SECTION_MAP["Wall"]
    if cat == "Bridge":
        return SECTION_MAP["Bridge"]
    if cat in ("Crate", "Resource spawn"):
        return SECTION_MAP["Crate"] if cat == "Crate" else SECTION_MAP["Resource"]
    if cat == "Civilian infantry":
        return SECTION_MAP["Civilian"]
    if cat == "Civilian vehicle":
        return SECTION_MAP["Civilian"]
    if cat == "Critter":
        return SECTION_MAP["Critter"]
    if cat == "Railway":
        return SECTION_MAP["Railway"]
    if cat == "Billboard":
        return SECTION_MAP["Billboard"]
    if cat == "Tunnel":
        return SECTION_MAP["Tunnel"]
    if cat in ("Destroable Tiles", "Destroyed Tiles", "Debris"):
        return SECTION_MAP["Destructible"]

    # Template-based guesses for actors without clear categories
    if "^Box" in templates:
        return SECTION_MAP["Decoration"]
    if "^Tree" in templates or "^TreeHusk" in templates:
        return SECTION_MAP["Tree"]
    if "^Rock" in templates:
        return SECTION_MAP["Rock"]
    if "^Wall" in templates:
        return SECTION_MAP["Wall"]
    if "^Bridge" in templates or "^BridgeHut" in templates or "LegacyBridgeHut" in resolved:
        return SECTION_MAP["Bridge"]
    if "^Crate" in templates or "^AmmoBox" in templates:
        return SECTION_MAP["Crate"]
    if "^TibTree" in templates:
        return SECTION_MAP["Resource"]
    if "^Creep" in templates or "^Critter" in templates:
        return SECTION_MAP["Critter"]
    if "^CivBuilding" in templates or "^TechBuilding" in templates or "^DesertCivBuilding" in templates:
        return SECTION_MAP["Building"]
    if "^DestroyableTile" in templates or "^DestroyedTile" in templates:
        return SECTION_MAP["Destructible"]

    if cat == "Decoration":
        return SECTION_MAP["Decoration"]

    return SECTION_MAP["Other"]


def is_environmental_actor(name, resolved, actors, sources, mod):
    """Return True if this actor should appear in the environmental reference."""
    if name.startswith("^") or "." in name:
        return False

    key = (mod, name.lower())
    if key in EXPLICIT_EXCLUDE:
        return False
    if key in EXPLICIT_INCLUDE:
        return True

    cat = editor_category(resolved)
    if cat in EXCLUDE_CATEGORIES:
        return False
    if cat in ENV_CATEGORIES:
        return True

    # Source-file fallback for actors without a recognized editor category.
    env_sources = set(ENV_SOURCE_FILES.get(mod, []))
    if env_sources & set(sources.get(name, [])):
        # Still ignore mobile player units (but keep creeps/critters).
        if "Mobile" in resolved or "Aircraft" in resolved:
            templates = inherited_templates(name, actors)
            if "^Creep" in templates or "^Critter" in templates:
                return True
            if name.lower() == "sandworm":
                return True
            return False
        return True

    return False


def actor_size(resolved):
    """Return a compact 'WxH footprint' string from the Building trait."""
    b = resolved.get("Building", {})
    if not isinstance(b, dict):
        return "—"
    dims = b.get("Dimensions", "")
    fp = b.get("Footprint", "")
    if dims and fp:
        return f"{dims} `{fp}`"
    if dims:
        return dims
    if fp:
        return f"`{fp}`"
    return "—"


def actor_name(name, resolved, fluent):
    """Resolve the actor's display name from Tooltip or Fluent."""
    tooltip = resolved.get("Tooltip", {})
    if isinstance(tooltip, dict):
        key = tooltip.get("Name", "")
        if key:
            val = fl(key, fluent)
            if val:
                return val
    editor = resolved.get("EditorOnlyTooltip", {})
    if isinstance(editor, dict):
        key = editor.get("Name", "")
        if key:
            val = fl(key, fluent)
            if val:
                return val
    return "—"


def key_traits(resolved):
    """Return a short, human-readable list of behavior traits."""
    traits = []
    for t in ["SpawnActorOnDeath", "FireWarheadsOnDeath", "SeedsResource", "SpiceBloom",
              "CashTrickler", "Capturable", "TransformOnCapture", "InstantlyRepairable",
              "RevealsShroud", "BaseProvider", "GivesBuildableArea", "ProvidesPrerequisite",
              "WithBuildingBib", "Crushable", "Demolishable", "AttackSwallow", "Sandworm"]:
        if t in resolved:
            traits.append(t)
    return ", ".join(traits) if traits else "—"


def notes_for(resolved, templates, mod, name):
    """Build a short notes field from MapEditorData tileset restrictions."""
    parts = []
    med = resolved.get("MapEditorData", {})
    if isinstance(med, dict):
        req = med.get("RequireTilesets", "")
        excl = med.get("ExcludeTilesets", "")
        if req:
            parts.append(f"Require {req}")
        if excl:
            parts.append(f"Exclude {excl}")
    # Mention inherited templates for non-obvious actors
    if "^TreeHusk" in templates:
        parts.append("Tree husk")
    if "^DesertCivBuilding" in templates:
        parts.append("Desert building")
    if "^CivField" in templates:
        parts.append("Non-interactive field")
    return "; ".join(parts) if parts else "—"


def collect(mod, actors, sources, fluent):
    """Collect all environmental actors for a mod."""
    rows = []
    for n in actors:
        r = resolve(n, actors)
        if not is_environmental_actor(n, r, actors, sources, mod):
            continue
        templates = inherited_templates(n, actors)
        section = environmental_section(r, templates, mod, n)
        name = actor_name(n, r, fluent)
        rows.append({
            "code": n,
            "name": name,
            "preview": f"![{name} preview](images/environmental/{mod}/{n.lower()}.png)",
            "size": actor_size(r),
            "traits": key_traits(r),
            "notes": notes_for(r, templates, mod, n),
            "section": section,
        })
    return rows


def placeholder(path, code, kind="cameo"):
    """Render a labelled grey/blue-grey placeholder PNG."""
    from PIL import Image, ImageDraw, ImageFont
    bg = (228, 228, 228) if kind == "cameo" else (214, 220, 230)
    img = Image.new("RGB", (48, 48), bg)
    d = ImageDraw.Draw(img)
    col = (90, 90, 90)  # neutral environmental tint
    d.rectangle([0, 0, 47, 47], outline=col, width=2)
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None
    label = code.lower()[:8]
    d.text((4, 18), label, fill=(30, 30, 30), font=font)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)


def table(mod, rows):
    """Build the markdown table for a section."""
    lines = [
        "| Preview | Actor | Name/Tooltip | Size | Key Traits | Notes |",
        "| :---: | :--- | :--- | :--- | :--- | :--- |",
    ]
    for r in rows:
        lines.append(f"| {r['preview']} | `{r['code']}` | {r['name']} | {r['size']} | {r['traits']} | {r['notes']} |")
    return "\n".join(lines)


HEADER = """# Appendix K — Environmental Actor Reference

This appendix catalogs the **environmental actors** in the four official OpenRA mods: *Red Alert (RA)*, *Tiberian Dawn (C&C)*, *Dune 2000 (D2K)*, and *Tiberian Sun (TS)*. Environmental actors are map-placed objects that are not produced by a player's factory or construction yard in the normal tech tree—things like trees, rocks, civilian buildings, bridges, walls, gates, crates, resource spawns, and decorative props. Some of them (sandbags, concrete walls, gates) can also be built by players once the right prerequisites are met, but they still behave as world objects rather than as units.

They differ from buildable combat actors in a few key ways:

* Most inherit from templates such as `^Tree`, `^Rock`, `^CivBuilding`, `^Bridge`, `^Wall`, or `^Crate` rather than from `^Building` or `^Vehicle`.
* They are usually owned by `Neutral` (or `Creeps` for hostile wildlife) and placed in the map editor.
* They typically use `Building` for footprint, `Interactable` for selection bounds, `Tooltip` for display names, and `MapEditorData` for editor categorization.
* Many are invulnerable or have very high health, and some have special death behavior such as `SpawnActorOnDeath`, `FireWarheadsOnDeath`, `SeedsResource`, or `CashTrickler`.

The tables use the YAML data as it appears in the rules files. "Name/Tooltip" shows the in-game display name resolved from the mod's Fluent translation files. "Size" combines the `Dimensions` and `Footprint` values from the `Building` trait. "Key Traits" highlights the most important behavior traits. A "—" means the field is not explicitly set on that actor or its inherited template.

> **Generated, not hand-written.** This appendix is produced by `build files/generate_environmental_actor_reference.py`, which parses each mod's `rules/*.yaml` (resolving `Inherits:` chains) and `fluent/rules.ftl` (for display names). The preview column shows labelled placeholders by default; run `build files/extract_environmental_images.py` after installing the game content to render real sprites with the OpenRA Utility's `--export-sequence-frame` command.

> **A note on art.** OpenRA's own assets are openly licensed; the classic Westwood/EA unit art is distributed as freeware and remains its owners' property. Showing previews in a free, non-commercial, educational reference is a fair-use use, not an open-license grant. Attribute the art to its owners and include a "not endorsed by or affiliated with EA" notice when publishing.

> Cross-references: [Part 1.1 — ECS](../chapters/Part_01_Chapter_01_ECS.md), [Part 2.4 — Rulesets, Actors, and Weapons](../chapters/Part_02_Chapter_04_Rules_Weapons.md), [Part 7.7 — RMG Resources and Actors](../chapters/Part_07_Chapter_07_Resources_Actors.md), [Part 10.1 — Official Mods](../chapters/Part_10_Chapter_01_Official_Mods.md), [Appendix J — Terrain Tile Reference](Appendix_J_Terrain_Tiles.md)

---

"""

FOOTER = """
## Summary

This appendix is a single-source, auto-generated reference to the environmental actors in OpenRA's four bundled mods. It pairs each object's internal codename with its editor category, footprint, key traits, and a preview slot, all drawn from the engine's own rules so the reference stays in sync with the pinned source.

## What to read next

- [Part 2.4 — Rules and Weapons](../chapters/Part_02_Chapter_04_Rules_Weapons.md) — how the actor and weapon YAML in these tables is defined.
- [Appendix J — Terrain Tile Reference](Appendix_J_Terrain_Tiles.md) — the terrain tiles these objects sit on.
- [Part 10.3 — Porting and Modding](../chapters/Part_10_Chapter_03_Port_And_Modding.md) — creating your own environmental actor from scratch.
"""


def main():
    manifest = {}
    total = 0
    sections = []
    for mod, label in MODS:
        actors, sources = load_mod(mod)
        fluent = parse_fluent(os.path.join(SRC, "mods", mod, "fluent", "rules.ftl"))
        rows = collect(mod, actors, sources, fluent)

        manifest[mod] = [r["code"] for r in rows]
        total += len(rows)

        os.makedirs(os.path.join(IMAGES, mod), exist_ok=True)
        for r in rows:
            code = r["code"].lower()
            base_path = os.path.join(IMAGES, mod, code + ".png")
            if not os.path.exists(base_path):
                placeholder(base_path, r["code"], "cameo")

        sec = [f"## {label}", f"*{len(rows)} environmental actors.*\n"]
        for title, _label in SECTION_ORDER:
            sub = [r for r in rows if r["section"] == title]
            if not sub:
                continue
            sec.append(f"### {title} ({len(sub)})")
            sec.append(table(mod, sub) + "\n")
        sections.append("\n".join(sec))

    out = HEADER + "\n".join(sections) + FOOTER
    with open(APPENDIX, "w", encoding="utf-8") as f:
        f.write(out)

    manifest_path = os.path.join(BUILD, "environmental_actor_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=1)

    print(f"Wrote {APPENDIX}")
    print(f"Wrote {manifest_path}")
    print(f"Environmental actors: {total}  " + "  ".join(f"{k}={len(v)}" for k, v in manifest.items()))


if __name__ == "__main__":
    main()
