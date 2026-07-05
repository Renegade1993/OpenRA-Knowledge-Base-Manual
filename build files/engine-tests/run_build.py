#!/usr/bin/env python3
import subprocess
import sys

repo = r"C:\Users\Kmoney\Documents\AI Projects\Cameo Work\Game Sources and Development Reference Materials\OpenRA GitHub Repositories\OpenRA"
result = subprocess.run(
    [repo + r"\make.cmd", "all"],
    cwd=repo,
    text=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT
)
print(result.stdout)
print(f"Exit code: {result.returncode}")
sys.exit(result.returncode)
