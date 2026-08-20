# -*- coding: utf-8 -*-
import requests
import json

API_BASE_URL = "http://127.0.0.1:8000"

print("=== TESTING MILK-WITHHOLDING ENFORCEMENT ===")

# Attempt to query withholding or operational flags for TD-015
endpoints_to_check = [
    "/farm/health-cases",
    "/farm/treatments"
]

for ep in endpoints_to_check:
    r = requests.get(f"{API_BASE_URL}{ep}", timeout=3)
    print(f"\n--- Output of {ep} ---")
    if r.status_code == 200:
        data = r.json()
        print(json.dumps(data, indent=2))
    else:
        print(f"Error {r.status_code}: {r.text}")