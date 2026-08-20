# -*- coding: utf-8 -*-
import json
from dairyos.app import app

spec = app.openapi()
components = spec.get("components", {}).get("schemas", {})

for endpoint, method in [("/farm/health-cases", "post"), ("/farm/treatments", "post"), ("/farm/health-observations", "post")]:
    print(f"\n=== API SPEC: {method.upper()} {endpoint} ===")
    route_spec = spec.get("paths", {}).get(endpoint, {}).get(method, {})
    req_body = route_spec.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema", {})
    ref = req_body.get("$ref")
    if ref:
        model_name = ref.split("/")[-1]
        print(f"Model: {model_name}")
        print(json.dumps(components.get(model_name, {}), indent=2))
    else:
        print(json.dumps(req_body, indent=2))