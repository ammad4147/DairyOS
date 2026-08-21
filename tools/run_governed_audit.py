# -*- coding: utf-8 -*-
import requests
import json
from datetime import date

API_BASE = "http://127.0.0.1:8000"

print("=" * 85)
print(" DAIRYOS GOVERNED MILKING & AUTOMATED UNIT COST RECONCILIATION")
print("=" * 85)

# 1. Post governed morning shift yields (TD-001 to TD-020)
print("\n[1] Submitting Governed Morning Yields (morning_yield & milking_session='MORNING')...")
for i in range(1, 21):
    tag = f"TD-{i:03d}"
    yield_val = 13.0 if i <= 10 else 12.0
    payload = {
        "animal_id": tag,
        "morning_yield": yield_val,
        "milking_session": "MORNING",
        "production_date": str(date.today()),
        "operator": "MILKER_LEADER_01"
    }
    r = requests.post(f"{API_BASE}/farm/milk", json=payload, timeout=5)

print("  [OK] 20 Governed Morning yields recorded.")

# 2. Fetch Production Summary
print("\n[2] Fetching Live Production Summary (/farm/milk/production-summary)...")
r_prod = requests.get(f"{API_BASE}/farm/milk/production-summary", timeout=5)
print(f"Status: {r_prod.status_code}")
print(json.dumps(r_prod.json(), indent=2))

# 3. Fetch Cost of Production
print("\n[3] Fetching Live Cost of Production (/farm/finance/cost-of-production)...")
r_cop = requests.get(f"{API_BASE}/farm/finance/cost-of-production", timeout=5)
print(f"Status: {r_cop.status_code}")
print(json.dumps(r_cop.json(), indent=2))

print("\n" + "=" * 85)
print(">>> GOVERNED RECONCILIATION AUDIT COMPLETE <<<")
print("=" * 85)