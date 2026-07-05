# -*- coding: utf-8 -*-
import re
from pathlib import Path

files = [
    "chapters/Part_02_Chapter_01_MiniYaml.md",
    "chapters/Part_03_Chapter_02_SDK_Bootstrap.md",
    "chapters/Part_04_Chapter_03_Widgets.md",
    "chapters/Part_07_Chapter_02_Data_Structures.md",
    "chapters/Part_09_Chapter_02_Server_Connection.md",
]

root = Path(__file__).resolve().parent

for rel in files:
    path = root / rel
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    # Check code blocks are balanced
    fence_count = 0
    for i, line in enumerate(lines):
        if line.startswith("```"):
            fence_count += 1
    if fence_count % 2 != 0:
        print(f"ERROR: {rel} has unbalanced code fences ({fence_count})")
    else:
        print(f"OK: {rel} has balanced code fences ({fence_count})")

    # Check for image references that appear inside code blocks
    # Heuristic: image reference line immediately after opening fence or before closing fence
    in_code_block = False
    for i, line in enumerate(lines):
        if line.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block and "![" in line and "](images/" in line:
            print(f"ERROR: {rel}:{i+1} image reference inside code block")

    # Check for backtick artifacts like "```csharp" merged with text
    for i, line in enumerate(lines):
        if re.search(r"```[a-zA-Z0-9+#_-]+[a-zA-Z0-9+#_\s-]", line) and not line.startswith("```"):
            print(f"ERROR: {rel}:{i+1} stray code fence marker: {line[:80]!r}")

print("Check complete.")
