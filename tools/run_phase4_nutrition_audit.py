# -*- coding: utf-8 -*-
import requests
import json

API_BASE = "http://127.0.0.1:8000"

print("=" * 85)
print(" FORENSIC PHASE 4: NUTRITION ENGINE, TMR RATIONS & INVENTORY AUDIT")
print("=" * 85)

# 1. Ingest Bulk Feed Stock Receipts into Inventory
print("\n[4.1] Ingesting Bulk Feed Commodity Inventory Receipts...")
commodities = [
    {"item_name": "Corn Silage", "category": "FEED", "quantity": 15000.0, "unit": "KG", "unit_price": 18.0, "supplier": "PUNJAB_SILAGE_CORP"},
    {"item_name": "Alfalfa Hay", "category": "FEED", "quantity": 5000.0, "unit": "KG", "unit_price": 42.0, "supplier": "ALFALFA_SUPPLIERS_KASUR"},
    {"item_name": "Dairy Concentrate 18% CP", "category": "FEED", "quantity": 6000.0, "unit": "KG", "unit_price": 115.0, "supplier": "ICI_PAKISTAN_FEEDS"},
    {"item_name": "Mineral Premix", "category": "FEED", "quantity": 500.0, "unit": "KG", "unit_price": 350.0, "supplier": "VET_MINERALS_LTD"}
]

for c in commodities:
    payload = {
        "item_name": c["item_name"],
        "category": c["category"],
        "movement_type": "IN",
        "quantity": c["quantity"],
        "unit": c["unit"],
        "cost_per_unit": c["unit_price"],
        "notes": f"Bulk delivery from {c['supplier']}",
        "operator": "STORE_MANAGER_01"
    }
    r = requests.post(f"{API_BASE}/farm/inventory", json=payload, timeout=5)
    print(f"  Stock Inflow [{r.status_code}]: {c['item_name']} -> {c['quantity']} {c['unit']} @ {c['unit_price']} PKR/kg")

# 2. Register Active High-Yield TMR Formulation
print("\n[4.2] Registering Active High-Yield TMR Formulation (TMR-LACT-HIGH-01)...")
ration_payload = {
    "name": "TMR-LACT-HIGH-01",
    "animal_group": "HIGH_YIELD_LACTATING",
    "target_dmi_kg": 22.5,
    "dry_matter_pct": 62.86,
    "crude_protein_pct": 16.8,
    "ndf_pct": 31.5,
    "energy_mcal_kg": 1.68,
    "cost_per_kg": 60.00,
    "ingredients_json": json.dumps([
        {"ingredient": "Corn Silage", "inclusion_pct": 48.0, "fresh_kg": 24.0},
        {"ingredient": "Alfalfa Hay", "inclusion_pct": 18.0, "fresh_kg": 9.0},
        {"ingredient": "Dairy Concentrate 18% CP", "inclusion_pct": 32.0, "fresh_kg": 16.0},
        {"ingredient": "Mineral Premix", "inclusion_pct": 2.0, "fresh_kg": 1.0}
    ]),
    "effective_date": "2026-08-21",
    "operator": "NUTRITIONIST_01"
}
r_ration = requests.post(f"{API_BASE}/farm/feed/rations", json=ration_payload, timeout=5)
print(f"  Ration Registration Status [{r_ration.status_code}]: {r_ration.text[:90]}")

# 3. Log Pen-Level TMR Feeding Dispatch
print("\n[4.3] Dispatching Morning TMR Feed Batch Deliveries...")
pens = ["PEN_01_HIGH_YIELD", "PEN_02_FRESH_COWS"]
for p in pens:
    feed_record_payload = {
        "group_or_pen": p,
        "feed_type": "TMR-LACT-HIGH-01",
        "quantity_kg": 250.0,
        "notes": f"Morning mix delivered at 06:30. 10 cows in pen.",
        "operator": "FEEDER_DRIVER_01"
    }
    r_feed = requests.post(f"{API_BASE}/farm/feed/records", json=feed_record_payload, timeout=5)
    print(f"  Feed Delivery to {p} [{r_feed.status_code}]: 250.0 kg fresh TMR")

# 4. Query Nutrition Overview & Warehouse Balances
print("\n[4.4] Fetching Feed & Nutrition Inventory Overview...")
r_overview = requests.get(f"{API_BASE}/farm/feed/overview", timeout=5)
print(f"  Feed Overview Status [{r_overview.status_code}]:")
if r_overview.status_code == 200:
    print(json.dumps(r_overview.json(), indent=2))
else:
    print(r_overview.text[:120])

print("\n" + "=" * 85)
print(">>> FORENSIC PHASE 4 NUTRITION & INVENTORY AUDIT COMPLETE <<<")
print("=" * 85)