# -*- coding: utf-8 -*-
import requests
import json

API_BASE_URL = "http://127.0.0.1:8000"

try:
    r = requests.get(f"{API_BASE_URL}/farm/reproduction/overview", timeout=3)
    print("=== UPDATED REPRODUCTION OVERVIEW ===")
    print(json.dumps(r.json(), indent=2))
except Exception as e:
    print(f"Error: {e}")