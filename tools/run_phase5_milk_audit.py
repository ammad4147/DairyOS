# -*- coding: utf-8 -*-
import requests
import json

API_BASE = "http://127.0.0.1:8000"

print("=" * 85)
print(" FORENSIC PHASE 5: MILKING SESSIONS, YIELD AGGREGATION & BULK TANK AUDIT")
print("=" * 85)

# 1. Log Morning Milking Session for all 20 cows
print("\n[5.1] Logging Morning Milking Session (TD-001 to TD-020)...")
session_records = []
total_recorded_yield = 0.0
diverted_yield = 0.0
saleable_yield = 0.0

for i in range(1, 21):
    tag = f"TD-{i:03d}"
    # Standard yield: 13.0L for high-yield (TD-001..10), 12.0L for fresh (TD-011..20)
    base_yield = 13.0 if i <= 10 else 12.0
    
    payload = {
        "animal_id": tag,
        "shift": "MORNING",
        "yield_litres": base_yield,
        "is_valid": True,
        "operator": "MILKER_LEADER_01"
    }
    r = requests.post(f"{API_BASE}/farm/milk", json=payload, timeout=5)
    data = r.json()
    
    is_warning = data.get("withdrawal_warning", False)
    total_recorded_yield += base_yield
    
    if tag == "TD-003" or is_warning:
        diverted_yield += base_yield
        print(f"  • {tag}: {base_yield:.1f} L -> [FLAGGED FOR WITHHOLDING DIVERSION] (Warning={is_warning})")
    else:
        saleable_yield += base_yield

print(f"\n  [SHIFT RECONCILIATION]")
print(f"  • Total Shift Output:   {total_recorded_yield:.1f} L")
print(f"  • Diverted Milk (MRL):  {diverted_yield:.1f} L (Animal TD-003 under active withdrawal)")
print(f"  • Net Saleable to Tank: {saleable_yield:.1f} L")

# 2. Query Milk Production Summary
print("\n[5.2] Fetching Consolidated Production Summary (/farm/milk/production-summary)...")
r_summary = requests.get(f"{API_BASE}/farm/milk/production-summary", timeout=5)
print(f"  Summary Status [{r_summary.status_code}]:")
if r_summary.status_code == 200:
    print(json.dumps(r_summary.json(), indent=2))
else:
    print(r_summary.text[:120])

# 3. Query Animal-Specific Production History for TD-001
print("\n[5.3] Querying Individual Production History for TD-001...")
r_cow_milk = requests.get(f"{API_BASE}/farm/animals/TD-001/production", timeout=5)
print(f"  TD-001 Production Status [{r_cow_milk.status_code}]:")
if r_cow_milk.status_code == 200:
    print(json.dumps(r_cow_milk.json(), indent=2))
else:
    print(r_cow_milk.text[:120])

print("\n" + "=" * 85)
print(">>> FORENSIC PHASE 5 MILKING AUDIT COMPLETE <<<")
print("=" * 85)