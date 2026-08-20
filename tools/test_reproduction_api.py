# -*- coding: utf-8 -*-
import requests
import json

API_BASE_URL = "http://127.0.0.1:8000"

print("=== 1. REPRODUCTION OVERVIEW (/farm/reproduction/overview) ===")
try:
    r = requests.get(f"{API_BASE_URL}/farm/reproduction/overview", timeout=3)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        print(json.dumps(r.json(), indent=2))
    else:
        print(r.text)
except Exception as e:
    print(f"Overview Request Error: {e}")

print("\n=== 2. BREEDING SCHEMA (/openapi.json -> /farm/breeding) ===")
try:
    r = requests.get(f"{API_BASE_URL}/openapi.json", timeout=3)
    if r.status_code == 200:
        spec = r.json()
        post_def = spec.get("paths", {}).get("/farm/breeding", {}).get("post", {})
        schema_ref = post_def.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema", {})
        ref = schema_ref.get("$ref")
        if ref:
            name = ref.split("/")[-1]
            schema_def = spec.get("components", {}).get("schemas", {}).get(name, {})
            print(f"Model: {name}")
            print(json.dumps(schema_def, indent=2))
        else:
            print(json.dumps(schema_ref, indent=2))
except Exception as e:
    print(f"OpenAPI Request Error: {e}")