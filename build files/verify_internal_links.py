#!/usr/bin/env python3
"""Verify internal markdown links in the OpenRA Knowledge Base Manual."""

import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
MANUAL_FILE = BASE_DIR.parent / "OpenRA_Knowledge_Base_Manual.md"


def main():
    text = MANUAL_FILE.read_text(encoding="utf-8")

    # Match markdown links [text](target)
    link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

    # Known external or special targets
    allowed_external_prefixes = (
        "http://", "https://", "mailto:", "#", "file://",
    )

    broken = []
    for match in link_pattern.finditer(text):
        label, target = match.group(1), match.group(2)

        # Skip external links, anchors, and mailto
        if any(target.startswith(p) for p in allowed_external_prefixes):
            continue

        # Skip anchor-only links within the same document (already handled by #)
        if target.startswith("#"):
            continue

        # Resolve relative to the combined manual's directory (where the rendered manual lives)
        target_path = (MANUAL_FILE.parent / target).resolve()
        if not target_path.exists():
            broken.append((match.start(), label, target))

    print(f"Internal links checked: {sum(1 for _ in link_pattern.finditer(text))}")
    print(f"Broken internal links: {len(broken)}")
    if broken:
        report_path = BASE_DIR / "internal_link_report.txt"
        with report_path.open("w", encoding="utf-8") as f:
            for pos, label, target in broken:
                f.write(f"BROKEN at offset {pos}: [{label}]({target})\n")
        print(f"See {report_path} for the list of broken links.")
        raise SystemExit(1)

    # Clean up any stale report from a previous failed run.
    report_path = BASE_DIR / "internal_link_report.txt"
    if report_path.exists():
        report_path.unlink()

    print("All internal links resolve to existing files.")


if __name__ == "__main__":
    main()
