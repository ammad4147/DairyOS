# -*- coding: utf-8 -*-
import json
from dairyos.app import app

spec = app.openapi()
components = spec.get("components", {}).get("schemas", {})

print("=== API SPEC: POST /farm/health-cases/{case_id}/resolve ===")
post_spec = spec.get("paths", {}).get("/farm/health-cases/{case_id}/resolve", {}).get("post", {})
req_body = post_spec.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema", {})
ref = req_body.get("$ref")
if ref:
    model_name = ref.split("/")[-1]
    print(f"Model: {model_name}")
    print(json.dumps(components.get(model_name, {}), indent=2))
else:
    print(json.dumps(req_body, indent=2))