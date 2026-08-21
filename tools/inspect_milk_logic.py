# -*- coding: utf-8 -*-
from pathlib import Path

for file_path in [Path("src/dairyos/api/farm_data_entry.py"), Path("src/dairyos/farm/operations/milk/production_summary.py")]:
    if file_path.exists():
        txt = file_path.read_text(encoding="utf-8")
        print(f"=== {file_path.name} ===")
        lines = txt.splitlines()
        for i, l in enumerate(lines, start=1):
            if any(k in l for k in ["def get_milk_production_summary", "def record_milk_entry", "morning_yield"]):
                for j in range(max(0, i - 2), min(len(lines), i + 25)):
                    print(f"{j+1:3d}: {lines[j]}")
                break