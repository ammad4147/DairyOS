# -*- coding: utf-8 -*-
from pathlib import Path

target_file = Path("src/dairyos/farm/operations/state/farm_operational_state.py")
content = target_file.read_text(encoding="utf-8")

# Fix line 193 explicitly as well
old_line_193 = 'self.milk_production_summary["total_litres_today"] += litres'
safe_line_193 = 'self.milk_production_summary["total_litres_today"] = float(self.milk_production_summary.get("total_litres_today") or 0.0) + float(litres or 0.0)'

if old_line_193 in content:
    content = content.replace(old_line_193, safe_line_193)
    target_file.write_text(content, encoding="utf-8")
    print(f"[OK] Patched line 193 with null-safe accumulator.")
else:
    print("[INFO] Line 193 already patched or modified.")