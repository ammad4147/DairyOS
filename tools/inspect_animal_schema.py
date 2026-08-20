# -*- coding: utf-8 -*-
import json
from dairyos.app import app
from dairyos.data.database.session import engine
from sqlalchemy import text

print("=== 1. ANIMAL ONBOARDING API ROUTES ===")
for r in app.routes:
    if any(k in r.path.lower() for k in ["animal", "herd", "calf", "calving"]) and "POST" in getattr(r, "methods", set()):
        print(f"Route: POST {r.path}")

spec = app.openapi()
components = spec.get("components", {}).get("schemas", {})

for endpoint in ["/farm/animals", "/farm/herd/animals", "/farm/calving"]:
    post_def = spec.get("paths", {}).get(endpoint, {}).get("post")
    if post_def:
        print(f"\n=== API SCHEMA: POST {endpoint} ===")
        req_body = post_def.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema", {})
        ref = req_body.get("$ref")
        if ref:
            name = ref.split("/")[-1]
            print(f"Model: {name}")
            print(json.dumps(components.get(name, {}), indent=2))
        else:
            print(json.dumps(req_body, indent=2))

print("\n=== 2. ANIMALS TABLE COLUMNS ===")
with engine.connect() as conn:
    cols = conn.execute(text("""
        SELECT column_name, data_type, is_nullable 
        FROM information_schema.columns 
        WHERE table_name = 'animals' 
        ORDER BY ordinal_position;
    """)).fetchall()
    for c in cols:
        print(f"  • {c.column_name:<20} | {c.data_type:<18} | Nullable: {c.is_nullable}")