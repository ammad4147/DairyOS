# -*- coding: utf-8 -*-
import requests
import json

API_BASE_URL = "http://127.0.0.1:8000"

print("=== 1. TESTING RESOLUTION ENDPOINT DUAL LOOKUP (Integer ID vs String) ===")
# Testing integer ID 4 created in our previous test
r_int = requests.post(f"{API_BASE_URL}/farm/health-cases/4/resolve", json={"resolution": "Clean"}, timeout=3)
print(f"Resolve by Integer ID '4' -> Status [{r_int.status_code}]: {r_int.text}")

print("\n=== 2. CHECKING UNLINKED TREATMENTS WITH OPEN HEALTH CASES ===")
r_cases = requests.get(f"{API_BASE_URL}/farm/health-cases", timeout=3)
r_treat = requests.get(f"{API_BASE_URL}/farm/treatments", timeout=3)
cases = r_cases.json().get("cases", [])
treats = r_treat.json() if isinstance(r_treat.json(), list) else r_treat.json().get("treatments", [])

unlinked = [t for t in treats if t.get("health_case_id") is None]
print(f"Total treatments: {len(treats)} | Unlinked (health_case_id=NULL): {len(unlinked)}")

print("\n=== 3. CHECKING HEIFER CALF (TD-021) WEANING & FEED STATUS ===")
r_animal = requests.get(f"{API_BASE_URL}/farm/animals", timeout=3)
herd = r_animal.json() if isinstance(r_animal.json(), list) else r_animal.json().get("animals", [])
calf = next((a for a in herd if a.get("animal_id") == "TD-021"), {})
print(f"TD-021 Status: Lifecycle={calf.get('lifecycle_status')}, Milking={calf.get('is_currently_milking')}")