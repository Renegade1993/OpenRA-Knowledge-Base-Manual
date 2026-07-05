#!/usr/bin/env python3
"""generate_actor_reference.py — build Appendix I (Actor Reference) for the
OpenRA Knowledge Base Manual from the bundled mods' rules YAML + Fluent strings.

It parses each mod's rules/*.yaml (resolving Inherits: chains) and fluent/rules.ftl
(for display names), extracts deep per-actor stats, writes
  appendices/Appendix_I_Actor_Reference.md
and regenerates faction-tinted placeholder cameos under
  ../images/actors/<mod>/<code>.png

Real cameos are produced separately by extract_cameos.ps1 (needs installed game
content) and overwrite the placeholders.

Point at the engine source with the OPENRA_SRC environment variable, e.g.:
  set OPENRA_SRC=C:\\...\\OpenRA GitHub Repositories\\OpenRA   (Windows)
  OPENRA_SRC=/path/to/OpenRA python generate_actor_reference.py  (Unix)

Requires Pillow (pip install pillow) for placeholder generation.
"""
import os, re, glob, json
from collections import OrderedDict, Counter

BUILD = os.path.dirname(os.path.abspath(__file__))
MANUAL_DIR = os.path.dirname(BUILD)                       # Manual/
APPENDIX = os.path.join(BUILD, "appendices", "Appendix_I_Actor_Reference.md")
IMAGES = os.path.join(MANUAL_DIR, "images", "actors")
SRC = os.environ.get(
    "OPENRA_SRC",
    r"C:\Users\Kmoney\Documents\AI Projects\Cameo Work\Game Sources and Development Reference Materials\OpenRA GitHub Repositories\OpenRA",
)

MODS = [("ra", "Red Alert"), ("cnc", "Tiberian Dawn"), ("d2k", "Dune 2000"), ("ts", "Tiberian Sun")]
FACTION_KW = {
    "ra": [
        ("soviet", "Soviet"), ("allies", "Allied"), ("allied", "Allied"),
        # Production buildings used as faction discriminators in prerequisites
        ("barr", "Soviet"), ("tent", "Allied"),
        ("afld", "Soviet"), ("hpad", "Allied"),
        ("syrd", "Soviet"), ("spen", "Soviet"), ("yard", "Allied"),
        ("stek", "Soviet"), ("atek", "Allied"),
        ("iron", "Soviet"), ("pdox", "Allied"), ("tsla", "Soviet"),
        ("agun", "Soviet"), ("gap", "Allied"),
        ("kenn", "Soviet"),
    ],
    "cnc": [
        ("gdi", "GDI"), ("nod", "Nod"),
        ("gweap", "GDI"), ("nweap", "Nod"),
        ("gapiled", "GDI"), ("nhand", "Nod"),
        ("gbar", "GDI"), ("nar", "Nod"),
        ("ghpad", "GDI"), ("nhpad", "Nod"),
        ("gfix", "GDI"), ("nfix", "Nod"),
        ("gtwr", "GDI"), ("ntwr", "Nod"),
        ("gproc", "GDI"), ("nproc", "Nod"),
        ("gtech", "GDI"), ("ntech", "Nod"),
        ("gun", "GDI"), ("nuke", "Nod"),
        ("gaair", "GDI"), ("nair", "Nod"),
        ("gadept", "GDI"), ("nadept", "Nod"),
    ],
    "d2k": [
        ("atreides", "Atreides"), ("harkonnen", "Harkonnen"), ("ordos", "Ordos"),
        ("corrino", "Corrino"), ("smuggler", "Smugglers"),
        (".a", "Atreides"), (".h", "Harkonnen"), (".o", "Ordos"),
        (".c", "Corrino"), (".s", "Smugglers"),
    ],
    "ts": [
        ("gdi", "GDI"), ("nod", "Nod"),
        ("gdihumvee", "GDI"), ("nodbuggy", "Nod"),
        ("gdisc", "GDI"), ("nodmcv", "Nod"),
        ("gdiharv", "GDI"), ("nodharv", "Nod"),
        ("gapipe", "GDI"), ("napulse", "Nod"),
        ("ga", "GDI"), ("na", "Nod"),
    ],
}
ABILITY_TRAITS = ['Cloak', 'DetectCloaked', 'Chronoshiftable', 'SelfHealing', 'Demolition',
    'C4Demolition', 'Captures', 'MindController', 'Submarine', 'Carryall', 'Parachutable',
    'Minelayer', 'SeedsResource', 'BaseProvider', 'ProvidesRadar', 'Transforms',
    'GrantConditionOnDeploy', 'NukePower', 'IonCannonPower', 'ParatroopersPower',
    'AirstrikePower', 'ProducibleWithLevel', 'Repairable']
