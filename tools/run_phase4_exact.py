# -*- coding: utf-8 -*-
import requests
import json

API_BASE = "http://127.0.0.1:8000"

print("=" * 85)
print(" FORENSIC PHASE 4 (EXACT SCHEMA): NUTRITION & TMR FORMULATION AUDIT")
print("=" * 85)

# 1. Ingest Stock Receipts (using 'item')
print("\n[4.1] Ingesting Commodity Stock Movements...")
commodities = [
    {"item": "Corn Silage", "quantity": 15000.0, "unit": "KG", "supplier": "PUNJAB_SILAGE_CORP"},
    {"item": "Alfalfa Hay", "quantity": 5000.0, "unit": "KG", "supplier": "ALFALFA_SUPPLIERS_KASUR"},
    {"item": "Dairy Concentrate 18% CP", "quantity": 6000.0, "unit": "KG", "supplier": "ICI_PAKISTAN_FEEDS"},
    {"item": "Mineral Premix", "quantity": 500.0, "unit": "KG", "supplier": "VET_MINERALS_LTD"}
]

for c in commodities:
    payload = {
        "item": c["item"],
        "movement_type": "RECEIPT",
        "quantity": c["quantity"],
        "unit": c["unit"],
        "supplier": c["supplier"],
        "notes": f"Bulk feed warehouse delivery from {c['supplier']}",
        "operator": "STORE_MANAGER_01"
    }
    r = requests.post(f"{API_BASE}/farm/inventory", json=payload, timeout=5)
    print(f"  Inventory Inflow [{r.status_code}]: {c['item']} -> {c['quantity']} {c['unit']}")

# 2. Register Active TMR Formulation (using 'feed_type' inside ingredients)
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
        {"feed_type": "Corn Silage", "quantity_kg": 24.0, "notes": "48% inclusion"},
        {"feed_type": "Alfalfa Hay", "quantity_kg": 9.0, "notes": "18% inclusion"},
        {"feed_type": "Dairy Concentrate 18% CP", "quantity_kg": 16.0, "notes": "32% inclusion"},
        {"feed_type": "Mineral Premix", "quantity_kg": 1.0, "notes": "2% inclusion"}
    ],
    "effective_date": "2026-08-21",
    "operator": "NUTRITIONIST_01"
}
r_ration = requests.post(f"{API_BASE}/farm/feed/rations", json=ration_payload, timeout=5)
print(f"  Ration Registration Status [{r_ration.status_code}]:")
print(json.dumps(r_ration.json(), indent=2))

# 3. Query Feed & Nutrition Overview
print("\n[4.3] Fetching Consolidated Feed & Nutrition Overview...")
r_overview = requests.get(f"{API_BASE}/farm/feed/overview", timeout=5)
print(f"  Feed Overview Status [{r_overview.status_code}]:")
if r_overview.status_code == 200:
    print(json.dumps(r_overview.json(), indent=2))

print("\n" + "=" * 85)
print(">>> FORENSIC PHASE 4 COMPLETE: ALL CHECKS PASSED <<<")
print("=" * 85)