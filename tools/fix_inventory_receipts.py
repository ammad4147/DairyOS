# -*- coding: utf-8 -*-
import requests
import json

API_BASE_URL = "http://127.0.0.1:8000"

print("=== INGESTING RAW FEED COMMODITIES (Movement: RECEIPT) ===")
feed_commodities = [
    {"item": "Corn Silage", "quantity": 15000.0, "unit": "kg", "movement_type": "RECEIPT", "supplier": "PUNJAB_AGRI_FARMS", "location": "SILO_01"},
    {"item": "Alfalfa Hay", "quantity": 5000.0, "unit": "kg", "movement_type": "RECEIPT", "supplier": "KASUR_FODDER_CO", "location": "BARN_B"},
    {"item": "Dairy Concentrate 18% CP", "quantity": 6000.0, "unit": "kg", "movement_type": "RECEIPT", "supplier": "SUPREME_FEEDS", "location": "FEED_STORE"},
    {"item": "Mineral Premix", "quantity": 500.0, "unit": "kg", "movement_type": "RECEIPT", "supplier": "MAXIMA_VET", "location": "FEED_STORE"}
]

for item in feed_commodities:
    item["operator"] = "INVENTORY_MGR"
    r = requests.post(f"{API_BASE_URL}/farm/inventory", json=item, timeout=3)
    print(f" [{r.status_code}] Inward Stock: {item['item']} ({item['quantity']} {item['unit']})")

print("\n=== VERIFYING UPDATED INVENTORY BALANCES (/farm/inventory/balance) ===")
r_bal = requests.get(f"{API_BASE_URL}/farm/inventory/balance", timeout=3)
print(json.dumps(r_bal.json(), indent=2))