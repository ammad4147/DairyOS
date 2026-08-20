# -*- coding: utf-8 -*-
import requests
import json

API_BASE_URL = "http://127.0.0.1:8000"

print("=== TESTING CASE RESOLUTION VIA NUMERIC ID (4) ===")
payload = {
    "resolution": "Foot examination clear, minor abrasion treated, returned to milking herd.",
    "operator": "DR_ASIF_VET",
    "resolved_by": "DR_ASIF_VET"
}

r = requests.post(f"{API_BASE_URL}/farm/health-cases/4/resolve", json=payload, timeout=3)
print(f"Status [{r.status_code}]:")
print(json.dumps(r.json(), indent=2))