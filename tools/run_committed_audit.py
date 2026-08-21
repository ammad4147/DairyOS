# -*- coding: utf-8 -*-
import requests
import json
from datetime import date

API_BASE = "http://127.0.0.1:8000"

print("=" * 85)
print(" DAIRYOS COMMITTED MILKING SESSION & COST OF PRODUCTION RECONCILIATION")
print("=" * 85)

# 1. Post committed morning shift yields for all 20 lactating cows
print("\n[1] Submitting Committed Session Yields (session_ledger=True)...")
for i in range(1, 21):
    tag = f"TD-{i:03d}"
    yield_val = 13.0 if i <= 10 else 12.0
    payload = {
        "animal_id": tag,
        "shift": "MORNING",
        "yield_litres": yield_val,
        "is_valid": True,
        "session_ledger": True,
        "production_date": str(date.today()),
        "operator": "MILKER_LEADER_01"
    }
    r = requests.post(f"{API_BASE}/farm/milk", json=payload, timeout=5)

print("  [OK] 20 Animal yields committed to live session ledger.")

# 2. Fetch Production Summary
print("\n[2] Fetching Live Production Summary (/farm/milk/production-summary)...")
r_prod = requests.get(f"{API_BASE}/farm/milk/production-summary", timeout=5)
prod_data = r_prod.json()
print(f"Status: {r_prod.status_code}")
print(json.dumps(prod_data, indent=2))

# 3. Fetch Cost of Production
print("\n[3] Fetching Live Cost of Production (/farm/finance/cost-of-production)...")
r_cop = requests.get(f"{API_BASE}/farm/finance/cost-of-production", timeout=5)
cop_data = r_cop.json()
print(f"Status: {r_cop.status_code}")
print(json.dumps(cop_data, indent=2))

print("\n" + "=" * 85)
print(">>> COMMITTED RECONCILIATION AUDIT COMPLETE <<<")
print("=" * 85)