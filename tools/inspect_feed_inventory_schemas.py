# -*- coding: utf-8 -*-
from pathlib import Path

p = Path("src/dairyos/api/farm_data_entry.py")
txt = p.read_text(encoding="utf-8")
lines = txt.splitlines()

print("=== 1. RATION ENTRY SCHEMA ===")
for i, line in enumerate(lines, start=1):
    if "class FeedRationEntryRequest" in line or "class Ration" in line or "@router.post(\"/feed/rations\")" in line:
        start = max(0, i - 10)
        end = min(len(lines), i + 30)
        for j in range(start, end):
            print(f"{j+1:3d}: {lines[j]}")
        break

print("\n=== 2. INVENTORY ENTRY SCHEMA ===")
for i, line in enumerate(lines, start=1):
    if "class InventoryEntryRequest" in line or "@router.post(\"/inventory\")" in line:
        start = max(0, i - 10)
        end = min(len(lines), i + 30)
        for j in range(start, end):
            print(f"{j+1:3d}: {lines[j]}")
        break