# -*- coding: utf-8 -*-
from pathlib import Path

p = Path("src/dairyos/api/milk_production_summary.py")
txt = p.read_text(encoding="utf-8")

# Helper placed at top
helper_def = """
def _clean_kpi_num(val):
    if val is None:
        return None
    r = round(float(val), 2)
    return int(round(r)) if abs(r - round(r)) < 0.0001 else r
"""

if "_clean_kpi_num(" not in txt:
    txt = helper_def + "\n" + txt

# Target specifically the "kpis": { ... } construction block around lines 676-695
old_block = """            "kpis": {
                "total_production_liters": (
                    current["total_liters"]
                ),
                "average_per_day_liters": (
                    current["average_liters_per_day"]
                ),
                "average_per_cow_liters": (
                    current["average_liters_per_cow"]
                ),
                "morning_liters": (
                    current["morning_liters"]
                ),
                "evening_liters": (
                    current["evening_liters"]
                ),"""

new_block = """            "kpis": {
                "total_production_liters": _clean_kpi_num(current["total_liters"]),
                "average_per_day_liters": _clean_kpi_num(current["average_liters_per_day"]),
                "average_per_cow_liters": _clean_kpi_num(current["average_liters_per_cow"]),
                "morning_liters": _clean_kpi_num(current["morning_liters"]),
                "evening_liters": _clean_kpi_num(current["evening_liters"]),"""

if old_block in txt:
    txt = txt.replace(old_block, new_block)
    p.write_text(txt, encoding="utf-8")
    print("[OK] Targeted KPI response block successfully patched.")
else:
    print("[INFO] Attempting normalized block replacement...")
    import re
    # Match and replace only inside the kpis dict
    pattern = r'("kpis":\s*\{\s*"total_production_liters":\s*\(\s*current\["total_liters"\]\s*\),\s*"average_per_day_liters":\s*\(\s*current\["average_liters_per_day"\]\s*\),\s*"average_per_cow_liters":\s*\(\s*current\["average_liters_per_cow"\]\s*\),\s*"morning_liters":\s*\(\s*current\["morning_liters"\]\s*\),\s*"evening_liters":\s*\(\s*current\["evening_liters"\]\s*\),)'
    txt = re.sub(pattern, new_block, txt)
    p.write_text(txt, encoding="utf-8")
    print("[OK] Regex pattern replacement applied.")