# Actors that have Buildable/Tooltip but no usable in-world art (no sequence defined).
SKIP_CODES = {
    'ra': {'WarriorAnt'},
}
FCOLOR = {'Soviet': (150, 40, 40), 'Allied': (40, 60, 150), 'GDI': (40, 80, 160),
    'Nod': (150, 40, 40), 'Atreides': (40, 80, 160), 'Harkonnen': (150, 40, 40),
    'Ordos': (40, 140, 120), '—': (90, 90, 90)}
CAT_ORDER = ['Infantry', 'Vehicle', 'Aircraft', 'Naval', 'Building']


def parse_miniyaml(path):
    a = OrderedDict(); cur = None; ct = None
    for raw in open(path, encoding='utf-8'):
        l = raw.rstrip('\n')
        if not l.strip() or l.strip().startswith('#'):
            continue
        ind = len(l) - len(l.lstrip('\t')); c = l.strip()
        if ind == 0:
            k = c.split(':', 1)[0].strip(); a[k] = OrderedDict(); cur = a[k]; ct = None
        elif ind == 1 and cur is not None:
            k, v = (c.split(':', 1) + [''])[:2]
            cur[k.strip()] = OrderedDict(); cur[k.strip()]['_v'] = v.strip(); ct = cur[k.strip()]
        elif ind >= 2 and ct is not None and ':' in c:
            k, v = c.split(':', 1); ct[k.strip()] = v.strip()
    return a


def load_mod(mod):
    a = OrderedDict()
    for f in sorted(glob.glob(os.path.join(SRC, "mods", mod, "rules", "*.yaml"))):
        for n, nd in parse_miniyaml(f).items():
            if n in a:
                for tk, tv in nd.items():
                    a[n][tk] = tv
            else:
                a[n] = nd
    return a


def resolve(name, a, seen=None):
    if seen is None:
        seen = set()
    if name not in a or name in seen:
        return OrderedDict()
    seen = seen | {name}; nd = a[name]; m = OrderedDict()
    for k, tv in nd.items():
        if k.split('@')[0] == 'Inherits':
            for ptk, ptv in resolve(tv.get('_v', '').strip(), a, seen).items():
                m[ptk] = OrderedDict(ptv)
    for k, tv in nd.items():
        if k.split('@')[0] == 'Inherits':
            continue
        if k.startswith('-'):
            m.pop(k[1:], None); continue
        if k in m:
            for fk, fv in tv.items():
                m[k][fk] = fv
        else:
            m[k] = OrderedDict(tv)
    return m


def parse_fluent(path):
    msgs = {}; cur = None
    if not os.path.exists(path):
        return msgs
    for raw in open(path, encoding='utf-8'):
        l = raw.rstrip('\n')
        if not l.strip() or l.lstrip().startswith('#'):
            continue
        m = re.match(r'^([A-Za-z0-9_-]+)\s*=(.*)$', l)
        if m and l[0] not in ' \t':
            cur = m.group(1); msgs.setdefault(cur, {'_v': m.group(2).strip()})
        else:
            am = re.match(r'^\s+\.([A-Za-z0-9_-]+)\s*=(.*)$', l)
            if am and cur:
                msgs[cur][am.group(1)] = am.group(2).strip()
    return msgs


def fl(key, fn):
    if not key:
        return None
    if '.' in key:
        msg, attr = key.rsplit('.', 1)
        return fn.get(msg, {}).get(attr) or fn.get(key, {}).get('_v')
    return fn.get(key, {}).get('_v')


def faction(mod, *texts):
    s = ' '.join(x for x in texts if x)
    f = []
    for kw, lab in FACTION_KW.get(mod, []):
        # Match the keyword as a whole token. For D2K suffixes (.a/.h/.o etc.) allow a leading building name;
        # for other keywords allow a leading ~, ., comma, or whitespace so ~vehicles.gdi and ~barr work.
        if kw.startswith('.'):
            pattern = r'(?:^|[\s,~])[a-z0-9_]+' + re.escape(kw) + r'\b'
        else:
            pattern = r'(?:^|[\s,~.])' + re.escape(kw) + r'\b'
        if re.search(pattern, s, re.IGNORECASE) and lab not in f:
            f.append(lab)
    return ' / '.join(f) if f else '—'


def category(r):
    if 'Aircraft' in r:
        return 'Aircraft'
    if any(k.split('@')[0] == 'Mobile' for k in r):
        loco = r.get('Mobile', {}).get('Locomotor', '').lower()
        if any(x in loco for x in ('boat', 'naval', 'ship', 'submarine', 'hover')):
            return 'Naval'
        if 'TakeCover' in r or 'WithInfantryBody' in r:
            return 'Infantry'
        return 'Vehicle'
    return 'Building'


