import requests
import json

API_BASE_URL = "http://127.0.0.1:8000"

try:
    r = requests.get(f"{API_BASE_URL}/openapi.json")
    if r.status_code == 200:
        spec = r.json()
        schema = spec.get("components", {}).get("schemas", {}).get("LegacyCompatibleMilkEntryRequest", {})
        print("=== LegacyCompatibleMilkEntryRequest Schema ===")
        print(json.dumps(schema, indent=2))
    else:
        print(f"Failed to fetch OpenAPI: {r.status_code}")
except Exception as e:
    print(f"Error: {e}")
