# -*- coding: utf-8 -*-
from pathlib import Path

p = Path("src/dairyos/api/farm_data_entry.py")
txt = p.read_text(encoding="utf-8")
lines = txt.splitlines()

for i, line in enumerate(lines, start=1):
    if "class MilkEntryRequest" in line:
        for j in range(max(0, i - 2), min(len(lines), i + 25)):
            print(f"{j+1:3d}: {lines[j]}")
        break