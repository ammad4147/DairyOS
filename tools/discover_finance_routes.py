# -*- coding: utf-8 -*-
from dairyos.app import app
from pathlib import Path

print("=== 1. REGISTERED FINANCE ROUTES ===")
for r in app.routes:
    path = getattr(r, "path", "")
    if any(k in path.lower() for k in ["finan", "expense", "revenue", "cost"]):
        methods = list(getattr(r, "methods", []))
        print(f"  • {str(methods):<18} {path}")