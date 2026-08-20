# -*- coding: utf-8 -*-
import requests
import json

API_BASE_URL = "http://127.0.0.1:8000"

print("=== 1. FEED INVENTORY BALANCES (/farm/inventory/balance) ===")
try:
    r = requests.get(f"{API_BASE_URL}/farm/inventory/balance", timeout=3)
    print(f"Status [{r.status_code}]:")
    print(json.dumps(r.json(), indent=2))
except Exception as e:
    print(f"Error: {e}")

print("\n=== 2. CURRENT RATIONS (/farm/nutrition/rations or /farm/feed/rations) ===")
for ep in ["/farm/nutrition/rations", "/farm/feed/rations"]:
    try:
        r = requests.get(f"{API_BASE_URL}{ep}", timeout=3)
        print(f"Endpoint {ep} Status [{r.status_code}]:")
        if r.status_code == 200:
            print(json.dumps(r.json(), indent=2))
    except Exception as e:
        print(f"Error checking {ep}: {e}")

print("\n=== 3. FEED OVERVIEW (/farm/feed/overview) ===")
try:
    r = requests.get(f"{API_BASE_URL}/farm/feed/overview", timeout=3)
    print(f"Status [{r.status_code}]:")
    print(json.dumps(r.json(), indent=2))
except Exception as e:
    print(f"Error: {e}")