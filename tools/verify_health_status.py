# -*- coding: utf-8 -*-
import requests
import json

API_BASE_URL = "http://127.0.0.1:8000"

print("=== 1. ACTIVE HEALTH CASES (/farm/health-cases) ===")
r_cases = requests.get(f"{API_BASE_URL}/farm/health-cases", timeout=3)
print(json.dumps(r_cases.json(), indent=2))

print("\n=== 2. TREATMENT & WITHHOLDING LOGS (/farm/treatments) ===")
r_treat = requests.get(f"{API_BASE_URL}/farm/treatments", timeout=3)
print(json.dumps(r_treat.json(), indent=2))