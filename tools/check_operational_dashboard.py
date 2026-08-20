# -*- coding: utf-8 -*-
import requests
import json

API_BASE_URL = "http://127.0.0.1:8000"

print("=== 1. OPERATIONAL DASHBOARD (/operations/dashboard) ===")
try:
    r = requests.get(f"{API_BASE_URL}/operations/dashboard", timeout=3)
    print(f"Status [{r.status_code}]:")
    print(json.dumps(r.json(), indent=2))
except Exception as e:
    print(f"Error: {e}")

print("\n=== 2. EXECUTIVE SUMMARY (/operations/executive) ===")
try:
    r = requests.get(f"{API_BASE_URL}/operations/executive", timeout=3)
    print(f"Status [{r.status_code}]:")
    print(json.dumps(r.json(), indent=2))
except Exception as e:
    print(f"Error: {e}")