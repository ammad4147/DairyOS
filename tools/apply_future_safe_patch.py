# -*- coding: utf-8 -*-
from pathlib import Path

p = Path("src/dairyos/api/milk_production_summary.py")
txt = p.read_text(encoding="utf-8")

helper_func = """

def _clean_kpi_num(val):
    if val is None:
        return None
    r = round(float(val), 2)
    return int(round(r)) if abs(r - round(r)) < 0.0001 else r
"""

# Insert helper right before the router definition
if "router = APIRouter(" in txt:
    txt = txt.replace("router = APIRouter(", helper_func + "\nrouter = APIRouter(")
elif "def get_milk_production_summary" in txt:
    txt = txt.replace("def get_milk_production_summary", helper_func + "\ndef get_milk_production_summary")

# Apply clean packaging to the kpis block
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
print("[OK] milk_production_summary.py patched with valid Python __future__ positioning.")