def image_name(code, resolved):
    """Return the sprite image name for the actor.

    Sequence image keys are case-insensitive in the engine but the utility's
    lookup is case-sensitive, so we always return a lowercase name.
    """
    rs = resolved.get('RenderSprites', {})
    if isinstance(rs, dict) and rs.get('Image'):
        return rs['Image'].lower()
    return code.lower()


def collect(mod):
    a = load_mod(mod); fn = parse_fluent(os.path.join(SRC, "mods", mod, "fluent", "rules.ftl"))
    out = []
    for n in a:
        if n.startswith('^') or '.' in n:
            continue
        r = resolve(n, a)
        if 'Buildable' not in r or 'Tooltip' not in r:
            continue
        nm = fl(r.get('Tooltip', {}).get('Name'), fn)
        if not nm:
            continue
        b = r.get('Buildable', {})
        weap = [tv.get('Weapon') for tk, tv in r.items()
                if tk.split('@')[0] == 'Armament' and tv.get('Weapon')]
        ab = [t for t in ABILITY_TRAITS if any(k.split('@')[0] == t for k in r)]
        out.append(dict(code=n, image=image_name(n, r), name=nm, cat=category(r),
            faction=faction(mod, b.get('Queue'), b.get('Prerequisites')),
            cost=r.get('Valued', {}).get('Cost') or '—',
            hp=r.get('Health', {}).get('HP') or '—',
            armor=(r.get('Armor', {}).get('Type') or '—').title(),
            speed=r.get('Mobile', {}).get('Speed') or r.get('Aircraft', {}).get('Speed') or '—',
            sight=r.get('RevealsShroud', {}).get('Range') or '—',
            prereq=b.get('Prerequisites') or '—',
            weapons=', '.join(weap) if weap else '—',
            abilities=', '.join(sorted(set(ab))) if ab else '—'))
    return out


def placeholder(path, code, fac, kind='cameo'):
    from PIL import Image, ImageDraw, ImageFont
    bg = (228, 228, 228) if kind == 'cameo' else (214, 220, 230)
    img = Image.new('RGB', (48, 48), bg); d = ImageDraw.Draw(img)
    col = FCOLOR.get(fac.split(' / ')[0], (90, 90, 90))
    d.rectangle([0, 0, 47, 47], outline=col, width=2)
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None
    d.text((4, 18), code.lower()[:8], fill=(30, 30, 30), font=font)
    img.save(path)


def table(mod, rows):
    L = ["| Preview | Code | Name | Faction | Cost | HP | Armor | Speed | Sight | Weapon(s) | Notable traits |",
         "| :---: | :--- | :--- | :--- | ---: | ---: | :--- | ---: | ---: | :--- | :--- |"]
    for r in rows:
        code = r['code'].lower()
        cameo = f"![{r['name']} cameo](images/actors/{mod}/{code}.png)"
        unit = f"![{r['name']} unit](images/actors/{mod}/{code}_unit.png)"
        # The two images are placed side-by-side in Markdown; the LaTeX post-processor
        # stacks them vertically in the Preview column.
        preview = f"{cameo} {unit}"
        L.append(f"| {preview} | `{r['code']}` | {r['name']} | {r['faction']} | {r['cost']} | "
                 f"{r['hp']} | {r['armor']} | {r['speed']} | {r['sight']} | {r['weapons']} | {r['abilities']} |")
    return '\n'.join(L)


