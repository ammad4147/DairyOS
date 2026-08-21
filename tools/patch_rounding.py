# -*- coding: utf-8 -*-
from pathlib import Path
import re

p = Path("src/dairyos/api/milk_production_summary.py")
txt = p.read_text(encoding="utf-8")

# Helper function to round floating points cleanly to whole numbers or 1 decimal place
def clean_round(val):
    if val is None:
        return None
    r = round(float(val), 2)
    return int(r) if r.is_integer() else r

# Let's check how the summary aggregates totals
print(f"File length: {len(txt)} chars")

# We apply round(..., 1) or int(round(...)) where totals are packaged
patched = txt
# Ensure total sums and averages don't leak IEEE-754 precision
patched = re.sub(r'(\b(?:total_production_liters|morning_liters|evening_liters|average_per_day_liters)\s*:\s*)([a-zA-Z0-9_\.]+)', 
                 r'\1(round(\2) if \2 is not None and isinstance(\2, (int, float)) else \2)', patched)

if patched != txt:
    p.write_text(patched, encoding="utf-8")
    print("[OK] milk_production_summary.py successfully updated with clean whole-number rounding.")
else:
    print("[INFO] Checking file structure directly...")
    # Print lines where response dictionary / model is constructed
    lines = txt.splitlines()
    for i, line in enumerate(lines, start=1):
        if "total_production_liters" in line or "kpis" in line:
            start = max(0, i - 5)
            end = min(len(lines), i + 20)
            for j in range(start, end):
                print(f"{j+1:3d}: {lines[j]}")
            break