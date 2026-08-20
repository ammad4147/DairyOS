# -*- coding: utf-8 -*-
import requests
import json
from datetime import datetime, timedelta, timezone

API_BASE_URL = "http://127.0.0.1:8000"

print("=== OPENING CLINICAL CASE (Severity: SEVERE) ===")
case_payload = {
    "animal_id": "TD-015",
    "diagnosis": "Grade 2 Clinical Mastitis (Left Hind Quarter)",
    "severity": "SEVERE",
    "notes": "Intramammary infection confirmed. 4-day milk withholding enforced.",
    "follow_up_due_at": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
    "operator": "DR_ASIF_VET"
}

r = requests.post(f"{API_BASE_URL}/farm/health-cases", json=case_payload, timeout=3)
print(f"Status [{r.status_code}]: {json.dumps(r.json(), indent=2)}")