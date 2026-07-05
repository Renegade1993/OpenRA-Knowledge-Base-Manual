# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""Convert SVGs to PDFs for the Pandoc PDF pipeline.

Uses Microsoft Edge (or Google Chrome) headless mode to render SVGs that contain
foreignObject/HTML text that rsvg-convert cannot handle. Outputs are cached in
"build files/svg-pdf-cache/" so only changed SVGs are reconverted.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MANUAL_ROOT = ROOT.parent
IMAGES_DIR = MANUAL_ROOT / "images"
CACHE_DIR = ROOT / "svg-pdf-cache"
MANIFEST = CACHE_DIR / "manifest.json"
COMBINED = MANUAL_ROOT / "OpenRA_Knowledge_Base_Manual.md"

BROWSER_CANDIDATES = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
]


def find_browser():
    for c in BROWSER_CANDIDATES:
        p = Path(c)
        if p.exists():
            return str(p)
    # Try PATH
    for name in ("msedge", "chrome"):
        try:
            r = subprocess.run(["where", name], capture_output=True, text=True, timeout=5)
            if r.returncode == 0:
                return r.stdout.strip().splitlines()[0]
        except Exception:
            pass
    return None


def parse_svg_size(svg_path):
    """Extract a tight (width, height) in points from the SVG's viewBox or width/height."""
    text = svg_path.read_text(encoding="utf-8")
    # Find viewBox="x y w h"
    import re
    m = re.search(r'viewBox=["\']([^"\']+)["\']', text)
    if m:
        parts = m.group(1).split()
        if len(parts) == 4:
            try:
                w = float(parts[2])
                h = float(parts[3])
                if w > 0 and h > 0:
                    return w, h
            except ValueError:
                pass
    # Fall back to width/height attributes
    wm = re.search(r'width=["\']([^"\']+)["\']', text)
    hm = re.search(r'height=["\']([^"\']+)["\']', text)
    if wm and hm:
        try:
            w = float(wm.group(1).replace("px", "").replace("pt", ""))
            h = float(hm.group(1).replace("px", "").replace("pt", ""))
            if w > 0 and h > 0:
                return w, h
        except ValueError:
            pass
    # Default to letter size
    return 612, 792


def convert_one(browser, svg_path, pdf_path):
    w, h = parse_svg_size(svg_path)
    svg_text = svg_path.read_text(encoding="utf-8")
    html_path = svg_path.with_suffix(".html")
    html = (
        "<!DOCTYPE html>\n"
        "<html>\n<head>\n"
        "<meta charset=\"utf-8\">\n"
        "<style>\n"
        f"@page {{ size: {w:.2f}pt {h:.2f}pt; margin: 0; }}\n"
        "body { margin: 0; padding: 0; }\n"
        "svg { width: 100%; height: 100%; max-width: none !important; max-height: none !important; }\n"
        "</style>\n"
        "</head>\n<body>\n"
        f"{svg_text}\n"
        "</body>\n</html>\n"
    )
    html_path.write_text(html, encoding="utf-8")
    url = html_path.as_uri()
    user_data_dir = tempfile.mkdtemp(prefix="edge_pdf_")
    cmd = [
        browser,
        "--headless",
        "--disable-gpu",
        "--no-sandbox",
        "--disable-software-rasterizer",
        "--disable-extensions",
        "--disable-background-networking",
        "--disable-sync",
        "--metrics-recording-only",
        "--disable-default-apps",
        "--no-first-run",
        "--no-pdf-header-footer",
        "--user-data-dir=" + user_data_dir,
        f"--print-to-pdf={pdf_path}",
        url,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    except subprocess.TimeoutExpired:
        return (str(svg_path), False, "timeout")
    except Exception as e:
        return (str(svg_path), False, str(e))
    finally:
        shutil.rmtree(user_data_dir, ignore_errors=True)
        try:
            html_path.unlink()
        except Exception:
            pass
    if result.returncode != 0 or not pdf_path.exists() or pdf_path.stat().st_size < 1000:
        return (str(svg_path), False, result.stderr or result.stdout or "empty output")
    return (str(svg_path), True, "")


def list_required_svgs():
    svgs = set()
    if COMBINED.exists():
        text = COMBINED.read_text(encoding="utf-8")
        for line in text.splitlines():
            if "](images/" in line and ".svg" in line:
                start = line.find("](images/") + 2
                end = line.find(".svg)", start)
                if end != -1:
                    svgs.add(line[start:end + 4])
    # Fallback: include all SVGs in the images directory
    if not svgs:
        for p in IMAGES_DIR.glob("*.svg"):
            svgs.add(f"images/{p.name}")
    return sorted(svgs)


def main():
    browser = find_browser()
    if not browser:
        print("WARNING: No Edge/Chrome browser found for SVG conversion. Falling back to Pandoc default.", file=sys.stderr)
        sys.exit(0)
    print(f"Using browser for SVG conversion: {browser}")

    CACHE_DIR.mkdir(exist_ok=True)
    svgs = list_required_svgs()

    manifest = {}
    if MANIFEST.exists():
        try:
            manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        except Exception:
            manifest = {}

    todo = []
    for rel in svgs:
        svg = MANUAL_ROOT / rel
        if not svg.exists():
            print(f"WARNING: SVG not found: {rel}", file=sys.stderr)
            continue
        pdf = CACHE_DIR / (svg.stem + ".pdf")
        svg_mtime = svg.stat().st_mtime
        cached_mtime = manifest.get(pdf.name, 0)
        if not pdf.exists() or pdf.stat().st_mtime < svg_mtime or cached_mtime < svg_mtime:
            todo.append((svg, pdf))

    if not todo:
        print(f"All {len(svgs)} SVGs are already cached as PDFs.")
        return

    print(f"Converting {len(todo)} SVGs to PDFs...")
    failed = []
    done = 0
    start = time.time()

    with ThreadPoolExecutor(max_workers=6) as ex:
        futures = {ex.submit(convert_one, browser, svg, pdf): (svg, pdf) for svg, pdf in todo}
        for future in as_completed(futures):
            svg_str, ok, err = future.result()
            done += 1
            if not ok:
                failed.append((svg_str, err))
            if done % 20 == 0 or done == len(todo):
                print(f"  {done}/{len(todo)} converted ({time.time()-start:.1f}s); {len(failed)} failed")

    if failed:
        print(f"WARNING: {len(failed)} SVG conversions failed", file=sys.stderr)
        for svg_str, err in failed[:10]:
            print(f"  {svg_str}: {err[:200]}", file=sys.stderr)

    # Update manifest
    new_manifest = {}
    for pdf in CACHE_DIR.glob("*.pdf"):
        new_manifest[pdf.name] = pdf.stat().st_mtime
    MANIFEST.write_text(json.dumps(new_manifest, indent=2), encoding="utf-8")
    print(f"Done. {done - len(failed)}/{len(todo)} PDFs ready in {CACHE_DIR}")


if __name__ == "__main__":
    main()
