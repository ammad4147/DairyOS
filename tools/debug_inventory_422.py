# -*- coding: utf-8 -*-
import requests
import json

API_BASE_URL = "http://127.0.0.1:8000"

payload = {
    "item": "Corn Silage",
    "quantity": 15000.0,
    "unit": "kg",
    "movement_type": "IN",
    "supplier": "PUNJAB_AGRI_FARMS",
    "location": "SILO_01",
    "operator": "INVENTORY_MGR"
}

r = requests.post(f"{API_BASE_URL}/farm/inventory", json=payload, timeout=3)
print(f"Status Code: {r.status_code}")
print(json.dumps(r.json(), indent=2))