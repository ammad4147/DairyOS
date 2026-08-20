# -*- coding: utf-8 -*-
import requests
import json
from datetime import datetime, timezone

API_BASE_URL = "http://127.0.0.1:8000"

print("=== 1. INGESTING RAW FEED COMMODITIES INTO INVENTORY ===")
feed_commodities = [
    {"item": "Corn Silage", "quantity": 15000.0, "unit": "kg", "movement_type": "IN", "supplier": "PUNJAB_AGRI_FARMS", "location": "SILO_01"},
    {"item": "Alfalfa Hay", "quantity": 5000.0, "unit": "kg", "movement_type": "IN", "supplier": "KASUR_FODDER_CO", "location": "BARN_B"},
    {"item": "Dairy Concentrate 18% CP", "quantity": 6000.0, "unit": "kg", "movement_type": "IN", "supplier": "SUPREME_FEEDS", "location": "FEED_STORE"},
    {"item": "Mineral Premix", "quantity": 500.0, "unit": "kg", "movement_type": "IN", "supplier": "MAXIMA_VET", "location": "FEED_STORE"}
]

for item in feed_commodities:
    item["operator"] = "INVENTORY_MGR"
    r = requests.post(f"{API_BASE_URL}/farm/inventory", json=item, timeout=3)
    print(f" [{r.status_code}] Inward Stock: {item['item']} ({item['quantity']} {item['unit']})")

print("\n=== 2. PUBLISHING BALANCED TMR RATION FORMULATION ===")
tmr_ration = {
    "plan_id": "TMR-LACT-HIGH-01",
    "name": "High Lactation TMR (16.8% CP / 1.68 Mcal)",
    "target_group": "LACTATING_COWS",
    "dry_matter_kg": 22.5,
    "crude_protein_pct": 16.8,
    "ndf_pct": 31.5,
    "energy_mcal": 1.68,
    "active": True,
    "farm_id": "DEFAULT",
    "ingredients": [
        {"item": "Corn Silage", "inclusion_pct": 48.0, "dm_pct": 34.0},
        {"item": "Alfalfa Hay", "inclusion_pct": 18.0, "dm_pct": 88.0},
        {"item": "Dairy Concentrate 18% CP", "inclusion_pct": 32.0, "dm_pct": 90.0},
        {"item": "Mineral Premix", "inclusion_pct": 2.0, "dm_pct": 95.0}
    ]
}

r_ration = requests.post(f"{API_BASE_URL}/farm/nutrition/rations", json=tmr_ration, timeout=3)
print(f"Ration Plan Status [{r_ration.status_code}]: {r_ration.text[:90]}")

print("\n=== 3. DISTRIBUTING MORNING FEED TO PENS ===")
feeding_deliveries = [
    {"group_or_pen": "PEN_01_HIGH_YIELD", "feed_type": "TMR-LACT-HIGH-01", "quantity_kg": 250.0, "notes": "Morning feed distribution - clean bunks"},
    {"group_or_pen": "PEN_02_FRESH_COWS", "feed_type": "TMR-LACT-HIGH-01", "quantity_kg": 250.0, "notes": "Morning feed distribution - good intake"}
]

for delivery in feeding_deliveries:
    r_feed = requests.post(f"{API_BASE_URL}/farm/feed/records", json=delivery, timeout=3)
    print(f" [{r_feed.status_code}] Feed Delivered to {delivery['group_or_pen']}: {delivery['quantity_kg']} kg")

print("\n>>> NUTRITION & FEED PIPELINE COMMITTED <<<")