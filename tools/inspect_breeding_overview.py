# -*- coding: utf-8 -*-
import requests
import json

API_BASE_URL = "http://127.0.0.1:8000"

print("=== 1. POST /farm/breeding OpenAPI Schema ===")
r = requests.get(f"{API_BASE_URL}/openapi.json")
if r.status_code == 200:
    spec = r.json()
    post_def = spec.get("paths", {}).get("/farm/breeding", {}).get("post", {})
    req_body = post_def.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema", {})
    ref = req_body.get("$ref")
    if ref:
        name = ref.split("/")[-1]
        print(f"Model: {name}")
        schema = spec.get("components", {}).get("schemas", {}).get(name, {})
        print(json.dumps(schema, indent=2))
    else:
        print(json.dumps(req_body, indent=2))

print("\n=== 2. Current GET /farm/reproduction/overview ===")
r_ov = requests.get(f"{API_BASE_URL}/farm/reproduction/overview")
if r_ov.status_code == 200:
    print(json.dumps(r_ov.json(), indent=2))
else:
    print(f"Error ({r_ov.status_code}): {r_ov.text}")