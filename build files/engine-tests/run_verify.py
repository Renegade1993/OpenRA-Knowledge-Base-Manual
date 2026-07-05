#!/usr/bin/env python3
import subprocess
import sys

build_dir = r"C:\Users\Kmoney\Documents\AI Projects\Cameo Work\Game Sources and Development Reference Materials\OpenRA Manual\build files"

commands = [
    ["python", "assemble_manual.py"],
    ["python", "verify_paths.py"],
    ["python", "verify_internal_links.py"],
]

for cmd in commands:
    print(f"\n=== {' '.join(cmd)} ===")
    result = subprocess.run(cmd, cwd=build_dir, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print(result.stdout)
    if result.returncode != 0:
        print(f"FAILED with exit code {result.returncode}")
        sys.exit(result.returncode)

print("\nAll verification commands passed.")
