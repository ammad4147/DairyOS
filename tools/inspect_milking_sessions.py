# -*- coding: utf-8 -*-
from dairyos.app import app

print("=== MILKING SESSION & LEDGER ENDPOINTS ===")
for r in app.routes:
    path = getattr(r, "path", "")
    if any(k in path.lower() for k in ["session", "tank", "ledger", "commit"]):
        methods = list(getattr(r, "methods", []))
        print(f"  • {str(methods):<18} {path}")