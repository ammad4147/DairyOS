# -*- coding: utf-8 -*-
from pathlib import Path
import re

p = Path("src/dairyos/api/farm_data_entry.py")
txt = p.read_text(encoding="utf-8")
lines = txt.splitlines()

for i, line in enumerate(lines, start=1):
    if "@router.post(\"/breeding\")" in line or "@router.post('/breeding')" in line:
        start = max(0, i - 1)
        end = min(len(lines), i + 40)
        for j in range(start, end):
            print(f"{j+1:3d}: {lines[j]}")
        break