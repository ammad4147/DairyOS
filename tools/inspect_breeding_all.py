# -*- coding: utf-8 -*-
import requests
import json
from dairyos.data.database.session import engine
from sqlalchemy import text

print("=== 1. DATABASE COLUMNS: breeding_records ===")
with engine.connect() as conn:
    cols = conn.execute(text("""
        SELECT column_name, data_type, is_nullable 
        FROM information_schema.columns 
        WHERE table_name = 'breeding_records' 
        ORDER BY ordinal_position;
    """)).fetchall()
    
    for col in cols:
        print(f" - {col.column_name:<18} | {col.data_type:<15} | Nullable: {col.is_nullable}")

print("\n=== 2. API SPEC: POST /farm/breeding ===")
API_BASE_URL = "http://127.0.0.1:8000"
try:
    r = requests.get(f"{API_BASE_URL}/openapi.json")
    if r.status_code == 200:
        spec = r.json()
        post_spec = spec.get("paths", {}).get("/farm/breeding", {}).get("post", {})
        print(f"Summary: {post_spec.get('summary')}")
        content = post_spec.get("requestBody", {}).get("content", {}).get("application/json", {})
        schema_info = content.get("schema", {})
        ref = schema_info.get("$ref")
        if ref:
            schema_name = ref.split("/")[-1]
            schema_def = spec.get("components", {}).get("schemas", {}).get(schema_name, {})
            print(f"Schema Name: {schema_name}")
            print("Required Fields:", schema_def.get("required", []))
            print("Properties:")
            for p, val in schema_def.get("properties", {}).items():
                print(f"   • {p}: {val.get('type') or val.get('$ref') or val.get('anyOf')}")
        else:
            print("Schema:", json.dumps(schema_info, indent=2))
    else:
        print(f"OpenAPI HTTP Error: {r.status_code}")
except Exception as e:
    print(f"API Check Error: {e}")