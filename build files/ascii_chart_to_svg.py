# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""Convert Markdown code blocks containing box-drawing ASCII art into SVG figures.

The script scans a Markdown file for ``` code blocks that contain Unicode box-
drawing characters (┌ ┐ └ ┘ ─ │ ├ ┤ ┬ ┴ ┼ ► ▲), renders each block as a monospace
SVG, and replaces the code block with a standard Markdown image reference.
"""

import argparse
import html
import re
from pathlib import Path

# Unicode box-drawing / arrow / tree characters that signal an ASCII chart.
BOX_CHARS = re.compile(r"[\u2500-\u257F\u25B2\u25BC\u25C4\u25BA\u2192\u2190\u2191\u2193]")

# ASCII-only diagrams ("+----+", "|    |", arrows like v/^/</>)
ASCII_FRAME_LINE = re.compile(r"^\s*([\+\|].*[\+\|\-]|[\+\-]+\+|\|[^\+]*\|)\s*$")
ASCII_ARROW = re.compile(r"[v^<>]")
ASCII_BOX_CORNER = re.compile(r"\+")

SVG_TEMPLATE = """<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="100%" height="100%" fill="white"/>
  <text x="{pad_x}" y="{pad_y}" font-family="Consolas, 'Courier New', monospace" font-size="{font_size}" xml:space="preserve">
{lines}
  </text>
</svg>
"""


def is_ascii_chart(text):
    if BOX_CHARS.search(text):
        return True
    lines = text.splitlines()
    frame_lines = sum(1 for line in lines if ASCII_FRAME_LINE.match(line))
    box_corners = sum(1 for line in lines if len(ASCII_BOX_CORNER.findall(line)) >= 2)
    has_arrow = any(ASCII_ARROW.search(line) for line in lines)
    return (frame_lines >= 2 or box_corners >= 2) and has_arrow


def generate_svg(text, font_size=14, line_height=20, char_width=9, pad=20):
    lines = text.splitlines()
    if not lines:
        return ""
    max_len = max(len(line) for line in lines)
    width = max_len * char_width + pad * 2
    height = len(lines) * line_height + pad * 2

    rendered = []
    for i, line in enumerate(lines):
        dy = line_height if i else 0
        safe = html.escape(line)
        rendered.append(f'    <tspan x="{pad}" dy="{dy}">{safe}</tspan>')

    return SVG_TEMPLATE.format(
        width=width,
        height=height,
        pad_x=pad,
        pad_y=pad + line_height // 2,
        font_size=font_size,
        lines="\n".join(rendered),
    )


def slugify(text):
    text = text.strip().replace(" ", "_").replace("-", "_")
    text = re.sub(r"[^A-Za-z0-9_]+", "", text)
    return text[:80]


def convert_file(markdown_path, images_dir):
    text = markdown_path.read_text(encoding="utf-8")
    pattern = re.compile(r"^```([a-zA-Z0-9+#_-]*)\s*\n(.*?)\n```\s*$", re.DOTALL | re.MULTILINE)

    counter = 0

    def repl(match):
        nonlocal counter
        block = match.group(2)
        if not is_ascii_chart(block):
            return match.group(0)
        counter += 1

        # Find the preceding heading to use as caption/filename hint
        start = match.start()
        before = text[:start]
        heading = ""
        for m in re.finditer(r"^#+\s*(.+)$", before, re.MULTILINE):
            heading = m.group(1).strip()
        base = slugify(heading) or markdown_path.stem
        filename = f"{markdown_path.stem}-{base}-{counter}.svg"
        svg_path = images_dir / filename

        svg = generate_svg(block)
        svg_path.write_text(svg, encoding="utf-8")

        caption = heading or "Diagram"
        return f"![{caption}](images/{filename})"

    new_text = pattern.sub(repl, text)
    if counter:
        markdown_path.write_text(new_text, encoding="utf-8")
    return counter


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+", help="Markdown files to process")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    images_dir = root / "images"
    images_dir.mkdir(exist_ok=True)

    total = 0
    for f in args.files:
        n = convert_file(Path(f), images_dir)
        print(f"{f}: {n} chart(s) converted")
        total += n
    print(f"Total: {total} chart(s) converted")


if __name__ == "__main__":
    main()
