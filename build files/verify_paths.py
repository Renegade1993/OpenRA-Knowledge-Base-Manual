#!/usr/bin/env python3
"""Verify file paths referenced in the combined manual against the cloned OpenRA source."""

import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
MANUAL_FILE = BASE_DIR.parent / "OpenRA_Knowledge_Base_Manual.md"
SOURCE_ROOT = Path("C:/Users/Kmoney/Documents/AI Projects/Cameo Work/Game Sources and Development Reference Materials/OpenRA GitHub Repositories/OpenRA")


def main():
    text = MANUAL_FILE.read_text(encoding="utf-8")

    # Pattern 1: plain OpenRA/Project/Dir/File.cs or .csproj references
    pattern1 = re.compile(
        r"OpenRA(?:\.Mods\.(?:Common|Cnc|D2k)|\.Game|\.Platforms\.Default|\.Server|\.Test|\.Launcher|\.WindowsLauncher|\.Utility)(?:/[A-Za-z0-9_\-\.]+)+\.(?:csproj|cs)"
    )
    # Pattern 2: paths wrapped in backticks, possibly without .cs extension
    pattern2 = re.compile(
        r"`((?:OpenRA(?:\.Mods\.(?:Common|Cnc|D2k)|\.Game|\.Platforms\.Default|\.Server|\.Test|\.Launcher|\.WindowsLauncher|\.Utility)(?:/[A-Za-z0-9_\-\.]+)+)(?:\.(?:csproj|cs))?)`"
    )

    # Paths that are explicitly referenced as old/removed/non-existent in the manual.
    INTENTIONAL_EXCEPTIONS = {
        "OpenRA.Game/GameRules/RulesetCache.cs",
        "OpenRA.Game/MathUtils.cs",
        "OpenRA.Mods.Common/Traits/World/MapGeneratorLogic.cs",
        "OpenRA.Mods.Common/Traits/World/MapGeneratorToolLogic.cs",
        "OpenRA.Game/GameRules/DamageTypes.cs",
    }

    matches = set(pattern1.findall(text))
    matches.update(m.group(1) for m in pattern2.finditer(text))

    missing = []
    for path in sorted(matches):
        if path in INTENTIONAL_EXCEPTIONS:
            continue
        fs_path = SOURCE_ROOT / Path(path.replace("/", "\\"))
        if not fs_path.exists():
            missing.append(path)

    print(f"Total unique file paths checked: {len(matches)}")
    print(f"Paths not found: {len(missing)}")
    for path in missing:
        print(f"  MISSING: {path}")

    if missing:
        raise SystemExit(1)

    print("All referenced paths exist in the cloned source.")


if __name__ == "__main__":
    main()
