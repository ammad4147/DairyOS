# -*- coding: utf-8 -*-
import requests
import json

API_BASE = "http://127.0.0.1:8000"

print("=" * 85)
print(" FORENSIC PHASE 4 (CORRECTED): NUTRITION & TMR FORMULATION AUDIT")
print("=" * 85)

# 1. Ingest Stock Receipts
print("\n[4.1] Ingesting Commodity Stock Movements...")
commodities = [
    {"item_name": "Corn Silage", "category": "FEED", "quantity": 15000.0, "unit": "KG", "cost_per_unit": 18.0},
    {"item_name": "Alfalfa Hay", "category": "FEED", "quantity": 5000.0, "unit": "KG", "cost_per_unit": 42.0},
    {"item_name": "Dairy Concentrate 18% CP", "category": "FEED", "quantity": 6000.0, "unit": "KG", "cost_per_unit": 115.0},
    {"item_name": "Mineral Premix", "category": "FEED", "quantity": 500.0, "unit": "KG", "cost_per_unit": 350.0}
]

for c in commodities:
    payload = {
        "item_name": c["item_name"],
        "category": c["category"],
        "movement_type": "IN",
        "quantity": c["quantity"],
        "unit": c["unit"],
        "cost_per_unit": c["cost_per_unit"],
        "notes": "Bulk feed warehouse stock",
        "operator": "STORE_MANAGER_01"
    }
    r = requests.post(f"{API_BASE}/farm/inventory", json=payload, timeout=5)
    print(f"  Inventory Inflow [{r.status_code}]: {c['item_name']} -> {c['quantity']} {c['unit']}")
    if r.status_code != 200:
        print(f"    Error detail: {r.text}")

# 2. Register Active TMR Formulation with 'ingredients' field
print("\n[4.2] Registering Active TMR Formulation (TMR-LACT-HIGH-01)...")
ration_payload = {
    "name": "TMR-LACT-HIGH-01",
    "animal_group": "HIGH_YIELD_LACTATING",
    "target_dmi_kg": 22.5,
    "dry_matter_pct": 62.86,
    "crude_protein_pct": 16.8,
    "ndf_pct": 31.5,
    "energy_mcal_kg": 1.68,
    "cost_per_kg": 60.00,
    "ingredients": [
        {"ingredient": "Corn Silage", "inclusion_pct": 48.0, "fresh_kg": 24.0},
        {"ingredient": "Alfalfa Hay", "inclusion_pct": 18.0, "fresh_kg": 9.0},
        {"ingredient": "Dairy Concentrate 18% CP", "inclusion_pct": 32.0, "fresh_kg": 16.0},
        {"ingredient": "Mineral Premix", "inclusion_pct": 2.0, "fresh_kg": 1.0}
    ],
    "effective_date": "2026-08-21",
    "operator": "NUTRITIONIST_01"
}
r_ration = requests.post(f"{API_BASE}/farm/feed/rations", json=ration_payload, timeout=5)
print(f"  Ration Registration Status [{r_ration.status_code}]: {r_ration.text[:120]}")

# 3. Query Feed & Nutrition Overview
print("\n[4.3] Fetching Consolidated Feed & Nutrition Overview...")
r_overview = requests.get(f"{API_BASE}/farm/feed/overview", timeout=5)
print(f"  Feed Overview Status [{r_overview.status_code}]:")
if r_overview.status_code == 200:
    print(json.dumps(r_overview.json(), indent=2))

print("\n" + "=" * 85)
print(">>> FORENSIC PHASE 4 COMPLETE <<<")
print("=" * 85)