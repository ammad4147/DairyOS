from pathlib import Path
import re

for py_file in Path("src/dairyos").rglob("*.py"):
    content = py_file.read_text(encoding="utf-8")
    if "_is_confirmed_pregnancy" in content or "confirmed_pregnancies" in content:
        print(f"=== File: {py_file} ===")
        for i, line in enumerate(content.splitlines(), start=1):
            if any(k in line for k in ["_is_confirmed_pregnancy", "confirmed_pregnancies", "def _management"]):
                print(f"{i:3d}: {line}")