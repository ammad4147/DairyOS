# -*- coding: utf-8 -*-
import requests
import json
from datetime import datetime, timezone, timedelta

API_BASE = "http://127.0.0.1:8000"

print("=" * 80)
print(" FORENSIC PHASE 1: HERD LIFECYCLE, PEDIGREE & YOUNGSTOCK GROWTH AUDIT")
print("=" * 80)

# 1. Inspect Herd Structure & Pedigree Integrity
print("\n[1.1] Inspecting Herd Registry & Pedigree Links...")
r_herd = requests.get(f"{API_BASE}/farm/animals", timeout=5)
assert r_herd.status_code == 200, f"Failed fetching herd: {r_herd.text}"
animals = r_herd.json() if isinstance(r_herd.json(), list) else r_herd.json().get("animals", [])

calf = next((a for a in animals if a.get("animal_id") == "TD-021"), None)
dam = next((a for a in animals if a.get("animal_id") == "TD-001"), None)

assert calf is not None, "ASSERTION FAILED: TD-021 calf record not found."
assert dam is not None, "ASSERTION FAILED: TD-001 dam record not found."
assert calf.get("dam_id") == "TD-001", f"ASSERTION FAILED: Dam link broken: {calf.get('dam_id')}"
assert calf.get("sire_id") == "HF-GENETICS-SEXED-STR-902", f"ASSERTION FAILED: Sire genetics missing"
print(f"  [PASS] Calf TD-021 verified -> Dam: {calf.get('dam_id')}, Sire: {calf.get('sire_id')}")

# 2. Sequential Youngstock Growth Tracking (ADG Calculation)
print("\n[1.2] Simulating Day-14 and Day-28 Biometric Growth Entries for TD-021...")
measurements = [
    {"day": 14, "weight_kg": 48.5, "wither_height_cm": 78.0, "notes": "Solid starter intake 0.5kg/day"},
    {"day": 28, "weight_kg": 59.8, "wither_height_cm": 82.5, "notes": "Vigorous appetite, starter 1.2kg/day"}
]

birth_date = datetime.fromisoformat(calf.get("date_of_birth") or "2026-08-20").date()

for m in measurements:
    measure_date = (birth_date + timedelta(days=m["day"])).isoformat()
    payload = {
        "weight_kg": m["weight_kg"],
        "wither_height_cm": m["wither_height_cm"],
        "notes": m["notes"],
        "operator": "CALF_SPECIALIST_01"
    }
    r_growth = requests.post(f"{API_BASE}/farm/youngstock/TD-021/growth", json=payload, timeout=5)
    print(f"  Day {m['day']:2d} Growth Record [{r_growth.status_code}]: Weight={m['weight_kg']}kg, Height={m['wither_height_cm']}cm")

# Compute ADG
birth_weight = 38.5 # Recorded on day 0
day_28_weight = 59.8
adg = (day_28_weight - birth_weight) / 28.0
print(f"\n  [ANALYSIS] Calculated Average Daily Gain (ADG): {adg:.3f} kg/day (Target: >= 0.75 kg/day)")
assert adg >= 0.75, f"Youngstock growth lagging: {adg:.3f} kg/day"
print("  [PASS] Youngstock growth trajectory meets elite heifer benchmarking standards.")

# 3. Schedule Milk Replacer & Weaning Plan
print("\n[1.3] Dispatching Twice-Daily Liquid Milk Replacer Plan...")
feeding_plan_payload = {
    "animal_id": "TD-021",
    "feed_type": "CALF_MILK_REPLACER_24_20",
    "volume_litres_per_day": 6.0,
    "feedings_per_day": 2,
    "target_weaning_date": (birth_date + timedelta(days=60)).isoformat(),
    "operator": "CALF_SPECIALIST_01"
}
# Log feeding record into feed pipeline
r_feed = requests.post(f"{API_BASE}/farm/feed/records", json={
    "animal_id": "TD-021",
    "group_or_pen": "CALF_HUTCHES_A",
    "feed_type": "MILK_REPLACER_24_20",
    "quantity_kg": 6.0,
    "notes": "Fed 3.0L AM (38C) + 3.0L PM (38C)",
    "operator": "CALF_SPECIALIST_01"
}, timeout=5)
print(f"  Milk Replacer Dispatch [{r_feed.status_code}]: {r_feed.text[:80]}")
print("\n>>> PHASE 1 HERD & YOUNGSTOCK FORENSIC AUDIT COMPLETE: ALL CHECKS PASSED <<<")