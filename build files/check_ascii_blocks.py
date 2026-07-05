# -*- coding: utf-8 -*-
import re
from pathlib import Path

BOX_CHARS = re.compile(r"[\u2500-\u257F\u25B2\u25BC\u25C4\u25BA\u2192\u2190\u2191\u2193]")

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
    # Match code blocks with optional language tag
    for m in re.finditer(r"^```([a-zA-Z0-9+#_-]*)\s*\n(.*?)\n```", text, re.DOTALL | re.MULTILINE):
        lang = m.group(1)
        block = m.group(2)
        if BOX_CHARS.search(block):
            start = text[:m.start()].count("\n") + 1
            print(f"{rel}:{start} lang={lang!r} has box-drawing chars")
