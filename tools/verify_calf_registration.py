# -*- coding: utf-8 -*-
import requests
import json

API_BASE_URL = "http://127.0.0.1:8000"

print("=== 1. DAM (TD-001) REPRODUCTIVE PASSPORT ===")
r_dam = requests.get(f"{API_BASE_URL}/farm/animals/TD-001/reproduction", timeout=3)
if r_dam.status_code == 200:
    print(json.dumps(r_dam.json(), indent=2))
else:
    print(f"Status {r_dam.status_code}: {r_dam.text}")

print("\n=== 2. VERIFY NEWBORN (TD-021) IN HERD REGISTRY ===")
r_herd = requests.get(f"{API_BASE_URL}/farm/animals", timeout=3)
if r_herd.status_code == 200:
    herd = r_herd.json()
    calf = next((a for a in (herd if isinstance(herd, list) else herd.get("animals", [])) if a.get("animal_id") == "TD-021"), None)
    if calf:
        print(f"Found TD-021: {json.dumps(calf, indent=2)}")
    else:
        print(f"Total Herd Count: {len(herd)}. Listing summary:")
        print(json.dumps(herd[:3] if isinstance(herd, list) else herd, indent=2))