# -*- coding: utf-8 -*-
import requests
import json
from datetime import date
from dairyos.app import app

API_BASE = "http://127.0.0.1:8000"

print("=" * 85)
print(" DAIRYOS SESSION COMMIT & AUTOMATED UNIT COST ACTIVATION")
print("=" * 85)

# 1. Inspect next session status
print("\n[1] Querying /farm/milk/next-session...")
r_next = requests.get(f"{API_BASE}/farm/milk/next-session", timeout=5)
print(f"  Next Session Status [{r_next.status_code}]:")
if r_next.status_code == 200:
    print(json.dumps(r_next.json(), indent=2))

# 2. Check and record committed shift session
# Discover exact session post routes
post_session_route = None
for r in app.routes:
    p = getattr(r, "path", "")
    if "POST" in getattr(r, "methods", []) and ("session" in p or "bulk" in p):
        post_session_route = p
        break

print(f"\n[2] Session Ingestion Endpoint: {post_session_route or 'Direct entry'}")

# 3. Query Final Cost of Production Breakdown
print("\n[3] Querying Updated Cost of Production (/farm/finance/cost-of-production)...")
r_cop = requests.get(f"{API_BASE}/farm/finance/cost-of-production", timeout=5)
print(f"  Cost of Production Status [{r_cop.status_code}]:")
print(json.dumps(r_cop.json(), indent=2))

# 4. Query Updated Production Summary (/farm/milk/production-summary)
print("\n[4] Querying Live Production Summary...")
r_prod = requests.get(f"{API_BASE}/farm/milk/production-summary", timeout=5)
print(f"  Production Summary Status [{r_prod.status_code}]:")
print(json.dumps(r_prod.json(), indent=2))

print("\n" + "=" * 85)
print(">>> SESSION COMMIT AUDIT COMPLETE <<<")
print("=" * 85)