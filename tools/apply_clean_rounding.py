# -*- coding: utf-8 -*-
from pathlib import Path

p = Path("src/dairyos/api/milk_production_summary.py")
txt = p.read_text(encoding="utf-8")

helper_def = """
def _clean_num(val):
    if val is None:
        return None
    r = round(float(val), 2)
    return int(round(r)) if abs(r - round(r)) < 0.0001 else r
"""

if "_clean_num(" not in txt:
    txt = helper_def + "\n" + txt

# Direct string replacements for KPI dictionary packaging
replacements = [
    ('current["total_liters"]', '_clean_num(current["total_liters"])'),
    ('current["average_liters_per_day"]', '_clean_num(current["average_liters_per_day"])'),
    ('current["average_liters_per_cow"]', '_clean_num(current["average_liters_per_cow"])'),
    ('current["morning_liters"]', '_clean_num(current["morning_liters"])'),
    ('current["evening_liters"]', '_clean_num(current["evening_liters"])'),
]

for target, repl in replacements:
    # Only replace where it is inside the KPIs block if not already replaced
    if target in txt and repl not in txt:
        txt = txt.replace(target, repl)

p.write_text(txt, encoding="utf-8")
print("[OK] src/dairyos/api/milk_production_summary.py patched cleanly.")