from pathlib import Path
import re

for py_file in Path("src/dairyos").rglob("*.py"):
    content = py_file.read_text(encoding="utf-8")
    if 'def create_animal' in content or 'add_animal' in content or '/farm/animals' in content:
        for i, line in enumerate(content.splitlines(), start=1):
            if any(k in line for k in ["@app.post", "@router.post", "def "]) and "animal" in line.lower():
                print(f"{py_file}:{i} -> {line}")