HEADER = """# Appendix I — Actor Reference

This appendix consolidates, in one place, every **buildable actor** in the four mods that ship with OpenRA — *Red Alert*, *Tiberian Dawn*, *Dune 2000*, and *Tiberian Sun* — with its cameo, codename, faction, role, and core combat statistics. The goal is the thing that exists nowhere else: the sprite, the internal codename you write in YAML, and the numbers that define the unit, all next to each other, so a new modder can see at a glance what a unit *is* and what rules drive it.

This is engine-data reference, not balance commentary. Every value here is read directly from the mod's own rules YAML, so it always reflects the pinned engine rather than a hand-maintained copy that can drift.

> **Generated, not hand-written.** This appendix is produced by `build files/generate_actor_reference.py`, which parses each mod's `rules/*.yaml` (resolving `Inherits:` chains) and `fluent/rules.ftl` (for display names).

## How to read these tables

Each mod is split into **Infantry, Vehicles, Aircraft, Naval, and Buildings**. Columns:

- **Preview** — the build-palette cameo and the in-world battlefield sprite stacked in one cell. The cameo is the icon shown in the production sidebar; the unit is the idle/stand frame rendered with the same palette the engine uses in-game. (See the note on the images below.)
- **Code** — the actor's internal name; this is the key you use in `rules/*.yaml`, map actor definitions, and Lua (`Actor.Create("e1", ...)`).
- **Name** — the in-game display name, resolved from the mod's Fluent (`.ftl`) strings.
- **Faction** — derived from the build `Prerequisites`/`Queue` (e.g. `~vehicles.soviet`). A dash means shared or not faction-restricted.
- **Cost** — `Valued.Cost` (credits).
- **HP** — `Health.HP`, in raw engine health units (OpenRA's RA mod uses a ~100x scale, so `60000` is the classic "600").
- **Armor** — `Armor.Type` (matched against weapon `Versus` tables).
- **Speed** — `Mobile.Speed` (ground) or `Aircraft.Speed` (air), in engine units.
- **Sight** — `RevealsShroud.Range`, in cells (`WDist`, e.g. `6c0` = 6 cells).
- **Weapon(s)** — the weapon name(s) from each `Armament`; look these up in the mod's `weapons/*.yaml`.
- **Notable traits** — a curated set of standout abilities present on the actor (cloak, capture, deploy, support powers, self-heal, etc.).

> **About the images.** Each actor shows a **Preview** cell containing both the build-palette cameo (sidebar/construction-menu icon) and the in-world battlefield sprite. Both are rendered from the original game art, which lives only where you have installed the OpenRA game content — it is not in the engine source, so it cannot be bundled. Until the extraction script (below) is run on a machine with the content installed, the cell shows two labelled faction-tinted **placeholders** (the cameo box is grey; the unit box is blue-grey). A handful of actors have no art for one of the two slots (e.g. fake structures, or units with no separate sidebar icon) and keep its placeholder there. The manual is fully laid out and link-valid in the meantime.

> **A note on art.** OpenRA's own assets are openly licensed; the classic Westwood/EA unit art is distributed as freeware and remains its owners' property. Showing cameos in a free, non-commercial, educational reference is a fair-use use, not an open-license grant. Attribute the art to its owners and include a "not endorsed by or affiliated with EA" notice when publishing.

"""

FOOTER = """
## Summary

This appendix is a single-source, auto-generated reference to every buildable actor in OpenRA's four bundled mods, pairing each unit's cameo and internal codename with its faction, role, and core statistics drawn straight from the engine's own rules. It lowers the barrier to entry for new modders by putting the sprite, the YAML codename, and the numbers in one place, and it stays accurate over time because it is regenerated from the pinned source rather than maintained by hand.

## What to read next

- [Part 2.4 — Rules and Weapons](../chapters/Part_02_Chapter_04_Rules_Weapons.md) — how the actor and weapon YAML in these tables is defined.
- [Appendix H — Asset Visual Reference](Appendix_H_Asset_Visual_Reference.md) — the file formats and engine classes behind cameos, sprites, and other assets.
- [Part 10.3 — Porting and Modding](../chapters/Part_10_Chapter_03_Port_And_Modding.md) — creating your own actor from scratch.
"""


def main():
    manifest = {}; sections = []; total = 0
    for mod, label in MODS:
        rows = collect(mod)
        skip = SKIP_CODES.get(mod, set())
        rows = [r for r in rows if r['code'] not in skip]
        # Rich manifest: code -> resolved image name (used by extract_cameos.ps1).
        manifest[mod] = {r['code']: r['image'] for r in rows}; total += len(rows)
        os.makedirs(os.path.join(IMAGES, mod), exist_ok=True)
        for r in rows:
            code = r['code'].lower()
            placeholder(os.path.join(IMAGES, mod, code + ".png"), r['code'], r['faction'], 'cameo')
            placeholder(os.path.join(IMAGES, mod, code + "_unit.png"), r['code'], r['faction'], 'unit')
        sec = [f"## {label}\n", f"*{len(rows)} buildable actors.*\n"]
        for c in CAT_ORDER:
            sub = [r for r in rows if r['cat'] == c]
            if not sub:
                continue
            sec.append(f"### {label} — {c} ({len(sub)})\n")
            sec.append(table(mod, sub) + "\n")
        sections.append('\n'.join(sec))
    out = HEADER + '\n'.join(sections) + FOOTER
    with open(APPENDIX, "w", encoding="utf-8") as f:
        f.write(out)
    with open(os.path.join(BUILD, "actor_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=1)
    print(f"Wrote {APPENDIX}")
    print(f"Actors: {total}  " + "  ".join(f"{k}={len(v)}" for k, v in manifest.items()))


if __name__ == "__main__":
    main()
