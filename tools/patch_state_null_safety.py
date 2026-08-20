# -*- coding: utf-8 -*-
from pathlib import Path

target_file = Path("src/dairyos/farm/operations/state/farm_operational_state.py")
content = target_file.read_text(encoding="utf-8")

# Replace direct += addition with null-safe numeric coercion
target_str = 'entry["litres"] += litres'
safe_str = 'entry["litres"] = float(entry.get("litres") or 0.0) + float(litres or 0.0)'

if target_str in content:
    new_content = content.replace(target_str, safe_str)
    target_file.write_text(new_content, encoding="utf-8")
    print(f"[OK] Patched {target_file} with null-safe float coercion.")
else:
    print(f"[INFO] Target string '{target_str}' not found or already patched.")