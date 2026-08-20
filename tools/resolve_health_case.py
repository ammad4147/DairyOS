# -*- coding: utf-8 -*-
import requests
import json

API_BASE_URL = "http://127.0.0.1:8000"

print("=== RESOLVING HEALTH CASE 3 (TD-015) ===")

payload = {
    "resolution": "Full clinical recovery. Somatic cell count normalized, foremilk clear, quarter pliable and non-tender.",
    "resolved_by": "DR_ASIF_VET",
    "operator": "DR_ASIF_VET"
}

# Resolve using case ID 3
r = requests.post(f"{API_BASE_URL}/farm/health-cases/3/resolve", json=payload, timeout=3)
print(f"Status [{r.status_code}]: {json.dumps(r.json(), indent=2)}")