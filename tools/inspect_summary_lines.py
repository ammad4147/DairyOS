# -*- coding: utf-8 -*-
from pathlib import Path

p = Path("src/dairyos/api/milk_production_summary.py")
txt = p.read_text(encoding="utf-8")
lines = txt.splitlines()

for i, line in enumerate(lines, start=1):
    if any(k in line for k in ["total_production", "average_per", "morning_liters", "evening_liters", "liters", "litres"]):
        print(f"{i:3d}: {line}")