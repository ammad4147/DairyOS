import requests
import json

API_BASE_URL = "http://127.0.0.1:8000"

try:
    r = requests.get(f"{API_BASE_URL}/openapi.json")
    if r.status_code == 200:
        spec = r.json()
        milk_post = spec.get("paths", {}).get("/farm/milk", {}).get("post", {})
        print("--- POST /farm/milk OpenAPI Spec ---")
        print(f"Summary: {milk_post.get('summary')}")
        req_body = milk_post.get("requestBody", {})
        print(f"Request Body Ref: {json.dumps(req_body, indent=2)}")
    else:
        print(f"Failed to fetch OpenAPI: {r.status_code}")
except Exception as e:
    print(f"Error: {e}")
