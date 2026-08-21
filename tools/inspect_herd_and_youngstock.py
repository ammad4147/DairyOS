# -*- coding: utf-8 -*-
import requests
import json
from dairyos.app import app

API_BASE = "http://127.0.0.1:8000"

print("=== 1. CURRENT HERD IN DATABASE ===")
r_animals = requests.get(f"{API_BASE}/farm/animals", timeout=5)
animals = r_animals.json() if isinstance(r_animals.json(), list) else r_animals.json().get("animals", [])
print(f"Total animals in API: {len(animals)}")
for a in animals:
    print(f"  • ID: {a.get('animal_id')} | Type: {a.get('animal_type')} | Status: {a.get('lifecycle_status') or a.get('status')} | Dam: {a.get('dam_id')}")

print("\n=== 2. DISCOVERING YOUNGSTOCK & GROWTH ROUTES ===")
for r in app.routes:
    path = getattr(r, "path", "")
    if any(k in path.lower() for k in ["youngstock", "growth", "calf", "wean", "weight"]):
        methods = list(getattr(r, "methods", []))
        print(f"  • {str(methods):<18} {path}")