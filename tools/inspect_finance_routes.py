# -*- coding: utf-8 -*-
from dairyos.app import app
import json

print("=== 1. FINANCIAL & EFFICIENCY API ROUTES ===")
for r in app.routes:
    path = getattr(r, "path", "")
    if any(k in path.lower() for k in ["cost", "finance", "kpi", "metric", "efficiency", "margin", "summary", "feed"]):
        methods = list(getattr(r, "methods", []))
        print(f"  • {str(methods):<18} {path}")